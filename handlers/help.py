from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

router = Router()

@router.message(Command("help"))
async def help_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /help")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Узнать статус", callback_data="status")]
        ]
    )
    await message.answer(
        "📋 Справка:\n"
        "/start — начать\n"
        "/help — помощь\n"
        "/status — узнать информацию о себе",
        reply_markup=keyboard
    )
