import os
import subprocess
import sys
import time
import traceback

# 📦 التثبيت والتحقق التلقائي من المكتبات المطلوبة
try:
    import telebot
    from telebot import types
    import yt_dlp
except ModuleNotFoundError:
    print("⚡ جاري تثبيت المكتبات المطلوبة لضمان العمل بأعلى كفاءة...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI", "yt-dlp", "requests"])
    import telebot
    from telebot import types
    import yt_dlp

# 🔑 توكين البوت الخاص بك
BOT_TOKEN = "8629100412:AAGvnlwDHKjXJUTET5lsfW7zOYZq5ycyrBo"

# 📢 معرف قناتك الرسمية للاشتراك الإجباري
CHANNEL_USERNAME = "@wanasatt"

bot = telebot.TeleBot(BOT_TOKEN)

# 🌐 نصوص البوت بجميع اللغات مع الأنيميشن
MESSAGES = {
    'ar': {
        'rtl': "\u200f",
        'welcome': "👋 <b>أهلاً بك في بوت التحميل السريع!</b>\n\nأرسل أي رابط (TikTok, Reels, Shorts, Facebook...) وسأقوم بتحميله فوراً بأعلى جودة 🚀",
        'force_sub': "⚠️ <b>عذراً عزيزي، يجب عليك الاشتراك في القناة لاستخدام البوت:</b>\n\nاشترك أولاً ثم أرسل الرابط مرة أخرى.",
        'btn_sub': "📢 الاشتراك في القناة",
        'btn_lang': "🌐 تغيير اللغة / Language",
        'loading_title': "⏳ <b>جاري تحميل الفيديو...</b>",
        'upload_title': "🚀 <b>جاري الإرسال للمحادثة...</b>",
        'steps': [
            ("📥 <i>جاري الاتصال بالخادم...</i>", "█░░░░░░░░░ 10%"),
            ("📥 <i>جاري سحب المقطع بأعلى جودة...</i>", "████░░░░░░ 40%"),
            ("📦 <i>جاري تجهيز الملف للإرسال...</i>", "████████░░ 80%"),
        ],
        'upload_status': "📤 <i>جاري رفع الفيديو إلى تيليجرام...</i>",
        'success': "✅ <b>تم تحميل الفيديو بنجاح!</b>",
        'err_download': "❌ <b>عذراً، حدث خطأ أثناء التحميل!</b>",
        'title': "العنوان",
        'author': "الناشر",
        'duration': "المدة",
        'platform': "المنصة",
        'sec': "ثانية",
        'bot_name': "البوت",
        'channel_name': "القناة"
    },
    'en': {
        'rtl': "",
        'welcome': "👋 <b>Welcome to Fast Media Downloader!</b>\n\nSend any video link (TikTok, Reels, Shorts, Facebook...) and I will download it instantly 🚀",
        'force_sub': "⚠️ <b>Sorry, you must subscribe to our channel to use this bot:</b>\n\nPlease subscribe and send the link again.",
        'btn_sub': "📢 Join Channel",
        'btn_lang': "🌐 Change Language",
        'loading_title': "⏳ <b>Downloading video...</b>",
        'upload_title': "🚀 <b>Sending video to chat...</b>",
        'steps': [
            ("📥 <i>Connecting to server...</i>", "█░░░░░░░░░ 10%"),
            ("📥 <i>Fetching video in HD...</i>", "████░░░░░░ 40%"),
            ("📦 <i>Preparing file for Telegram...</i>", "████████░░ 80%"),
        ],
        'upload_status': "📤 <i>Uploading video to Telegram...</i>",
        'success': "✅ <b>Video downloaded successfully!</b>",
        'err_download': "❌ <b>An error occurred during download!</b>",
        'title': "Title",
        'author': "Author",
        'duration': "Duration",
        'platform': "Platform",
        'sec': "seconds",
        'bot_name': "Bot",
        'channel_name': "Channel"
    },
    'tr': {
        'rtl': "",
        'welcome': "👋 <b>Hızlı Video İndirme Botuna Hoş Geldiniz!</b>\n\nHerhangi bir video bağlantısını gönderin (TikTok, Reels, Shorts...) anında indireyim 🚀",
        'force_sub': "⚠️ <b>Üzgünüz, botu kullanabilmek için önce kanalımıza abone olmalısınız:</b>",
        'btn_sub': "📢 Kanala Katıl",
        'btn_lang': "🌐 Dili Değiştir",
        'loading_title': "⏳ <b>Video indiriliyor...</b>",
        'upload_title': "🚀 <b>Sohbete gönderiliyor...</b>",
        'steps': [
            ("📥 <i>Sunucuya bağlanılıyor...</i>", "█░░░░░░░░░ 10%"),
            ("📥 <i>Video HD kalitede indiriliyor...</i>", "████░░░░░░ 40%"),
            ("📦 <i>Telegram için hazırlanıyor...</i>", "████████░░ 80%"),
        ],
        'upload_status': "📤 <i>Video yükleniyor...</i>",
        'success': "✅ <b>Video başarıyla indirildi!</b>",
        'err_download': "❌ <b>İndirme sırasında bir hata oluştu!</b>",
        'title': "Başlık",
        'author': "Yayıncı",
        'duration': "Süre",
        'platform': "Platform",
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

# 🎬 معالجة وتحميل الفيديو
@bot.message_handler(func=lambda message: message.text and ('http://' in message.text or 'https://' in message.text))
def handle_download(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    urls = [w for w in message.text.split() if w.startswith('http://') or w.startswith('https://')]
    if not urls:
        return
    url = urls[0]

    lang = user_languages.get(user_id, 'ar')
    txt = MESSAGES[lang]
    rtl = txt['rtl']
    
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(txt['btn_sub'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        bot.send_message(chat_id, txt['force_sub'], parse_mode='HTML', reply_markup=markup)
        return

    msg = bot.send_message(
        chat_id, 
        f"{rtl}{txt['loading_title']} ⠋\n\n[{txt['steps'][0][1]}]\n{txt['steps'][0][0]}", 
        parse_mode='HTML'
    )
    
    output_filename = f"vid_{user_id}_{int(time.time())}.mp4"

    ydl_opts = {
        'format': 'b[ext=mp4]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
    }

    try:
        bot.edit_message_text(
            f"{rtl}{txt['loading_title']} ⠙\n\n[{txt['steps'][1][1]}]\n{txt['steps'][1][0]}",
            chat_id, msg.message_id, parse_mode='HTML'
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'Video')
            author = info.get('uploader', info.get('uploader_id', 'Unknown'))
            duration = info.get('duration', 0)
            extractor = info.get('extractor_key', 'Media')

        bot.edit_message_text(
            f"{rtl}{txt['upload_title']} ⚡\n\n[██████████ 100%]\n{txt['upload_status']}",
            chat_id, msg.message_id, parse_mode='HTML'
        )

        caption = f"""
{rtl}{txt['success']}

━━━━━━━━━━━━━━━━━━
🎬 <b>{txt['title']}:</b> <code>{video_title[:45]}</code>
👤 <b>{txt['author']}:</b> <code>{author}</code>
⏱️ <b>{txt['duration']}:</b> <code>{duration} {txt['sec']}</code>
🌐 <b>{txt['platform']}:</b> <code>{extractor}</code>
━━━━━━━━━━━━━━━━━━
📢 <b>{txt['channel_name']}:</b> {CHANNEL_USERNAME}
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(txt['btn_sub'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
            types.InlineKeyboardButton(txt['btn_lang'], callback_data="set_lang_ar")
        )

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
        traceback.print_exc()
        print(repr(e))
        bot.send_message(chat_id, f"DEBUG:\n{repr(e)}")

    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == "__main__":
    print("⚡ البوت يعمل بنجاح مع نمط تصحيح الأخطاء (DEBUG)...")
    try:
        bot.infinity_polling(timeout=15, long_polling_timeout=5)
    except Exception as e:
        print(f"\n❌ خطأ تشغيل:\n{e}\n")
 
