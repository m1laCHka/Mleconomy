# handlers/roulette.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from database.models import get_user, update_balance, update_stats
import random
import asyncio
from datetime import datetime, timedelta

router = Router()

# Константы
MIN_BET = 50
GAME_TIMER = 60  # секунд на ставки

# Хранилище активных игр
active_games = {}

# Числа и цвета
RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

class RouletteGame:
    def __init__(self, chat_id: int, creator_id: int, creator_name: str, min_bet: int):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.min_bet = min_bet
        self.bets = []  # [{"user_id": id, "username": name, "bet_type": type, "amount": amount, "number": num}]
        self.is_active = True
        self.message_id = None
        self.timer_task = None
    
    def add_bet(self, user_id: int, username: str, bet_type: str, amount: int, number: int = None):
        """Добавить ставку игрока"""
        # Проверяем, не ставил ли уже этот игрок
        for bet in self.bets:
            if bet["user_id"] == user_id:
                return False, "Ты уже сделал ставку!"
        
        self.bets.append({
            "user_id": user_id,
            "username": username,
            "bet_type": bet_type,
            "amount": amount,
            "number": number
        })
        return True, "Ставка принята!"
    
    def get_bets_text(self) -> str:
        """Получить текст со ставками"""
        if not self.bets:
            return "нет"
        
        text = ""
        for bet in self.bets:
            bet_text = get_bet_type_text(bet["bet_type"], bet["number"])
            text += f"• @{bet['username']}: {bet_text} — {bet['amount']}💰\n"
        return text

def spin_roulette() -> dict:
    """Крутить рулетку"""
    number = random.randint(0, 36)
    
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
    """Рассчитать выигрыш"""
    if bet_type == "red" and result["color"] == "red":
        return amount * 2
    elif bet_type == "black" and result["color"] == "black":
        return amount * 2
    elif bet_type == "zero" and result["number"] == 0:
        return amount * 100
    elif bet_type == "even" and result["is_even"] == True:
        return amount * 2
    elif bet_type == "odd" and result["is_even"] == False:
        return amount * 2
    elif bet_type == "number" and number == result["number"]:
        return amount * 50
    elif bet_type == "dozen1" and 1 <= result["number"] <= 12:
        return amount * 3
    elif bet_type == "dozen2" and 13 <= result["number"] <= 24:
        return amount * 3
    elif bet_type == "dozen3" and 25 <= result["number"] <= 36:
        return amount * 3
    
    return 0

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
    elif bet_type == "dozen1":
        return "🎲 Дюжина 1"
    elif bet_type == "dozen2":
        return "🎲 Дюжина 2"
    elif bet_type == "dozen3":
        return "🎲 Дюжина 3"
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

