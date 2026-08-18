# handlers/profile.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database.db import db
from database.models import get_user
from keyboards.main_menu import get_main_menu

router = Router()

# Фото для профиля
FEMALE_PHOTO = "https://i.ibb.co/RMbs94m/584b2c22-ff9b-491f-bccf-63fa7e692f6a.jpg"
MALE_PHOTO = "https://i.ibb.co/pv7by3Y9/7e592789-6a08-4897-bfaa-054df3735f95.jpg"

def is_private_chat(message: Message) -> bool:
    """Проверка, является ли чат личным"""
    return message.chat.type == "private"

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

def safe_winrate(wins: int, total: int) -> float:
    """Безопасное вычисление винрейта"""
    if total > 0:
        return (wins / total) * 100
    return 0.0

async def show_profile(message: Message, user_id: int):
    """Показать профиль пользователя"""
    try:
        user = await get_user(db, user_id)
        
        if not user:
            await message.answer(
                "❌ Сначала пройди регистрацию через /start"
            )
            return
        
        # Выбираем фото в зависимости от пола
        photo = FEMALE_PHOTO if user.get('gender') == 'female' else MALE_PHOTO
        
        # Определяем отображаемое имя
        display_name = user.get('custom_nick') or f"@{user.get('username', 'User')}"
        
        # Вычисляем статистику с защитой от None
        total_games = user.get('total_games') or 0
        wins = user.get('wins') or 0
        losses = user.get('losses') or 0
        winrate = safe_winrate(wins, total_games)
        
        # Определяем лучшую игру
        best_game = "Нет игр"
        best_winrate = 0.0
        
        games_stats = {
            "🎰 Рулетка": (user.get('roulette_wins') or 0, user.get('roulette_games') or 0),
            "🤠 Дуэль": (user.get('duel_wins') or 0, user.get('duel_games') or 0),
            "🐱 Котики": (user.get('cat_wins') or 0, user.get('cat_games') or 0),
            "🎰 Казино": (user.get('casino_wins') or 0, user.get('casino_games') or 0)
        }
        
        for game_name, (game_wins, game_total) in games_stats.items():
            if game_total > 0:
                game_winrate = safe_winrate(game_wins, game_total)
                if game_winrate > best_winrate:
                    best_winrate = game_winrate
                    best_game = f"{game_name} ({game_winrate:.1f}%)"
        
        # Получаем ранг
        rank = get_rank(wins, total_games)
        
        # Получаем VIP статус
        vip_status = get_vip_status(user)
        
        # Получаем баланс и звёзды с защитой
        balance = user.get('balance') or 0
        stars = user.get('stars') or 0
        
        # Получаем дату регистрации
        created_at = user.get('created_at')
        if created_at:
            created_date = created_at.strftime('%d.%m.%Y')
        else:
            created_date = "Неизвестно"
        
        # Формируем профиль
        profile_text = f"""
👤 ПРОФИЛЬ ИГРОКА

📱 ID: {user['user_id']}
📝 Имя: {display_name}
🏅 Ранг: {rank}
💎 VIP: {vip_status}

💰 Баланс: {balance} 💵
⭐ Звёзды: {stars}

📊 Общая статистика:
• Игр сыграно: {total_games}
• Побед: {wins}
• Поражений: {losses}
• Винрейт: {winrate:.1f}%

🎯 Лучшая игра: {best_game}

🏆 Достижения:
• Турнирные очки: {user.get('tournament_score') or 0}
• Квестов выполнено: {user.get('quests_completed') or 0}

👨‍👩‍👧 Семья: {'Есть' if user.get('family_id') else 'Нет'}

📅 Регистрация: {created_date}
"""
        
        # Показываем меню только в личных сообщениях
        if is_private_chat(message):
            await message.answer_photo(
                photo=photo,
                caption=profile_text,
                reply_markup=get_main_menu()
            )
        else:
            # В группах без меню
            await message.answer_photo(
                photo=photo,
                caption=profile_text
            )
    except Exception as e:
        print(f"❌ Ошибка получения профиля: {e}")
        await message.answer(
            "⚠️ Ошибка сервера, попробуй позже"
        )

async def show_statistics(message: Message, user_id: int):
    """Показать подробную статистику игр"""
    try:
        user = await get_user(db, user_id)
        
        if not user:
            await message.answer(
                "❌ Сначала пройди регистрацию через /start"
            )
            return
        
        # Получаем все значения с защитой от None
        roulette_wins = user.get('roulette_wins') or 0
        roulette_games = user.get('roulette_games') or 0
        duel_wins = user.get('duel_wins') or 0
        duel_games = user.get('duel_games') or 0
        cat_wins = user.get('cat_wins') or 0
        cat_games = user.get('cat_games') or 0
        casino_wins = user.get('casino_wins') or 0
        casino_games = user.get('casino_games') or 0
        total_wins = user.get('wins') or 0
        total_games = user.get('total_games') or 0
        total_losses = user.get('losses') or 0
        
        # Статистика по каждой игре
        stats_text = f"""
📊 СТАТИСТИКА ИГР

🎰 Рулетка:
• Побед: {roulette_wins}/{roulette_games}
• Винрейт: {safe_winrate(roulette_wins, roulette_games):.1f}%

🤠 Дуэли:
• Побед: {duel_wins}/{duel_games}
• Винрейт: {safe_winrate(duel_wins, duel_games):.1f}%

🐱 Котики:
• Побед: {cat_wins}/{cat_games}
• Винрейт: {safe_winrate(cat_wins, cat_games):.1f}%

🎰 Казино:
• Побед: {casino_wins}/{casino_games}
• Винрейт: {safe_winrate(casino_wins, casino_games):.1f}%

📈 Общая статистика:
• Всего игр: {total_games}
• Всего побед: {total_wins}
• Всего поражений: {total_losses}
• Общий винрейт: {safe_winrate(total_wins, total_games):.1f}%

💡 Играй в игры, чтобы увидеть статистику!
"""
        
        # Показываем меню только в личных сообщениях
        if is_private_chat(message):
            await message.answer(
                stats_text,
                reply_markup=get_main_menu()
            )
        else:
            # В группах без меню
            await message.answer(stats_text)
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        await message.answer(
            "⚠️ Ошибка сервера, попробуй позже"
        )

# Обработчики команд

@router.message(Command("profile"))
async def profile_command(message: Message):
    """Команда /profile"""
    await show_profile(message, message.from_user.id)

@router.message(Command("p"))
async def profile_short_command(message: Message):
    """Команда /p"""
    await show_profile(message, message.from_user.id)

@router.message(Command("профиль"))
async def profile_ru_command(message: Message):
    """Команда /профиль"""
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

@router.message(Command("stat"))
async def stat_command(message: Message):
    """Команда /stat"""
    await show_statistics(message, message.from_user.id)

@router.message(Command("статистика"))
async def statistics_ru_command(message: Message):
    """Команда /статистика"""
    await show_statistics(message, message.from_user.id)

@router.message(Command("стата"))
async def stats_ru_command(message: Message):
    """Команда /стата"""
    await show_statistics(message, message.from_user.id)

@router.message(F.text == "📊 Статистика")
async def statistics_button(message: Message):
    """Кнопка статистики"""
    await show_statistics(message, message.from_user.id)
