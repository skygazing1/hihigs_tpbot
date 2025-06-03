import logging
import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from script.classes import VMConfigManager, SSHConnection
import paramiko

logger = logging.getLogger(__name__)
router = Router()

vm_config_manager = VMConfigManager()

@router.message(Command("vmpath"))
async def vmpath_handler(message: Message):
    user_id = message.from_user.id
    args_text = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ""

    if not args_text:
        await message.answer(
            "Пожалуйста, укажите данные для подключения к ВМ.\n"
            "Формат: <code>/vmpath &lt;host&gt; &lt;username&gt; &lt;password&gt;</code>\n"
            "Или: <code>/vmpath &lt;host:port&gt; &lt;username&gt; &lt;password&gt;</code>\n"
            "Пример: <code>/vmpath 192.168.1.100 myuser mypass123</code>\n"
            "Пример: <code>/vmpath your.server.com:2222 myuser mypass123</code>"
        )
        return