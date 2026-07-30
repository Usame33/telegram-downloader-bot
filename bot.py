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
# 0. خادم إبقاء البوت حياً 24/7 وإرضاء Render
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
    print(f"⚡ Keep-Alive Server active on port {port}")
    server.serve_forever()

threading.Thread(target=run_keep_alive, daemon=True).start()

# ==========================================
# 1. التحديث التلقائي للمكتبات
# ==========================================
try:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
except Exception as e:
    print(f"Warning updating yt-dlp: {e}")

# ==========================================
# 2. الإعدادات والروابط الرئيسية
# ==========================================
BOT_TOKEN = "8629100412:AAFnsQbPXXTjyJro49NXAYe0ut3Z-PoeOu8"
CHANNEL_USERNAME = "@wanasatt"
CHANNEL_URL = "https://t.me/wanasatt"
ADMIN_ID = 123456789  # قم بتغييره لمعرفك الشخصي (Telegram User ID)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

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
# 3. النصوص بتصميم عصري وأيقونات تفاعلية
# ==========================================
TEXT = {
    "ar": {
        "welcome": (
            "╭━━━ Network Media Downloader ━━━╮\n"
            "│ ⚡️ <b>مرحباً بك في البوت المطور للتحميل</b>\n"
            "├─── 🌟 <b>المميزات:</b>\n"
            "│ 💎 تحميل سريع وبأعلى جودة متاحة\n"
            "│ 🌀 دعم (YouTube, TikTok, Instagram, ...)\n"
            "│ 🎧 استخراج الصوت بأعلى نقاء MP3\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚙️ <b>اختر الجودة المطلوبة قبل إرسال الرابط:</b>"
        ),
        "need_sub": (
            "⚠️ <b>تنبيه: الاشتراك إجباري لاستخدام البوت!</b>\n\n"
            "🔰 لدعم الاستمرار والتحميل السريع بدون حدود، يرجى الاشتراك في القناة أولاً ثم اضغط على زر التفعيل بالأسفل 👇"
        ),
        "sub_btn": "📢 رابط القناة الرسمية",
        "check_sub": "🔄 اضغط هنا بعد الاشتراك للتفعيل",
        "checking": "🔍 <b>جاري تحليل الرابط وتجاوز القيود...</b> ⏳",
        "downloading": "📥 <b>جاري تنزيل المحتوى بالسيرفر...</b> 🚀",
        "uploading": "📤 <b>جاري رفعه إليك فوراً...</b> ⚡️",
        "failed": "❌ <b>عذراً، تعذر جلب هذا المقطع!</b>\nتأكد من صحة الرابط أو جرب رابطاً آخر.",
        "verified": "🎉 <b>تم تفعيل الحساب بنجاح!</b>\n\n🔗 أرسل أي رابط الآن وسأقوم بتحميله فوراً.",
        "not_subbed": "🚫 عذراً، لم تشترك في القناة بعد!",
        "quality_selected": "🎯 <b>تم اختيار الجودة:</b> <code>{}</code>\n\n📥 <b>أرسل رابط الفيديو الآن للبدء.</b>",
        "uploader": "المنشئ",
        "duration": "المدة",
        "platform": "المنصة",
        "size": "الحجم",
        "seconds": "ثانية",
        "visit_channel": "✨ اضغط هنا لزيارة قناتنا الرسمية",
        "choose_lang": "🌐 <b>اختر لغة واجهة البوت / Language:</b>",
        "lang_changed": "✅ <b>تم حفظ اللغة بنجاح!</b>",
        "best_q": "🔥 الجودة الأقصى تلقائياً",
        "audio_only": "🎵 صوت فقط (MP3 320kbps)"
    },
    "en": {
        "welcome": (
            "╭━━━ Network Media Downloader ━━━╮\n"
            "│ ⚡️ <b>Welcome to Ultra Downloader Bot</b>\n"
            "├─── 🌟 <b>Features:</b>\n"
            "│ 💎 High speed & Maximum Quality\n"
            "│ 🌀 Supports (YouTube, TikTok, Insta, ...)\n"
            "│ 🎧 High Quality MP3 Extraction\n"
            "╰━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚙️ <b>Select your preferred quality:</b>"
        ),
        "need_sub": (
            "⚠️ <b>Subscription Required!</b>\n\n"
            "🔰 Please subscribe to our channel first to unlock all features, then click the verify button below 👇"
        ),
        "sub_btn": "📢 Join Official Channel",
        "check_sub": "🔄 Verify Subscription Now",
        "checking": "🔍 <b>Analyzing link and bypassing limits...</b> ⏳",
        "downloading": "📥 <b>Downloading content...</b> 🚀",
        "uploading": "📤 <b>Uploading to Telegram...</b> ⚡️",
        "failed": "❌ <b>Download Failed!</b>\nEnsure the link is correct and public.",
        "verified": "🎉 <b>Account Verified!</b>\n\n🔗 Send any video link now to download.",
        "not_subbed": "🚫 You haven't joined the channel yet!",
        "quality_selected": "🎯 <b>Selected Quality:</b> <code>{}</code>\n\n📥 <b>Send video link now!</b>",
        "uploader": "Uploader",
        "duration": "Duration",
        "platform": "Platform",
        "size": "Size",
        "seconds": "sec",
        "visit_channel": "✨ Visit Our Official Channel",
        "choose_lang": "🌐 <b>Choose Interface Language:</b>",
        "lang_changed": "✅ <b>Language updated successfully!</b>",
        "best_q": "🔥 Maximum Auto Quality",
        "audio_only": "🎵 Audio Only (MP3 320kbps)"
    }
}

