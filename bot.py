import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.INFO)

TOKEN = "8629100412:AAFtcB8IT7D-aXpTSsy2b1Tcu05Ta4JUft4"
CHANNEL_URL = "https://t.me/wanasatt"
CHANNEL_USERNAME = "@wanasatt"

# --- القاموس متعدد اللغات (AR, EN, TR, FA) ---
TEXTS = {
    'ar': {
        'sub_required': "🔒 **الوصول مقيد!** لاستخدام خدمات التحميل، يرجى الانضمام لقناتنا الرسمية أولاً ثم الضغط على زر التحقق بالأسفل 🫆",
        'sub_btn': "📢 انضم للقناة أولاً",
        'check_btn': "🫆 تحقق من الاشتراك",
        'welcome': "🥳 **أهلاً بك يا {name} في بوت التحميل التفاعلي!** ✨\n\n🎮 **ماذا تريد أن تفعل اليوم؟**\nأرسل رابطاً من (TikTok, Instagram, YouTube, X...) وسأقوم بتحميله أو تحويله إلى MP3 فوراً! 🎶🎬",
        'help_btn': "📖 دليل الاستخدام",
        'about_btn': "ℹ️ حول البوت",
        'channel_btn': "📢 القناة الرسمية",
        'invalid_url': "🤔 **هذا لا يبدو كرابط!** أرسل رابطاً يبدأ بـ `http` أو `https`.",
        'analyzing': "🔎 **جاري فحص الرابط وجلب التفاصيل...** ⚡",
        'error_fetch': "💥 **عذراً! تعذر تحليل الرابط.** تأكد أن المقطع عام وليس خاصاً.",
        'mp3_btn': "🎧 استخراج الصوت (MP3)",
        'card_title': "📌 **تفاصيل المقطع:**\n📝 **العنوان:** `{title}`\n⏱️ **المدة:** `{duration}` | 👤 **الناشر:** `{uploader}`\n\n👇 **اختر الخيار المناسب للتحميل:**",
        'downloading_vid': "⚙️ **جاري تحميل وتجهيز الفيديو...** ⏳",
        'downloading_aud': "🎶 **جاري تحويل الفيديو إلى صوت MP3...** ⏳",
        'uploading': "🚀 **جاري الرفع إلى التليجرام...** 📡",
        'success_vid': "✅ **تم التحميل بنجاح!**\n🎬 **{title}**\n\n📢 **قناتنا:** {url}",
        'success_aud': "🎧 **تم استخراج الصوت بنجاح!**\n\n📢 **قناتنا:** {url}",
        'err_dl': "❌ **تعذر التحميل!** قد يكون الحجم كبيراً جداً (أكثر من 50 ميجابايت).",
        'session_exp': "⌛ **انتهت صلاحية الجلسة!** يرجى إرسال الرابط مجدداً.",
        'verified': "🎉 **تم التحقق بنجاح!** أرسل أي رابط الآن للبدء. 🚀",
        'not_verified': "❌ لم تنضم للقناة بعد! اشترك ثم اضغط زر التحقق.",
        'help_text': "📖 **طريقة الاستخدام:**\n1️⃣ انسخ رابط الفيديو من أي تطبيق.\n2️⃣ أرسله هنا في المحادثة.\n3️⃣ اختر الجودة أو تحويله إلى MP3 بنقرة واحدة!",
        'about_text': "ℹ️ **حول البوت:**\nبوت سريع ومطور للتحميل من جميع المنصات بأعلى جودة وبدون علامة مائية. ⚡"
    },
    'en': {
        'sub_required': "🔒 **Access Restricted!** To use download services, please join our channel first and click check 🫆",
        'sub_btn': "📢 Join Channel First",
        'check_btn': "🫆 Verify Subscription",
        'welcome': "🥳 **Welcome {name} to the Downloader Bot!** ✨\n\n🎮 **What would you like to do?**\nSend a link from (TikTok, Instagram, YouTube, X...) and I will download it or convert it to MP3! 🎶🎬",
        'help_btn': "📖 How to use",
        'about_btn': "ℹ️ About Bot",
        'channel_btn': "📢 Official Channel",
        'invalid_url': "🤔 **That doesn't look like a link!** Please send a link starting with `http` or `https`.",
        'analyzing': "🔎 **Analyzing link and fetching details...** ⚡",
        'error_fetch': "💥 **Sorry! Failed to fetch link.** Make sure the video is public.",
        'mp3_btn': "🎧 Extract Audio (MP3)",
        'card_title': "📌 **Media Details:**\n📝 **Title:** `{title}`\n⏱️ **Duration:** `{duration}` | 👤 **Uploader:** `{uploader}`\n\n👇 **Select download option:**",
        'downloading_vid': "⚙️ **Downloading video...** ⏳",
        'downloading_aud': "🎶 **Converting video to MP3...** ⏳",
        'uploading': "🚀 **Uploading to Telegram...** 📡",
        'success_vid': "✅ **Downloaded successfully!**\n🎬 **{title}**\n\n📢 **Our Channel:** {url}",
        'success_aud': "🎧 **Audio extracted successfully!**\n\n📢 **Our Channel:** {url}",
        'err_dl': "❌ **Download failed!** File might exceed 50MB limit.",
        'session_exp': "⌛ **Session expired!** Please send the link again.",
        'verified': "🎉 **Verified successfully!** Send any link to start. 🚀",
        'not_verified': "❌ Not subscribed yet! Join the channel first.",
        'help_text': "📖 **How to use:**\n1️⃣ Copy video link.\n2️⃣ Send it here.\n3️⃣ Choose quality or convert to MP3!",
        'about_text': "ℹ️ **About Bot:**\nFast bot to download from all platforms with high quality and no watermark. ⚡"
    },
    'tr': {
        'sub_required': "🔒 **Erişim Kısıtlandı!** İndirme hizmetlerini kullanmak için lütfen önce kanalımıza katılın ve doğrula butonuna basın 🫆",
        'sub_btn': "📢 Önce Kanala Katıl",
        'check_btn': "🫆 Aboneliği Doğrula",
        'welcome': "🥳 **Hoş geldin {name}!** ✨\n\n🎮 **Bugün ne yapmak istersin?**\n(TikTok, Instagram, YouTube, X...) bağlantısı gönder, hemen indireyim veya MP3'e dönüştüreyim! 🎶🎬",
        'help_btn': "📖 Kullanım Kılavuzu",
        'about_btn': "ℹ️ Bot Hakkında",
        'channel_btn': "📢 Resmi Kanal",
        'invalid_url': "🤔 **Bu bir bağlantı gibi görünmüyor!** `http` veya `https` ile başlayan bir bağlantı gönderin.",
        'analyzing': "🔎 **Bağlantı analiz ediliyor...** ⚡",
        'error_fetch': "💥 **Üzgünüm! Bağlantı alınamadı.** Videonun herkese açık olduğundan emin olun.",
        'mp3_btn': "🎧 Sesi Çıkar (MP3)",
        'card_title': "📌 **Medya Detayları:**\n📝 **Başlık:** `{title}`\n⏱️ **Süre:** `{duration}` | 👤 **Yayınlayan:** `{uploader}`\n\n👇 **İndirme seçeneğini belirleyin:**",
        'downloading_vid': "⚙️ **Video indiriliyor...** ⏳",
        'downloading_aud': "🎶 **MP3'e dönüştürülüyor...** ⏳",
        'uploading': "🚀 **Telegram'a yükleniyor...** 📡",
        'success_vid': "✅ **Başarıyla indirildi!**\n🎬 **{title}**\n\n📢 **Kanalımız:** {url}",
        'success_aud': "🎧 **Ses başarıyla çıkarıldı!**\n\n📢 **Kanalımız:** {url}",
        'err_dl': "❌ **İndirme başarısız!** Dosya boyutu 50MB sınırını aşıyor olabilir.",
        'session_exp': "⌛ **Oturum süresi doldu!** Lütfen bağlantıyı tekrar gönderin.",
        'verified': "🎉 **Başarıyla doğrulandı!** Başlamak için bir bağlantı gönderin. 🚀",
        'not_verified': "❌ Henüz abone olmadınız! Önce kanala katılın.",
        'help_text': "📖 **Kullanım:**\n1️⃣ Bağlantıyı kopyalayın.\n2️⃣ Buraya gönderin.\n3️⃣ Kaliteyi seçin veya MP3'e dönüştürün!",
        'about_text': "ℹ️ **Hakkında:**\nTüm platformlardan filigransız ve yüksek kalitede hızlı indirme botu. ⚡"
    },
    'fa': {
        'sub_required': "🔒 **دسترسی محدود است!** برای استفاده از خدمات دانلود، لطفاً ابتدا عضو کانال شوید و دکمه تایید را بزنید 🫆",
        'sub_btn': "📢 ابتدا عضو کانال شوید",
        'check_btn': "🫆 تایید عضویت",
        'welcome': "🥳 **خوش آمدید {name}!** ✨\n\n🎮 **امروز می‌خواهید چه کاری انجام دهید؟**\nلینک (TikTok, Instagram, YouTube, X...) را بفرستید تا سریعاً ویدیو یا MP3 آن را دریافت کنید! 🎶🎬",
        'help_btn': "📖 راهنمای استفاده",
        'about_btn': "ℹ️ درباره ربات",
        'channel_btn': "📢 کانال رسمی",
        'invalid_url': "🤔 **این یک لینک معتبر نیست!** لینکی ارسال کنید که با `http` یا `https` شروع شود.",
        'analyzing': "🔎 **در حال تحلیل لینک و دریافت اطلاعات...** ⚡",
        'error_fetch': "💥 **متاسفانه لینک تحلیل نشد!** مطمئن شوید ویدیو عمومی است.",
        'mp3_btn': "🎧 استخراج صدا (MP3)",
        'card_title': "📌 **مشخصات فایل:**\n📝 **عنوان:** `{title}`\n⏱️ **مدت زمان:** `{duration}` | 👤 **ناشر:** `{uploader}`\n\n👇 **گزینه دانلود را انتخاب کنید:**",
        'downloading_vid': "⚙️ **در حال دانلود ویدیو...** ⏳",
        'downloading_aud': "🎶 **در حال تبدیل به MP3...** ⏳",
        'uploading': "🚀 **در حال آپلود به تلگرام...** 📡",
        'success_vid': "✅ **با موفقیت دانلود شد!**\n🎬 **{title}**\n\n📢 **کانال ما:** {url}",
        'success_aud': "🎧 **صدا با موفقیت استخراج شد!**\n\n📢 **کانال ما:** {url}",
        'err_dl': "❌ **خطا در دانلود!** ممکن است حجم فایل بیشتر از ۵۰ مگابایت باشد.",
        'session_exp': "⌛ **جلسه منقضی شد!** لطفاً لینک را دوباره ارسال کنید.",
        'verified': "🎉 **عضویت تایید شد!** اکنون یک لینک بفرستید. 🚀",
        'not_verified': "❌ شما هنوز عضو کانال نشده‌اید!",
        'help_text': "📖 **راهنما:**\n1️⃣ لینک را کپی کنید.\n2️⃣ اینجا بفرستید.\n3️⃣ کیفیت را انتخاب یا به MP3 تبدیل کنید!",
        'about_text': "ℹ️ **درباره ربات:**\nربات سریع برای دانلود بدون واترمارک و با بالاترین کیفیت از تمام پلتفرم‌ها. ⚡"
    }
}

