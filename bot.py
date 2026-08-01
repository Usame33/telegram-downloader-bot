import os
import re
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
import yt_dlp

# إعداد التسجيل للمراقبة وتشخيص الأخطاء
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# جلب بيانات الاعتماد من متغيرات البيئة (أو وضعها مباشرة)
API_ID = os.getenv("API_ID", "ضع_API_ID_هنا")
API_HASH = os.getenv("API_HASH", "ضع_API_HASH_هنا")
BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_BOT_TOKEN_هنا")
MUST_JOIN_CHANNEL = os.getenv("CHANNEL_USERNAME", "wanasatt") # معرف القناة بدون @

bot = Client(
    "MediaDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# قاموس لتخزين لغة كل مستخدم
USER_LANG = {}

# قاموس اللغات الـ 10 والأصوص الاحترافية
TEXTS = {
    "ar": {
        "flag": "🇸🇾", "name": "العربية",
        "welcome": "👋 **أهلاً بك في بوت تحميل الوسائط المتقدم!**\n\n⚡ يمكنني تحميل الفيديوهات والصوتيات من يوتيوب، تيك توك، إنستغرام، وغيرها بروابط مباشرة وبأعلى جودة.\n\n📌 اختر اللغة أو أرسل رابط الفيديو للبدء مباشرة!",
        "sub_required": "⚠️ **عذراً عزيزي، يجب عليك الاشتراك في قناة البوت أولاً لاستخدام الخدمة:**\n\n📢 @{channel}\n\nبعد الاشتراك اضغط على زر **تأكيد الاشتراك** بالأسفل 👇",
        "sub_btn": "📢 انضم للقناة", "verify_btn": "✅ تم الاشتراك / تأكيد",
        "sub_success": "🎉 شكرًا لاشتراكك! يمكنك الآن إرسال أي رابط لتحميله.",
        "not_subbed": "❌ لم تقم بالاشتراك في القناة بعد! يرجى الانضمام أولاً.",
        "lang_select": "🌐 **اختر لغة واجهة البوت / Select language:**",
        "processing": "⏳ **جاري معالجة الرابط وجلب البيانات...**",
        "choose_format": "🎬 **اختر صيغة التحميل المطلوبة:**\n\n📝 **العنوان:** `{title}`",
        "downloading": "📥 **جاري تنزيل الملف وإرساله... قد يستغرق هذا بضع لحظات.**",
        "error": "❌ **حدث خطأ أثناء معالجة الطلب:**\n`{error}`",
        "btn_video": "📹 فيديو (أعلى جودة)", "btn_audio": "🎵 صوت (MP3)",
        "btn_lang": "🌐 تغيير اللغة", "btn_help": "ℹ️ التعليمات"
    },
    "en": {
        "flag": "🇬🇧", "name": "English",
        "welcome": "👋 **Welcome to Media Downloader Bot!**\n\n⚡ Download videos and audio from YouTube, TikTok, Instagram with high speed.\n\n📌 Send a link to start!",
        "sub_required": "⚠️ **Please subscribe to our channel to use the bot:**\n\n📢 @{channel}",
        "sub_btn": "📢 Join Channel", "verify_btn": "✅ Verify Subscription",
        "sub_success": "🎉 Thank you! Send any link to download.",
        "not_subbed": "❌ You are not subscribed yet!",
        "lang_select": "🌐 **Select your language:**",
        "processing": "⏳ **Processing link...**",
        "choose_format": "🎬 **Choose format:**\n\n📝 **Title:** `{title}`",
        "downloading": "📥 **Downloading and uploading...**",
        "error": "❌ **Error:**\n`{error}`",
        "btn_video": "📹 Video (Best Quality)", "btn_audio": "🎵 Audio (MP3)",
        "btn_lang": "🌐 Change Language", "btn_help": "ℹ️ Help"
    },
    "tr": {
        "flag": "🇹🇷", "name": "Türkçe",
        "welcome": "👋 **Medya İndirme Botuna Hoş Geldiniz!**",
        "sub_required": "⚠️ **Botu kullanmak için kanala abone olmalısınız:**\n📢 @{channel}",
        "sub_btn": "📢 Kanala Katıl", "verify_btn": "✅ Onayla",
        "sub_success": "🎉 Teşekkürler! Artık botu kullanabilirsiniz.",
        "not_subbed": "❌ Henüz abone olmadınız!",
        "lang_select": "🌐 **Dil seçin:**",
        "processing": "⏳ **Bağlantı işleniyor...**",
        "choose_format": "🎬 **Format seçin:**\n\n📝 **Başlık:** `{title}`",
        "downloading": "📥 **İndiriliyor ve gönderiliyor...**",
        "error": "❌ **Hata:**\n`{error}`",
        "btn_video": "📹 Video", "btn_audio": "🎵 Ses MP3",
        "btn_lang": "🌐 Dili Değiştir", "btn_help": "ℹ️ Yardım"
    },
    "es": {
        "flag": "🇪🇸", "name": "Español",
        "welcome": "👋 **¡Bienvenido al Bot Descargador!**",
        "sub_required": "⚠️ **Debes suscribirte al canal:**\n📢 @{channel}",
        "sub_btn": "📢 Unirse al Canal", "verify_btn": "✅ Verificar",
        "sub_success": "🎉 ¡Gracias por suscribirte!",
        "not_subbed": "❌ ¡Aún no estás suscrito!",
        "lang_select": "🌐 **Selecciona idioma:**",
        "processing": "⏳ **Procesando enlace...**",
        "choose_format": "🎬 **Elige formato:**",
        "downloading": "📥 **Descargando...**",
        "error": "❌ **Error:**\n`{error}`",
        "btn_video": "📹 Video", "btn_audio": "🎵 Audio MP3",
        "btn_lang": "🌐 Cambiar idioma", "btn_help": "ℹ️ Ayuda"
    },
    "fr": {
        "flag": "🇫🇷", "name": "Français",
        "welcome": "👋 **Bienvenue sur le Bot Téléchargeur!**",
        "sub_required": "⚠️ **Abonnez-vous à la chaîne:**\n📢 @{channel}",
        "sub_btn": "📢 Rejoindre le canal", "verify_btn": "✅ Vérifier",
        "sub_success": "🎉 Merci pour votre abonnement!",
        "not_subbed": "❌ Vous n'êtes pas abonné!",
        "lang_select": "🌐 **Choisissez votre langue:**",
        "processing": "⏳ **Traitement du lien...**",
        "choose_format": "🎬 **Format:**",
        "downloading": "📥 **Téléchargement...**",
        "error": "❌ **Erreur:**\n`{error}`",
        "btn_video": "📹 Vidéo", "btn_audio": "🎵 MP3",
        "btn_lang": "🌐 Langue", "btn_help": "ℹ️ Aide"
    },
    "de": {
        "flag": "🇩🇪", "name": "Deutsch",
        "welcome": "👋 **Willkommen beim Media Downloader Bot!**",
        "sub_required": "⚠️ **Bitte Kanal abonnieren:**\n📢 @{channel}",
        "sub_btn": "📢 Kanal beitreten", "verify_btn": "✅ Bestätigen",
        "sub_success": "🎉 Danke für das Abonnement!",
        "not_subbed": "❌ Noch nicht abonniert!",
        "lang_select": "🌐 **Sprache wählen:**",
        "processing": "⏳ **Verarbeite Link...**",
        "choose_format": "🎬 **Format wählen:**",
        "downloading": "📥 **Download läuft...**",
        "error": "❌ **Fehler:**\n`{error}`",
        "btn_video": "📹 Video", "btn_audio": "🎵 Audio MP3",
        "btn_lang": "🌐 Sprache ändern", "btn_help": "ℹ️ Hilfe"
    },
    "ru": {
        "flag": "🇷🇺", "name": "Русский",
        "welcome": "👋 **Добро пожаловать в Медиа Загрузчик!**",
        "sub_required": "⚠️ **Подпишитесь на канал:**\n📢 @{channel}",
        "sub_btn": "📢 Подписаться", "verify_btn": "✅ Проверить",
        "sub_success": "🎉 Спасибо за подписку!",
        "not_subbed": "❌ Вы еще не подписались!",
        "lang_select": "🌐 **Выберите язык:**",
        "processing": "⏳ **Обработка...**",
        "choose_format": "🎬 **Выберите формат:**",
        "downloading": "📥 **Загрузка...**",
        "error": "❌ **Ошибка:**\n`{error}`",
        "btn_video": "📹 Видео", "btn_audio": "🎵 Аудио MP3",
        "btn_lang": "🌐 Сменить язык", "btn_help": "ℹ️ Помощь"
    },
    "hi": {
        "flag": "🇮🇳", "name": "हिन्दी",
        "welcome": "👋 **मीडिया डाउनलोडर में आपका स्वागत है!**",
        "sub_required": "⚠️ **कृपया चैनल की सदस्यता लें:**\n📢 @{channel}",
        "sub_btn": "📢 चैनल से जुड़ें", "verify_btn": "✅ पुष्टि करें",
        "sub_success": "🎉 धन्यवाद!",
        "not_subbed": "❌ आपने सदस्यता नहीं ली है!",
        "lang_select": "🌐 **भाषा चुनें:**",
        "processing": "⏳ **प्रोसेसिंग...**",
        "choose_format": "🎬 **स्वरूप चुनें:**",
        "downloading": "📥 **डाउनलोड हो रहा है...**",
        "error": "❌ **त्रुटि:**\n`{error}`",
        "btn_video": "📹 वीडियो", "btn_audio": "🎵 ऑडियो MP3",
        "btn_lang": "🌐 भाषा बदलें", "btn_help": "ℹ️ सहायता"
    },
    "zh": {
        "flag": "🇨🇳", "name": "中文",
        "welcome": "👋 **欢迎使用媒体下载机器人！**",
        "sub_required": "⚠️ **请先关注频道：**\n📢 @{channel}",
        "sub_btn": "📢 加入频道", "verify_btn": "✅ 验证",
        "sub_success": "🎉 感谢关注！",
        "not_subbed": "❌ 您尚未关注！",
        "lang_select": "🌐 **选择语言：**",
        "processing": "⏳ **处理中...**",
        "choose_format": "🎬 **选择格式：**",
        "downloading": "📥 **下载中...**",
        "error": "❌ **错误：**\n`{error}`",
        "btn_video": "📹 视频", "btn_audio": "🎵 音频 MP3",
        "btn_lang": "🌐 语言", "btn_help": "ℹ️ 帮助"
    },
    "fa": {
        "flag": "🇮🇷", "name": "فارسی",
        "welcome": "👋 **به ربات دانلودر خوش آمدید!**",
        "sub_required": "⚠️ **لطفاً ابتدا عضو کانال شوید:**\n📢 @{channel}",
        "sub_btn": "📢 عضویت در کانال", "verify_btn": "✅ تایید",
        "sub_success": "🎉 با تشکر از عضویت شما!",
        "not_subbed": "❌ شما عضو نشده‌اید!",
        "lang_select": "🌐 **انتخاب زبان:**",
        "processing": "⏳ **در حال پردازش...**",
        "choose_format": "🎬 **انتخاب فرمت:**",
        "downloading": "📥 **در حال دانلود...**",
        "error": "❌ **خطا:**\n`{error}`",
        "btn_video": "📹 ویدیو", "btn_audio": "🎵 صوتی MP3",
        "btn_lang": "🌐 تغییر زبان", "btn_help": "ℹ️ راهنما"
    }
}

def get_text(user_id, key):
    lang = USER_LANG.get(user_id, "ar")
    return TEXTS.get(lang, TEXTS["ar"]).get(key, "")

# التحقق من الاشتراك الإجباري
async def check_subscription(client: Client, user_id: int):
    if not MUST_JOIN_CHANNEL:
        return True
    try:
        member = await client.get_chat_member(f"@{MUST_JOIN_CHANNEL}", user_id)
        if member.status in ["owner", "administrator", "member"]:
            return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return True
    return False

def build_lang_keyboard():
    buttons = []
    keys = list(TEXTS.keys())
    for i in range(0, len(keys), 2):
        row = []
        k1 = keys[i]
        row.append(InlineKeyboardButton(f"{TEXTS[k1]['flag']} {TEXTS[k1]['name']}", callback_data=f"setlang_{k1}"))
        if i + 1 < len(keys):
            k2 = keys[i+1]
            row.append(InlineKeyboardButton(f"{TEXTS[k2]['flag']} {TEXTS[k2]['name']}", callback_data=f"setlang_{k2}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

# أمر Start
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if not await check_subscription(client, user_id):
        txt = get_text(user_id, "sub_required").format(channel=MUST_JOIN_CHANNEL)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user_id, "sub_btn"), url=f"https://t.me/{MUST_JOIN_CHANNEL}")],
            [InlineKeyboardButton(get_text(user_id, "verify_btn"), callback_data="check_sub")]
        ])
        await message.reply_text(txt, reply_markup=kb)
        return

    welcome_txt = get_text(user_id, "welcome")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, "btn_lang"), callback_data="change_lang")]
    ])
    await message.reply_text(welcome_txt, reply_markup=kb)

