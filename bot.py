import os
import sys
import time
import logging
import asyncio
import sqlite3
import threading
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==========================================
# 0. خادم إبقاء البوت حياً 24/7 (Render Keep-Alive)
# ==========================================
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Bot is running 24/7 Smoothly!</h1>")

    def log_message(self, format, *args):
        return

def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    server.serve_forever()

threading.Thread(target=run_keep_alive, daemon=True).start()

# ==========================================
# 1. التحديث التلقائي لمكتبة التنزيل
# ==========================================
try:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
except Exception:
    pass

# ==========================================
# 2. الإعدادات وتجهيز المجلدات وقواعد البيانات
# ==========================================
BOT_TOKEN = "8629100412:AAFnsQbPXXTjyJro49NXAYe0ut3Z-PoeOu8"
CHANNEL_USERNAME = "@wanasatt"
CHANNEL_URL = "https://t.me/wanasatt"
ADMIN_ID = 123456789  # ضع آيدي حسابه في تلغرام هنا

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

DB = sqlite3.connect("users.db", check_same_thread=False)
CURSOR = DB.cursor()
CURSOR.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    lang TEXT DEFAULT 'ar'
)
""")
DB.commit()

user_quality = {}
broadcast_mode = {}
downloads_count = 0

# ==========================================
# 3. النصوص المحدثة بـ 4 لغات وأيقونات جذابة
# ==========================================
TEXT = {
    "ar": {
        "welcome": (
            "╭━━━ 💎 <b>ULTRA DOWNLOADER V4</b> 💎 ━━━╮\n"
            "│\n"
            "├── ⚡️ <b>مرحباً بك في أسرع بوت تحميل آلي!</b>\n"
            "│\n"
            "├── 🌟 <b>الخدمات والمنصات المدعومة:</b>\n"
            "│  ├ 🌀 YouTube (Videos & Shorts)\n"
            "│  ├ 🎵 TikTok (بدون علامة مائية)\n"
            "│  ├ 📸 Instagram (Reels & Stories)\n"
            "│  └ 🎧 استخراج الصوت بأعلى نقاء MP3\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚙️ <b>اختر جودة التنزيل المطلوبة للبدء:</b>"
        ),
        "need_sub": (
            "╭━━━ ⚠️ <b>اشتراك إجباري للتفعيل</b> ⚠️ ━━━╮\n"
            "│\n"
            "│ 🔰 لضمان مجانية الخدمة والتحميل السريع،\n"
            "│ يرجى الاشتراك بقناتنا الرسمية أولاً.\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
        ),
        "sub_btn": "📢 الانضمام للقناة الرسمية",
        "check_sub": "🔄 اضغط هنا للتفعيل بعد الاشتراك",
        "checking": "🔍 <b>جاري فحص الرابط وفك القيود...</b> ⏳\n\n<code>[░░░░░░░░░░░░░░░░░░░░] 0%</code>",
        "downloading": "📥 <b>جاري تنزيل المحتوى بالسيرفر...</b> 🚀\n\n<code>[{}] {}%</code>",
        "uploading": "📤 <b>جاري إرسال الملف إليك...</b> ⚡️\n\n<code>[████████████████████] 100%</code>",
        "failed": "❌ <b>عذراً، تعذر جلب المقطع!</b>\nتأكد من أن الرابط عام وصحيح ثم حاول مجدداً.",
        "verified": "🎉 <b>تم تفعيل حسابك بنجاح!</b>\n\n🔗 أرسل أي رابط الآن وسأقوم بتحميله فوراً.",
        "not_subbed": "🚫 عذراً، لم تشترك في القناة بعد!",
        "quality_selected": "🎯 <b>تم اختيار الجودة:</b> <code>{}</code>\n\n📥 <b>أرسل رابط المقطع الآن للبدء.</b>",
        "uploader": "المنشئ",
        "duration": "المدة",
        "platform": "المنصة",
        "size": "الحجم",
        "seconds": "ثانية",
        "visit_channel": "✨ القناة الرسمية للبوت",
        "choose_lang": "🌐 <b>اختر لغة واجهة البوت / Choose Language:</b>",
        "lang_changed": "✅ <b>تم تحديث اللغة بنجاح!</b>",
        "best_q": "🔥 الجودة الأقصى (تلقائي)",
        "audio_only": "🎵 صوت فقط (MP3 High Quality)"
    },
    "en": {
        "welcome": (
            "╭━━━ 💎 <b>ULTRA DOWNLOADER V4</b> 💎 ━━━╮\n"
            "│\n"
            "├── ⚡️ <b>Welcome to the fastest downloader!</b>\n"
            "│\n"
            "├── 🌟 <b>Supported Platforms:</b>\n"
            "│  ├ 🌀 YouTube (Videos & Shorts)\n"
            "│  ├ 🎵 TikTok (No Watermark)\n"
            "│  ├ 📸 Instagram (Reels & Stories)\n"
            "│  └ 🎧 High Quality 320kbps MP3 Audio\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚙️ <b>Select your preferred video quality:</b>"
        ),
        "need_sub": (
            "╭━━━ ⚠️ <b>Subscription Required</b> ⚠️ ━━━╮\n"
            "│\n"
            "│ 🔰 Please join our official channel first\n"
            "│ to unlock unlimited downloads.\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
        ),
        "sub_btn": "📢 Join Official Channel",
        "check_sub": "🔄 Verify Subscription Now",
        "checking": "🔍 <b>Analyzing link and bypassing limits...</b> ⏳\n\n<code>[░░░░░░░░░░░░░░░░░░░░] 0%</code>",
        "downloading": "📥 <b>Downloading content to server...</b> 🚀\n\n<code>[{}] {}%</code>",
        "uploading": "📤 <b>Sending file to you...</b> ⚡️\n\n<code>[████████████████████] 100%</code>",
        "failed": "❌ <b>Download Failed!</b>\nEnsure the link is correct and public.",
        "verified": "🎉 <b>Account Verified!</b>\n\n🔗 Send any media link now to start downloading.",
        "not_subbed": "🚫 You haven't joined the channel yet!",
        "quality_selected": "🎯 <b>Selected Quality:</b> <code>{}</code>\n\n📥 <b>Send media link now.</b>",
        "uploader": "Uploader",
        "duration": "Duration",
        "platform": "Platform",
        "size": "Size",
        "seconds": "sec",
        "visit_channel": "✨ Official Channel",
        "choose_lang": "🌐 <b>Choose Interface Language:</b>",
        "lang_changed": "✅ <b>Language updated successfully!</b>",
        "best_q": "🔥 Maximum Auto Quality",
        "audio_only": "🎵 Audio Only (MP3 HQ)"
    },
    "tr": {
        "welcome": (
            "╭━━━ 💎 <b>ULTRA DOWNLOADER V4</b> 💎 ━━━╮\n"
            "│\n"
            "├── ⚡️ <b>En hızlı indirme botuna hoş geldiniz!</b>\n"
            "│\n"
            "├── 🌟 <b>Desteklenen Platformlar:</b>\n"
            "│  ├ 🌀 YouTube (Videolar & Shorts)\n"
            "│  ├ 🎵 TikTok (Filigransız)\n"
            "│  ├ 📸 Instagram (Reels & Hikayeler)\n"
            "│  └ 🎧 Yüksek Kalite MP3 Ses\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚙️ <b>Lütfen video kalitesini seçin:</b>"
        ),
        "need_sub": (
            "╭━━━ ⚠️ <b>Zorunlu Kanal Aboneliği</b> ⚠️ ━━━╮\n"
            "│\n"
            "│ 🔰 Sınırsız indirme yapmak için lütfen\n"
            "│ önce resmi kanalımıza katılın.\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
        ),
        "sub_btn": "📢 Resmi Kanalımız",
        "check_sub": "🔄 Aboneliği Doğrula",
        "checking": "🔍 <b>Bağlantı analiz ediliyor...</b> ⏳\n\n<code>[░░░░░░░░░░░░░░░░░░░░] 0%</code>",
        "downloading": "📥 <b>İçerik sunucuya indiriliyor...</b> 🚀\n\n<code>[{}] {}%</code>",
        "uploading": "📤 <b>Dosya size gönderiliyor...</b> ⚡️\n\n<code>[████████████████████] 100%</code>",
        "failed": "❌ <b>İndirme Başarısız!</b>\nBağlantının geçerli olduğundan emin olun.",
        "verified": "🎉 <b>Abonelik Doğrulandı!</b>\n\n🔗 Bağlantıyı hemen gönderebilirsiniz.",
        "not_subbed": "🚫 Henüz kanala katılmadınız!",
        "quality_selected": "🎯 <b>Seçilen Kalite:</b> <code>{}</code>\n\n📥 <b>Medya bağlantısını gönderin.</b>",
        "uploader": "Yayıncı",
        "duration": "Süre",
        "platform": "Platform",
        "size": "Boyut",
        "seconds": "sn",
        "visit_channel": "✨ Resmi Kanalımızı Ziyaret Edin",
        "choose_lang": "🌐 <b>Arayüz Dilini Seçin:</b>",
        "lang_changed": "✅ <b>Dil başarıyla güncellendi!</b>",
        "best_q": "🔥 En Yüksek Kalite (Otomatik)",
        "audio_only": "🎵 Sadece Ses (MP3 Yüksek Kalite)"
    },
    "ru": {
        "welcome": (
            "╭━━━ 💎 <b>ULTRA DOWNLOADER V4</b> 💎 ━━━╮\n"
            "│\n"
            "├── ⚡️ <b>Добро пожаловать в быстрый загрузчик!</b>\n"
            "│\n"
            "├── 🌟 <b>Поддерживаемые платформы:</b>\n"
            "│  ├ 🌀 YouTube (Видео и Shorts)\n"
            "│  ├ 🎵 TikTok (Без водяного знака)\n"
            "│  ├ 📸 Instagram (Reels и Истории)\n"
            "│  └ 🎧 Высокое качество MP3 320kbps\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚙️ <b>Выберите качество видео:</b>"
        ),
        "need_sub": (
            "╭━━━ ⚠️ <b>Обязательная подписка</b> ⚠️ ━━━╮\n"
            "│\n"
            "│ 🔰 Пожалуйста, подпишитесь на наш\n"
            "│ канал, чтобы разблокировать функции.\n"
            "│\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯"
        ),
        "sub_btn": "📢 Официальный канал",
        "check_sub": "🔄 Проверить подписку",
        "checking": "🔍 <b>Анализ ссылки и обход ограничений...</b> ⏳\n\n<code>[░░░░░░░░░░░░░░░░░░░░] 0%</code>",
        "downloading": "📥 <b>Скачивание файла на сервер...</b> 🚀\n\n<code>[{}] {}%</code>",
        "uploading": "📤 <b>Отправка файла вам...</b> ⚡️\n\n<code>[████████████████████] 100%</code>",
        "failed": "❌ <b>Ошибка скачивания!</b>\nПроверьте правильность ссылки.",
        "verified": "🎉 <b>Успешно активировано!</b>\n\n🔗 Отправьте ссылку на видео.",
        "not_subbed": "🚫 Вы еще не подписались!",
        "quality_selected": "🎯 <b>Выбранное качество:</b> <code>{}</code>\n\n📥 <b>Отправьте ссылку прямо сейчас.</b>",
        "uploader": "Автор",
        "duration": "Длительность",
        "platform": "Платформа",
        "size": "Размер",
        "seconds": "сек",
        "visit_channel": "✨ Наш официальный канал",
        "choose_lang": "🌐 <b>Выберите язык интерфейса:</b>",
        "lang_changed": "✅ <b>Язык успешно изменен!</b>",
        "best_q": "🔥 Максимальное качество",
        "audio_only": "🎵 Только аудио (MP3 HQ)"
    }
}

# ==========================================
# 4. دالة شريط التقدم المتدرج (Progress Bar)
# ==========================================
def make_progress_bar(percent: int) -> str:
    total_blocks = 20
    filled_blocks = int(round(total_blocks * (percent / 100)))
    bar = "█" * filled_blocks + "░" * (total_blocks - filled_blocks)
    return bar

# ==========================================
# 5. إدارة قواعد البيانات واللغات
# ==========================================
def register_user(user_id: int, default_lang: str = "ar"):
    lang = default_lang if default_lang in TEXT else "ar"
    CURSOR.execute("INSERT OR IGNORE INTO users (id, lang) VALUES(?, ?)", (user_id, lang))
    DB.commit()

def set_user_lang(user_id: int, lang: str):
    CURSOR.execute("UPDATE users SET lang = ? WHERE id = ?", (lang, user_id))
    DB.commit()

def get_user_lang(user_id: int) -> str:
    CURSOR.execute("SELECT lang FROM users WHERE id = ?", (user_id,))
    res = CURSOR.fetchone()
    return res[0] if res and res[0] in TEXT else "ar"

def add_download():
    global downloads_count
    downloads_count += 1

def clean_downloads():
    now = time.time()
    for file in DOWNLOAD_DIR.iterdir():
        try:
            if now - file.stat().st_mtime > 3600:
                file.unlink()
        except Exception:
            pass

# ==========================================
# 6. الأزرار اللوحية والتفاعلية
# ==========================================
async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return True

def force_keyboard(lang: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXT[lang]["sub_btn"], url=CHANNEL_URL)],
        [InlineKeyboardButton(TEXT[lang]["check_sub"], callback_data="check_sub")]
    ])

def quality_keyboard(lang: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 360p", callback_data="360"),
            InlineKeyboardButton("🎬 720p HD", callback_data="720"),
            InlineKeyboardButton("🎬 1080p FHD", callback_data="1080"),
        ],
        [InlineKeyboardButton(TEXT[lang]["best_q"], callback_data="best")],
        [InlineKeyboardButton(TEXT[lang]["audio_only"], callback_data="mp3")]
    ])

def language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
        ],
        [
            InlineKeyboardButton("🇹🇷 Türkçe", callback_data="set_lang_tr"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        ]
    ])

def channel_button_under_video(lang: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXT[lang]["visit_channel"], url=CHANNEL_URL)]
    ])

# ==========================================
# 7. إعدادات yt-dlp للتمويه وتجاوز القيود
# ==========================================
def build_ydl_opts(output: str, quality: str):
    common_opts = {
        "outtmpl": output,
        "quiet": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "mweb", "android"],
                "skip": ["dash", "hls"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
        }
    }

    if os.path.exists("cookies.txt"):
        common_opts["cookiefile"] = "cookies.txt"

    if quality == "360":
        fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]"
    elif quality == "720":
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif quality == "1080":
        fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif quality == "mp3":
        common_opts.update({
            "format": "bestaudio/best",
            "extract_audio": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]
        })
        return common_opts
    else:
        fmt = "bestvideo+bestaudio/best"

    common_opts["format"] = fmt
    common_opts["merge_output_format"] = "mp4"
    return common_opts

# ==========================================
# 8. معالجة الأوامر والردود
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_lang_code = user.language_code[:2] if user.language_code else "ar"
    register_user(user.id, user_lang_code)
    lang = get_user_lang(user.id)

    if not await is_subscribed(context, user.id):
        await update.message.reply_text(
            TEXT[lang]["need_sub"],
            reply_markup=force_keyboard(lang),
            parse_mode="HTML"
        )
        return

    await update.message.reply_text(
        TEXT[lang]["welcome"],
        reply_markup=quality_keyboard(lang),
        parse_mode="HTML"
    )

async def set_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    await update.message.reply_text(
        TEXT[lang]["choose_lang"],
        reply_markup=language_keyboard(),
        parse_mode="HTML"
    )

async def check_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_user_lang(query.from_user.id)

    if await is_subscribed(context, query.from_user.id):
        await query.edit_message_text(TEXT[lang]["verified"], parse_mode="HTML")
    else:
        await query.answer(TEXT[lang]["not_subbed"], show_alert=True)

async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    lang = get_user_lang(query.from_user.id)
    user_quality[query.from_user.id] = choice
    
    quality_name = {
        "360": "360p Standard",
        "720": "720p HD",
        "1080": "1080p Full HD",
        "best": "🔥 Maximum Quality",
        "mp3": "🎵 High Quality MP3"
    }.get(choice, choice)

    msg_text = TEXT[lang]["quality_selected"].format(quality_name)
    await query.edit_message_text(msg_text, parse_mode="HTML")

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_lang = query.data.replace("set_lang_", "")
    
    set_user_lang(query.from_user.id, selected_lang)
    await query.edit_message_text(TEXT[selected_lang]["lang_changed"], parse_mode="HTML")

# ==========================================
# 9. محرك التحميل التفاعلي
# ==========================================
async def handle_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    register_user(user.id)
    lang = get_user_lang(user.id)

    if user.id == ADMIN_ID and broadcast_mode.get(user.id):
        await receive_broadcast(update, context)
        return

    if not await is_subscribed(context, user.id):
        await update.message.reply_text(
            TEXT[lang]["need_sub"],
            reply_markup=force_keyboard(lang),
            parse_mode="HTML"
        )
        return

    text = update.message.text.strip()
    if not text.startswith(("http://", "https://")):
        return

    status = await update.message.reply_text(TEXT[lang]["checking"], parse_mode="HTML")
    quality = user_quality.get(user.id, "best")
    output = str(DOWNLOAD_DIR / f"{user.id}_{int(time.time())}_%(title)s.%(ext)s")

    loop = asyncio.get_running_loop()

    def worker():
        opts = build_ydl_opts(output, quality)
        with yt_dlp.YoutubeDL(opts) as ydl:
            inf = ydl.extract_info(text, download=True)
            fpath = ydl.prepare_filename(inf)
            
            if quality == "mp3":
                fpath = os.path.splitext(fpath)[0] + ".mp3"

            if not os.path.exists(fpath):
                base = os.path.splitext(fpath)[0]
                for ext in (".mp4", ".mkv", ".webm", ".mov", ".mp3"):
                    if os.path.exists(base + ext):
                        fpath = base + ext
                        break
            return inf, fpath

    download_task = loop.run_in_executor(None, worker)

    # حلقة شريط التقدم الحركي
    progress_steps = [15, 35, 60, 85]
    for step in progress_steps:
        if download_task.done():
            break
        await asyncio.sleep(1.2)
        try:
            bar_str = make_progress_bar(step)
            await status.edit_text(TEXT[lang]["downloading"].format(bar_str, step), parse_mode="HTML")
        except Exception:
            pass

    try:
        info, file_path = await download_task
    except Exception as e:
        logging.exception(e)
        await status.edit_text(
            f"{TEXT[lang]['failed']}\n\n<code>{e}</code>",
            parse_mode="HTML",
        )
        return

    try:
        await status.edit_text(TEXT[lang]["uploading"], parse_mode="HTML")

        title = info.get("title", "Media File")
        uploader = info.get("uploader", "Unknown")
        duration = info.get("duration", 0)
        extractor = info.get("extractor_key", "Media")
        size = os.path.getsize(file_path) / (1024 * 1024)

        caption = (
            f"🎬 <b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>{TEXT[lang]['uploader']}:</b> {uploader}\n"
            f"⏱ <b>{TEXT[lang]['duration']}:</b> {duration} {TEXT[lang]['seconds']}\n"
            f"🌐 <b>{TEXT[lang]['platform']}:</b> {extractor}\n"
            f"📦 <b>{TEXT[lang]['size']}:</b> {size:.2f} MB"
        )

        video_keyboard = channel_button_under_video(lang)
        
        with open(file_path, "rb") as media_file:
            if quality == "mp3":
                await update.message.reply_audio(
                    audio=media_file, 
                    caption=caption, 
                    parse_mode="HTML", 
                    reply_markup=video_keyboard
                )
            else:
                await update.message.reply_video(
                    video=media_file, 
                    caption=caption, 
                    parse_mode="HTML", 
                    reply_markup=video_keyboard
                )

        await status.delete()
        add_download()

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        logging.exception(e)
        await status.edit_text(
            f"{TEXT[lang]['failed']}\n\n<code>{e}</code>",
            parse_mode="HTML",
        )

# ==========================================
# 10. أوامر لوحة تحكم المسؤول (Admin)
# ==========================================
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    CURSOR.execute("SELECT COUNT(*) FROM users")
    total = CURSOR.fetchone()[0]
    await update.message.reply_text(f"👥 <b>إجمالي مستخدمي البوت:</b> <code>{total}</code>", parse_mode="HTML")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    CURSOR.execute("SELECT COUNT(*) FROM users")
    total = CURSOR.fetchone()[0]
    text = (
        "📊 <b>إحصائيات النظام الكلية</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>عدد المستخدمين:</b> {total}\n"
        f"📥 <b>إجمالي التحميلات الناجحة:</b> {downloads_count}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    broadcast_mode[update.effective_user.id] = True
    await update.message.reply_text("📢 <b>أرسل الرسالة المطلوبة لإذاعتها للجميع:</b>", parse_mode="HTML")

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    broadcast_mode.pop(uid, None)

    text = update.message.text
    CURSOR.execute("SELECT id FROM users")
    users = CURSOR.fetchall()

    sent, failed = 0, 0
    msg = await update.message.reply_text("🚀 <b>جاري إرسال الإذاعة...</b>", parse_mode="HTML")

    for user in users:
        try:
            await context.bot.send_message(user[0], text)
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1

    await msg.edit_text(
        f"✨ <b>تمت الإذاعة بنجاح!</b>\n\n🎯 <b>وصلت لـ:</b> {sent}\n❌ <b>فشل مع:</b> {failed}",
        parse_mode="HTML"
    )

# ==========================================
# 11. نقطة الانطلاق التشغيلية
# ==========================================
def main():
    clean_downloads()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", set_language_command))

    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    app.add_handler(CallbackQueryHandler(check_button, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(quality_callback, pattern="^(360|720|1080|best|mp3)$"))
    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^set_lang_"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media_download))

    print("🚀 Ultra Bot V4 active and listening 24/7...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
