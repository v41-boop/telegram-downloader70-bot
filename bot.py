import os
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==============================
# 🔐 ENV VARIABLES CHECK
# ==============================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN NOT FOUND IN RAILWAY VARIABLES")

CHANNEL_USERNAME = "ossae"  # بدون @

# ==============================
# ✅ CHECK SUBSCRIPTION
# ==============================

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=f"@{CHANNEL_USERNAME}",
            user_id=user_id,
        )
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


# ==============================
# 🚀 START COMMAND
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    is_subscribed = await check_subscription(user.id, context)

    if not is_subscribed:
        await update.message.reply_text(
            "🔒 لاستخدام البوت يجب الاشتراك بالقناة أولاً:\n"
            "https://t.me/ossae\n\n"
            "وبعد الاشتراك اضغط /start مرة ثانية."
        )
        return

    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}\n\n"
        "🤖 بوت تحميل الفيديوهات الاحترافي.\n"
        "📥 أرسل رابط أي فيديو من مواقع التواصل\n"
        "🎬 وسيتم تنزيله بأعلى جودة متاحة."
    )


# ==============================
# 🎬 DOWNLOAD HANDLER
# ==============================

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text

    is_subscribed = await check_subscription(user.id, context)

    if not is_subscribed:
        await update.message.reply_text(
            "🔒 يجب الاشتراك بالقناة أولاً:\nhttps://t.me/ossae"
        )
        return

    await update.message.reply_text("⏳ جاري تحميل الفيديو بأعلى جودة...")

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "video.%(ext)s",
        "merge_output_format": "mp4",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        await update.message.reply_video(
            video=open(file_name, "rb"),
            supports_streaming=True
        )

        os.remove(file_name)

    except Exception as e:
        await update.message.reply_text(
            "❌ حدث خطأ أثناء التحميل.\n"
            "تأكد من صحة الرابط أو جرب رابط آخر."
        )


# ==============================
# 🧠 MAIN APP
# ==============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("✅ Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
