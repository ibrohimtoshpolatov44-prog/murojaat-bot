import asyncio
import logging
import sqlite3
import time
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                            InlineKeyboardMarkup, InlineKeyboardButton, PollAnswer)

# --- SOZLAMALAR ---
API_TOKEN = '7773701126:AAFX4uHDUo3y1brZa1Y84OUA7SOCaJr1Zic' # @BotFather bergan tokenni aniq qo'ying
CH_ID = "@Tarixchilar_1IDUM"
ADMIN_ID = 7751709985 # O'zingizning ID raqamingiz
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_results = {}

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

# --- WEB SERVER (PING UCHUN) ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# --- TUGMALAR (Tuzatilgan) ---
def get_menu(user_id):
    kb = [
        [KeyboardButton(text="1. Milliy Sertifikat 📝")],
        [KeyboardButton(text="2. Bizning kanal 📢")],
        [KeyboardButton(text="5. Botni baholash ⭐")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="➕ Savol qo'shish")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- MAJBURIY OBUNA FUNKSIYASI ---
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CH_ID, user_id=user_id)
        # Member, Administrator yoki Creator bo'lsa True qaytaradi
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Obuna tekshirishda xato: {e}")
        return False

# --- HANDLERLAR ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    is_sub = await check_sub(message.from_user.id)
    if is_sub:
        await message.answer("Xush kelibsiz! Bo'limni tanlang:", reply_markup=get_menu(message.from_user.id))
    else:
        btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Kanalga a'zo bo'lish", url=f"https://t.me/{CH_ID[1:]}")],
            [InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_sub")]
        ])
        await message.answer(f"Botdan foydalanish uchun {CH_ID} kanaliga a'zo bo'ling!", reply_markup=btn)

@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Tabriklaymiz! Obuna tasdiqlandi.", reply_markup=get_menu(call.from_user.id))
    else:
        await call.answer("Siz hali a'zo emassiz! ❌", show_alert=True)

# 2. Bizning kanal
@dp.message(F.text == "2. Bizning kanal 📢")
async def show_channel(message: types.Message):
    await message.answer(f"Bizning rasmiy kanalimiz: {CH_ID}\nLink: https://t.me/{CH_ID[1:]}")

# 5. Botni baholash
@dp.message(F.text == "5. Botni baholash ⭐")
async def rate_bot(message: types.Message):
    btns = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"star_{i}"))
        if i % 5 == 0:
            btns.append(row)
            row = []
    await message.answer("Botni 10 ballik tizimda baholang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@dp.callback_query(F.data.startswith("star_"))
async def process_rating(call: types.CallbackQuery):
    ball = call.data.split("_")[1]
    await call.message.edit_text(f"Rahmat! Siz botni {ball} ballga baholadingiz. ✨")
    await call.answer()

# --- QOLGAN FUNKSIYALAR (SAVOL QO'SHISH VA QUIZ) ---
# ... (Yuqoridagi kod bilan bir xil, lekin F.text filtrlariga e'tibor bering)
@dp.message(F.text == "➕ Savol qo'shish", F.from_user.id == ADMIN_ID)
async def start_add_q(message: types.Message, state: FSMContext):
    await message.answer("Yangi savolni yuboring:")
    await state.set_state(AdminState.waiting_for_question)

# ... (AdminState handlerlari shu yerda bo'ladi)

async def main():
    init_db()
    await asyncio.gather(start_web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
            