# استقبال تغيير اللغة
@bot.on_callback_query(filters.regex("^change_lang$"))
async def change_language_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(get_text(user_id, "lang_select"), reply_markup=build_lang_keyboard())

@bot.on_callback_query(filters.regex("^setlang_"))
async def set_language_cb(client: Client, callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id
    USER_LANG[user_id] = lang_code
    await callback.answer("✅ Done")
    welcome_txt = get_text(user_id, "welcome")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, "btn_lang"), callback_data="change_lang")]
    ])
    await callback.message.edit_text(welcome_txt, reply_markup=kb)

# التحقق عند الضغط على زر "تأكيد الاشتراك"
@bot.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(client, user_id):
        await callback.answer(get_text(user_id, "sub_success"), show_alert=True)
        await callback.message.delete()
        await start_handler(client, callback.message)
    else:
        await callback.answer(get_text(user_id, "not_subbed"), show_alert=True)

# معالجة الروابط لجميع المواقع
@bot.on_message(filters.private & filters.text & ~filters.command(["start"]))
async def download_link_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if not await check_subscription(client, user_id):
        txt = get_text(user_id, "sub_required").format(channel=MUST_JOIN_CHANNEL)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user_id, "sub_btn"), url=f"https://t.me/{MUST_JOIN_CHANNEL}")],
            [InlineKeyboardButton(get_text(user_id, "verify_btn"), callback_data="check_sub")]
        ])
        await message.reply_text(txt, reply_markup=kb)
        return

    url = message.text.strip()
    if not re.match(r'https?://[^\s]+', url):
        return

    msg = await message.reply_text(get_text(user_id, "processing"))

    # إعدادات yt-dlp مع تفعيل الكوكيز والخيارات المتقدمة
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    loop = asyncio.get_event_loop()
    try:
        def fetch_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, fetch_info)
        title = info.get('title', 'Media File')
        
        # تخزين الرابط للخطوة التالية عبر Callback
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(get_text(user_id, "btn_video"), callback_data="dl_video"),
                InlineKeyboardButton(get_text(user_id, "btn_audio"), callback_data="dl_audio")
            ]
        ])
        
        await msg.edit_text(
            get_text(user_id, "choose_format").format(title=title),
            reply_markup=kb
        )
        
        # ربط الرابط المؤقت بالحساب
        bot.temp_store = getattr(bot, 'temp_store', {})
        bot.temp_store[user_id] = url

    except Exception as e:
        await msg.edit_text(get_text(user_id, "error").format(error=str(e)))

