import os
import csv
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "7437848217"))  # Replace with your actual Telegram user ID
PDF_FOLDER = "pdfs"
LOG_FOLDER = "logs"

# Flask app for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

# Subjects split into Theory and Labs
subjects_theory = [
    "biology",
    "mathematics",
    "communication_skill",
    "electrical_engineering",
    "mechanical_engineering",
    "environmental_science",
    "physics"
]

subjects_labs = [
    "physics_lab",
    "engineering_graphics_lab",
    "workshop",
    "mechanics_lab",
    "chemistry_lab",
    "language_lab",
    "design_thinking_lab"
]

# Log download to CSV and notify admin
def log_download(user, subject, exam_type, year):
    os.makedirs(LOG_FOLDER, exist_ok=True)
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")

    username = user.username or "NoUsername"
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "UserID", "Username", "Name", "Subject", "ExamType", "Year"])
        writer.writerow([timestamp, user.id, username, name, subject, exam_type, year])

    try:
        bot = Bot(token=TOKEN)
        msg = (f"📥 *New Download*\n👤 {name or username}\n🗂 Subject: {subject.title()}\n"
               f"📄 Type: {exam_type.replace('_', ' ').title()} ({year})")
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Admin alert failed: {e}")

# Clean logs older than 30 days
def clean_old_logs():
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    if not os.path.isfile(log_file):
        return

    df = pd.read_csv(log_file, parse_dates=["Timestamp"])
    df = df[df["Timestamp"] >= (datetime.now() - timedelta(days=30))]
    df.to_csv(log_file, index=False)

# Scheduled report to admin
def send_report_to_admin():
    log_file = os.path.join(LOG_FOLDER, "downloads.csv")
    if not os.path.isfile(log_file):
        return

    try:
        df = pd.read_csv(log_file)
        total = len(df)
        subject_counts = df["Subject"].value_counts().head(3)
        top_users = df["Username"].value_counts().head(3)

        msg = f"📊 *Weekly Download Summary*\n\n"
        msg += f"📥 Total Downloads: {total}\n\n"
        msg += "🏅 Top Subjects:\n"
        for subject, count in subject_counts.items():
            msg += f"• {subject.title()}: {count}\n"
        msg += "\n👤 Top Users:\n"
        for user, count in top_users.items():
            msg += f"• @{user}: {count}\n"

        bot = Bot(token=TOKEN)
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode="Markdown")
    except Exception as e:
        print(f"[Scheduler] Report error: {e}")

# Scheduler

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_report_to_admin, 'cron', day_of_week='mon', hour=9, minute=0)  # Weekly on Monday 9 AM
    scheduler.start()

# Telegram Bot Commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 Theory Subjects", callback_data="theory")],
        [InlineKeyboardButton("🧪 Lab Subjects", callback_data="labs")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("📚 Choose a category:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("📚 Choose a category:", reply_markup=reply_markup)

async def show_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data

    if category == "theory":
        keyboard = [[InlineKeyboardButton(subj.replace("_", " ").title(), callback_data=subj)] for subj in subjects_theory]
    elif category == "labs":
        keyboard = [[InlineKeyboardButton(subj.replace("_", " ").title(), callback_data=subj)] for subj in subjects_labs]
    else:
        keyboard = []

    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📚 Select a subject:", reply_markup=reply_markup)

async def subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subject = query.data
    context.user_data["subject"] = subject

    if subject == "physics":
        keyboard = [
            [InlineKeyboardButton("Physics 1", callback_data="physics1")],
            [InlineKeyboardButton("Physics 2", callback_data="physics2")],
            [InlineKeyboardButton("⬅️ Back to Subjects", callback_data="theory")]
        ]
        await query.edit_message_text("🔬 Select a Physics section:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif subject == "mathematics":
        keyboard = [
            [InlineKeyboardButton("Mathematics 1", callback_data="mathematics1")],
            [InlineKeyboardButton("Mathematics 2", callback_data="mathematics2")],
            [InlineKeyboardButton("⬅️ Back to Subjects", callback_data="theory")]
        ]
        await query.edit_message_text("📐 Select a Mathematics section:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    is_lab = subject in subjects_labs

    if is_lab:
        keyboard = [
            [InlineKeyboardButton("📘 Material", callback_data="unit1")],
            [InlineKeyboardButton("⬅️ Back to Subjects", callback_data="labs")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📄 Mid Sem 1", callback_data="yearselect_mid_sem1")],
            [InlineKeyboardButton("📄 Mid Sem 2", callback_data="yearselect_mid_sem2")],
            [InlineKeyboardButton("📄 End Sem", callback_data="yearselect_end_sem")],
            [InlineKeyboardButton("📘 Notes: Unit 1", callback_data="unit1"),
             InlineKeyboardButton("Unit 2", callback_data="unit2")],
            [InlineKeyboardButton("Unit 3", callback_data="unit3"),
             InlineKeyboardButton("Unit 4", callback_data="unit4")],
            [InlineKeyboardButton("Unit 5", callback_data="unit5")],
            [InlineKeyboardButton("⬅️ Back to Subjects", callback_data="theory")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📘 {subject.replace('_', ' ').title()} - Choose an option:", reply_markup=reply_markup)

async def ask_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    exam_type = query.data.replace("yearselect_", "")
    context.user_data["exam_type"] = exam_type
    subject = context.user_data.get("subject")

    default_years = ["2024", "2023"]
    keyboard = [[InlineKeyboardButton(year, callback_data=f"year_{year}")] for year in default_years]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=subject)])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"📅 Select year for {exam_type.replace('_', ' ').title()}:", reply_markup=reply_markup)

async def send_exam_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    year = query.data.split("_")[1]
    subject = context.user_data.get("subject")
    exam_type = context.user_data.get("exam_type")

    if not subject or not exam_type:
        await query.message.reply_text("⚠️ Please start again with /start.")
        return

    file_path = os.path.join(PDF_FOLDER, f"{subject}_{exam_type}_{year}.pdf")

    if os.path.isfile(file_path):
        log_download(query.from_user, subject, exam_type, year)
        with open(file_path, "rb") as f:
            await query.message.reply_document(document=f)
    else:
        await query.message.reply_text(f"❌ PDF for {subject.replace('_', ' ').title()} ({exam_type.replace('_', ' ').title()}) {year} not found.")

async def unit_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    unit = query.data
    subject = context.user_data.get("subject")

    if not subject:
        await query.message.reply_text("⚠️ Please select a subject first using /start.")
        return

    file_path = os.path.join(PDF_FOLDER, f"{subject}_{unit}.pdf")
    if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            await query.message.reply_document(document=f)
    else:
        await query.message.reply_text("❌ PDF for this unit not found.")

# Main Entry

def main():
    keep_alive()
    clean_old_logs()
    start_scheduler()

    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(show_subjects, pattern="^(theory|labs)$"))
    app_bot.add_handler(CallbackQueryHandler(start, pattern="^back_to_categories$"))
    app_bot.add_handler(CallbackQueryHandler(subject_handler, pattern="^" + "|".join(subjects_theory + subjects_labs + ["physics1", "physics2", "mathematics1", "mathematics2"]) + "$"))
    app_bot.add_handler(CallbackQueryHandler(ask_year, pattern="^yearselect_(mid_sem1|mid_sem2|end_sem)$"))
    app_bot.add_handler(CallbackQueryHandler(send_exam_pdf, pattern="^year_\\d{4}$"))
    app_bot.add_handler(CallbackQueryHandler(unit_note_handler, pattern="^unit[1-5]$"))
    print("Bot is polling...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
