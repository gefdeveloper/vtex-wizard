from common.log import logger
from bot.service import generate_random_numbers, save_to_excel
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram import ReplyKeyboardMarkup

EAN_NUMBER = range(1)

async def start_ean(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about the method of EAN codes generation."""
    user_name = update.effective_user.first_name
    message_text = f"Hi {user_name}, please choose how you want to generate EAN codes:\n"
    message_text += "/excel - Generate EAN codes as Excel file.\n"
    message_text += "/message - Generate EAN codes as message."

    await update.message.reply_text(message_text)

    context.user_data["generate_method"] = None
    
    return EAN_NUMBER


async def start_ean_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation for generating EAN codes as Excel file."""
    context.user_data["generate_method"] = "excel"
    await update.message.reply_text("How many EAN codes do you want to generate?")
    return EAN_NUMBER


async def start_ean_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation for generating EAN codes as message."""
    context.user_data["generate_method"] = "message"
    await update.message.reply_text("How many EAN codes do you want to generate?")
    return EAN_NUMBER


async def ean_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the number of EAN codes to generate and ends the conversation."""
    try:
        ean_code_quantity = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return EAN_NUMBER

    if context.user_data.get("generate_method") == "excel":
        # Generate EAN codes and send as Excel file
        random_numbers_list = generate_random_numbers(ean_code_quantity)
        save_to_excel(random_numbers_list)
        await update.message.reply_text(
            f"{ean_code_quantity} EAN codes have been generated and stored in an ean_codes.xlsx."
        )
        # Send the generated Excel file
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open("./excel-files/ean/ean_codes.xlsx", "rb"),
        )
    else:
        random_numbers_list = generate_random_numbers(ean_code_quantity)
        message = "Here are your EAN codes:\n"
        message += "\n".join(random_numbers_list)
        await update.message.reply_text(message)

    return ConversationHandler.END


async def cancel_ean(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")

    return ConversationHandler.END


ean_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start_ean", start_ean)],
    states={
        EAN_NUMBER: [
            CommandHandler("excel", start_ean_excel),
            CommandHandler("message", start_ean_message),
            MessageHandler(filters.TEXT & ~filters.COMMAND, ean_number),
        ],
    },
    fallbacks=[CommandHandler("cancel_ean", cancel_ean)],
)
