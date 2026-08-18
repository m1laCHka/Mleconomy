import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import config
from db import Database
from routers.users import router as users_router

bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
dp = Dispatcher()
db = Database(config.database_url)


async def main():
    await db.connect()
    await db.init_db()

    dp["db"] = db
    dp.include_router(users_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
