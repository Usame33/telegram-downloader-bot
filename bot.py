import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# إعداد السجلات بشكل أنيق
logging.basicConfig(format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.INFO)

TOKEN = "8629100412:AAGuY2wf13Mr7R3gsMxAon1bYrTELnsu94U"
CHANNEL_URL = "https://t.me/wanasatt"
CHANNEL_USERNAME = "@wanasatt"  # معرف قناتك للاستعلام عن الاشتراك

# --- دالة فحص الاشتراك الإجباري ---
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Subscription Check Error: {e}")
    return False

# --- أمر البداية /start بتصميم عصري ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في قناة البوت الرسمية", url=CHANNEL_URL)],
            [InlineKeyboardButton("🫆 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✨ **أهلاً بك يا {user_name} في عالم التحميل الذكي!**\n\n"
            "🔒 **عذراً، البوت محمي بنظام الاشتراك الإجباري.**\n"
            "للاستفادة من مميزات التحميل السريع، يرجى:\n"
            "1️⃣ الانضمام للقناة عبر الزر أدناه.\n"
            "2️⃣ الضغط على زر التحقق `🫆` أدناه.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton("💎 قناة البوت الرسمية", url=CHANNEL_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"⚡ **مرحباً بك مجدداً، {user_name}!**\n\n"
        "╭───────────────╮\n"
        "  🚀 **مركز تحميل الوسائط المتطور**\n"
        "╰───────────────╯\n\n"
        "📌 **ما يمكنني فعله لأجلك:**\n"
        "├ 📥 التحميل من (TikTok, Instagram, YouTube...)\n"
        "├ 🎬 اختيار الجودة المناسبة بدقة عالية\n"
        "└ ⏱️ معالجة فورية تعمل على مدار الساعة 24/7\n\n"
        "👇 **أرسل رابط الفيديو الآن لتبدأ العملية!**"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# --- معالجة الرابط المرسل واستخراج الجودات ---
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # فحص الاشتراك الإجباري
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في قناة البوت الرسمية", url=CHANNEL_URL)],
            [InlineKeyboardButton("🫆 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ **عذراً، لا يمكنك إرسال روابط قبل إتمام الاشتراك في القناة!**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("⚠️ **الرابط غير صالح!** يرجى التأكد من إرسال رابط يبدأ بـ `http` أو `https`.", parse_mode="Markdown")
        return

    msg = await update.message.reply_text("🔍 **جاري تحليل الرابط وتجاوز حماية المنصة...** ⏳", parse_mode="Markdown")

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, lambda: fetch_video_info(url))
    except Exception as e:
        await msg.edit_text("❌ **عذراً، تعذر جلب معلومات الفيديو.** تأكد من صحة الرابط أو جرب منصة أخرى.", parse_mode="Markdown")
        return

    video_id = info.get('id', 'video_id')
    context.user_data[video_id] = {
        'url': url,
        'title': info.get('title', 'فيديو بدون عنوان')
    }

    keyboard = []
    formats = info.get('formats', [])
    
    seen_qualities = set()
    for f in formats:
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
            height = f.get('height')
            format_id = f.get('format_id')
            if height and height not in seen_qualities:
                seen_qualities.add(height)
                # أيقونات عصرية حسب جودة الفيديو
                icon = "🔥" if height >= 720 else "📱"
                keyboard.append([
                    InlineKeyboardButton(f"{icon} جودة العرض {height}p", callback_data=f"dl|{video_id}|{format_id}")
                ])
                if len(keyboard) >= 4:
                    break

    if not keyboard:
        keyboard.append([InlineKeyboardButton("✨ تحميل بأفضل جودة متوفرة", callback_data=f"dl|{video_id}|best")])

    keyboard.append([InlineKeyboardButton("💎 قناة البوت الرسمية", url=CHANNEL_URL)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # تنظيف العنوان لكي لا يكسر تنسيق الماركداون
    clean_title = info.get('title', 'فيديو بدون عنوان').replace('_', ' ').replace('*', ' ')
    if len(clean_title) > 60:
        clean_title = clean_title[:60] + "..."

    caption_text = (
        "╭───────────────╮\n"
        f"  🎬 **{clean_title}**\n"
        "╰───────────────╯\n\n"
        "👇 **اختر الجودة المطلوبة للبدء بالتحميل الفوري:**"
    )
    await msg.edit_text(caption_text, reply_markup=reply_markup, parse_mode="Markdown")

def fetch_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- معالجة الضغط على الأزرار ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("|")
    
    # زر التحقق من الاشتراك
    if data[0] == "check_sub":
        await query.answer()
        is_subscribed = await check_subscription(user_id, context)
        
        if is_subscribed:
            await query.edit_message_text(
                "✅ **تم التحقق بنجاح وتفعيل حسابك!**\n\n"
                "🎉 أهلاً بك في البوت، يمكنك الآن إرسال أي رابط وسأقوم بتحليله وتحميله فوراً.",
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ لم تقم بالاشتراك في القناة حتى الآن!", show_alert=True)
        return

    if data[0] != "dl":
        return

    await query.answer()
    
    # فحص أمني إضافي أثناء التحميل
    if not await check_subscription(user_id, context):
        await query.edit_message_text("⚠️ **عذراً، لقد قمت بإلغاء الاشتراك من القناة! يرجى إعادة الاشتراك للاستمرار.**", parse_mode="Markdown")
        return

    video_id = data[1]
    format_id = data[2]
    
    video_data = context.user_data.get(video_id)
    if not video_data:
        await query.edit_message_text("⚠️ **عذراً، انتهت صلاحية الجلسة. أرسل الرابط مجدداً من فضلك.**", parse_mode="Markdown")
        return

    url = video_data['url']
    await query.edit_message_text("🚀 **جاري سحب الملف ومعالجته بأقصى سرعة...** ⏳", parse_mode="Markdown")

    loop = asyncio.get_running_loop()
    filename = f"{video_id}.mp4"
    
    try:
        await loop.run_in_executor(None, lambda: download_video(url, format_id, filename))
        
        keyboard = [[InlineKeyboardButton("💎 تابعنا على القناة", url=CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("📤 **جاري رفع الفيديو وإرساله إليك...** 📡", parse_mode="Markdown")

        with open(filename, 'rb') as video_file:
            await query.message.reply_video(
                video=video_file,
                caption=f"✅ **تم التحميل بنجاح!**\n\n📌 **{video_data['title']}**\n\n🔗 **قناتنا الرسمية:** {CHANNEL_URL}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        await query.delete_message()

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await query.message.reply_text("❌ **فشل التحميل!** قد يكون حجم الفيديو أكبر من مسموحات تليجرام أو أن الرابط غير مدعوم حالياً.")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def download_video(url, format_id, output_filename):
    ydl_opts = {
        'format': format_id if format_id != 'best' else 'best/bestvideo+bestaudio',
        'outtmpl': output_filename,
        'max_filesize': 50 * 1024 * 1024,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("⚡ البوت المطور يعمل الآن بكفاءة وبأعلى معايير الأمان والتصميم...")
    app.run_polling()

if __name__ == '__main__':
    main()
