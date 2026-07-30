import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

# ====================== CONFIG ======================
TOKEN = "8629100412:AAFzVLA9uur4pIVX0oHBs8N4fqB6nz3ub-k"  # ضع توكنك هنا
CHANNEL_ID = "@wanasatt"          # معرف القناة
CHANNEL_URL = "https://t.me/wanasatt"

DOWNLOAD_PATH = Path("downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================== TRANSLATIONS ======================
translations = {
    "ar": {
        "start": "🌟 مرحباً بك في بوت التحميل الاحترافي!\n\nأرسل الرابط لتحميل الفيديو.",
        "subscribe_first": "⚠️ يجب عليك الاشتراك في القناة أولاً لاستخدام البوت.",
        "subscribe": "اشترك في القناة",
        "processing": "⏳ جاري التحليل...",
        "downloading": "⬇️ جاري التحميل...",
        "uploading": "⬆️ جاري الرفع...",
        "success": "✅ تم التحميل بنجاح!",
        "error": "❌ حدث خطأ، حاول مرة أخرى.",
    },
    "tr": {
        "start": "🌟 Profesyonel İndirme Botuna Hoş Geldiniz!\n\nVideoyu indirmek için linki gönderin.",
        "subscribe_first": "⚠️ Botu kullanmak için önce kanala abone olmalısınız.",
        "subscribe": "Kanala Abone Ol",
        "processing": "⏳ Analiz ediliyor...",
        "downloading": "⬇️ İndiriliyor...",
        "uploading": "⬆️ Yükleniyor...",
        "success": "✅ Başarıyla indirildi!",
        "error": "❌ Hata oluştu, tekrar deneyin.",
    },
    "en": {
        "start": "🌟 Welcome to the Professional Video Downloader Bot!\n\nSend the link to download.",
        "subscribe_first": "⚠️ You must subscribe to the channel first to use the bot.",
        "subscribe": "Subscribe to Channel",
        "processing": "⏳ Analyzing...",
        "downloading": "⬇️ Downloading...",
        "uploading": "⬆️ Uploading...",
        "success": "✅ Downloaded successfully!",
        "error": "❌ An error occurred, please try again.",
    },
    "ru": {
        "start": "🌟 Добро пожаловать в профессионального бота для скачивания видео!\n\nОтправьте ссылку для скачивания.",
        "subscribe_first": "⚠️ Чтобы использовать бота, сначала подпишитесь на канал.",
        "subscribe": "Подписаться на канал",
        "processing": "⏳ Анализ...",
        "downloading": "⬇️ Скачивание...",
        "uploading": "⬆️ Загрузка...",
        "success": "✅ Успешно скачано!",
        "error": "❌ Произошла ошибка, попробуйте снова.",
    }
}

def get_lang(user_lang: str):
    lang_map = {"ar": "ar", "tr": "tr", "en": "en", "ru": "ru"}
    return lang_map.get(user_lang, "ar")  # العربية افتراضي

# ====================== CHECK SUBSCRIPTION ======================
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ====================== KEYBOARDS ======================
def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 اشترك الآن", url=CHANNEL_URL)]
    ])

def subscribe_keyboard_multi(lang: str):
    text = translations[lang]["subscribe"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, url=CHANNEL_URL)]
    ])

# ====================== HANDLERS ======================
@router.message(Command("start"))
async def start(message: Message):
    lang = get_lang(message.from_user.language_code)
    await message.answer(
        translations[lang]["start"],
        reply_markup=subscribe_keyboard()
    )


@router.message(F.text)
async def handle_url(message: Message):
    lang = get_lang(message.from_user.language_code)

    if not await is_subscribed(message.from_user.id):
        return await message.answer(
            translations[lang]["subscribe_first"],
            reply_markup=subscribe_keyboard_multi(lang)
        )

    url = re.findall(r'https?://[^\s]+', message.text)
    if not url:
        return

    url = url[0]
    status_msg = await message.answer(f"{translations[lang]['processing']}")

    try:
        # استخراج المعلومات
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get('title', 'Video')[:100]
        video_id = str(hash(url))[-10:]

        bot.video_data = getattr(bot, 'video_data', {})
        bot.video_data[video_id] = {"url": url, "title": title, "lang": lang, "user_id": message.from_user.id}

        await status_msg.edit_text(
            f"🎥 <b>{title}</b>\n\n"
            f"اختر الجودة:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎥 1080p", callback_data=f"q_{video_id}_1080")],
                [InlineKeyboardButton(text="🎥 720p", callback_data=f"q_{video_id}_720")],
                [InlineKeyboardButton(text="🎥 480p", callback_data=f"q_{video_id}_480")],
                [InlineKeyboardButton(text="🎵 MP3", callback_data=f"q_{video_id}_audio")]
            ])
        )

    except Exception as e:
        await status_msg.edit_text(translations[lang]["error"])


