# handlers/start.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database.db import db
from database.models import user_exists, create_user, update_user_gender
from keyboards.main_menu import get_gender_selection, get_main_menu

router = Router()

START_PHOTO = "https://i.ibb.co/N6dqh7MQ/5953fda8-0711-46b4-90ab-80f1fc2955f3.jpg"

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    
    # Проверяем, существует ли пользователь
    if await user_exists(db, user_id):
        # Если уже зарегистрирован — показываем главное меню
        await message.answer_photo(
            photo=START_PHOTO,
            caption="👋 Добро пожаловать! Выбери действие:",
            reply_markup=get_main_menu()
        )
    else:
        # Если первый раз — просим выбрать пол
        await message.answer_photo(
            photo=START_PHOTO,
            caption="👋 Привет! Сначала выбери свой пол:",
            reply_markup=get_gender_selection()
        )

@router.callback_query(F.data == "gender_male")
async def gender_male_callback(callback: CallbackQuery):
    """Обработка выбора мужского пола"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "User"
    
    try:
        # Создаём пользователя с полом
        await create_user(db, user_id, username, gender="male")
        
        await callback.answer("✅ Пол выбран: Мужской")
        await callback.message.delete()
        
        # Показываем главное меню
        await callback.message.answer(
            "🎉 Отлично! Теперь ты зарегистрирован. Выбери действие:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"❌ Ошибка при выборе пола: {e}")
        await callback.answer("⚠️ Ошибка сервера")

@router.callback_query(F.data == "gender_female")
async def gender_female_callback(callback: CallbackQuery):
    """Обработка выбора женского пола"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "User"
    
    try:
        # Создаём пользователя с полом
        await create_user(db, user_id, username, gender="female")
        
        await callback.answer("✅ Пол выбран: Женский")
        await callback.message.delete()
        
        # Показываем главное меню
        await callback.message.answer(
            "🎉 Отлично! Теперь ты зарегистрирован. Выбери действие:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"❌ Ошибка при выборе пола: {e}")
        await callback.answer("⚠️ Ошибка сервера")
