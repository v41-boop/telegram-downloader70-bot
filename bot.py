import os
import uuid
import logging
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

# ================== الإعدادات ==================
TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = "@ossae"

logging.basicConfig(level=logging.INFO)

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
            os.remove(filename)
        else:
            mp3_file = f"{file_id}.mp3"
            await query.message.reply_audio(audio=open(mp3_file, "rb"))
            os.remove(mp3_file)

    except Exception as e:
        await query.message.reply_text("❌ حدث خطأ أثناء التحميل")


# ================== إضافة الهاندلرات ==================
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CallbackQueryHandler(button_handler))


# ================== تشغيل البوت (Polling) ==================
if __name__ == "__main__":
    telegram_app.run_polling()
