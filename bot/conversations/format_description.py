from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from common.log import logger
from bot.service import change_html_to_text, verificar_columnas_excel_de_descripciones
from bot.handlers import TWO, EIGHT

DESCRIPTION_EXCEL_FILE = range(1)


async def start_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks excel file with description."""
    user_name = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        text=f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_des_format to stop talking to me.\n\n",
        chat_id=update.effective_chat.id,
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/examples/raw-description-template.xlsx", "rb"),
    )

    await context.bot.send_message(
        text="Please send me this template with the descriptions to correct, with a maximum size of up to 20 MB.",
        chat_id=update.effective_chat.id,
    )
    return DESCRIPTION_EXCEL_FILE


async def format_descriptions_excel_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.message.from_user
    if (
        update.message.effective_attachment.mime_type
        != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        await update.message.reply_text("Please send an Excel file.")
        return DESCRIPTION_EXCEL_FILE

    new_file = await update.message.effective_attachment.get_file()
    await new_file.download_to_drive("./excel-files/descriptions/description-html.xlsx")
    logger.info("File of %s: %s", user.first_name, "description-html.xlsx")
    if not verificar_columnas_excel_de_descripciones(
        "./excel-files/descriptions/description-html.xlsx"
    ):
        await update.message.reply_text(
            "Invalid Excel format. Please resend the file in the correct format."
        )
        return DESCRIPTION_EXCEL_FILE
    await update.message.reply_text("Excel file saved!")
    try:
        change_html_to_text()
    except Exception as e:
        await update.message.reply_text(
            "An error occurred. Please correct the sent file and resend it. If the error persists, contact @gcasasolah for assistance."
        )
        return DESCRIPTION_EXCEL_FILE
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/descriptions/description-text.xlsx", "rb"),
    )
    await update.message.reply_text(
        "The descriptions have been converted and stored in description-text.xlsx."
    )
    logger.info("User %s canceled the description conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def cancel_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user_name = update.effective_user.first_name
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    logger.info("User %s canceled the description conversation.", user_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END


description_format_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_description, pattern="^" + str(TWO) + "$")
    ],
    states={
        DESCRIPTION_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, format_descriptions_excel_file)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_description, pattern="^" + str(EIGHT) + "$"),
        CommandHandler("cancel_des_format", cancel_description),
    ],
)
