# bot.py
import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# ====== إعداد المتغيرات ======
TOKEN = os.getenv("TOKEN")  # ضع توكن بوتك
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # الرابط الكامل للموقع بدون TOKEN، مثال: https://mybot.up.railway.app

# ====== إعداد Flask ======
app = Flask(__name__)

# ====== إعداد البوت ======
telegram_app = Application.builder().token(TOKEN).build()

# مثال أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً! البوت جاهز ويعمل بالـ Webhook 🚀")

telegram_app.add_handler(CommandHandler("start", start))

# ====== Route لـ Webhook ======
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if data:
        update = Update.de_json(data, telegram_app.bot)
        asyncio.run(telegram_app.update_queue.put(update))
    return "OK"

# ====== تشغيل البوت + Flask ======
async def main():
    # initialize البوت
    await telegram_app.initialize()
    # ضبط webhook
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print(f"✅ Webhook set to: {WEBHOOK_URL}/{TOKEN}")
    # بدء البوت بدون polling
    await telegram_app.start()
    print("🚀 البوت جاهز ويستقبل التحديثات")
    # تشغيل Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    asyncio.run(main())
