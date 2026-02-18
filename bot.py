from __future__ import annotations

import logging
import os
import random
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv
import question_bank
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from question_bank import ALL_QUESTIONS, QuizQuestion

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DB_PATH = "quiz_bot.db"
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@AserGfx")

ADMIN_IDS = {
    int(os.getenv("ADMIN_1_ID", "6511741820")),
    int(os.getenv("ADMIN_2_ID", "5570011875")),
}

(
    ASK_NAME,
    ASK_AGE,
    ASK_BATCH,
    ASK_CUSTOM_BATCH,
    BROADCAST_WAIT,
) = range(5)


@dataclass
class Session:
    questions: List[QuizQuestion]
    current: int = 0
    score: int = 0
    unanswered_streak: int = 0


ABOUT_US = """✨ *About Aser Production*

Hello,
We are *Aser Production – Visual Creative Solutions*, a creative team helping personal brands and companies build strong, attractive, and trustworthy online presence.

*What we do:*
◉ *Content Creation*
• Graphic design
• Video editing
• Script & promotional content writing

◉ *Social Media Management*
• Platform management (Instagram, Facebook, TikTok, YouTube)
• Content planning & creation
• Audience engagement & growth
• Analytics tracking & performance reporting
• Brand consistency & strategy optimization

◉ *Telegram Bot Development*
• Assistant bots
• E-commerce bots
• Registration & automation bots

We have *5+ years* of experience and have worked with *6+ companies*, including:
Eima Fashion, Luy System, Qesem Academy, Muke Salon & Spa, Bright Stationery, and Sabi Engineering.

Let’s discuss how we can support your business.
Feel free to message us anytime.

*Aser Production – Visual Creative Solutions* 🎗️"""

OUR_STORY = """📖 *Our Story*
Aser Production was founded by *Eden Solomon* and *Biruk Girma*, two university students with a passion for visual creativity and technology.

We specialize in graphics design, content creation, video editing, and providing quality training courses in emerging technologies.
Our mission is to help businesses and individuals express their ideas visually and provide the skills needed to thrive in the digital world.

👩‍💻 *Eden Solomon* — Founder & CEO
Computer Science Student at Bule Hora University

🧑‍💻 *Biruk Girma* — Co-Founder & CTO
Computer Science Student at Wolkite University

◉ Telegram Eden: t.me/AserProOfficial
◉ Telegram Biruk: t.me/AserSupport

Contact:
📧 aser972912@gmail.com
📱 +251936141055 / +251991076523
🌐 https://aserproduction.netlify.app/"""

SERVICES = """💼 *OUR SERVICES*

Aser Production – Visual Creative Solutions
Building strong, attractive, and trustworthy online presence.

🎨 *Content Creation*
• Professional Graphic Design
• High-Quality Video Editing
• Script & Promotional Writing
• Social Media Graphics
• Logo & Brand Identity

📱 *Social Media Management*
• Platform Management (Instagram, Facebook, TikTok, YouTube)
• Content Planning & Creation
• Audience Growth Strategies
• Analytics & Reporting
• Brand Optimization

🤖 *Telegram Bot Development*
• Assistant Bots
• Quiz & Educational Bots
• Custom Business Solutions

Our Experience:
• 5+ years in creative industry
• Worked with 6+ companies
• 100% Satisfaction Guarantee

Contact for Services:
/contact"""

CONTACT = """📞 *Contact Aser Production*
📧 aser972912@gmail.com
📱 +251936141055 / +251991076523
🌐 https://aserproduction.netlify.app/
Fiverr: https://www.fiverr.com/s/R7PapP2"""

