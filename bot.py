import os
import sys
import time
import logging
import asyncio
import sqlite3
import subprocess
from pathlib import Path

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

# ==========================
# 1. التحديث التلقائي للمكتبة
# ==========================
try:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
except Exception as e:
    print(f"Warning: Failed to auto-update yt-dlp: {e}")

# ==========================
# 2. الإعدادات والروابط
# ==========================
BOT_TOKEN = "8629100412:AAGm4yGHRUpRqAzdReY4ZbLw3ESQVtmk26g"
CHANNEL_USERNAME = "@wanasatt"
CHANNEL_URL = "https://t.me/wanasatt"
BOT_URL = "https://t.me/Ussame_bot"
ADMIN_ID = 123456789  # ضع معرفك هنا للوحة التحكم

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# قواعد البيانات
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
progress_cache = {}
broadcast_mode = {}
downloads_count = 0

# ==========================
# 3. النصوص متعددة اللغات (Multi-Language)
# ==========================
TEXT = {
    "ar": {
        "welcome": "👋 أهلاً بك في بوت التحميل الاحترافي.\n\nأرسل رابط فيديو وسأقوم بتحميله.",
        "need_sub": "⚠️ يجب الاشتراك في القناة أولاً لاستخدام البوت.",
        "sub_btn": "📢 الاشتراك في القناة",
        "check_sub": "✅ تحقق من الاشتراك",
        "checking": "🔍 جاري فحص الرابط...",
        "downloading": "📥 جاري تحميل الفيديو...",
        "uploading": "📤 جاري إرسال الفيديو...",
        "failed": "❌ تعذر تحميل الفيديو.",
        "verified": "✅ تم التحقق بنجاح.\n\nأرسل رابط الفيديو الآن.",
        "not_subbed": "❌ لم تشترك بعد في القناة.",
        "quality_selected": "✅ تم اختيار الجودة: <b>{}</b>\n\nأرسل رابط الفيديو الآن.",
        "title": "العنوان",
        "uploader": "الناشر",
        "duration": "المدة",
        "platform": "المنصة",
        "size": "الحجم",
        "seconds": "ثانية",
        "visit_channel": "📢 انضم لقناتنا على تلغرام",
        "choose_lang": "🌐 اختر لغتك المفضلة / Choose your language / Choisissez votre langue:",
        "lang_changed": "✅ تم تغيير اللغة إلى العربية بنجاح.",
        "best_q": "🏆 أفضل جودة",
        "audio_only": "🎵 MP3 صوت فقط"
    },
    "en": {
        "welcome": "👋 Welcome to the Professional Downloader Bot.\n\nSend me a video link to download.",
        "need_sub": "⚠️ You must subscribe to our channel first to use this bot.",
        "sub_btn": "📢 Subscribe to Channel",
        "check_sub": "✅ Verify Subscription",
        "checking": "🔍 Checking link...",
        "downloading": "📥 Downloading video...",
        "uploading": "📤 Uploading video...",
        "failed": "❌ Failed to download video.",
        "verified": "✅ Successfully verified.\n\nSend a video link now.",
        "not_subbed": "❌ You are not subscribed yet.",
        "quality_selected": "✅ Quality selected: <b>{}</b>\n\nSend a video link now.",
        "title": "Title",
        "uploader": "Uploader",
        "duration": "Duration",
        "platform": "Platform",
        "size": "Size",
        "seconds": "seconds",
        "visit_channel": "📢 Join Our Telegram Channel",
        "choose_lang": "🌐 Choose your language / اختر لغتك المفضلة:",
        "lang_changed": "✅ Language successfully set to English.",
        "best_q": "🏆 Best Quality",
        "audio_only": "🎵 MP3 Audio Only"
    },
    "fr": {
        "welcome": "👋 Bienvenue sur le bot de téléchargement professionnel.\n\nEnvoyez un lien vidéo à télécharger.",
        "need_sub": "⚠️ Vous devez d'abord vous abonner à notre chaîne pour utiliser ce bot.",
        "sub_btn": "📢 S'abonner à la chaîne",
        "check_sub": "✅ Vérifier l'abonnement",
        "checking": "🔍 Vérification du lien...",
        "downloading": "📥 Téléchargement de la vidéo...",
        "uploading": "📤 Envoi de la vidéo...",
        "failed": "❌ Échec du téléchargement de la vidéo.",
        "verified": "✅ Vérifié avec succès.\n\nEnvoyez un lien vidéo maintenant.",
        "not_subbed": "❌ Vous n'êtes pas encore abonné.",
        "quality_selected": "✅ Qualité sélectionnée: <b>{}</b>\n\nEnvoyez un lien vidéo maintenant.",
        "title": "Titre",
        "uploader": "Publié par",
        "duration": "Durée",
        "platform": "Plateforme",
        "size": "Taille",
        "seconds": "secondes",
        "visit_channel": "📢 Rejoignez notre canal Telegram",
        "choose_lang": "🌐 Choisissez votre langue / Choose your language:",
        "lang_changed": "✅ Langue changée en Français avec succès.",
        "best_q": "🏆 Meilleure Qualité",
        "audio_only": "🎵 MP3 Audio Uniquement"
    }
}

