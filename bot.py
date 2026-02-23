import os
import uuid
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

# ================== الإعدادات ==================
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثال: https://yourproject.up.railway.app
CHANNEL_USERNAME = "@ossae"

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
telegram_app = Application.builder().token(TOKEN).build()
app = Flask(__name__)

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
        keyboard = [[InlineKeyboardButton("اشترك بالقناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        await update.message.reply_text("⚠️ لازم تشترك بالقناة حتى تستخدم البوت", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("📥 ارسل رابط الفيديو")

# ================== استقبال الرابط ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await check_subscription(user.id):
        keyboard = [[InlineKeyboardButton("اشترك بالقناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        await update.message.reply_text("⚠️ لازم تشترك بالقناة", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    url = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("🎥 فيديو", callback_data=f"video|{url}")]]
    await update.message.reply_text("اختر نوع التحميل:", reply_markup=InlineKeyboardMarkup(keyboard))

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

        filename = next((f for f in os.listdir(".") if f.startswith(file_id) and f.endswith((".mp4", ".mkv", ".webm"))), None)
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

# ================== Flask Webhook Endpoint ==================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    telegram_app.update_queue.put(update)
    return "OK"

# ================== تشغيل Webhook ==================
if __name__ == "__main__":
    # تعيين Webhook تلقائياً عند التشغيل
    bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    # تشغيل Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
