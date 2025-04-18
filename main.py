import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from dotenv import load_dotenv
import asyncio
import os

# Настройка логов
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Загрузка токена
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик /start
@dp.message(Command("start"))
async def process_start_command(message: Message):
    await message.answer("Привет!")

# Обработчик /status
@dp.message(Command("status"))
async def process_status_command(message: Message):
    username = message.from_user.username or "не указан"
    logging.info(f"Пользователь {message.from_user.id} вызвал /status")
    await message.answer(
        f"🧾 Твой ID: <code>{message.from_user.id}</code>\n"
        f"Юзернейм: @{username}",
        parse_mode="HTML"
    )

# Основной запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
