from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from common.log import logger
from bot.service import generate_keywords

KEYWORDS_EXCEL_FILE = range(1)


async def start_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks excel file with description."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_key to stop talking to me.\n\n"
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/examples/keywords-template.xlsx", "rb"),
    )
    await update.message.reply_text(
        "Please send me this template with the product names and categories, with a maximum size of up to 20 MB."
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
    await update.message.reply_text("Excel file saved!")
    generate_keywords()
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


async def cancel_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the keyword conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")

    return ConversationHandler.END


keyword_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start_key", start_keyword)],
    states={
        KEYWORDS_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, create_keywords_excel_file)
        ],
    },
    fallbacks=[CommandHandler("cancel_key", cancel_description)],
)
