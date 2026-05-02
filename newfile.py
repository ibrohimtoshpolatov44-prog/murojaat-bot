import asyncio
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)

# --- KONFIG ---
API_TOKEN = "8465608102:AAF_WROmWkVd06dCdV0_cbYqUNhYUk8_ThY"
CHANNELS = [ "@appzumer"]
PORT = int(os.environ.get("PORT", 10000))
WEB_APP_URL = "https://ibrohimtoshpolatov44-prog.github.io/Tarixchi/"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- WEB SERVER (CRON-JOB ENDPOINT) ---
async def handle_ping(request):
    return web.json_response({"status": "ok"})

async def handle_root(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()

    # 🔥 CRON-JOB SHU URLGA URADI:
    app.router.add_get("/ping", handle_ping)

    # optional home page
    app.router.add_get("/", handle_root)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logging.info(f"Web server started on port {PORT}")

# --- OBUNA TEKSHIRISH ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# --- TUGMALAR ---
def get_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Bizning kanal"), KeyboardButton(text="📱 Mini Ilova")]
        ],
        resize_keyboard=True
    )

def get_sub_buttons():
    buttons = [
        [InlineKeyboardButton(text=f"Obuna bo'lish {ch}", url=f"https://t.me/{ch[1:]}")]
        for ch in CHANNELS
    ]
    buttons.append([InlineKeyboardButton(text="Tekshirish ✅", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- HANDLERLAR ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await message.answer(
            "Botdan foydalanish uchun kanallarga obuna bo'ling:",
            reply_markup=get_sub_buttons()
        )
        return

    await message.answer("Xush kelibsiz!", reply_markup=get_menu())

@dp.callback_query(F.data == "check_sub")
async def check_sub(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Obuna tasdiqlandi ✅", reply_markup=get_menu())
    else:
        await call.answer("Hali obuna bo'lmagansiz ❌", show_alert=True)

@dp.message(F.text == "📢 Bizning kanal")
async def channels(message: types.Message):
    text = "\n".join([f"https://t.me/{ch[1:]}" for ch in CHANNELS])
    await message.answer(f"Bizning kanallar:\n{text}")

@dp.message(F.text == "📱 Mini Ilova")
async def mini_app(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await message.answer("Avval obuna bo'ling!", reply_markup=get_sub_buttons())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ilovani ochish 🚀", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    await message.answer("Mini ilovani oching:", reply_markup=kb)

# --- MAIN ---
async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