SOCIALS = """🌐 *Our Social Media*
Telegram Channel: https://t.me/AserGfx
Admin: https://t.me/AserProOfficial
Support: https://t.me/AserSupport
Telegram bot: @aser_academy_bot
TikTok: https://www.tiktok.com/@aser.production
YouTube: www.youtube.com/@AserTechNovaContentCreation
LinkedIn: www.linkedin.com/in/aser-production-a91020398"""


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🧩 Start Quiz"), KeyboardButton("📊 My Status")],
            [KeyboardButton("🏆 Top Students"), KeyboardButton("📈 Bot Status")],
            [KeyboardButton("💼 Job"), KeyboardButton("ℹ️ About Us")],
            [KeyboardButton("📖 Our Story"), KeyboardButton("🌐 Social Media")],
            [KeyboardButton("🆘 Help"), KeyboardButton("📞 Contact")],
        ],
        resize_keyboard=True,
    )


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(db()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                age INTEGER,
                batch TEXT,
                joined_at TEXT,
                last_seen TEXT
            );

            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                submitted_at TEXT,
                score INTEGER,
                total INTEGER,
                percentage REAL,
                grade TEXT,
                status TEXT,
                level TEXT,
                batch TEXT
            );

            CREATE TABLE IF NOT EXISTS user_activity (
                user_id INTEGER,
                day TEXT,
                PRIMARY KEY(user_id, day)
            );
            """
        )
        conn.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def touch_activity(user_id: int) -> None:
    day = today_key()
    with closing(db()) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_activity (user_id, day) VALUES (?, ?)",
            (user_id, day),
        )
        conn.commit()


def upsert_user(user_id: int, username: Optional[str], full_name: str, age: int, batch: str) -> None:
    with closing(db()) as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, full_name, age, batch, joined_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                age=excluded.age,
                batch=excluded.batch,
                last_seen=excluded.last_seen
            """,
            (user_id, username, full_name, age, batch, now_iso(), now_iso()),
        )
        conn.commit()


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with closing(db()) as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def all_user_ids() -> List[int]:
    with closing(db()) as conn:
        rows = conn.execute("SELECT user_id FROM users").fetchall()
    return [int(row["user_id"]) for row in rows]


