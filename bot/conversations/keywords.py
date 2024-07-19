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
from bot.service import (
    generate_keywords_excel_file,
    verificar_columnas_excel_de_keywords,
)
from bot.handlers import FIVE, ELEVEN

KEYWORDS_EXCEL_FILE = range(1)


async def start_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks excel file with description."""
    user_name = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_key to stop talking to me.\n\n",
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/examples/keywords-template.xlsx", "rb"),
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send me this template with the product names and categories, with a maximum size of up to 20 MB.",
    )
    return KEYWORDS_EXCEL_FILE


async def create_keywords_excel_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.message.from_user
    if (
        update.message.effective_attachment.mime_type
        != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        await update.message.reply_text("Please send an Excel file.")
        return KEYWORDS_EXCEL_FILE

    new_file = await update.message.effective_attachment.get_file()
    await new_file.download_to_drive("./excel-files/keywords/products-list.xlsx")
    logger.info("File of %s: %s", user.first_name, "products-list.xlsx")
    if not verificar_columnas_excel_de_keywords(
        "./excel-files/keywords/products-list.xlsx"
    ):
        await update.message.reply_text(
            "Invalid Excel format. Please resend the file in the correct format."
        )
        return KEYWORDS_EXCEL_FILE
    await update.message.reply_text("Excel file saved!")
    try:
        generate_keywords_excel_file()
    except Exception as e:
        await update.message.reply_text(
            "An error occurred. Please correct the sent file and resend it. If the error persists, contact @gcasasolah for assistance."
        )
        return KEYWORDS_EXCEL_FILE
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/keywords/keywords-list.xlsx", "rb"),
    )
    await update.message.reply_text(
        "The keywords have been converted and stored in keywords-list.xlsx."
    )
    logger.info("User %s canceled the keyword conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def cancel_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user_name = update.effective_user.first_name
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    logger.info("User %s canceled the keyword conversation.", user_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END


keyword_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_keyword, pattern="^" + str(FIVE) + "$")],
    states={
        KEYWORDS_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, create_keywords_excel_file)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(start_keyword, pattern="^" + str(ELEVEN) + "$"),
        CommandHandler("cancel_key", cancel_keyword),
    ],
)
