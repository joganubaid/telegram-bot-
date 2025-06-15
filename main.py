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
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "123456789"))  # Replace with your actual Telegram user ID
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

# Subjects List
THEORY_SUBJECTS = [
    "biology",
    "mathematics",
    "communication_skill",
    "electrical_engineering",
    "mechanical_engineering",
    "environmental_science",
    "physics_1",
    "physics_2",
    "mathematics_1",
    "mathematics_2",
    "chemistry",
    "constitution_of_india",
    "civil_engineering",
    "electronics",
    "fundamental_of_computing"
]

LAB_SUBJECTS = [
    "physics_laboratory_1",
    "physics_laboratory_2",
    "engineering_graphics_lab",
    "workshop",
    "mechanics_laboratory",
    "chemistry_lab",
    "language_lab",
    "design_thinking"
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
    scheduler.add_job(send_report_to_admin, 'cron', day_of_week='mon', hour=9, minute=0)
    scheduler.start()

# Telegram Bot Commands

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📘 Theory", callback_data="category_theory")],
                [InlineKeyboardButton("🧪 Labs", callback_data="category_labs")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("📚 Choose a category:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("📚 Choose a category:", reply_markup=reply_markup)

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("category_", "")

    subjects = THEORY_SUBJECTS if category == "theory" else LAB_SUBJECTS
    context.user_data["category"] = category

    keyboard = [[InlineKeyboardButton(subj.replace("_", " ").title(), callback_data=subj)] for subj in subjects]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("📘 Select a subject:", reply_markup=reply_markup)

async def subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subject = query.data
    context.user_data["subject"] = subject

    if subject in LAB_SUBJECTS:
        keyboard = [[InlineKeyboardButton("📁 Material", callback_data="lab_material")],
                    [InlineKeyboardButton("⬅️ Back to Subjects", callback_data=f"category_{context.user_data.get('category')}")]]
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
            [InlineKeyboardButton("⬅️ Back to Subjects", callback_data=f"category_{context.user_data.get('category')}")]
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

async def lab_material_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subject = context.user_data.get("subject")

    file_path = os.path.join(PDF_FOLDER, f"{subject}_material.pdf")
    if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            await query.message.reply_document(document=f)
    else:
        await query.message.reply_text("❌ Material PDF not found.")

# Main Entry

def main():
    keep_alive()
    clean_old_logs()
    start_scheduler()

    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(start, pattern="^back_to_main$"))
    app_bot.add_handler(CallbackQueryHandler(category_handler, pattern="^category_(theory|labs)$"))
    app_bot.add_handler(CallbackQueryHandler(subject_handler, pattern="^" + "|".join(THEORY_SUBJECTS + LAB_SUBJECTS) + "$"))
    app_bot.add_handler(CallbackQueryHandler(ask_year, pattern="^yearselect_(mid_sem1|mid_sem2|end_sem)$"))
    app_bot.add_handler(CallbackQueryHandler(send_exam_pdf, pattern="^year_\\d{4}$"))
    app_bot.add_handler(CallbackQueryHandler(unit_note_handler, pattern="^unit[1-5]$"))
    app_bot.add_handler(CallbackQueryHandler(lab_material_handler, pattern="^lab_material$"))
    print("Bot is polling...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()

