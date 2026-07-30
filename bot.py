
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.INFO)

# 🔑 التوكن الجديد الخاص بك
TOKEN = "8629100412:AAE3o7PxOhixD91H3yRQtg2MslbCp8k-Mzo"
CHANNEL_URL = "https://t.me/wanasatt"
CHANNEL_USERNAME = "@wanasatt"

# متغير عام لتخزين معرف البوت التلقائي
BOT_USERNAME = ""

# --- 🌐 خادم ويب وهمي لإبقاء Render حياً عبر UptimeRobot ---
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Bot is active and running 24/7!")

    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), PingHandler)
    server.serve_forever()

# --- القاموس متعدد اللغات بالتصميم الأنيق ---
TEXTS = {
    'ar': {
        'welcome': (
            "🎬 **مرحباً بك في VideoHub Downloader**\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚡ أسرع بوت لتحميل الفيديوهات\n"
            "🎞️ جودة عالية\n"
            "🎵 تحويل إلى MP3\n"
            "🌍 يدعم معظم المنصات\n"
            "🟢 يعمل 24/7\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📎 **أرسل رابط الفيديو وسأتولى الباقي.**"
        ),
        'sub_required': (
            "🔒 **الاشتراك الإجباري**\n\n"
            "قبل استخدام البوت، يجب الاشتراك في القناة.\n"
            "اشترك ثم اضغط زر التحقق."
        ),
        'sub_btn': "📢 اشترك في القناة",
        'check_btn': "🫆 التحقق",
        'channel_btn': "📢 قناتنا الرسمية",
        'invalid_url': "🤔 **هذا لا يبدو كرابط صحيح!** أرسل رابطاً يبدأ بـ `http` أو `https`.",
        'analyzing': (
            "⏳ **جارِ تحليل الرابط...**\n\n"
            "🔍 التعرف على المنصة...\n"
            "📥 تجهيز الملف...\n"
            "🚀 بدء التحميل..."
        ),
        'error_fetch': "💥 **عذراً! تعذر تحليل الرابط.** تأكد من أن المقطع عام وليس خاصاً.",
        'mp3_btn': "🎵 تحويل إلى MP3",
        'card_title': (
            "📌 **تفاصيل الفيديو:**\n\n"
            "🎬 **اسم الفيديو:**\n`{title}`\n\n"
            "👤 **الناشر:** {uploader}\n"
            "⏱️ **المدة:** {duration}\n\n"
            "👇 **اختر الجودة أو الصيغة المطلوبة:**"
        ),
        'downloading_vid': "⚙️ **جارِ تحميل وتجهيز الفيديو...** ⏳",
        'downloading_aud': "🎶 **جارِ تحويل الفيديو إلى MP3...** ⏳",
        'uploading': "🚀 **جارِ رفع الملف إلى تليجرام...** 📡",
        'success_vid': (
            "✅ **تم التحميل بنجاح.**\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎬 **اسم الفيديو:**\n{title}\n\n"
            "👤 **الناشر:** {uploader}\n"
            "🌍 **المنصة:** {extractor}\n"
            "⏱️ **المدة:** {duration}\n"
            "🎞️ **الجودة:** {quality}\n\n"
            "🤖 **تم التحميل بواسطة**\n{bot_link}\n\n"
            "شكراً لاستخدامك البوت ❤️\n"
            "━━━━━━━━━━━━━━━━━━"
        ),
        'err_dl': "❌ **تعذر التحميل!** قد يكون الحجم كبيراً جداً (أكثر من 50 ميجابايت).",
        'session_exp': "⌛ **انتهت صلاحية الجلسة!** يرجى إعادة إرسال الرابط.",
        'verified': "🎉 **تم التحقق بنجاح!** أرسل أي رابط الآن للبدء. 🚀",
        'not_verified': "❌ لم تشترك في القناة بعد! اشترك ثم اضغط زر التحقق."
    },
    'en': {
        'welcome': (
            "🎬 **Welcome to VideoHub Downloader**\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚡ Fastest Video Downloader\n"
            "🎞️ High Quality\n"
            "🎵 Convert to MP3\n"
            "🌍 Supports Most Platforms\n"
            "🟢 Online 24/7\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📎 **Send the video link and I'll do the rest.**"
        ),
        'sub_required': (
            "🔒 **Subscription Required**\n\n"
            "Please join our channel before using the bot.\n"
            "Subscribe then click Verify."
        ),
        'sub_btn': "📢 Subscribe to Channel",
        'check_btn': "🫆 Verify",
        'channel_btn': "📢 Official Channel",
        'invalid_url': "🤔 **Invalid link!** Send a link starting with `http` or `https`.",
        'analyzing': (
            "⏳ **Analyzing link...**\n\n"
            "🔍 Identifying platform...\n"
            "📥 Preparing file...\n"
            "🚀 Starting download..."
        ),
        'error_fetch': "💥 **Failed to analyze link.** Make sure the video is public.",
        'mp3_btn': "🎵 Convert to MP3",
        'card_title': (
            "📌 **Video Details:**\n\n"
            "🎬 **Title:**\n`{title}`\n\n"
            "👤 **Uploader:** {uploader}\n"
            "⏱️ **Duration:** {duration}\n\n"
            "👇 **Choose quality or format:**"
        ),
        'downloading_vid': "⚙️ **Downloading video...** ⏳",
        'downloading_aud': "🎶 **Converting to MP3...** ⏳",
        'uploading': "🚀 **Uploading to Telegram...** 📡",
        'success_vid': (
            "✅ **Downloaded Successfully.**\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎬 **Title:**\n{title}\n\n"
            "👤 **Uploader:** {uploader}\n"
            "🌍 **Platform:** {extractor}\n"
            "⏱️ **Duration:** {duration}\n"
            "🎞️ **Quality:** {quality}\n\n"
            "🤖 **Downloaded by**\n{bot_link}\n\n"
            "Thanks for using our bot ❤️\n"
            "━━━━━━━━━━━━━━━━━━"
        ),
        'err_dl': "❌ **Download failed!** File size may exceed 50MB.",
        'session_exp': "⌛ **Session expired!** Send the link again.",
        'verified': "🎉 **Verified successfully!** Send a link to start. 🚀",
        'not_verified': "❌ You haven't subscribed yet! Please join the channel first."
    }
}

