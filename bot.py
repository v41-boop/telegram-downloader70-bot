import telebot
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

TOKEN = "8440895412:AAGoiWXxyKreGgHpBKMY9lJXptMAmV78_hg"
CHANNEL_USERNAME = "@ossae"

bot = telebot.TeleBot(TOKEN)

# التحقق من الاشتراك الاجباري
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# رسالة البداية
@bot.message_handler(commands=['start'])
def start(message):
    if not check_subscription(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك بالقناة", url="https://t.me/ossae"))
        bot.send_message(message.chat.id, "⚠️ لازم تشترك بالقناة حتى تستخدم البوت", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "📥 ارسل رابط الفيديو من اي منصة")

# استقبال الرابط
@bot.message_handler(func=lambda m: True)
def handle_message(message):

    if not check_subscription(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك بالقناة", url="https://t.me/ossae"))
        bot.send_message(message.chat.id, "⚠️ لازم تشترك بالقناة", reply_markup=markup)
        return

    url = message.text

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎥 تحميل فيديو", callback_data=f"video|{url}"),
        InlineKeyboardButton("🎵 تحميل صوت MP3", callback_data=f"audio|{url}")
    )

    bot.send_message(message.chat.id, "اختر نوع التحميل:", reply_markup=markup)

# معالجة الضغط على الازرار
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data = call.data.split("|")
    mode = data[0]
    url = data[1]

    bot.send_message(call.message.chat.id, "⏳ جاري التحميل...")

    if mode == "video":
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as f:
            bot.send_video(call.message.chat.id, f)

        os.remove(filename)

    elif mode == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_file = filename.rsplit('.', 1)[0] + '.mp3'

        with open(mp3_file, 'rb') as f:
            bot.send_audio(call.message.chat.id, f)

        os.remove(mp3_file)

bot.infinity_polling()
