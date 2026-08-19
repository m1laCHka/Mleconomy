# handlers/duel.py

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
MIN_BET = 10
COMMISSION = 0.10  # 10% комиссия
ACCEPT_TIMER = 60   # секунд на принятие
TURN_TIMER = 120    # секунд на ход

# Фото для дуэли
DUEL_PHOTO = "https://i.ibb.co/d4WXhwSV/345580c2-5ad0-435c-8ae4-ed6ad56ad6a2.jpg"

# Хранилище активных дуэлей
active_duels = {}

class DuelGame:
    def __init__(self, chat_id: int, creator_id: int, creator_name: str, opponent_id: int, opponent_name: str, bet: int, bot: Bot):
        self.chat_id = chat_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.opponent_id = opponent_id
        self.opponent_name = opponent_name
        self.bet = bet
        self.bot = bot
        self.is_active = True
        self.is_accepted = False
        self.message_id = None
        self.accept_timer_task = None
        self.turn_timer_task = None

        # Здоровье
        self.creator_hp = 100
        self.opponent_hp = 100

        # Ходы (для одновременной системы)
        self.creator_moved = False
        self.opponent_moved = False
        self.creator_damage = 0
        self.opponent_damage = 0
        self.creator_dodged = False
        self.opponent_dodged = False
        
        self.round = 1
        self.last_attack_time = datetime.now()

    def get_hp_bar(self, hp: int) -> str:
        """Красивый HP бар"""
        filled = int(hp / 10)
        empty = 10 - filled
        return f"{'▰' * filled}{'▱' * empty}"

    def get_status_text(self) -> str:
        """Текст текущего состояния дуэли"""
        return (
            f"⚔️ ДУЭЛЬ — РАУНД {self.round}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 @{self.creator_name} vs @{self.opponent_name}\n"
            f"💰 Банк: {self.bet * 2} монет\n\n"
            f"❤️ @{self.creator_name}: {self.creator_hp} HP\n"
            f"{self.get_hp_bar(self.creator_hp)}\n\n"
            f"❤️ @{self.opponent_name}: {self.opponent_hp} HP\n"
            f"{self.get_hp_bar(self.opponent_hp)}\n\n"
            f"⏳ Ожидание ходов обоих игроков...\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

    def reset_round(self):
        """Сбросить ходы для нового раунда"""
        self.creator_moved = False
        self.opponent_moved = False
        self.creator_damage = 0
        self.opponent_damage = 0
        self.creator_dodged = False
        self.opponent_dodged = False
        self.round += 1
        self.last_attack_time = datetime.now()

async def finish_duel(chat_id: int, winner_id: int = None, reason: str = "win"):
    """Завершить дуэль"""
    try:
        duel = active_duels.get(chat_id)
        if not duel or not duel.is_active:
            return

        duel.is_active = False
        
        if duel.accept_timer_task:
            duel.accept_timer_task.cancel()
        if duel.turn_timer_task:
            duel.turn_timer_task.cancel()

        if reason == "cancel" or reason == "no_accept":
            await update_balance(db, duel.creator_id, duel.bet)
            text = (
                f"⚔️ ДУЭЛЬ ОТМЕНЕНА\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"❌ {'Никто не принял вызов' if reason == 'no_accept' else 'Дуэль отменена'}\n"
                f"💰 Ставка возвращена: {duel.bet} монет"
            )
        elif reason == "draw":
            await update_balance(db, duel.creator_id, duel.bet)
            await update_balance(db, duel.opponent_id, duel.bet)
            text = (
                f"⚔️ ДУЭЛЬ — НИЧЬЯ!\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💀 @{duel.creator_name}: {duel.creator_hp} HP\n"
                f"💀 @{duel.opponent_name}: {duel.opponent_hp} HP\n\n"
                f"🤝 НИЧЬЯ! Ставки возвращены!"
            )
            await update_stats(db, duel.creator_id, "duel", False)
            await update_stats(db, duel.opponent_id, "duel", False)
        elif reason == "surrender":
            winner_name = duel.opponent_name if winner_id == duel.opponent_id else duel.creator_name
            loser_name = duel.creator_name if winner_id == duel.opponent_id else duel.opponent_name
            win_amount = int((duel.bet * 2) * (1 - COMMISSION))
            await update_balance(db, winner_id, win_amount)
            text = (
                f"⚔️ ДУЭЛЬ ЗАВЕРШЕНА\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏳️ @{loser_name} сдался!\n"
                f"🏆 ПОБЕДИТЕЛЬ: @{winner_name}\n"
                f"💰 Выигрыш: {win_amount} монет"
            )
            loser_id = duel.creator_id if winner_id == duel.opponent_id else duel.opponent_id
            await update_stats(db, winner_id, "duel", True)
            await update_stats(db, loser_id, "duel", False)
        elif reason == "timeout":
            winner_name = duel.opponent_name if winner_id == duel.opponent_id else duel.creator_name
            loser_name = duel.creator_name if winner_id == duel.opponent_id else duel.opponent_name
            win_amount = int((duel.bet * 2) * (1 - COMMISSION))
            await update_balance(db, winner_id, win_amount)
            text = (
                f"⚔️ ДУЭЛЬ ЗАВЕРШЕНА\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⏰ @{loser_name} не успел сходить!\n"
                f"🏆 ПОБЕДИТЕЛЬ: @{winner_name}\n"
                f"💰 Выигрыш: {win_amount} монет"
            )
            loser_id = duel.creator_id if winner_id == duel.opponent_id else duel.opponent_id
            await update_stats(db, winner_id, "duel", True)
            await update_stats(db, loser_id, "duel", False)
        else:
            winner_name = duel.opponent_name if winner_id == duel.opponent_id else duel.creator_name
            win_amount = int((duel.bet * 2) * (1 - COMMISSION))
            await update_balance(db, winner_id, win_amount)
            text = (
                f"⚔️ ДУЭЛЬ ЗАВЕРШЕНА\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏆 ПОБЕДИТЕЛЬ: @{winner_name}\n"
                f"💰 Выигрыш: {win_amount} монет\n\n"
                f"❤️ @{duel.creator_name}: {duel.creator_hp} HP\n"
                f"❤️ @{duel.opponent_name}: {duel.opponent_hp} HP"
            )
            loser_id = duel.opponent_id if winner_id == duel.creator_id else duel.creator_id
            await update_stats(db, winner_id, "duel", True)
            await update_stats(db, loser_id, "duel", False)

        try:
            await duel.bot.send_photo(
                chat_id=chat_id,
                photo=DUEL_PHOTO,
                caption=text
            )
        except Exception as e:
            print(f"❌ Ошибка отправки результата дуэли: {e}")

        del active_duels[chat_id]

    except Exception as e:
        print(f"❌ Ошибка завершения дуэли: {e}")

async def duel_turn_timeout(chat_id: int):
    """Таймер на ход"""
    await asyncio.sleep(TURN_TIMER)
    
    if chat_id in active_duels and active_duels[chat_id].is_active and active_duels[chat_id].is_accepted:
        duel = active_duels[chat_id]
        
        if not duel.creator_moved and duel.opponent_moved:
            await finish_duel(chat_id, duel.opponent_id, "timeout")
        elif not duel.opponent_moved and duel.creator_moved:
            await finish_duel(chat_id, duel.creator_id, "timeout")
        elif not duel.creator_moved and not duel.opponent_moved:
            winner = random.choice([duel.creator_id, duel.opponent_id])
            await finish_duel(chat_id, winner, "timeout")

# Команда "дуэль"
@router.message(F.text.lower().startswith("дуэль"))
async def duel_start(message: Message):
    """Начать дуэль"""
    try:
        if message.chat.type == "private":
            await message.answer("❌ Дуэль доступна только в группах!")
            return

        if not message.reply_to_message:
            await message.answer("❌ Ответь на сообщение противника!\nПример: дуэль 100")
            return

        opponent = message.reply_to_message.from_user
        if opponent.id == message.from_user.id:
            await message.answer("❌ Нельзя вызвать на дуэль самого себя!")
            return

        if message.chat.id in active_duels and active_duels[message.chat.id].is_active:
            await message.answer("❌ В этом чате уже идет дуэль!")
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Укажи ставку!\nПример: дуэль 100")
            return

        try:
            bet = int(parts[1])
        except:
            await message.answer("❌ Ставка должна быть числом!")
            return

        if bet < MIN_BET:
            await message.answer(f"❌ Минимальная ставка: {MIN_BET}💰")
            return

        creator = await get_user(db, message.from_user.id)
        if not creator:
            await message.answer("❌ Сначала пройди регистрацию через /start")
            return

        if creator['balance'] < bet:
            await message.answer(f"❌ Недостаточно монет! У тебя: {creator['balance']}💰")
            return

        opponent_user = await get_user(db, opponent.id)
        if not opponent_user:
            await message.answer("❌ Противник не зарегистрирован в боте!")
            return

        if opponent_user['balance'] < bet:
            await message.answer(f"❌ У противника недостаточно монет! У него: {opponent_user['balance']}💰")
            return

        await update_balance(db, message.from_user.id, -bet)

        creator_name = message.from_user.username or message.from_user.first_name
        opponent_name = opponent.username or opponent.first_name
        duel = DuelGame(
            chat_id=message.chat.id,
            creator_id=message.from_user.id,
            creator_name=creator_name,
            opponent_id=opponent.id,
            opponent_name=opponent_name,
            bet=bet,
            bot=message.bot
        )
        active_duels[message.chat.id] = duel

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять вызов", callback_data="duel_accept")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data="duel_decline")]
        ])

        msg = await message.answer_photo(
            photo=DUEL_PHOTO,
            caption=(
                f"⚔️ ДУЭЛЬ\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 @{creator_name} вызывает на дуэль!\n"
                f"🎯 Противник: @{opponent_name}\n"
                f"💰 Ставка: {bet} монет\n\n"
                f"⏳ Ожидание принятия: {ACCEPT_TIMER} секунд"
            ),
            reply_markup=keyboard
        )
        duel.message_id = msg.message_id

        duel.accept_timer_task = asyncio.create_task(duel_accept_timeout(message.chat.id))

    except Exception as e:
        print(f"❌ Ошибка создания дуэли: {e}")
        await message.answer("⚠️ Ошибка сервера")

