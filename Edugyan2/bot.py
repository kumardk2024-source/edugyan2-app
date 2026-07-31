import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ==========================================
# 🔑 सुरक्षा के लिए यहाँ अपनी असली की (Keys) दर्ज करें
# ==========================================
TOKEN = "*********************************"      # यहाँ अपना असली टेलीग्राम बॉट टोकन डालें
GEMINI_API_KEY = "YOUR_API_KEY_HERE" # यहाँ अपनी असली Gemini API Key डालें

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

# 1️⃣ /start कमांड: यूज़र के लिए रजिस्ट्रेशन और एंटी-बॉट वेरिफिकेशन पेज खोलना (index.html)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # आपके GitHub Pages का होम/रजिस्ट्रेशन पेज लिंक (index.html)
    index_url = "https://kumardk2024-source.github.io/edugyan2-app/form.html"
    
    keyboard = [
        [InlineKeyboardButton("📝 Register & Verify (Anti-Robot)", web_app=WebAppInfo(url=index_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"नमस्ते {user.first_name}!\n\n"
        "Edugyan2 क्विज़ बॉट में आपका स्वागत है।\n"
        "आगे बढ़ने और यह सुनिश्चित करने के लिए कि आप रोबोट नहीं हैं, कृपया नीचे दिए गए बटन पर क्लिक करके अपना रजिस्ट्रेशन पूरा करें:",
        reply_markup=reply_markup
    )

# 2️⃣ रजिस्ट्रेशन के बाद मेनू दिखाना (AI Quiz, NCERT Quiz, Create Question)
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🤖 AI Quiz", callback_data="menu_ai_quiz")],
        [InlineKeyboardButton("📚 NCERT Quiz (Class 6th to 12th)", callback_data="menu_ncert_quiz")],
        [InlineKeyboardButton("✍️ Create Your Own Quiz / Question", callback_data="menu_create_quiz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🎉 **रजिस्ट्रेशन सफलतापूर्वक पूरा हो गया है!**\n\nअब आप अपनी पसंद का विकल्प चुनें:"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# 3️⃣ वेबसाइट/मिनी ऐप से डेटा आने पर हैंडल करना और शेयर/स्टार्ट विकल्प देना
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data_json = update.message.web_app_data.data
        user_data = json.loads(data_json)
        
        # चेक करें कि क्या यह क्विज़ का सवाल है या सिर्फ रजिस्ट्रेशन डेटा
        question = user_data.get('question')
        
        if not question:
            # अगर यह सिर्फ रजिस्ट्रेशन/होम फॉर्म का डेटा था, तो सीधे मेनू दिखाओ
            await show_main_menu(update, context)
            return

        options = user_data.get('options', [])
        options_text = "\n".join([f"• {opt}" for opt in options]) if options else "कोई विकल्प नहीं"
        
        share_text = f"🎯 नया क्विज़ आया है!\n\n❓ सवाल: {question}\n{options_text}"
        
        # आपके प्लान के अनुसार सभी एक्शन बटन
        keyboard = [
            [InlineKeyboardButton("🚀 Let's Start", callback_data="lets_start_quiz")],
            [InlineKeyboardButton("▶️ Start Quiz", callback_data="start_quiz")],
            [InlineKeyboardButton("📤 Share Quiz in Group", switch_inline_query=share_text)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # क्रिएटर को सफलता का मैसेज
        await update.message.reply_text(
            f"🎉 **बधाई हो! आपका क्विज़ सफलतापूर्वक बन गया है!** ✅\n\n"
            f"❓ **सवाल:** {question}\n\n"
            f"📋 **विकल्प (Options):**\n{options_text}\n\n"
            f"अब आप नीचे दिए गए विकल्पों में से चुन सकते हैं:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error handling web app data: {e}")
        # अगर कोई गड़बड़ी हो, तो सेफ साइड के लिए मेनू दिखा दें
        await show_main_menu(update, context)

# 4️⃣ बटन क्लिक्स को मैनेज करना (जहाँ से Create Question के लिए form.html खुलेगा)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_ai_quiz":
        await query.message.reply_text("🤖 AI Quiz मोड जल्द शुरू हो रहा है! अपना टॉपिक भेजें:")
    elif query.data == "menu_ncert_quiz":
        await query.message.reply_text("📚 NCERT Quiz (Class 6th to 12th) चुनें:\nकृपया अपनी कक्षा (Class) चुनें या विषय भेजें।")
    elif query.data == "menu_create_quiz":
        # यहाँ पर आपके क्वेश्चन क्रिएशन वाले फॉर्म का लिंक (form.html) जोड़ा गया है
        form_url = "https://kumardk2024-source.github.io/edugyan2-app/index.html"
        keyboard = [[InlineKeyboardButton("✍️ Open Quiz Creator Form", web_app=WebAppInfo(url=form_url))]]
        await query.message.reply_text("अपना नया सवाल और विकल्प दर्ज करने के लिए नीचे दिए गए बटन पर क्लिक करें:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data in ["lets_start_quiz", "start_quiz"]:
        await query.message.reply_text("🎯 क्विज़ शुरू हो चुका है! तैयार हो जाइए...")

def main():
    app = Application.builder().token(TOKEN).build()

    # कमांड, वेब ऐप डेटा और बटन क्लिक्स के लिए हैंडलर्स
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Kumardk's Quiz Bot is running successfully with complete links...")
    app.run_polling()

if __name__ == "__main__":
    main()