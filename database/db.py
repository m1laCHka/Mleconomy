# database/db.py
import asyncpg
import logging
from config import DATABASE_URL

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("✅ Подключение к PostgreSQL успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Отключение от PostgreSQL")
    
    async def execute(self, query, *args):
        """Выполнить SQL запрос"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetchval(self, query, *args):
        """Получить одно значение"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def fetchrow(self, query, *args):
        """Получить одну строку"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch(self, query, *args):
        """Получить несколько строк"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

# Создаем экземпляр базы данных
db = Database()
