import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.enums import ParseMode

from aiogram.types import Message
from aiogram.filters import Command

from dotenv import load_dotenv
import asyncio
import os

# === Настройка логирования ===
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === Загрузка токена из .env ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

# === Инициализация бота и диспетчера ===
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


# === Обработчики ===

@dp.message(Command("start"))
async def start_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /start")
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\nТвой ID: <code>{message.from_user.id}</code>"
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /help")
    await message.answer(
        "📋 Справка:\n"
        "/start — начать\n"
        "/help — помощь\n"
        "/status — узнать информацию о себе"
    )

@dp.message(Command("status"))
async def status_handler(message: Message):
    logging.info(f"Пользователь {message.from_user.id} вызвал /status")
    username = message.from_user.username or "нет username"
    await message.answer(
        f"🧾 Твой ID: <code>{message.from_user.id}</code>\n"
        f"Юзернейм: @{username}"
    )


# === Настройка меню команд ===
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Справка"),
        BotCommand(command="/status", description="Информация о тебе"),
    ]
    await bot.set_my_commands(commands)


# === Запуск бота ===
async def main():
    await set_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