def get_lang(user_lang_code: str) -> dict:
    if not user_lang_code:
        return TEXTS['ar']
    lang = user_lang_code.lower()[:2]
    return TEXTS.get(lang, TEXTS['ar'])

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Subscription Check Error: {e}")
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.language_code)
    
    if not await check_subscription(user.id, context):
        keyboard = [
            [InlineKeyboardButton(lang['sub_btn'], url=CHANNEL_URL)],
            [InlineKeyboardButton(lang['check_btn'], callback_data="check_sub")]
        ]
        await update.message.reply_text(lang['sub_required'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    keyboard = [
        [InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)]
    ]
    await update.message.reply_text(lang['welcome'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.language_code)
    
    if not await check_subscription(user.id, context):
        keyboard = [
            [InlineKeyboardButton(lang['sub_btn'], url=CHANNEL_URL)],
            [InlineKeyboardButton(lang['check_btn'], callback_data="check_sub")]
        ]
        await update.message.reply_text(lang['sub_required'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    url = update.message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text(lang['invalid_url'], parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text(lang['analyzing'], parse_mode="Markdown")

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, lambda: fetch_video_info(url))
    except Exception as e:
        await status_msg.edit_text(lang['error_fetch'], parse_mode="Markdown")
        return

    video_id = info.get('id', 'vid')
    title = info.get('title', 'فيديو بدون عنوان')
    duration = info.get('duration_string', 'غير معروف')
    uploader = info.get('uploader', 'غير معروف')
    extractor = info.get('extractor_key', 'المنصة العامة')

    context.user_data[video_id] = {
        'url': url, 
        'title': title,
        'uploader': uploader,
        'duration': duration,
        'extractor': extractor
    }

    keyboard = []
    keyboard.append([InlineKeyboardButton(lang['mp3_btn'], callback_data=f"dl_audio|{video_id}")])
    
    formats = info.get('formats', [])
    seen_qualities = set()
    quality_buttons = []
    
    for f in formats:
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
            height = f.get('height')
            format_id = f.get('format_id')
            if height and height not in seen_qualities:
                seen_qualities.add(height)
                badge = "✨ High" if height >= 720 else "📱 SD"
                quality_buttons.append(InlineKeyboardButton(f"🎞️ {height}p ({badge})", callback_data=f"dl_vid|{video_id}|{format_id}|{height}p"))
                if len(quality_buttons) == 2:
                    keyboard.append(quality_buttons)
                    quality_buttons = []
                if len(seen_qualities) >= 4:
                    break
                    
    if quality_buttons:
        keyboard.append(quality_buttons)

    if not seen_qualities:
        keyboard.append([InlineKeyboardButton("🎞️ أعلى جودة متاحة", callback_data=f"dl_vid|{video_id}|best|HD")])

    keyboard.append([InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)])

    card_text = lang['card_title'].format(
        title=title[:60] + "...",
        uploader=uploader,
        duration=duration
    )
    await status_msg.edit_text(card_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def fetch_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    lang = get_lang(user.language_code)
    data = query.data.split("|")
    action = data[0]

    if action == "check_sub":
        await query.answer()
        if await check_subscription(user.id, context):
            await query.edit_message_text(lang['verified'], parse_mode="Markdown")
        else:
            await query.answer(lang['not_verified'], show_alert=True)
        return

    if not await check_subscription(user.id, context):
        await query.answer(lang['not_verified'], show_alert=True)
        return

    video_id = data[1]
    video_data = context.user_data.get(video_id)
    if not video_data:
        await query.edit_message_text(lang['session_exp'], parse_mode="Markdown")
        return

    url = video_data['url']
    loop = asyncio.get_running_loop()

    bot_link = f"@{BOT_USERNAME}" if BOT_USERNAME else "@Bot"

    # 🎬 تحميل فيديو
    if action == "dl_vid":
        await query.answer()
        format_id = data[2]
        quality = data[3] if len(data) > 3 else "HD"
        await query.edit_message_text(lang['downloading_vid'], parse_mode="Markdown")
        
        filename = f"{video_id}.mp4"
        try:
            await loop.run_in_executor(None, lambda: download_media(url, format_id, filename, is_audio=False))
            await query.edit_message_text(lang['uploading'], parse_mode="Markdown")
            
            caption_text = lang['success_vid'].format(
                title=video_data['title'],
                uploader=video_data['uploader'],
                extractor=video_data['extractor'],
                duration=video_data['duration'],
                quality=quality,
                bot_link=bot_link
            )
            
            with open(filename, 'rb') as f:
                await query.message.reply_video(
                    video=f,
                    caption=caption_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)]]),
                    parse_mode="Markdown"
                )
            await query.delete_message()
        except Exception as e:
            logging.error(f"Vid Error: {e}")
            await query.message.reply_text(lang['err_dl'])
        finally:
            if os.path.exists(filename): os.remove(filename)

    # 🎵 تحميل صوت MP3
    elif action == "dl_audio":
        await query.answer()
        await query.edit_message_text(lang['downloading_aud'], parse_mode="Markdown")
        
        filename = f"{video_id}.mp3"
        try:
            await loop.run_in_executor(None, lambda: download_media(url, 'bestaudio/best', filename, is_audio=True))
            await query.edit_message_text(lang['uploading'], parse_mode="Markdown")
            
            caption_text = lang['success_vid'].format(
                title=video_data['title'],
                uploader=video_data['uploader'],
                extractor=video_data['extractor'],
                duration=video_data['duration'],
                quality="MP3 (Audio)",
                bot_link=bot_link
            )
            
            with open(filename, 'rb') as f:
                await query.message.reply_audio(
                    audio=f,
                    title=video_data['title'],
                    caption=caption_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)]]),
                    parse_mode="Markdown"
                )
            await query.delete_message()
        except Exception as e:
            logging.error(f"Audio Error: {e}")
            await query.message.reply_text(lang['err_dl'])
        finally:
            if os.path.exists(filename): os.remove(filename)

def download_media(url, format_id, output_filename, is_audio=False):
    ydl_opts = {
        'outtmpl': output_filename,
        'max_filesize': 50 * 1024 * 1024,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    if is_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = format_id if format_id != 'best' else 'best/bestvideo+bestaudio'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def post_init(application: Application):
    global BOT_USERNAME
    bot_info = await application.bot.get_me()
    BOT_USERNAME = bot_info.username
    print(f"✅ تم التعرف تلقائياً على معرّف البوت: @{BOT_USERNAME}")

def main():
    Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 VideoHub Downloader يعمل الآن مع التوكين الجديد...")
    app.run_polling()

if __name__ == '__main__':
    main()
 os
