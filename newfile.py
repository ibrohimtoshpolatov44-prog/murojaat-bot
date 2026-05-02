import asyncio
import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                            InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo)

# --- KONFIGURATSIYA ---
API_TOKEN = '7773701126:AAGWC3SNwHBTmkxBtAuU2HaDKl2gX3CfmIY'
CHANNELS = ["@Tarixchilar_1IDUM", "@appzumer"]
ADMIN_ID = 7751709985
PORT = int(os.environ.get("PORT", 10000))
WEB_APP_URL = "https://ibrohimtoshpolatov44-prog.github.io/Tarixchi/"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class AdminState(StatesGroup):
    waiting_for_question = State()
    waiting_for_options = State()
    waiting_for_correct_id = State()

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('tarix_quiz.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       question TEXT, options TEXT, correct_id INTEGER)''')
    conn.commit()
    conn.close()

# --- CRON-JOB UCHUN WEB SERVER (UHLAB QOLMASLIK UCHUN) ---
async def handle_ping(request):
    return web.Response(text="Bot is live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# --- OBUNANI TEKSHIRISH ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

# --- TUGMALAR ---
def get_menu(user_id):
    kb = [
        [KeyboardButton(text="1. Milliy Sertifikat 📝")],
        [KeyboardButton(text="2. Bizning kanal 📢"), KeyboardButton(text="3. Mini Ilova 📱")],
        [KeyboardButton(text="5. Botni baholash ⭐")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="➕ Savol qo'shish")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_sub_buttons():
    btns = [[InlineKeyboardButton(text=f"Obuna bo'lish {ch}", url=f"https://t.me/{ch[1:]}")] for ch in CHANNELS]
    btns.append([InlineKeyboardButton(text="Tekshirish ✅", callback_data="sub_check")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

# --- HANDLERLAR ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await message.answer("Botdan foydalanish uchun kanallarga obuna bo'ling:", reply_markup=get_sub_buttons())
        return
    await message.answer("Xush kelibsiz!", reply_markup=get_menu(message.from_user.id))

@dp.callback_query(F.data == "sub_check")
async def sub_check_callback(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Obuna tasdiqlandi!", reply_markup=get_menu(call.from_user.id))
    else:
        await call.answer("Hali obuna bo'lmagansiz! ❌", show_alert=True)

@dp.message(F.text == "3. Mini Ilova 📱")
async def open_mini_app(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await message.answer("Avval obuna bo'ling!", reply_markup=get_sub_buttons())
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ilovani ochish 🚀", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await message.answer("Tarixiy mini ilovangizni ishga tushiring:", reply_markup=kb)

# --- MAIN ---
async def main():
    init_db()
    # Web serverni cron-job uchun alohida task qilib ishga tushiramiz
    asyncio.create_task(start_web_server())
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
          