async def duel_accept_timeout(chat_id: int):
    """Таймер на принятие дуэли"""
    await asyncio.sleep(ACCEPT_TIMER)
    
    if chat_id in active_duels and active_duels[chat_id].is_active and not active_duels[chat_id].is_accepted:
        await finish_duel(chat_id, reason="no_accept")

# Обработка кнопок дуэли
@router.callback_query(F.data.startswith("duel_"))
async def duel_callback(callback: CallbackQuery):
    """Обработка кнопок дуэли"""
    try:
        chat_id = callback.message.chat.id
        duel = active_duels.get(chat_id)

        if not duel or not duel.is_active:
            await callback.answer("❌ Дуэль уже завершена!", show_alert=True)
            return

        action = callback.data.replace("duel_", "")
        user_id = callback.from_user.id

        if action == "accept":
            if user_id != duel.opponent_id:
                await callback.answer("❌ Только противник может принять вызов!", show_alert=True)
                return

            opponent = await get_user(db, user_id)
            if opponent['balance'] < duel.bet:
                await callback.answer("❌ Недостаточно монет!", show_alert=True)
                return

            await update_balance(db, user_id, -duel.bet)
            duel.is_accepted = True
            if duel.accept_timer_task:
                duel.accept_timer_task.cancel()

            await callback.answer("✅ Дуэль началась!")

            await callback.message.edit_caption(
                caption=duel.get_status_text(),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⚔️ Атаковать", callback_data="duel_attack")],
                    [InlineKeyboardButton(text="🏳️ Сдаться", callback_data="duel_surrender")]
                ])
            )

            duel.turn_timer_task = asyncio.create_task(duel_turn_timeout(chat_id))
            return

        if action == "decline":
            if user_id != duel.opponent_id:
                await callback.answer("❌ Только противник может отклонить!", show_alert=True)
                return
            await finish_duel(chat_id, reason="no_accept")
            await callback.answer("Дуэль отклонена")
            return

        if action == "waiting":
            await callback.answer("⏳ Ожидай противника...")
            return

        if action == "attack":
            if not duel.is_accepted:
                await callback.answer("❌ Дуэль еще не началась!", show_alert=True)
                return

            if user_id not in [duel.creator_id, duel.opponent_id]:
                await callback.answer("❌ Ты не участвуешь в дуэли!", show_alert=True)
                return

            if user_id == duel.creator_id and duel.creator_moved:
                await callback.answer("✅ Ты уже сделал ход!", show_alert=True)
                return
            if user_id == duel.opponent_id and duel.opponent_moved:
                await callback.answer("✅ Ты уже сделал ход!", show_alert=True)
                return

            dodged = random.random() < 0.15
            damage = random.randint(1, 50)  # ← УРОН 1-50

            if user_id == duel.creator_id:
                duel.creator_moved = True
                duel.creator_damage = damage
                duel.creator_dodged = dodged
            else:
                duel.opponent_moved = True
                duel.opponent_damage = damage
                duel.opponent_dodged = dodged

            await callback.answer(f"⚔️ Урон: {damage} HP" + (" 💨" if dodged else ""))

            if duel.creator_moved and duel.opponent_moved:
                if not duel.creator_dodged:
                    duel.creator_hp -= duel.opponent_damage
                if not duel.opponent_dodged:
                    duel.opponent_hp -= duel.creator_damage

                if duel.creator_hp <= 0 and duel.opponent_hp <= 0:
                    await finish_duel(chat_id, reason="draw")
                    await callback.answer("💀 Ничья!")
                    return
                elif duel.creator_hp <= 0:
                    await finish_duel(chat_id, duel.opponent_id)
                    await callback.answer("💥 Победа!")
                    return
                elif duel.opponent_hp <= 0:
                    await finish_duel(chat_id, duel.creator_id)
                    await callback.answer("💥 Победа!")
                    return

                result_text = (
                    f"⚔️ ДУЭЛЬ — РАУНД {duel.round}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                
                if duel.creator_dodged:
                    result_text += f"💨 @{duel.creator_name} увернулся!\n"
                else:
                    result_text += f"💥 @{duel.opponent_name} нанес {duel.opponent_damage} урона!\n"
                
                if duel.opponent_dodged:
                    result_text += f"💨 @{duel.opponent_name} увернулся!\n"
                else:
                    result_text += f"💥 @{duel.creator_name} нанес {duel.creator_damage} урона!\n"
                
                duel.reset_round()
                
                result_text += (
                    f"\n❤️ @{duel.creator_name}: {duel.creator_hp} HP\n"
                    f"{duel.get_hp_bar(duel.creator_hp)}\n\n"
                    f"❤️ @{duel.opponent_name}: {duel.opponent_hp} HP\n"
                    f"{duel.get_hp_bar(duel.opponent_hp)}\n\n"
                    f"⏳ Ожидание ходов...\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )

                await callback.message.edit_caption(
                    caption=result_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⚔️ Атаковать", callback_data="duel_attack")],
                        [InlineKeyboardButton(text="🏳️ Сдаться", callback_data="duel_surrender")]
                    ])
                )

                if duel.turn_timer_task:
                    duel.turn_timer_task.cancel()
                duel.turn_timer_task = asyncio.create_task(duel_turn_timeout(chat_id))
            else:
                await callback.message.edit_caption(
                    caption=(
                        f"⚔️ ДУЭЛЬ — РАУНД {duel.round}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"⏳ Ожидание хода противника..."
                    ),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⏳ Ожидание...", callback_data="duel_waiting")]
                    ])
                )
            return

        if action == "surrender":
            if user_id not in [duel.creator_id, duel.opponent_id]:
                await callback.answer("❌ Ты не участвуешь в дуэли!", show_alert=True)
                return

            winner_id = duel.opponent_id if user_id == duel.creator_id else duel.creator_id
            await finish_duel(chat_id, winner_id, "surrender")
            await callback.answer("🏳️ Ты сдался!")
            return

    except Exception as e:
        print(f"❌ Ошибка в дуэли: {e}")
        await callback.answer("⚠️ Ошибка сервера", show_alert=True)
