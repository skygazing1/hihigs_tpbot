from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from models import User, async_session
from sqlalchemy.future import select

router = Router()

@router.message(Command("status"))
async def status_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /status")
    user_id = message.from_user.id
    username = message.from_user.username or "нет username"

    async with async_session() as session:
        # Используем select для асинхронного запроса
        result = await session.execute(select(User).where(User.userid == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
            return

        # Используем поле role для определения статуса
        if user.role == "преподаватель":
            await message.answer(
                f"🧾 Твой ID: <code>{user_id}</code>\n"
                f"Юзернейм: @{username}\n"
                f"Роль: Преподаватель\n"
                f"Код: {user.tutorcode}"
            )
        elif user.role == "слушатель":
            # Можно добавить здесь поиск имени преподавателя по user.tutor_id, если нужно именно имя
            await message.answer(
                f"🧾 Твой ID: <code>{user_id}</code>\n"
                f"Юзернейм: @{username}\n"
                f"Роль: Слушатель\n"
                f"Подписан на преподавателя ID: {user.tutor_id}" # Пока выводим ID преподавателя
            )

@router.callback_query(F.data == "status")
async def status_callback(callback: CallbackQuery):
    logging.info(f"Пользователь {callback.from_user.id} нажал кнопку 'Узнать статус'")
    user_id = callback.from_user.id
    username = callback.from_user.username or "нет username"

    async with async_session() as session:
        # Используем select для асинхронного запроса
        result = await session.execute(select(User).where(User.userid == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.message.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
            return

        # Используем поле role для определения статуса
        if user.role == "преподаватель":
            await callback.message.answer(
                f"🧾 Твой ID: <code>{user_id}</code>\n"
                f"Юзернейм: @{username}\n"
                f"Роль: Преподаватель\n"
                f"Код: {user.tutorcode}"
            )
        elif user.role == "слушатель":
            # Можно добавить здесь поиск имени преподавателя по user.tutor_id, если нужно именно имя
            await callback.message.answer(
                f"🧾 Твой ID: <code>{user_id}</code>\n"
                f"Юзернейм: @{username}\n"
                f"Роль: Слушатель\n"
                f"Подписан на преподавателя ID: {user.tutor_id}" # Пока выводим ID преподавателя
            )
    await callback.answer()
