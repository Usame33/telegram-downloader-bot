import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.INFO)

# 🔑 التوكن والمعلومات الخاصة بك
TOKEN = "8629100412:AAE3o7PxOhixD91H3yRQtg2MslbCp8k-Mzo"
CHANNEL_URL = "https://t.me/wanasatt"
CHANNEL_USERNAME = "@wanasatt"

# 🤖 معرف البوت الخاص بك
BOT_USERNAME = "@Ussame_bot"

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

# --- 🌍 نظام اللغات والواجهة الاحترافية ---
TEXTS = {
    'ar': {
        'welcome': (
            "✨ **مرحباً بك في VideoHub Pro** ✨\n"
            "─── ･ ｡ﾟ☆: *.☽ .* :☆ﾟ. ───\n\n"
            "🚀 **أسرع بوت لتحميل الفيديوهات والصوتيات**\n\n"
            "💎 **المميزات:**\n"
            " ├ 🎞️ تحميل بأعلى الجودات (HD / SD)\n"
            " ├ 🎵 تحويل مجاني ومباشر إلى MP3\n"
            " ├ 🌍 دعم منصات: YouTube, TikTok, Instagram, Twitter...\n"
            " └ ⚡ خوادم فائقة السرعة تعمل 24/7\n\n"
            "📌 **كيفية الاستخدام:**\n"
            "فقط أرسل رابط الفيديو المباشر وسأقوم بالباقي!"
        ),
        'sub_required': (
            "🔒 **اشتراك إجباري في القناة**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "لاستخدام البوت والاستمتاع بالتحميل السريع، يرجى الاشتراك في قناتنا الرسمية أولاً.\n\n"
            "👇 اشترك الآن ثم اضغط على زر **التحقق**."
        ),
        'sub_btn': "📢 اشتراك في القناة",
        'check_btn': "🔄 التحقق من الاشتراك",
        'channel_btn': "📢 القناة الرسمية",
        'lang_btn': "🌐 تغيير اللغة / Language",
        'select_lang': "🌐 **اختر لغتك المفضلة / Select Your Language:**",
        'lang_changed': "✅ تم تغيير اللغة إلى العربية بنجاح!",
        'invalid_url': "⚠️ **رابط غير صالح!** يرجى إرسال رابط صحيح يبدأ بـ `http://` أو `https://`",
        'analyzing': (
            "🔄 **جارِ معالجة الرابط...**\n"
            " ├ 🔍 فحص المنصة...\n"
            " └ ⚙️ جلب الجودات المتاحة..."
        ),
        'error_fetch': "❌ **تعذر تحليل الرابط!** تأكد من أن الفيديو عام وليس خاصاً أو محذوفاً.",
        'mp3_btn': "🎵 تحويل الصوت (MP3)",
        'card_title': (
            "🎬 **تفاصيل المقطع:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📌 **العنوان:**\n`{title}`\n\n"
            "👤 **الناشر:** `{uploader}`\n"
            "⏱️ **المدة:** `{duration}`\n"
            "🌐 **المنصة:** `{extractor}`\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "👇 **اختر صيغة أو جودة التحميل:**"
        ),
        'downloading_vid': "📥 **جارِ تحميل وتجهيز الفيديو...** ⏳",
        'downloading_aud': "🎶 **جارِ استخراج وتحويل الصوت...** ⏳",
        'uploading': "🚀 **جارِ رفع الملف إليك...** 📡",
        'success_vid': (
            "✅ **تم التحميل بنجاح!**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎬 **العنوان:** {title}\n"
            "👤 **الناشر:** {uploader}\n"
            "⏱️ **المدة:** {duration}\n"
            "🎞️ **الجودة:** {quality}\n\n"
            "🤖 **البوت:** [Ussame_bot](https://t.me/Ussame_bot)\n"
            "📢 **القناة:** [وناسة](https://t.me/wanasatt)\n"
            "━━━━━━━━━━━━━━━━━━"
        ),
        'err_dl': "❌ **فشل التحميل!** قد يتجاوز حجم الفيديو الحد المسموح (50 ميجابايت).",
        'session_exp': "⚠️ **انتهت الجلسة!** أرسل الرابط مرة أخرى.",
        'verified': "🎉 **تم التحقق بنجاح!** يمكنك الآن إرسال الروابط للتحميل. 🚀",
        'not_verified': "❌ لم تشترك بالقناة بعد! اشترك أولاً ثم حاول مجدداً."
    },
    'en': {
        'welcome': (
            "✨ **Welcome to VideoHub Pro** ✨\n"
            "─── ･ ｡ﾟ☆: *.☽ .* :☆ﾟ. ───\n\n"
            "🚀 **Fastest Video & Audio Downloader**\n\n"
            "💎 **Features:**\n"
            " ├ 🎞️ High Quality Downloads (HD / SD)\n"
            " ├ 🎵 Free MP3 Audio Conversion\n"
            " ├ 🌍 Supports: YouTube, TikTok, Instagram, Twitter...\n"
            " └ ⚡ Ultra-fast servers 24/7\n\n"
            "📌 **How to use:**\n"
            "Just send any video link and I'll handle the rest!"
        ),
        'sub_required': (
            "🔒 **Channel Subscription Required**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "To use this bot, please subscribe to our official channel first.\n\n"
            "👇 Join now then click **Verify**."
        ),
        'sub_btn': "📢 Join Channel",
        'check_btn': "🔄 Verify Subscription",
        'channel_btn': "📢 Official Channel",
        'lang_btn': "🌐 Language / اللغة",
        'select_lang': "🌐 **Select Your Language / اختر لغتك:**",
        'lang_changed': "✅ Language successfully set to English!",
        'invalid_url': "⚠️ **Invalid URL!** Please send a valid link starting with `http://` or `https://`",
        'analyzing': (
            "🔄 **Processing link...**\n"
            " ├ 🔍 Checking platform...\n"
            " └ ⚙️ Fetching available qualities..."
        ),
        'error_fetch': "❌ **Failed to process link!** Make sure the video is public and valid.",
        'mp3_btn': "🎵 Convert to MP3",
        'card_title': (
            "🎬 **Video Details:**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📌 **Title:**\n`{title}`\n\n"
            "👤 **Uploader:** `{uploader}`\n"
            "⏱️ **Duration:** `{duration}`\n"
            "🌐 **Platform:** `{extractor}`\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "👇 **Choose download format or quality:**"
        ),
        'downloading_vid': "📥 **Downloading & preparing video...** ⏳",
        'downloading_aud': "🎶 **Extracting & converting audio...** ⏳",
        'uploading': "🚀 **Uploading file to Telegram...** 📡",
        'success_vid': (
            "✅ **Downloaded Successfully!**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎬 **Title:** {title}\n"
            "👤 **Uploader:** {uploader}\n"
            "⏱️ **Duration:** {duration}\n"
            "🎞️ **Quality:** {quality}\n\n"
            "🤖 **Bot:** [Ussame_bot](https://t.me/Ussame_bot)\n"
            "📢 **Channel:** [Wanasatt](https://t.me/wanasatt)\n"
            "━━━━━━━━━━━━━━━━━━"
        ),
        'err_dl': "❌ **Download failed!** File size may exceed 50MB limit.",
        'session_exp': "⚠️ **Session expired!** Please send the link again.",
        'verified': "🎉 **Verified successfully!** Send any link now to start. 🚀",
        'not_verified': "❌ You haven't subscribed yet! Join the channel and try again."
    },
    'es': {
        'welcome': "✨ **Bienvenido a VideoHub Pro** ✨\n\n🚀 **Descargador rápido**",
        'sub_required': "🔒 **Suscripción requerida**\nPor favor únete al canal.",
        'sub_btn': "📢 Unirse al Canal",
        'check_btn': "🔄 Verificar",
        'channel_btn': "📢 Canal Oficial",
        'lang_btn': "🌐 Idioma",
        'select_lang': "🌐 **Selecciona tu idioma:**",
        'lang_changed': "✅ ¡Idioma cambiado a Español!",
        'invalid_url': "⚠️ **¡Enlace no válido!**",
        'analyzing': "🔄 **Procesando...**",
        'error_fetch': "❌ **Error al procesar**",
        'mp3_btn': "🎵 Convertir a MP3",
        'card_title': "🎬 **Detalles:**\n\n📌 `{title}`",
        'downloading_vid': "📥 **Descargando...**",
        'downloading_aud': "🎶 **Convirtiendo...**",
        'uploading': "🚀 **Subiendo...**",
        'success_vid': (
            "✅ **¡Descargado con éxito!**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎬 **Título:** {title}\n"
            "🎞️ **Calidad:** {quality}\n\n"
            "🤖 **Por:** [Ussame_bot](https://t.me/Ussame_bot)\n"
            "📢 **Canal:** [Wanasatt](https://t.me/wanasatt)\n"
            "━━━━━━━━━━━━━━━━━━"
        ),
        'err_dl': "❌ **Error de descarga**",
        'session_exp': "⚠️ **Sesión expirada**",
        'verified': "🎉 **Verificado**",
        'not_verified': "❌ No te has suscrito"
    },
    'fr': {
        'welcome': "✨ **Bienvenue sur VideoHub Pro** ✨\n\n🚀 **Téléchargeur rapide**",
        'sub_required': "🔒 **Abonnement Requis**",
        'sub_btn': "📢 Rejoindre la chaîne",
        'check_btn': "🔄 Vérifier",
        'channel_btn': "📢 Chaîne Officielle",
        'lang_btn': "🌐 Langue",
        'select_lang': "🌐 **Choisissez votre langue:**",
        'lang_changed': "✅ Langue changée en Français!",
        'invalid_url': "⚠️ **Lien invalide!**",
        'analyzing': "🔄 **Traitement...**",
        'error_fetch': "❌ **Échec!**",
        'mp3_btn': "🎵 Convertir en MP3",
        'card_title': "🎬 **Détails:**\n\n📌 `{title}`",
        'downloading_vid': "📥 **Téléchargement...**",
        'downloading_aud': "🎶 **Conversion MP3...**",
        'uploading': "🚀 **Envoi...**",
        'success_vid': (
            "✅ **Téléchargé avec succès!**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎬 **Titre:** {title}\n"
            "🎞️ **Qualité:** {quality}\n\n"
            "🤖 **Via:** [Ussame_bot](https://t.me/Ussame_bot)\n"
            "📢 **Chaîne:** [Wanasatt](https://t.me/wanasatt)\n"
            "━━━━━━━━━━━━━━━━━━"
        ),
        'err_dl': "❌ **Échec!**",
        'session_exp': "⚠️ **Session expirée!**",
        'verified': "🎉 **Vérifié avec succès!**",
        'not_verified': "❌ Pas encore abonné."
    }
}

