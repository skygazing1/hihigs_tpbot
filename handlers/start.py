from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import random
import string
import logging
from aiogram.exceptions import TelegramBadRequest

from models import User, async_session
from sqlalchemy.future import select

router = Router()
logging.basicConfig(level=logging.INFO)

# Определяем состояния для регистрации студента
class StudentRegistration(StatesGroup):
    waiting_for_tutor_code = State()

# Функция для генерации уникального кода преподавателя
def generate_tutor_code(length=6):
    letters_and_digits = string.ascii_uppercase + string.digits
    # В реальном приложении можно добавить проверку уникальности в БД, но для задания хватит генерации
    return ''.join(random.choice(letters_and_digits) for i in range(length))


@router.message(Command("start"))
async def cmd_start(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /start")
    user_id = message.from_user.id

    async with async_session() as session:
        # Проверяем, зарегистрирован ли пользователь
        result = await session.execute(select(User).where(User.userid == user_id))
        user = result.scalar_one_or_none()

        # Если пользователь не найден ИЛИ роль не определена, предлагаем выбрать роль
        if not user or user.role is None:
            builder = InlineKeyboardBuilder()
            builder.button(text="Я Преподаватель", callback_data="role_tutor")
            builder.button(text="Я Слушатель", callback_data="role_student")
            await message.answer("Добро пожаловать! Выберите, кто вы?", reply_markup=builder.as_markup())
        else:
            await message.answer(f"Вы уже зарегистрированы как {user.role}.")

@router.callback_query(F.data == "role_tutor")
async def process_role_selection_tutor(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Пользователь {callback.from_user.id} выбрал роль Преподаватель")
    user_id = callback.from_user.id
    username = callback.from_user.username or f"user_{user_id}"

    async with async_session() as session:
        # Проверяем, зарегистрирован ли пользователь (на всякий случай)
        result = await session.execute(select(User).where(User.userid == user_id))
        user = result.scalar_one_or_none()

        if not user:
            # Генерируем уникальный код преподавателя (для простоты, без проверки уникальности)
            tutor_code = generate_tutor_code()
            new_user = User(userid=user_id, username=username, role="преподаватель", tutorcode=tutor_code)
            session.add(new_user)
            await session.commit()
            # Редактируем сообщение вместо отправки нового
            try:
                await callback.message.edit_text(f"Вы зарегистрированы как преподаватель. Ваш код: {tutor_code}")
            except TelegramBadRequest: # Обработка случая, если сообщение не может быть отредактировано
                await callback.message.answer(f"Вы зарегистрированы как преподаватель. Ваш код: {tutor_code}")
        elif user.role is None: # Если пользователь существует, но роль не выбрана
             # Генерируем уникальный код преподавателя (для простоты, без проверки уникальности)
            tutor_code = generate_tutor_code()
            user.role = "преподаватель"
            user.tutorcode = tutor_code
            await session.commit()
            try:
                await callback.message.edit_text(f"Вы зарегистрированы как преподаватель. Ваш код: {tutor_code}")
            except TelegramBadRequest:
                await callback.message.answer(f"Вы зарегистрированы как преподаватель. Ваш код: {tutor_code}")
        else:
            # Редактируем сообщение
            try:
                await callback.message.edit_text(f"Вы уже зарегистрированы как {user.role}.")
            except TelegramBadRequest:
                await callback.message.answer(f"Вы уже зарегистрированы как {user.role}.")

    await callback.answer()

@router.callback_query(F.data == "role_student")
async def process_role_selection_student(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Пользователь {callback.from_user.id} выбрал роль Слушатель")
    user_id = callback.from_user.id

    async with async_session() as session:
        # Проверяем, зарегистрирован ли пользователь
        result = await session.execute(select(User).where(User.userid == user_id))
        user = result.scalar_one_or_none()

        if not user or user.role is None: # Если пользователь не найден ИЛИ роль не выбрана
            # Редактируем сообщение и просим ввести код
            try:
                await callback.message.edit_text("Введите код преподавателя:")
                await state.set_state(StudentRegistration.waiting_for_tutor_code)
            except TelegramBadRequest:
                await callback.message.answer("Введите код преподавателя:")
                await state.set_state(StudentRegistration.waiting_for_tutor_code)
        else:
            # Редактируем сообщение
            try:
                await callback.message.edit_text(f"Вы уже зарегистрированы как {user.role}.")
            except TelegramBadRequest:
                 await callback.message.answer(f"Вы уже зарегистрированы как {user.role}.")

    await callback.answer()

@router.message(StudentRegistration.waiting_for_tutor_code)
async def process_tutor_code(message: Message, state: FSMContext):
    logging.info(f"Пользователь {message.from_user.id} ввел код преподавателя: {message.text}")
    tutor_code = message.text
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    async with async_session() as session:
        # Ищем преподавателя с таким кодом
        result = await session.execute(select(User).where(User.role == "преподаватель", User.tutorcode == tutor_code))
        tutor_user = result.scalar_one_or_none()

        if tutor_user:
            # Проверяем, не зарегистрирован ли уже студент ИЛИ если он есть, но без роли
            result = await session.execute(select(User).where(User.userid == user_id))
            student_user = result.scalar_one_or_none()

            if not student_user: # Новый студент
                # Регистрируем студента и привязываем к преподавателю
                new_user = User(userid=user_id, username=username, role="слушатель", subscribe=tutor_user.username, tutor_id=tutor_user.userid)
                session.add(new_user)
                await session.commit()
                await message.answer(f"Вы успешно зарегистрированы как слушатель у преподавателя {tutor_user.username}!")
                await state.clear()
            elif student_user.role is None: # Существующий пользователь без роли
                 student_user.role = "слушатель"
                 student_user.subscribe = tutor_user.username
                 student_user.tutor_id = tutor_user.userid
                 await session.commit()
                 await message.answer(f"Вы успешно зарегистрированы как слушатель у преподавателя {tutor_user.username}!")
                 await state.clear()
            else:
                await message.answer(f"Вы уже зарегистрированы как {student_user.role}.")
                await state.clear()
        else:
            await message.answer("Неверный код преподавателя. Попробуйте еще раз или используйте /start для выбора другой роли.")

# Обновляем status_handler для использования поля role
# (Этот шаг будет выполнен далее в handlers/status.py)
