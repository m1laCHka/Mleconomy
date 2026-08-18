# handlers/roulette.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from database.models import get_user, update_balance, update_stats
import random
import asyncio
from datetime import datetime

router = Router()

# Константы
MIN_BET = 50
GAME_TIMER = 60  # секунд
COMMISSION = 0.10  # 10% комиссия

# Фото для результата рулетки
ROULETTE_RESULT_PHOTO = "https://i.ibb.co/Rpnv0nxh/237437bd-7bef-4f31-83ae-19b0457bca2f.jpg"

# Числа и цвета (0-21)
RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21]
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20]

# Хранилище активных игр
active_games = {}

class RouletteGame:
    def __init__(self, chat_id: int, creator_id: int, creator_name: str, bot: Bot):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.bot = bot
        self.bets = []
        self.is_active = True
        self.message_id = None
        self.timer_task = None
        self.started_at = datetime.now()  # Время начала игры
    
    def add_bet(self, user_id: int, username: str, bet_type: str, amount: int, number: int = None):
        """Добавить ставку"""
        user_bets = [b for b in self.bets if b["user_id"] == user_id]
        
        if bet_type == "number":
            number_bets = [b for b in user_bets if b["bet_type"] == "number"]
            if len(number_bets) >= 3:
                return False, "❌ Максимум 3 ставки на числа!"
        
        if bet_type in ["red", "black"]:
            color_bets = [b for b in user_bets if b["bet_type"] in ["red", "black"]]
            if color_bets:
                return False, "❌ Ты уже поставил на цвет!"
        
        if bet_type in ["even", "odd"]:
            parity_bets = [b for b in user_bets if b["bet_type"] in ["even", "odd"]]
            if parity_bets:
                return False, "❌ Ты уже поставил на чет/нечет!"
        
        if bet_type == "zero":
            zero_bets = [b for b in user_bets if b["bet_type"] == "zero"]
            if zero_bets:
                return False, "❌ Ты уже поставил на зеро!"
        
        if len(user_bets) >= 6:
            return False, "❌ Максимум 6 ставок!"
        
        self.bets.append({
            "user_id": user_id,
            "username": username,
            "bet_type": bet_type,
            "amount": amount,
            "number": number
        })
        return True, "✅ Ставка принята!"
    
    def get_bets_text(self) -> str:
        """Получить текст со ставками"""
        if not self.bets:
            return "нет"
        
        text = ""
        for bet in self.bets:
            bet_text = get_bet_type_text(bet["bet_type"], bet["number"])
            text += f"• @{bet['username']}: {bet_text} — {bet['amount']}💰\n"
        return text
    
    def get_user_bets_text(self, user_id: int) -> str:
        """Получить ставки конкретного пользователя"""
        user_bets = [b for b in self.bets if b["user_id"] == user_id]
        if not user_bets:
            return "У тебя нет ставок"
        
        text = "📊 Твои ставки:\n\n"
        for bet in user_bets:
            bet_text = get_bet_type_text(bet["bet_type"], bet["number"])
            text += f"• {bet_text} — {bet['amount']}💰\n"
        return text
    
    def get_remaining_seconds(self) -> int:
        """Получить оставшееся время (не сбрасывается)"""
        elapsed = (datetime.now() - self.started_at).total_seconds()
        remaining = GAME_TIMER - elapsed
        return max(0, int(remaining))

def spin_roulette() -> dict:
    """Крутить рулетку (0-21)"""
    number = random.randint(0, 21)
    
    if number == 0:
        color = "zero"
    elif number in RED_NUMBERS:
        color = "red"
    else:
        color = "black"
    
    is_even = number % 2 == 0 if number != 0 else None
    
    return {
        "number": number,
        "color": color,
        "is_even": is_even
    }

def calculate_win(bet_type: str, amount: int, number: int, result: dict) -> int:
    """Рассчитать выигрыш (с учетом комиссии 10%)"""
    win = 0
    
    if bet_type == "red" and result["color"] == "red":
        win = amount * 2
    elif bet_type == "black" and result["color"] == "black":
        win = amount * 2
    elif bet_type == "zero" and result["number"] == 0:
        win = amount * 22
    elif bet_type == "even" and result["is_even"] == True:
        win = amount * 2
    elif bet_type == "odd" and result["is_even"] == False:
        win = amount * 2
    elif bet_type == "number" and number == result["number"]:
        win = amount * 22
    
    if win > 0:
        win = int(win * (1 - COMMISSION))
    
    return win