# Обработка команды "рулетка"
@router.message(F.text.lower().startswith("рулетка"))
async def roulette_start(message: Message):
    """Начать игру в рулетку"""
    try:
        parts = message.text.split()
        
        # Проверяем, не идет ли уже игра
        if message.chat.id in active_games and active_games[message.chat.id].is_active:
            await message.answer("❌ В этом чате уже идет игра в рулетку!")
            return
        
        # Определяем минимальную ставку
        min_bet = MIN_BET
        if len(parts) > 1:
            try:
                min_bet = max(MIN_BET, int(parts[1]))
            except:
                pass
        
        # Создаем игру
        username = message.from_user.username or message.from_user.first_name
        game = RouletteGame(
            chat_id=message.chat.id,
            creator_id=message.from_user.id,
            creator_name=username,
            min_bet=min_bet
        )
        
        # Сохраняем игру
        active_games[message.chat.id] = game
        
        # Отправляем сообщение
        msg = await message.answer(
            f"╔══════════════════════╗\n"
            f"║      🎰 РУЛЕТКА      ║\n"
            f"╚══════════════════════╝\n\n"
            f"🎮 Игра создана!\n"
            f"👤 Организатор: @{username}\n"
            f"💰 Минимальная ставка: {min_bet} монет\n"
            f"⏳ Время на ставки: {GAME_TIMER} секунд\n\n"
            f"📊 Текущие ставки: нет\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_bet_keyboard()
        )
        
        game.message_id = msg.message_id
        
        # Запускаем таймер
        game.timer_task = asyncio.create_task(finish_game_after_timer(message.chat.id))
        
    except Exception as e:
        print(f"❌ Ошибка создания игры: {e}")
        await message.answer("⚠️ Ошибка сервера")

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
        
        # Формируем сообщение
        if results:
            results_text = "\n".join(results)
        else:
            results_text = "Никто не сделал ставку"
        
        final_message = f"""
╔══════════════════════╗
║      🎰 РУЛЕТКА      ║
╚══════════════════════╝

🎲 Результат: {result_text}

📊 Итоги:
{results_text}

━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Клавиатура с кнопкой "Как играть"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Как играть?", callback_data="roulette_help")]
        ])
        
        # Отправляем результат
        await bot.send_message(chat_id, final_message, reply_markup=keyboard)
        
        # Удаляем игру
        del active_games[chat_id]
        
    except Exception as e:
        print(f"❌ Ошибка завершения игры: {e}")

# Обработка ставок
@router.callback_query(F.data.startswith("bet_"))
async def bet_callback(callback: CallbackQuery):
    """Обработка ставок"""
    try:
        chat_id = callback.message.chat.id
        game = active_games.get(chat_id)
        
        if not game or not game.is_active:
            await callback.answer("❌ Игра уже завершена!", show_alert=True)
            return
        
        bet_type = callback.data.replace("bet_", "")
        
        # Отмена игры
        if bet_type == "cancel":
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
        
        # Проверяем пользователя
        user = await get_user(db, callback.from_user.id)
        if not user:
            await callback.answer("❌ Сначала пройди регистрацию через /start", show_alert=True)
            return
        
        # Проверяем баланс
        if user['balance'] < game.min_bet:
            await callback.answer(f"❌ Недостаточно монет! Минимум: {game.min_bet}💰", show_alert=True)
            return
        
        # Определяем ставку
        number = None
        bet_type_mapped = None
        
        if bet_type == "red":
            bet_type_mapped = "red"
        elif bet_type == "black":
            bet_type_mapped = "black"
        elif bet_type == "zero":
            bet_type_mapped = "zero"
        elif bet_type == "even":
            bet_type_mapped = "even"
        elif bet_type == "odd":
            bet_type_mapped = "odd"
        
        # Списываем монеты
        await update_balance(db, callback.from_user.id, -game.min_bet)
        
        # Добавляем ставку
        username = callback.from_user.username or callback.from_user.first_name
        success, message_text = game.add_bet(
            callback.from_user.id,
            username,
            bet_type_mapped,
            game.min_bet,
            number
        )
        
        if not success:
            # Возвращаем монеты если ставка не принята
            await update_balance(db, callback.from_user.id, game.min_bet)
            await callback.answer(message_text, show_alert=True)
            return
        
        await callback.answer(f"✅ {message_text}")
        
        # Обновляем сообщение
        await callback.message.edit_text(
            f"╔══════════════════════╗\n"
            f"║      🎰 РУЛЕТКА      ║\n"
            f"╚══════════════════════╝\n\n"
            f"🎮 Игра создана!\n"
            f"👤 Организатор: @{game.creator_name}\n"
            f"💰 Минимальная ставка: {game.min_bet} монет\n"
            f"⏳ Время на ставки: {GAME_TIMER} секунд\n\n"
            f"📊 Текущие ставки:\n{game.get_bets_text()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=get_bet_keyboard()
        )
        
    except Exception as e:
        print(f"❌ Ошибка ставки: {e}")
        await callback.answer("⚠️ Ошибка сервера", show_alert=True)

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

# Помощь
@router.callback_query(F.data == "roulette_help")
async def roulette_help_callback(callback: CallbackQuery):
    """Показать помощь по рулетке"""
    help_text = """
🎰 Игра "Рулетка": Как играть?

🔹 Виды ставок:
🎯 Число: Угадай конкретное число (0-36).
⠀Пример: Рулетка 7 500 (ставка 500 на число 7). Выигрыш ×50

🎲 Дюжина: Выбери группу чисел:
⠀1-ая (1-12), 2-ая (13-24), 3-я (25-36).
⠀Пример: Рулетка д2 300 (ставка 300 на 2-ю дюжину). Выигрыш ×3

🔴 Красное: Ставка на красное. Выигрыш ×2
⚫ Черное: Ставка на черное. Выигрыш ×2
🔢 Чет/Нечет: Ставка на чет/нечет. Выигрыш ×2
🟢 Зеро: Ставка на 0. Выигрыш ×100

🔹 Как играть:
1. Напиши 'рулетка' в чат
2. Игроки нажимают кнопки для ставок
3. Через 60 секунд рулетка крутится
4. Результат виден всем!

💡 Подсказка: Напиши 'лог' чтобы анализировать!
"""
    
    await callback.message.answer(help_text)
    await callback.answer()
