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
    """Главное меню (только для ЛС)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🎮 Игры")],
            [KeyboardButton(text="🛍️ Магазин"), KeyboardButton(text="🎁 Приз")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )
    return keyboard

def get_profile_menu() -> ReplyKeyboardMarkup:
    """Меню профиля"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Перевод"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )
    return keyboard

def get_games_menu() -> ReplyKeyboardMarkup:
    """Меню игр"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Игры в чате")],
            [KeyboardButton(text="🤖 Игры с ботом")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )
    return keyboard

def get_chat_games_menu() -> ReplyKeyboardMarkup:
    """Меню игр в чате"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 Рулетка"), KeyboardButton(text="⚔️ Дуэль")],
            [KeyboardButton(text="🐱 Котики")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )
    return keyboard

def get_bot_games_menu() -> ReplyKeyboardMarkup:
    """Меню игр с ботом"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 Казино")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )
    return keyboard
