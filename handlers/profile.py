# handlers/profile.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database.db import db
from database.models import get_user, update_balance, update_stars
from keyboards.main_menu import get_main_menu

router = Router()

# Фото для профиля
FEMALE_PHOTO = "https://i.ibb.co/RMbs94m/584b2c22-ff9b-491f-bccf-63fa7e692f6a.jpg"
MALE_PHOTO = "https://i.ibb.co/pv7by3Y9/7e592789-6a08-4897-bfaa-054df3735f95.jpg"

def get_rank(wins: int, total_games: int) -> str:
    """Определить ранг игрока по винрейту"""
    if total_games < 10:
        return "🆕 Новобранец"
    
    winrate = (wins / total_games) * 100 if total_games > 0 else 0
    
    if winrate < 20:
        return "🥚 Новичок"
    elif winrate < 40:
        return "🪶 Любитель"
    elif winrate < 55:
        return "⚔️ Боец"
    elif winrate < 70:
        return "🛡️ Ветеран"
    elif winrate < 85:
        return "🏅 Мастер"
    elif winrate < 95:
        return "👑 Легенда"
    else:
        return "🌟 Бог игры"

def get_vip_status(user) -> str:
    """Получить статус VIP"""
    if user.get('is_vip'):
        return f"✅ VIP (до {user['vip_until']})"
    return "❌ Нет VIP"

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
        
        # Определяем отображаемое имя
        display_name = user.get('custom_nick') or f"@{user['username']}"
        
        # Вычисляем статистику
        total_games = user.get('total_games', 0)
        wins = user.get('wins', 0)
        losses = user.get('losses', 0)
        winrate = (wins / total_games * 100) if total_games > 0 else 0
        
        # Определяем лучшую игру
        best_game = "Нет игр"
        best_winrate = 0
        
        games_stats = {
            "🎰 Рулетка": (user.get('roulette_wins', 0), user.get('roulette_games', 0)),
            "🤠 Дуэль": (user.get('duel_wins', 0), user.get('duel_games', 0)),
            "🐱 Котики": (user.get('cat_wins', 0), user.get('cat_games', 0)),
            "🎰 Казино": (user.get('casino_wins', 0), user.get('casino_games', 0))
        }
        
        for game_name, (game_wins, game_total) in games_stats.items():
            if game_total > 0:
                game_winrate = (game_wins / game_total) * 100
                if game_winrate > best_winrate:
                    best_winrate = game_winrate
                    best_game = f"{game_name} ({game_winrate:.1f}%)"
        
        # Получаем ранг
        rank = get_rank(wins, total_games)
        
        # Получаем VIP статус
        vip_status = get_vip_status(user)
        
        # Формируем профиль
        profile_text = f"""
👤 **ПРОФИЛЬ ИГРОКА**

📱 **ID:** `{user['user_id']}`
📝 **Имя:** {display_name}
🏅 **Ранг:** {rank}
💎 **VIP:** {vip_status}

💰 **Баланс:** {user.get('balance', 0)} 💵
⭐ **Звёзды:** {user.get('stars', 0)}

📊 **Общая статистика:**
• Игр сыграно: {total_games}
• Побед: {wins}
• Поражений: {losses}
• Винрейт: {winrate:.1f}%

🎯 **Лучшая игра:** {best_game}

🏆 **Достижения:**
• Турнирные очки: {user.get('tournament_score', 0)}
• Квестов выполнено: {user.get('quests_completed', 0)}

👨‍👩‍👧 **Семья:** {'Есть' if user.get('family_id') else 'Нет'}

📅 **Регистрация:** {user['created_at'].strftime('%d.%m.%Y') if user.get('created_at') else 'Неизвестно'}
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

async def show_statistics(message: Message, user_id: int):
    """Показать подробную статистику игр"""
    try:
        user = await get_user(db, user_id)
        
        if not user:
            await message.answer(
                "❌ Сначала пройди регистрацию через /start",
                reply_markup=get_main_menu()
            )
            return
        
        # Статистика по каждой игре
        stats_text = f"""
📊 **СТАТИСТИКА ИГР**

🎰 **Рулетка:**
• Побед: {user.get('roulette_wins', 0)}/{user.get('roulette_games', 0)}
• Винрейт: {(user.get('roulette_wins', 0) / user.get('roulette_games', 1) * 100):.1f}%

🤠 **Дуэли:**
• Побед: {user.get('duel_wins', 0)}/{user.get('duel_games', 0)}
• Винрейт: {(user.get('duel_wins', 0) / user.get('duel_games', 1) * 100):.1f}%

🐱 **Котики:**
• Побед: {user.get('cat_wins', 0)}/{user.get('cat_games', 0)}
• Винрейт: {(user.get('cat_wins', 0) / user.get('cat_games', 1) * 100):.1f}%

🎰 **Казино:**
• Побед: {user.get('casino_wins', 0)}/{user.get('casino_games', 0)}
• Винрейт: {(user.get('casino_wins', 0) / user.get('casino_games', 1) * 100):.1f}%

📈 **Общая статистика:**
• Всего игр: {user.get('total_games', 0)}
• Всего побед: {user.get('wins', 0)}
• Всего поражений: {user.get('losses', 0)}
• Общий винрейт: {(user.get('wins', 0) / user.get('total_games', 1) * 100):.1f}%
"""
        
        await message.answer(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        await message.answer(
            "⚠️ Ошибка сервера, попробуй позже",
            reply_markup=get_main_menu()
        )

@router.message(Command("profile"))
async def profile_command(message: Message):
    """Команда /profile"""
    await show_profile(message, message.from_user.id)

@router.message(Command("p"))
async def profile_short_command(message: Message):
    """Команда /p"""
    await show_profile(message, message.from_user.id)

@router.message(F.text == "👤 Профиль")
async def profile_button(message: Message):
    """Кнопка профиля"""
    await show_profile(message, message.from_user.id)

@router.message(Command("statistics"))
async def statistics_command(message: Message):
    """Команда /statistics"""
    await show_statistics(message, message.from_user.id)

@router.message(Command("stats"))
async def stats_command(message: Message):
    """Команда /stats"""
    await show_statistics(message, message.from_user.id)

@router.message(Command("стата"))
async def stats_ru_command(message: Message):
    """Команда /стата"""
    await show_statistics(message, message.from_user.id)

@router.message(F.text == "📊 Статистика")
async def statistics_button(message: Message):
    """Кнопка статистики"""
    await show_statistics(message, message.from_user.id)
