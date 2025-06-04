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

    parts = args_text.split()
    if len(parts) != 3:
        await message.answer(
            "Неверный формат. Пожалуйста, предоставьте хост (опционально с портом), имя пользователя и пароль.\n"
            "Формат: <code>/vmpath &lt;host_or_host:port&gt; &lt;username&gt; &lt;password&gt;</code>\n"
            "Пример: <code>/vmpath 192.168.1.100:22 myuser mypass123</code>"
        )
        return

    host_port_str, username, password = parts[0], parts[1], parts[2]

    host = host_port_str
    port = 22

    if ':' in host_port_str:
        match = re.fullmatch(r'([^:]+):(\d+)', host_port_str)
        if match:
            host = match.group(1)
            try:
                port = int(match.group(2))
                if not (0 < port < 65536):
                    await message.answer("Неверный номер порта. Порт должен быть числом от 1 до 65535.")
                    return
            except ValueError:
                await message.answer("Номер порта должен быть числом.")
                return
        else:
            await message.answer(
                "Неверный формат хоста и порта. Используйте <code>host:port</code>, например, <code>192.168.1.100:2222</code>."
            )
            return

    logger.info(f"User {user_id} attempting to set VM path: Host={host}, Port={port}, User={username}")

    success = await vm_config_manager.save_vm_config(user_id, host, port, username, password)

    if success:
        await message.answer("✅ Данные для подключения к виртуальной машине успешно сохранены!")
    else:
        await message.answer("❌ Произошла ошибка при сохранении данных. Попробуйте позже или обратитесь к администратору.")

@router.message(Command("check"))
async def check_vm_connection_handler(message: Message):
    user_id = message.from_user.id
    await message.answer("Проверяю подключение к виртуальной машине... ⏳")

    vm_config = await vm_config_manager.get_vm_config(user_id)

    if not vm_config:
        await message.answer(
            "⚠️ Данные для подключения к ВМ не найдены. "
            "Пожалуйста, сначала используйте команду /vmpath, чтобы их указать."
        )
        return

    host = vm_config.get("host")
    port = vm_config.get("port", 22)
    username = vm_config.get("username")
    password = vm_config.get("password")

    if not all([host, username, password]):
        await message.answer(
            "⚠️ Неполные данные для подключения к ВМ (отсутствует хост, имя пользователя или пароль). "
            "Пожалуйста, проверьте сохраненные данные с помощью /vmpath."
        )
        return