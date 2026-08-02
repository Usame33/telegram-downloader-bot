import os
import re
import logging
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import yt_dlp

# --- سيرفر وهمي لضمان استمرار عمل Render ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Media Downloader Bot Status: OK")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()

# --- الإعدادات وتأمين البيانات ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAF1Nt7eBMTucCNtEwfd63NRKK3cX2i64UE")
MUST_JOIN_CHANNEL = os.getenv("CHANNEL_USERNAME", "wanasatt")

bot = telebot.TeleBot(BOT_TOKEN)
USER_TEMP = {}

# --- لوحة الأزرار الشفافة التفاعلية (تصميم جديد ومبتكر) ---
def main_reply_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🔻 يوتيوب • YouTube"),
        KeyboardButton("📸 إنستغرام • Instagram"),
        KeyboardButton("🔹 فيسبوك • Facebook"),
        KeyboardButton("🎵 تيك توك • TikTok"),
        KeyboardButton("👻 سناب شات • Snapchat"),
        KeyboardButton("🐦 تويتر • Twitter/X"),
        KeyboardButton("📍 بنترست • Pinterest"),
        KeyboardButton("💎 لايكي • Likee")
    )
    markup.add(
        KeyboardButton("📊 إحصائياتي والسرعة"),
        KeyboardButton("🔗 إضافة للمجموعات")
    )
    return markup

def check_sub(user_id):
    if not MUST_JOIN_CHANNEL:
        return True
    try:
        member = bot.get_chat_member(f"@{MUST_JOIN_CHANNEL}", user_id)
        return member.status in ["owner", "administrator", "member"]
    except Exception:
        return True

def is_youtube_url(url):
    return 'youtube.com' in url or 'youtu.be' in url

