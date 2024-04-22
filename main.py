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
from bot.handlers import error_handler, text_handler, unknown_command
from bot.commands.ean import ean_conv_handler
from bot.commands.description import description_conv_handler
from bot.commands.image import download_img_conv_handler
from bot.commands.format import raw_image_excel_file_conv_handler


def add_handlers(dp):
    dp.add_handler(CommandHandler("menu", text_handler))
    dp.add_handler(ean_conv_handler)
    dp.add_handler(description_conv_handler)
    dp.add_handler(download_img_conv_handler)
    dp.add_handler(raw_image_excel_file_conv_handler)
    dp.add_error_handler(error_handler)
    dp.add_handler(MessageHandler(filters.COMMAND, unknown_command))

add_handlers(ptb)

if __name__ == "__main__":
    if config.DEBUG == "True":
        ptb.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
