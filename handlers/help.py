from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import logging

router = Router()

@router.message(Command("help"))
async def help_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /help")
    await message.answer(
        "📋 Справка:\n"
        "/start — начать\n"
        "/help — помощь\n"
        "/status — узнать информацию о себе"
    )
