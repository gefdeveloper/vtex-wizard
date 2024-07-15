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
from bot.service import save_cropped_image
from bot.handlers import SIX, TWELVE

(
    GET_IMAGE,
    GET_TOP_MARGIN,
    GET_BOTTOM_MARGIN,
    GET_RIGHT_MARGIN,
    GET_LEFT_MARGIN,
    CROP_IMAGE,
) = range(6)


async def start_crop_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks excel file with description."""
    user_name = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_crop_image to stop talking to me.\n\n",
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send me the image to crop, with a maximum size of 20 MB.",
    )
    return GET_IMAGE


async def save_image_to_crop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo to crop."""
    user = update.message.from_user

    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive("./media/images/image-to-crop.jpg")
    logger.info("File of %s: %s", user.first_name, "image-to-crop.jpg")
    await update.message.reply_text("Image saved!")
    await update.message.reply_text("What is top margin in pixels?")
    return GET_TOP_MARGIN


async def save_top_margin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the number of bottom margin."""
    try:
        top_margin = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return GET_TOP_MARGIN
    context.user_data["top_margin"] = top_margin
    await update.message.reply_text("Top margin saved!")
    await update.message.reply_text("What is bottom margin in pixels?")
    return GET_BOTTOM_MARGIN


async def save_bottom_margin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the number of bottom margin."""
    try:
        bottom_margin = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return GET_BOTTOM_MARGIN
    context.user_data["bottom_margin"] = bottom_margin
    await update.message.reply_text("Bottom margin saved!")
    await update.message.reply_text("What is right margin in pixels?")
    return GET_RIGHT_MARGIN


async def save_right_margin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the number of right margin."""
    try:
        right_margin = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return GET_RIGHT_MARGIN
    context.user_data["right_margin"] = right_margin
    await update.message.reply_text("Right margin saved!")
    await update.message.reply_text("What is left margin in pixels?")
    return GET_LEFT_MARGIN


async def save_left_margin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the number of left margin."""
    try:
        left_margin = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return GET_LEFT_MARGIN
    context.user_data["left_margin"] = left_margin
    await update.message.reply_text("Left margin saved!")
    await update.message.reply_text(
        "Do you want to crop the image? /yes or /cancel_crop_image"
    )
    return CROP_IMAGE


async def crop_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Crop image."""
    top_margin = context.user_data["top_margin"]
    bottom_margin = context.user_data["bottom_margin"]
    right_margin = context.user_data["right_margin"]
    left_margin = context.user_data["left_margin"]
    save_cropped_image(bottom_margin, top_margin, left_margin, right_margin)
    await update.message.reply_text("Sending cropped image ...")
    await context.bot.send_document(
        chat_id=update.message.chat_id,
        document="./media/images/cropped-image.jpg",
        disable_notification=True,
        write_timeout=35.0,
    )
    user = update.message.from_user
    logger.info("User %s canceled the ean conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def cancel_crop_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user_name = update.effective_user.first_name
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    logger.info("User %s canceled the crop-image conversation.", user_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END


crop_image_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_crop_image, pattern="^" + str(SIX) + "$")],
    states={
        GET_IMAGE: [
            MessageHandler(filters.PHOTO, save_image_to_crop),
        ],
        GET_TOP_MARGIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_top_margin),
        ],
        GET_BOTTOM_MARGIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_bottom_margin),
        ],
        GET_RIGHT_MARGIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_right_margin),
        ],
        GET_LEFT_MARGIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_left_margin),
        ],
        CROP_IMAGE: [
            CommandHandler("yes", crop_image),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_crop_image, pattern="^" + str(TWELVE) + "$"),
        CommandHandler("cancel_crop_image", cancel_crop_image),
    ],
)