def get_user_lang(user_data: dict, telegram_lang: str) -> str:
    if 'lang' in user_data:
        return user_data['lang']
    if telegram_lang:
        code = telegram_lang.lower()[:2]
        if code in TEXTS:
            return code
    return 'ar'

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
    lang_code = get_user_lang(context.user_data, user.language_code)
    lang = TEXTS[lang_code]
    
    if not await check_subscription(user.id, context):
        keyboard = [
            [InlineKeyboardButton(lang['sub_btn'], url=CHANNEL_URL)],
            [InlineKeyboardButton(lang['check_btn'], callback_data="check_sub")],
            [InlineKeyboardButton(lang['lang_btn'], callback_data="open_lang")]
        ]
        await update.message.reply_text(lang['sub_required'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    keyboard = [
        [InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)],
        [InlineKeyboardButton(lang['lang_btn'], callback_data="open_lang")]
    ]
    await update.message.reply_text(lang['welcome'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_language_selector(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang|ar"), InlineKeyboardButton("🇬🇧 English", callback_data="set_lang|en")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="set_lang|es"), InlineKeyboardButton("🇫🇷 Français", callback_data="set_lang|fr")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update_or_query, 'message') and update_or_query.message:
        await update_or_query.message.reply_text("🌐 **Select Language / اختر اللغة:**", reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text("🌐 **Select Language / اختر اللغة:**", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang_code = get_user_lang(context.user_data, user.language_code)
    lang = TEXTS[lang_code]
    
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
    title = info.get('title', 'Video')
    duration = info.get('duration_string', 'N/A')
    uploader = info.get('uploader', 'Unknown')
    extractor = info.get('extractor_key', 'Web')

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
                badge = "✨ HD" if height >= 720 else "📱 SD"
                quality_buttons.append(InlineKeyboardButton(f"🎬 {height}p ({badge})", callback_data=f"dl_vid|{video_id}|{format_id}|{height}p"))
                if len(quality_buttons) == 2:
                    keyboard.append(quality_buttons)
                    quality_buttons = []
                if len(seen_qualities) >= 4:
                    break
                    
    if quality_buttons:
        keyboard.append(quality_buttons)

    if not seen_qualities:
        keyboard.append([InlineKeyboardButton("🎬 Best Quality / أعلى جودة", callback_data=f"dl_vid|{video_id}|best|HD")])

    keyboard.append([InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)])

    card_text = lang['card_title'].format(
        title=title[:50] + "..." if len(title) > 50 else title,
        uploader=uploader,
        duration=duration,
        extractor=extractor
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
    data = query.data.split("|")
    action = data[0]

    if action == "open_lang":
        await query.answer()
        await show_language_selector(query, context)
        return

    if action == "set_lang":
        selected_lang = data[1]
        context.user_data['lang'] = selected_lang
        lang = TEXTS[selected_lang]
        await query.answer(lang['lang_changed'], show_alert=True)
        keyboard = [
            [InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)],
            [InlineKeyboardButton(lang['lang_btn'], callback_data="open_lang")]
        ]
        await query.edit_message_text(lang['welcome'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    lang_code = get_user_lang(context.user_data, user.language_code)
    lang = TEXTS[lang_code]

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
                duration=video_data['duration'],
                quality=quality
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
            if os.path.exists(filename):
                os.remove(filename)

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
                duration=video_data['duration'],
                quality="MP3 (Audio)"
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
            if os.path.exists(filename):
                os.remove(filename)

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

def main():
    Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_callback))

    print(f"🚀 البوت {BOT_USERNAME} يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