def download_youtube_via_api(url, is_audio=False):
    api_endpoint = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "url": url,
        "isAudioOnly": is_audio,
        "aBitrate": "128"
    }
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") in ["stream", "redirect"]:
                return data.get("url")
    except Exception:
        pass
    return None

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    if not check_sub(user_id):
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("📢 الانضمام للقناة الرسمية", url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        inline_kb.add(InlineKeyboardButton("⚡️ تأكيد الاشتراك الآن", callback_data="verify_sub"))
        bot.reply_to(
            message, 
            f"👋 **أهلاً بك يا {name}!**\n\n"
            "⚠️ لاستخدام خدمات التنزيل السريع، يرجى الانضمام إلى القناة أولاً لتفعيل الحساب:\n"
            f"👉 @{MUST_JOIN_CHANNEL}", 
            reply_markup=inline_kb, 
            parse_mode="Markdown"
        )
        return

    welcome_text = (
        f"💎 **أهلاً بك {name} في محرك تحميل الوسائط!**\n"
        "━━━━━━━ Single Media Bot ━━━━━━━\n\n"
        "📥 **كيفية الاستخدام:**\n"
        "أرسل **رابط الفيديو أو الصوت** مباشرة، وسأتولى معالجته وإرساله إليك فوراً.\n\n"
        "🌐 **المنصات المدعومة:**\n"
        "• YouTube • TikTok • Instagram\n"
        "• Facebook • Twitter • Snapchat\n\n"
        "👥 **للمجموعات:** أرسل `/d` متبوعة بالرابط داخل أي جروب."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_reply_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_sub")
def verify_callback(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم تأكيد اشتراكك بنجاح! استمتع بالخدمة.", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على اشتراكك، يرجى الضغط على رابط القناة والانضمام أولاً!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # التفاعل مع الأزرار الرئيسية
    if any(p in text for p in ["يوتيوب", "إنستغرام", "فيسبوك", "تيك توك", "لايكي", "سناب شات", "تويتر", "بنترست"]):
        bot.reply_to(message, "📌 **تفضل بإرسال الرابط المباشر للمقطع هنا:**", parse_mode="Markdown")
        return
    elif text == "📊 إحصائياتي والسرعة":
        bot.reply_to(message, "⚡️ **حالة الخدمة والاتصال:**\n\n• خادم المعالجة: 🟢 متصل ومستقر\n• جودة التنزيل: ⚡️ أسرع وضع مباشر", parse_mode="Markdown")
        return
    elif text == "🔗 إضافة للمجموعات":
        bot.reply_to(message, f"🚀 **لإضافة البوت إلى مجموعتك:**\nhttps://t.me/{bot.get_me().username}?startgroup=true", parse_mode="Markdown")
        return

    if message.chat.type in ['group', 'supergroup']:
        if not text.startswith('/d'):
            return
        text = text.replace('/d', '').strip()

    if not re.match(r'https?://[^\s]+', text):
        return

    if not check_sub(user_id):
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("📢 الانضمام للقناة", url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        inline_kb.add(InlineKeyboardButton("⚡️ تأكيد الاشتراك الآن", callback_data="verify_sub"))
        bot.reply_to(message, f"⚠️ يرجى الاشتراك في القناة أولاً لتفعيل التحميل:\n👉 @{MUST_JOIN_CHANNEL}", reply_markup=inline_kb)
        return

    status_msg = bot.reply_to(message, "⏳ **جاري تحليل الرابط وتأكيد البيانات...**", parse_mode="Markdown")
    USER_TEMP[user_id] = text

    # تصميم أزرار خيارات التنزيل الجديدة
    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        InlineKeyboardButton("🎙 صوت بصمة (Voice)", callback_data="dl_voice"),
        InlineKeyboardButton("🎧 ملف MP3 (Audio)", callback_data="dl_audio")
    )
    inline_kb.add(InlineKeyboardButton("🎬 فيديو MP4 (Video)", callback_data="dl_video"))

    bot.edit_message_text(
        "✨ **تم استخراج بيانات الرابط بنجاح!**\n\n👇 **اختر طريقة التنزيل أو نوع الملف المطلوب:**",
        chat_id=status_msg.chat.id,
        message_id=status_msg.message_id,
        reply_markup=inline_kb,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_"))
def process_download(call):
    user_id = call.from_user.id
    url = USER_TEMP.get(user_id)

    if not url:
        bot.answer_callback_query(call.id, "⚠️ انتهت مهلة الجلسة، يرجى إعادة إرسال الرابط.", show_alert=True)
        return

    action = call.data.split("_")[1]
    is_audio = action in ["audio", "voice"]
    bot.edit_message_text("📥 **جاري سحب الملف وإرساله... قد يستغرق ذلك بضع ثوانٍ.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    out_file = f"media_{user_id}_{call.id}"

    try:
        # 1. يوتيوب
        if is_youtube_url(url):
            dl_link = download_youtube_via_api(url, is_audio=is_audio)
            if dl_link:
                req = requests.get(dl_link, stream=True, timeout=60)
                file_ext = "mp3" if is_audio else "mp4"
                file_path = f"{out_file}.{file_ext}"

                with open(file_path, "wb") as f:
                    for chunk in req.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)

                with open(file_path, "rb") as f:
                    if action == "voice":
                        bot.send_voice(call.message.chat.id, f)
                    elif action == "audio":
                        bot.send_audio(call.message.chat.id, f)
                    else:
                        bot.send_video(call.message.chat.id, f)

                os.remove(file_path)
                bot.delete_message(call.message.chat.id, call.message.message_id)
                return

        # 2. المنصات الأخرى (فيسبوك، إنستغرام، تيك توك)
        ydl_opts = {
            'outtmpl': f'{out_file}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': 'ba/bestaudio' if is_audio else 'b/bestvideo+bestaudio/best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'تم التحميل بنجاح')

        downloaded_file = None
        for file in os.listdir("."):
            if file.startswith(out_file):
                downloaded_file = file
                break

        if downloaded_file and os.path.exists(downloaded_file):
            with open(downloaded_file, 'rb') as f:
                if action == "voice":
                    bot.send_voice(call.message.chat.id, f, caption=f"🎙 {title[:60]}")
                elif action == "audio":
                    bot.send_audio(call.message.chat.id, f, caption=f"🎧 {title[:60]}")
                else:
                    bot.send_video(call.message.chat.id, f, caption=f"🎬 {title[:60]}")

            os.remove(downloaded_file)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            raise Exception("لم يتم العثور على الملف.")

    except Exception:
        bot.edit_message_text("⚠️ **تعذر جلب الملف حالياً.**\nيرجى التأكد من أن الرابط مباشر أو التجربة مجدداً بعد لحظات.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
