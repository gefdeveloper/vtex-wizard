from settings import config
from api import app
import uvicorn
from telegram import Update
from bot.ptb import ptb
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
)
from bot.handlers import error_handler, start, cancel_command, unknown_command
from bot.conversations.ean import ean_conv_handler
from bot.conversations.image import download_img_conv_handler
from bot.conversations.format_description import description_format_conv_handler
from bot.conversations.keywords import keyword_conv_handler
from bot.conversations.crop_image import crop_image_conv_handler
from bot.conversations.format_image_excel_file import raw_image_excel_file_conv_handler


def add_handlers(dp):
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(ean_conv_handler)
    dp.add_handler(description_format_conv_handler)
    dp.add_handler(download_img_conv_handler)
    dp.add_handler(raw_image_excel_file_conv_handler)
    dp.add_handler(keyword_conv_handler)
    dp.add_handler(crop_image_conv_handler)
    dp.add_error_handler(error_handler)
    dp.add_handler(CommandHandler("cancel", cancel_command))
    dp.add_handler(MessageHandler(filters.TEXT, unknown_command))


add_handlers(ptb)

if __name__ == "__main__":
    if config.DEBUG == "True":
        ptb.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
