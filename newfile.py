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
# Xavfsizlik uchun tokenni o'zgaruvchidan olamiz
API_TOKEN = os.getenv("7773701126:AAFX4uHDUo3y1brZa1Y84OUA7SOCaJr1Zic") 
ADMIN_ID = int(os.getenv("ADMIN_ID", 7751709985))
CHANNEL_USERNAME = "@Tarixchilar_1IDUM"

TEST_URL = "https://ibrohimtoshpolatov44-prog.github.io/Milliy_Sertifikat_Tarix1/"
JAHON_TARIXI_7_URL = "https://ibrohimtoshpolatov44-prog.github.io/7-sinf_JahonTarixi_v1/"

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

# ================= WEB SERVER (RENDER UCHUN) =================
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# ================= PDF & IMAGE FUNKSIYALARI =================
def create_pdf(text, user_id):
    if not os.path.exists("pdfs"): os.makedirs("pdfs")
    filepath = f"pdfs/{user_id}.pdf"
    
    # HYSMyeongJo o'rniga standartroq font yoki ro'yxatdan o'tgan font ishlating
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
        font_name = 'HYSMyeongJo-Medium'
    except:
        font_name = 'Helvetica' # Zaxira font

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    style = ParagraphStyle(name='Uz', fontName=font_name, fontSize=12)
    doc.build([Paragraph(text, style)])
    return filepath

def create_note_image(text, user_id):
    if not os.path.exists("notes"): os.makedirs("notes")
    width, height = 800, 1000
    image = Image.new("RGB", (width, height), "#fdf6e3")
    draw = ImageDraw.Draw(image)

    # Chiziqlar chizish
    for y in range(120, height, 60):
        draw.line((60, y, width-60, y), fill="#c2b280", width=2)

    try:
        font = ImageFont.truetype("arial.ttf", 35) # O'lcham biroz kichraytirildi
    except:
        font = ImageFont.load_default()

    # Matnni bir nechta qatorga bo'lish logikasi qo'shilishi mumkin, hozircha oddiy:
    draw.text((100, 150), text[:500], fill="black", font=font)
    filepath = f"notes/{user_id}.png"
    image.save(filepath)
    return filepath

# ================= MENYU =================
def get_main_menu():
    kb = [
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
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(f"Assalomu alaykum {message.from_user.full_name}! 👋\nTarix botiga xush kelibsiz.", reply_markup=get_main_menu())

@dp.message(F.text == "📚 Tarix o‘zi nima?")
async def tarix_info(message: types.Message):
    await message.answer("📜 Tarix — insoniyat xotirasi.\n⏳ O‘tgan kunlar sabog‘i.\n🏛 Buyuk davlatlar va allomalar hikoyasi.")

@dp.message(F.text == "📢 Kanal")
async def channel_info(message: types.Message):
    await message.answer(f"Rasmiy kanalimiz: {CHANNEL_USERNAME}")

# PDF Logic
@dp.message(F.text == "📄 Text to PDF")
async def ask_pdf(message: types.Message, state: FSMContext):
    await message.answer("PDF ga aylantirish uchun matn yuboring (max 500 belgi):")
    await state.set_state(PDFState.waiting_text)

@dp.message(PDFState.waiting_text)
async def process_pdf(message: types.Message, state: FSMContext):
    msg = await message.answer("Fayl tayyorlanmoqda... ⏳")
    filepath = create_pdf(message.text, message.from_user.id)
    await message.answer_document(FSInputFile(filepath))
    os.remove(filepath)
    await msg.delete()
    await state.clear()

# Note Logic
@dp.message(F.text == "📝 Daftarga Yoz")
async def ask_note(message: types.Message, state: FSMContext):
    await message.answer("Daftar sahifasiga yozish uchun matn yuboring:")
    await state.set_state(NoteState.waiting_text)

@dp.message(NoteState.waiting_text)
async def process_note(message: types.Message, state: FSMContext):
    msg = await message.answer("Rasm chizilmoqda... 🎨")
    filepath = create_note_image(message.text, message.from_user.id)
    await message.answer_photo(FSInputFile(filepath))
    os.remove(filepath)
    await msg.delete()
    await state.clear()

@dp.message(F.text == "📬 Kanaldan Post")
async def random_post(message: types.Message):
    try:
        # Tasodifiy post olish (Kanalda kamida 200 ta post bor deb hisoblaymiz)
        msg_id = random.randint(1, 200)
        await bot.copy_message(message.chat.id, CHANNEL_USERNAME, msg_id)
    except Exception:
        await message.answer("Hozircha post topilmadi yoki bot kanalga a'zo emas.")

@dp.message(F.text == "⭐ Botni baholash")
async def rate_bot(message: types.Message):
    buttons = []
    # Tugmalarni qatorga 5 tadan joylash
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"rate_{i}"))
        if i % 5 == 0:
            buttons.append(row)
            row = []
    await message.answer("Botni baholang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("rate_"))
async def process_rating(call: types.CallbackQuery):
    rating = int(call.data.split("_")[1])
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ratings VALUES (?, ?)", (call.from_user.id, rating))
    conn.commit()
    conn.close()
    await call.answer("Rahmat!")
    await call.message.edit_text(f"Siz {rating} ball berdingiz. Rahmat! ✨")
    await bot.send_message(ADMIN_ID, f"🔔 Yangi baho!\n👤 {call.from_user.full_name}: {rating}/10")

# ================= MAIN =================
async def main():
    init_db()
    # Web serverni orqa fonda ishga tushirish
    await start_web_server()
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
    
