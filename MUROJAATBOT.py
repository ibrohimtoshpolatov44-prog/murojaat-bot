import asyncio
from aiogram import Bot, Dispatcher, types, F

# O'z ma'lumotlaringizni kiriting
API_TOKEN = '7773701126:AAEIsIWkcerz8URbr1R3SBNuJrvAfBeIqzs'
ADMIN_ID = 7751709985  # O'zingizning ID raqamingizni yozing

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# /start buyrug'i uchun
@dp.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.reply("Assalomu alaykum! Murojaatingizni yozing, men uni adminga yetkazaman.")

# Foydalanuvchi xabar yozsa, uni adminga yuborish
@dp.message()
async def forward_to_admin(message: types.Message):
    # Adminga xabar yuborish
    text = (f"Yangi murojaat!\n"
            f"Kimdan: {message.from_user.full_name}\n"
            f"ID: {message.from_user.id}\n"
            f"Xabar: {message.text}")
    
    await bot.send_message(chat_id=ADMIN_ID, text=text)
    
    # Foydalanuvchiga javob qaytarish
    await message.answer("Xabaringiz adminga yetkazildi. Tez orada javob beramiz!")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
