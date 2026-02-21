import os
import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8440895412:AAGoiWXxyKreGgHpBKMY9lJXptMAmV78_hg"
CHANNEL_USERNAME = "@ossae"

# ================== تحقق الاشتراك ==================
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================== استقبال الرابط ==================
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_subscription(update, context):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك بالقناة", url="https://t.me/ossae")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "❌ لازم تشترك بالقناة أولاً",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    url = update.message.text
    context.user_data["url"] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو", callback_data="video"),
            InlineKeyboardButton("🎵 صوت", callback_data="audio"),
        ]
    ]

    await update.message.reply_text(
        "اختر نوع التحميل:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== أزرار ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_sub":
        if await check_subscription(update, context):
            await query.edit_message_text("✅ تم التحقق، أرسل رابط الآن.")
        else:
            keyboard = [
                [InlineKeyboardButton("📢 اشترك بالقناة", url="https://t.me/ossae")],
                [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
            ]
            await query.edit_message_text(
                "❌ لم يتم الاشتراك بعد!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return

    url = context.user_data.get("url")
    if not url:
        await query.edit_message_text("❌ أرسل رابط أولاً.")
        return

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        ydl_opts = {
            "format": "best",
            "outtmpl": "video.%(ext)s",
            "quiet": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0"
            }
        }

        if query.data == "audio":
            ydl_opts["format"] = "bestaudio"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if query.data == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"

        if query.data == "video":
            await query.message.reply_video(video=open(filename, "rb"))
        else:
            await query.message.reply_audio(audio=open(filename, "rb"))

        os.remove(filename)

    except Exception as e:
        await query.message.reply_text(f"❌ حدث خطأ:\n{e}")

# ================== تشغيل البوت ==================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

print("البوت يعمل الآن!")
app.run_polling()
