import os
import logging
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# الإعدادات الرئيسية
TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAFn_wgwwO_ZN_ifYyGqdADlvU-IZDUkgZY")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@wanasatt") # قناة الاشتراك الإجباري
ADMIN_ID = int(os.getenv("ADMIN_ID", "8904859256")) # معرف حسابك كمالك للبوت

# ----------------- إعداد قاعدة البيانات -----------------
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    for key in ['total_downloads', 'dl_1080', 'dl_720', 'dl_480', 'dl_mp3']:
        cursor.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0)", (key,))
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def increment_stat(stat_key: str):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE stats SET value = value + 1 WHERE key = ?", (stat_key,))
    cursor.execute("UPDATE stats SET value = value + 1 WHERE key = 'total_downloads'")
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT key, value FROM stats")
    stats_data = dict(cursor.fetchall())
    conn.close()
    return total_users, stats_data

init_db()

user_links = {}

# التحقق من الاشتراك الإجباري
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
    return False

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة الرسمية", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        caption = (
            "🔒 **عذراً عزيزي المستخدم!**\n\n"
            "ميزة التحميل المجاني مخصصة للمشتركين في قناتنا الرسمية لمتابعة كل جديد.\n\n"
            "👇 **اشترك الآن ثم اضغط على زر التحقق بالأسفل للاستخدام:**"
        )
        await update.message.reply_text(caption, reply_markup=reply_markup, parse_mode="Markdown")
        return

    await update.message.reply_text(
        "🚀 **مرحباً بك في بوت التحميل الاحترافي!**\n\n"
        "أرسل لي رابط المقطع (من فيسبوك، يوتيوب، إنستغرام، إلخ) وسأعطيك خيارات التحميل! ⚡",
        parse_mode="Markdown"
    )

# أمر الإحصائيات (خاص بالمالك فقط)
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص لمالك البوت فقط.")
        return

    total_users, stats_data = get_stats()
    
    msg = (
        "📊 **إحصائيات البوت الشاملة:**\n\n"
        f"👤 **عدد المستخدمين الكلي:** `{total_users}` مستخدم\n"
        f"📥 **إجمالي التحميلات الناجحة:** `{stats_data.get('total_downloads', 0)}` عملية\n\n"
        "🎬 **تفاصيل التحميل حسب الجودة:**\n"
        f"• 🔥 1080p: `{stats_data.get('dl_1080', 0)}` فيديو\n"
        f"• 🌟 720p: `{stats_data.get('dl_720', 0)}` فيديو\n"
        f"• ⚡ 480p: `{stats_data.get('dl_480', 0)}` فيديو\n"
        f"• 🎧 MP3: `{stats_data.get('dl_mp3', 0)}` مقطع صوتي"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# التعامل مع الأزرار التفاعلية
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "check_sub":
        is_subscribed = await check_subscription(user_id, context)
        if is_subscribed:
            await query.message.edit_text(
                "✅ **تم التحقق بنجاح!**\n\n"
                "أهلاً بك، يمكنك الآن إرسال أي رابط وسأقوم بتحميله لك فوراً. 🚀",
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ لم تقم بالاشتراك في القناة بعد! يرجى الاشتراك أولاً.", show_alert=True)
            
    elif data.startswith("dl_"):
        if user_id not in user_links:
            await query.message.edit_text("⚠️ انتهت صلاحية الرابط أو حدث خطأ. أرسل الرابط من جديد.")
            return
            
        url = user_links[user_id]
        quality = data.split("_")[1]
        
        await query.message.edit_text("⏳ **جاري بدء التحميل والمعالجة، قد يستغرق ذلك بضع ثوانٍ...**", parse_mode="Markdown")
        
        success = await download_and_send(update, context, url, quality)
        if success:
            increment_stat(f"dl_{quality}")

# استقبال الروابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        await start(update, context)
        return

    text = update.message.text
    if not text or not (text.startswith("http://") or text.startswith("https://")):
        await update.message.reply_text("❌ يرجى إرسال رابط صالح فقط (يوتيوب، فيسبوك، انستغرام...).")
        return

    user_links[user_id] = text

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو | 1080p 🔥", callback_data="dl_1080")],
        [InlineKeyboardButton("✨ فيديو | 720p 🌟", callback_data="dl_720")],
        [InlineKeyboardButton("⚡ فيديو | 480p ⚡", callback_data="dl_480")],
        [InlineKeyboardButton("🎵 صوت فقط | MP3 🎧", callback_data="dl_mp3")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎬 **اختر الجودة أو الصيغة المطلوبة للتحميل:**\n\n👇 اضغط على أحد الخيارات أدناه لبدء التنزيل فورًا:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# دالة التحميل الفعلي
async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str, quality: str) -> bool:
    chat_id = update.effective_chat.id
    output_template = f"downloads/{chat_id}_%(id)s.%(ext)s"
    os.makedirs("downloads", exist_ok=True)
    
    ydl_opts = {
        'outtmpl': output_template,
        'noplaylist': True,
        'geo_bypass': True,
    }
    
    if quality == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif quality == "1080":
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
    elif quality == "720":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
    else:
        ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'

    file_path = None
    try:
        def run_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if quality == "mp3":
                    filename = os.path.splitext(filename)[0] + ".mp3"
                return filename

        file_path = await asyncio.to_thread(run_download)

        if not file_path or not os.path.exists(file_path):
            await context.bot.send_message(chat_id=chat_id, text="❌ عذراً، فشل تحميل الملف.")
            return False

        with open(file_path, 'rb') as f:
            if quality == "mp3":
                await context.bot.send_audio(chat_id=chat_id, audio=f, caption="✨ تم التحميل بنجاح بواسطة البوت 🚀")
            else:
                await context.bot.send_video(chat_id=chat_id, video=f, caption="✨ تم التحميل بنجاح بواسطة البوت 🚀")
        return True

    except Exception as e:
        logging.error(f"Download error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ حدث خطأ أثناء التحميل، تأكد من صحة الرابط.")
        return False
    
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
