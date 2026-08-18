# handlers/admin.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from database.models import get_user
from config import ADMIN_ID
from keyboards.main_menu import get_main_menu

router = Router()

# Клавиатура админ-панели
def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🗑️ Очистить все данные",
                callback_data="admin_clear_all"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика бота",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Закрыть",
                callback_data="admin_close"
            )
        ]
    ])
    return keyboard

# Клавиатура подтверждения очистки
def get_confirm_clear_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения очистки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, удалить всё!",
                callback_data="admin_confirm_clear"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Нет, отмена",
                callback_data="admin_cancel"
            )
        ]
    ])
    return keyboard

@router.message(Command("admin"))
async def admin_command(message: Message):
    """Команда /admin"""
    try:
        # Проверяем, является ли пользователь админом
        if message.from_user.id != ADMIN_ID:
            await message.answer(
                "❌ У вас нет доступа к админ-панели!",
                reply_markup=get_main_menu()
            )
            return
        
        await message.answer(
            "👑 **АДМИН-ПАНЕЛЬ**\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        print(f"❌ Ошибка админ-панели: {e}")
        await message.answer(
            "⚠️ Ошибка сервера",
            reply_markup=get_main_menu()
        )

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    """Показать статистику бота"""
    try:
        # Получаем статистику
        total_users = await db.fetchval("SELECT COUNT(*) FROM users")
        total_families = await db.fetchval("SELECT COUNT(*) FROM families")
        total_games = await db.fetchval("SELECT COALESCE(SUM(total_games), 0) FROM users")
        total_wins = await db.fetchval("SELECT COALESCE(SUM(wins), 0) FROM users")
        
        stats_text = f"""
📊 **СТАТИСТИКА БОТА**

👥 **Пользователи:**
• Всего: {total_users or 0}

👨‍👩‍👧 **Семьи:**
• Всего: {total_families or 0}

🎮 **Игры:**
• Всего игр: {total_games or 0}
• Всего побед: {total_wins or 0}

💰 **Экономика:**
• Всего монет: {await db.fetchval("SELECT COALESCE(SUM(balance), 0) FROM users") or 0}
• Всего звёзд: {await db.fetchval("SELECT COALESCE(SUM(stars), 0) FROM users") or 0}
"""
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
    except Exception as e:
        print(f"❌ Ошибка статистики: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@router.callback_query(F.data == "admin_clear_all")
async def admin_clear_all_callback(callback: CallbackQuery):
    """Запрос на очистку всех данных"""
    try:
        await callback.message.edit_text(
            "⚠️ **ВНИМАНИЕ!**\n\n"
            "Вы уверены, что хотите удалить **ВСЕ ДАННЫЕ**?\n\n"
            "Будут удалены:\n"
            "• Все пользователи\n"
            "• Все семьи\n"
            "• Все достижения\n"
            "• Все промокоды\n"
            "• Вся статистика\n\n"
            "Это действие **НЕОБРАТИМО**!",
            parse_mode="Markdown",
            reply_markup=get_confirm_clear_keyboard()
        )
        await callback.answer()
    except Exception as e:
        print(f"❌ Ошибка запроса очистки: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@router.callback_query(F.data == "admin_confirm_clear")
async def admin_confirm_clear_callback(callback: CallbackQuery):
    """Подтверждение очистки всех данных"""
    try:
        # Удаляем все данные из таблиц
        await db.execute("DELETE FROM user_promos")
        await db.execute("DELETE FROM achievements")
        await db.execute("DELETE FROM children")
        await db.execute("DELETE FROM families")
        await db.execute("DELETE FROM promos")
        await db.execute("DELETE FROM users")
        
        await callback.message.edit_text(
            "✅ **ВСЕ ДАННЫЕ УСПЕШНО УДАЛЕНЫ!**\n\n"
            "База данных полностью очищена.\n"
            "Пользователи могут зарегистрироваться заново через /start",
            parse_mode="Markdown"
        )
        await callback.answer("✅ Данные очищены!", show_alert=True)
        
        print("✅ Все данные удалены из БД")
    except Exception as e:
        print(f"❌ Ошибка очистки данных: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при очистке данных: {e}",
            parse_mode="Markdown"
        )
        await callback.answer("⚠️ Ошибка", show_alert=True)

@router.callback_query(F.data == "admin_cancel")
async def admin_cancel_callback(callback: CallbackQuery):
    """Отмена очистки данных"""
    try:
        await callback.message.edit_text(
            "✅ Операция отменена.\n"
            "Данные не были удалены.",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer("Операция отменена")
    except Exception as e:
        print(f"❌ Ошибка отмены: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)

@router.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: CallbackQuery):
    """Закрыть админ-панель"""
    try:
        await callback.message.delete()
        await callback.answer("Панель закрыта")
    except Exception as e:
        print(f"❌ Ошибка закрытия: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)
