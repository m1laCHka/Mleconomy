# handlers/prize.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from database.models import get_user, update_balance, update_stars
import random
from datetime import datetime, date

router = Router()

# Призы (могут повторяться!)
PRIZES = [
    {"coins": 200, "stars": 0, "weight": 30},
    {"coins": 500, "stars": 0, "weight": 25},
    {"coins": 800, "stars": 0, "weight": 20},
    {"coins": 1000, "stars": 1, "weight": 15},
    {"coins": 1500, "stars": 5, "weight": 10},
]

def generate_prizes() -> list:
    """Сгенерировать 5 призов (могут повторяться)"""
    prizes = []
    for _ in range(5):
        prize = random.choices(PRIZES, weights=[p["weight"] for p in PRIZES])[0]
        prizes.append(prize.copy())
    return prizes

def format_prize(prize: dict) -> str:
    """Форматировать приз"""
    if prize["stars"] > 0:
        return f"💰 {prize['coins']} монет + ⭐ {prize['stars']}"
    return f"💰 {prize['coins']} монет"

def get_prize_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с 5 звёздами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data="prize_0"),
            InlineKeyboardButton(text="⭐", callback_data="prize_1"),
            InlineKeyboardButton(text="⭐", callback_data="prize_2"),
            InlineKeyboardButton(text="⭐", callback_data="prize_3"),
            InlineKeyboardButton(text="⭐", callback_data="prize_4"),
        ]
    ])
    return keyboard

def is_private_chat(message: Message) -> bool:
    return message.chat.type == "private"

async def check_daily_games(user_id: int) -> int:
    """Проверить, сколько игр сыграл пользователь сегодня"""
    try:
        # Проверяем по дате последней активности
        user = await get_user(db, user_id)
        if not user:
            return 0
        
        # Если last_active_date != сегодня, значит сегодня ещё не играл
        if user.get('last_active_date') != date.today():
            return 0
        
        # Считаем игры за сегодня (упрощенно — total_games)
        # Можно добавить отдельную таблицу для точного подсчета
        return user.get('total_games', 0) or 0
    except Exception as e:
        print(f"❌ Ошибка проверки игр: {e}")
        return 0

async def check_prize_today(user_id: int) -> bool:
    """Проверить, получал ли приз сегодня"""
    try:
        user = await get_user(db, user_id)
        if not user:
            return False
        
        return user.get('last_prize_date') == date.today()
    except Exception as e:
        print(f"❌ Ошибка проверки приза: {e}")
        return False

# Команда "приз" или кнопка "🎁 Приз"
@router.message(F.text.lower() == "приз")
@router.message(F.text == "🎁 Приз")
async def prize_command(message: Message):
    """Ежедневный приз"""
    try:
        # Только в ЛС
        if not is_private_chat(message):
            await message.answer("❌ Ежедневный приз доступен только в личных сообщениях с ботом!\n\nНапиши мне в ЛС: @твой_бот")
            return
        
        user = await get_user(db, message.from_user.id)
        if not user:
            await message.answer("❌ Сначала пройди регистрацию через /start")
            return
        
        # Проверяем, получал ли уже приз
        if await check_prize_today(message.from_user.id):
            # Уже получил
            await message.answer(
                f"🎁 ЕЖЕДНЕВНЫЙ ПРИЗ\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📅 {date.today().strftime('%d.%m.%Y')}\n\n"
                f"✅ Ты уже получил приз сегодня!\n\n"
                f"⏳ Следующий приз завтра после 00:00"
            )
            return
        
        # Проверяем условие — сыграл ли хотя бы 1 игру
        games_today = await check_daily_games(message.from_user.id)
        
        if games_today < 1:
            await message.answer(
                f"🎁 ЕЖЕДНЕВНЫЙ ПРИЗ\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📅 {date.today().strftime('%d.%m.%Y')}\n\n"
                f"❌ Условие не выполнено!\n\n"
                f"Чтобы получить приз, сыграй хотя бы 1 игру сегодня.\n\n"
                f"🎮 Игр сегодня: {games_today}/1\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 Игры:\n"
                f"• 🎰 Рулетка — «рулетка» в чате\n"
                f"• ⚔️ Дуэль — «дуэль 100» в чате\n"
                f"• 🐱 Котики — «котики 100» в чате\n"
                f"• 🎰 Казино — «казино» в ЛС"
            )
            return
        
        # Условие выполнено — показываем звёзды
        await message.answer(
            f"🎁 ЕЖЕДНЕВНЫЙ ПРИЗ\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {date.today().strftime('%d.%m.%Y')}\n\n"
            f"✅ Условие выполнено!\n"
            f"🎮 Игр сегодня: {games_today}\n\n"
            f"Выбери звезду:\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Призы:\n"
            f"💰 200 | 💰 500 | 💰 800\n"
            f"💰 1000+1⭐ | 💰 1500+5⭐",
            reply_markup=get_prize_keyboard()
        )
        
    except Exception as e:
        print(f"❌ Ошибка приза: {e}")
        await message.answer("⚠️ Ошибка сервера")

