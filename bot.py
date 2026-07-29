import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8629100412:AAGuY2wf13Mr7R3gsMxAon1bYrTELnsu94U"
CHANNEL_URL = "https://t.me/wanasatt"
CHANNEL_USERNAME = "@wanasatt"  # معرف قناتك بدون رابط للاستعلام عنها برمجياً

# --- دالة التحقق من اشتراك المستخدم في القناة ---
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # الحالات التي تعني أن المستخدم مشترك
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
    return False

# --- أمر البداية /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # فحص الاشتراك عند الضغط على /start
    is_subscribed = await check_subscription(user_id, context)
    
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 انضم للقناة الرسمية", url=CHANNEL_URL)],
            [InlineKeyboardButton("🫆 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ **عذراً، يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه!**\n\n"
            "1️⃣ انضم للقناة من الزر أدناه.\n"
            "2️⃣ اضغط على زر **(تحقق من الاشتراك)** لفتح البوت.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    # إذا كان مشتركاً بالفعل
    keyboard = [[InlineKeyboardButton("✨ انضم لقناتنا الرسمية", url=CHANNEL_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "👋 **أهلاً بك في بوت التحميل السريع!**\n\n"
        "🚀 **المميزات:**\n"
        "├ 📥 دعم التحميل من معظم المنصات\n"
        "├ 🎯 اختيار الجودة المناسبة\n"
        "└ ⚡ سريع ويعمل على مدار الساعة\n\n"
        "🔗 **أرسل رابط الفيديو الآن للبدء...**"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# --- معالجة الرابط المرسل ---
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق من الاشتراك الإجباري قبل قبول الرابط
    is_subscribed = await check_subscription(user_id, context)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 انضم للقناة الرسمية", url=CHANNEL_URL)],
            [InlineKeyboardButton("🫆 تحقق من الاشتراك", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ **يجب عليك الاشتراك في القناة أولاً لتتمكن من إرسال الروابط والتحميل!**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("⚠️ **عذراً، يرجى إرسال رابط صحيح (يبدأ بـ http أو https).**", parse_mode="Markdown")
        return

    msg = await update.message.reply_text("⚡ **جاري فحص الرابط واستخراج الجودات...**", parse_mode="Markdown")

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, lambda: fetch_video_info(url))
    except Exception as e:
        await msg.edit_text("❌ **تعذر جلب معلومات الفيديو.** تأكد من صحة الرابط أو حاول مجدداً.", parse_mode="Markdown")
        return

    video_id = info.get('id', 'video')
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
                icon = "🔥" if height >= 720 else "📲"
                keyboard.append([
                    InlineKeyboardButton(f"{icon} جودة {height}p", callback_data=f"dl|{video_id}|{format_id}")
                ])
                if len(keyboard) >= 4:
                    break

    if not keyboard:
        keyboard.append([InlineKeyboardButton("✨ أفضل جودة متاحة", callback_data=f"dl|{video_id}|best")])

    keyboard.append([InlineKeyboardButton("📢 قناة البوت الرسمية", url=CHANNEL_URL)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption_text = f"🎬 **{info.get('title', 'عنوان الفيديو')}**\n\n👇 **اختر الجودة المطلوبة للتحميل:**"
    await msg.edit_text(caption_text, reply_markup=reply_markup, parse_mode="Markdown")

def fetch_video_info(url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

# --- معالجة الأزرار (التحقق والتحميل) ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("|")
    
    # 1. إذا ضغط على زر التحقق من الاشتراك
    if data[0] == "check_sub":
        await query.answer()
        is_subscribed = await check_subscription(user_id, context)
        
        if is_subscribed:
            await query.edit_message_text(
                "✅ **تم التحقق بنجاح!**\n\n"
                "🎉 أهلاً بك، يمكنك الآن إرسال أي رابط وسأقوم بتحميله لك فوراً.",
                parse_mode="Markdown"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📢 انضم للقناة الرسمية", url=CHANNEL_URL)],
                [InlineKeyboardButton("🫆 تحقق من الاشتراك", callback_data="check_sub")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.answer("❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)
        return

    # 2. إذا ضغط على أزرار التحميل
    if data[0] != "dl":
        return

    await query.answer()
    
    # فحص الاشتراك مجددًا كحماية إضافية أثناء التحميل
    if not await check_subscription(user_id, context):
        await query.edit_message_text("⚠️ **عذراً، لقد قمت إلغاء الاشتراك في القناة! يرجى إعادة الاشتراك للاستمرار.**", parse_mode="Markdown")
        return

    video_id = data[1]
    format_id = data[2]
    
    video_data = context.user_data.get(video_id)
    if not video_data:
        await query.edit_message_text("⚠️ **انتهت صلاحية الجلسة، يرجى إرسال الرابط مجدداً.**", parse_mode="Markdown")
        return

    url = video_data['url']
    await query.edit_message_text("⏳ **جاري التحميل والمعالجة... يرجى الانتظار لحظات.** 🚀", parse_mode="Markdown")

    loop = asyncio.get_running_loop()
    filename = f"{video_id}.mp4"
    
    try:
        await loop.run_in_executor(None, lambda: download_video(url, format_id, filename))
        
        keyboard = [[InlineKeyboardButton("📢 انضم لقناتنا", url=CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("📤 **جاري رفع الفيديو إلى تليجرام...**", parse_mode="Markdown")

        with open(filename, 'rb') as video_file:
            await query.message.reply_video(
                video=video_file,
                caption=f"✅ **تم التحميل بنجاح!**\n\n📌 **{video_data['title']}**\n\n💎 **قناتنا:** {CHANNEL_URL}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        await query.delete_message()

    except Exception:
        await query.message.reply_text("❌ **حدث خطأ أثناء تحميل الملف** (قد يكون الحجم كبيراً جداً بالنسبة لتليجرام).")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def download_video(url, format_id, output_filename):
    ydl_opts = {
        'format': format_id if format_id != 'best' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'max_filesize': 50 * 1024 * 1024,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("⚡ البوت يعمل بنجاح مع نظام الاشتراك الإجباري وبصمة النيون...")
    app.run_polling()

if __name__ == '__main__':
    main()
