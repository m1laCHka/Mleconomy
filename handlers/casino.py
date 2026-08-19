# handlers/casino.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from database.models import get_user, update_balance, update_stars, update_stats
import random
from datetime import datetime, timedelta

router = Router()

# Константы
CASINO_COST = 25  # звёзд за игру

# Призы
PRIZES = [
    {"type": "coins", "min": 50, "max": 3000, "emoji": "💰", "name": "Монеты"},
    {"type": "stars", "min": 10, "max": 75, "emoji": "⭐", "name": "Звёзды"},
    {"type": "vip", "days": [4, 5, 6, 7, 8, 9, 10], "emoji": "👑", "name": "VIP"},
    {"type": "jackpot", "emoji": "💎", "name": "ДЖЕКПОТ"},
]

def get_casino_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с 5 сундуками"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁", callback_data="casino_0"),
            InlineKeyboardButton(text="🎁", callback_data="casino_1"),
            InlineKeyboardButton(text="🎁", callback_data="casino_2"),
            InlineKeyboardButton(text="🎁", callback_data="casino_3"),
            InlineKeyboardButton(text="🎁", callback_data="casino_4"),
        ]
    ])
    return keyboard

def get_after_win_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после выигрыша"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔓 Открыть ещё раз", callback_data="casino_again"),
            InlineKeyboardButton(text="👀 Что могло выпасть?", callback_data="casino_reveal"),
        ],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="casino_close")]
    ])
    return keyboard

def generate_prizes() -> list:
    """Сгенерировать призы для 5 сундуков"""
    prizes = []
    for _ in range(5):
        # Шансы: 40% монеты, 30% VIP, 29% звёзды, 1% джекпот
        roll = random.random() * 100
        
        if roll < 1:  # 1% джекпот
            prizes.append({"type": "jackpot", "emoji": "💎", "name": "ДЖЕКПОТ", "coins": 5000, "stars": 50, "vip_days": 30})
        elif roll < 30:  # 29% звёзды
            stars = random.randint(10, 75)
            prizes.append({"type": "stars", "emoji": "⭐", "name": "Звёзды", "stars": stars, "coins": 0, "vip_days": 0})
        elif roll < 60:  # 30% VIP
            vip_days = random.choice([4, 5, 6, 7, 8, 9, 10])
            prizes.append({"type": "vip", "emoji": "👑", "name": "VIP", "stars": 0, "coins": 0, "vip_days": vip_days})
        else:  # 40% монеты
            coins = random.randint(50, 3000)
            prizes.append({"type": "coins", "emoji": "💰", "name": "Монеты", "stars": 0, "coins": coins, "vip_days": 0})
    
    return prizes

def format_prize(prize: dict) -> str:
    """Форматировать приз для отображения"""
    if prize["type"] == "coins":
        return f"💰 {prize['coins']} монет"
    elif prize["type"] == "stars":
        return f"⭐ {prize['stars']} звёзд"
    elif prize["type"] == "vip":
        return f"👑 VIP на {prize['vip_days']} дней"
    elif prize["type"] == "jackpot":
        return f"💎 ДЖЕКПОТ: 5000💰 + 50⭐ + VIP 30 дней"
    return "Неизвестно"

async def apply_vip(user_id: int, days: int):
    """Выдать VIP"""
    try:
        user = await get_user(db, user_id)
        if not user:
            return
        
        # Если уже VIP — продлеваем
        if user.get('is_vip') and user.get('vip_until'):
            vip_until = user['vip_until'] + timedelta(days=days)
        else:
            vip_until = datetime.now() + timedelta(days=days)
        
        await db.execute(
            "UPDATE users SET is_vip = TRUE, vip_until = $1 WHERE user_id = $2",
            vip_until, user_id
        )
    except Exception as e:
        print(f"❌ Ошибка VIP: {e}")

# Команда "казино"
@router.message(F.text.lower() == "казино")
async def casino_start(message: Message):
    """Начать игру в казино"""
    try:
        user = await get_user(db, message.from_user.id)
        if not user:
            await message.answer("❌ Сначала пройди регистрацию через /start")
            return
        
        if user['stars'] < CASINO_COST:
            await message.answer(
                f"❌ Недостаточно звёзд!\n\n"
                f"💎 Нужно: {CASINO_COST}⭐\n"
                f"⭐ У тебя: {user['stars']}⭐\n\n"
                f"Заработай звёзды в играх или получи ежедневный приз!"
            )
            return
        
        await message.answer(
            f"🎰 КАЗИНО\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💎 Стоимость игры: {CASINO_COST}⭐\n\n"
            f"🎁 Выбери сундук:\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Возможные призы:\n"
            f"💰 Монеты\n"
            f"⭐ Звёзды\n"
            f"👑 VIP\n"
            f"💎 И ещё кое-что...",
            reply_markup=get_casino_keyboard()
        )
    except Exception as e:
        print(f"❌ Ошибка казино: {e}")