# Обработка выбора звезды
@router.callback_query(F.data.startswith("prize_"))
async def prize_callback(callback: CallbackQuery):
    """Обработка выбора звезды"""
    try:
        star_index = int(callback.data.replace("prize_", ""))
        
        user = await get_user(db, callback.from_user.id)
        if not user:
            await callback.answer("❌ Сначала зарегистрируйся!", show_alert=True)
            return
        
        # Проверяем, не получил ли уже приз
        if await check_prize_today(callback.from_user.id):
            await callback.answer("❌ Ты уже получил приз сегодня!", show_alert=True)
            return
        
        # Проверяем условие
        games_today = await check_daily_games(callback.from_user.id)
        if games_today < 1:
            await callback.answer("❌ Сыграй хотя бы 1 игру!", show_alert=True)
            return
        
        # Генерируем призы
        prizes = generate_prizes()
        selected_prize = prizes[star_index]
        
        # Выдаём приз
        await update_balance(db, callback.from_user.id, selected_prize["coins"])
        if selected_prize["stars"] > 0:
            await update_stars(db, callback.from_user.id, selected_prize["stars"])
        
        # Отмечаем, что приз получен
        await db.execute(
            "UPDATE users SET last_prize_date = $1 WHERE user_id = $2",
            date.today(), callback.from_user.id
        )
        
        # Формируем результат
        result_text = (
            f"🎁 ЕЖЕДНЕВНЫЙ ПРИЗ\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {date.today().strftime('%d.%m.%Y')}\n\n"
            f"⭐ Ты выбрал звезду #{star_index + 1}!\n\n"
            f"🎉 ТВОЙ ПРИЗ:\n\n"
            f"{format_prize(selected_prize)}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ Следующий приз завтра!"
        )
        
        # Клавиатура "что могло выпасть"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👀 Что могло выпасть?", callback_data="prize_reveal")]
        ])
        
        await callback.message.edit_text(result_text, reply_markup=keyboard)
        await callback.answer("🎉 Приз получен!")
        
    except Exception as e:
        print(f"❌ Ошибка приза: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

# Показать что могло выпасть
@router.callback_query(F.data == "prize_reveal")
async def prize_reveal_callback(callback: CallbackQuery):
    """Показать все возможные призы"""
    try:
        prizes = generate_prizes()
        
        text = "👀 ЧТО МОГЛО ВЫПАСТЬ:\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, prize in enumerate(prizes, 1):
            text += f"⭐ Звезда {i}: {format_prize(prize)}\n"
        
        text += "\n━━━━━━━━━━━━━━━━━━━━"
        
        await callback.message.answer(text)
        await callback.answer()
    except Exception as e:
        print(f"❌ Ошибка показа призов: {e}")
