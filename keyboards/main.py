from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🛒 Магазин")],
        [KeyboardButton(text="🎮 Игры"), KeyboardButton(text="🏆 Топы")]
    ],
    resize_keyboard=True
)
