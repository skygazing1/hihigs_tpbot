from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import logging

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /start")
    username = message.from_user.full_name
    await message.answer(
        f"👋 Привет, {username}!\n"
        f"Твой ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )
