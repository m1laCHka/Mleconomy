# database/models.py

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    gender VARCHAR(10),
    balance BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_FAMILIES_TABLE = """
CREATE TABLE IF NOT EXISTS families (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    family_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

async def init_db(db):
    """Инициализировать БД"""
    try:
        await db.execute(CREATE_USERS_TABLE)
        await db.execute(CREATE_FAMILIES_TABLE)
        print("✅ Таблицы созданы")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
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
        print(f"❌ Ошибка проверки пользователя: {e}")
        return False

async def create_user(db, user_id: int, username: str, gender: str = None):
    """Создать пользователя"""
    try:
        await db.execute(
            "INSERT INTO users (user_id, username, gender) VALUES ($1, $2, $3)",
            user_id, username, gender
        )
        print(f"✅ Пользователь {user_id} создан")
    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        raise

async def get_user(db, user_id: int):
    """Получить профиль пользователя"""
    try:
        user = await db.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )
        return user
    except Exception as e:
        print(f"❌ Ошибка получения профиля: {e}")
        return None

async def update_user_gender(db, user_id: int, gender: str):
    """Обновить пол пользователя"""
    try:
        await db.execute(
            "UPDATE users SET gender = $1 WHERE user_id = $2",
            gender, user_id
        )
        print(f"✅ Пол пользователя {user_id} обновлён на {gender}")
    except Exception as e:
        print(f"❌ Ошибка обновления пола: {e}")
        raise
