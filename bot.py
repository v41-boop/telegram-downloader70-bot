import os
import logging
import uuid
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# ================== إعدادات ==================
TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = "@ossae"
WEBHOOK_URL = os.getenv("RAILWAY_STATIC_URL")

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
        keyboard = [
            [InlineKeyboardButton("اشترك بالقناة", url="https://t.me/ossae")]
        ]
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
        keyboard = [
            [InlineKeyboardButton("اشترك بالقناة", url="https://t.me/ossae")]
        ]
        await update.message.reply_text(
            "⚠️ لازم تشترك بالقناة",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    url = update.message.text.strip()

    keyboard = [
        [
            InlineKeyboardButton("🎥 فيديو", callback_data=f"video|{url}"),
            InlineKeyboardButton("🎵 صوت MP3", callback_data=f"audio|{url}"),
        ]
    ]

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

    if mode == "video":
        ydl_opts = {
            "format": "best",
            "outtmpl": f"{file_id}.%(ext)s",
        }
    else:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{file_id}.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if mode == "video":
            await query.message.reply_video(video=open(filename, "rb"))
        else:
            mp3_file = f"{file_id}.mp3"
            await query.message.reply_audio(audio=open(mp3_file, "rb"))
            filename = mp3_file

        os.remove(filename)

    except Exception as e:
        await query.message.reply_text("❌ حدث خطأ أثناء التحميل")


# ================== إضافة الهاندلرات ==================
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CallbackQueryHandler(button_handler))


# ================== Webhook ==================
@app.route("/", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"


async def main():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/")


if __name__ == "__main__":
    asyncio.run(main())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