# --- دالة الحصول على لغة المستخدم ---
def get_lang(user_lang_code: str) -> dict:
    if not user_lang_code:
        return TEXTS['ar']
    lang = user_lang_code.lower()[:2]
    return TEXTS.get(lang, TEXTS['en'])

# --- دالة فحص الاشتراك الإجباري ---
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Subscription Check Error: {e}")
    return False

# --- الواجهة الرئيسية (/start) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.language_code)
    
    if not await check_subscription(user.id, context):
        keyboard = [
            [InlineKeyboardButton(lang['sub_btn'], url=CHANNEL_URL)],
            [InlineKeyboardButton(lang['check_btn'], callback_data="check_sub")]
        ]
        await update.message.reply_text(
            f"👋 **{user.first_name}**\n\n" + lang['sub_required'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton(lang['help_btn'], callback_data="help"), InlineKeyboardButton(lang['about_btn'], callback_data="about")],
        [InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)]
    ]
    
    welcome_msg = lang['welcome'].format(name=user.first_name)
    await update.message.reply_text(welcome_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- معالجة الرابط ---
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
    title = info.get('title', 'Video')
    duration = info.get('duration_string', 'N/A')
    uploader = info.get('uploader', 'N/A')

    context.user_data[video_id] = {'url': url, 'title': title}

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
                quality_buttons.append(InlineKeyboardButton(f"🎬 {height}p ({badge})", callback_data=f"dl_vid|{video_id}|{format_id}"))
                if len(quality_buttons) == 2:
                    keyboard.append(quality_buttons)
                    quality_buttons = []
                if len(seen_qualities) >= 4:
                    break
                    
    if quality_buttons:
        keyboard.append(quality_buttons)

    if not seen_qualities:
        keyboard.append([InlineKeyboardButton("🎬 Best Quality", callback_data=f"dl_vid|{video_id}|best")])

    keyboard.append([InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)])

    card_text = lang['card_title'].format(
        title=title[:45] + "...",
        duration=duration,
        uploader=uploader
    )
    await status_msg.edit_text(card_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def fetch_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- معالجة الأزرار التفاعلية ---
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

    if action == "help":
        await query.answer()
        await query.message.reply_text(lang['help_text'], parse_mode="Markdown")
        return

    if action == "about":
        await query.answer()
        await query.message.reply_text(lang['about_text'], parse_mode="Markdown")
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

    # تحميل فيديو
    if action == "dl_vid":
        await query.answer()
        format_id = data[2]
        await query.edit_message_text(lang['downloading_vid'], parse_mode="Markdown")
        
        filename = f"{video_id}.mp4"
        try:
            await loop.run_in_executor(None, lambda: download_media(url, format_id, filename, is_audio=False))
            await query.edit_message_text(lang['uploading'], parse_mode="Markdown")
            
            with open(filename, 'rb') as f:
                await query.message.reply_video(
                    video=f,
                    caption=lang['success_vid'].format(title=video_data['title'], url=CHANNEL_URL),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(lang['channel_btn'], url=CHANNEL_URL)]]),
                    parse_mode="Markdown"
                )
            await query.delete_message()
        except Exception as e:
            logging.error(f"Vid Error: {e}")
            await query.message.reply_text(lang['err_dl'])
        finally:
            if os.path.exists(filename): os.remove(filename)

    # تحميل صوت MP3
    elif action == "dl_audio":
        await query.answer()
        await query.edit_message_text(lang['downloading_aud'], parse_mode="Markdown")
        
        filename = f"{video_id}.mp3"
        try:
            await loop.run_in_executor(None, lambda: download_media(url, 'bestaudio/best', filename, is_audio=True))
            await query.edit_message_text(lang['uploading'], parse_mode="Markdown")
            
            with open(filename, 'rb') as f:
                await query.message.reply_audio(
                    audio=f,
                    title=video_data['title'],
                    caption=lang['success_aud'].format(url=CHANNEL_URL),
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

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 البوت متعدد اللغات تعمل الآن بأعلى كفاءة...")
    app.run_polling()

if __name__ == '__main__':
    main()
