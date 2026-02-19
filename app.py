import os
import random
import asyncio
from datetime import datetime
from flask import Flask, request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from questions import photoshop_questions, illustrator_questions

TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_CHANNEL = "@AserGfx"
ADMINS = [6511741820, 5570011875]

# ================= STORAGE (FREE VERSION) ================= #

users = {}
leaderboard = []
daily_users = set()
monthly_users = set()

# ================= FLASK ================= #

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# ================= UTILITIES ================= #

def calculate_grade(score):
    if score >= 90:
        return "🏆 Excellent"
    elif score >= 75:
        return "🥇 Very Good"
    elif score >= 60:
        return "👍 Good"
    elif score >= 50:
        return "✅ Pass"
    else:
        return "❌ Fail"

async def check_channel(user_id, context):
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= START ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    daily_users.add(user.id)
    monthly_users.add(user.id)

    keyboard = [
        [InlineKeyboardButton("🧩 Start Quiz", callback_data="start_quiz")],
        [InlineKeyboardButton("📊 My Status", callback_data="status")],
        [InlineKeyboardButton("🏆 Top Students", callback_data="top")],
        [InlineKeyboardButton("📈 Bot Stats", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ About Us", callback_data="about")],
        [InlineKeyboardButton("💼 Job / Services", callback_data="job")],
    ]

    await update.message.reply_text(
        "🎗️ Welcome to *Aser Course Quiz Bot 🧩*\n\n"
        "Test your Photoshop & Illustrator knowledge.\n"
        "100 Questions = 100%",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ================= BUTTON HANDLER ================= #

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "start_quiz":
        joined = await check_channel(user_id, context)
        if not joined:
            await query.message.reply_text(
                "❌ You must join our channel first:\nhttps://t.me/AserGfx"
            )
            return

        users[user_id] = {"step": "name"}
        await query.message.reply_text("📝 Enter your Full Name:")

    elif query.data == "status":
        if user_id not in users or "score" not in users[user_id]:
            await query.message.reply_text("❗ You haven't taken the quiz yet.")
            return

        data = users[user_id]
        await query.message.reply_text(
            f"📊 Your Status\n\n"
            f"Name: {data['name']}\n"
            f"Age: {data['age']}\n"
            f"Batch: {data['batch']}\n"
            f"Score: {data['score']}%\n"
            f"Grade: {data['grade']}"
        )

    elif query.data == "top":
        if not leaderboard:
            await query.message.reply_text("No students yet.")
            return

        sorted_board = sorted(leaderboard, key=lambda x: x["score"], reverse=True)
        text = "🏆 Top Students\n\n"
        for i, user in enumerate(sorted_board[:10], 1):
            text += f"{i}. {user['name']} ({user['batch']}) - {user['score']}%\n"
        await query.message.reply_text(text)

    elif query.data == "stats":
        await query.message.reply_text(
            f"📈 Bot Statistics\n\n"
            f"Daily Users: {len(daily_users)}\n"
            f"Monthly Users: {len(monthly_users)}"
        )

    elif query.data == "about":
        await query.message.reply_text(
            "🎗️ Aser Production – Visual Creative Solutions\n\n"
            "Graphic Design • Video Editing • Social Media • Telegram Bots"
        )

    elif query.data == "job":
        await query.message.reply_text(
            "💼 Our Services\n\n"
            "🎨 Graphic Design\n"
            "📱 Social Media Management\n"
            "🤖 Telegram Bot Development\n\n"
            "Contact: /contact"
        )

# ================= MESSAGE HANDLER ================= #

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in users:
        return

    step = users[user_id]["step"]

    # -------- NAME -------- #
    if step == "name":
        if any(char.isdigit() for char in text):
            await update.message.reply_text("❌ Name must not contain numbers.")
            return
        users[user_id]["name"] = text
        users[user_id]["step"] = "age"
        await update.message.reply_text("🎂 Enter your Age:")

    # -------- AGE -------- #
    elif step == "age":
        if not text.isdigit():
            await update.message.reply_text("❌ Age must be a number.")
            return
        users[user_id]["age"] = text
        users[user_id]["step"] = "batch"

        keyboard = [
            [InlineKeyboardButton("Batch 1", callback_data="batch_1")],
            [InlineKeyboardButton("Batch 2", callback_data="batch_2")],
            [InlineKeyboardButton("Batch 3", callback_data="batch_3")],
            [InlineKeyboardButton("Other", callback_data="batch_other")],
        ]

        await update.message.reply_text(
            "🎓 Select Your Batch:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

# ================= BATCH SELECTION ================= #

async def batch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if "batch_" in query.data:
        batch = query.data.replace("batch_", "")
        users[user_id]["batch"] = batch
        users[user_id]["step"] = "quiz"

        await query.message.reply_text("🚀 Quiz Starting...")
        await start_quiz(user_id, context)

# ================= QUIZ ENGINE ================= #

async def start_quiz(user_id, context):
    questions = photoshop_questions + illustrator_questions
    random.shuffle(questions)

    users[user_id]["questions"] = questions
    users[user_id]["score"] = 0
    users[user_id]["current"] = 0
    users[user_id]["skipped"] = 0

    await send_question(user_id, context)

async def send_question(user_id, context):
    user = users[user_id]
    index = user["current"]

    if index >= len(user["questions"]):
        await finish_quiz(user_id, context)
        return

    q = user["questions"][index]

    keyboard = []
    for option in q["options"]:
        keyboard.append(
            [InlineKeyboardButton(option, callback_data=f"ans|{option}")]
        )

    await context.bot.send_message(
        user_id,
        f"🧩 Question {index+1}/100\n\n{q['question']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    asyncio.create_task(question_timer(user_id, context))

async def question_timer(user_id, context):
    await asyncio.sleep(120)

    if user_id not in users:
        return

    users[user_id]["skipped"] += 1
    users[user_id]["current"] += 1

    if users[user_id]["skipped"] >= 5:
        await context.bot.send_message(
            user_id,
            "❌ Quiz stopped due to 5 unanswered questions."
        )
        await finish_quiz(user_id, context)
        return

    await send_question(user_id, context)

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in users:
        return

    selected = query.data.split("|")[1]
    current_q = users[user_id]["questions"][users[user_id]["current"]]

    if selected == current_q["answer"]:
        users[user_id]["score"] += 1
        await query.message.reply_text("✅ Correct!")
    else:
        await query.message.reply_text(
            f"❌ Wrong!\nCorrect Answer: {current_q['answer']}"
        )

    users[user_id]["current"] += 1
    await send_question(user_id, context)

# ================= FINISH ================= #

async def finish_quiz(user_id, context):
    score = users[user_id]["score"]
    percentage = score
    grade = calculate_grade(percentage)

    users[user_id]["score"] = percentage
    users[user_id]["grade"] = grade

    leaderboard.append({
        "name": users[user_id]["name"],
        "batch": users[user_id]["batch"],
        "score": percentage
    })

    await context.bot.send_message(
        user_id,
        f"🎉 Quiz Finished!\n\n"
        f"Score: {percentage}%\n"
        f"Grade: {grade}"
    )

    for admin in ADMINS:
        await context.bot.send_message(
            admin,
            f"🎓 Student Finished:\n"
            f"{users[user_id]['name']} - {percentage}%"
        )

# ================= BROADCAST ================= #

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast message")
        return

    msg = " ".join(context.args)
    count = 0

    for uid in users.keys():
        try:
            await context.bot.send_message(uid, msg)
            count += 1
        except:
            pass

    await update.message.reply_text(f"✅ Sent to {count} users.")

# ================= WEBHOOK ================= #

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

@app.route("/")
def home():
    return "Aser Course Quiz Bot is Running!"

# ================= HANDLERS ================= #

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("broadcast", broadcast))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(CallbackQueryHandler(batch_handler, pattern="batch_"))
application.add_handler(CallbackQueryHandler(answer_handler, pattern="ans|"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=f"https://your-render-url.onrender.com/{TOKEN}",
    )