# ==========================================
# 4. إدارة قواعد البيانات واللغات
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
    return res[0] if res else "ar"

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
# 5. الأزرار ولوحات التحكم
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
        [
            InlineKeyboardButton(TEXT[lang]["best_q"], callback_data="best")
        ],
        [
            InlineKeyboardButton(TEXT[lang]["audio_only"], callback_data="mp3")
        ]
    ])

def language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
        ]
    ])

def channel_button_under_video(lang: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXT[lang]["visit_channel"], url=CHANNEL_URL)]
    ])

# ==========================================
# 6. إعدادات yt-dlp للتحميل الذكي
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
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        fmt = "bv*+ba/b"

    common_opts["format"] = fmt
    common_opts["merge_output_format"] = "mp4"
    return common_opts

# ==========================================
# 7. الأوامر البرمجية والردود
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
        "best": "🔥 Highest Quality",
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
# 8. معالجة التنزيل وتجاوز حظر يوتيوب عبر نظام السيرفرات المتعددة
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

    # قائمة النطاقات والبدائل للالتفاف على حظر يوتيوب بالتتابع
    urls_to_try = [text]
    if ("youtube.com" in text or "youtu.be" in text) and not os.path.exists("cookies.txt"):
        urls_to_try = [
            text.replace("youtube.com", "vid.puffyan.us").replace("youtu.be/", "vid.puffyan.us/watch?v="),
            text.replace("youtube.com", "invidious.nerdvpn.de").replace("youtu.be/", "invidious.nerdvpn.de/watch?v="),
            text.replace("youtube.com", "inv.tux.pizza").replace("youtu.be/", "inv.tux.pizza/watch?v="),
            text.replace("youtube.com", "yewtu.be").replace("youtu.be/", "yewtu.be/watch?v="),
            text  # التجربة المباشرة كخيار أخير
        ]

    await status.edit_text(TEXT[lang]["downloading"], parse_mode="HTML")
    loop = asyncio.get_running_loop()

    success = False
    last_error = None
    info, file_path = None, None

    for current_url in urls_to_try:
        def worker():
            opts = build_ydl_opts(output, quality)
            with yt_dlp.YoutubeDL(opts) as ydl:
                inf = ydl.extract_info(current_url, download=True)
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

        try:
            info, file_path = await loop.run_in_executor(None, worker)
            success = True
            break
        except Exception as e:
            last_error = e
            continue

    if not success:
        logging.exception(last_error)
        await status.edit_text(
            f"{TEXT[lang]['failed']}\n\n<code>{last_error}</code>",
            parse_mode="HTML",
        )
        return

    try:
        title = info.get("title", "Media File")
        uploader = info.get("uploader", "Unknown")
        duration = info.get("duration", 0)
        extractor = "YouTube" if any(domain in text for domain in ["youtube.com", "youtu.be"]) else info.get("extractor_key", "Media")
        size = os.path.getsize(file_path) / (1024 * 1024)

        caption = (
            f"🎬 <b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>{TEXT[lang]['uploader']}:</b> {uploader}\n"
            f"⏱ <b>{TEXT[lang]['duration']}:</b> {duration} {TEXT[lang]['seconds']}\n"
            f"🌐 <b>{TEXT[lang]['platform']}:</b> {extractor}\n"
            f"📦 <b>{TEXT[lang]['size']}:</b> {size:.2f} MB"
        )

        await status.edit_text(TEXT[lang]["uploading"], parse_mode="HTML")
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
# 9. لوحة تحكم المسؤول (Admin)
# ==========================================
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    CURSOR.execute("SELECT COUNT(*) FROM users")
    total = CURSOR.fetchone()[0]
    await update.message.reply_text(f"👥 <b>عدد أفراد البوت:</b> <code>{total}</code>", parse_mode="HTML")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    CURSOR.execute("SELECT COUNT(*) FROM users")
    total = CURSOR.fetchone()[0]
    text = (
        "📊 <b>إحصائيات الأداء الكلي</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>المستخدمون:</b> {total}\n"
        f"📥 <b>إجمالي عمليات التحميل:</b> {downloads_count}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    broadcast_mode[update.effective_user.id] = True
    await update.message.reply_text("📢 <b>أرسل نص الرسالة لإذاعتها لجميع المستخدمين:</b>", parse_mode="HTML")

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    broadcast_mode.pop(uid, None)

    text = update.message.text
    CURSOR.execute("SELECT id FROM users")
    users = CURSOR.fetchall()

    sent, failed = 0, 0
    msg = await update.message.reply_text("🚀 <b>جاري إرسال الإذاعة الجماعية...</b>", parse_mode="HTML")

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
# 10. نقطة التشغيل الرئيسية
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

    print("🚀 Bot deployed and listening 24/7...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