def get_bet_type_text(bet_type: str, number: int = None) -> str:
    """Получить текст ставки"""
    if bet_type == "red":
        return "🔴 Красное"
    elif bet_type == "black":
        return "⚫ Черное"
    elif bet_type == "zero":
        return "🟢 Зеро"
    elif bet_type == "even":
        return "🔢 Четное"
    elif bet_type == "odd":
        return "🔢 Нечетное"
    elif bet_type == "number":
        return f"🎯 Число {number}"
    return "Неизвестно"

def get_result_text(result: dict) -> str:
    """Получить текст результата"""
    if result["number"] == 0:
        return "🟢 Зеро (0)"
    elif result["color"] == "red":
        return f"🔴 Красное ({result['number']})"
    else:
        return f"⚫ Черное ({result['number']})"

def get_bet_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ставок"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔴 Красное", callback_data="bet_red"),
            InlineKeyboardButton(text="⚫ Черное", callback_data="bet_black"),
        ],
        [
            InlineKeyboardButton(text="🟢 Зеро", callback_data="bet_zero"),
            InlineKeyboardButton(text="🔢 Чет", callback_data="bet_even"),
        ],
        [
            InlineKeyboardButton(text="🔢 Нечет", callback_data="bet_odd"),
            InlineKeyboardButton(text="🎯 Число", callback_data="bet_number"),
        ],
        [
            InlineKeyboardButton(text="📊 Мои ставки", callback_data="my_bets"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="bet_cancel"),
        ]
    ])
    return keyboard

