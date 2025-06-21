import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['show_comments'] = False  # по умолчанию комментарии не показываются

    keyboard = [
        [InlineKeyboardButton("Выбрать группу", callback_data='choose_group')],
        [InlineKeyboardButton("Поиск по зачётке", callback_data='enter_record')],
        [InlineKeyboardButton("Комментарии: НЕТ", callback_data='toggle_comments')]
    ]
    await update.message.reply_text('Выберите действие:', reply_markup=InlineKeyboardMarkup(keyboard))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'toggle_comments':
        current = context.user_data.get('show_comments', False)
        context.user_data['show_comments'] = not current
        new_text = "Комментарии: ДА" if not current else "Комментарии: НЕТ"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Выбрать группу", callback_data='choose_group')],
            [InlineKeyboardButton("Поиск по зачётке", callback_data='enter_record')],
            [InlineKeyboardButton(new_text, callback_data='toggle_comments')]
        ])
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except Exception as e:
            print("Ошибка при обновлении клавиатуры:", e)

    elif query.data == 'choose_group':
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            await query.message.reply_text("Нет данных для отображения.")
            return

        groups = sorted(set(student["группа"] for student in data))
        buttons = [InlineKeyboardButton(group, callback_data=f"group_{group}") for group in groups]
        keyboard = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')])
        sent_message = await query.message.reply_text("Выберите группу:", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data['last_group_list_message_id'] = sent_message.message_id

    elif query.data.startswith('group_'):
        group = query.data.replace('group_', '')
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            await query.message.reply_text("Ошибка чтения данных.")
            return

        students = [s for s in data if s["группа"] == group]
        if not students:
            await query.message.reply_text("Группа не найдена.")
            return

        show_comments = context.user_data.get('show_comments', False)
        message_text = f"Студенты группы {group}:\n\n"
        for student in students:
            comment = f"\nКомментарий: {student['комментарий']}" if show_comments else ""
            message_text += (
                f"Зачётка: {student['номер_зачётки']}\n"
                f"Оценка: {student['оценка']}"
                f"{comment}\n"
                f"{'-' * 20}\n"
            )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data='back_message')]
        ])
        sent_message = await query.message.reply_text(message_text, reply_markup=keyboard)
        context.user_data['last_group_message_id'] = sent_message.message_id

    elif query.data == 'enter_record':
        await query.message.reply_text("Введите номер зачётки:")

    elif query.data == 'back_message':
        last_message_id = context.user_data.pop('last_group_message_id', None)
        if last_message_id:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=last_message_id)
            except Exception as e:
                print("Сообщение уже удалено или не найдено:", e)

    elif query.data == 'back_to_menu':
        last_message_id = context.user_data.pop('last_group_list_message_id', None)
        if last_message_id:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=last_message_id)
            except Exception as e:
                print("Сообщение уже удалено или не найдено:", e)


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    record_id = update.message.text.strip()
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        await update.message.reply_text("Ошибка чтения данных.")
        return

    show_comments = context.user_data.get('show_comments', False)
    student = next((item for item in data if item["номер_зачётки"] == record_id), None)
    if not student:
        await update.message.reply_text("Студент с такой зачёткой не найден.")
        return

    comment = f"\nКомментарий: {student['комментарий']}" if show_comments else ""
    response = (
        f"Информация о студенте:\n"
        f"Группа: {student['группа']}\n"
        f"Оценка: {student['оценка']}"
        f"{comment}"
    )
    await update.message.reply_text(response)


async def run_bot():
    from settings import TOKEN
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    print("🤖 Бот запущен...")
    await app.run_polling()