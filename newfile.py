import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# 1. SOZLAMALAR
API_TOKEN = '7773701126:AAEIsIWkcerz8URbr1R3SBNuJrvAfBeIqzs'
ADMIN_ID = 7751709985
CHANNEL_USERNAME = "@Tarixchilar_1IDUM"
# Siz bergan yangi URL
TEST_URL = "https://ibrohimtoshpolatov44-prog.github.io/Milliy_Sertifikat_Tarix1/"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- KLAVIATURALAR ---

# Asosiy Menyu (Tugmalar ko'rinishi uchun)
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Tarix Milliy Sertifikat testi", web_app=WebAppInfo(url=TEST_URL))],
            [KeyboardButton(text="📢 Bizning kanal")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Kanalga obuna bo'lish tugmasi
def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])
    return keyboard

# --- FUNKSIYALAR ---

async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Obunani tekshirishda xato: {e}")
        return False

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Xush kelibsiz, Admin! Menyu aktivlashtirildi.", reply_markup=get_main_menu())
        return

    if await is_subscribed(message.from_user.id):
        await message.answer(
            "Assalomu alaykum! Savolingizni yozib qoldiring yoki testni boshlang 👇", 
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "Botdan foydalanish uchun kanalimizga a'zo bo'ling:", 
            reply_markup=get_sub_keyboard()
        )

@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer(
            "Rahmat! Endi menyudan foydalanishingiz mumkin.", 
            reply_markup=get_main_menu()
        )
    else:
        await call.answer("Siz hali kanalga a'zo emassiz! ❌", show_alert=True)

# Kanal haqida ma'lumot
@dp.message(F.text == "📢 Bizning kanal")
async def channel_info(message: types.Message):
    await message.answer(f"Bizning rasmiy kanalimiz: {CHANNEL_USERNAME}\n\nA'zo bo'lganingiz uchun rahmat!")

# FOYDALANUVCHIDAN ADMINGA XABAR
@dp.message(F.chat.id != ADMIN_ID)
async def handle_user_msg(message: types.Message):
    # Agar foydalanuvchi WebApp tugmasini bossa, bu xabar deb hisoblanmaydi
    if message.text == "📝 Tarix Milliy Sertifikat testi":
        return

    if not await is_subscribed(message.from_user.id):
        await message.answer("Xabar yuborish uchun kanalga a'zo bo'ling.", reply_markup=get_sub_keyboard())
        return

    user_info = f"#ID{message.from_user.id}"
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👤 **Kimdan:** {message.from_user.full_name}\n🆔 **ID:** `{message.from_user.id}`\n\n💬 **Xabar:**\n{message.text if message.text else '[Media]'}\n\n{user_info}",
        parse_mode="Markdown"
    )
    await message.answer("✅ Xabaringiz adminga yuborildi. Tezp orada javob olasiz.")

# ADMINDAN FOYDALANUVCHIGA JAVOB
@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    reply_text = message.reply_to_message.text
    
    if reply_text and "#ID" in reply_text:
        try:
            target_user_id = int(reply_text.split("#ID")[-1])
            await bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=ADMIN_ID,
                message_id=message.message_id
            )
            await message.answer("✅ Javobingiz yuborildi.")
        except Exception as e:
            await message.answer(f"❌ Xato: Foydalanuvchi botni bloklagan bo'lishi mumkin.")
    else:
        await message.answer("❌ Javob yozish uchun foydalanuvchi xabariga 'Reply' qiling.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
