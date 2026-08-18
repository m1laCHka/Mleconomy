# handlers/help.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu

router = Router()

HELP_PHOTO = "https://i.ibb.co/N6dqh7MQ/5953fda8-0711-46b4-90ab-80f1fc2955f3.jpg"

HELP_TEXT = """
❓ **ПОМОЩЬ**

🔍 **Основные команды:**
• `/start` — начать работу
• `/profile` — открыть профиль
• `/statistics` — статистика игр
• `/help` — эта справка

🛍️ **Функции:**
• **Профиль** — просмотр статистики
• **Магазин** — покупка предметов
• **Ежедневный приз** — получить награду
• **Переводы** — отправить деньги другу

💡 **Советы:**
• Играй каждый день для бонусов
• Участвуй в событиях
• Присоединись к команде

❓ Остались вопросы? Свяжись с поддержкой: @support_bot
"""

@router.message(Command("help"))
async def help_command(message: Message):
    """Команда /help"""
    try:
        await message.answer_photo(
            photo=HELP_PHOTO,
            caption=HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"❌ Ошибка отправки помощи: {e}")
        await message.answer(
            HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    """Кнопка помощи"""
    try:
        await message.answer_photo(
            photo=HELP_PHOTO,
            caption=HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"❌ Ошибка отправки помощи (кнопка): {e}")
        await message.answer(
            HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

@router.message(F.text == "/help")
async def help_slash_command(message: Message):
    """Команда /help (дополнительная)"""
    try:
        await message.answer_photo(
            photo=HELP_PHOTO,
            caption=HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"❌ Ошибка отправки помощи (слеш): {e}")
        await message.answer(
            HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
