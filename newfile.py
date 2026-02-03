import asyncio
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)

# ================== SOZLAMALAR ==================

API_TOKEN = '7773701126:AAEIsIWkcerz8URbr1R3SBNuJrvAfBeIqzs'
ADMIN_ID = 7751709985
CHANNEL_USERNAME = "@Tarixchilar_1IDUM"
TEST_URL = "https://ibrohimtoshpolatov44-prog.github.io/Milliy_Sertifikat_Tarix1/"
RENDER_URL = "https://murojaat-bot-1-jqjg.onrender.com"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================== UYQUGA QARSHI (SELF-PING) ==================

async def keep_alive():
    """Har 10 daqiqada serverni uyg‘oq tutadi"""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(RENDER_URL) as response:
                    logging.info(f"Self-ping yuborildi: {response.status}")
            except Exception as e:
                logging.error(f"Self-ping xatosi: {e}")
            await asyncio.sleep(600)  # 10 daqiqa

async def handle(request):
    return web.Response(text="Bot is running!")

# ================== KLAVIATURALAR ==================

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📝 Tarix Milliy Sertifikat testi",
                web_app=WebAppInfo(url=TEST_URL)
            )],
            [KeyboardButton(text="📢 Bizning kanal")]
        ],
        resize_keyboard=True
    )

def get_sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📢 Kanalga a'zo bo‘lish",
            url=f"https://t.me/{CHANNEL_USERNAME[1:]}"
        )],
        [InlineKeyboardButton(
            text="✅ Tekshirish",
            callback_data="check_sub"
        )]
    ])

# ================== YORDAMCHI FUNKSIYA ==================

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

# ================== HANDLERLAR ==================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if await is_subscribed(message.from_user.id) or message.from_user.id == ADMIN_ID:
        await message.answer(
            "Xush kelibsiz! Menyu tugmalaridan foydalaning 👇",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "Botdan foydalanish uchun kanalga a'zo bo‘ling:",
            reply_markup=get_sub_keyboard()
        )

@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer(
            "Rahmat! Endi foydalanishingiz mumkin.",
            reply_markup=get_main_menu()
        )
    else:
        await call.answer(
            "Siz hali kanalga a'zo bo‘lmadingiz ❌",
            show_alert=True
        )

# ================== FOYDALANUVCHIDAN ADMINGA ==================

@dp.message(F.chat.id != ADMIN_ID)
async def handle_user_msg(message: types.Message):
    if message.text in [
        "📝 Tarix Milliy Sertifikat testi",
        "📢 Bizning kanal"
    ]:
        if message.text == "📢 Bizning kanal":
            await message.answer(f"Bizning rasmiy kanalimiz: {CHANNEL_USERNAME}")
        return

    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "Xabar yuborish uchun kanalga a'zo bo‘ling.",
            reply_markup=get_sub_keyboard()
        )
        return

    user_tag = f"#ID{message.from_user.id}"
    await bot.send_message(
        ADMIN_ID,
        f"👤 Kimdan: {message.from_user.full_name}\n\n"
        f"💬 Xabar: {message.text}\n\n"
        f"{user_tag}"
    )
    await message.answer("✅ Xabaringiz adminga yuborildi.")

# ================== ADMINDAN FOYDALANUVCHIGA ==================

@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    try:
        original_text = message.reply_to_message.text
        target_id = int(original_text.split("#ID")[-1])
        await bot.copy_message(
            chat_id=target_id,
            from_chat_id=ADMIN_ID,
            message_id=message.message_id
        )
        await message.answer("✅ Javob foydalanuvchiga yuborildi.")
    except:
        await message.answer("❌ Xato: foydalanuvchi ID topilmadi.")

# ================== ISHGA TUSHIRISH ==================

async def main():
    app = web.Application()
    app.router.add_get('/', handle)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

    await asyncio.gather(
        dp.start_polling(bot),
        keep_alive()
    )

if __name__ == "__main__":
    asyncio.run(main())
