import os
import logging
import asyncio
import sqlite3
import threading
import time
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, CallbackQueryHandler, filters
)
import yt_dlp

# ----------------- خادم الويب لإبقاء البوت مستيقظاً -----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ----------------- الإعدادات وسجلات الأخطاء -----------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAFn_wgwwO_ZN_ifYyGqdADlvU-IZDUkgZY")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@wanasatt")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8904859256"))

# قفل التزامن لمنع المستخدم من تحميل أكثر من رابط في نفس الوقت
user_locks = {}
user_links = {}

# ----------------- النصوص متعددة اللغات -----------------
MESSAGES = {
    'ar': {
        'welcome': "أهلاً بك يا {name}! 🌸\n\nيسعدنا استخدامك لبوت التحميل السريع! ⚡\nلاستخدام البوت والاستفادة من خدماته، يرجى الاشتراك في القناة أولاً.",
        'welcome_subbed': "🎉 أهلاً بك يا {name}!\n\nيمكنك الآن إرسال أي رابط فيديو من (يوتيوب، تيك توك، إنستغرام، فيسبوك) وسيتم تحميله فوراً.",
        'sub_btn': "📢 اشترك في القناة",
        'check_sub_btn': "🫆 تحقق من الاشتراك",
        'sub_success': "✅ تم التحقق من اشتراكك بنجاح.\n\n🎉 يمكنك الآن إرسال أي رابط فيديو.",
        'sub_failed': "❌ لم تقم بالاشتراك في القناة بعد! اشترك ثم اضغط تحقق.",
        'busy': "⚠️ لديك عملية تحميل قيد المعالجة حالياً! يرجى الانتظار حتى تنتهي.",
        'invalid_link': "❌ يرجى إرسال رابط فيديو صالح.",
        'downloading': "⏳ جاري بدء التحميل والمكافأة...",
        'uploading': "📤 جاري رفع الفيديو إلى تلغرام...",
        'error': "❌ حدث خطأ غير متوقع أثناء معالجة الرابط. يرجى المحاولة لاحقاً.",
        'lang_set': "✅ تم تغيير اللغة إلى العربية.",
        'stats_user': "📊 عدد تحميلاتك الكلي: {count} فيديو."
    },
    'en': {
        'welcome': "Welcome {name}! 🌸\n\nTo use this bot, please subscribe to our official channel first.",
        'welcome_subbed': "🎉 Welcome {name}!\n\nYou can now send any video link to download immediately.",
        'sub_btn': "📢 Subscribe to Channel",
        'check_sub_btn': "🫆 Check Subscription",
        'sub_success': "✅ Subscription verified successfully.\n\n🎉 You can now send any video link.",
        'sub_failed': "❌ You haven't subscribed yet! Please subscribe and check again.",
        'busy': "⚠️ You already have an active download! Please wait.",
        'invalid_link': "❌ Please send a valid video URL.",
        'downloading': "⏳ Starting download...",
        'uploading': "📤 Uploading video to Telegram...",
        'error': "❌ An unexpected error occurred. Please try again later.",
        'lang_set': "✅ Language set to English.",
        'stats_user': "📊 Your total downloads: {count} videos."
    },
    'tr': {
        'welcome': "Hoş geldiniz {name}! 🌸\n\nBotu kullanmak için lütfen önce kanalımıza abone olun.",
        'welcome_subbed': "🎉 Hoş geldiniz {name}!\n\nArtık indirmek istediğiniz فيديو bağlantısını gönderebilirsiniz.",
        'sub_btn': "📢 Kanala Abone Ol",
        'check_sub_btn': "🫆 Aboneliği Kontrol Et",
        'sub_success': "✅ Aboneliğiniz başarıyla doğrulandı.\n\n🎉 Şimdi bir فيديو bağlantısı gönderebilirsiniz.",
        'sub_failed': "❌ Henüz abone olmadınız! Lütfen abone olup tekrar deneyin.",
        'busy': "⚠️ Halihazırda devam eden bir indirme işleminiz var!",
        'invalid_link': "❌ Lütfen geçerli bir فيديو bağlantısı gönderin.",
        'downloading': "⏳ İndirme başlatılıyor...",
        'uploading': "📤 Telegram'a yükleniyor...",
        'error': "❌ Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
        'lang_set': "✅ Dil Türkçe olarak ayarlandı.",
        'stats_user': "📊 Toplam indirmeleriniz: {count} فيديو."
    }
}

