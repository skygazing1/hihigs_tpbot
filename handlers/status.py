from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import logging

router = Router()

@router.message(Command("status"))
async def status_handler(message: Message):
    username = message.from_user.username or "не указан"
    logging.info(f"Пользователь {message.from_user.id} вызвал /status")
    await message.answer(
        f"🧾 Твой ID: <code>{message.from_user.id}</code>\n"
        f"Юзернейм: @{username}"
    )
