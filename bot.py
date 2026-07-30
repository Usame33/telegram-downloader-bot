import time
import telebot
from telebot import types

# 🔑 توكين البوت الجديد الخاص بك
BOT_TOKEN = "8629100412:AAGvnlwDHKjXJUTET5lsfW7zOYZq5ycyrBo"

# 📢 معرف القناة الرسمية للاشتراك الإجباري (يرجى رفع البوت مشرفاً في القناة)
CHANNEL_USERNAME = "@wanasatt"

bot = telebot.TeleBot(BOT_TOKEN)

# 🌐 القاموس الموحد لنصوص البوت بكافة اللغات
MESSAGES = {
    'ar': {
        'rtl': "\u200f",
        'welcome': "👋 <b>أهلاً بك في بوت تحميل المقاطع!</b>\n\nأرسل لي رابط الفيديو وسأقوم بتحميله فوراً 🚀",
        'force_sub': "⚠️ <b>عذراً عزيزي، يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:</b>\n\nاشترك ثم أعد إرسال الرابط.",
        'btn_sub': "📢 الاشتراك في القناة",
        'btn_lang': "🌐 تغيير اللغة / Language",
        'loading_title': "⏳ <b>جاري التحميل...</b>",
        'upload_title': "🚀 <b>جاري الإرسال للمحادثة...</b>",
        'steps': [
            ("📥 <i>جاري الاتصال بالخادم...</i>", "1"),
            ("📥 <i>جاري تحميل الفيديو (HD)...</i>", "2"),
            ("📥 <i>جاري معالجة البيانات...</i>", "3"),
            ("📦 <i>جارٍ ضبط الحجم المناسب...</i>", "4"),
            ("⚡ <i>اقتربنا من الانتهاء...</i>", "5"),
        ],
        'upload_status': "📤 <i>جاري رفع الملف إلى تيليجرام...</i>",
        'success': "✅ <b>تم تحميل الفيديو بنجاح!</b>",
        'title': "العنوان",
        'author': "الناشر",
        'duration': "المدة",
        'quality': "الجودة",
        'platform': "المنصة",
        'sec': "ثانية",
        'bot_name': "البوت",
        'channel_name': "القناة"
    },
    'en': {
        'rtl': "",
        'welcome': "👋 <b>Welcome to Video Downloader Bot!</b>\n\nSend me a video link and I'll download it for you 🚀",
        'force_sub': "⚠️ <b>Sorry, you must subscribe to our channel first to use this bot:</b>\n\nPlease subscribe and try sending the link again.",
        'btn_sub': "📢 Subscribe to Channel",
        'btn_lang': "🌐 Change Language",
        'loading_title': "⏳ <b>Downloading...</b>",
        'upload_title': "🚀 <b>Sending to chat...</b>",
        'steps': [
            ("📥 <i>Connecting to server...</i>", "1"),
            ("📥 <i>Downloading video (HD)...</i>", "2"),
            ("📥 <i>Processing data...</i>", "3"),
            ("📦 <i>Compressing file...</i>", "4"),
            ("⚡ <i>Almost done...</i>", "5"),
        ],
        'upload_status': "📤 <i>Uploading video to Telegram...</i>",
        'success': "✅ <b>Video downloaded successfully!</b>",
        'title': "Title",
        'author': "Author",
        'duration': "Duration",
        'quality': "Quality",
        'platform': "Platform",
        'sec': "seconds",
        'bot_name': "Bot",
        'channel_name': "Channel"
    },
    'tr': {
        'rtl': "",
        'welcome': "👋 <b>Video İndirme Botuna Hoş Geldiniz!</b>\n\nİndirmek istediğiniz video bağlantısını gönderin 🚀",
        'force_sub': "⚠️ <b>Üzgünüz, botu kullanabilmek için önce kanalımıza abone olmalısınız:</b>\n\nAbone olduktan sonra bağlantıyı tekrar gönderin.",
        'btn_sub': "📢 Kanala Abone Ol",
        'btn_lang': "🌐 Dili Değiştir",
        'loading_title': "⏳ <b>İndiriliyor...</b>",
        'upload_title': "🚀 <b>Sohbete gönderiliyor...</b>",
        'steps': [
            ("📥 <i>Sunucuya bağlanılıyor...</i>", "1"),
            ("📥 <i>Video indiriliyor (HD)...</i>", "2"),
            ("📥 <i>Veriler işleniyor...</i>", "3"),
            ("📦 <i>Boyut ayarlanıyor...</i>", "4"),
            ("⚡ <i>Neredeyse bitti...</i>", "5"),
        ],
        'upload_status': "📤 <i>Video Telegram'a yükleniyor...</i>",
        'success': "✅ <b>Video başarıyla indirildi!</b>",
        'title': "Başlık",
        'author': "Yayıncı",
        'duration': "Süre",
        'quality': "Kalite",
        'platform': "Platform",
        'sec': "saniye",
        'bot_name': "Bot",
        'channel_name': "Kanal"
    }
}

