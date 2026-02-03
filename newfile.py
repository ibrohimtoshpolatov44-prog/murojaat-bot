import asyncio
import logging
import aiohttp
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# 1. SOZLAMALAR
API_TOKEN = '7773701126:AAEIsIWkcerz8URbr1R3SBNuJrvAfBeIqzs'
ADMIN_ID = 7751709985
CHANNEL_USERNAME = "@Tarixchilar_1IDUM"

# HAVOLALAR
TEST_URL = "https://ibrohimtoshpolatov44-prog.github.io/Milliy_Sertifikat_Tarix1/"
JAHON_TARIXI_7_URL = "https://ibrohimtoshpolatov44-prog.github.io/7-sinf_JahonTarixi_v1/"
RENDER_URL = "https://murojaat-bot-1-jqjg.onrender.com" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MA'LUMOTLAR BAZASI BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, full_name, username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, full_name, username) VALUES (?, ?, ?)", 
                   (user_id, full_name, username))
    conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# --- UYQUGA QARSHI TIZIM ---
async def keep_alive():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(RENDER_URL) as response:
                    logging.info(f"Self-ping: {response.status}")
            except Exception as e:
                logging.error(f"Ping error: {e}")
            await asyncio.sleep(600)

async def handle(request):
    return web.Response(text="Bot is running!")

# --- KLAVIATURALAR ---
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Tarix Milliy Sertifikat testi", web_app=WebAppInfo(url=TEST_URL))],
            [KeyboardButton(text="🌍 7-sinf Jahon Tarixi (1-19 mavzular)", web_app=WebAppInfo(url=JAHON_TARIXI_7_URL))],
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
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return False

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # Foydalanuvchini bazaga qo'shish
    add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    
    if await is_subscribed(message.from_user.id) or message.from_user.id == ADMIN_ID:
        await message.answer("Xush kelibsiz! Menyu tugmalaridan foydalaning 👇", reply_markup=get_main_menu())
    else:
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=get_sub_keyboard())

@dp.message(Command("stat"), F.from_user.id == ADMIN_ID)
async def stat_handler(message: types.Message):
    count = get_total_users()
    await message.answer(f"📊 **Bot statistikasi:**\n\nJami foydalanuvchilar: {count} ta")

@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Rahmat! Endi foydalanishingiz mumkin.", reply_markup=get_main_menu())
    else:
        await call.answer("Siz hali a'zo bo'lmadingiz! ❌", show_alert=True)

@dp.message(F.chat.id != ADMIN_ID)
async def handle_user_msg(message: types.Message):
    ignore_list = ["📝 Tarix Milliy Sertifikat testi", "🌍 7-sinf Jahon Tarixi (1-19 mavzular)", "📢 Bizning kanal"]
    if message.text in ignore_list:
        if message.text == "📢 Bizning kanal":
            await message.answer(f"Bizning rasmiy kanalimiz: {CHANNEL_USERNAME}")
        return

    if not await is_subscribed(message.from_user.id):
        await message.answer("Xabar yuborish uchun kanalga a'zo bo'ling.", reply_markup=get_sub_keyboard())
        return

    user_info = f"#ID{message.from_user.id}"
    await bot.send_message(ADMIN_ID, f"👤 **Kimdan:** {message.from_user.full_name}\n\n💬 **Xabar:** {message.text}\n\n{user_info}")
    await message.answer("✅ Xabaringiz adminga yuborildi.")

@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    try:
        target_id = int(message.reply_to_message.text.split("#ID")[-1])
        await bot.copy_message(target_id, ADMIN_ID, message.message_id)
        await message.answer("✅ Javobingiz yuborildi.")
    except:
        await message.answer("❌ Xato: ID topilmadi.")

# --- ISHGA TUSHIRISH ---
async def main():
    init_db() # Bazani yaratish
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

    await asyncio.gather(dp.start_polling(bot), keep_alive())

if __name__ == '__main__':
    asyncio.run(main())
                        
