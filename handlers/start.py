from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import logging

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /start")
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\nТвой ID: <code>{message.from_user.id}</code>"
    )
