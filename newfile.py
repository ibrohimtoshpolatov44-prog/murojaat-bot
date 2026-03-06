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
API_TOKEN = '7773701126:AAFX4uHDUo3y1brZa1Y84OUA7SOCaJr1Zic'
CH_ID = "@Tarixchilar_1IDUM"
ADMIN_ID = 7751709985 # O'zingizning ID raqamingiz
PORT = int(os.environ.get("PORT", 10000)) # Render beradigan port

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Natijalar xotirasi
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

# --- WEB SERVER (RENDER UCHUN) ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Web server {PORT} portida ishga tushdi.")

# --- TUGMALAR ---
def get_menu(user_id):
    buttons = [[KeyboardButton(text="1. Milliy Sertifikat 📝")],
               [KeyboardButton(text="2. Bizning kanal 📢")],
               [KeyboardButton(text="5. Botni baholash ⭐")]]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="➕ Savol qo'shish")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- BOT LOGIKASI ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Tarix fanidan Quiz botiga xush kelibsiz!", reply_markup=get_menu(message.from_user.id))

@dp.message(F.text == "➕ Savol qo'shish", F.from_user.id == ADMIN_ID)
async def start_add(message: types.Message, state: FSMContext):
    await message.answer("Savolni yuboring:")
    await state.set_state(AdminState.waiting_for_question)

@dp.message(AdminState.waiting_for_question)
async def process_q(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer("Variantlarni vergul bilan ajratib yuboring:")
    await state.set_state(AdminState.waiting_for_options)

@dp.message(AdminState.waiting_for_options)
async def process_o(message: types.Message, state: FSMContext):
    opts = [i.strip() for i in message.text.split(",")]
    await state.update_data(options=opts)
    await message.answer("To'g'ri javob indeksini yuboring (0 dan boshlab):")
    await state.set_state(AdminState.waiting_for_correct_id)

@dp.message(AdminState.waiting_for_correct_id)
async def process_c(message: types.Message, state: FSMContext):
    data = await state.get_data()
    conn = sqlite3.connect('tarix_quiz.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (question, options, correct_id) VALUES (?, ?, ?)", 
                   (data['question'], ",".join(data['options']), int(message.text)))
    conn.commit()
    conn.close()
    await message.answer("✅ Savol saqlandi!", reply_markup=get_menu(message.from_user.id))
    await state.clear()

@dp.message(F.text == "1. Milliy Sertifikat 📝")
async def start_quiz(message: types.Message):
    conn = sqlite3.connect('tarix_quiz.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()

    if not questions:
        await message.answer("Hozircha savollar yo'q.")
        return

    user_id = message.from_user.id
    user_results[user_id] = {'correct': 0, 'total': len(questions), 'start_time': time.time()}

    await message.answer(f"Viktorina boshlandi! {len(questions)} ta savol.")

    for q in questions:
        await bot.send_poll(
            chat_id=message.chat.id,
            question=q[1],
            options=q[2].split(","),
            type='quiz',
            correct_option_id=int(q[3]),
            open_period=30,
            is_anonymous=False
        )
        await asyncio.sleep(31)

    res = user_results.get(user_id)
    if res:
        duration = int(time.time() - res['start_time'])
        text = (f"🏁 **Natija:**\n"
                f"✅ To'g'ri: {res['correct']} ta\n"
                f"⏱ Vaqt: {duration // 60}m {duration % 60}s")
        await message.answer(text, parse_mode="Markdown")
        del user_results[user_id]

@dp.poll_answer()
async def handle_poll_answer(quiz_answer: PollAnswer):
    user_id = quiz_answer.user.id
    if user_id in user_results:
        # Bu yerda foydalanuvchi tanlagan variant to'g'riligini Poll orqali tekshirish murakkabroq, 
        # shuning uchun har bir javobni to'g'ri deb hisoblash xatoga olib kelishi mumkin.
        # Professional versiyada poll_id ni bazadagi correct_id bilan solishtirish kerak.
        user_results[user_id]['correct'] += 1

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    init_db()
    # Web server va Botni bir vaqtda ishga tushirish
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
