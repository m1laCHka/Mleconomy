# database/models.py

import logging

logger = logging.getLogger(__name__)

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    custom_nick VARCHAR(255) DEFAULT NULL,
    gender VARCHAR(10),
    balance BIGINT DEFAULT 500,
    stars INT DEFAULT 10,
    is_vip BOOLEAN DEFAULT FALSE,
    vip_until TIMESTAMP DEFAULT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    insurance BOOLEAN DEFAULT FALSE,
    family_id INT DEFAULT NULL,
    spouse_id BIGINT DEFAULT NULL,
    divorce_until DATE DEFAULT NULL,
    daily_stars_transferred INT DEFAULT 0,
    last_transfer_date DATE DEFAULT NULL,
    last_prize_date DATE DEFAULT NULL,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    total_games INT DEFAULT 0,
    daily_net_win INT DEFAULT 0,
    roulette_games INT DEFAULT 0,
    roulette_wins INT DEFAULT 0,
    duel_games INT DEFAULT 0,
    duel_wins INT DEFAULT 0,
    cat_games INT DEFAULT 0,
    cat_wins INT DEFAULT 0,
    casino_games INT DEFAULT 0,
    casino_wins INT DEFAULT 0,
    quests_completed INT DEFAULT 0,
    quest1_done BOOLEAN DEFAULT FALSE,
    quest2_done BOOLEAN DEFAULT FALSE,
    quest3_done BOOLEAN DEFAULT FALSE,
    quest4_done BOOLEAN DEFAULT FALSE,
    quest5_done BOOLEAN DEFAULT FALSE,
    quest_bonus_claimed BOOLEAN DEFAULT FALSE,
    tournament_fee_paid BOOLEAN DEFAULT FALSE,
    tournament_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_date DATE DEFAULT CURRENT_DATE
);
"""

CREATE_FAMILIES_TABLE = """
CREATE TABLE IF NOT EXISTS families (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL,
    name VARCHAR(255) DEFAULT NULL,
    score INT DEFAULT 0,
    created_at DATE NOT NULL,
    top1_count INT DEFAULT 0,
    last_anniversary_month INT DEFAULT 0
);
"""

CREATE_CHILDREN_TABLE = """
CREATE TABLE IF NOT EXISTS children (
    id SERIAL PRIMARY KEY,
    family_id INT NOT NULL,
    child_id BIGINT NOT NULL,
    FOREIGN KEY (family_id) REFERENCES families(id)
);
"""

CREATE_ACHIEVEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS achievements (
    user_id BIGINT NOT NULL,
    ach_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_id, ach_id)
);
"""

CREATE_PROMOS_TABLE = """
CREATE TABLE IF NOT EXISTS promos (
    code VARCHAR(50) PRIMARY KEY,
    stars INT DEFAULT 0,
    coins BIGINT DEFAULT 0,
    max_uses INT DEFAULT 100,
    uses INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_USER_PROMOS_TABLE = """
CREATE TABLE IF NOT EXISTS user_promos (
    user_id BIGINT NOT NULL,
    code VARCHAR(50) NOT NULL,
    PRIMARY KEY (user_id, code)
);
"""

async def init_db(db):
    """Инициализировать все таблицы БД"""
    try:
        # Удаляем старую таблицу users (если есть проблемы)
        await db.execute("DROP TABLE IF EXISTS users CASCADE")
        await db.execute("DROP TABLE IF EXISTS families CASCADE")
        await db.execute("DROP TABLE IF EXISTS children CASCADE")
        await db.execute("DROP TABLE IF EXISTS achievements CASCADE")
        await db.execute("DROP TABLE IF EXISTS promos CASCADE")
        await db.execute("DROP TABLE IF EXISTS user_promos CASCADE")
        
        # Создаем все таблицы заново
        await db.execute(CREATE_USERS_TABLE)
        await db.execute(CREATE_FAMILIES_TABLE)
        await db.execute(CREATE_CHILDREN_TABLE)
        await db.execute(CREATE_ACHIEVEMENTS_TABLE)
        await db.execute(CREATE_PROMOS_TABLE)
        await db.execute(CREATE_USER_PROMOS_TABLE)
        
        logger.info("✅ Все таблицы созданы успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise

async def user_exists(db, user_id: int) -> bool:
    """Проверить существование пользователя"""
    try:
        result = await db.fetchval(
            "SELECT user_id FROM users WHERE user_id = $1",
            user_id
        )
        return result is not None
    except Exception as e:
        logger.error(f"❌ Ошибка проверки пользователя: {e}")
        return False

async def create_user(db, user_id: int, username: str, gender: str = None):
    """Создать нового пользователя"""
    try:
        # Проверяем, какие поля есть в таблице
        await db.execute(
            """
            INSERT INTO users (user_id, username, gender, balance, stars)
            VALUES ($1, $2, $3, 500, 10)
            """,
            user_id, username, gender
        )
        logger.info(f"✅ Пользователь {user_id} создан с балансом 500 монет и 10 звёзд")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания пользователя: {e}")
        raise

async def get_user(db, user_id: int):
    """Получить полный профиль пользователя"""
    try:
        user = await db.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )
        return user
    except Exception as e:
        logger.error(f"❌ Ошибка получения профиля: {e}")
        return None

async def update_user_gender(db, user_id: int, gender: str):
    """Обновить пол пользователя"""
    try:
        await db.execute(
            "UPDATE users SET gender = $1 WHERE user_id = $2",
            gender, user_id
        )
        logger.info(f"✅ Пол пользователя {user_id} обновлён на {gender}")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления пола: {e}")
        raise

async def update_balance(db, user_id: int, amount: int):
    """Обновить баланс пользователя"""
    try:
        await db.execute(
            "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
            amount, user_id
        )
        logger.info(f"✅ Баланс пользователя {user_id} обновлён на {amount}")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления баланса: {e}")
        raise

async def update_stars(db, user_id: int, amount: int):
    """Обновить звёзды пользователя"""
    try:
        await db.execute(
            "UPDATE users SET stars = stars + $1 WHERE user_id = $2",
            amount, user_id
        )
        logger.info(f"✅ Звёзды пользователя {user_id} обновлены на {amount}")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления звёзд: {e}")
        raise
