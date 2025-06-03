import os
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