def store_result(user_id: int, score: int, total: int, grade: str, status: str, level: str, batch: str) -> None:
    percentage = round((score / total) * 100, 2) if total else 0
    with closing(db()) as conn:
        conn.execute(
            """
            INSERT INTO quiz_results (user_id, submitted_at, score, total, percentage, grade, status, level, batch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, now_iso(), score, total, percentage, grade, status, level, batch),
        )
        conn.commit()


def latest_result(user_id: int) -> Optional[sqlite3.Row]:
    with closing(db()) as conn:
        return conn.execute(
            "SELECT * FROM quiz_results WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()


def leaderboard(batch: Optional[str] = None, limit: int = 10) -> List[sqlite3.Row]:
    query = (
        "SELECT u.full_name, u.batch, q.percentage "
        "FROM quiz_results q JOIN users u ON q.user_id=u.user_id"
    )
    params: List[object] = []
    if batch:
        query += " WHERE u.batch=?"
        params.append(batch)
    query += " ORDER BY q.percentage DESC, q.score DESC LIMIT ?"
    params.append(limit)

    with closing(db()) as conn:
        return conn.execute(query, params).fetchall()


def usage_stats() -> Dict[str, int]:
    today = today_key()
    month = today[:7]
    with closing(db()) as conn:
        daily_users = conn.execute(
            "SELECT COUNT(*) AS c FROM user_activity WHERE day=?", (today,)
        ).fetchone()["c"]
        monthly_users = conn.execute(
            "SELECT COUNT(*) AS c FROM user_activity WHERE substr(day, 1, 7)=?", (month,)
        ).fetchone()["c"]
    return {"daily": int(daily_users or 0), "monthly": int(monthly_users or 0)}


def grade_result(score: int, total: int) -> Tuple[str, str, str]:
    pct = (score / total * 100) if total else 0
    if pct >= 90:
        return "A+", "Pass ✅", "Excellent 🌟"
    if pct >= 80:
        return "A", "Pass ✅", "Very Good 🎉"
    if pct >= 70:
        return "B", "Pass ✅", "Good 👍"
    if pct >= 60:
        return "C", "Pass ✅", "Fair 🙂"
    if pct >= 50:
        return "D", "Pass ✅", "Needs Improvement 🧠"
    return "F", "Fail ❌", "Try Again 💪"


def parse_name(text: str) -> Optional[str]:
    cleaned = " ".join(text.split())
    if not cleaned or any(ch.isdigit() for ch in cleaned):
        return None
    valid_chars = set(" -'’")
    if any(not (ch.isalpha() or ch in valid_chars) for ch in cleaned):
        return None
    return cleaned


async def is_admin(update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id in ADMIN_IDS)


async def is_in_required_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False

    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        return member.status in {"member", "administrator", "creator"}
    except Exception as exc:
        logger.warning("Failed to check channel membership: %s", exc)
        return False


async def send_join_message(update: Update) -> None:
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📢 Join Required Channel", url="https://t.me/AserGfx")]]
    )
    await update.effective_message.reply_text(
        "⚠️ To use the quiz, you must join our required channel first: @AserGfx",
        reply_markup=markup,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    touch_activity(update.effective_user.id)

    await update.effective_message.reply_text(
        "🎉 *Welcome to Aser Course Quiz Bot 🧩*\n\n"
        "Let's register first.\n"
        "Please send your *full name* (letters only).",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    full_name = parse_name(update.effective_message.text)
    if not full_name:
        await update.effective_message.reply_text("❌ Full name must contain only letters and spaces.")
        return ASK_NAME

    context.user_data["full_name"] = full_name
    await update.effective_message.reply_text("✅ Great! Now send your age (number only).")
    return ASK_AGE


async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age_text = update.effective_message.text.strip()
    if not age_text.isdigit():
        await update.effective_message.reply_text("❌ Age must be a number.")
        return ASK_AGE

    age = int(age_text)
    if age < 8 or age > 99:
        await update.effective_message.reply_text("⚠️ Please enter age between 8 and 99.")
        return ASK_AGE

    context.user_data["age"] = age
    markup = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Batch 1"), KeyboardButton("Batch 2")],
            [KeyboardButton("Batch 3"), KeyboardButton("Other")],
        ],
        resize_keyboard=True,
    )
    await update.effective_message.reply_text("📚 Choose your batch:", reply_markup=markup)
    return ASK_BATCH


async def ask_batch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    batch = update.effective_message.text.strip()
    if batch == "Other":
        await update.effective_message.reply_text("✍️ Type your batch name:", reply_markup=ReplyKeyboardRemove())
        return ASK_CUSTOM_BATCH

    if batch not in {"Batch 1", "Batch 2", "Batch 3"}:
        await update.effective_message.reply_text("Please choose Batch 1, Batch 2, Batch 3, or Other.")
        return ASK_BATCH

    return await finish_registration(update, context, batch)


async def ask_custom_batch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    custom_batch = " ".join(update.effective_message.text.split())
    if not custom_batch:
        await update.effective_message.reply_text("❌ Batch name cannot be empty.")
        return ASK_CUSTOM_BATCH
    return await finish_registration(update, context, custom_batch)


async def finish_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, batch: str) -> int:
    user = update.effective_user
    upsert_user(user.id, user.username, context.user_data["full_name"], context.user_data["age"], batch)
    touch_activity(user.id)

    await update.effective_message.reply_text(
        "✅ Registration completed!\n"
        "Use /quiz or click *🧩 Start Quiz* to begin.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu(),
    )
    return ConversationHandler.END


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    touch_activity(user.id)

    profile = get_user(user.id)
    if not profile:
        await update.effective_message.reply_text("Please register first with /start.")
        return

    if not await is_in_required_channel(update, context):
        await send_join_message(update)
        return

    questions = ALL_QUESTIONS.copy()
    random.shuffle(questions)
    context.application.user_data[user.id]["session"] = Session(questions=questions)

    await update.effective_message.reply_text(
        "🎯 *Quiz Started!*\n"
        "• 100 questions (Photoshop + Illustrator)\n"
        "• 2 minutes per question\n"
        "• 1-minute warning\n"
        "• 5 consecutive skips/timeouts = quiz stopped",
        parse_mode=ParseMode.MARKDOWN,
    )
    await send_question(chat_id=update.effective_chat.id, user_id=user.id, context=context)


async def send_question(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    ud = context.application.user_data.get(user_id, {})
    session: Optional[Session] = ud.get("session")
    if not session:
        return

    if session.current >= len(session.questions):
        await finish_quiz(chat_id, user_id, context)
        return

    question = session.questions[session.current]
    keyboard = [
        [InlineKeyboardButton(f"{chr(65+i)}. {opt}", callback_data=f"ans:{i}")]
        for i, opt in enumerate(question.options)
    ]
    keyboard.append([InlineKeyboardButton("⏭️ Skip", callback_data="skip")])

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"🎨 *Question {session.current + 1}/{len(session.questions)}*\n"
            f"*Topic:* {question.topic}\n\n"
            f"{question.prompt}\n\n"
            "⏱️ You have 2 minutes"
        ),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    for key in ("warn_job", "timeout_job"):
        old = ud.get(key)
        if old:
            old.schedule_removal()

    ud["warn_job"] = context.job_queue.run_once(
        question_warning,
        when=60,
        data={"chat_id": chat_id, "user_id": user_id},
    )
    ud["timeout_job"] = context.job_queue.run_once(
        question_timeout,
        when=120,
        data={"chat_id": chat_id, "user_id": user_id},
    )


async def question_warning(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=context.job.data["chat_id"],
        text="⚠️ 1 minute left for this question.",
    )


async def question_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data["chat_id"]
    user_id = context.job.data["user_id"]
    ud = context.application.user_data.get(user_id, {})
    session: Optional[Session] = ud.get("session")
    if not session:
        return

    session.current += 1
    session.unanswered_streak += 1

    await context.bot.send_message(chat_id=chat_id, text="⌛ Time up. Moving to next question.")

    if session.unanswered_streak >= 5:
        await context.bot.send_message(chat_id=chat_id, text="🛑 Quiz stopped after 5 consecutive unanswered questions.")
        await finish_quiz(chat_id, user_id, context)
        return

    await send_question(chat_id, user_id, context)


async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    ud = context.application.user_data.get(user_id, {})
    session: Optional[Session] = ud.get("session")
    if not session or session.current >= len(session.questions):
        await query.edit_message_text("⚠️ No active question. Start again with /quiz.")
        return

    for key in ("warn_job", "timeout_job"):
        job = ud.get(key)
        if job:
            job.schedule_removal()
            ud[key] = None

    question = session.questions[session.current]

    if query.data == "skip":
        session.unanswered_streak += 1
        feedback = "⏭️ Skipped."
    else:
        selected = int(query.data.split(":", maxsplit=1)[1])
        if selected == question.answer_index:
            session.score += 1
            session.unanswered_streak = 0
            feedback = f"✅ Correct!\n{question.explanation}"
        else:
            session.unanswered_streak = 0
            feedback = f"❌ Wrong. Correct answer: *{question.options[question.answer_index]}*"

    await query.edit_message_text(feedback, parse_mode=ParseMode.MARKDOWN)
    session.current += 1

    if session.unanswered_streak >= 5:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🛑 Quiz stopped after 5 consecutive unanswered questions.",
        )
        await finish_quiz(update.effective_chat.id, user_id, context)
        return

    await send_question(update.effective_chat.id, user_id, context)


async def finish_quiz(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    ud = context.application.user_data.get(user_id, {})
    session: Optional[Session] = ud.get("session")
    if not session:
        return

    total = len(session.questions)
    grade, status, level = grade_result(session.score, total)
    percent = round((session.score / total) * 100, 2) if total else 0
    profile = get_user(user_id)
    batch = profile["batch"] if profile else "Unknown"

    store_result(user_id, session.score, total, grade, status, level, batch)

    result_text = (
        "🏁 *Quiz Completed*\n"
        f"👤 Name: {profile['full_name'] if profile else 'N/A'}\n"
        f"🎂 Age: {profile['age'] if profile else 'N/A'}\n"
        f"🏷️ Batch: {batch}\n"
        f"📊 Score: {session.score}/{total} ({percent}%)\n"
        f"🧾 Grade: {grade}\n"
        f"📌 Status: {status}\n"
        f"🌈 Level: {level}"
    )
    await context.bot.send_message(chat_id=chat_id, text=result_text, parse_mode=ParseMode.MARKDOWN)

    admin_text = (
        "📥 *Student Finished Quiz*\n"
        f"ID: `{user_id}`\n"
        f"Name: {profile['full_name'] if profile else 'N/A'}\n"
        f"Batch: {batch}\n"
        f"Score: {session.score}/{total} ({percent}%)\n"
        f"Reply with /feedback {user_id} <message>"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as exc:
            logger.warning("Cannot notify admin %s: %s", admin_id, exc)

    ud.pop("session", None)


async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    touch_activity(user.id)

    profile = get_user(user.id)
    if not profile:
        await update.effective_message.reply_text("Please register first with /start.")
        return

    result = latest_result(user.id)
    if not result:
        await update.effective_message.reply_text(
            f"👤 {profile['full_name']}\n🎂 {profile['age']}\n🏷️ {profile['batch']}\nNo quiz attempt yet.",
            reply_markup=main_menu(),
        )
        return

    await update.effective_message.reply_text(
        f"👤 {profile['full_name']}\n"
        f"🎂 {profile['age']}\n"
        f"🏷️ {profile['batch']}\n"
        f"📊 Last Score: {result['score']}/{result['total']} ({result['percentage']}%)\n"
        f"🧾 Grade: {result['grade']} | {result['status']} | {result['level']}",
        reply_markup=main_menu(),
    )


def format_leaderboard(title: str, rows: Iterable[sqlite3.Row]) -> List[str]:
    lines = [title]
    for index, row in enumerate(rows, start=1):
        lines.append(f"{index}. {row['full_name']} ({row['batch']}) - {row['percentage']}%")
    if len(lines) == 1:
        lines.append("• No data yet")
    return lines


async def top_students_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)

    blocks = []
    blocks.extend(format_leaderboard("🏆 *Top Students (All Batches)*", leaderboard(None, 10)))
    blocks.append("")
    blocks.extend(format_leaderboard("📌 *Top Batch 1*", leaderboard("Batch 1", 3)))
    blocks.append("")
    blocks.extend(format_leaderboard("📌 *Top Batch 2*", leaderboard("Batch 2", 3)))
    blocks.append("")
    blocks.extend(format_leaderboard("📌 *Top Batch 3*", leaderboard("Batch 3", 3)))

    await update.effective_message.reply_text("\n".join(blocks), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())


async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)
    stats = usage_stats()
    await update.effective_message.reply_text(
        "📈 *Bot Status*\n"
        f"Daily users (today): {stats['daily']}\n"
        f"Monthly users (sum of daily users): {stats['monthly']}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu(),
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)
    await update.effective_message.reply_text(ABOUT_US, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())


async def story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)
    await update.effective_message.reply_text(OUR_STORY, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())


async def job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)
    await update.effective_message.reply_text(SERVICES, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())


async def social(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)
    await update.effective_message.reply_text(SOCIALS, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)
    await update.effective_message.reply_text(CONTACT, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    touch_activity(update.effective_user.id)
    await update.effective_message.reply_text(
        "🆘 *Help Menu*\n"
        "/start - Register\n"
        "/quiz - Start quiz\n"
        "/mystatus - Your status\n"
        "/top - Leaderboard\n"
        "/botstatus - Daily & monthly users\n"
        "/about - About us\n"
        "/story - Our story\n"
        "/job - Services\n"
        "/social - Social links\n"
        "/contact - Contact details\n"
        "/help - This help",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu(),
    )


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_admin(update):
        await update.effective_message.reply_text("🚫 Admin only.")
        return ConversationHandler.END
    await update.effective_message.reply_text("📣 Send the broadcast message now:")
    return BROADCAST_WAIT


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.effective_message.text
    recipients = all_user_ids()
    sent = 0

    for user_id in recipients:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 *Announcement*\n\n{message}", parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except Exception:
            continue

    await update.effective_message.reply_text(f"✅ Broadcast done. Sent to {sent}/{len(recipients)} users.")
    return ConversationHandler.END


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update):
        await update.effective_message.reply_text("🚫 Admin only.")
        return

    if len(context.args) < 2 or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /feedback <user_id> <message>")
        return

    user_id = int(context.args[0])
    message = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=user_id, text=f"📬 *Admin Feedback*\n\n{message}", parse_mode=ParseMode.MARKDOWN)
        await update.effective_message.reply_text("✅ Feedback sent.")
    except Exception as exc:
        await update.effective_message.reply_text(f"❌ Failed to send feedback: {exc}")


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    mapping = {
        "🧩 Start Quiz": quiz,
        "📊 My Status": my_status,
        "🏆 Top Students": top_students_cmd,
        "📈 Bot Status": bot_status,
        "💼 Job": job,
        "ℹ️ About Us": about,
        "📖 Our Story": story,
        "🌐 Social Media": social,
        "🆘 Help": help_cmd,
        "📞 Contact": contact,
    }
    handler = mapping.get(text)
    if handler:
        await handler(update, context)


def build_app() -> Application:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing. Put it in .env")

    app = Application.builder().token(token).build()

    registration = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_BATCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_batch)],
            ASK_CUSTOM_BATCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_custom_batch)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    broadcast = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={BROADCAST_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)]},
        fallbacks=[],
    )

    app.add_handler(registration)
    app.add_handler(broadcast)

    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(answer_callback, pattern=r"^(ans:\d+|skip)$"))
    app.add_handler(CommandHandler("mystatus", my_status))
    app.add_handler(CommandHandler("top", top_students_cmd))
    app.add_handler(CommandHandler("botstatus", bot_status))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("story", story))
    app.add_handler(CommandHandler("job", job))
    app.add_handler(CommandHandler("social", social))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("feedback", feedback))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router), group=20)
    return app


def main() -> None:
    init_db()
    application = build_app()
    logger.info("Starting Aser Course Quiz Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
question_bank.py
question_bank.py