@router.callback_query(F.data.startswith("q_"))
async def quality_callback(callback: CallbackQuery):
    _, video_id, quality = callback.data.split("_")
    data = getattr(bot, 'video_data', {}).get(video_id)
    if not data:
        return await callback.answer("انتهت الصلاحية", show_alert=True)

    lang = data["lang"]
    await callback.message.edit_text(translations[lang]["downloading"])

    try:
        url = data["url"]
        title = data["title"]
        safe_title = "".join(c if c.isalnum() else "_" for c in title)[:80]
        output_path = str(DOWNLOAD_PATH / f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.%(ext)s")

        format_str = "bestaudio/best" if quality == "audio" else f"bestvideo[height<={quality}]+bestaudio/best"

        ydl_opts = {'format': format_str, 'outtmpl': output_path, 'merge_output_format': 'mp4'}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = list(DOWNLOAD_PATH.glob(f"{safe_title}*"))
        video_file = max(files, key=os.path.getsize)

        sub_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=translations[lang]["subscribe"], url=CHANNEL_URL)]
        ])

        caption = f"{translations[lang]['success']}\n\n🎬 {title}"

        if quality == "audio":
            await bot.send_audio(callback.message.chat.id, FSInputFile(video_file), caption=caption, reply_markup=sub_btn)
        else:
            await bot.send_video(callback.message.chat.id, FSInputFile(video_file), caption=caption, reply_markup=sub_btn, supports_streaming=True)

        await callback.message.delete()
        video_file.unlink(missing_ok=True)

    except Exception as e:
        await callback.message.edit_text(translations[lang]["error"])


dp.include_router(router)

async def main():
    print("🚀 البوت يعمل الآن @Ussame_bot")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()):",
        'sub_required': "⚠️ عذراً، يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه!",
        'check_sub': "🫆 تحقق من الاشتراك",
        'send_link': "✅ أرسل رابط الفيديو الآن (يوتيوب، تيك توك، إنستغرام، فيسبوك...):",
        'choose_quality': "إليك الجودات المتاحة والصيغ، اختر ما يناسبك:",
        'downloading': "⏳ جاري جلب الفيديو ومعالجة البيانات...",
        'uploading': "📤 جاري رفع الملف إلى تلجرام...",
        'channel_btn': "📢 القناة الرسمية",
        'bot_btn': "🤖 مشاركة البوت",
        'error': "❌ حدث خطأ، يرجى التأكد من صحة الرابط أو محاولة جودة أخرى."
    },
    'en': {
        'select_lang': "Welcome to the All-in-One Downloader Bot! 🎥\nPlease select your language:",
        'sub_required': "⚠️ Sorry, you must subscribe to our channel first to use the bot!",
        'check_sub': "🫆 Check Subscription",
        'send_link': "✅ Send the video link now (YouTube, TikTok, Instagram, Facebook...):",
        'choose_quality': "Select your preferred quality or format:",
        'downloading': "⏳ Processing video...",
        'uploading': "📤 Uploading file...",
        'channel_btn': "📢 Official Channel",
        'bot_btn': "🤖 Share Bot",
        'error': "❌ An error occurred. Please check the link or try another quality."
    },
    'tr': {
        'select_lang': "Hepsi Bir Arada İndirici Botuna Hoş Geldiniz! 🎥\nLütfen dilinizi seçin:",
        'sub_required': "⚠️ Üzgünüz, botu kullanmak için önce kanalımıza abone olmalısınız!",
        'check_sub': "🫆 Aboneliği Kontrol Et",
        'send_link': "✅ Video bağlantısını şimdi gönderin (YouTube, TikTok, Instagram, Facebook...):",
        'choose_quality': "Lütfen kalite veya format seçin:",
        'downloading': "⏳ Video işleniyor...",
        'uploading': "📤 Dosya yükleniyor...",
        'channel_btn': "📢 Resmi Kanal",
        'bot_btn': "🤖 Botu Paylaş",
        'error': "❌ Bir hata oluştu, lütfen bağlantıyı kontrol edin."
    },
    'ru': {
        'select_lang': "Добро пожаловать в универсальный бот-загрузчик! 🎥\nПожалуйста, выберите язык:",
        'sub_required': "⚠️ Извините, вы должны сначала подписаться на наш канал!",
        'check_sub': "🫆 Проверить подписку",
        'send_link': "✅ Отправьте ссылку на видео (YouTube, TikTok, Instagram, Facebook...):",
        'choose_quality': "Выберите качество или формат:",
        'downloading': "⏳ Обработка видео...",
        'uploading': "📤 Загрузка файла...",
        'channel_btn': "📢 Официальный канал",
        'bot_btn': "🤖 Поделиться ботом",
        'error': "❌ Произошла ошибка, проверьте ссылку."
    }
}

