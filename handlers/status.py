from aiogram import Router, types
from aiogram.filters import Command
import logging

router = Router()

@router.message(Command("status"))
async def status_handler(message: types.Message):
    user = message.from_user
    logging.info(f"/status вызван пользователем {user.id} ({user.username})")
    await message.answer(
        f"Текущий статус:\n"
        f"ID: {user.id}\n"
        f"Username: @{user.username if user.username else 'нет username'}"
    )