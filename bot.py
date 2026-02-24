import os
import yt_dlp
import sqlite3
from datetime import datetime
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
ADMIN_ID = 8059759575       # ايدي حسابك كـ ادمن

# ==============================
# 🗄 DATABASE SETUP
# ==============================

conn = sqlite3.connect("downloads.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    full_name TEXT,
    url TEXT,
    timestamp TEXT
)
""")
conn.commit()

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
            f"https://t.me/{CHANNEL_USERNAME}\n\n"
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
            f"🔒 يجب الاشتراك بالقناة أولاً:\nhttps://t.me/{CHANNEL_USERNAME}"
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

        # ==============================
        # SAVE TO DATABASE
        # ==============================
        cursor.execute(
            "INSERT INTO downloads (user_id, username, full_name, url, timestamp) VALUES (?, ?, ?, ?, ?)",
            (
                user.id,
                user.username,
                user.full_name,
                url,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        conn.commit()

        # ==============================
        # SEND ADMIN NOTIFICATION
        # ==============================
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"""
📥 تحميل جديد

👤 الاسم: {user.full_name}
🆔 ID: {user.id}
🔗 الرابط: {url}
🕒 الوقت: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            )
        except:
            pass

    except Exception as e:
        await update.message.reply_text(
            "❌ حدث خطأ أثناء التحميل.\n"
            "تأكد من صحة الرابط أو جرب رابط آخر."
        )

# ==============================
# 📊 STATS COMMAND
# ==============================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM downloads")
    total = cursor.fetchone()[0]

    await update.message.reply_text(f"📊 عدد الفيديوهات المحملة: {total}")

# ==============================
# 🧠 MAIN APP
# ==============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
