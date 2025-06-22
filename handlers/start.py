import logging
import uuid
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from script.db import User, async_session

logger = logging.getLogger(__name__)
router = Router()

class Registration(StatesGroup):
    role = State()
    tutor_code = State()

def get_role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я Преподаватель", callback_data="role_teacher")],
        [InlineKeyboardButton(text="Я Слушатель", callback_data="role_student")]
    ])

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with async_session() as session:
        user = await session.get(User, user_id)

    if user:
        await message.answer(f"👋 Привет, {user.username}!\nТы уже зарегистрирован как {user.role}.")
        await state.clear()
    else:
        await message.answer(
            "👋 Привет! Пожалуйста, выбери свою роль:",
            reply_markup=get_role_keyboard()
        )
        await state.set_state(Registration.role)

@router.callback_query(Registration.role, F.data == 'role_teacher')
async def teacher_role_chosen(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    username = query.from_user.username or f"user_{user_id}"
    tutor_code = str(uuid.uuid4())[:8] # Генерируем уникальный код

    new_user = User(
        userid=user_id,
        username=username,
        role='teacher',
        tutorcode=tutor_code
    )
    async with async_session() as session:
        session.add(new_user)
        await session.commit()

    await query.message.edit_text(
        "✅ Вы зарегистрированы как <b>Преподаватель</b>.\n"
        f"Ваш код для студентов: <code>{tutor_code}</code>"
    )
    await state.clear()

@router.callback_query(Registration.role, F.data == 'role_student')
async def student_role_chosen(query: CallbackQuery, state: FSMContext):
    await query.message.edit_text("Введите код преподавателя:")
    await state.set_state(Registration.tutor_code)

@router.message(Registration.tutor_code)
async def process_tutor_code(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    tutor_code = message.text

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tutorcode == tutor_code))
        teacher = result.scalar_one_or_none()

    if teacher:
        new_user = User(
            userid=user_id,
            username=username,
            role='student',
            subscribe=teacher.username
        )
        async with async_session() as session:
            session.add(new_user)
            await session.commit()

        await message.answer(f"✅ Вы успешно зарегистрированы как <b>Слушатель</b> и подписаны на преподавателя @{teacher.username}.")
        await state.clear()
    else:
        await message.answer("❌ Преподаватель с таким кодом не найден. Попробуйте еще раз или вернитесь к выбору роли, нажав /start.")

# Обновляем status_handler для использования поля role
# (Этот шаг будет выполнен далее в handlers/status.py)
