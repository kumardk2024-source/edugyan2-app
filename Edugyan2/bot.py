import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- अपनी असली की यहाँ डालें (GitHub पर इसे कभी पुश न करें) ---
TOKEN = "****************"          # अपना टेलीग्राम बॉट टोकन यहाँ लिखें
GEMINI_API_KEY = "****************" # अपनी असली Gemini API Key यहाँ लिखें

# Gemini AI सेट अप
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}
model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

# लॉगिंग सेट अप
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# /start कमांड का फंक्शन
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # आपके GitHub Pages का लाइव लिंक
    webapp_url = "https://kumardk2024-source.github.io/edugyan2-app/form.html"
    
    keyboard = [
        [InlineKeyboardButton("📝 Open Registration Form", web_app=WebAppInfo(url=webapp_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"नमस्ते {user.first_name}!\n\n"
        "Edugyan2 क्विज़ बॉट में आपका स्वागत है। रजिस्ट्रेशन करने के लिए नीचे दिए गए बटन पर क्लिक करें:",
        reply_markup=reply_markup
    )

# जब यूजर वेब ऐप से फॉर्म सबमिट करेगा
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data_json = update.message.web_app_data.data
        user_data = json.loads(data_json)
        
        fullname = user_data.get('fullname')
        mobile = user_data.get('mobile')
        district = user_data.get('district')
        state = user_data.get('state')
        country = user_data.get('country', 'India')
        
        # यूजर को सफलता का संदेश भेजें
        await update.message.reply_text(
            f"🎉 **रजिस्ट्रेशन सफलतापूर्वक पूरा हो गया है!**\n\n"
            f"👤 **नाम:** {fullname}\n"
            f"📱 **मोबाइल:** {mobile}\n"
            f"📍 **जिला:** {district}\n"
            f"🇮🇳 **राज्य:** {state} ({country})\n\n"
            f"अब आप अपनी तैयारी और क्विज़ का आनंद ले सकते हैं!"
        )
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")
        await update.message.reply_text("⚠️ डेटा प्रोसेस करने में कुछ त्रुटि हुई। कृपया दोबारा प्रयास करें।")

def main():
    # बॉट एप्लीकेशन बनाएं
    app = Application.builder().token(TOKEN).build()

    # कमांड और डेटा हैंडलर जोड़ें
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    print("Kumardk's Quiz Bot is running successfully...")
    
    # बॉट को शुरू करें
    app.run_polling()

if __name__ == "__main__":
    main()