# ==========================
# 4. إدارة المستخدم واللغات
# ==========================
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

# ==========================
# 5. الاشتراك والإزرار الشفافة
# ==========================
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
            InlineKeyboardButton("360P", callback_data="360"),
            InlineKeyboardButton("720P", callback_data="720"),
        ],
        [
            InlineKeyboardButton("1080P", callback_data="1080"),
            InlineKeyboardButton(TEXT[lang]["best_q"], callback_data="best"),
        ],
        [
            InlineKeyboardButton(TEXT[lang]["audio_only"], callback_data="mp3"),
        ]
    ])

def language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="set_lang_fr"),
        ]
    ])

def channel_button_under_video(lang: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXT[lang]["visit_channel"], url=CHANNEL_URL)]
    ])

# ==========================
# 6. إعدادات yt-dlp
# ==========================
def progress_hook(d):
    if d.get("status") == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if total:
            percent = int(downloaded * 100 / total)
            progress_cache["percent"] = percent

def build_ydl_opts(output: str, quality: str):
    if quality == "360":
        fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]"
    elif quality == "720":
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif quality == "1080":
        fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif quality == "mp3":
        return {
            "format": "bestaudio/best",
            "outtmpl": output,
            "quiet": True,
            "extract_audio": True,
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]
        }
    else:
        fmt = "bv*+ba/b"

    opts = {
        "format": fmt,
        "merge_output_format": "mp4",
        "outtmpl": output,
        "quiet": True,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "progress_hooks": [progress_hook],
        "http_headers": {"User-Agent": "Mozilla/5.0"}
    }

    if os.path.exists("cookies.txt"):
        opts["cookiefile"] = "cookies.txt"

    return opts

# ==========================
# 7. الأوامر والمعالجة
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_lang_code = user.language_code[:2] if user.language_code else "ar"
    register_user(user.id, user_lang_code)
    lang = get_user_lang(user.id)

    if not await is_subscribed(context, user.id):
        await update.message.reply_text(TEXT[lang]["need_sub"], reply_markup=force_keyboard(lang))
        return

    await update.message.reply_text(
        TEXT[lang]["welcome"],
        reply_markup=quality_keyboard(lang)
    )

async def set_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    await update.message.reply_text(
        TEXT[lang]["choose_lang"],
        reply_markup=language_keyboard()
    )

async def check_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_user_lang(query.from_user.id)

    if await is_subscribed(context, query.from_user.id):
        await query.edit_message_text(TEXT[lang]["verified"])
    else:
        await query.answer(TEXT[lang]["not_subbed"], show_alert=True)

async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    lang = get_user_lang(query.from_user.id)
    user_quality[query.from_user.id] = choice
    
    msg_text = TEXT[lang]["quality_selected"].format(choice)
    await query.edit_message_text(msg_text, parse_mode="HTML")

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected_lang = query.data.replace("set_lang_", "")
    
    set_user_lang(query.from_user.id, selected_lang)
    await query.edit_message_text(TEXT[selected_lang]["lang_changed"])

