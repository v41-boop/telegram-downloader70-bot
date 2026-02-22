import os
import logging
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

# 🔴 حط توكنك هنا بدل YOUR_TOKEN
TOKEN = "8440895412:AAGoiWXxyKreGgHpBKMY9lJXptMAmV78_hg"

CHANNEL_USERNAME = "@ossae"

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()


# التحقق من الاشتراك الاجباري
async def check_subscription(user_id):
    try:
        member = await telegram_app.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# start
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


# استقبال الرابط
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

    url = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("🎥 تحميل فيديو", callback_data=f"video|{url}"),
            InlineKeyboardButton("🎵 تحميل صوت MP3", callback_data=f"audio|{url}"),
        ]
    ]

    await update.message.reply_text(
        "اختر نوع التحميل:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# معالجة الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode, url = query.data.split("|")

    await query.message.reply_text("⏳ جاري التحميل...")

    if mode == "video":
        ydl_opts = {
            "format": "best[ext=mp4]",
            "outtmpl": "video.%(ext)s",
        }
    else:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "audio.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if mode == "video":
        await query.message.reply_video(video=open("video.mp4", "rb"))
        os.remove("video.mp4")
    else:
        await query.message.reply_audio(audio=open("audio.mp3", "rb"))
        os.remove("audio.mp3")


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CallbackQueryHandler(button_handler))


@app.route("/", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"


if __name__ == "__main__":
    telegram_app.initialize()
    telegram_app.bot.set_webhook("https://YOUR_RAILWAY_URL.up.railway.app/")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
