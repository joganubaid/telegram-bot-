# Updated start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.effective_user.id} started the bot")
    keyboard = [
        [InlineKeyboardButton("Chemistry", callback_data="chemistry")],
        [InlineKeyboardButton("Physics", callback_data="physics")],
        [InlineKeyboardButton("Mathematics", callback_data="mathematics")],
        [InlineKeyboardButton("Biology", callback_data="biology")],
        [InlineKeyboardButton("📄 End Sem PYQ", callback_data="end_sem")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 Select a subject or view End Sem PYQs:", reply_markup=reply_markup)

# Handle button click for 'End Sem PYQ'
async def end_sem_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subjects = [
        ("Biology", "pyq_biology"),
        ("Mathematics", "pyq_mathematics"),
        ("Physics", "pyq_physics"),
        ("Communication Skill", "pyq_communication_skill"),
        ("Electrical Engineering", "pyq_electrical_engineering"),
        ("Mechanical Engineering", "pyq_mechanical_engineering"),
        ("Environmental Science", "pyq_environmental_science"),
    ]

    keyboard = [[InlineKeyboardButton(name, callback_data=cb)] for name, cb in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📝 Choose a subject for End Sem PYQ:", reply_markup=reply_markup)

# Handle selection of a specific PYQ subject
async def send_pyq_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subject_map = {
        "pyq_biology": "biology_end_sem_2024.pdf",
        "pyq_mathematics": "mathematics_end_sem_2024.pdf",
        "pyq_physics": "physics_end_sem_2024.pdf",
        "pyq_communication_skill": "communication_skill_end_sem_2024.pdf",
        "pyq_electrical_engineering": "electrical_engineering_end_sem_2024.pdf",
        "pyq_mechanical_engineering": "mechanical_engineering_end_sem_2024.pdf",
        "pyq_environmental_science": "environmental_science_end_sem_2024.pdf",
    }

    file_name = subject_map.get(query.data)
    file_path = os.path.join(PDF_FOLDER, file_name)

    if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            await query.message.reply_document(document=f)
    else:
        await query.message.reply_text("❌ PDF not found.")

