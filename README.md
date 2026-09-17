# Tabib AI — Telegram Bot

## Railway.app da ishlatish (BEPUL, telefonda ham bo'ladi)

### 1-qadam: GitHub
1. github.com ga kiring (bepul ro'yxatdan o'ting)
2. "New repository" → nom: `tabib-ai-bot`
3. Bu 3 faylni yuklang: bot.py, requirements.txt, railway.json

### 2-qadam: Railway
1. railway.app ga kiring → "Login with GitHub"
2. "New Project" → "Deploy from GitHub repo"
3. tabib-ai-bot ni tanlang

### 3-qadam: Environment Variables (MUHIM!)
Railway dashboard → Variables bo'limiga qo'shing:
```
ANTHROPIC_API_KEY = sk-ant-api03-...
TELEGRAM_TOKEN = 8908681539:AAF7...
```

### 4-qadam: Deploy
"Deploy" tugmasini bosing → 2-3 daqiqada bot ishga tushadi!

## Bot buyruqlari
- /start — Botni ishga tushirish
- Ixtiyoriy matn → tibbiy konsultatsiya

## Eslatma
Bot maslahat uchun. Yakuniy tashxis uchun vrach ko'rigidan o'ting.
