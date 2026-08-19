# main.py (обновленный)

import asyncio
import logging
from aiohttp import web
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, PORT
from database.db import db
from database.models import init_db
from handlers import start, profile, help, admin, roulette, duel
from utils.logger import logger

async def health_check(request):
    return web.Response(text="Bot is running!")

async def main():
    bot = None
    try:
        logger.info("🔗 Подключение к БД...")
        await db.connect()
        
        logger.info("🗄️ Инициализация БД...")
        await init_db(db)
        
        logger.info("🤖 Инициализация бота...")
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрируем маршруты
        dp.include_router(start.router)
        dp.include_router(profile.router)
        dp.include_router(help.router)
        dp.include_router(admin.router)
        dp.include_router(roulette.router)
        dp.include_router(duel.router)
        
        # Веб-сервер для Render
        app = web.Application()
        app.router.add_get("/", health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        
        logger.info(f"✅ Бот запущен на порту {PORT}!")
        
        # Запускаем polling с drop_pending_updates
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        if bot:
            await bot.session.close()
        await db.disconnect()
        logger.info("🔌 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