# ----------------- قاعدة البيانات (SQLite) -----------------
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'ar',
            downloads_count INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS downloads_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            platform TEXT,
            download_date DATE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            url TEXT PRIMARY KEY,
            file_id TEXT,
            caption TEXT,
            thumb_id TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user_data(user_id: int):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT lang, downloads_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, lang, downloads_count) VALUES (?, 'ar', 0)", (user_id,))
        conn.commit()
        row = ('ar', 0)
    conn.close()
    return {'lang': row[0], 'downloads_count': row[1]}

def set_user_lang(user_id: int, lang: str):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def log_download(user_id: int, url: str):
    domain = urlparse(url).netloc.replace('www.', '').split('.')[0]
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET downloads_count = downloads_count + 1 WHERE user_id = ?", (user_id,))
    cursor.execute("INSERT INTO downloads_log (user_id, platform, download_date) VALUES (?, ?, ?)", (user_id, domain, today))
    conn.commit()
    conn.close()

def get_cached_file(url: str):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption, thumb_id FROM cache WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_to_cache(url: str, file_id: str, caption: str, thumb_id: str = None):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO cache (url, file_id, caption, thumb_id) VALUES (?, ?, ?, ?)", (url, file_id, caption, thumb_id))
    conn.commit()
    conn.close()

init_db()

# ----------------- الدعم والتحقق من الاشتراك -----------------
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Subscription Check Error: {e}")
    return False

