# keyboards/main_menu.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_gender_selection() -> InlineKeyboardMarkup:
    """Выбор пола при регистрации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 Женский", callback_data="gender_female"),
        ]
    ])
    return keyboard

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню (только для личных сообщений)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🛍️ Магазин")],
            [KeyboardButton(text="🎁 Ежедневный приз")],
            [KeyboardButton(text="💳 Переводы")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )
    return keyboard
