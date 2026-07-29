import os
import sys
import logging
import asyncio
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import yt_dlp

# تحديث تلقائي لـ yt-dlp عند تشغيل البوت لضمان دعم كافة المنصات
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
except Exception as e:
    print(f"Failed to update yt-dlp: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# التوكن الجديد الخاص بالبوت
TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAE507iUBx8p5x05xgXxcToSX4n_r_TGa0w")
CHANNEL_URL = "https://t.me/wanasatt"

# قاموس مؤقت لتخزين روابط المستخدمين بين الخطوات
user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "<b>مرحباً بك في بوت التحميل الاحترافي 🚀</b>\n\n"
        "أرسل لي <b>رابط المقطع</b> وسأعطيك خيارات تحميل الجودة أو الصوت بكل سهولة! ⚡️"
    )
    keyboard = [
        [
            InlineKeyboardButton("📢 القناة الرسمية", url=CHANNEL_URL),
            InlineKeyboardButton("💬 الدعم الفني", url="https://t.me/Ussame_bot")
        ]
    ]
    await update.message.reply_text(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

# 1. عند استلام الرابط: تحليل الفيديو وإظهار أزرار الدقة
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        return

    status_msg = await update.message.reply_text("🔎 <i>جاري تحليل الرابط وجلب الجودات المتاحة...</i>", parse_mode="HTML")

    # حفظ الرابط الخاص بالمستخدم
    user_id = update.effective_user.id
    user_links[user_id] = url

    # لوحة الأزرار المودرن للاختيار
    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو | 1080p 🔥", callback_data="dl_1080"),
            InlineKeyboardButton("🎬 فيديو | 720p ✨", callback_data="dl_720")
        ],
        [
            InlineKeyboardButton("🎬 فيديو | 480p ⚡️", callback_data="dl_480"),
            InlineKeyboardButton("🎵 صوت فقط | MP3 🎧", callback_data="dl_mp3")
        ],
        [
            InlineKeyboardButton("📢 قناتنا على تلجرام 🚀", url=CHANNEL_URL)
        ]
    ]

    await status_msg.edit_text(
        "<b>🎬 اختر الجودة أو الصيغة المطلوبة للتحميل:</b>\n\n"
        "👇 اضغط على أحد الخيارات أدناه لبدء التنزيل فوراً:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 2. عند النقر على أحد الأزرار: تنفيذ التنزيل حسب الخيار
async def process_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_links.get(user_id)

    if not url:
        await query.edit_message_text("❌ <b>انتهت جلسة التحميل!</b> يرجى إرسال الرابط من جديد.", parse_mode="HTML")
        return

    choice = query.data
    output_template = f"downloads/{user_id}_%(id)s.%(ext)s"

    # تحديد خيارات yt-dlp بناءً على زر المستخدم
    if choice == "dl_mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        is_audio = True
    else:
        res_map = {
            "dl_1080": "1080",
            "dl_720": "720",
            "dl_480": "480"
        }
        target_res = res_map.get(choice, "720")
        
        ydl_opts = {
            'format': f'bestvideo[height<={target_res}][ext=mp4]+bestaudio[ext=m4a]/best[height<={target_res}][ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        is_audio = False

    await query.edit_message_text("⚡️ <i>جاري التحميل بالصيغة والجودة المختارة...</i>", parse_mode="HTML")

    loop = asyncio.get_event_loop()

    try:
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if is_audio:
                    filename = os.path.splitext(filename)[0] + ".mp3"
                return info, filename

        info, file_path = await loop.run_in_executor(None, run_dl)

        await query.edit_message_text("📤 <i>جاري إرسال الملف إليك...</i>", parse_mode="HTML")

        title = info.get('title', 'مقطع ميديا')
        caption = (
            f"📌 <b>{title}</b>\n\n"
            f"✨ <i>تم التحميل عبر: @Ussame_bot</i>"
        )
        
        channel_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في قناتنا الرسمية 🚀", url=CHANNEL_URL)]
        ])

        if is_audio:
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=audio_file,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=channel_btn
                )
        else:
            with open(file_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=channel_btn
                )

        if os.path.exists(file_path):
            os.remove(file_path)

        await query.delete_message()

    except Exception as e:
        logger.error(f"Error processing link: {e}")
        await query.edit_message_text(
            "❌ <b>حدث خطأ أثناء التنزيل!</b>\nقد تكون الجودة المختارة غير متوفرة لهذا المقطع أو أن الرابط محمي.",
            parse_mode="HTML"
        )

def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(process_choice))

    print("Bot is running with new token...")
    app.run_polling()

if __name__ == "__main__":
    main()
