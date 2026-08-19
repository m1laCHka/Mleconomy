# handlers/help.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu

router = Router()

HELP_PHOTO = "https://i.ibb.co/vC09RQpC/1cee67ae-bca8-4add-b6a4-fbc5b452874f.jpg"

HELP_TEXT = """
❓ ПОМОЩЬ

🎮 ИГРЫ:
• Рулетка — напиши «рулетка» в чате
• Дуэль — ответь на сообщение и напиши «дуэль [сумма]»
• Котики — скоро
• Казино — скоро

💰 ЭКОНОМИКА:
• Приз — ежедневный бонус
• Магазин — скоро
• Перевод — скоро

🏆 СОРЕВНОВАНИЯ:
• Турнир — скоро
• Квесты — скоро
• Топ игроков — скоро

💍 СЕМЬЯ:
• Брак — скоро
• Развод — скоро
• Дети — скоро

👤 ПРОФИЛЬ:
• /profile — свой профиль
• /profile @user — чужой профиль
• /stats — статистика игр

🎁 ПРОЧЕЕ:
• Промокоды — скоро
• Достижения — скоро
• Ранги — скоро

💡 По вопросам: @m1lnv
"""

def is_private_chat(message: Message) -> bool:
    return message.chat.type == "private"

@router.message(Command("help"))
async def help_command(message: Message):
    try:
        if is_private_chat(message):
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT,
                reply_markup=get_main_menu()
            )
        else:
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT
            )
    except Exception as e:
        print(f"❌ Ошибка отправки помощи: {e}")
        if is_private_chat(message):
            await message.answer(HELP_TEXT, reply_markup=get_main_menu())
        else:
            await message.answer(HELP_TEXT)

@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    try:
        if is_private_chat(message):
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT,
                reply_markup=get_main_menu()
            )
        else:
            await message.answer_photo(
                photo=HELP_PHOTO,
                caption=HELP_TEXT
            )
    except Exception as e:
        print(f"❌ Ошибка отправки помощи (кнопка): {e}")
        if is_private_chat(message):
            await message.answer(HELP_TEXT, reply_markup=get_main_menu())
        else:
            await message.answer(HELP_TEXT)
