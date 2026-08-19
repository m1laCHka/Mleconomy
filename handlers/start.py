# handlers/start.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from database.models import user_exists, create_user
from keyboards.main_menu import get_main_menu

router = Router()

START_PHOTO = "https://i.ibb.co/N6dqh7MQ/5953fda8-0711-46b4-90ab-80f1fc2955f3.jpg"

def get_gender_keyboard():
    """Клавиатура для выбора пола"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 Женский", callback_data="gender_female"),
        ]
    ])
    return keyboard

def is_private_chat(message: Message) -> bool:
    """Проверка, является ли чат личным"""
    return message.chat.type == "private"

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработка команды /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "User"
        
        if await user_exists(db, user_id):
            if is_private_chat(message):
                # В ЛС — с меню
                await message.answer_photo(
                    photo=START_PHOTO,
                    caption="👋 Добро пожаловать! Выбери действие:",
                    reply_markup=get_main_menu()
                )
            else:
                # В группе — без меню
                await message.answer_photo(
                    photo=START_PHOTO,
                    caption="👋 Добро пожаловать! Используй команды:\n"
                            "/profile — профиль\n"
                            "/help — помощь\n"
                            "/statistics — статистика"
                )
        else:
            # Первый раз — выбор пола
            await message.answer_photo(
                photo=START_PHOTO,
                caption="👋 Привет! Сначала выбери свой пол:",
                reply_markup=get_gender_keyboard()
            )
    except Exception as e:
        print(f"❌ Ошибка в /start: {e}")
        try:
            await message.answer(
                "👋 Привет! Выбери свой пол:",
                reply_markup=get_gender_keyboard()
            )
        except Exception as e2:
            print(f"❌ Критическая ошибка в /start: {e2}")

@router.callback_query(F.data == "gender_male")
async def gender_male_callback(callback: CallbackQuery):
    """Выбор мужского пола"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or "User"
        
        if await user_exists(db, user_id):
            await callback.answer("Ты уже зарегистрирован!")
            try:
                await callback.message.delete()
            except:
                pass
            
            if is_private_chat(callback.message):
                await callback.message.answer("Главное меню:", reply_markup=get_main_menu())
            else:
                await callback.message.answer("Используй команды: /profile, /help")
            return
        
        await create_user(db, user_id, username, gender="male")
        await callback.answer("✅ Пол выбран: Мужской")
        
        try:
            await callback.message.delete()
        except:
            pass
        
        if is_private_chat(callback.message):
            await callback.message.answer(
                "🎉 Отлично! Теперь ты зарегистрирован.\n"
                "💰 Твой стартовый баланс: 500 монет и 10 звёзд\n\n"
                "Выбери действие:",
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.answer(
                "🎉 Отлично! Теперь ты зарегистрирован.\n"
                "💰 Твой стартовый баланс: 500 монет и 10 звёзд\n\n"
                "Используй команды: /profile, /help"
            )
    except Exception as e:
        print(f"❌ Ошибка выбора мужского пола: {e}")
        try:
            await callback.answer("⚠️ Ошибка сервера", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "gender_female")
async def gender_female_callback(callback: CallbackQuery):
    """Выбор женского пола"""
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or "User"
        
        if await user_exists(db, user_id):
            await callback.answer("Ты уже зарегистрирована!")
            try:
                await callback.message.delete()
            except:
                pass
            
            if is_private_chat(callback.message):
                await callback.message.answer("Главное меню:", reply_markup=get_main_menu())
            else:
                await callback.message.answer("Используй команды: /profile, /help")
            return
        
        await create_user(db, user_id, username, gender="female")
        await callback.answer("✅ Пол выбран: Женский")
        
        try:
            await callback.message.delete()
        except:
            pass
        
        if is_private_chat(callback.message):
            await callback.message.answer(
                "🎉 Отлично! Теперь ты зарегистрирована.\n"
                "💰 Твой стартовый баланс: 500 монет и 10 звёзд\n\n"
                "Выбери действие:",
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.answer(
                "🎉 Отлично! Теперь ты зарегистрирована.\n"
                "💰 Твой стартовый баланс: 500 монет и 10 звёзд\n\n"
                "Используй команды: /profile, /help"
            )
    except Exception as e:
        print(f"❌ Ошибка выбора женского пола: {e}")
        try:
            await callback.answer("⚠️ Ошибка сервера", show_alert=True)
        except:
            pass
