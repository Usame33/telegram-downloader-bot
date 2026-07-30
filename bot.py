import os
import subprocess
import sys
import time

# 📦 تثبيت المكتبات تلقائياً إذا لم تكن موجودة
try:
    import telebot
    from telebot import types
    import yt_dlp
except ModuleNotFoundError:
    print("⚡ جاري تثبيت المكتبات المطلوبة تلقائياً...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI", "yt-dlp"])
    import telebot
    from telebot import types
    import yt_dlp

# 🔑 توكين البوت الخاص بك
BOT_TOKEN = "8629100412:AAGvnlwDHKjXJUTET5lsfW7zOYZq5ycyrBo"
CHANNEL_USERNAME = "@wanasatt"

bot = telebot.TeleBot(BOT_TOKEN)

MESSAGES = {
    'ar': {
        'rtl': "\u200f",
        'welcome': "👋 <b>أهلاً بك في بوت تحميل المقاطع!</b>\n\nأرسل لي رابط الفيديو (TikTok, Instagram, YouTube) وسأقوم بتحميله فوراً 🚀",
        'force_sub': "⚠️ <b>عذراً عزيزي، يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:</b>\n\nاشترك ثم أعد إرسال الرابط.",
        'btn_sub': "📢 الاشتراك في القناة",
        'btn_lang': "🌐 تغيير اللغة / Language",
        'loading_title': "⏳ <b>جاري جلب الفيديو وتحميله...</b>",
        'upload_title': "🚀 <b>جاري رفع الفيديو إلى المحادثة...</b>",
        'success': "✅ <b>تم تحميل الفيديو بنجاح!</b>",
        'err_download': "❌ <b>عذراً، تعذر تحميل هذا الفيديو! تأكد من صحة الرابط أو حاول لاحقاً.</b>",
        'title': "العنوان",
        'author': "الناشر",
        'duration': "المدة",
        'sec': "ثانية",
        'bot_name': "البوت",
        'channel_name': "القناة"
    },
    'en': {
        'rtl': "",
        'welcome': "👋 <b>Welcome to Video Downloader Bot!</b>\n\nSend me a video link (TikTok, Instagram, Shorts) and I'll download it 🚀",
        'force_sub': "⚠️ <b>Sorry, you must subscribe to our channel first to use this bot:</b>",
        'btn_sub': "📢 Subscribe to Channel",
        'btn_lang': "🌐 Change Language",
        'loading_title': "⏳ <b>Downloading video...</b>",
        'upload_title': "🚀 <b>Sending video to chat...</b>",
        'success': "✅ <b>Video downloaded successfully!</b>",
        'err_download': "❌ <b>Failed to download this video. Please check the link.</b>",
        'title': "Title",
        'author': "Author",
        'duration': "Duration",
        'sec': "seconds",
        'bot_name': "Bot",
        'channel_name': "Channel"
    },
    'tr': {
        'rtl': "",
        'welcome': "👋 <b>Video İndirme Botuna Hoş Geldiniz!</b>\n\nİndirmek istediğiniz video bağlantısını gönderin 🚀",
        'force_sub': "⚠️ <b>Üzgünüz, botu kullanabilmek için önce kanalımıza abone olmalısınız:</b>",
        'btn_sub': "📢 Kanala Abone Ol",
        'btn_lang': "🌐 Dili Değiştir",
        'loading_title': "⏳ <b>Video indiriliyor...</b>",
        'upload_title': "🚀 <b>Video sohbete gönderiliyor...</b>",
        'success': "✅ <b>Video başarıyla indirildi!</b>",
        'title': "Başlık",
        'author': "Yayıncı",
        'duration': "Süre",
        'sec': "saniye",
        'bot_name': "Bot",
        'channel_name': "Kanal"
    }
}

user_languages = {}

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def get_language_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="set_lang_ar"),
        types.InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
        types.InlineKeyboardButton("Türkçe 🇹🇷", callback_data="set_lang_tr")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(MESSAGES[lang]['btn_sub'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        bot.send_message(message.chat.id, MESSAGES[lang]['force_sub'], parse_mode='HTML', reply_markup=markup)
        return

    bot.send_message(message.chat.id, MESSAGES[lang]['welcome'], parse_mode='HTML', reply_markup=get_language_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
def set_language(call):
    lang_code = call.data.split('_')[2]
    user_languages[call.from_user.id] = lang_code
    confirm_text = {'ar': "تم ضبط اللغة إلى العربية 🇸🇦", 'en': "Language set to English 🇬🇧", 'tr': "Dil Türkçe olarak ayarlandı 🇹🇷"}
    bot.answer_callback_query(call.id, confirm_text[lang_code])
    bot.edit_message_text(confirm_text[lang_code], call.message.chat.id, call.message.message_id)

# 🎬 معالجة التحميل الفعلي للرابط
@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def handle_download(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    url = message.text.strip()
    lang = user_languages.get(user_id, 'ar')
    txt = MESSAGES[lang]
    rtl = txt['rtl']
    
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(txt['btn_sub'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        bot.send_message(chat_id, txt['force_sub'], parse_mode='HTML', reply_markup=markup)
        return

    msg = bot.send_message(chat_id, f"{rtl}{txt['loading_title']}\n\n⏳ [████░░░░░░] 40%", parse_mode='HTML')
    
    output_filename = f"video_{user_id}_{int(time.time())}.mp4"

    # إعدادات yt-dlp للتحميل
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'Video')
            author = info.get('uploader', info.get('uploader_id', 'Unknown'))
            duration = info.get('duration', 0)

        bot.edit_message_text(f"{rtl}{txt['upload_title']}\n\n🚀 [██████████] 100%", chat_id, msg.message_id, parse_mode='HTML')

        caption = f"""
{rtl}{txt['success']}

━━━━━━━━━━━━━━━━━━

🎬 <b>{txt['title']}:</b> <code>{video_title[:50]}</code>
👤 <b>{txt['author']}:</b> <code>{author}</code>
⏱️ <b>{txt['duration']}:</b> <code>{duration} {txt['sec']}</code>

━━━━━━━━━━━━━━━━━━

🤖 <b>{txt['bot_name']}:</b> @Ussame_bot
📢 <b>{txt['channel_name']}:</b> {CHANNEL_USERNAME}
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(txt['btn_sub'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
            types.InlineKeyboardButton(txt['btn_lang'], callback_data="set_lang_ar")
        )

        # 📹 إرسال ملف الفيديو الحقيقي بـ send_video!
        with open(output_filename, 'rb') as video_file:
            bot.send_video(
                chat_id,
                video_file,
                caption=caption,
                parse_mode='HTML',
                reply_markup=markup
            )

        bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(f"{rtl}{txt.get('err_download', 'Error')}", chat_id, msg.message_id, parse_mode='HTML')

    finally:
        # مسح الفيديو من السيرفر بعد الإرسال لتوفير المساحة
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == "__main__":
    print("⚡ البوت يعمل بنجاح وجاهز لتحميل الفيديوهات الحقيقية...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"\n❌ حدث خطأ:\n{e}\n")
