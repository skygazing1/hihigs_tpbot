import os
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from handlers import start, help, status  # Импорт роутеров
from models import engine, init_db # Импорт engine и init_db

# === Логирование ===
Path("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename="logs/bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# === Загрузка токена ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

# === Инициализация бота и диспетчера ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# === Подключение роутеров ===
dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(status.router)

# === Настройка меню команд ===
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="status", description="Информация о тебе"),
    ]
    await bot.set_my_commands(commands)

# Основной запуск
async def main():
    # Initialize database
    await init_db() # Вызываем init_db для создания/обновления БД

    await set_bot_commands(bot)
    await dp.start_polling(bot, close_bot_session=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped manually")
    finally:
        # Dispose database engine
        asyncio.run(engine.dispose())
