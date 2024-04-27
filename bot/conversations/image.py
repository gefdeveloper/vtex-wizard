from telegram import Update, error
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from common.log import logger
import os, asyncio, time
from bot.service import save_images_from_excel, create_excel_non_working_urls
import shutil

IMAGE_EXCEL_FILE, DOWNLOAD_IMAGE, SENDING_IMAGE, FAILED_URL_EXCEL_FAILED = range(4)


async def start_download_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Starts the conversation and asks images Excel file."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_img to stop talking to me.\n\n"
        "Please, send me the Excel file with image URLs of up to 20MB in size."
    )

    return IMAGE_EXCEL_FILE


async def save_image_excel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save Excel file with image URLs."""
    user = update.message.from_user

    if (
        update.message.effective_attachment.mime_type
        != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        await update.message.reply_text("Please send an Excel file.")
        return IMAGE_EXCEL_FILE

    new_file = await update.message.effective_attachment.get_file()

    await new_file.download_to_drive("./excel-files/image/image-url.xlsx")

    logger.info("File of %s: %s", user.first_name, "image-url.xlsx")
    await update.message.reply_text("Excel file saved!")
    await update.message.reply_text("Do you want to download images?/download or /skip_download")

    return DOWNLOAD_IMAGE


async def download_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Download images from URLs provided in an Excel file."""
    await update.message.reply_text("Downloading images...")
    user = update.message.from_user
    # Crear una carpeta con el nombre de usuario y la hora actual para guardar las imágenes
    folder_name = f"{user.first_name}_{int(time.time())}"
    folder_path = os.path.join("./media", folder_name)
    os.makedirs(folder_path, exist_ok=True)
    # Descargar las imágenes
    save_images_from_excel("./excel-files/image/image-url.xlsx", folder_path)
    context.user_data["image_folder_path"] = folder_path
    await update.message.reply_text("Images downloaded succesfully")
    await update.message.reply_text(
        "Do you want me to send you the images?/send or /skip_send"
    )
    return SENDING_IMAGE


async def send_download_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Download images from URLs provided in an Excel file."""
    # Enviar las imágenes
    folder_path = context.user_data["image_folder_path"]
    
    image_files = os.listdir(folder_path)
    for file_name in image_files:
        image_path = os.path.join(folder_path, file_name)
        try:
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=image_path,
                disable_notification=True,
                write_timeout=35.0,
            )
        except error.TimedOut as e:
            await update.message.reply_text(
                f"Sending the image {file_name} timed out: {e}"
            )
            continue
        except Exception as e:
            await update.message.reply_text(
                f"An error occurred while sending the image {file_name}: {e}"
            )
        await asyncio.sleep(3)
    await update.message.reply_text(
        "Do you want to Excel file with failed URLs?/failed_url or /cancel_img"
    )
    return FAILED_URL_EXCEL_FAILED


async def skip_download_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Download images from URLs provided in an Excel file."""
    await update.message.reply_text(
        "Do you want to Excel file with failed URLs?/failed_url or /cancel_img"
    )
    return FAILED_URL_EXCEL_FAILED


async def skip_send_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Download images from URLs provided in an Excel file."""
    await update.message.reply_text(
        "Do you want to Excel file with failed URLs?/failed_url or /cancel_img"
    )
    return FAILED_URL_EXCEL_FAILED


async def send_failed_urls_excel_file(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Download images from URLs provided in an Excel file."""
    # Crear un excel con las urls que no funcionan
    await update.message.reply_text("Sending failed_urls.xlsx")
    create_excel_non_working_urls(
        "./excel-files/image/image-url.xlsx",
        "./excel-files/image",
    )
    # Enviar el excel con las urls que no funcionan
    await context.bot.send_document(
        chat_id=update.message.chat_id,
        document=open("./excel-files/image/failed_urls.xlsx", "rb"),
    )

    return ConversationHandler.END


async def cancel_download_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancels and ends the conversation."""
    #Eliminar carpeta de imagenes descargadas
    if context.user_data["image_folder_path"]:
        shutil.rmtree(context.user_data["image_folder_path"])
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")

    return ConversationHandler.END


download_img_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start_img", start_download_image)],
    states={
        IMAGE_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, save_image_excel),   
        ],
        DOWNLOAD_IMAGE:[
            CommandHandler("download", download_image),
            CommandHandler("skip_download", skip_download_image),
        ],
        SENDING_IMAGE:[
            CommandHandler("send", send_download_image),
            CommandHandler("skip_send", skip_send_image),
        ],
        FAILED_URL_EXCEL_FAILED:[
            CommandHandler("failed_url", send_failed_urls_excel_file),
        ]
    },
    fallbacks=[CommandHandler("cancel_img", cancel_download_image)],
)
