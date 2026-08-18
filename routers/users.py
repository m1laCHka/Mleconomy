from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from keyboards.main import main_menu
from keyboards.gender import gender_kb
from constants import START_HELP_PHOTO, FEMALE_PROFILE_PHOTO, MALE_PROFILE_PHOTO

router = Router()


async def ensure_user(db, user_id: int, username: str | None):
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT user_id, gender FROM users WHERE user_id=$1", user_id)
        if not user:
            await conn.execute(
                "INSERT INTO users (user_id, username) VALUES ($1, $2)",
                user_id, username
            )
            return True, None

        await conn.execute(
            "UPDATE users SET username=$1 WHERE user_id=$2",
            username, user_id
        )
        return False, user["gender"]


async def send_profile(target: Message, db):
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", target.from_user.id)
        if not user:
            return await target.answer("Сначала нажми /start")

        gender = user["gender"]
        if gender == "female":
            photo = FEMALE_PROFILE_PHOTO
            gender_text = "Женский"
        else:
            photo = MALE_PROFILE_PHOTO
            gender_text = "Мужской"

        name = user["custom_nick"] or target.from_user.full_name

        text = (
            f"👤 Профиль\n"
            f"Ник: {name}\n"
            f"Пол: {gender_text}\n"
            f"💰 Монеты: {user['coins']}\n"
            f"⭐ Звёзды: {user['stars']}"
        )

        if target.chat.type == "private":
            await target.answer_photo(photo=photo, caption=text, reply_markup=main_menu())
        else:
            await target.answer_photo(photo=photo, caption=text)


@router.message(CommandStart())
async def start_handler(message: Message, db):
    is_new, gender = await ensure_user(db, message.from_user.id, message.from_user.username)

    if is_new or not gender:
        await message.answer_photo(
            photo=START_HELP_PHOTO,
            caption="Привет! Для продолжения выбери пол:",
            reply_markup=gender_kb()
        )
        return

    if message.chat.type == "private":
        await message.answer_photo(
            photo=START_HELP_PHOTO,
            caption="Привет! Добро пожаловать.",
            reply_markup=main_menu()
        )
    else:
        await message.answer_photo(
            photo=START_HELP_PHOTO,
            caption="Привет! Добро пожаловать."
        )


@router.message(Command("help"))
async def help_handler(message: Message):
    text = (
        "Справка:\n"
        "/start — начать\n"
        "/help — помощь\n"
        "профиль — открыть профиль в чате\n"
        "п  — открыть профиль в чате только если после п ничего нет"
    )
    await message.answer_photo(photo=START_HELP_PHOTO, caption=text)


@router.callback_query(F.data.startswith("gender:"))
async def gender_choose(call: CallbackQuery, db):
    gender = call.data.split(":", 1)[1]

    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET gender=$1 WHERE user_id=$2",
            gender,
            call.from_user.id
        )

    await call.message.edit_caption(
        caption="Пол сохранён. Теперь можешь открыть профиль.",
        reply_markup=None
    )
    await call.answer("Сохранено")


@router.message(F.text == "профиль")
async def profile_word_handler(message: Message, db):
    await send_profile(message, db)


@router.message(F.text == "п ")
async def p_space_handler(message: Message, db):
    await send_profile(message, db)


@router.message(F.text == "👤 Профиль")
async def profile_button_handler(message: Message, db):
    await send_profile(message, db)
