# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID администратора
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL")

# ID чата для уведомлений
CHAT_ID = os.getenv("CHAT_ID", "")

# Порт для веб-сервера
PORT = int(os.getenv("PORT", "8080"))

# Проверка наличия обязательных переменных
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавь его в переменные окружения на Render")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не найден! Добавь его в переменные окружения на Render")
