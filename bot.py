import os
import uuid
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import yt_dlp
import asyncio

# ================== الإعدادات ==================
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # رابط السيرفر HTTPS
CHANNEL_USERNAME = "@ossae"

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()


# ================== تحقق الاشتراك ==================
async def check_subscription(user_id):
    try:
        member = await telegram_app.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ================== /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_subscription(user.id):
        keyboard = [[InlineKeyboardButton("اشترك بالقناة", url="https://t.me/ossae")]]
        await update.message.reply_text(
            "⚠️ لازم تشترك بالقناة حتى تستخدم البوت",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    await update.message.reply_text("📥 ارسل رابط الفيديو")


# ================== استقبال الرابط ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_subscription(user.id):
        keyboard = [[InlineKeyboardButton("اشترك بالقناة", url="https://t.me/ossae")]]
        await update.message.reply_text(
            "⚠️ لازم تشترك بالقناة",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    url = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("🎥 فيديو", callback_data=f"video|{url}")]]
    await update.message.reply_text(
        "اختر نوع التحميل:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ================== معالجة الأزرار ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode, url = query.data.split("|")
    await query.message.reply_text("⏳ جاري التحميل...")

    file_id = str(uuid.uuid4())

    ydl_opts = {
        "format": "best",
        "outtmpl": f"{file_id}.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # البحث عن ملف الفيديو بعد التحميل
        filename = next(
            (f for f in os.listdir(".") if f.startswith(file_id) and f.endswith((".mp4", ".mkv", ".webm"))),
            None
        )
        if filename:
            await query.message.reply_video(video=open(filename, "rb"))
            os.remove(filename)
        else:
            await query.message.reply_text("❌ لم يتم العثور على ملف الفيديو")

    except Exception as e:
        logging.error(e)
        await query.message.reply_text("❌ حدث خطأ أثناء التحميل")


# ================== إضافة الهاندلرات ==================
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CallbackQueryHandler(button_handler))


# ================== Webhook ==================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.update_queue.put(update))
    return "OK"


if __name__ == "__main__":
    # ضبط Webhook
    asyncio.run(telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}"))
    logging.info(f"Webhook set to: {WEBHOOK_URL}/{TOKEN}")

    # تشغيل Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
