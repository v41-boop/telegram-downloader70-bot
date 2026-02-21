from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8440895412:AAHASqywVBlmyyoOhNtQMU2b8OUXI5bTPpc"
CHANNEL_USERNAME = "@ossae"  # قناتك للتحقق من الاشتراك

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except:
        return False

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_subscribed = await check_subscription(update, context)

    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك بالقناة أولاً", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "❌ لازم تشترك بالقناة قبل استخدام البوت",
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر نوع التحميل:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_sub":
        subscribed = await check_subscription(update, context)
        if subscribed:
            await query.edit_message_text("✅ تم التحقق، يمكنك الآن إرسال رابط لتحميله!")
        else:
            await query.edit_message_text(
                "❌ لم يتم الاشتراك بعد! اشترك بالقناة أولاً.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 اشترك بالقناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
                    [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
                ])
            )
    elif query.data == "video":
        await query.edit_message_text(f"⏳ جاري تحميل الفيديو من الرابط: {context.user_data.get('url')}")
    elif query.data == "audio":
        await query.edit_message_text(f"⏳ جاري تحميل الصوت من الرابط: {context.user_data.get('url')}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
app.add_handler(CallbackQueryHandler(button_handler))

print("البوت يعمل الآن!")
app.run_polling()
