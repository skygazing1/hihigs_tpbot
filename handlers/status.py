from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging
from script.db import User, async_session
from sqlalchemy.future import select

router = Router()

logger = logging.getLogger(__name__)

@router.message(Command("status"))
async def status_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    async with async_session() as session:
        user = await session.get(User, user_id)

    if not user:
        await message.answer(
            "⚠️ Вы не зарегистрированы!\n"
            "Пожалуйста, используйте команду /start для начала работы."
        )
        return

    status_text = (
        f"<b>📝 Ваш статус</b>\n\n"
        f"<b>ID:</b> <code>{user.userid}</code>\n"
        f"<b>Юзернейм:</b> @{username}\n"
    )

    if user.role == 'teacher':
        status_text += f"<b>Роль:</b> Преподаватель\n"
        status_text += f"<b>Код для студентов:</b> <code>{user.tutorcode}</code>"
    elif user.role == 'student':
        status_text += f"<b>Роль:</b> Слушатель\n"
        status_text += f"<b>Подписан на:</b> @{user.subscribe}"

    if not user.vm_host:
        status_text += "\n\n" \
                       "❗️ Данные для подключения к VM не заданы.\n" \
                       "Используйте команду /vmpath, чтобы их указать."

    await message.answer(status_text)

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
