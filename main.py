import os
from threading import Thread
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
PDF_FOLDER = "pdfs"

pdfs = {
    "chemistry": {
        "unit1": os.path.join(PDF_FOLDER, "chemistry_unit1.pdf"),
        "unit2": os.path.join(PDF_FOLDER, "chemistry_unit2.pdf"),
        "unit3": os.path.join(PDF_FOLDER, "chemistry_unit3.pdf"),
        "unit4": os.path.join(PDF_FOLDER, "chemistry_unit4.pdf"),
        "unit5": os.path.join(PDF_FOLDER, "chemistry_unit5.pdf"),
    },
    "physics": {
        "unit1": os.path.join(PDF_FOLDER, "physics_unit1.pdf"),
        "unit2": os.path.join(PDF_FOLDER, "physics_unit2.pdf"),
        "unit3": os.path.join(PDF_FOLDER, "physics_unit3.pdf"),
        "unit4": os.path.join(PDF_FOLDER, "physics_unit4.pdf"),
        "unit5": os.path.join(PDF_FOLDER, "physics_unit5.pdf"),
    },
    "biology": {
        "unit1": os.path.join(PDF_FOLDER, "biology_unit1.pdf"),
        "unit2": os.path.join(PDF_FOLDER, "biology_unit2.pdf"),
        "unit3": os.path.join(PDF_FOLDER, "biology_unit3.pdf"),
        "unit4": os.path.join(PDF_FOLDER, "biology_unit4.pdf"),
        "unit5": os.path.join(PDF_FOLDER, "biology_unit5.pdf"),
    },
    "mathematics": {
        "unit1": os.path.join(PDF_FOLDER, "math_unit1.pdf"),
        "unit2": os.path.join(PDF_FOLDER, "math_unit2.pdf"),
        "unit3": os.path.join(PDF_FOLDER, "math_unit3.pdf"),
        "unit4": os.path.join(PDF_FOLDER, "math_unit4.pdf"),
        "unit5": os.path.join(PDF_FOLDER, "math_unit5.pdf"),
    }
}

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.effective_user.id} started the bot")
    keyboard = [
        [InlineKeyboardButton("Chemistry", callback_data="chemistry")],
        [InlineKeyboardButton("Physics", callback_data="physics")],
        [InlineKeyboardButton("Mathematics", callback_data="mathematics")],
        [InlineKeyboardButton("Biology", callback_data="biology")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 Select a subject:", reply_markup=reply_markup)

async def subject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        print(f"Error in query.answer(): {e}")

    subject = query.data
    print(f"User selected subject: {subject}")
    context.user_data["subject"] = subject

    keyboard = [[InlineKeyboardButton(f"Unit {i}", callback_data=f"unit{i}") for i in range(1, 6)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
   await query.edit_message_text(
    f"You selected *{subject.title()}*.\nNow select a unit:",
    reply_markup=reply_markup,
    parse_mode="Markdown"
)


async def unit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        print(f"query.answer() failed: {e}")

    unit = query.data
    user_id = update.effective_user.id
    print(f"User {user_id} selected unit: {unit}")
    subject = context.user_data.get("subject")

    if not subject:
        print("Subject not found in context.user_data")
        await query.message.reply_text("⚠️ Please use /start and select a subject first.")
        return

    file_path = pdfs.get(subject, {}).get(unit)
    if file_path and os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            await query.message.reply_document(document=f)
    else:
        await query.message.reply_text("❌ PDF file not found.")

def main():
    keep_alive()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(subject_handler, pattern="^(chemistry|physics|mathematics|biology)$"))
    app_bot.add_handler(CallbackQueryHandler(unit_handler, pattern="^unit[1-5]$"))
    print("Bot is polling...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
