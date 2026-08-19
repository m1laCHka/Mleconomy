# handlers/cats.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from database.models import get_user, update_balance, update_stats
import random
import asyncio

router = Router()

# Константы
MIN_BET = 10
COMMISSION = 0.10
SOLO_TIMER = 15
MAX_CATS = 50
MAX_ATTEMPTS = 3

# Хранилище активных игр
active_cat_games = {}

class CatGame:
    def __init__(self, chat_id: int, creator_id: int, creator_name: str, bet: int, bot: Bot):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.bet = bet
        self.bot = bot
        self.is_active = True
        self.mode = None
        self.message_id = None
        self.timer_task = None
        
        self.opponent_id = None
        self.opponent_name = None
        self.is_accepted = False
        self.accept_timer_task = None
        
        self.cats = []
        self.yellow_count = 0
        self.black_count = 0
        
        self.creator_attempts = MAX_ATTEMPTS
        self.opponent_attempts = MAX_ATTEMPTS
        
        self.creator_guessed = False
        self.opponent_guessed = False
        self.solo_answered = False
    
    def generate_cats(self):
        total = random.randint(5, MAX_CATS)
        yellow = random.randint(1, total - 1)
        black = total - yellow
        
        self.yellow_count = yellow
        self.black_count = black
        
        self.cats = ['🐈'] * yellow + ['🐈‍⬛'] * black
        random.shuffle(self.cats)
    
    def get_cats_text(self) -> str:
        text = ""
        for i in range(0, len(self.cats), 10):
            text += " ".join(self.cats[i:i+10]) + "\n"
        return text.strip()
    
    def get_mode_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 Один", callback_data="cat_solo"),
                InlineKeyboardButton(text="👥 С кем-то", callback_data="cat_duel"),
            ]
        ])
    
    def get_accept_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять вызов", callback_data="cat_accept")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data="cat_decline")]
        ])

async def finish_solo_game(chat_id: int):
    try:
        await asyncio.sleep(SOLO_TIMER)
        
        game = active_cat_games.get(chat_id)
        if not game or not game.is_active or game.mode != "solo":
            return
        
        if game.solo_answered:
            return
        
        game.is_active = False
        
        text = (
            f"🐱 КОТИКИ — ВРЕМЯ ВЫШЛО\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 @{game.creator_name}\n"
            f"💰 Ставка: {game.bet} монет\n\n"
            f"{game.get_cats_text()}\n\n"
            f"❌ Время вышло!\n"
            f"✅ Правильный ответ: {game.yellow_count} ЖЕЛТЫХ котиков\n"
            f"💸 Ставка сгорела: {game.bet} монет"
        )
        
        await update_stats(db, game.creator_id, "cat", False)
        await game.bot.send_message(chat_id, text)
        
        del active_cat_games[chat_id]
    except Exception as e:
        print(f"❌ Ошибка завершения соло: {e}")

# Команда "котики"
@router.message(F.text.lower().startswith("котики"))
async def cats_start(message: Message):
    try:
        if message.chat.type == "private":
            await message.answer("❌ Котики доступны только в группах!")
            return
        
        if message.chat.id in active_cat_games and active_cat_games[message.chat.id].is_active:
            await message.answer("❌ В этом чате уже идет игра в котиков!")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Укажи ставку!\nПример: котики 100")
            return
        
        try:
            bet = int(parts[1])
        except:
            await message.answer("❌ Ставка должна быть числом!")
            return
        
        if bet < MIN_BET:
            await message.answer(f"❌ Минимальная ставка: {MIN_BET}💰")
            return
        
        user = await get_user(db, message.from_user.id)
        if not user:
            await message.answer("❌ Сначала пройди регистрацию через /start")
            return
        
        if user['balance'] < bet:
            await message.answer(f"❌ Недостаточно монет! У тебя: {user['balance']}💰")
            return
        
        await update_balance(db, message.from_user.id, -bet)
        
        creator_name = message.from_user.username or message.from_user.first_name
        game = CatGame(
            chat_id=message.chat.id,
            creator_id=message.from_user.id,
            creator_name=creator_name,
            bet=bet,
            bot=message.bot
        )
        active_cat_games[message.chat.id] = game
        
        msg = await message.answer(
            f"🐱 КОТИКИ\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 @{creator_name} запустил игру!\n"
            f"💰 Ставка: {bet} монет\n\n"
            f"Выбери режим:",
            reply_markup=game.get_mode_keyboard()
        )
        game.message_id = msg.message_id
        
    except Exception as e:
        print(f"❌ Ошибка создания игры: {e}")
        await message.answer("⚠️ Ошибка сервера")

