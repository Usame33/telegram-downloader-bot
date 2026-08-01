import os
import re
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- سيرفر وهمي لإبقاء Render سعيداً ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()

# --- إعدادات تسجيل الأخطاء ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# البيانات الخاصة بك
BOT_TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAF1Nt7eBMTucCNtEwfd63NRKK3cX2i64UE")
MUST_JOIN_CHANNEL = os.getenv("CHANNEL_USERNAME", "wanasatt")

bot = telebot.TeleBot(BOT_TOKEN)

USER_LANG = {}
TEMP_DATA = {}
COOKIE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

TEXTS = {
    "ar": {
        "flag": "🇸🇾", "name": "العربية",
        "welcome": "✨ **أهلاً بك في بوت تحميل الوسائط الشامل الاحترافي!**\n\n⚡ **الميزات المتاحة:**\n• تحميل الفيديو من يوتيوب، تيك توك، إنستغرام، فيسبوك، وتويتر.\n• جودات عالية ومتعددة مع دعم تحويل الصوت MP3.\n• دعم 10 لغات مختلفة لسهولة الاستخدام.\n\n📌 **أرسل رابط الفيديو الآن للبدء!**",
        "sub_required": "⚠️ **عذراً عزيزي، للاستفادة من خدمات البوت يرجى الاشتراك بقناتنا أولاً:**\n\n📢 @{channel}\n\n👇 **بعد الانضمام، اضغط على زر تأكيد الاشتراك:**",
        "sub_btn": "📢 انضمام للقناة", "verify_btn": "✅ تأكيد الاشتراك",
        "sub_success": "🎉 شكراً لاشتراكك! يمكنك الآن إرسال الرابط للتحميل.",
        "not_subbed": "❌ لم تقم بالاشتراك في القناة بعد! يرجى الانضمام أولاً.",
        "lang_select": "🌐 **اختر لغة الواجهة المناسبة لك / Select Language:**",
        "processing": "🔍 **جاري فحص الرابط واستخراج خيارات التحميل...**",
        "choose_format": "🎬 **معلومات الفيديو:**\n\n📌 **العنوان:** `{title}`\n⏱ **المدة:** `{duration}` ثانية\n\n👇 **اختر جودة أو صيغة التحميل المطلوبة:**",
        "downloading": "📥 **جاري تنزيل الملف وتحضيره للإرسال... قد يستغرق ذلك ثوانٍ قليلة.**",
        "error": "❌ **حدث خطأ أثناء معالجة الطلب:**\n`{error}`",
        "btn_best": "🌟 أفضل جودة متاحة",
        "btn_720": "🎥 فيديو 720p (HD)",
        "btn_480": "🎬 فيديو 480p (SD)",
        "btn_audio": "🎵 ملف صوتي MP3",
        "btn_lang": "🌐 تغيير اللغة",
        "btn_channel": "📢 القناة الرسمية",
        "btn_help": "ℹ️ تعليمات البوت",
        "help_msg": "🛠 **طريقة الاستخدام:**\n1. أرسل أي رابط من يوتيوب، تيك توك، أو إنستغرام.\n2. اختر الجودة أو الصيغة المناسبة لك من الأزرار.\n3. سيتم تنزيل وسحب الملف وإرساله لك مباشرة!"
    },
    "en": {
        "flag": "🇬🇧", "name": "English",
        "welcome": "✨ **Welcome to the Professional All-in-One Downloader Bot!**\n\n⚡ **Features:**\n• Download from YouTube, TikTok, Instagram, Facebook & Twitter.\n• High-quality videos and MP3 audio extraction.\n• Multi-language support (10 languages).\n\n📌 **Send a video link now to begin!**",
        "sub_required": "⚠️ **Please subscribe to our channel to use this bot:**\n\n📢 @{channel}",
        "sub_btn": "📢 Join Channel", "verify_btn": "✅ Verify Subscription",
        "sub_success": "🎉 Thank you for subscribing! Send any link to download.",
        "not_subbed": "❌ You are not subscribed yet!",
        "lang_select": "🌐 **Select your preferred language:**",
        "processing": "🔍 **Processing link and extracting formats...**",
        "choose_format": "🎬 **Video Details:**\n\n📌 **Title:** `{title}`\n⏱ **Duration:** `{duration}`s\n\n👇 **Choose format:**",
        "downloading": "📥 **Downloading and preparing file...**",
        "error": "❌ **An error occurred:**\n`{error}`",
        "btn_best": "🌟 Best Available",
        "btn_720": "🎥 Video 720p (HD)",
        "btn_480": "🎬 Video 480p (SD)",
        "btn_audio": "🎵 Audio MP3",
        "btn_lang": "🌐 Change Language",
        "btn_channel": "📢 Channel",
        "btn_help": "ℹ️ Help",
        "help_msg": "🛠 **How to use:**\n1. Send any valid link.\n2. Choose your preferred quality or MP3 format.\n3. The bot will download and send it to you."
    }
}

def get_text(user_id, key):
    lang = USER_LANG.get(user_id, "ar")
    return TEXTS.get(lang, TEXTS["ar"]).get(key, "")

