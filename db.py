import asyncpg


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=10)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def init_db(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                custom_nick TEXT DEFAULT NULL,
                gender TEXT DEFAULT NULL,
                coins BIGINT NOT NULL DEFAULT 500,
                stars INT NOT NULL DEFAULT 10,
                is_vip BOOLEAN NOT NULL DEFAULT FALSE,
                vip_until TIMESTAMP DEFAULT NULL,
                is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
                insurance BOOLEAN NOT NULL DEFAULT FALSE,
                family_id BIGINT DEFAULT NULL,
                spouse_id BIGINT DEFAULT NULL,
                divorce_until DATE DEFAULT NULL,
                daily_stars_transferred INT NOT NULL DEFAULT 0,
                last_transfer_date DATE DEFAULT NULL,
                last_prize_date DATE DEFAULT NULL,
                wins INT NOT NULL DEFAULT 0,
                losses INT NOT NULL DEFAULT 0,
                total_games INT NOT NULL DEFAULT 0,
                daily_net_win INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """)