# Обработка кнопок
@router.callback_query(F.data.startswith("cat_"))
async def cats_callback(callback: CallbackQuery):
    try:
        chat_id = callback.message.chat.id
        game = active_cat_games.get(chat_id)
        
        if not game or not game.is_active:
            await callback.answer("❌ Игра уже завершена!", show_alert=True)
            return
        
        action = callback.data.replace("cat_", "")
        user_id = callback.from_user.id
        
        if action == "solo":
            if user_id != game.creator_id:
                await callback.answer("❌ Только создатель может выбрать!", show_alert=True)
                return
            
            game.mode = "solo"
            game.generate_cats()
            
            await callback.answer("🎮 Одиночный режим!")
            
            await callback.message.edit_text(
                f"🐱 КОТИКИ — ОДИНОЧНЫЙ РЕЖИМ\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 @{game.creator_name}\n"
                f"💰 Ставка: {game.bet} монет\n\n"
                f"{game.get_cats_text()}\n\n"
                f"❓ Сколько ЖЕЛТЫХ котиков? (🐈)\n\n"
                f"⏳ {SOLO_TIMER} секунд на ответ!\n"
                f"✏️ Напиши число в чат"
            )
            
            game.timer_task = asyncio.create_task(finish_solo_game(chat_id))
            return
        
        if action == "duel":
            if user_id != game.creator_id:
                await callback.answer("❌ Только создатель может выбрать!", show_alert=True)
                return
            
            game.mode = "duel"
            
            await callback.answer("👥 Дуэльный режим!")
            
            await callback.message.edit_text(
                f"🐱 КОТИКИ — ДУЭЛЬ\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 @{game.creator_name} вызывает на игру!\n"
                f"💰 Ставка: {game.bet} монет\n\n"
                f"⏳ Ожидание противника...",
                reply_markup=game.get_accept_keyboard()
            )
            
            game.accept_timer_task = asyncio.create_task(accept_timeout(chat_id))
            return
        
        if action == "accept":
            if game.mode != "duel":
                await callback.answer("❌ Это не дуэль!", show_alert=True)
                return
            
            if user_id == game.creator_id:
                await callback.answer("❌ Нельзя играть с самим собой!", show_alert=True)
                return
            
            opponent = await get_user(db, user_id)
            if not opponent:
                await callback.answer("❌ Сначала пройди регистрацию!", show_alert=True)
                return
            
            if opponent['balance'] < game.bet:
                await callback.answer("❌ Недостаточно монет!", show_alert=True)
                return
            
            await update_balance(db, user_id, -game.bet)
            
            game.opponent_id = user_id
            game.opponent_name = callback.from_user.username or callback.from_user.first_name
            game.is_accepted = True
            
            if game.accept_timer_task:
                game.accept_timer_task.cancel()
            
            game.generate_cats()
            
            await callback.answer("✅ Игра началась!")
            
            await callback.message.edit_text(
                f"🐱 КОТИКИ — ДУЭЛЬ\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 @{game.creator_name} vs @{game.opponent_name}\n"
                f"💰 Банк: {game.bet * 2} монет\n\n"
                f"{game.get_cats_text()}\n\n"
                f"❓ Сколько ЖЕЛТЫХ котиков? (🐈)\n\n"
                f"🎯 У каждого {MAX_ATTEMPTS} попытки!\n"
                f"✏️ Пишите свои варианты в чат!"
            )
            return
        
        if action == "decline":
            if user_id == game.creator_id:
                await callback.answer("❌ Только противник может отклонить!", show_alert=True)
                return
            
            game.is_active = False
            if game.accept_timer_task:
                game.accept_timer_task.cancel()
            
            await update_balance(db, game.creator_id, game.bet)
            
            await callback.message.edit_text(
                f"🐱 КОТИКИ — ОТМЕНЕНА\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"❌ Вызов отклонен\n"
                f"💰 Ставка возвращена: {game.bet} монет"
            )
            
            del active_cat_games[chat_id]
            await callback.answer("Отклонено")
            return
        
    except Exception as e:
        print(f"❌ Ошибка в котиках: {e}")
        await callback.answer("⚠️ Ошибка сервера", show_alert=True)

async def accept_timeout(chat_id: int):
    await asyncio.sleep(60)
    
    if chat_id in active_cat_games and active_cat_games[chat_id].is_active and not active_cat_games[chat_id].is_accepted:
        game = active_cat_games[chat_id]
        game.is_active = False
        await update_balance(db, game.creator_id, game.bet)
        
        await game.bot.send_message(
            chat_id,
            f"🐱 КОТИКИ — ОТМЕНЕНА\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ Никто не принял вызов\n"
            f"💰 Ставка возвращена: {game.bet} монет"
        )
        
        del active_cat_games[chat_id]