def build_main_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(get_text(user_id, "btn_lang"), callback_data="change_lang"),
        InlineKeyboardButton(get_text(user_id, "btn_help"), callback_data="show_help")
    )
    markup.row(InlineKeyboardButton(get_text(user_id, "btn_channel"), url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
    return markup

def build_lang_keyboard():
    markup = InlineKeyboardMarkup()
    keys = list(TEXTS.keys())
    for i in range(0, len(keys), 2):
        k1 = keys[i]
        btn1 = InlineKeyboardButton(f"{TEXTS[k1]['flag']} {TEXTS[k1]['name']}", callback_data=f"setlang_{k1}")
        if i + 1 < len(keys):
            k2 = keys[i+1]
            btn2 = InlineKeyboardButton(f"{TEXTS[k2]['flag']} {TEXTS[k2]['name']}", callback_data=f"setlang_{k2}")
            markup.row(btn1, btn2)
        else:
            markup.row(btn1)
    return markup

def check_subscription(user_id):
    if not MUST_JOIN_CHANNEL:
        return True
    try:
        member = bot.get_chat_member(f"@{MUST_JOIN_CHANNEL}", user_id)
        return member.status in ["owner", "administrator", "member"]
    except Exception:
        return True

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton(get_text(user_id, "sub_btn"), url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        markup.row(InlineKeyboardButton(get_text(user_id, "verify_btn"), callback_data="check_sub"))
        bot.reply_to(message, get_text(user_id, "sub_required").format(channel=MUST_JOIN_CHANNEL), reply_markup=markup, parse_mode="Markdown")
        return

    bot.reply_to(message, get_text(user_id, "welcome"), reply_markup=build_main_keyboard(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "change_lang")
def change_lang_cb(call):
    user_id = call.from_user.id
    bot.edit_message_text(get_text(user_id, "lang_select"), call.message.chat.id, call.message.message_id, reply_markup=build_lang_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlang_"))
def set_lang_cb(call):
    lang_code = call.data.split("_")[1]
    user_id = call.from_user.id
    USER_LANG[user_id] = lang_code
    bot.answer_callback_query(call.id, "✅ Updated")
    bot.edit_message_text(get_text(user_id, "welcome"), call.message.chat.id, call.message.message_id, reply_markup=build_main_keyboard(user_id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def show_help_cb(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id, get_text(user_id, "help_msg"), show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_cb(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, get_text(user_id, "sub_success"), show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)
    else:
        bot.answer_callback_query(call.id, get_text(user_id, "not_subbed"), show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton(get_text(user_id, "sub_btn"), url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        markup.row(InlineKeyboardButton(get_text(user_id, "verify_btn"), callback_data="check_sub"))
        bot.reply_to(message, get_text(user_id, "sub_required").format(channel=MUST_JOIN_CHANNEL), reply_markup=markup, parse_mode="Markdown")
        return

    url = message.text.strip()
    if not re.match(r'https?://[^\s]+', url):
        return

    msg = bot.reply_to(message, get_text(user_id, "processing"), parse_mode="Markdown")

    ydl_opts = {'quiet': True, 'nocheckcertificate': True}
    if os.path.exists(COOKIE_PATH):
        ydl_opts['cookiefile'] = COOKIE_PATH

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get('title', 'Video')
        duration = info.get('duration', 0)

        TEMP_DATA[user_id] = url

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton(get_text(user_id, "btn_best"), callback_data="dl_best"))
        markup.row(
            InlineKeyboardButton(get_text(user_id, "btn_720"), callback_data="dl_720"),
            InlineKeyboardButton(get_text(user_id, "btn_480"), callback_data="dl_480")
        )
        markup.row(InlineKeyboardButton(get_text(user_id, "btn_audio"), callback_data="dl_audio"))

        bot.edit_message_text(
            get_text(user_id, "choose_format").format(title=title, duration=duration),
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Fetch Error: {e}")
        bot.edit_message_text(get_text(user_id, "error").format(error=str(e)[:120]), chat_id=msg.chat.id, message_id=msg.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_"))
def process_dl(call):
    user_id = call.from_user.id
    url = TEMP_DATA.get(user_id)

    if not url:
        bot.answer_callback_query(call.id, "⚠️ Session expired, please resend the link.", show_alert=True)
        return

    fmt = call.data.split("_")[1]
    bot.edit_message_text(get_text(user_id, "downloading"), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    out_file = f"down_{user_id}_{call.id}"
    
    ydl_opts = {
        'outtmpl': f'{out_file}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    if os.path.exists(COOKIE_PATH):
        ydl_opts['cookiefile'] = COOKIE_PATH

    # --- صيغ مجربة ومرنة مع يوتيوب بدون حظر صيغة ---
    if fmt == "audio":
        ydl_opts['format'] = 'bestaudio/best'
    elif fmt == "720":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    elif fmt == "480":
        ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        file_path = None
        for file in os.listdir("."):
            if file.startswith(out_file):
                file_path = file
                break

        if not file_path or not os.path.exists(file_path):
            raise Exception("File creation failed.")

        title = info.get('title', 'Downloaded Media')

        with open(file_path, 'rb') as f:
            if fmt == "audio":
                bot.send_audio(call.message.chat.id, f, caption=title)
            else:
                bot.send_video(call.message.chat.id, f, caption=title)

        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        logging.error(f"DL Error: {e}")
        bot.edit_message_text(get_text(user_id, "error").format(error=str(e)[:150]), call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    finally:
        for file in os.listdir("."):
            if file.startswith(out_file):
                try:
                    os.remove(file)
                except Exception:
                    pass

if __name__ == "__main__":
    logging.info("Starting bot with Telebot...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
