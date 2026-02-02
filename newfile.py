import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 1. SOZLAMALAR (Bularni albatta o'zgartiring)
API_TOKEN = '7773701126:AAEIsIWkcerz8URbr1R3SBNuJrvAfBeIqzs'
ADMIN_ID = 7751709985 # @userinfobot orqali olgan ID-ingiz
CHANNEL_USERNAME = "@Tarixchilar_1IDUM" # Kanal linki

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# A'zolikni tekshirish funksiyasi
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # Agar a'zo bo'lsa yoki admin bo'lsa True qaytaradi
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        return False

# Obuna tugmasi
def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])
    return keyboard

# /start xabari
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Xush kelibsiz, Admin! Foydalanuvchilar xabari shu yerga keladi.")
        return

    if await is_subscribed(message.from_user.id):
        await message.answer("Assalomu alaykum! Savolingizni yozib qoldiring.")
    else:
        await message.answer("Botdan foydalanish uchun kanalimizga a'zo bo'ling:", reply_markup=get_sub_keyboard())

# Tekshirish tugmasi bosilganda
@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.edit_text("Rahmat! Endi savolingizni yuborishingiz mumkin.")
    else:
        await call.answer("Siz hali a'zo emassiz!", show_alert=True)

# FOYDALANUVCHIDAN ADMINGA (Faqat a'zolarga ruxsat)
@dp.message(F.chat.id != ADMIN_ID)
async def handle_user_msg(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("Xabar yuborish uchun kanalga a'zo bo'lishingiz shart.", reply_markup=get_sub_keyboard())
        return

    # Adminga xabarni yuborishda foydalanuvchi ID-sini matn ichiga yashiramiz (Maxfiylik muammosini hal qiladi)
    user_info = f"#ID{message.from_user.id}"
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👤 **Kimdan:** {message.from_user.full_name}\n🆔 **ID:** `{message.from_user.id}`\n\n💬 **Xabar:**\n{message.text if message.text else '[Media xabar]'}\n\n{user_info}",
        parse_mode="Markdown"
    )

# ADMINDAN FOYDALANUVCHIGA (Reply orqali)
@dp.message(F.chat.id == ADMIN_ID, F.reply_to_message)
async def handle_admin_reply(message: types.Message):
    reply_text = message.reply_to_message.text
    
    # Kelgan xabardan foydalanuvchi ID-sini qidiramiz
    if "#ID" in reply_text:
        try:
            target_user_id = int(reply_text.split("#ID")[-1])
            await bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=ADMIN_ID,
                message_id=message.message_id
            )
            await message.answer("✅ Javobingiz yuborildi.")
        except Exception as e:
            await message.answer(f"❌ Yuborishda xato: {e}")
    else:
        await message.answer("❌ Bu xabar orqali javob yozib bo'lmaydi. ID topilmadi.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
