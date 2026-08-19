# handlers/admin.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import ADMIN_ID

router = Router()

# Хранилище состояний админа (для настройки промокодов)
admin_states = {}

def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    return user_id == ADMIN_ID

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    # Получаем количество промокодов по умолчанию
    default_uses = admin_states.get("default_uses", 100)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🎫 Создать промокод", callback_data="admin_create_promo")],
        [InlineKeyboardButton(text=f"📋 Промолист [{default_uses}]", callback_data="admin_promo_list")],
        [InlineKeyboardButton(text="⚙️ Лимит промокодов", callback_data="admin_set_limit")],
        [InlineKeyboardButton(text="🗑️ Удалить промокод", callback_data="admin_delete_promo")],
        [InlineKeyboardButton(text="💰 Накрутить монеты", callback_data="admin_add_coins")],
        [InlineKeyboardButton(text="⭐ Накрутить звёзды", callback_data="admin_add_stars")],
        [InlineKeyboardButton(text="🗑️ Очистить все данные", callback_data="admin_clear_all")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
    ])
    return keyboard

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    return keyboard

def get_confirm_clear_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение очистки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить всё!", callback_data="admin_confirm_clear")],
        [InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin_back")]
    ])
    return keyboard

def get_promo_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа промокода"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Монеты", callback_data="promo_type_coins")],
        [InlineKeyboardButton(text="⭐ Звёзды", callback_data="promo_type_stars")],
        [InlineKeyboardButton(text="💰⭐ Всё вместе", callback_data="promo_type_both")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    return keyboard

@router.message(Command("admin"))
async def admin_command(message: Message):
    """Команда /admin"""
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ У вас нет доступа к админ-панели!")
            return
        
        await message.answer(
            "👑 АДМИН-ПАНЕЛЬ\n\n"
            "Выберите действие:",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        print(f"❌ Ошибка админ-панели: {e}")

@router.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery):
    """Обработка кнопок админ-панели"""
    try:
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Ты не админ!", show_alert=True)
            return
        
        action = callback.data.replace("admin_", "")
        
        if action == "back":
            await callback.message.edit_text(
                "👑 АДМИН-ПАНЕЛЬ\n\nВыберите действие:",
                reply_markup=get_admin_keyboard()
            )
            await callback.answer()
            return
        
        if action == "close":
            await callback.message.delete()
            await callback.answer("Панель закрыта")
            return
        
        if action == "stats":
            total_users = await db.fetchval("SELECT COUNT(*) FROM users") or 0
            total_coins = await db.fetchval("SELECT COALESCE(SUM(balance), 0) FROM users") or 0
            total_stars = await db.fetchval("SELECT COALESCE(SUM(stars), 0) FROM users") or 0
            total_games = await db.fetchval("SELECT COALESCE(SUM(total_games), 0) FROM users") or 0
            total_promos = await db.fetchval("SELECT COUNT(*) FROM promos") or 0
            
            stats_text = (
                f"📊 СТАТИСТИКА БОТА\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👥 Пользователей: {total_users}\n"
                f"💰 Монет в игре: {total_coins}\n"
                f"⭐ Звёзд в игре: {total_stars}\n"
                f"🎮 Всего игр: {total_games}\n"
                f"🎫 Промокодов: {total_promos}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            await callback.message.edit_text(stats_text, reply_markup=get_back_keyboard())
            await callback.answer()
            return
        
        if action == "create_promo":
            await callback.message.edit_text(
                "🎫 СОЗДАНИЕ ПРОМОКОДА\n\n"
                "Выбери тип промокода:",
                reply_markup=get_promo_type_keyboard()
            )
            await callback.answer()
            return
        
        if action == "set_limit":
            admin_states[callback.from_user.id] = {"state": "set_limit"}
            await callback.message.edit_text(
                "⚙️ ЛИМИТ ПРОМОКОДОВ\n\n"
                "Напиши число — сколько раз можно использовать новые промокоды:\n\n"
                "Пример: 50",
                reply_markup=get_back_keyboard()
            )
            await callback.answer()
            return
        
        if action == "promo_list":
            promos = await db.fetch("SELECT code, stars, coins, max_uses, uses FROM promos ORDER BY created_at DESC")
            
            if not promos:
                await callback.message.edit_text(
                    "📋 ПРОМОКОДЫ\n\n"
                    "❌ Нет созданных промокодов",
                    reply_markup=get_back_keyboard()
                )
            else:
                text = "📋 ПРОМОКОДЫ\n━━━━━━━━━━━━━━━━━━━━\n\n"
                for promo in promos:
                    text += (
                        f"🎫 <code>{promo['code']}</code>\n"
                        f"⭐ {promo['stars']} | 💰 {promo['coins']}\n"
                        f"📊 {promo['uses']}/{promo['max_uses']}\n\n"
                    )
                
                await callback.message.edit_text(
                    text,
                    reply_markup=get_back_keyboard(),
                    parse_mode="HTML"
                )
            await callback.answer()
            return
        
        if action == "delete_promo":
            await callback.message.edit_text(
                "🗑️ УДАЛЕНИЕ ПРОМОКОДА\n\n"
                "Напиши:\n"
                "/delete_promo КОД",
                reply_markup=get_back_keyboard()
            )
            await callback.answer()
            return
        
        if action == "add_coins":
            await callback.message.edit_text(
                "💰 НАКРУТКА МОНЕТ\n\n"
                "Напиши:\n"
                "/add_coins @user СУММА",
                reply_markup=get_back_keyboard()
            )
            await callback.answer()
            return
        
        if action == "add_stars":
            await callback.message.edit_text(
                "⭐ НАКРУТКА ЗВЁЗД\n\n"
                "Напиши:\n"
                "/add_stars @user СУММА",
                reply_markup=get_back_keyboard()
            )
            await callback.answer()
            return
        
        if action == "clear_all":
            await callback.message.edit_text(
                "⚠️ ВНИМАНИЕ!\n\n"
                "Удалить ВСЕ ДАННЫЕ?",
                reply_markup=get_confirm_clear_keyboard()
            )
            await callback.answer()
            return
        
        if action == "confirm_clear":
            await db.execute("DELETE FROM user_promos")
            await db.execute("DELETE FROM achievements")
            await db.execute("DELETE FROM children")
            await db.execute("DELETE FROM families")
            await db.execute("DELETE FROM promos")
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM roulette_logs")
            
            await callback.message.edit_text(
                "✅ ВСЕ ДАННЫЕ УДАЛЕНЫ!",
                reply_markup=get_back_keyboard()
            )
            await callback.answer("✅ Данные очищены!", show_alert=True)
            return
        
    except Exception as e:
        print(f"❌ Ошибка админ-панели: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

# ============ ВЫБОР ТИПА ПРОМОКОДА ============

@router.callback_query(F.data.startswith("promo_type_"))
async def promo_type_callback(callback: CallbackQuery):
    """Выбор типа промокода"""
    try:
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Ты не админ!", show_alert=True)
            return
        
        promo_type = callback.data.replace("promo_type_", "")
        
        if promo_type == "coins":
            admin_states[callback.from_user.id] = {"state": "create_promo_coins"}
            await callback.message.edit_text(
                "💰 ПРОМОКОД НА МОНЕТЫ\n\n"
                "Напиши:\n"
                "/create [код] [количество монет]\n\n"
                "Пример:\n"
                "/create WELCOME 1000",
                reply_markup=get_back_keyboard()
            )
        elif promo_type == "stars":
            admin_states[callback.from_user.id] = {"state": "create_promo_stars"}
            await callback.message.edit_text(
                "⭐ ПРОМОКОД НА ЗВЁЗДЫ\n\n"
                "Напиши:\n"
                "/create [код] [количество звёзд]\n\n"
                "Пример:\n"
                "/create WELCOME 50",
                reply_markup=get_back_keyboard()
            )
        elif promo_type == "both":
            admin_states[callback.from_user.id] = {"state": "create_promo_both"}
            await callback.message.edit_text(
                "💰⭐ ПРОМОКОД НА ВСЁ\n\n"
                "Напиши:\n"
                "/create [код] [монеты] [звёзды]\n\n"
                "Пример:\n"
                "/create WELCOME 1000 50",
                reply_markup=get_back_keyboard()
            )
        
        await callback.answer()
    except Exception as e:
        print(f"❌ Ошибка типа промокода: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

# ============ СОЗДАНИЕ ПРОМОКОДА ============

@router.message(Command("create"))
async def create_promo_new(message: Message):
    """Создать промокод через /create"""
    try:
        if not is_admin(message.from_user.id):
            return
        
        state = admin_states.get(message.from_user.id, {}).get("state", "")
        
        if state == "create_promo_coins":
            # /create КОД МОНЕТЫ
            parts = message.text.split()
            if len(parts) < 3:
                await message.answer("❌ Формат: /create [код] [монеты]\nПример: /create WELCOME 1000")
                return
            
            code = parts[1].upper()
            coins = int(parts[2])
            stars = 0
        elif state == "create_promo_stars":
            # /create КОД ЗВЕЗДЫ
            parts = message.text.split()
            if len(parts) < 3:
                await message.answer("❌ Формат: /create [код] [звёзды]\nПример: /create WELCOME 50")
                return
            
            code = parts[1].upper()
            stars = int(parts[2])
            coins = 0
        elif state == "create_promo_both":
            # /create КОД МОНЕТЫ ЗВЕЗДЫ
            parts = message.text.split()
            if len(parts) < 4:
                await message.answer("❌ Формат: /create [код] [монеты] [звёзды]\nПример: /create WELCOME 1000 50")
                return
            
            code = parts[1].upper()
            coins = int(parts[2])
            stars = int(parts[3])
        else:
            await message.answer("❌ Сначала выбери тип промокода в админ-панели (/admin)")
            return
        
        # Получаем лимит использований
        max_uses = admin_states.get("default_uses", 100)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promos (
                code VARCHAR(50) PRIMARY KEY,
                stars INT DEFAULT 0,
                coins BIGINT DEFAULT 0,
                max_uses INT DEFAULT 100,
                uses INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await db.execute("""
            INSERT INTO promos (code, stars, coins, max_uses, uses)
            VALUES ($1, $2, $3, $4, 0)
        """, code, stars, coins, max_uses)
        
        await message.answer(
            f"✅ Промокод создан!\n\n"
            f"🎫 Код: <code>{code}</code>\n"
            f"💰 Монеты: {coins}\n"
            f"⭐ Звёзды: {stars}\n"
            f"📊 Лимит: {max_uses} использований\n\n"
            f"Нажми на код, чтобы скопировать!",
            parse_mode="HTML"
        )
        
        # Сбрасываем состояние
        admin_states[message.from_user.id] = {}
    except Exception as e:
        print(f"❌ Ошибка создания промокода: {e}")
        await message.answer("⚠️ Ошибка. Возможно, такой код уже существует!")

# ============ УСТАНОВКА ЛИМИТА ============

@router.message(F.text.regexp(r'^\d+$'))
async def set_limit_handler(message: Message):
    """Обработка установки лимита"""
    try:
        if not is_admin(message.from_user.id):
            return
        
        state = admin_states.get(message.from_user.id, {}).get("state", "")
        
        if state == "set_limit":
            limit = int(message.text)
            if limit < 1 or limit > 10000:
                await message.answer("❌ Лимит должен быть от 1 до 10000")
                return
            
            admin_states["default_uses"] = limit
            admin_states[message.from_user.id] = {}
            
            await message.answer(
                f"✅ Лимит промокодов установлен: {limit}\n\n"
                f"Все новые промокоды будут иметь {limit} использований.",
                reply_markup=get_admin_keyboard()
            )
    except Exception as e:
        print(f"❌ Ошибка лимита: {e}")

# ============ ОСТАЛЬНЫЕ КОМАНДЫ ============

@router.message(Command("delete_promo"))
async def delete_promo_command(message: Message):
    """Удалить промокод"""
    try:
        if not is_admin(message.from_user.id):
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Формат: /delete_promo КОД")
            return
        
        code = parts[1].upper()
        await db.execute("DELETE FROM promos WHERE code = $1", code)
        await db.execute("DELETE FROM user_promos WHERE code = $1", code)
        await message.answer(f"✅ Промокод <code>{code}</code> удален!", parse_mode="HTML")
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")

@router.message(Command("add_coins"))
async def add_coins_command(message: Message):
    """Накрутить монеты"""
    try:
        if not is_admin(message.from_user.id):
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("❌ Формат: /add_coins @user СУММА")
            return
        
        username = parts[1].replace("@", "")
        amount = int(parts[2])
        
        user = await db.fetchrow("SELECT user_id FROM users WHERE username = $1", username)
        if not user:
            await message.answer(f"❌ Пользователь @{username} не найден!")
            return
        
        from database.models import update_balance
        await update_balance(db, user['user_id'], amount)
        await message.answer(f"✅ @{username} получил {amount} монет!")
    except Exception as e:
        print(f"❌ Ошибка монет: {e}")

@router.message(Command("add_stars"))
async def add_stars_command(message: Message):
    """Накрутить звёзды"""
    try:
        if not is_admin(message.from_user.id):
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("❌ Формат: /add_stars @user СУММА")
            return
        
        username = parts[1].replace("@", "")
        amount = int(parts[2])
        
        user = await db.fetchrow("SELECT user_id FROM users WHERE username = $1", username)
        if not user:
            await message.answer(f"❌ Пользователь @{username} не найден!")
            return
        
        from database.models import update_stars
        await update_stars(db, user['user_id'], amount)
        await message.answer(f"✅ @{username} получил {amount} звёзд!")
    except Exception as e:
        print(f"❌ Ошибка звёзд: {e}")

# ============ ПРОМОКОД ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ============

@router.message(Command("promo"))
async def use_promo_command(message: Message):
    """Использовать промокод: /promo КОД"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("❌ Формат: /promo КОД\nПример: /promo WELCOME")
            return
        
        code = parts[1].upper()
        
        promo = await db.fetchrow("SELECT * FROM promos WHERE code = $1", code)
        if not promo:
            await message.answer("❌ Промокод не найден!")
            return
        
        if promo['uses'] >= promo['max_uses']:
            await message.answer("❌ Промокод исчерпан!")
            return
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_promos (
                user_id BIGINT NOT NULL,
                code VARCHAR(50) NOT NULL,
                PRIMARY KEY (user_id, code)
            )
        """)
        
        user_promo = await db.fetchrow(
            "SELECT * FROM user_promos WHERE user_id = $1 AND code = $2",
            message.from_user.id, code
        )
        if user_promo:
            await message.answer("❌ Ты уже использовал этот промокод!")
            return
        
        from database.models import update_balance, update_stars
        if promo['coins'] > 0:
            await update_balance(db, message.from_user.id, promo['coins'])
        if promo['stars'] > 0:
            await update_stars(db, message.from_user.id, promo['stars'])
        
        await db.execute(
            "INSERT INTO user_promos (user_id, code) VALUES ($1, $2)",
            message.from_user.id, code
        )
        await db.execute("UPDATE promos SET uses = uses + 1 WHERE code = $1", code)
        
        await message.answer(
            f"✅ Промокод активирован!\n\n"
            f"🎁 Получено:\n"
            f"💰 Монеты: {promo['coins']}\n"
            f"⭐ Звёзды: {promo['stars']}"
        )
    except Exception as e:
        print(f"❌ Ошибка промокода: {e}")
