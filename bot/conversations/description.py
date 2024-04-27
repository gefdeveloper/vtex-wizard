from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from common.log import logger
from bot.service import change_html_to_text

DESCRIPTION_EXCEL_FILE = range(1)


async def start_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks excel file with description."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_des to stop talking to me.\n\n"
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/examples/description-template.xlsx", "rb"),
    )
    await update.message.reply_text(
        "Please send me this template with the descriptions to correct, with a maximum size of up to 20 MB."
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
    await update.message.reply_text("Excel file saved!")
    change_html_to_text()
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/descriptions/description-text.xlsx", "rb"),
    )
    await update.message.reply_text(
        "The descriptions have been converted and stored in description-text.xlsx."
    )
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def cancel_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")

    return ConversationHandler.END


description_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start_des", start_description)],
    states={
        DESCRIPTION_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, format_descriptions_excel_file)
        ],
    },
    fallbacks=[CommandHandler("cancel_des", cancel_description)],
)
