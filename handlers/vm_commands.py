import logging
import re
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from script.classes import VMConfigManager, SSHConnection
import paramiko
from script.db import async_session

logger = logging.getLogger(__name__)
router = Router()

# Создаем один экземпляр менеджера конфигураций
vm_config_manager = VMConfigManager(async_session)

@router.message(Command("vmpath"))
async def vmpath_handler(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    logger.info(f"/vmpath args from user {user_id}: {args}")
    if len(args) != 4:
        await message.answer(
            "Неверный формат. Используйте: <code>/vmpath host username password</code>\n"
            "Пример: <code>/vmpath 1.2.3.4 myuser mypass123</code>"
        )
        return

    host_str, username, password = args[1], args[2], args[3]
    # Простая валидация хоста
    if ':' in host_str:
        host, port_str = host_str.split(':', 1)
        if not port_str.isdigit() or not (0 < int(port_str) < 65536):
            await message.answer("Неверный номер порта. Укажите число от 1 до 65535.")
            return
        port = int(port_str)
    else:
        host = host_str
        port = 22

    logger.info(f"User {user_id} setting VM config: Host={host}, Port={port}, User={username}")

    try:
        success = await vm_config_manager.save_vm_config(user_id, host, port, username, password)
        if success:
            await message.answer("✅ Данные для подключения к VM успешно сохранены!")
        else:
            # Проверим, зарегистрирован ли пользователь
            from script.db import User, async_session
            async with async_session() as session:
                user = await session.get(User, user_id)
            if not user:
                logger.warning(f"User {user_id} tried to set VM config but is not registered.")
                await message.answer("❗️ Вы не зарегистрированы. Сначала используйте /start.")
            else:
                await message.answer("❌ Ошибка при сохранении данных. Проверьте логи или обратитесь к администратору.")
    except Exception as e:
        logger.error(f"Exception in /vmpath for user {user_id}: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


@router.message(Command("check"))
async def check_vm_connection_handler(message: Message):
    user_id = message.from_user.id
    await message.answer("Проверяю подключение к VM... ⏳")

    vm_config = await vm_config_manager.get_vm_config(user_id)
    if not vm_config:
        await message.answer("⚠️ Данные для подключения не найдены. Сначала используйте /vmpath.")
        return

    try:
        async with SSHConnection(**vm_config) as ssh:
            stdout, stderr, status = await ssh.execute_command("echo Connection test successful")
            if status == 0:
                await message.answer(f"✅ Успешное подключение к {vm_config['host']}.\nСервер ответил: <code>{stdout}</code>")
            else:
                await message.answer(f"⚠️ Подключение установлено, но тестовая команда провалилась.\nОшибка: <code>{stderr}</code>")
    except paramiko.AuthenticationException:
        await message.answer("❌ Ошибка аутентификации. Неверное имя пользователя или пароль.")
    except Exception as e:
        logger.error(f"User {user_id} SSH check error: {e}")
        await message.answer(f"❌ Не удалось подключиться: {e}")

@router.message(Command("ls"))
async def ls_handler(message: Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    path = args[1] if len(args) > 1 else "."

    vm_config = await vm_config_manager.get_vm_config(user_id)
    if not vm_config:
        await message.answer("⚠️ Данные для подключения не найдены. Сначала используйте /vmpath.")
        return

    await message.answer(f"Получаю содержимое директории <code>{path}</code>...")

    try:
        async with SSHConnection(**vm_config) as ssh:
            stdout, stderr, status = await ssh.execute_command(f"ls -la {path}")
            if status == 0:
                if not stdout:
                    await message.answer(f"Директория <code>{path}</code> пуста.")
                else:
                    await message.answer(f"<pre>{stdout[:4000]}</pre>")
            else:
                await message.answer(f"❌ Ошибка выполнения команды ls:\n<pre>{stderr}</pre>")
    except Exception as e:
        logger.error(f"User {user_id} ls error: {e}")
        await message.answer(f"❌ Ошибка при выполнении команды: {e}")

@router.message(Command("cat"))
async def cat_handler(message: Message):
    user_id = message.from_user.id
    
    args = message.text.split()
    if len(args) != 2:
        await message.answer("Неверный формат. Используйте: <code>/cat путь_к_файлу</code>")
        return
    
    file_path = args[1]

    vm_config = await vm_config_manager.get_vm_config(user_id)
    if not vm_config:
        await message.answer("⚠️ Данные для подключения не найдены. Сначала используйте /vmpath.")
        return
        
    await message.answer(f"Читаю файл <code>{file_path}</code>...")

    try:
        async with SSHConnection(**vm_config) as ssh:
            stdout, stderr, status = await ssh.execute_command(f"cat {file_path}")
            if status == 0:
                if not stdout:
                    await message.answer(f"Файл <code>{file_path}</code> пуст.")
                else:
                    for i in range(0, len(stdout), 4000):
                        await message.answer(f"<pre>{stdout[i:i+4000]}</pre>")
            else:
                await message.answer(f"❌ Ошибка чтения файла:\n<pre>{stderr}</pre>")
    except Exception as e:
        logger.error(f"User {user_id} cat error: {e}")
        await message.answer(f"❌ Ошибка при выполнении команды: {e}")