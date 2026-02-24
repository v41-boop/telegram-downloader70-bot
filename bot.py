import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "ossae"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "🔒 للاستخدام يجب الاشتراك بالقناة أولاً:\n"
                "https://t.me/ossae\n\n"
                "وبعد الاشتراك اضغط /start مرة ثانية."
            )
            return
    except:
        await update.message.reply_text("حدث خطأ بالتحقق من الاشتراك.")
        return

    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}\n\n"
        "🤖 هذا بوت تنزيل الفيديوهات.\n"
        "📥 أرسل رابط أي فيديو من مواقع التواصل\n"
        "🎬 وسيتم تنزيله بأعلى جودة ممكنة."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text("🔒 يجب الاشتراك بالقناة أولاً:\nhttps://t.me/ossae")
            return
    except:
        await update.message.reply_text("خطأ في التحقق من الاشتراك.")
        return

    await update.message.reply_text("⏳ جاري تحميل الفيديو...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        await update.message.reply_video(video=open(file_name, 'rb'))
        os.remove(file_name)

    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ أثناء التحميل.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

app.run_polling()