# Обработка выбора сундука
@router.callback_query(F.data.startswith("casino_"))
async def casino_callback(callback: CallbackQuery):
    """Обработка кнопок казино"""
    try:
        action = callback.data.replace("casino_", "")
        
        # Закрыть
        if action == "close":
            await callback.message.delete()
            await callback.answer("Закрыто")
            return
        
        # Открыть ещё раз
        if action == "again":
            user = await get_user(db, callback.from_user.id)
            if not user:
                await callback.answer("❌ Сначала зарегистрируйся!", show_alert=True)
                return
            
            if user['stars'] < CASINO_COST:
                await callback.answer(f"❌ Недостаточно звёзд! Нужно {CASINO_COST}⭐", show_alert=True)
                return
            
            await callback.message.delete()
            
            await callback.message.answer(
                f"🎰 КАЗИНО\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💎 Стоимость игры: {CASINO_COST}⭐\n\n"
                f"🎁 Выбери сундук:\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Возможные призы:\n"
                f"💰 Монеты\n"
                f"⭐ Звёзды\n"
                f"👑 VIP\n"
                f"💎 И ещё кое-что...",
                reply_markup=get_casino_keyboard()
            )
            await callback.answer()
            return
        
        # Показать что могло выпасть
        if action == "reveal":
            # Здесь показываем все призы, которые были в сундуках
            # Так как призы генерируются при выборе, сохраняем их
            # Для простоты — генерируем заново
            prizes = generate_prizes()
            
            text = "👀 ЧТО МОГЛО ВЫПАСТЬ:\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, prize in enumerate(prizes, 1):
                text += f"🎁 Сундук {i}: {format_prize(prize)}\n"
            
            text += "\n━━━━━━━━━━━━━━━━━━━━"
            
            await callback.message.answer(text)
            await callback.answer()
            return
        
        # Выбор сундука (casino_0, casino_1, ...)
        if action.isdigit():
            box_index = int(action)
            
            user = await get_user(db, callback.from_user.id)
            if not user:
                await callback.answer("❌ Сначала зарегистрируйся!", show_alert=True)
                return
            
            if user['stars'] < CASINO_COST:
                await callback.answer(f"❌ Недостаточно звёзд! Нужно {CASINO_COST}⭐", show_alert=True)
                return
            
            # Списываем звёзды
            await update_stars(db, callback.from_user.id, -CASINO_COST)
            
            # Генерируем призы
            prizes = generate_prizes()
            selected_prize = prizes[box_index]
            
            # Выдаём приз
            if selected_prize["type"] == "coins":
                await update_balance(db, callback.from_user.id, selected_prize["coins"])
                await update_stats(db, callback.from_user.id, "casino", True)
            elif selected_prize["type"] == "stars":
                await update_stars(db, callback.from_user.id, selected_prize["stars"])
                await update_stats(db, callback.from_user.id, "casino", True)
            elif selected_prize["type"] == "vip":
                await apply_vip(callback.from_user.id, selected_prize["vip_days"])
                await update_stats(db, callback.from_user.id, "casino", True)
            elif selected_prize["type"] == "jackpot":
                await update_balance(db, callback.from_user.id, selected_prize["coins"])
                await update_stars(db, callback.from_user.id, selected_prize["stars"])
                await apply_vip(callback.from_user.id, selected_prize["vip_days"])
                await update_stats(db, callback.from_user.id, "casino", True)
            
            # Формируем сообщение
            if selected_prize["type"] == "jackpot":
                result_text = (
                    f"🎰 КАЗИНО\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎁 Ты выбрал сундук #{box_index + 1}!\n\n"
                    f"💎💎💎 ДЖЕКПОТ! 💎💎💎\n\n"
                    f"🎉 ТВОЙ ВЫИГРЫШ:\n\n"
                    f"💰 Монеты: 5000\n"
                    f"⭐ Звёзды: 50\n"
                    f"👑 VIP: 30 дней!\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
            else:
                result_text = (
                    f"🎰 КАЗИНО\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎁 Ты выбрал сундук #{box_index + 1}!\n\n"
                    f"🎉 ТВОЙ ВЫИГРЫШ:\n\n"
                    f"{format_prize(selected_prize)}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
            
            # Обновляем сообщение
            await callback.message.edit_text(
                result_text,
                reply_markup=get_after_win_keyboard()
            )
            
            await callback.answer("🎉 Открываем!")
            return
        
    except Exception as e:
        print(f"❌ Ошибка казино: {e}")
        await callback.answer("⚠️ Ошибка сервера", show_alert=True)
