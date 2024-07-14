import logging
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

httpx_logger = logging.getLogger("httpx")

httpx_logger.setLevel(logging.WARNING)

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)
