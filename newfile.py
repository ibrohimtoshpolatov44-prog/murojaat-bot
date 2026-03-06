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
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                            InlineKeyboardMarkup, InlineKeyboardButton, PollAnswer)

# --- SOZLAMALAR ---
API_TOKEN = '7773701126:AAFX4uHDUo3y1brZa1Y84OUA7SOCaJr1Zic'
CH_ID = "@Tarixchilar_1IDUM"
ADMIN_ID = 7751709985
PORT = int(os.environ.get("PORT", 10000))

BTN_QUIZ = "1. Milliy Sertifikat 📝"
BTN_CHAN = "2. Bizning kanal 📢"
BTN_RATE = "5. Botni baholash ⭐"
BTN_ADD  = "➕ Savol qo'shish"

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

# --- WEB SERVER ---
async def handle_ping(request):
    return web.Response(text="Bot is live!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# --- TUGMALAR ---
def get_menu(user_id):
    kb = [
        [KeyboardButton(text=BTN_QUIZ)],
        [KeyboardButton(text=BTN_CHAN)],
        [KeyboardButton(text=BTN_RATE)]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text=BTN_ADD)])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- START ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Tarix fanidan Quiz botiga xush kelibsiz!",
        reply_markup=get_menu(message.from_user.id)
    )

# --- QUIZ ---
@dp.message(F.text == BTN_QUIZ)
async def start_quiz(message: types.Message):
    conn = sqlite3.connect('tarix_quiz.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()

    if not questions:
        await message.answer("Hozircha bazada savollar yo'q. Admin savol qo'shishi kerak.")
        return

    await message.answer(f"Viktorina boshlandi! Savollar soni: {len(questions)}")

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

# --- KANAL ---
@dp.message(F.text == BTN_CHAN)
async def show_chan(message: types.Message):
    await message.answer(f"Bizning kanal: {CH_ID}\nLink: https://t.me/{CH_ID[1:]}")

# --- BAHOLASH ---
@dp.message(F.text == BTN_RATE)
async def rate_bot(message: types.Message):
    btns = [
        [InlineKeyboardButton(text=str(i), callback_data=f"r_{i}") for i in range(1,6)],
        [InlineKeyboardButton(text=str(i), callback_data=f"r_{i}") for i in range(6,11)]
    ]

    await message.answer(
        "Botni baholang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )

@dp.callback_query(F.data.startswith("r_"))
async def process_rate(call: types.CallbackQuery):
    await call.message.edit_text("Bahoyingiz uchun rahmat! ✨")

# --- ADMIN ---
@dp.message(F.text == BTN_ADD)
async def admin_add(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("Yangi savolni yuboring:")
    await state.set_state(AdminState.waiting_for_question)

@dp.message(AdminState.waiting_for_question)
async def proc_q(message: types.Message, state: FSMContext):
    await state.update_data(q=message.text)

    await message.answer(
        "Variantlarni vergul bilan yuboring (masalan: 1336,1405,1200)"
    )

    await state.set_state(AdminState.waiting_for_options)

@dp.message(AdminState.waiting_for_options)
async def proc_o(message: types.Message, state: FSMContext):
    await state.update_data(o=message.text)

    await message.answer(
        "To'g'ri javob indeksini yuboring (0 dan boshlanadi)"
    )

    await state.set_state(AdminState.waiting_for_correct_id)

@dp.message(AdminState.waiting_for_correct_id)
async def proc_c(message: types.Message, state: FSMContext):
    data = await state.get_data()

    conn = sqlite3.connect('tarix_quiz.db')
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO questions (question, options, correct_id) VALUES (?, ?, ?)",
        (data['q'], data['o'], int(message.text))
    )

    conn.commit()
    conn.close()

    await message.answer(
        "✅ Savol saqlandi!",
        reply_markup=get_menu(message.from_user.id)
    )

    await state.clear()

# --- MAIN ---
async def main():
    init_db()

    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
