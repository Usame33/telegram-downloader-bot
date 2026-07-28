import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- 1. إعداد تطبيق Flask لإبقاء السيرفر حياً ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# --- 2. إعدادات التليجرام والمصادر ---
TOKEN = os.environ.get("TOKEN")
CHANNEL = "@wanasatt"
CHANNEL_LINK = "https://t.me/wanasatt"
BOT_LINK = "https://t.me/Ussame_bot"

bot = telebot.TeleBot(TOKEN)

# --- 3. إدارة الإحصائيات والمستخدمين ---
def update_users(user_id):
    users_file = "users.txt"
    users = set()
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = set(f.read().splitlines())
    
    users.add(str(user_id))
    with open(users_file, "w") as f:
        f.write("\n".join(users))

# --- 4. التحقق من الاشتراك الإجباري ---
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
    btn_check = InlineKeyboardButton("🫆 تأكيد الاشتراك", callback_data="check_sub")
    markup.add(btn_link)
    markup.add(btn_check)
    return markup

# --- 5. أوامر البوت (/start و /stats) ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    update_users(message.from_user.id)
    
    if not check_sub(message.from_user.id):
        bot.send_message(
            message.chat.id, 
            "⚠️ عذراً، يجب عليك الاشتراك في القناة لاستخدام البوت:", 
            reply_markup=sub_keyboard()
        )
        return

    bot.reply_to(message, "مرحباً بك! أرسل لي رابط الفيديو الذي تريد تحميله 🚀")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    users_file = "users.txt"
    total_users = 0
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            total_users = len(f.read().splitlines())
            
    bot.reply_to(
        message, 
        f"📊 **إحصائيات البوت الحالية:**\n\n👥 إجمالي عدد المستخدمين: `{total_users}`", 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "🫆 تم التحقق بنجاح! شكراً لاشتراكك")
        bot.send_message(call.message.chat.id, "أرسل لي الآن رابط الفيديو الذي تريد تحميله.")
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك في القناة بعد!", show_alert=True)

# --- 6. معالجة الروابط والتحميل ---
def download_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        print(f"جاري التحميل: {percent}")

@bot.message_handler(func=lambda message: True)
def process_video_request(message):
    update_users(message.from_user.id)
    
    if not check_sub(message.from_user.id):
        bot.send_message(
            message.chat.id, 
            "⚠️ يجب عليك الاشتراك في القناة أولاً لتتمكن من التحميل:", 
            reply_markup=sub_keyboard()
        )
        return

    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ يرجى إرسال رابط فيديو صحيح.")
        return

    msg = bot.reply_to(message, "⏳ جاري جلب المعلومات وتحميل الفيديو...")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'video_{message.from_user.id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [download_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'فيديو بدون عنوان')
            uploader = info.get('uploader', 'غير معروف')

        # تجهيز الحقوق والمعلومات مع إيقونة البصمة 🫆
        caption = (
            f"🎬 **{title}**\n"
            f"👤 الناشر: {uploader}\n\n"
            f"📢 القناة: {CHANNEL_LINK}\n"
            f"🫆 البوت: {BOT_LINK}"
        )

        # إرسال الفيديو للمستخدم
        with open(filename, 'rb') as video:
            bot.send_video(
                message.chat.id, 
                video, 
                caption=caption, 
                parse_mode="Markdown",
                reply_to_message_id=message.message_id
            )

        # تنظيف وتحسين
        if os.path.exists(filename):
            os.remove(filename)

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء التحميل: {e}")

# --- 7. تشغيل البوت ---
bot.infinity_polling()
