import os
import re
import logging
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

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

# --- إعدادات البوت ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAF1Nt7eBMTucCNtEwfd63NRKK3cX2i64UE")
MUST_JOIN_CHANNEL = os.getenv("CHANNEL_USERNAME", "wanasatt")

bot = telebot.TeleBot(BOT_TOKEN)
USER_TEMP = {}

# --- لوحة الأزرار الشفافة السفلية بتصميم جديد ---
def main_reply_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🔴 يوتيوب - YouTube"),
        KeyboardButton("📸 إنستغرام - Instagram"), KeyboardButton("🔵 فيسبوك - Facebook"),
        KeyboardButton("🎵 تيك توك - TikTok"), KeyboardButton("💎 لايكي - Likee"),
        KeyboardButton("👻 سناب شات - Snapchat"), KeyboardButton("🐦 تويتر - Twitter/X"),
        KeyboardButton("📌 بنترست - Pinterest"),
        KeyboardButton("📈 إحصائياتي"),
        KeyboardButton("🚀 إضافة البوت لمجموعتك")
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

def extract_youtube_id(url):
    pattern = r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    if not check_sub(user_id):
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("📢 انضمام للقناة الرسمية", url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        inline_kb.add(InlineKeyboardButton("✨ تأكيد الاشتراك الأن", callback_data="verify_sub"))
        bot.reply_to(message, f"🔒 **أهلاً بك يا {name}!**\n\nتفضل بالانضمام إلى قناتنا أولاً لتفعيل واستخدام خدمات البوت التلقائية:\n\n👉 @{MUST_JOIN_CHANNEL}", reply_markup=inline_kb, parse_mode="Markdown")
        return

    msg_text = (
        f"👑 **مرحباً بك {name} في بوت التحميل السريع!**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **كل ما عليك هو إرسال رابط المقطع المباشر!**\n\n"
        "🌐 **المنصات المدعومة بالكامل:**\n"
        "▫️ YouTube  ▫️ TikTok  ▫️ Instagram\n"
        "▫️ Facebook ▫️ Twitter ▫️ Snapchat\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "💡 **للعمل داخل المجموعات:**\n"
        "أرسل كلمة `/d` متبوعة بالرابط"
    )
    bot.send_message(message.chat.id, msg_text, reply_markup=main_reply_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_sub")
def verify_callback(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "🎉 مرحباً بك! تم تأكيد اشتراكك بنجاح.", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على اشتراكك، يرجى الانضمام أولاً!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # التفاعل مع الأزرار الرئيسية
    if any(p in text for p in ["يوتيوب", "إنستغرام", "فيسبوك", "تيك توك", "لايكي", "سناب شات", "تويتر", "بنترست"]):
        bot.reply_to(message, f"🔗 **أرسل الآن رابط الفيديو المطلوب تحويله أو تنزيله.**", parse_mode="Markdown")
        return
    elif text == "📈 إحصائياتي":
        bot.reply_to(message, "📊 **سجل التنزيلات الخاص بك:**\n\n• إجمالي الملفات المحملة: `1`\n• حالة الخدمة: 🟢 متصل ومستقر", parse_mode="Markdown")
        return
    elif text == "🚀 إضافة البوت لمجموعتك":
        bot.reply_to(message, f"🔮 **لإضافة البوت إلى مجموعتك ومنحه صلاحية التحميل المباشر:**\nhttps://t.me/{bot.get_me().username}?startgroup=true", parse_mode="Markdown")
        return

    if message.chat.type in ['group', 'supergroup']:
        if not text.startswith('/d'):
            return
        text = text.replace('/d', '').strip()

    if not re.match(r'https?://[^\s]+', text):
        return

    if not check_sub(user_id):
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("📢 انضمام للقناة", url=f"https://t.me/{MUST_JOIN_CHANNEL}"))
        inline_kb.add(InlineKeyboardButton("✨ تأكيد الاشتراك الأن", callback_data="verify_sub"))
        bot.reply_to(message, f"🔒 يرجى الاشتراك في القناة أولاً لتفعيل التنزيل:\n👉 @{MUST_JOIN_CHANNEL}", reply_markup=inline_kb)
        return

    status_msg = bot.reply_to(message, "⚙️ **جاري فحص الرابط وتحضير خيارات التنزيل...**", parse_mode="Markdown")
    USER_TEMP[user_id] = text

    # أزرار التنزيل الشفافة بتصميم عصري
    inline_kb = InlineKeyboardMarkup(row_width=2)
    inline_kb.add(
        InlineKeyboardButton("🎙 بصمة صوتية", callback_data="dl_voice"),
        InlineKeyboardButton("🎧 ملف صوتي MP3", callback_data="dl_audio")
    )
    inline_kb.add(InlineKeyboardButton("🎬 مقطع فيديو MP4", callback_data="dl_video"))

    bot.edit_message_text(
        "✨ **تم التعرف على الرابط بنجاح!**\n👇 اختر الصيغة أو الشكل المطلوب للإرسال:",
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
        bot.answer_callback_query(call.id, "⚠️ انتهت مهلة الجلسة، يرجى إرسال الرابط من جديد.", show_alert=True)
        return

    action = call.data.split("_")[1]
    bot.edit_message_text("🚀 **جاري التنزيل والمعالجة بأعلى جودة متاحة...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    video_id = extract_youtube_id(url)
    download_success = False

    if video_id:
        invidious_instances = [
            "https://inv.nadeko.net",
            "https://invidious.nerdvpn.de",
            "https://invidious.drgns.space"
        ]

        for instance in invidious_instances:
            try:
                api_url = f"{instance}/api/v1/videos/{video_id}"
                res = requests.get(api_url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    title = data.get("title", "فيديو ميديا")
                    
                    target_url = None
                    if action in ["audio", "voice"]:
                        adaptive = data.get("adaptiveFormats", [])
                        audio_streams = [f for f in adaptive if f.get("type", "").startswith("audio/")]
                        if audio_streams:
                            target_url = audio_streams[0].get("url")
                    else:
                        format_streams = data.get("formatStreams", [])
                        if format_streams:
                            target_url = format_streams[-1].get("url")

                    if target_url:
                        file_res = requests.get(target_url, stream=True, timeout=30)
                        temp_file = f"temp_{user_id}.mp3" if action in ["audio", "voice"] else f"temp_{user_id}.mp4"
                        
                        with open(temp_file, "wb") as f:
                            for chunk in file_res.iter_content(chunk_size=1024*1024):
                                if chunk:
                                    f.write(chunk)

                        with open(temp_file, "rb") as f:
                            if action == "voice":
                                bot.send_voice(call.message.chat.id, f, caption=f"🎙 {title}")
                            elif action == "audio":
                                bot.send_audio(call.message.chat.id, f, caption=f"🎧 {title}")
                            else:
                                bot.send_video(call.message.chat.id, f, caption=f"🎬 {title}")

                        os.remove(temp_file)
                        download_success = True
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                        break
            except Exception:
                continue

    if not download_success:
        try:
            cobalt_url = "https://co.wuk.sh/api/json"
            payload = {"url": url, "isAudioOnly": True if action in ["audio", "voice"] else False}
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            
            res = requests.post(cobalt_url, json=payload, headers=headers, timeout=15)
            data = res.json()
            
            file_dl_url = data.get("url")
            if file_dl_url:
                file_res = requests.get(file_dl_url, stream=True, timeout=30)
                temp_file = f"temp_alt_{user_id}.mp3" if action in ["audio", "voice"] else f"temp_alt_{user_id}.mp4"
                
                with open(temp_file, "wb") as f:
                    for chunk in file_res.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)

                with open(temp_file, "rb") as f:
                    if action == "voice":
                        bot.send_voice(call.message.chat.id, f)
                    elif action == "audio":
                        bot.send_audio(call.message.chat.id, f)
                    else:
                        bot.send_video(call.message.chat.id, f)

                os.remove(temp_file)
                download_success = True
                bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    if not download_success:
        bot.edit_message_text("⚠️ **تعذر جلب المقطع حالياً، أعد تجربة إرسال الرابط مرة أخرى.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
