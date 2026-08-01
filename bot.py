import os
import re
import logging
import asyncio
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import yt_dlp

# --- سيرفر وهمي لمنع Render من إغلاق الـ Web Service ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# تشغيل خادم الويب في الخلفية
Thread(target=run_web_server, daemon=True).start()

# --- إعدادات تسجيل الأخطاء ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# البيانات الخاصة بك
API_ID = int(os.getenv("API_ID", "32636127"))
API_HASH = os.getenv("API_HASH", "fc5ce2f719114cb68ccdc24a564e15e0")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8629100412:AAF1Nt7eBMTucCNtEwfd63NRKK3cX2i64UE")
MUST_JOIN_CHANNEL = os.getenv("CHANNEL_USERNAME", "wanasatt")

bot = Client("MediaDownloaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_LANG = {}
TEMP_DATA = {}
COOKIE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

TEXTS = {
    "ar": {
        "flag": "🇸🇾", "name": "العربية",
        "welcome": "✨ **أهلاً بك في بوت تحميل الوسائط الشامل الاحترافي!**\n\n⚡ **الميزات المتاحة:**\n• تحميل الفيديو من يوتيوب، تيك توك، إنستغرام، فيسبوك، وتويتر.\n• جودات عالية ومتعددة مع دعم تحويل الصوت MP3.\n• دعم 10 لغات مختلفة لسهولة الاستخدام.\n\n📌 **أرسل رابط الفيديو الآن للبدء!**",
        "sub_required": "⚠️ **عذراً عزيزي، للاستفادة من خدمات البوت يرجى الاشتراك بقناتنا أولاً:**\n\n📢 @{channel}\n\n👇 **بعد الانضمام، اضغط على زر تأكيد الاشتراك:**",
        "sub_btn": "📢 انضمام للقناة", "verify_btn": "✅ تأكيد الاشتراك",
        "sub_success": "🎉 شكراً لاشتراكك! يمكنك الآن إرسال الرابط للتحميل.",
        "not_subbed": "❌ لم تقم بالاشتراك في القناة بعد! يرجى الانضمام أولاً.",
        "lang_select": "🌐 **اختر لغة الواجهة المناسبة لك / Select Language:**",
        "processing": "🔍 **جاري فحص الرابط واستخراج خيارات التحميل...**",
        "choose_format": "🎬 **معلومات الفيديو:**\n\n📌 **العنوان:** `{title}`\n⏱ **المدة:** `{duration}` ثانية\n\n👇 **اختر جودة أو صيغة التحميل المطلوبة:**",
        "downloading": "📥 **جاري تنزيل الملف وتحضيره للإرسال... قد يستغرق ذلك ثوانٍ قليلة.**",
        "error": "❌ **حدث خطأ أثناء معالجة الطلب:**\n`{error}`",
        "btn_best": "🌟 أفضل جودة متاحة",
        "btn_720": "🎥 فيديو 720p (HD)",
        "btn_480": "🎬 فيديو 480p (SD)",
        "btn_audio": "🎵 ملف صوتي MP3",
        "btn_lang": "🌐 تغيير اللغة",
        "btn_channel": "📢 القناة الرسمية",
        "btn_help": "ℹ️ تعليمات البوت",
        "help_msg": "🛠 **طريقة الاستخدام:**\n1. أرسل أي رابط من يوتيوب، تيك توك، أو إنستغرام.\n2. اختر الجودة أو الصيغة المناسبة لك من الأزرار.\n3. سيتم تنزيل وسحب الملف وإرساله لك مباشرة!"
    },
    "en": {
        "flag": "🇬🇧", "name": "English",
        "welcome": "✨ **Welcome to the Professional All-in-One Downloader Bot!**\n\n⚡ **Features:**\n• Download from YouTube, TikTok, Instagram, Facebook & Twitter.\n• High-quality videos and MP3 audio extraction.\n• Multi-language support (10 languages).\n\n📌 **Send a video link now to begin!**",
        "sub_required": "⚠️ **Please subscribe to our channel to use this bot:**\n\n📢 @{channel}",
        "sub_btn": "📢 Join Channel", "verify_btn": "✅ Verify Subscription",
        "sub_success": "🎉 Thank you for subscribing! Send any link to download.",
        "not_subbed": "❌ You are not subscribed yet!",
        "lang_select": "🌐 **Select your preferred language:**",
        "processing": "🔍 **Processing link and extracting formats...**",
        "choose_format": "🎬 **Video Details:**\n\n📌 **Title:** `{title}`\n⏱ **Duration:** `{duration}`s\n\n👇 **Choose format:**",
        "downloading": "📥 **Downloading and preparing file...**",
        "error": "❌ **An error occurred:**\n`{error}`",
        "btn_best": "🌟 Best Available",
        "btn_720": "🎥 Video 720p (HD)",
        "btn_480": "🎬 Video 480p (SD)",
        "btn_audio": "🎵 Audio MP3",
        "btn_lang": "🌐 Change Language",
        "btn_channel": "📢 Channel",
        "btn_help": "ℹ️ Help",
        "help_msg": "🛠 **How to use:**\n1. Send any valid link.\n2. Choose your preferred quality or MP3 format.\n3. The bot will download and send it to you."
    }
}

def get_text(user_id, key):
    lang = USER_LANG.get(user_id, "ar")
    return TEXTS.get(lang, TEXTS["ar"]).get(key, "")

def build_main_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text(user_id, "btn_lang"), callback_data="change_lang"),
            InlineKeyboardButton(get_text(user_id, "btn_help"), callback_data="show_help")
        ],
        [
            InlineKeyboardButton(get_text(user_id, "btn_channel"), url=f"https://t.me/{MUST_JOIN_CHANNEL}")
        ]
    ])

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