async def save_roulette_log(chat_id: int, result: dict):
    """Сохранить результат в лог"""
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS roulette_logs (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT,
                number INT,
                color VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            INSERT INTO roulette_logs (chat_id, number, color)
            VALUES ($1, $2, $3)
        """, chat_id, result["number"], result["color"])
        
    except Exception as e:
        print(f"❌ Ошибка сохранения лога: {e}")

async def update_game_message(game: RouletteGame):
    """Обновить сообщение с игрой"""
    try:
        remaining = game.get_remaining_seconds()
        await game.bot.edit_message_text(
            chat_id=game.chat_id,
            message_id=game.message_id,
            text=(
                f"🎰 РУЛЕТКА\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎮 Игра идет!\n"
                f"👤 Организатор: @{game.creator_name}\n"
                f"💰 Минимальная ставка: {MIN_BET} монет\n"
                f"⏳ Осталось: {remaining} секунд\n"
                f"💸 Комиссия: 10%\n\n"
                f"📊 Текущие ставки:\n{game.get_bets_text()}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Нажми на кнопку, чтобы сделать ставку:"
            ),
            reply_markup=get_bet_keyboard()
        )
    except Exception as e:
        print(f"❌ Ошибка обновления сообщения: {e}")

async def finish_game_after_timer(chat_id: int):
    """Завершить игру после таймера"""
    await asyncio.sleep(GAME_TIMER)
    
    if chat_id in active_games and active_games[chat_id].is_active:
        await finish_roulette_game(chat_id)

async def finish_roulette_game(chat_id: int):
    """Завершить игру в рулетку"""
    try:
        game = active_games.get(chat_id)
        if not game or not game.is_active:
            return
        
        game.is_active = False
        
        # Крутим рулетку
        result = spin_roulette()
        
        # Сохраняем в лог
        await save_roulette_log(chat_id, result)
        
        # Рассчитываем результаты
        result_text = get_result_text(result)
        results = []
        
        for bet in game.bets:
            win_amount = calculate_win(bet["bet_type"], bet["amount"], bet["number"], result)
            
            if win_amount > 0:
                await update_balance(db, bet["user_id"], win_amount)
                await update_stats(db, bet["user_id"], "roulette", True)
                results.append(f"✅ @{bet['username']}: +{win_amount}💰 ({get_bet_type_text(bet['bet_type'], bet['number'])})")
            else:
                await update_stats(db, bet["user_id"], "roulette", False)
                results.append(f"❌ @{bet['username']}: -{bet['amount']}💰 ({get_bet_type_text(bet['bet_type'], bet['number'])})")
        
        if results:
            results_text = "\n".join(results)
        else:
            results_text = "Никто не сделал ставку"
        
        final_caption = (
            f"🎰 РУЛЕТКА — РЕЗУЛЬТАТ\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎲 Выпало: {result_text}\n\n"
            f"📊 Итоги:\n{results_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Отправляем результат с фото
        await game.bot.send_photo(
            chat_id=chat_id,
            photo=ROULETTE_RESULT_PHOTO,
            caption=final_caption
        )
        
        # Удаляем игру
        del active_games[chat_id]
        
    except Exception as e:
        print(f"❌ Ошибка завершения игры: {e}")

# Обработка команды "рулетка" (только в группах)
@router.message(F.text.lower().startswith("рулетка"))
async def roulette_start(message: Message):
    """Начать игру в рулетку"""
    try:
        # Проверяем, что это группа
        if message.chat.type == "private":
            await message.answer("❌ Рулетка доступна только в группах!")
            return
        
        chat_id = message.chat.id
        bot = message.bot
        
        # Проверяем, идет ли уже игра
        if chat_id in active_games and active_games[chat_id].is_active:
            game = active_games[chat_id]
            
            # НЕ сбрасываем таймер! Просто показываем оставшееся время
            remaining = game.get_remaining_seconds()
            
            if remaining <= 0:
                # Если время вышло, завершаем игру
                await finish_roulette_game(chat_id)
                await message.answer("🎰 Игра завершена! Начинаем новую...")
                # Создаем новую игру
                return await roulette_start(message)
            
            await message.answer(
                f"⏳ Игра уже идет! Осталось: {remaining} секунд"
            )
            await update_game_message(game)
            return
        
        # Создаем новую игру
        username = message.from_user.username or message.from_user.first_name
        game = RouletteGame(chat_id, message.from_user.id, username, bot)
        active_games[chat_id] = game
        
        # Отправляем сообщение
        msg = await message.answer(
            f"🎰 РУЛЕТКА\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎮 Игра создана!\n"
            f"👤 Организатор: @{username}\n"
            f"💰 Минимальная ставка: {MIN_BET} монет\n"
            f"⏳ Время на ставки: {GAME_TIMER} секунд\n"
            f"💸 Комиссия: 10%\n\n"
            f"📊 Текущие ставки: нет\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Нажми на кнопку, чтобы сделать ставку:",
            reply_markup=get_bet_keyboard()
        )
        
        game.message_id = msg.message_id
        game.timer_task = asyncio.create_task(finish_game_after_timer(chat_id))
        
    except Exception as e:
        print(f"❌ Ошибка создания игры: {e}")
        await message.answer("⚠️ Ошибка сервера")

# Обработка ставок через кнопки
@router.callback_query(F.data.startswith("bet_"))
async def bet_callback(callback: CallbackQuery):
    """Обработка нажатий на кнопки"""
    try:
        chat_id = callback.message.chat.id
        game = active_games.get(chat_id)
        
        if not game or not game.is_active:
            await callback.answer("❌ Игра уже завершена!", show_alert=True)
            return
        
        action = callback.data.replace("bet_", "")
        
        # Отмена игры
        if action == "cancel":
            if callback.from_user.id == game.creator_id:
                game.is_active = False
                if game.timer_task:
                    game.timer_task.cancel()
                del active_games[chat_id]
                await callback.message.edit_text("❌ Игра отменена организатором")
                await callback.answer("Игра отменена")
                return
            else:
                await callback.answer("❌ Только организатор может отменить игру!", show_alert=True)
                return
        
        # Показать мои ставки
        if action == "my_bets":
            bets_text = game.get_user_bets_text(callback.from_user.id)
            await callback.message.answer(bets_text)
            await callback.answer()
            return
        
        # Ставка на число
        if action == "number":
            await callback.message.answer(
                f"🎯 Введи число от 0 до 21:\n"
                f"Напиши: число [номер] [сумма]\n"
                f"Пример: число 7 100"
            )
            await callback.answer()
            return
        
        # Для остальных ставок спрашиваем сумму
        bet_type_names = {
            "red": "красное",
            "black": "черное",
            "zero": "зеро",
            "even": "чет",
            "odd": "нечет"
        }
        
        bet_type = action
        bet_name = bet_type_names.get(bet_type, bet_type)
        
        await callback.message.answer(
            f"💰 Введи сумму ставки:\n"
            f"Напиши: {bet_name} [сумма]\n"
            f"Пример: {bet_name} 100\n\n"
            f"Минимальная ставка: {MIN_BET} монет"
        )
        await callback.answer()
        
    except Exception as e:
        print(f"❌ Ошибка ставки: {e}")
        await callback.answer("⚠️ Ошибка сервера", show_alert=True)

# Обработка суммы ставки
@router.message(F.text.lower().startswith(("красное", "черное", "зеро", "чет", "нечет", "четное", "нечетное")))
async def amount_bet(message: Message):
    """Обработка суммы ставки"""
    try:
        chat_id = message.chat.id
        game = active_games.get(chat_id)
        
        if not game or not game.is_active:
            await message.answer("❌ Нет активной игры!")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Укажи сумму!\nПример: красное 100")
            return
        
        bet_type_str = parts[0].lower()
        try:
            amount = int(parts[1])
        except:
            await message.answer("❌ Сумма должна быть числом!")
            return
        
        if amount < MIN_BET:
            await message.answer(f"❌ Минимальная ставка: {MIN_BET}💰")
            return
        
        user = await get_user(db, message.from_user.id)
        if not user:
            await message.answer("❌ Сначала пройди регистрацию через /start")
            return
        
        if user['balance'] < amount:
            await message.answer(f"❌ Недостаточно монет! У тебя: {user['balance']}💰")
            return
        
        if bet_type_str in ["красное"]:
            bet_type = "red"
        elif bet_type_str in ["черное"]:
            bet_type = "black"
        elif bet_type_str in ["зеро"]:
            bet_type = "zero"
        elif bet_type_str in ["чет", "четное"]:
            bet_type = "even"
        elif bet_type_str in ["нечет", "нечетное"]:
            bet_type = "odd"
        else:
            return
        
        await update_balance(db, message.from_user.id, -amount)
        
        username = message.from_user.username or message.from_user.first_name
        success, msg_text = game.add_bet(message.from_user.id, username, bet_type, amount)
        
        if not success:
            await update_balance(db, message.from_user.id, amount)
            await message.answer(msg_text)
            return
        
        await message.answer(f"✅ {msg_text}")
        await update_game_message(game)
        
    except Exception as e:
        print(f"❌ Ошибка суммы ставки: {e}")
        await message.answer("⚠️ Ошибка сервера")

# Обработка ставки на число
@router.message(F.text.lower().startswith("число"))
async def number_bet(message: Message):
    """Обработка ставки на число"""
    try:
        chat_id = message.chat.id
        game = active_games.get(chat_id)
        
        if not game or not game.is_active:
            await message.answer("❌ Нет активной игры!")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("❌ Укажи число и сумму!\nПример: число 7 100")
            return
        
        try:
            number = int(parts[1])
            amount = int(parts[2])
        except:
            await message.answer("❌ Число и сумма должны быть числами!")
            return
        
        if number < 0 or number > 21:
            await message.answer("❌ Число должно быть от 0 до 21!")
            return
        
        if amount < MIN_BET:
            await message.answer(f"❌ Минимальная ставка: {MIN_BET}💰")
            return
        
        user = await get_user(db, message.from_user.id)
        if not user:
            await message.answer("❌ Сначала пройди регистрацию через /start")
            return
        
        if user['balance'] < amount:
            await message.answer(f"❌ Недостаточно монет! У тебя: {user['balance']}💰")
            return
        
        await update_balance(db, message.from_user.id, -amount)
        
        username = message.from_user.username or message.from_user.first_name
        success, msg_text = game.add_bet(message.from_user.id, username, "number", amount, number)
        
        if not success:
            await update_balance(db, message.from_user.id, amount)
            await message.answer(msg_text)
            return
        
        await message.answer(f"✅ {msg_text}")
        await update_game_message(game)
        
    except Exception as e:
        print(f"❌ Ошибка ставки на число: {e}")
        await message.answer("⚠️ Ошибка сервера")

# Лог
@router.message(F.text.lower() == "лог")
@router.message(F.text.lower() == "история")
async def roulette_log(message: Message):
    """Показать историю рулетки"""
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS roulette_logs (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT,
                number INT,
                color VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logs = await db.fetch("""
            SELECT number, color
            FROM roulette_logs
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT 5
        """, message.chat.id)
        
        if not logs:
            await message.answer(
                "🎡 История рулетки пуста.\n\n"
                "Напиши 'рулетка' чтобы начать игру!"
            )
            return
        
        log_text = "🎡 история 5 последних чисел рулетки:\n\n"
        
        for log in logs:
            number = log['number']
            color = log['color']
            
            if color == 'red':
                color_text = "🔴 Красное"
            elif color == 'black':
                color_text = "⚫️ Чёрное"
            else:
                color_text = "🟢 Зеленое"
            
            log_text += f"— {number} ({color_text})\n"
        
        log_text += "\n📌 Последние результаты находятся вверху списка."
        
        await message.answer(log_text)
        
    except Exception as e:
        print(f"❌ Ошибка лога: {e}")
        await message.answer("⚠️ Ошибка сервера")