# Обработка ВСЕХ сообщений для котиков (только числа)
@router.message()
async def cats_answer_handler(message: Message):
    """Обработчик для ответов в котиках"""
    try:
        chat_id = message.chat.id
        game = active_cat_games.get(chat_id)
        
        if not game or not game.is_active:
            return
        
        if not game.cats:
            return
        
        # Проверяем, что это число
        text = message.text.strip() if message.text else ""
        if not text.isdigit():
            return
        
        answer = int(text)
        user_id = message.from_user.id
        
        # Одиночный режим
        if game.mode == "solo":
            if user_id != game.creator_id:
                return
            
            if game.solo_answered:
                return
            
            game.solo_answered = True
            game.is_active = False
            
            if game.timer_task:
                game.timer_task.cancel()
            
            if answer == game.yellow_count:
                win_amount = int(game.bet * 1.8 * (1 - COMMISSION))
                await update_balance(db, user_id, win_amount)
                await update_stats(db, user_id, "cat", True)
                
                text = (
                    f"🐱 КОТИКИ — РЕЗУЛЬТАТ\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 @{game.creator_name}\n"
                    f"💰 Ставка: {game.bet} монет\n\n"
                    f"{game.get_cats_text()}\n\n"
                    f"✅ Правильный ответ: {game.yellow_count} ЖЕЛТЫХ котиков!\n\n"
                    f"🎉 @{game.creator_name} угадал!\n"
                    f"💰 Выигрыш: +{win_amount} монет"
                )
            else:
                await update_stats(db, user_id, "cat", False)
                
                text = (
                    f"🐱 КОТИКИ — РЕЗУЛЬТАТ\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 @{game.creator_name}\n"
                    f"💰 Ставка: {game.bet} монет\n\n"
                    f"{game.get_cats_text()}\n\n"
                    f"❌ Ответ: {answer} — неверно\n"
                    f"✅ Правильный ответ: {game.yellow_count} ЖЕЛТЫХ котиков\n\n"
                    f"💸 Ставка сгорела: {game.bet} монет"
                )
            
            await message.answer(text)
            del active_cat_games[chat_id]
            return
        
        # Дуэльный режим
        if game.mode == "duel":
            if not game.is_accepted:
                return
            
            if user_id not in [game.creator_id, game.opponent_id]:
                return
            
            if user_id == game.creator_id:
                if game.creator_attempts <= 0:
                    return
            else:
                if game.opponent_attempts <= 0:
                    return
            
            if answer == game.yellow_count:
                game.is_active = False
                winner_id = user_id
                winner_name = message.from_user.username or message.from_user.first_name
                
                win_amount = int((game.bet * 2) * (1 - COMMISSION))
                await update_balance(db, winner_id, win_amount)
                await update_stats(db, winner_id, "cat", True)
                
                loser_id = game.opponent_id if winner_id == game.creator_id else game.creator_id
                await update_stats(db, loser_id, "cat", False)
                
                text = (
                    f"🐱 КОТИКИ — ДУЭЛЬ ЗАВЕРШЕНА\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 @{game.creator_name} vs @{game.opponent_name}\n\n"
                    f"{game.get_cats_text()}\n\n"
                    f"✅ Правильный ответ: {game.yellow_count} ЖЕЛТЫХ котиков!\n\n"
                    f"🏆 ПОБЕДИТЕЛЬ: @{winner_name}\n"
                    f"💰 Выигрыш: +{win_amount} монет"
                )
                
                await message.answer(text)
                del active_cat_games[chat_id]
                return
            else:
                if user_id == game.creator_id:
                    game.creator_attempts -= 1
                    attempts_left = game.creator_attempts
                    player_name = game.creator_name
                else:
                    game.opponent_attempts -= 1
                    attempts_left = game.opponent_attempts
                    player_name = game.opponent_name
                
                if game.creator_attempts <= 0 and game.opponent_attempts <= 0:
                    game.is_active = False
                    await update_balance(db, game.creator_id, game.bet)
                    await update_balance(db, game.opponent_id, game.bet)
                    
                    text = (
                        f"🐱 КОТИКИ — НИЧЬЯ\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"👤 @{game.creator_name} vs @{game.opponent_name}\n\n"
                        f"{game.get_cats_text()}\n\n"
                        f"✅ Правильный ответ: {game.yellow_count} ЖЕЛТЫХ котиков\n\n"
                        f"🤝 Оба не угадали! Ставки возвращены!"
                    )
                    
                    await message.answer(text)
                    del active_cat_games[chat_id]
                    return
                
                await message.answer(
                    f"❌ @{player_name}: {answer} — неверно!\n"
                    f"🎯 Осталось попыток: {attempts_left}"
                )
            return
        
    except Exception as e:
        print(f"❌ Ошибка ответа: {e}")
