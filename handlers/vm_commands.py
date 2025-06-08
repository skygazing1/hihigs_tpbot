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
    except Exception as e:
        logger.error(f"User {user_id}: Unexpected error during SSH check to {host}:{port} - {e}")
        await message.answer(f"❌ Произошла непредвиденная ошибка: {e}")
    finally:
        if ssh_conn:
            ssh_conn.disconnect()


@router.message(Command("ls"))
async def ls_handler(message: Message):
    user_id = message.from_user.id
    path_to_list = "~"
    args_text = message.text.split(maxsplit=1)
    if len(args_text) > 1:
        path_to_list = args_text[1].strip()
        if not path_to_list:
            path_to_list = "~"

    await message.answer(f"Получаю список файлов из каталога <code>{path_to_list}</code>... ⏳")

    vm_config = await vm_config_manager.get_vm_config(user_id)
    if not vm_config:
        await message.answer("⚠️ Данные для подключения к ВМ не найдены. Используйте /vmpath.")
        return

    host, port, username, password = vm_config["host"], vm_config["port"], vm_config["username"], vm_config["password"]
    if not all([host, username, password]):
        await message.answer("⚠️ Неполные данные для подключения к ВМ. Проверьте /vmpath.")
        return

    ssh_conn = None
    try:
        ssh_conn = SSHConnection(host=host, port=port, username=username, password=password)
        ssh_conn.connect()

        command = f"ls -la {path_to_list}"
        logger.info(f"User {user_id}: Executing '{command}' on {host}")
        stdout, stderr, status = ssh_conn.execute_command(command)

        if status == 0:
            if stdout:
                if len(stdout) > 4000:
                    await message.answer(f"Содержимое каталога <code>{path_to_list}</code> (начало):")
                    for i in range(0, len(stdout), 4000):
                        await message.answer(f"<pre>{stdout[i:i + 4000]}</pre>")
                else:
                    await message.answer(f"Содержимое каталога <code>{path_to_list}</code>:\n<pre>{stdout}</pre>")
            else:
                await message.answer(f"Каталог <code>{path_to_list}</code> пуст или команда не вернула вывод.")
        else:
            logger.warning(f"User {user_id}: Error executing '{command}' on {host}. STDERR: {stderr}")
            await message.answer(f"❌ Ошибка при выполнении команды <code>ls</code>:\n<pre>{stderr if stderr else 'Неизвестная ошибка'}</pre>")

    except paramiko.AuthenticationException:
        await message.answer("❌ Ошибка аутентификации. Проверьте данные /vmpath.")
    except paramiko.SSHException as e:
        await message.answer(f"❌ Ошибка SSH подключения: {e}")
    except ConnectionRefusedError:
        await message.answer(f"❌ Подключение отклонено сервером {host}:{port}.")
    except TimeoutError:
        await message.answer(f"❌ Истекло время ожидания подключения к {host}:{port}.")
    except Exception as e:
        logger.error(f"User {user_id}: Unexpected error during ls command on {host} - {e}")
        await message.answer(f"❌ Произошла непредвиденная ошибка: {e}")
    finally:
        if ssh_conn:
            ssh_conn.disconnect()

@router.message(Command("cat"))
async def cat_handler(message: Message):
    user_id = message.from_user.id
    args_text = message.text.split(maxsplit=1)

    if len(args_text) < 2 or not args_text[1].strip():
        await message.answer("Пожалуйста, укажите путь к файлу, который вы хотите просмотреть.\n"
                             "Формат: <code>/cat &lt;путь_к_файлу&gt;</code>")
        return

    file_path = args_text[1].strip()
    await message.answer(f"Загружаю содержимое файла <code>{file_path}</code>... ⏳")

    vm_config = await vm_config_manager.get_vm_config(user_id)
    if not vm_config:
        await message.answer("⚠️ Данные для подключения к ВМ не найдены. Используйте /vmpath.")
        return

    host, port, username, password = vm_config["host"], vm_config["port"], vm_config["username"], vm_config["password"]
    if not all([host, username, password]):
        await message.answer("⚠️ Неполные данные для подключения к ВМ. Проверьте /vmpath.")
        return

    ssh_conn = None
    try:
        ssh_conn = SSHConnection(host=host, port=port, username=username, password=password)
        ssh_conn.connect()

        check_type_command = f"file -b --mime-type \"{file_path}\""
        logger.info(f"User {user_id}: Executing '{check_type_command}' on {host}")
        mime_type_stdout, mime_type_stderr, mime_status = ssh_conn.execute_command(check_type_command)

        if mime_status != 0:
            logger.warning(f"User {user_id}: Error checking file type for '{file_path}'. STDERR: {mime_type_stderr}")
            await message.answer(f"❌ Не удалось определить тип файла <code>{file_path}</code>.\n<pre>{mime_type_stderr}</pre>")
            return

        if not mime_type_stdout.startswith("text/"):
            logger.info(f"User {user_id}: File '{file_path}' is not a text file (MIME: {mime_type_stdout}). Aborting cat.")
            await message.answer(f"⚠️ Файл <code>{file_path}</code> не является текстовым (тип: {mime_type_stdout}). Вывод невозможен.")
            return

        cat_command = f"cat \"{file_path}\""
        logger.info(f"User {user_id}: Executing '{cat_command}' on {host}")
        stdout, stderr, status = ssh_conn.execute_command(cat_command)

        if status == 0:
            if stdout:
                if len(stdout) > 4000:
                    await message.answer(f"Содержимое файла <code>{file_path}</code> (начало):")
                    for i in range(0, len(stdout), 4000):
                        await message.answer(f"<pre>{stdout[i:i + 4000]}</pre>")
                else:
                    await message.answer(f"Содержимое файла <code>{file_path}</code>:\n<pre>{stdout}</pre>")
            else:
                await message.answer(f"Файл <code>{file_path}</code> пуст.")
        else:
            logger.warning(f"User {user_id}: Error executing '{cat_command}' on {host}. STDERR: {stderr}")
            await message.answer(f"❌ Ошибка при чтении файла <code>{file_path}</code>:\n<pre>{stderr if stderr else 'Неизвестная ошибка'}</pre>")

    except paramiko.AuthenticationException:
        await message.answer("❌ Ошибка аутентификации. Проверьте данные /vmpath.")
    except paramiko.SSHException as e:
        await message.answer(f"❌ Ошибка SSH подключения: {e}")
    except ConnectionRefusedError:
        await message.answer(f"❌ Подключение отклонено сервером {host}:{port}.")
    except TimeoutError:
        await message.answer(f"❌ Истекло время ожидания подключения к {host}:{port}.")
    except Exception as e:
        logger.error(f"User {user_id}: Unexpected error during cat command for '{file_path}' on {host} - {e}")
        await message.answer(f"❌ Произошла непредвиденная ошибка: {e}")
    finally:
        if ssh_conn:
            ssh_conn.disconnect()