user_languages = {}

# 🛡️ التحقق من الاشتراك الإجباري
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

# 🔘 أزرار تغيير اللغة
def get_language_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("العربية 🇸🇦", callback_data="set_lang_ar"),
        types.InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en"),
        types.InlineKeyboardButton("Türkçe 🇹🇷", callback_data="set_lang_tr")
    )
    return markup

# 🚀 أمر البدء /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(MESSAGES[lang]['btn_sub'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        bot.send_message(message.chat.id, MESSAGES[lang]['force_sub'], parse_mode='HTML', reply_markup=markup)
        return

    markup = get_language_keyboard()
    bot.send_message(message.chat.id, MESSAGES[lang]['welcome'], parse_mode='HTML', reply_markup=markup)

# 🌐 تغيير اللغة عبر الكولباك
@bot.callback_query_handler(func=lambda call: call.data.startswith('set_lang_'))
def set_language(call):
    lang_code = call.data.split('_')[2]
    user_languages[call.from_user.id] = lang_code
    
    confirm_text = {
        'ar': "تم ضبط اللغة إلى العربية 🇸🇦",
        'en': "Language set to English 🇬🇧",
        'tr': "Dil Türkçe olarak ayarlandı 🇹🇷"
    }
    
    bot.answer_callback_query(call.id, confirm_text[lang_code])
    bot.edit_message_text(confirm_text[lang_code], call.message.chat.id, call.message.message_id)

# 🎬 استقبال المحتوى وتتبع شريط التحميل
@bot.message_handler(func=lambda message: True)
def handle_video_request(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
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
        f"{rtl}{txt['loading_title']}\n\n[░░░░░░░░░░] 0%\n{txt['steps'][0][0]}", 
        parse_mode='HTML'
    )

    bars = ["█░░░░░░░░░ 10%", "███░░░░░░░ 30%", "█████░░░░░ 50%", "███████░░░ 70%", "█████████░ 90%"]

    # حركة شريط التقدم والأنيميشن
    for i, (status, frame) in enumerate(txt['steps']):
        spinner = "⠋" if frame in ["1", "3", "5"] else "⠙"
        bot.edit_message_text(
            f"{rtl}{txt['loading_title']} {spinner}\n\n[{bars[i]}]\n{status}",
            chat_id,
            msg.message_id,
            parse_mode='HTML'
        )
        time.sleep(0.4)

    # انيميشن الإرسال
    bot.edit_message_text(
        f"{rtl}{txt['upload_title']}\n\n[██████████] 100%\n{txt['upload_status']}",
        chat_id,
        msg.message_id,
        parse_mode='HTML'
    )
    time.sleep(0.5)

    caption = f"""
{rtl}{txt['success']}

━━━━━━━━━━━━━━━━━━

🎬 <b>{txt['title']}:</b>
<code>daha hatırlamadığım neler var kim bilir #fyp</code>

👤 <b>{txt['author']}:</b> <code>yalniczagono</code>
⏱️ <b>{txt['duration']}:</b> <code>15 {txt['sec']}</code>
🎞️ <b>{txt['quality']}:</b> <code>1280p (HD)</code>
🌐 <b>{txt['platform']}:</b> <code>TikTok</code>

━━━━━━━━━━━━━━━━━━

🤖 <b>{txt['bot_name']}:</b> @Ussame_bot
📢 <b>{txt['channel_name']}:</b> {CHANNEL_USERNAME}
"""

    bot.delete_message(chat_id, msg.message_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(txt['btn_sub'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
        types.InlineKeyboardButton(txt['btn_lang'], callback_data="set_lang_ar")
    )

    bot.send_message(chat_id, caption, parse_mode='HTML', reply_markup=markup)

if __name__ == "__main__":
    print("⚡ البوت يعمل الآن بالتوكين الجديد...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"\n❌ حدث خطأ أدى لتوقف البوت:\n{e}\n")
