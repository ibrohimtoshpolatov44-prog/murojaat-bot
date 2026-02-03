import asyncio
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# 1. SOZLAMALAR
API_TOKEN = '7773701126:AAEIsIWkcerz8URbr1R3SBNuJrvAfBeIqzs'
ADMIN_ID = 7751709985
CHANNEL_USERNAME = "@Tarixchilar_1IDUM"
TEST_URL = "https://ibrohimtoshpolatov44-prog.github.io/Milliy_Sertifikat_Tarix1/"
GAME_URL = "https://ibrohimtoshpolatov44-prog.github.io/tarix-oyin/"
RENDER_URL = "https://murojaat-bot-1-jqjg.onrender.com" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- UYQUGA QARSHI TIZIM (SELF-PING) ---

async def keep_alive():
    """Har 10 daqiqada o'ziga so'rov yuborib, serverni uyg'oq tutadi"""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(RENDER_URL) as response:
                    logging.info(f"Self-ping yuborildi: {response.status}")
            except Exception as e:
                logging.error(f"Self-pingda xato: {e}")
            await asyncio.sleep(600) # 600 soniya = 10 daqiqa

async def handle(request):
    return web.Response(text="Bot is running!")

# --- KLAVIATURALAR ---

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Tarix Milliy Sertifikat testi", web_app=WebAppInfo(url=TEST_URL))],
            [KeyboardButton(text="🎮 Tarixiy o'yin", web_app=WebAppInfo(url=GAME_URL))],
            [KeyboardButton(text="📢 Bizning kanal")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])
    return keyboard

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if await is_subscribed(message.from_user.id) or message.from_user.id == ADMIN_ID:
        await message.answer("Xush kelibsiz! Menyu tugmalaridan foydalaning 👇", reply_markup=get_main_menu())
    else:
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=get_sub_keyboard())

async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return False

@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Rahmat! Endi foydalanishingiz mumkin.", reply_markup=get_main_menu())
    else:
        await call.answer("Siz hali a'zo bo'lmadingiz! ❌", show_alert=True)

# Foydalanuvchidan adminga
@dp.message(F.chat.id != ADMIN_ID)
async def handle_user_msg(message: types.Message):
    if message.text in ["📝 Tarix Milliy Sertifikat testi", "🎮 Tarixiy o'yin", "📢 Bizning kanal"]:
        if message.text == "📢 Bizning kanal":
            await message.answer(f"Bizning rasmiy kanalimiz: {CHANNEL_USERNAME}")
        return

    if not await is_subscribed(message.from_user.id):
        await message.answer("Xabar yuborish uchun kanalga a'zo bo'ling.", reply_markup=get_sub_keyboard())
        return

    user_info = f"#ID{message.from_user.id}"
    await bot.send_message(ADMIN_ID, f"👤 **Kimdan:** {message.from_user.full_name}\n\n💬 **Xabar:** {message.text}\n\n{user_info}")
    await message.answer("✅ Xabaringiz adminga yuborildi.")

# Admindan foydalanuvchiga
@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    try:
        reply_text = message.reply_to_message.text
        target_id = int(reply_text.split("#ID")[-1])
        await bot.copy_message(target_id, ADMIN_ID, message.message_id)
        await message.answer("✅ Javobingiz yuborildi.")
    except:
        await message.answer("❌ Xato: Javob yuborib bo'lmadi (ID topilmadi).")

# --- ASOSIY ISHGA TUSHIRISH ---

async def main():
    # Render uchun Veb-server (Port 10000 qilib belgilandi)
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render Free tier odatda 10000 portini kutadi
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

    # Parallel ravishda Bot va Self-pingni ishga tushirish
    await asyncio.gather(
        dp.start_polling(bot),
        keep_alive()
    )

if __name__ == '__main__':
    asyncio.run(main())
    
