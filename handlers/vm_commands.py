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

    ssh_conn = None
    try:
        logger.info(f"User {user_id}: Attempting to check SSH connection to {username}@{host}:{port}")
        ssh_conn = SSHConnection(host=host, port=port, username=username, password=password)

        if ssh_conn.connect():
            await message.answer(f"✅ Успешное подключение к {host}:{port} пользователем {username}!")
            try:
                stdout, stderr, status = ssh_conn.execute_command("echo hello")
                if status == 0 and "hello" in stdout:
                    logger.info(f"User {user_id}: Test command 'echo hello' successful on {host}")
                    await message.answer("Тестовая команда на сервере выполнена успешно.")
                else:
                    logger.warning(f"User {user_id}: Test command 'echo hello' failed or unexpected output on {host}. STDOUT: {stdout}, STDERR: {stderr}")
                    await message.answer("⚠️ Тестовая команда на сервере не дала ожидаемого результата, но подключение установлено.")
            except Exception as e_cmd:
                logger.error(f"User {user_id}: Error executing test command on {host}: {e_cmd}")
                await message.answer("⚠️ Ошибка при выполнении тестовой команды на сервере, но подключение было установлено.")
        else:
            await message.answer(f"❌ Не удалось подключиться к {host}. Проверьте данные и доступность сервера.")

    except paramiko.AuthenticationException:
        logger.warning(f"User {user_id}: Authentication failed for {username}@{host}:{port}")
        await message.answer("❌ Ошибка аутентификации. Неверное имя пользователя или пароль.")
    except paramiko.SSHException as e:
        logger.error(f"User {user_id}: SSH connection error to {host}:{port} - {e}")
        await message.answer(f"❌ Ошибка SSH подключения: {e}. Проверьте адрес хоста, порт и доступность сервера.")
    except ConnectionRefusedError:
        logger.error(f"User {user_id}: Connection refused for {host}:{port}")
        await message.answer(f"❌ Подключение отклонено сервером {host}:{port}. Убедитесь, что SSH сервер запущен и порт не заблокирован.")
    except TimeoutError:
        logger.error(f"User {user_id}: Connection timeout for {host}:{port}")
        await message.answer(f"❌ Истекло время ожидания подключения к {host}:{port}. Проверьте сеть и доступность сервера.")