# ==========================
# 8. التحميل والرفع مع الأزرار الشفافة
# ==========================
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
        await update.message.reply_text(TEXT[lang]["need_sub"], reply_markup=force_keyboard(lang))
        return

    text = update.message.text.strip()
    if not text.startswith(("http://", "https://")):
        return

    status = await update.message.reply_text(TEXT[lang]["checking"])
    quality = user_quality.get(user.id, "best")
    output = str(DOWNLOAD_DIR / f"{user.id}_{int(time.time())}_%(title)s.%(ext)s")

    try:
        await status.edit_text(TEXT[lang]["downloading"])
        loop = asyncio.get_running_loop()

        def worker():
            opts = build_ydl_opts(output, quality)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(text, download=True)
                file_path = ydl.prepare_filename(info)
                
                if quality == "mp3":
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

                if not os.path.exists(file_path):
                    base = os.path.splitext(file_path)[0]
                    for ext in (".mp4", ".mkv", ".webm", ".mov", ".mp3"):
                        if os.path.exists(base + ext):
                            file_path = base + ext
                            break
                return info, file_path

        info, file_path = await loop.run_in_executor(None, worker)

        title = info.get("title", "Unknown")
        uploader = info.get("uploader", "Unknown")
        duration = info.get("duration", 0)
        extractor = info.get("extractor_key", "Media")
        size = os.path.getsize(file_path) / (1024 * 1024)

        # تجهيز الوصف بلغة المستخدم
        caption = (
            f"✅ <b>{title}</b>\n\n"
            f"👤 <b>{TEXT[lang]['uploader']}:</b> {uploader}\n"
            f"⏱ <b>{TEXT[lang]['duration']}:</b> {duration} {TEXT[lang]['seconds']}\n"
            f"🌐 <b>{TEXT[lang]['platform']}:</b> {extractor}\n"
            f"📦 <b>{TEXT[lang]['size']}:</b> {size:.2f} MB"
        )

        await status.edit_text(TEXT[lang]["uploading"])

        # إرسال الفيديو/الصوت مع زر شفاف أسفل المقطع للقناة
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

# ==========================
# 9. لوحة الإدارة والإذاعة
# ==========================
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    CURSOR.execute("SELECT COUNT(*) FROM users")
    total = CURSOR.fetchone()[0]
    await update.message.reply_text(f"👥 <b>إجمالي المستخدمين:</b> {total}", parse_mode="HTML")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    CURSOR.execute("SELECT COUNT(*) FROM users")
    total = CURSOR.fetchone()[0]
    text = (
        "📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 <b>المستخدمون:</b> {total}\n"
        f"📥 <b>التحميلات الناجحة:</b> {downloads_count}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    broadcast_mode[update.effective_user.id] = True
    await update.message.reply_text("✉️ أرسل الرسالة التي تريد إذاعتها الآن لجميع المستخدمين.")

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    broadcast_mode.pop(uid, None)

    text = update.message.text
    CURSOR.execute("SELECT id FROM users")
    users = CURSOR.fetchall()

    sent, failed = 0, 0
    msg = await update.message.reply_text("🚀 جاري بدء الإذاعة...")

    for user in users:
        try:
            await context.bot.send_message(user[0], text)
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1

    await msg.edit_text(f"✅ <b>اكتملت الإذاعة</b>\n\n🎯 نجح: {sent}\n❌ فشل: {failed}", parse_mode="HTML")

# ==========================
# 10. التشغيل الرئيسي
# ==========================
def main():
    clean_downloads()

    app = Application.builder().token(BOT_TOKEN).build()

    # الأوامر العامة
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", set_language_command))

    # أوامر الإدارة
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    # الكولباك (Callback Queries)
    app.add_handler(CallbackQueryHandler(check_button, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(quality_callback, pattern="^(360|720|1080|best|mp3)$"))
    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^set_lang_"))

    # معالج التحميل والرسائل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media_download))

    print("🤖 Bot Started Successfully with Multi-Language Support & Inline Keyboard...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
