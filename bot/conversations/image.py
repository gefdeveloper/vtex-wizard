from telegram import Update, error
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from common.log import logger
import os, asyncio, time
from bot.service import (
    save_images_from_excel,
    create_excel_non_working_urls,
    verificar_columnas_excel_de_imagenes,
    escape_string,
)
import shutil
from urllib.parse import urlparse
from bot.handlers import THREE, NINE

IMAGE_EXCEL_FILE, DOWNLOAD_IMAGE, SENDING_IMAGE, FAILED_URL_EXCEL_FAILED = range(4)


async def start_download_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Starts the conversation and asks images Excel file."""
    user_name = update.effective_user.first_name
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hi {user_name}. I will hold a conversation with you. "
        "Send /cancel_img to stop talking to me.\n\n",
    )
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open("./excel-files/examples/img-download-template.xlsx", "rb"),
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send me this template with the image URLs to download, with a maximum size of up to 20 MB.",
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
    if not verificar_columnas_excel_de_imagenes("./excel-files/image/image-url.xlsx"):
        await update.message.reply_text(
            "Invalid Excel format. Please resend the file in the correct format."
        )
        return IMAGE_EXCEL_FILE
    await update.message.reply_text("Excel file saved!")
    await update.message.reply_text(
        "Do you want to download images?/download or /skip_download"
    )

    return DOWNLOAD_IMAGE


async def download_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Download images from URLs provided in an Excel file."""
    try:
        user = update.message.from_user
        # Crear una carpeta con el nombre de usuario y la hora actual para guardar las imágenes
        folder_name = f"{user.first_name}_{int(time.time())}"
        folder_path = os.path.join("./media", folder_name)
        os.makedirs(folder_path, exist_ok=True)
        # Descargar las imágenes
        await update.message.reply_text("Downloading images...")

        save_images_from_excel("./excel-files/image/image-url.xlsx", folder_path)
        
        # Comprimir cada carpeta Lote_X en un archivo ZIP separado
        lote_folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f)) and f.startswith("Lote_")]
        
        for lote_folder in lote_folders:
            lote_folder_path = os.path.join(folder_path, lote_folder)
            shutil.make_archive("./media/zip/"+lote_folder, 'zip', lote_folder_path)
    except Exception as e:
        await update.message.reply_text(
            "An error occurred. Please correct the sent file and resend it. If the error persists, contact @gcasasolah for assistance."
        )
        return IMAGE_EXCEL_FILE
    context.user_data["image_folder_path"] = folder_path
    await update.message.reply_text(
        "Do you want me to send you the images compressed in a ZIP file? /send or /skip_send"
    )
    return SENDING_IMAGE


async def send_download_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Download zip file with downloaded images provided."""

    try:
        # Listar todos los archivos .zip en la carpeta zip
        zip_files = [f for f in os.listdir("./media/zip") if f.endswith(".zip")]

        # Enviar cada archivo zip
        for zip_file in zip_files:
            zip_file_path = os.path.join("./media/zip", zip_file)
            try:
                await context.bot.send_document(
                        chat_id=update.message.chat_id,
                        document=zip_file_path,
                        disable_notification=True,
                        write_timeout=60.0,
                    )
            except error.TimedOut as e:
                await update.message.reply_text(
                        f"A timed out error occurred while sending the file {zip_file}: {e}"
                    )
                continue
            except Exception as e:
                await update.message.reply_text(
                        f"An error occurred while sending the file {zip_file}: {e}"
                    )
            await asyncio.sleep(6)
    except Exception as e:
        await update.message.reply_text(
            f"An error occurred: {e}"
        )
        return FAILED_URL_EXCEL_FAILED
    
    await update.message.reply_text(
        "Do you want to Excel file with failed URLs?/failed_url or /cancel_img"
    )
    return FAILED_URL_EXCEL_FAILED


async def skip_download_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
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
    failed_urls_number = create_excel_non_working_urls(
        "./excel-files/image/image-url.xlsx",
        "./excel-files/image",
    )
    if failed_urls_number == 0:
        await update.message.reply_text("Failed URLs not found.")
    else:
        await update.message.reply_text(f"We found {failed_urls_number} failed URLs.")
        await context.bot.send_document(
            chat_id=update.message.chat_id,
            document=open("./excel-files/image/failed_urls.xlsx", "rb"),
        )

    if (
        "image_folder_path" in context.user_data
        and context.user_data["image_folder_path"] != ""
    ):
        # Delete the downloaded image folder
        shutil.rmtree(context.user_data["image_folder_path"])
        context.user_data["image_folder_path"] = ""
        
    # List all .zip files in zip folder
    zip_files = [f for f in os.listdir("./media/zip") if f.endswith(".zip")]

    # Delete the .zip files from zip folder
    for zip_file in zip_files:
        zip_file_path = os.path.join("./media/zip", zip_file)
    
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
    
    user = update.message.from_user
    logger.info("User %s canceled the image conversation.", user.first_name)
    await update.message.reply_text("Bye! I hope we can talk again some day.")
    return ConversationHandler.END


async def cancel_download_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancels and ends the conversation."""
    # Check if the image folder path exists in user data
    if (
        "image_folder_path" in context.user_data
        and context.user_data["image_folder_path"] != ""
    ):
        # Delete the downloaded image folder
        shutil.rmtree(context.user_data["image_folder_path"])
        context.user_data["image_folder_path"] = ""

    # List all .zip files in zip folder
    zip_files = [f for f in os.listdir("./media/zip") if f.endswith(".zip")]

    # Delete the .zip files from zip folder
    for zip_file in zip_files:
        zip_file_path = os.path.join("./media/zip", zip_file)
    
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
    
    user_name = update.effective_user.first_name
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    logger.info("User %s canceled the image conversation.", user_name)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bye! I hope we can talk again some day."
    )

    return ConversationHandler.END


download_img_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_download_image, pattern="^" + str(THREE) + "$")
    ],
    states={
        IMAGE_EXCEL_FILE: [
            MessageHandler(filters.ATTACHMENT, save_image_excel),
        ],
        DOWNLOAD_IMAGE: [
            CommandHandler("download", download_image),
            CommandHandler("skip_download", skip_download_image),
        ],
        SENDING_IMAGE: [
            CommandHandler("send", send_download_image),
            CommandHandler("skip_send", skip_send_image),
        ],
        FAILED_URL_EXCEL_FAILED: [
            CommandHandler("failed_url", send_failed_urls_excel_file),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_download_image, pattern="^" + str(NINE) + "$"),
        CommandHandler("cancel_img", cancel_download_image),
    ],
)
