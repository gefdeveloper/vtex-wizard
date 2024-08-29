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
    verificar_columnas_excel_de_generacion_descripciones,
    generation_description_exce_file,
)

DESCRIPTION_GENERATION_EXCEL_FILE = range(1)
from bot.handlers import SIX, TWELVE


async def start_generation_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks excel file with description."""
    user_name = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        text=f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_des to stop talking to me.\n\n",
        chat_id=update.effective_chat.id,
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/examples/description-template.xlsx", "rb"),
    )
    await context.bot.send_message(
        text="Please send me this template with the list of products, with a maximum size of up to 20 MB.",
        chat_id=update.effective_chat.id,
    )
    return DESCRIPTION_GENERATION_EXCEL_FILE


async def create_descriptions_excel_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.message.from_user
    if (
        update.message.effective_attachment.mime_type
        != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        await update.message.reply_text("Please send an Excel file.")
        return DESCRIPTION_GENERATION_EXCEL_FILE

    new_file = await update.message.effective_attachment.get_file()
    await new_file.download_to_drive("./excel-files/descriptions/products-list.xlsx")
    logger.info("File of %s: %s", user.first_name, "products-list.xlsx")

    if not verificar_columnas_excel_de_generacion_descripciones(
        "./excel-files/descriptions/products-list.xlsx"
    ):
        await update.message.reply_text(
            "Invalid Excel format. Please resend the file in the correct format."
        )
        return DESCRIPTION_GENERATION_EXCEL_FILE

    await update.message.reply_text("Excel file saved!")
    try:
        generation_description_exce_file()
    except Exception as e:
        await update.message.reply_text(
            "An error occurred. Please correct the sent file and resend it. If the error persists, contact @gcasasolah for assistance."
        )
        return DESCRIPTION_GENERATION_EXCEL_FILE
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/descriptions/descriptions-list.xlsx", "rb"),
    )
    await update.message.reply_text(
        "The descriptions have been converted and stored in descriptions-list.xlsx."
    )
    logger.info("User %s canceled the description generation conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def cancel_generation_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    logger.info("User %s canceled the description generation conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")

    return ConversationHandler.END


description_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_generation_description, pattern="^" + str(SIX) + "$")
    ],
    states={
        DESCRIPTION_GENERATION_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, create_descriptions_excel_file)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_generation_description, pattern="^" + str(TWELVE) + "$"),
        CommandHandler("cancel_des", cancel_generation_description),
    ],
)
