from telegram.ext import ApplicationBuilder, MessageHandler, filters
import yt_dlp

# 🔹 التوكن مضمن مباشرة
BOT_TOKEN = "8440895412:AAGoiWXxyKreGgHpBKMY9lJXptMAmV78_hg"

# دالة تحميل الفيديوهات
async def download_video(update, context):
    url = update.message.text
    await update.message.reply_text("⏳ جاري التحميل...")

    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await update.message.reply_video(video=open("video.mp4", "rb"))
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {e}")

# إنشاء التطبيق وتشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

app.run_polling()
