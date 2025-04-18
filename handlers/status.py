from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

router = Router()

@router.message(Command("status"))
async def status_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /status")
    username = message.from_user.username or "нет username"
    await message.answer(
        f"🧾 Твой ID: <code>{message.from_user.id}</code>\n"
        f"Юзернейм: @{username}"
    )

@router.callback_query(F.data == "status")
async def status_callback(callback: CallbackQuery):
    logging.info(f"Пользователь {callback.from_user.id} нажал кнопку 'Узнать статус'")
    username = callback.from_user.username or "нет username"
    await callback.message.answer(
        f"🧾 Твой ID: <code>{callback.from_user.id}</code>\n"
        f"Юзернейм: @{username}"
    )
    await callback.answer()
