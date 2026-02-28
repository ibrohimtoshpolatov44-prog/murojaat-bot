import asyncio
import logging
import aiohttp
import sqlite3
import os
import random
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, FSInputFile
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4

# Image
from PIL import Image, ImageDraw, ImageFont

# ================= SOZLAMALAR =================
API_TOKEN = os.getenv("7773701126:AAEIsIWkcerz8URbr1R3SBNuJrvAfBeIqzs")  # GitHub safe uchun .env dan oling
ADMIN_ID = int(os.getenv("ADMIN_ID", 7751709985))
CHANNEL_USERNAME = "@Tarixchilar_1IDUM"

TEST_URL = "https://ibrohimtoshpolatov44-prog.github.io/Milliy_Sertifikat_Tarix1/"
JAHON_TARIXI_7_URL = "https://ibrohimtoshpolatov44-prog.github.io/7-sinf_JahonTarixi_v1/"
RENDER_URL = "https://murojaat-bot-1-jqjg.onrender.com"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= STATE =================
class PDFState(StatesGroup):
    waiting_text = State()

class NoteState(StatesGroup):
    waiting_text = State()

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, full_name TEXT, username TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS ratings (user_id INTEGER, rating INTEGER)")
    conn.commit()
    conn.close()

def add_user(user_id, full_name, username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", (user_id, full_name, username))
    conn.commit()
    conn.close()

# ================= KEEP ALIVE =================
async def keep_alive():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(RENDER_URL)
            except:
                pass
            await asyncio.sleep(600)

async def handle(request):
    return web.Response(text="Bot ishlayapti!")

# ================= PDF =================
def create_pdf(text, user_id):
    os.makedirs("pdfs", exist_ok=True)
    filepath = f"pdfs/{user_id}.pdf"

    pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    style = ParagraphStyle(name='Uz', fontName='HYSMyeongJo-Medium', fontSize=12)
    doc.build([Paragraph(text, style)])
    return filepath

# ================= DAFTARGA YOZ =================
def create_note_image(text, user_id):
    os.makedirs("notes", exist_ok=True)
    width, height = 800, 1000
    image = Image.new("RGB", (width, height), "#fdf6e3")
    draw = ImageDraw.Draw(image)

    for y in range(120, height, 60):
        draw.line((60, y, width-60, y), fill="#c2b280", width=2)

    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except:
        font = ImageFont.load_default()

    draw.text((100, 150), text, fill="black", font=font)
    filepath = f"notes/{user_id}.png"
    image.save(filepath)
    return filepath

# ================= MENYU =================
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Milliy Sertifikat testi", web_app=WebAppInfo(url=TEST_URL)),
                KeyboardButton(text="🌍 7-sinf Jahon Tarixi", web_app=WebAppInfo(url=JAHON_TARIXI_7_URL))
            ],
            [
                KeyboardButton(text="📄 Text to PDF"),
                KeyboardButton(text="📝 Daftarga Yoz")
            ],
            [
                KeyboardButton(text="📬 Kanaldan Post"),
                KeyboardButton(text="⭐ Botni baholash")
            ],
            [
                KeyboardButton(text="📚 Tarix o‘zi nima?"),
                KeyboardButton(text="📢 Kanal")
            ]
        ],
        resize_keyboard=True
    )

# ================= START =================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer("Xush kelibsiz 👋", reply_markup=get_main_menu())

# ================= TARIX =================
@dp.message(F.text == "📚 Tarix o‘zi nima?")
async def tarix_info(message: types.Message):
    await message.answer(
        "📜 Tarix — insoniyat xotirasi.\n"
        "⏳ O‘tgan kunlar sabog‘i.\n"
        "🏛 Buyuk davlatlar va allomalar hikoyasi.\n"
        "🌟 Tarixni bilgan inson kelajakni ongli quradi."
    )

# ================= PDF =================
@dp.message(F.text == "📄 Text to PDF")
async def ask_pdf(message: types.Message, state: FSMContext):
    await message.answer("Matn yuboring (500 belgi).")
    await state.set_state(PDFState.waiting_text)

@dp.message(PDFState.waiting_text)
async def process_pdf(message: types.Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("❌ 500 belgidan oshmasin.")
        return
    filepath = create_pdf(message.text, message.from_user.id)
    await message.answer_document(FSInputFile(filepath))
    os.remove(filepath)
    await state.clear()

# ================= DAFTAR =================
@dp.message(F.text == "📝 Daftarga Yoz")
async def ask_note(message: types.Message, state: FSMContext):
    await message.answer("Yozmoqchi bo‘lgan matnni yuboring.")
    await state.set_state(NoteState.waiting_text)

@dp.message(NoteState.waiting_text)
async def process_note(message: types.Message, state: FSMContext):
    filepath = create_note_image(message.text, message.from_user.id)
    await message.answer_photo(FSInputFile(filepath))
    os.remove(filepath)
    await state.clear()

# ================= RANDOM POST =================
@dp.message(F.text == "📬 Kanaldan Post")
async def random_post(message: types.Message):
    try:
        msg_id = random.randint(1, 200)
        await bot.copy_message(message.chat.id, CHANNEL_USERNAME, msg_id)
    except:
        await message.answer("Bot kanal admini emas yoki post topilmadi.")

# ================= BAHOLASH =================
@dp.message(F.text == "⭐ Botni baholash")
async def rate_bot(message: types.Message):
    buttons = [[InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"rate_{i}")] for i in range(1, 11)]
    await message.answer("Baholang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("rate_"))
async def process_rating(call: types.CallbackQuery):
    rating = int(call.data.split("_")[1])
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ratings VALUES (?, ?)", (call.from_user.id, rating))
    conn.commit()
    conn.close()
    await call.message.delete()
    await call.message.answer("Rahmat ⭐")
    await bot.send_message(ADMIN_ID, f"{call.from_user.full_name} baho berdi: {rating}/10")

# ================= RUN =================
async def main():
    init_db()
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))  # Render $PORT
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await asyncio.gather(dp.start_polling(bot), keep_alive())

if __name__ == "__main__":
    asyncio.run(main())
