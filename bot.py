import os
import re
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import yt_dlp

# --- سيرفر وهمي لإبقاء Render حياً ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()

# --- الإعدادات الرئيسية ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAF1Nt7eBMTucCNtEwfd63NRKK3cX2i64UE")
MUST_JOIN_CHANNEL = os.getenv("CHANNEL_USERNAME", "wanasatt")

bot = telebot.TeleBot(BOT_TOKEN)
USER_TEMP = {}
COOKIE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

# --- لوحة الأزرار الشفافة السفلية ---
def main_reply_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("اليوتيوب"),
        KeyboardButton("الانستغرام"), KeyboardButton("الفيسبوك"),
        KeyboardButton("التيك توك"), KeyboardButton("لايكي"),
        KeyboardButton("سناب شات"), KeyboardButton("تويتر"),
        KeyboardButton("بنترست"),
        KeyboardButton("📊 إحصائياتي"),
        KeyboardButton("➕ أضف البوت لمجموعتك")
    )
    return markup

# --- التحقق من الاشتراك الإجباري ---
def check_sub(user_id):
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
    name = message.from_user.first_name

    if not check_sub(user_id):
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("📢 انضمام للقناة", url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        inline_kb.add(InlineKeyboardButton("✅ تأكيد الاشتراك", callback_data="verify_sub"))
        bot.reply_to(message, f"⚠️ **عذراً ({name})، يرجى الاشتراك في القناة أولاً لاستخدام البوت:**\n\n📢 @{MUST_JOIN_CHANNEL}", reply_markup=inline_kb, parse_mode="Markdown")
        return

    msg_text = (
        f"🙋‍♂️ مرحباً ({name})\n"
        "───────────────────\n"
        "📥 **أرسل أي رابط وسأحمله لك فوراً**\n\n"
        "**المنصات المدعومة:**\n"
        "📸 Instagram • 🌐 X (Twitter)\n"
        "🎵 TikTok • ▶️ YouTube\n"
        "👻 Snapchat • 📌 Pinterest\n"
        "───────────────────\n"
        "📖 **داخل المجموعات:**\n"
        "أرسل `/d` مع الرابط للتحميل"
    )
    bot.send_message(message.chat.id, msg_text, reply_markup=main_reply_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_sub")
def verify_callback(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "🎉 تم التأكيد بنجاح!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في القناة بعد!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # استجابة أزرار القائمة السفلية
    if text in ["اليوتيوب", "الانستغرام", "الفيسبوك", "التيك توك", "لايكي", "سناب شات", "تويتر", "بنترست"]:
        bot.reply_to(message, f"📌 **أرسل الآن رابط من منصة ({text}) للتحميل المباشر.**", parse_mode="Markdown")
        return
    elif text == "📊 إحصائياتي":
        bot.reply_to(message, "📊 **إحصائيات استخدامك:**\n• عدد التحميلات: 1", parse_mode="Markdown")
        return
    elif text == "➕ أضف البوت لمجموعتك":
        bot.reply_to(message, f"🔗 **رابط إضافة البوت للمجموعات:**\nhttps://t.me/{bot.get_me().username}?startgroup=true", parse_mode="Markdown")
        return

    # دعم التحميل داخل المجموعات بالأمر /d
    if message.chat.type in ['group', 'supergroup']:
        if not text.startswith('/d'):
            return
        text = text.replace('/d', '').strip()

    if not re.match(r'https?://[^\s]+', text):
        return

    if not check_sub(user_id):
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("📢 انضمام للقناة", url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        inline_kb.add(InlineKeyboardButton("✅ تأكيد الاشتراك", callback_data="verify_sub"))
        bot.reply_to(message, f"⚠️ يرجى الاشتراك في القناة أولاً لاستخدام البوت:\n📢 @{MUST_JOIN_CHANNEL}", reply_markup=inline_kb)
        return

    status_msg = bot.reply_to(message, "🔍 **جاري قراءة البيانات والرابط...**", parse_mode="Markdown")
    USER_TEMP[user_id] = text

    # إنشاء الأزرار التفاعلية المباشرة
    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        InlineKeyboardButton("مقطع صوتي", callback_data="dl_voice"),
        InlineKeyboardButton("ملف صوتي", callback_data="dl_audio")
    )
    inline_kb.add(InlineKeyboardButton("مقطع فيديو", callback_data="dl_video"))

    bot.edit_message_text(
        "🎬 **اختر نوع التحميل المطلوب:**",
        chat_id=status_msg.chat.id,
        message_id=status_msg.message_id,
        reply_markup=inline_kb,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_"))
def process_ytdlp_download(call):
    user_id = call.from_user.id
    url = USER_TEMP.get(user_id)

    if not url:
        bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، يرجى إعادة إرسال الرابط.", show_alert=True)
        return

    action = call.data.split("_")[1]
    bot.edit_message_text("📥 **جاري تنزيل الملف وإرساله...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    out_file = f"media_{user_id}_{call.id}"

    # إعدادات yt-dlp المعززة لفك قيود يوتيوب و Render
    ydl_opts = {
        'outtmpl': f'{out_file}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        }
    }

    if os.path.exists(COOKIE_PATH):
        ydl_opts['cookiefile'] = COOKIE_PATH

    if action in ["voice", "audio"]:
        ydl_opts['format'] = 'ba/bestaudio/best'
    else:
        ydl_opts['format'] = 'b/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        downloaded_path = None
        for file in os.listdir("."):
            if file.startswith(out_file):
                downloaded_path = file
                break

        if not downloaded_path or not os.path.exists(downloaded_path):
            raise Exception("تعذر العثور على الملف بعد التنزيل.")

        title = info.get('title', 'تم التنزيل بنجاح')

        with open(downloaded_path, 'rb') as f:
            if action == "voice":
                bot.send_voice(call.message.chat.id, f, caption=title)
            elif action == "audio":
                bot.send_audio(call.message.chat.id, f, caption=title)
            else:
                bot.send_video(call.message.chat.id, f, caption=title)

        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ **حدث خطأ أثناء التنزيل:**\n`{str(e)[:120]}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    finally:
        for file in os.listdir("."):
            if file.startswith(out_file):
                try:
                    os.remove(file)
                except Exception:
                    pass

if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
