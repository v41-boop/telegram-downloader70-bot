import os
import uuid
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

# ================== الإعدادات ==================
TOKEN = os.getenv("TOKEN")  # ضع توكن البوت هنا في Variables
CHANNEL_USERNAME = "@ossae"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # رابط HTTPS للويب هوك

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
            [InlineKeyboardButton("اشترك بالقناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
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
            [InlineKeyboardButton("اشترك بالقناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
        ]
        await update.message.reply_text(
            "⚠️ لازم تشترك بالقناة",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    url = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("🎥 تحميل الفيديو", callback_data=f"video|{url}")]
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
    msg = await query.message.reply_text("⏳ جاري التحميل...")

    file_id = str(uuid.uuid4())
    output_template = f"{file_id}.%(ext)s"

    def download():
        ydl_opts = {
            "format": "best",
            "outtmpl": output_template,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    import asyncio
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, download)

    filename = next(
        (f for f in os.listdir(".") if f.startswith(file_id) and f.endswith((".mp4", ".mkv", ".webm"))),
        None
    )

    if filename:
        await query.message.reply_video(video=open(filename, "rb"))
        os.remove(filename)
        await msg.delete()
    else:
        await msg.edit_text("❌ لم يتم العثور على ملف الفيديو")

# ================== إضافة الهاندلرات ==================
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CallbackQueryHandler(button_handler))

# ================== Flask webhook ==================
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"

# ================== تشغيل البوت ==================
async def main():
    # تسجيل Webhook عند تليجرام
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook تم تفعيله!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    # تشغيل Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