# دالة التحقق من اشتراك المستخدم في القناة
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

# أمر البدء (/start) وعرض الأزرار الأربعة للغات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇸🇾 العربية", callback_data="lang_ar"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ]
    await update.message.reply_text(
        "Please select your language / اختر لغتك:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# معالجة الضغط على أزرار الأوامر واللغات
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # 1. حفظ لغة المستخدم
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        context.user_data['lang'] = lang
        
        # التحقق من الاشتراك مباشرة بعد اختيار اللغة
        if await is_subscribed(user_id, context):
            await query.edit_message_text(TEXTS[lang]['send_link'])
        else:
            keyboard = [
                [InlineKeyboardButton(TEXTS[lang]['channel_btn'], url=CHANNEL_URL)],
                [InlineKeyboardButton(TEXTS[lang]['check_sub'], callback_data="verify_sub")]
            ]
            await query.edit_message_text(
                TEXTS[lang]['sub_required'],
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    # 2. زر التحقق من الاشتراك (البصمة 🫆)
    elif data == "verify_sub":
        lang = context.user_data.get('lang', 'ar')
        if await is_subscribed(user_id, context):
            await query.edit_message_text(TEXTS[lang]['send_link'])
        else:
            await query.answer("❌ عذراً، لم تقم بالاشتراك في القناة بعد!", show_alert=True)

    # 3. اختيار الجودة أو الملف الصوتي
    elif data.startswith("dl_"):
        lang = context.user_data.get('lang', 'ar')
        parts = data.split("_")
        quality = parts[1]
        url = context.user_data.get('last_url')

        await query.edit_message_text(TEXTS[lang]['downloading'])
        await process_download(query.message, context, url, quality, lang)

# استقبال رسائل الروابط من المستخدم
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'ar')

    # التأكد من الاشتراك قبل قبول أي رابط
    if not await is_subscribed(user_id, context):
        keyboard = [
            [InlineKeyboardButton(TEXTS[lang]['channel_btn'], url=CHANNEL_URL)],
            [InlineKeyboardButton(TEXTS[lang]['check_sub'], callback_data="verify_sub")]
        ]
        await update.message.reply_text(
            TEXTS[lang]['sub_required'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    url = update.message.text
    context.user_data['last_url'] = url

    # إظهار أزرار الجودات وزر الصوت (MP3)
    keyboard = [
        [
            InlineKeyboardButton("🎬 1080p", callback_data="dl_1080"),
            InlineKeyboardButton("🎬 720p", callback_data="dl_720"),
            InlineKeyboardButton("🎬 480p", callback_data="dl_480")
        ],
        [InlineKeyboardButton("🎵 MP3 (Audio Only)", callback_data="dl_audio")]
    ]
    await update.message.reply_text(
        TEXTS[lang]['choose_quality'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# دالة معالجة التحميل عبر yt-dlp وإرسال النتيجة مع الأزرار المطلوبة
async def process_download(message, context, url, quality, lang):
    os.makedirs('downloads', exist_ok=True)
    output_template = 'downloads/%(id)s.%(ext)s'
    
    if quality == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
            'outtmpl': output_template,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if quality == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        await message.edit_text(TEXTS[lang]['uploading'])

        # الأزرار أسفل الفيديو (القناة + البوت)
        bottom_keyboard = [
            [
                InlineKeyboardButton(TEXTS[lang]['channel_btn'], url=CHANNEL_URL),
                InlineKeyboardButton(TEXTS[lang]['bot_btn'], url=BOT_URL)
            ]
        ]

        with open(filename, 'rb') as file:
            caption_text = f"🎥 **{info.get('title', 'Media')}**\n🔗 Bot: @Ussame_bot"
            if quality == "audio":
                await message.reply_audio(audio=file, caption=caption_text, reply_markup=InlineKeyboardMarkup(bottom_keyboard))
            else:
                await message.reply_video(video=file, caption=caption_text, reply_markup=InlineKeyboardMarkup(bottom_keyboard))

        # تنظيف الملفات المؤقتة
        if os.path.exists(filename):
            os.remove(filename)
        await message.delete()

    except Exception as e:
        await message.edit_text(TEXTS[lang]['error'])

# التشغيل الأساسي للبوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot @Ussame_bot is up and running successfully!")
    app.run_polling()
