# main.py

import asyncio
import logging
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import db
from database.models import init_db
from handlers import start, profile, help

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    """Запуск бота"""
    # Подключаемся к БД
    logger.info("🔗 Подключение к БД...")
    await db.connect()
    await init_db(db)
    
    # Инициализируем бота
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем маршруты
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(help.router)
    
    logger.info("✅ Бот запущен!")
    
    # Запускаем polling
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")
    finally:
        await db.disconnect()
        await bot.session.close()
        logger.info("🔌 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