def format_duration(seconds):
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# ----------------- الأوامر والوظائف الأساسية -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_user_data(user.id)
    lang = u_data['lang']
    
    is_subbed = await check_subscription(user.id, context)
    
    keyboard = [
        [InlineKeyboardButton(MESSAGES[lang]['sub_btn'], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(MESSAGES[lang]['check_sub_btn'], callback_data="check_sub")],
        [InlineKeyboardButton("🌐 Language / اللغة", callback_data="change_lang")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not is_subbed:
        await update.message.reply_text(
            MESSAGES[lang]['welcome'].format(name=user.first_name),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            MESSAGES[lang]['welcome_subbed'].format(name=user.first_name),
            reply_markup=reply_markup
        )

# أزرار التفاعل والإعدادات
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    u_data = get_user_data(user_id)
    lang = u_data['lang']
    data = query.data
    
    if data == "check_sub":
        if await check_subscription(user_id, context):
            await query.message.edit_text(MESSAGES[lang]['sub_success'])
        else:
            await query.answer(MESSAGES[lang]['sub_failed'], show_alert=True)
            
    elif data == "change_lang":
        keyboard = [
            [InlineKeyboardButton("العربية 🇸🇦", callback_data="set_lang_ar")],
            [InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")],
            [InlineKeyboardButton("Türkçe 🇹🇷", callback_data="set_lang_tr")]
        ]
        await query.message.edit_text("اختر اللّغة / Choose Language:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif data.startswith("set_lang_"):
        new_lang = data.split("_")[2]
        set_user_lang(user_id, new_lang)
        await query.message.edit_text(MESSAGES[new_lang]['lang_set'])
        
    elif data.startswith("dl_"):
        if user_id not in user_links:
            await query.message.edit_text(MESSAGES[lang]['invalid_link'])
            return
            
        url = user_links[user_id]
        quality = data.split("_")[1]
        
        # حظر المعالجات المتعددة لنفس المستخدم
        if user_locks.get(user_id, False):
            await query.message.reply_text(MESSAGES[lang]['busy'])
            return
            
        user_locks[user_id] = True
        status_msg = await query.message.edit_text(MESSAGES[lang]['downloading'])
        
        try:
            await download_and_process(update, context, url, quality, status_msg, lang)
        finally:
            user_locks[user_id] = False

# استقبال الروابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    u_data = get_user_data(user_id)
    lang = u_data['lang']
    
    if not await check_subscription(user_id, context):
        await start(update, context)
        return

    text = update.message.text
    if not text or not (text.startswith("http://") or text.startswith("https://")):
        await update.message.reply_text(MESSAGES[lang]['invalid_link'])
        return

    if user_locks.get(user_id, False):
        await update.message.reply_text(MESSAGES[lang]['busy'])
        return

    # التخزين المؤقت (Cache Check)
    cached = get_cached_file(text)
    if cached:
        file_id, caption, thumb_id = cached
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_VIDEO)
        channel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 قناة البوت", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]])
        await update.message.reply_video(video=file_id, caption=caption, parse_mode="Markdown", reply_markup=channel_btn)
        log_download(user_id, text)
        return

    user_links[user_id] = text

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو | 1080p 🔥", callback_data="dl_1080")],
        [InlineKeyboardButton("✨ فيديو | 720p 🌟", callback_data="dl_720")],
        [InlineKeyboardButton("⚡ فيديو | 480p ⚡", callback_data="dl_480")],
        [InlineKeyboardButton("🎵 صوت فقط | MP3 🎧", callback_data="dl_mp3")]
    ]
    await update.message.reply_text("🎬 **اختر الجودة المطلوب تحميلها:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ----------------- عملية التحميل والمعالجة -----------------
async def download_and_process(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, quality: str, status_msg, lang: str):
    chat_id = update.effective_chat.id
    output_template = f"downloads/{chat_id}_%(id)s.%(ext)s"
    os.makedirs("downloads", exist_ok=True)
    
    # إرسال حالة "جاري تسجيل/رفع الفيديو"
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VIDEO)

    ydl_opts = {
        'outtmpl': output_template,
        'writethumbnail': True,
        'noplaylist': True,
        'geo_bypass': True,
    }

    if quality == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
    elif quality == "1080":
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
    elif quality == "720":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
    else:
        ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'

    file_path = None
    thumb_path = None

    try:
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fn = ydl.prepare_filename(info)
                if quality == "mp3":
                    fn = os.path.splitext(fn)[0] + ".mp3"
                
                # البحث عن الصورة المصغرة الاستخراجية
                t_path = None
                base_name = os.path.splitext(fn)[0]
                for ext in ['.jpg', '.png', '.webp']:
                    if os.path.exists(base_name + ext):
                        t_path = base_name + ext
                        break
                return fn, info, t_path

        file_path, info_dict, thumb_path = await asyncio.to_thread(run_dl)

        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text(MESSAGES[lang]['error'])
            return

        await status_msg.edit_text(MESSAGES[lang]['uploading'])
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

        # استخراج التفاصيل وتنسيق الرسالة المطلوبة
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        uploader = info_dict.get('uploader') or info_dict.get('uploader_id') or '@username'
        duration_str = format_duration(info_dict.get('duration', 0))

        caption_text = (
            "✅ **تم التحميل بنجاح**\n\n"
            f"📦 **الحجم:** {file_size_mb:.1f} MB\n"
            f"🎥 **الجودة:** {quality if quality != 'mp3' else 'MP3 Audio'}\n"
            f"👤 **الناشر:** {uploader}\n"
            f"⏱️ **المدة:** {duration_str}\n\n"
            "━━━━━━━━━━━━━━\n"
            "📢 **قناة البوت:**\n"
            f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}\n"
            "━━━━━━━━━━━━━━"
        )

        channel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 قناة البوت", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]])

        # فتح الملف وإرساله
        with open(file_path, 'rb') as f:
            thumb_file = open(thumb_path, 'rb') if thumb_path and os.path.exists(thumb_path) else None
            
            if quality == "mp3":
                sent_msg = await context.bot.send_audio(
                    chat_id=chat_id, audio=f, caption=caption_text,
                    reply_markup=channel_btn, parse_mode="Markdown"
                )
                file_id = sent_msg.audio.file_id
            else:
                sent_msg = await context.bot.send_video(
                    chat_id=chat_id, video=f, thumbnail=thumb_file, caption=caption_text,
                    reply_markup=channel_btn, parse_mode="Markdown"
                )
                file_id = sent_msg.video.file_id

            if thumb_file:
                thumb_file.close()

        # حفظ الرابط في الـ Cache لسرعة الإرسال لاحقاً
        add_to_cache(url, file_id, caption_text)
        log_download(update.effective_user.id, url)
        
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error during processing: {e}")
        await status_msg.edit_text(MESSAGES[lang]['error'])

    finally:
        # نظافة السيرفر وحذف الملفات المؤقتة
        for p in [file_path, thumb_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

# ----------------- لوحة تحكم المالك الإحصائية (/stats) -----------------
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM downloads_log WHERE download_date = ?", (today,))
    today_downloads = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM downloads_log")
    total_downloads = cursor.fetchone()[0]

    cursor.execute("SELECT platform, COUNT(*) as c FROM downloads_log GROUP BY platform ORDER BY c DESC LIMIT 3")
    top_platforms = cursor.fetchall()
    conn.close()

    platforms_str = "\n".join([f"• {p[0].capitalize()}: `{p[1]}` عملية" for p in top_platforms]) or "لا توجد بيانات كافية"

    msg = (
        "📈 **لوحة إدارة وإحصائيات البوت:**\n\n"
        f"👤 **عدد المستخدمين الكلي:** `{total_users}` مستخدم\n"
        f"📥 **تحميلات اليوم:** `{today_downloads}` فيديو\n"
        f"📊 **إجمالي التحميلات:** `{total_downloads}` عملية\n\n"
        f"🌐 **أكثر المنصات استخداماً:**\n{platforms_str}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ----------------- تشغيل التطبيق -----------------
def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Professional Downloader Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
