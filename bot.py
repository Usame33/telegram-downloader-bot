import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = "8629100412:AAFbCinwIOHvhSwvReg2l67-K9dqUgHpyjM"
CHANNEL = "@wanasatt"
CHANNEL_LINK = "https://t.me/wanasatt"

bot = telebot.TeleBot(TOKEN)

def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"خطأ في فحص الاشتراك: {e}")
        return False

def sub_keyboard():
    markup = InlineKeyboardMarkup()
    btn_link = InlineKeyboardButton("📢 اشترك في القناة أولاً", url=CHANNEL_LINK)
    btn_check = InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")
    markup.add(btn_link)
    markup.add(btn_check)
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if check_sub(user_id):
        bot.reply_to(message, "🎬 أهلاً بك! أرسل لي رابط الفيديو من (تيك توك، إنستغرام، يوتيوب...) وسأقوم بتحميله لك فوراً.")
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ عذراً عزيزي، يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:\n\n"
            "اشترك ثم اضغط على زر (تحقق من الاشتراك) بالأسفل.",
            reply_markup=sub_keyboard()
        )

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check(call):
    user_id = call.from_user.id
    if check_sub(user_id):
        bot.answer_callback_query(call.id, "✅ شكراً لاشتراكك! يمكنك الآن استخدام البوت.", show_alert=True)
        try:
            bot.edit_message_text(
                "✅ تم التحقق من الاشتراك بنجاح!\n\n🎬 أرسل لي الآن رابط الفيديو الذي تريد تحميله.",
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في القناة بعد! يرجى الانضمام للقناة أولاً ثم المحاولة.", show_alert=True)

@bot.message_handler(func=lambda message: True)
def download_video(message):
    user_id = message.from_user.id
    if not check_sub(user_id):
        bot.send_message(
            message.chat.id,
            "⚠️ لا يمكنك التحميل حتى تشترك في القناة أولاً!",
            reply_markup=sub_keyboard()
        )
        return

    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ يرجى إرسال رابط فيديو صحيح.")
        return

    msg = bot.reply_to(message, "⏳ جاري تحميل الفيديو، انتظر قليلاً...")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'video_{user_id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✨ تم التحميل بنجاح!")

        bot.delete_message(message.chat.id, msg.message_id)
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل: {e}", message.chat.id, msg.message_id)

print("جاري تشغيل البوت...")
bot.infinity_polling()