async def check_subscription(client: Client, user_id: int):
    if not MUST_JOIN_CHANNEL:
        return True
    try:
        member = await client.get_chat_member(f"@{MUST_JOIN_CHANNEL}", user_id)
        return member.status in ["owner", "administrator", "member"]
    except Exception:
        return True

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if not await check_subscription(client, user_id):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user_id, "sub_btn"), url=f"https://t.me/{MUST_JOIN_CHANNEL}")],
            [InlineKeyboardButton(get_text(user_id, "verify_btn"), callback_data="check_sub")]
        ])
        await message.reply_text(get_text(user_id, "sub_required").format(channel=MUST_JOIN_CHANNEL), reply_markup=kb)
        return

    await message.reply_text(get_text(user_id, "welcome"), reply_markup=build_main_keyboard(user_id))

@bot.on_callback_query(filters.regex("^change_lang$"))
async def change_lang_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(get_text(user_id, "lang_select"), reply_markup=build_lang_keyboard())

@bot.on_callback_query(filters.regex("^setlang_"))
async def set_lang_cb(client: Client, callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id
    USER_LANG[user_id] = lang_code
    await callback.answer("✅ Updated")
    await callback.message.edit_text(get_text(user_id, "welcome"), reply_markup=build_main_keyboard(user_id))

@bot.on_callback_query(filters.regex("^show_help$"))
async def show_help_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer(get_text(user_id, "help_msg"), show_alert=True)

@bot.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_cb(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(client, user_id):
        await callback.answer(get_text(user_id, "sub_success"), show_alert=True)
        await callback.message.delete()
        await start_cmd(client, callback.message)
    else:
        await callback.answer(get_text(user_id, "not_subbed"), show_alert=True)

@bot.on_message(filters.private & filters.text & ~filters.command(["start"]))
async def handle_url(client: Client, message: Message):
    user_id = message.from_user.id
    if not await check_subscription(client, user_id):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user_id, "sub_btn"), url=f"https://t.me/{MUST_JOIN_CHANNEL}")],
            [InlineKeyboardButton(get_text(user_id, "verify_btn"), callback_data="check_sub")]
        ])
        await message.reply_text(get_text(user_id, "sub_required").format(channel=MUST_JOIN_CHANNEL), reply_markup=kb)
        return

    url = message.text.strip()
    if not re.match(r'https?://[^\s]+', url):
        return

    msg = await message.reply_text(get_text(user_id, "processing"))

    ydl_opts = {'quiet': True, 'nocheckcertificate': True}
    if os.path.exists(COOKIE_PATH):
        ydl_opts['cookiefile'] = COOKIE_PATH

    loop = asyncio.get_running_loop()
    try:
        def fetch_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, fetch_info)
        title = info.get('title', 'Video')
        duration = info.get('duration', 0)

        TEMP_DATA[user_id] = url

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user_id, "btn_best"), callback_data="dl_best")],
            [
                InlineKeyboardButton(get_text(user_id, "btn_720"), callback_data="dl_720"),
                InlineKeyboardButton(get_text(user_id, "btn_480"), callback_data="dl_480")
            ],
            [InlineKeyboardButton(get_text(user_id, "btn_audio"), callback_data="dl_audio")]
        ])

        await msg.edit_text(
            get_text(user_id, "choose_format").format(title=title, duration=duration),
            reply_markup=kb
        )

    except Exception as e:
        logging.error(f"Fetch Error: {e}")
        await msg.edit_text(get_text(user_id, "error").format(error=str(e)[:120]))

@bot.on_callback_query(filters.regex("^dl_"))
async def process_dl(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    url = TEMP_DATA.get(user_id)

    if not url:
        await callback.answer("⚠️ Session expired, please resend the link.", show_alert=True)
        return

    fmt = callback.data.split("_")[1]
    await callback.message.edit_text(get_text(user_id, "downloading"))

    out_file = f"down_{user_id}_{callback.id}"
    
    ydl_opts = {
        'outtmpl': f'{out_file}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    if os.path.exists(COOKIE_PATH):
        ydl_opts['cookiefile'] = COOKIE_PATH

    if fmt == "audio":
        ydl_opts['format'] = 'bestaudio/best'
    elif fmt == "720":
        ydl_opts['format'] = 'b[height<=720][ext=mp4]/best[height<=720]/best'
    elif fmt == "480":
        ydl_opts['format'] = 'b[height<=480][ext=mp4]/best[height<=480]/best'
    else:
        ydl_opts['format'] = 'b[ext=mp4]/best'

    loop = asyncio.get_running_loop()

    try:
        def do_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        info = await loop.run_in_executor(None, do_download)
        
        file_path = None
        for file in os.listdir("."):
            if file.startswith(out_file):
                file_path = file
                break

        if not file_path or not os.path.exists(file_path):
            raise Exception("File creation failed.")

        title = info.get('title', 'Downloaded Media')

        if fmt == "audio":
            await client.send_audio(chat_id=callback.message.chat.id, audio=file_path, caption=title)
        else:
            await client.send_video(chat_id=callback.message.chat.id, video=file_path, caption=title)

        await callback.message.delete()

    except Exception as e:
        logging.error(f"DL Error: {e}")
        await callback.message.edit_text(get_text(user_id, "error").format(error=str(e)[:150]))

    finally:
        for file in os.listdir("."):
            if file.startswith(out_file):
                try:
                    os.remove(file)
                except Exception:
                    pass

async def main():
    await bot.start()
    logging.info("Bot started successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
