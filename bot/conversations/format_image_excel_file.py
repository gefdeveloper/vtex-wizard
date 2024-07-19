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
from bot.service import format_image_excel_file, verificar_columnas_excel_de_imagenes
from bot.handlers import FOUR, TEN

RAW_IMAGE_EXCEL_FILE = range(1)


async def start_format_image_excel_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Starts the conversation and asks images Excel file."""
    user_name = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_format to stop talking to me.\n\n",
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open(
            "./excel-files/examples/unformatted-image-URLs-template.xlsx", "rb"
        ),
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send me this template with the image URLs to format, with a maximum size of up to 20 MB.",
    )
    return RAW_IMAGE_EXCEL_FILE


async def format_raw_image_excel_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Save and format images Excel file."""
    user = update.message.from_user
    if (
        update.message.effective_attachment.mime_type
        != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        await update.message.reply_text("Please send an Excel file.")
        return RAW_IMAGE_EXCEL_FILE

    new_file = await update.message.effective_attachment.get_file()
    await new_file.download_to_drive("./excel-files/format/raw-excel-file.xlsx")
    logger.info("File of %s: %s", user.first_name, "raw-excel-file.xlsx")
    if not verificar_columnas_excel_de_imagenes("./excel-files/image/image-url.xlsx"):
        await update.message.reply_text(
            "Invalid Excel format. Please resend the file in the correct format."
        )
        return RAW_IMAGE_EXCEL_FILE
    await update.message.reply_text("Excel file saved!")
    try:
        format_image_excel_file()
    except Exception as e:
        await update.message.reply_text(
            "An error occurred. Please correct the sent file and resend it. If the error persists, contact @gcasasolah for assistance."
        )
        return RAW_IMAGE_EXCEL_FILE
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/format/formatted-excel-file.xlsx", "rb"),
    )
    await update.message.reply_text(
        "The formatted Excel file is formatted-excel-file.xlsx."
    )
    logger.info("User %s canceled the format conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def cancel_format_image_excel_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancels and ends the conversation."""
    user_name = update.effective_user.first_name
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    logger.info("User %s canceled the format conversation.", user_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bye! I hope we can talk again some day."
    )
    
    return ConversationHandler.END


raw_image_excel_file_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            start_format_image_excel_file, pattern="^" + str(FOUR) + "$"
        )
    ],
    states={
        RAW_IMAGE_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, format_raw_image_excel_file)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            cancel_format_image_excel_file, pattern="^" + str(TEN) + "$"
        ),
        CommandHandler("cancel_format", cancel_format_image_excel_file),
    ],
)
