import os
import sys
import asyncio
import logging
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from script.db import initialize_db, init_db as create_tables_if_not_exist, engine as db_engine

DATABASE_URL = f"sqlite+aiosqlite:///{project_root}/bot.db"
LOG_FILE_PATH = project_root / "logs" / "bot.log"

initialize_db(DATABASE_URL)

from handlers import start, help, status, vm_commands

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE_PATH),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=project_root / '.env')
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.critical("BOT_TOKEN не найден. Убедитесь, что файл .env существует в корне проекта и содержит BOT_TOKEN.")
    sys.exit("BOT_TOKEN not configured. Exiting.")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(help.router)
dp.include_router(status.router)
dp.include_router(vm_commands.router)

async def set_bot_commands(bot_instance: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="status", description="Информация о тебе"),
        BotCommand(command="vmpath", description="Указать данные ВМ (host user pass)"),
        BotCommand(command="check", description="Проверить подключение к ВМ"),
        BotCommand(command="ls", description="Список файлов на ВМ (опц. путь)"),
        BotCommand(command="cat", description="Показать файл с ВМ (путь_к_файлу)"),
    ]
    await bot_instance.set_my_commands(commands)

async def main_async():
    await create_tables_if_not_exist()
    logger.info("Database tables initialized/checked.")

    await set_bot_commands(bot)
    logger.info("Bot commands set.")
    logger.info("Starting bot polling...")
    await dp.start_polling(bot, close_bot_session=True)

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually")
    except Exception as e:
        logger.critical(f"Critical error during bot execution: {e}", exc_info=True)
    finally:
        if db_engine:
            logger.info("Disposing database engine.")
            asyncio.run(db_engine.dispose())
        logger.info("Bot shutdown complete.") 