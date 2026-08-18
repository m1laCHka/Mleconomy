# handlers/profile.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.db import db
from database.models import get_user
from keyboards.main_menu import get_main_menu

router = Router()

FEMALE_PHOTO = "https://i.ibb.co/RMbs94m/584b2c22-ff9b-491f-bccf-63fa7e692f6a.jpg"
MALE_PHOTO = "https://i.ibb.co/pv7by3Y9/7e592789-6a08-4897-bfaa-054df3735f95.jpg"

async def show_profile(message: Message, user_id: int):
    """Показать профиль пользователя"""
    try:
        user = await get_user(db, user_id)
        
        if not user:
            await message.answer(
                "❌ Сначала пройди регистрацию через /start",
                reply_markup=get_main_menu()
            )
            return
        
        # Выбираем фото в зависимости от пола
        photo = FEMALE_PHOTO if user['gender'] == 'female' else MALE_PHOTO
        
        # Формируем профиль
        profile_text = f"""
👤 **ТВЕ ПРОФИЛЬ**

📱 ID: `{user['user_id']}`
📝 Имя: @{user['username']}
⚥ Пол: {'👩 Женский' if user['gender'] == 'female' else '👨 Мужской'}
💰 Баланс: {user['balance']} 💵
📅 Дата регистрации: {user['created_at']}
"""
        
        await message.answer_photo(
            photo=photo,
            caption=profile_text,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"❌ Ошибка получения профиля: {e}")
        await message.answer(
            "⚠️ Ошибка сервера, попробуй позже",
            reply_markup=get_main_menu()
        )

@router.message(Command("profile"))
async def profile_command(message: Message):
    """Команда /profile"""
    await show_profile(message, message.from_user.id)

@router.message(F.text == "👤 Профиль")
async def profile_button(message: Message):
    """Кнопка профиля"""
    await show_profile(message, message.from_user.id)
