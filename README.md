# Aser Course Quiz Bot 🧩

Telegram bot for Aser students with colorful UX, registration, timed quiz flow, grading, leaderboards, and admin tools.

## What is included
- ✅ Registration flow with validation:
  - Full name (letters only)
  - Age (number only)
  - Batch button selection (`Batch 1/2/3`) + custom batch input
- ✅ Required channel check before quiz (`@AserGfx`)
- ✅ 100-question quiz (50 Photoshop + 50 Illustrator)
- ✅ Per-question timer:
  - 1-minute warning
  - 2-minute timeout auto move
  - Auto-stop after 5 consecutive skips/timeouts
- ✅ Correct/incorrect symbols (`✅` / `❌`) and colorful feedback text
- ✅ Result summary with score, grade, pass/fail, and level
- ✅ Admin notified when any student finishes quiz
- ✅ Admin tools:
  - `/broadcast` send message to all users with delivery count
  - `/feedback <user_id> <message>` send direct feedback to student
- ✅ Public features:
  - `/top` (overall + per batch)
  - `/mystatus`
  - `/botstatus` (daily + monthly user counts)
  - `/about`, `/story`, `/job`, `/social`, `/contact`, `/help`
- ✅ Main menu keyboard for better UI/UX navigation

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill BOT_TOKEN in .env
python bot.py
```

## Environment variables
See `.env.example`:
- `BOT_TOKEN`
- `REQUIRED_CHANNEL`
- `ADMIN_1_ID`
- `ADMIN_2_ID`

## Database
The bot uses SQLite and auto-creates `quiz_bot.db` with:
- `users`
- `quiz_results`
- `user_activity`