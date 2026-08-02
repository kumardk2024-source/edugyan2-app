import json
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import database

# Environment Variables लोड करें
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_BASE_URL")

# डेटाबेस शुरू करें
database.init_db()

# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # चेक करें कि यूजर रजिस्टर्ड है या नहीं
    if not database.is_user_registered(user_id):
        # Registration WebApp Button
        reg_url = f"{WEB_APP_URL}/index.html"
        keyboard = [
            [KeyboardButton(text="📝 Complete Registration", web_app=WebAppInfo(url=reg_url))]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "👋 *Kumardk's Quiz Bot में आपका स्वागत है!*\n\nआगे बढ़ने के लिए कृपया अपना रजिस्ट्रेशन पूरा करें।",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await show_main_menu(update, context)

# Main Menu Display
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🤖 AI Quiz (Gemini)", callback_data="quiz_ai")],
        [InlineKeyboardButton("📚 NCERT Quiz (Class 6-12)", callback_data="quiz_ncert")],
        [InlineKeyboardButton("✍️ Create Your Own Quiz", web_app=WebAppInfo(url=f"{WEB_APP_URL}/create_quiz.html"))],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"), InlineKeyboardButton("📊 My History", callback_data="history")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🎯 *Main Menu*\n\nआप कौन सा क्विज़ शुरू करना चाहते हैं?"
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# Web App से आया रजिस्ट्रेशन डेटा हैंडओवर करें
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    raw_data = update.message.web_app_data.data
    
    try:
        data = json.loads(raw_data)
        if data.get("type") == "registration":
            database.register_user(user_id, data)
            await update.message.reply_text(
                "✅ *रजिस्ट्रेशन सफलतापूर्वक पूरा हो गया!*",
                parse_mode="Markdown"
            )
            await show_main_menu(update, context)
    except Exception as e:
        await update.message.reply_text(f"⚠️ डेटा प्रोसेसिंग में त्रुटि: {str(e)}")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN .env फाइल में नहीं मिला!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers Registration
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    print("🚀 Kumardk's Quiz Bot सफलतापूर्वक चालू हो गया है...")
    app.run_polling()

if __name__ == "__main__":
    main()