import json
import os
import asyncio
import io
from google import genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove, WebAppInfo, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    PollAnswerHandler,
    filters,
)

# database.py से सभी जरूरी फंक्शन्स इंपोर्ट किए गए हैं
from database import init_db, check_user_exists, register_user_details, save_question, get_user_quiz, NCERT_DATABASE, get_random_ncert_questions

init_db()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "*************************************")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "*************************************")

client = genai.Client(api_key=GEMINI_API_KEY)

WEB_APP_URL = "https://kumardk2024-source.github.io/edugyan2-app/form.html"
QUIZ_WEB_APP = "https://kumardk2024-source.github.io/edugyan2-app/index.html"

SUBJECT, NUM_QUESTIONS = range(2)
NCERT_SUBJECT, NCERT_NUM_Q, NCERT_TIME = range(20, 23)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_record = check_user_exists(user.id)
    
    if not user_record or user_record[1] == 0:
        caption = (
            f"<b>Namaste, {user.first_name}! 🙏</b>\n\n"
            "Aapka swagat hai **EDUGYAN2 SYSTEM QUIZ BOT** mein.\n"
            "Bot का उपयोग करने के लिए कृपया नीचे दिए गए बटन पर क्लिक करके अपना **Verification Form** (नाम, मोबाइल, जिला, राज्य) भरें:"
        )
        keyboard = [[InlineKeyboardButton("📝 Complete Verification", web_app=WebAppInfo(url=WEB_APP_URL))]]
        if update.message:
            await update.message.reply_text(caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.callback_query:
            await update.callback_query.message.reply_text(caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = (
        f"<b>Welcome back, {user.first_name}!</b>\n\n"
        "<b>EDUGYAN2 SYSTEM QUIZ BOT</b>\n"
        "Aap successfully verified hain. Ab aap quizzes create kar sakte hain ya practice shuru kar sakte hain!"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Add bot to group", url="https://t.me/edugyan2_bot?startgroup=true")],
        [InlineKeyboardButton("✨ Create a question (Popup Form)", web_app=WebAppInfo(url=QUIZ_WEB_APP))],
        [InlineKeyboardButton("🤖 AI / Massive Subject Quiz", callback_data="start_ai_quiz")],
        [InlineKeyboardButton("📚 NCERT Database Quiz", callback_data="start_db_quiz")],
        [InlineKeyboardButton("ℹ️ About This Bot", callback_data="about_bot")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(caption, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("Neeche diye gaye menu se option chunein:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(caption, parse_mode="HTML", reply_markup=reply_markup)

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data_str = update.effective_message.web_app_data.data
    user_id = update.effective_user.id
    
    try:
        data = json.loads(data_str)
        
        if "verified" in data and data["verified"]:
            name = data.get("fullname")
            mobile = data.get("mobile")
            district = data.get("district")
            state = data.get("state")
            country = data.get("country")
            
            register_user_details(user_id, name, mobile, district, state, country)
            
            await update.message.reply_text(
                f"🎉 **Verification Successful!**\n\n"
                f"👤 Name: {name}\n"
                f"📱 Mobile: {mobile}\n"
                f"📍 Location: {district}, {state} ({country})\n\n"
                f"✅ Aapka account successfully register ho gaya hai!"
            )
            await show_main_menu(update, context)
            return

        q_text = data.get("question")
        options = data.get("options")
        is_done = data.get("done", False)
        
        if not q_text or not options or len(options) < 2:
            return

        save_question(user_id, "My Custom Quiz", q_text, options, correct=0)
        all_questions = get_user_quiz(user_id)
        total_q = len(all_questions)
        
        if is_done or total_q >= 150:
            context.user_data['subject'] = "My Custom Quiz"
            context.user_data['quiz_questions'] = all_questions
            
            bot_username = (await context.bot.get_me()).username
            share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text=Maine%20ek%20naya%20quiz%20banaya%20hai!"
            group_url = f"https://t.me/{bot_username}?startgroup=quiz"
            
            keyboard = [
                [InlineKeyboardButton("🚀 Start Quiz (Self)", callback_data="start_interactive_quiz")],
                [InlineKeyboardButton("👥 Start Quiz in Group", url=group_url)],
                [InlineKeyboardButton("📢 Share Quiz with Friends", url=share_url)],
            ]
            await update.message.reply_text(
                f"🎉 **Quiz Successfully Completed!**\n\nTotal Questions Saved: {total_q}\nAb option chunein:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("✨ Add Another Question", web_app=WebAppInfo(url=QUIZ_WEB_APP))],
                [InlineKeyboardButton("✅ Finish Quiz", callback_data="finish_custom_quiz")]
            ]
            await update.message.reply_text(
                f"✅ **Question Successfully Saved!**\n📊 Total Questions in Quiz: **{total_q}**\n\nAgla question jodne ya khatam karne ke liye chunein:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Error: {e}")

async def finish_custom_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    questions = get_user_quiz(user_id)
    if not questions:
        await query.message.reply_text("❌ Aapne abhi tak koi question nahi joda hai.")
        return
        
    context.user_data['subject'] = "My Custom Quiz"
    context.user_data['quiz_questions'] = questions
    
    bot_username = (await context.bot.get_me()).username
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text=Maine%20ek%20naya%20quiz%20banaya%20hai!"
    group_url = f"https://t.me/{bot_username}?startgroup=quiz"
    
    keyboard = [
        [InlineKeyboardButton("🚀 Start Quiz (Self)", callback_data="start_interactive_quiz")],
        [InlineKeyboardButton("👥 Start Quiz in Group", url=group_url)],
        [InlineKeyboardButton("📢 Share Quiz with Friends", url=share_url)],
    ]
    await query.message.edit_text(
        f"🎉 **Quiz Completed!**\n\nTotal Questions: {len(questions)}\nAb option chunein:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def db_quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subjects_list = "\n".join([f"• {s}" for s in NCERT_DATABASE.keys()])
    await query.message.edit_text(
        "📚 **NCERT Database Quiz (Class 6-12)**\n\n"
        f"Available Subjects:\n{subjects_list}\n\n"
        "🎯 Kripya upar diye gaye subjects mein se kisi ek ka naam **type karein**:",
        parse_mode="Markdown"
    )
    return NCERT_SUBJECT

async def ncert_receive_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub_name = update.message.text.strip()
    found_sub = None
    for s in NCERT_DATABASE.keys():
        if sub_name.lower() in s.lower():
            found_sub = s
            break
    if not found_sub:
        await update.message.reply_text("❌ Yeh subject database mein nahi mila. Sahi naam likhein:")
        return NCERT_SUBJECT
    context.user_data['subject'] = found_sub
    await update.message.reply_text("📊 Aapko kitne prashno ka quiz chahiye? *(5 se 150 ke beech likhein)*:")
    return NCERT_NUM_Q

async def ncert_receive_num_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(update.message.text)
        if num < 5 or num > 150:
            await update.message.reply_text("⚠️ Kripya 5 se 150 ke beech sankhya likhein:")
            return NCERT_NUM_Q
        context.user_data['num_questions'] = num
    except ValueError:
        await update.message.reply_text("Valid number likhein:")
        return NCERT_NUM_Q
    
    keyboard = [
        [InlineKeyboardButton("15 Seconds", callback_data="ncert_time_15"), InlineKeyboardButton("30 Seconds", callback_data="ncert_time_30")],
        [InlineKeyboardButton("45 Seconds", callback_data="ncert_time_45"), InlineKeyboardButton("60 Seconds", callback_data="ncert_time_60")]
    ]
    await update.message.reply_text("⏱️ Har question ke liye kitna time set karna chahte hain?", reply_markup=InlineKeyboardMarkup(keyboard))
    return NCERT_TIME

async def ncert_receive_time_and_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time_limit = int(query.data.replace("ncert_time_", ""))
    context.user_data['time_limit'] = time_limit
    sub_name = context.user_data.get('subject')
    num_q = context.user_data.get('num_questions')
    
    selected_questions = get_random_ncert_questions(sub_name, num_q)
    context.user_data['quiz_questions'] = selected_questions
    context.user_data['current_index'] = 0
    context.user_data['score'] = 0
    context.user_data['user_answers'] = {}
    context.user_data['is_paused'] = False
    
    keyboard = [[InlineKeyboardButton("🚀 Click to Start Quiz", callback_data="start_interactive_quiz")]]
    await query.message.edit_text(f"✅ **NCERT Quiz Ready!**\nSubject: {sub_name}\nQuestions: {num_q}\nTime: {time_limit}s", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

async def ai_quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🎯 Subject ka naam likhein (Jaise: *Indian History, Physics*):")
    return SUBJECT

async def receive_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['subject'] = update.message.text
    await update.message.reply_text("📊 Kitne prashno ka quiz chahiye? *(5 se 150)*:")
    return NUM_QUESTIONS

async def receive_num_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(update.message.text)
        if num < 5 or num > 150:
            await update.message.reply_text("5 se 150 ke beech likhein:")
            return NUM_QUESTIONS
        context.user_data['num_questions'] = num
    except ValueError:
        await update.message.reply_text("Valid number likhein:")
        return NUM_QUESTIONS
    
    keyboard = [
        [InlineKeyboardButton("15 Seconds", callback_data="time_15"), InlineKeyboardButton("30 Seconds", callback_data="time_30")],
        [InlineKeyboardButton("45 Seconds", callback_data="time_45"), InlineKeyboardButton("60 Seconds", callback_data="time_60")]
    ]
    await update.message.reply_text("⏱️ Time set karein:", reply_markup=InlineKeyboardMarkup(keyboard))
    return NCERT_TIME

async def start_interactive_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['current_index'] = 0
    context.user_data['score'] = 0
    context.user_data['user_answers'] = {}
    context.user_data['is_paused'] = False
    await send_single_question(query.message.chat_id, context)

async def send_single_question(chat_id, context):
    if context.user_data.get('is_paused', False):
        return
    questions = context.user_data.get('quiz_questions', [])
    index = context.user_data.get('current_index', 0)
    time_limit = context.user_data.get('time_limit', 30)
    
    if index < len(questions):
        q_data = questions[index]
        message = await context.bot.send_poll(
            chat_id=chat_id,
            question=f"Q.{index + 1}: {q_data.get('question')}",
            options=q_data.get('options'),
            type="quiz",
            correct_option_id=q_data.get('correct', 0),
            is_anonymous=False,
            open_period=time_limit
        )
        context.user_data['active_poll_id'] = message.poll.id
        context.user_data['current_correct_idx'] = q_data.get('correct', 0)
        context.user_data['current_options'] = q_data.get('options')
        context.user_data['current_question_text'] = q_data.get('question')
        
        keyboard = [[InlineKeyboardButton("⏸️ Pause", callback_data="pause_quiz"), InlineKeyboardButton("⏹️ Stop", callback_data="stop_quiz")]]
        ctrl_msg = await context.bot.send_message(chat_id=chat_id, text=f"⚙️ Control (Q.{index+1}):", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data['active_ctrl_msg_id'] = ctrl_msg.message_id
        asyncio.create_task(wait_and_next(chat_id, message.poll.id, time_limit, context))
    else:
        await finish_quiz(chat_id, context)

async def wait_and_next(chat_id, poll_id, time_limit, context):
    await asyncio.sleep(time_limit)
    if context.user_data.get('active_poll_id') == poll_id and not context.user_data.get('is_paused', False):
        index = context.user_data['current_index']
        context.user_data['user_answers'][index] = {
            "question": context.user_data.get('current_question_text'),
            "options": context.user_data.get('current_options'),
            "user_choice_idx": -1,
            "correct_idx": context.user_data.get('current_correct_idx'),
            "correct_choice": context.user_data.get('current_options')[context.user_data.get('current_correct_idx')],
            "status": "Unattempted"
        }
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data.get('active_ctrl_msg_id'))
        except:
            pass
        context.user_data['current_index'] += 1
        context.user_data['active_poll_id'] = None
        await send_single_question(chat_id, context)

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    poll_id = answer.poll_id
    user_options = answer.option_ids
    if context.user_data.get('active_poll_id') == poll_id and not context.user_data.get('is_paused', False):
        correct_idx = context.user_data.get('current_correct_idx', 0)
        options = context.user_data.get('current_options', [])
        index = context.user_data.get('current_index', 0)
        chat_id = answer.user.id
        user_choice_idx = user_options[0] if user_options else -1
        status = "Correct" if user_options and user_options[0] == correct_idx else ("Incorrect" if user_options else "Unattempted")
        if status == "Correct":
            context.user_data['score'] = context.user_data.get('score', 0) + 1
            
        context.user_data['user_answers'][index] = {
            "question": context.user_data.get('current_question_text'),
            "options": options,
            "correct_idx": correct_idx,
            "user_choice_idx": user_choice_idx,
            "correct_choice": options[correct_idx],
            "status": status
        }
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data.get('active_ctrl_msg_id'))
        except:
            pass
        context.user_data['current_index'] += 1
        context.user_data['active_poll_id'] = None
        await send_single_question(chat_id, context)

async def handle_quiz_controls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id
    if data == "pause_quiz":
        context.user_data['is_paused'] = True
        await query.message.edit_text("⏸️ Paused", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Resume", callback_data="resume_quiz")]]))
    elif data == "resume_quiz":
        context.user_data['is_paused'] = False
        await query.message.edit_text("▶️ Resumed")
        await send_single_question(chat_id, context)
    elif data == "stop_quiz":
        context.user_data['is_paused'] = True
        context.user_data['active_poll_id'] = None
        await query.message.edit_text("⏹️ Stopped")
        await finish_quiz(chat_id, context)

async def finish_quiz(chat_id, context):
    user_answers = context.user_data.get('user_answers', {})
    total_questions = len(context.user_data.get('quiz_questions', []))
    score = sum(1 for v in user_answers.values() if v.get("status") == "Correct")
    summary = f"📊 **QUIZ REPORT**\n\nTotal: {total_questions}\nScore: {score}/{total_questions}\n\nPDF report ke liye neeche click karein:"
    keyboard = [[InlineKeyboardButton("📥 Download PDF Report", callback_data="generate_custom_pdf")]]
    await context.bot.send_message(chat_id=chat_id, text=summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def generate_custom_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.from_user.id
    subject = context.user_data.get('subject', 'Quiz')
    user_answers = context.user_data.get('user_answers', {})
    total_questions = len(context.user_data.get('quiz_questions', []))
    correct = sum(1 for v in user_answers.values() if v.get('status') == 'Correct')
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=35, bottomMargin=30)
    story = [Paragraph(f"<b>Scorecard: {subject}</b>", ParagraphStyle('T', fontSize=16, alignment=1)), Spacer(1, 10), Paragraph(f"Total: {total_questions} | Correct: {correct}", ParagraphStyle('S', fontSize=12, alignment=1))]
    doc.build(story)
    buffer.seek(0)
    await context.bot.send_document(chat_id=chat_id, document=InputFile(buffer, filename="Report.pdf"), caption="🎨 Yeh raha aapka PDF report!")

async def menu_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "about_bot":
        await query.message.edit_text("ℹ️ Edugyan2 Enterprise System Quiz Bot.")
    elif data == "back_to_menu":
        await start(update, context)

async def post_init(application):
    await application.bot.set_my_commands([BotCommand("start", "Start Bot"), BotCommand("create", "Create Quiz")])

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    
    ai_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ai_quiz_start, pattern="^start_ai_quiz$")],
        states={
            SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_subject)],
            NUM_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_num_questions)],
        },
        fallbacks=[]
    )
    
    ncert_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(db_quiz_start, pattern="^start_db_quiz$")],
        states={
            NCERT_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ncert_receive_subject)],
            NCERT_NUM_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, ncert_receive_num_questions)],
            NCERT_TIME: [CallbackQueryHandler(ncert_receive_time_and_start, pattern="^ncert_time_")]
        },
        fallbacks=[]
    )
    
    app.add_handler(ai_conv)
    app.add_handler(ncert_conv)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create", lambda update, context: update.message.reply_text(
    "✨ नया क्विज़ बनाने के लिए नीचे दिए गए बटन पर क्लिक करें:",
    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✨ Create Quiz Form", web_app=WebAppInfo(url=QUIZ_WEB_APP))]])
)))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
    
    app.add_handler(CallbackQueryHandler(finish_custom_quiz_callback, pattern="^finish_custom_quiz$"))
    app.add_handler(CallbackQueryHandler(start_interactive_quiz, pattern="^start_interactive_quiz$"))
    app.add_handler(PollAnswerHandler(receive_poll_answer))
    app.add_handler(CallbackQueryHandler(handle_quiz_controls, pattern="^(pause_quiz|resume_quiz|stop_quiz)$"))
    
    # यहाँ पर पिछला अतिरिक्त बैकटीック (`) हटा दिया गया है
    app.add_handler(CallbackQueryHandler(generate_custom_pdf, pattern="^generate_custom_pdf$"))
    
    app.add_handler(CallbackQueryHandler(menu_button_callback, pattern="^(about_bot|back_to_menu)$"))
    
    print("Updated Quiz & Registration System Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()