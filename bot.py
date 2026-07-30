import os
import re
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# إعداد السجلات (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8629100412:AAFL7o3P67F2XlU7PqKeRjcrs3rqSBTYtnA"
CHANNEL_URL = "https://t.me/wanasatt"
BOT_URL = "https://t.me/Ussame_bot"

# قاموس اللغات (عربي / إنجليزي)
TEXTS = {
    'ar': {
        'welcome': "👋 أهلاً بك في بوت تحميل الفيديوهات السريع!\n\nأرسل لي رابط الفيديو من أي منصة (YouTube, TikTok, Instagram, Twitter...) وستتمكن من اختيارات الجودة وتنزيله فوراً.",
        'select_quality': "🎬 اختر الجودة المطلوبة للتحميل:",
        'downloading': "⏳ جاري تحميل الفيديو ودمج الملفات، يرجى الانتظار...",
        'uploading': "📤 جاري رفع الفيديو إلى تلجرام...",
        'error': "❌ حدث خطأ أثناء تنزيل الفيديو. تأكد من صحة الرابط أو جرب لاحقاً.",
        'channel_btn': "📢 القناة الرسمية",
        'bot_btn': "🤖 البوت الرئيسي",
        'lang_btn': "🌐 English",
        'audio_option': "🎵 صوت فقط (MP3)",
        'best_option': "✨ أفضل جودة متاحة",
    },
    'en': {
        'welcome': "👋 Welcome to the Fast Downloader Bot!\n\nSend me any video link from platforms like YouTube, TikTok, Instagram, Twitter, etc., and select your preferred quality.",
        'select_quality': "🎬 Choose your preferred video quality:",
        'downloading': "⏳ Downloading and processing video, please wait...",
        'uploading': "📤 Uploading to Telegram...",
        'error': "❌ An error occurred while processing the video. Please check the link and try again.",
        'channel_btn': "📢 Main Channel",
        'bot_btn': "🤖 Main Bot",
        'lang_btn': "🌐 العربية",
        'audio_option': "🎵 Audio Only (MP3)",
        'best_option': "✨ Best Quality",
    }
}

# لوحة الأزرار التفاعلية الرئيسية
def get_main_keyboard(lang: str = 'ar') -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(TEXTS[lang]['channel_btn'], url=CHANNEL_URL),
            InlineKeyboardButton(TEXTS[lang]['bot_btn'], url=BOT_URL)
        ],
        [
            InlineKeyboardButton(TEXTS[lang]['lang_btn'], callback_data=f"toggle_lang_{'en' if lang == 'ar' else 'ar'}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# لوحة اختيار الجودات
def get_quality_keyboard(video_url: str, lang: str = 'ar') -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]['best_option'], callback_data=f"dl|best|{video_url}")],
        [
            InlineKeyboardButton("1080p", callback_data=f"dl|1080|{video_url}"),
            InlineKeyboardButton("720p", callback_data=f"dl|720|{video_url}"),
            InlineKeyboardButton("480p", callback_data=f"dl|480|{video_url}")
        ],
        [InlineKeyboardButton(TEXTS[lang]['audio_option'], callback_data=f"dl|audio|{video_url}")],
    ]
    return InlineKeyboardMarkup(keyboard)

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(
        TEXTS[user_lang]['welcome'],
        reply_markup=get_main_keyboard(user_lang)
    )

# استقبال الروابط
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_lang = context.user_data.get('lang', 'ar')

    # التحقق البسيط من صحة الرابط
    if not re.match(r'https?://[^\s]+', url):
        return

    await update.message.reply_text(
        TEXTS[user_lang]['select_quality'],
        reply_markup=get_quality_keyboard(url, user_lang)
    )

# معالجة الضغط على الأزرار (تغيير اللغة أو بدء التنزيل)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_lang = context.user_data.get('lang', 'ar')

    # تبديل اللغة
    if data.startswith("toggle_lang_"):
        new_lang = data.split("_")[2]
        context.user_data['lang'] = new_lang
        await query.edit_message_text(
            TEXTS[new_lang]['welcome'],
            reply_markup=get_main_keyboard(new_lang)
        )
        return

    # معالجة طلب التنزيل
    if data.startswith("dl|"):
        _, quality, video_url = data.split("|", 2)
        
        status_msg = await query.message.reply_text(TEXTS[user_lang]['downloading'])
        
        # إعدادات yt-dlp لتخطي قيود يوتيوب وسرعة التحميل
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            # تخطي قيود الحظر والعمر بالعملاء المدمجين (Android/iOS)
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        # تحديد صياغة الجودة المطلوب تحميلها
        if quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality == 'best':
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        else:
            ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best'

        # تنزيل الملف في خيط منفصل لتفادي تجميد البوت
        loop = asyncio.get_event_loop()
        try:
            filename = await loop.run_in_executor(None, lambda: download_video(video_url, ydl_opts))
            
            await status_msg.edit_text(TEXTS[user_lang]['uploading'])

            # إرسال الملف للمستخدم
            with open(filename, 'rb') as file:
                if quality == 'audio' or filename.endswith('.mp3'):
                    await query.message.reply_audio(audio=file, caption="Downloaded by @Ussame_bot")
                else:
                    await query.message.reply_video(video=file, caption="Downloaded by @Ussame_bot")

            await status_msg.delete()

            # مسح الملف من السيرفر بعد الإرسال لتوفير المساحة
            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            logging.error(f"Error downloading: {e}")
            await status_msg.edit_text(TEXTS[user_lang]['error'])

def download_video(url, opts):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("⚡ Bot is running successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