# تنزيل الصوت والفيديو بناء على اختيار المستخدم
@bot.on_callback_query(filters.regex("^dl_"))
async def process_download_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data
    url = getattr(bot, 'temp_store', {}).get(user_id)

    if not url:
        await callback.answer("⚠️ Session expired. Send link again.")
        return

    await callback.message.edit_text(get_text(user_id, "downloading"))
    out_file = f"download_{user_id}"

    if action == "dl_audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{out_file}.%(ext)s',
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        ext = "mp3"
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'{out_file}.%(ext)s',
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        }
        ext = "mp4"

    loop = asyncio.get_event_loop()
    try:
        def do_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        info = await loop.run_in_executor(None, do_download)
        file_path = f"{out_file}.{ext}"
        if not os.path.exists(file_path):
            # البحث عن الملف المنزل في حال اختلاف الامتداد
            for f in os.listdir("."):
                if f.startswith(out_file):
                    file_path = f
                    break

        if action == "dl_audio":
            await client.send_audio(chat_id=callback.message.chat.id, audio=file_path, caption=info.get('title'))
        else:
            await client.send_video(chat_id=callback.message.chat.id, video=file_path, caption=info.get('title'))

        await callback.message.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await callback.message.edit_text(get_text(user_id, "error").format(error=str(e)))

if __name__ == "__main__":
    print("🤖 Bot is starting...")
    bot.run()
