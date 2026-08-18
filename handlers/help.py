# handlers/help.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu

router = Router()

HELP_PHOTO = "https://i.ibb.co/N6dqh7MQ/5953fda8-0711-46b4-90ab-80f1fc2955f3.jpg"

HELP_TEXT = """
❓ ПОМОЩЬ

🔍 Основные команды:
• /start — начать работу
• /profile — открыть профиль
• /statistics — статистика игр
• /help — эта справка

🛍️ Функции:
• Профиль — просмотр статистики
• Магазин — покупка предметов
• Ежедневный приз — получить награду
• Переводы — отправить деньги другу

💡 Советы:
• Играй каждый день для бонусов
• Участвуй в событиях
• Присоединись к команде

❓ Остались вопросы? Свяжись с поддержкой: @m1lnv
"""

def is_private_chat(message: Message) -> bool:
    """Проверка, является ли чат личным"""
    return message.chat.type == "private"

@router.message(Command("help"))
async def help_command(message: Message):
    """Команда /help"""
    try:
        if is_private_chat(message):
            # В личных сообщениях с меню
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT,
                reply_markup=get_main_menu()
            )
        else:
            # В группах без меню
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT
            )
    except Exception as e:
        print(f"❌ Ошибка отправки помощи: {e}")
        # Запасной вариант без фото
        if is_private_chat(message):
            await message.answer(
                HELP_TEXT,
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(HELP_TEXT)

@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    """Кнопка помощи"""
    try:
        if is_private_chat(message):
            # В личных сообщениях с меню
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT,
                reply_markup=get_main_menu()
            )
        else:
            # В группах без меню
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT
            )
    except Exception as e:
        print(f"❌ Ошибка отправки помощи (кнопка): {e}")
        # Запасной вариант без фото
        if is_private_chat(message):
            await message.answer(
                HELP_TEXT,
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(HELP_TEXT)
