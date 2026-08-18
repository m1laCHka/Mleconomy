# utils/logger.py
import logging
import sys

def setup_logger():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log", encoding="utf-8")
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()
