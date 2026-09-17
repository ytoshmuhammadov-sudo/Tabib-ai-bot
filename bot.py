import os
import logging
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a world-class medical AI consultant named "Tabib AI", combining expertise of the world's best doctors across ALL medical specialties including:
- Neurology (Adams & Victor, Harrison's level)
- Cardiology, Pulmonology, Gastroenterology
- Orthopedics, Rheumatology, Endocrinology
- Pediatrics, Gynecology, Dermatology
- Psychiatry, Oncology, Urology, and more

You detect the user's language automatically and respond in the SAME language (Uzbek, Russian, or English).

When a user describes symptoms or asks medical questions, respond with this structure:

🔍 **TAHLIL / АНАЛИЗ / ANALYSIS**
Brief analysis of the symptoms

🩺 **EHTIMOLIY SABABLAR / ВОЗМОЖНЫЕ ПРИЧИНЫ / POSSIBLE CAUSES**
List 2-4 possible diagnoses from most to least likely

📋 **TEKSHIRUVLAR / ОБСЛЕДОВАНИЯ / TESTS NEEDED**
Which tests/examinations are recommended

⚠️ **XAVFLI BELGILAR / ОПАСНЫЕ СИМПТОМЫ / RED FLAGS**
When to seek emergency care immediately

💊 **MASLAHAT / СОВЕТ / ADVICE**
General advice (never give specific drug doses)

STRICT RULES:
- NEVER prescribe specific drug doses — always say "consult a doctor"
- If life-threatening symptoms: immediately say "CALL 103/112 NOW"
- End every response with a disclaimer in detected language
- Be thorough but clear and understandable
- Treat as if consulting the world's best specialist in that field"""

user_histories = {}

WELCOME_UZ = """👨‍⚕️ *Tabib AI* ga xush kelibsiz!

Men dunyodagi eng yaxshi shifokorlar darajasida maslahat beradigan tibbiy AI yordamchiman.

🏥 *Qaysi sohada yordam bera olaman:*
• Nevrologiya • Kardiologiya • Gastroenterologiya
• Ortopediya • Endokrinologiya • Pediatriya
• Ginekologiya • Dermatologiya • Psixiatriya
• Va barcha boshqa tibbiy sohalar

📝 Simptomlaringizni yozing yoki quyidagi bo'limlardan tanlang:"""

WELCOME_RU = """👨‍⚕️ Добро пожаловать в *Tabib AI*!

Я медицинский ИИ-ассистент уровня лучших врачей мира.

🏥 *Чем могу помочь:*
• Неврология • Кардиология • Гастроэнтерология
• Ортопедия • Эндокринология • Педиатрия
• Гинекология • Дерматология • Психиатрия
• И все другие медицинские специальности

📝 Опишите симптомы или выберите раздел:"""

WELCOME_EN = """👨‍⚕️ Welcome to *Tabib AI*!

I'm a medical AI assistant at the level of the world's best doctors.

🏥 *I can help with:*
• Neurology • Cardiology • Gastroenterology
• Orthopedics • Endocrinology • Pediatrics
• Gynecology • Dermatology • Psychiatry
• And all other medical specialties

📝 Describe your symptoms or choose a section:"""

def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🧠 Nevro/Neuro", callback_data="spec_neuro"),
            InlineKeyboardButton("❤️ Kardio", callback_data="spec_cardio"),
        ],
        [
            InlineKeyboardButton("🦴 Ortoped", callback_data="spec_ortho"),
            InlineKeyboardButton("🫁 Pulmo", callback_data="spec_pulmo"),
        ],
        [
            InlineKeyboardButton("🍽️ Gastro", callback_data="spec_gastro"),
            InlineKeyboardButton("🧬 Endokrin", callback_data="spec_endo"),
        ],
        [
            InlineKeyboardButton("👶 Pediatriya", callback_data="spec_pedia"),
            InlineKeyboardButton("🧠 Psixiatriya", callback_data="spec_psych"),
        ],
        [
            InlineKeyboardButton("🚨 Favqulodda belgilar", callback_data="emergency"),
        ],
        [
            InlineKeyboardButton("🔄 Suhbatni tozala", callback_data="clear"),
            InlineKeyboardButton("ℹ️ Haqida", callback_data="about"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

SPECIALTY_PROMPTS = {
    "spec_neuro": "Ask me about neurology: headaches, dizziness, seizures, stroke symptoms, numbness, memory problems, etc.",
    "spec_cardio": "Ask me about cardiology: chest pain, palpitations, blood pressure, shortness of breath, etc.",
    "spec_ortho": "Ask me about orthopedics: joint pain, back pain, fractures, sports injuries, etc.",
    "spec_pulmo": "Ask me about pulmonology: cough, breathing difficulties, asthma, etc.",
    "spec_gastro": "Ask me about gastroenterology: stomach pain, digestive issues, nausea, etc.",
    "spec_endo": "Ask me about endocrinology: diabetes, thyroid, hormone issues, etc.",
    "spec_pedia": "Ask me about pediatrics: children's health, development, vaccines, etc.",
    "spec_psych": "Ask me about psychiatry: depression, anxiety, sleep disorders, stress, etc.",
}

EMERGENCY_TEXT = """🚨 *DARHOL 103/112 GA QO'NG'IROQ QILING:*

❤️ *Yurak:*
• Ko'krak og'rig'i + qo'lga tarqalishi
• Nafas qisishi + ter bosishi

🧠 *Miya (FAST):*
• Yuz qiyshayishi
• Qo'l tushib ketishi  
• Nutq buzilishi
• To'satdan paydo bo'lsa → 103!

🩺 *Boshqa holatlar:*
• Ong yo'qotish
• Juda kuchli bosh og'rig'i (birinchi marta)
• Isitma + bo'yin qattiqligi
• Tutqanoq birinchi marta

---
🇷🇺 *Срочно звоните 103/112 при:*
Боли в груди, потере сознания, инсульте, судорогах

🇬🇧 *Call 103/112 immediately for:*
Chest pain, loss of consciousness, stroke symptoms, seizures"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text(
        WELCOME_UZ,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "clear":
        user_histories[user_id] = []
        await query.message.reply_text("✅ Suhbat tozalandi. Yangi savol bering!", reply_markup=get_main_keyboard())
    elif data == "emergency":
        await query.message.reply_text(EMERGENCY_TEXT, parse_mode='Markdown', reply_markup=get_main_keyboard())
    elif data == "about":
        about_text = """ℹ️ *Tabib AI haqida*

🤖 Men Claude AI asosida ishlaychi tibbiy konsultant botman.

📚 *Bilim bazam:*
• Harrison's Principles of Internal Medicine
• Adams & Victor's Neurology
• Dunyodagi eng yaxshi tibbiy qo'llanmalar

⚕️ *Muhim eslatma:*
Bu bot maslahat uchun. Yakuniy tashxis va davolash uchun albatta shifokorga murojaat qiling.

💻 Versiya: 1.0 | Tabib AI Pro"""
        await query.message.reply_text(about_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    elif data in SPECIALTY_PROMPTS:
        specialty_names = {
            "spec_neuro": "🧠 Nevrologiya",
            "spec_cardio": "❤️ Kardiologiya", 
            "spec_ortho": "🦴 Ortopediya",
            "spec_pulmo": "🫁 Pulmonologiya",
            "spec_gastro": "🍽️ Gastroenterologiya",
            "spec_endo": "🧬 Endokrinologiya",
            "spec_pedia": "👶 Pediatriya",
            "spec_psych": "🧠 Psixiatriya",
        }
        name = specialty_names.get(data, "")
        await query.message.reply_text(
            f"{name} bo'limini tanladingiz.\n\nSavolingizni yozing — men dunyoning eng yaxshi {name.split()[1]} mutaxassisi sifatida javob beraman! 👨‍⚕️",
            reply_markup=get_main_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    user_histories[user_id].append({"role": "user", "content": user_text})

    # Keep last 10 messages for context
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )
        reply = response.content[0].text
        user_histories[user_id].append({"role": "assistant", "content": reply})

        # Split long messages
        if len(reply) > 4000:
            parts = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown', reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text(reply, parse_mode='Markdown', reply_markup=get_main_keyboard())

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring yoki /start bosing.",
            reply_markup=get_main_keyboard()
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Tabib AI bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
