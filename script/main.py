import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import paramiko
from .classes import FileOperations
from .db import get_db_session, VMConnection

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("ls"))
async def cmd_ls(message: Message):
    """
    Обработчик команды /ls.
    Выводит список содержимого домашнего каталога пользователя на VM.
    """
    try:
        # Получаем информацию о подключении из БД
        session = get_db_session()
        vm_connection = session.query(VMConnection).filter_by(user_id=message.from_user.id).first()
        
        if not vm_connection:
            await message.answer("Сначала укажите параметры подключения к VM с помощью команды /vmpath")
            return
            
        # Создаем SSH-клиент
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Подключаемся к VM
            ssh.connect(
                hostname=vm_connection.host,
                username=vm_connection.username,
                password=vm_connection.password
            )
            
            # Создаем экземпляр FileOperations
            file_ops = FileOperations(ssh)
            
            # Получаем список файлов
            files = await file_ops.list_directory()
            
            # Форматируем вывод
            response = "Содержимое домашнего каталога:\n\n"
            for file_info in files:
                file_type = "📁" if file_info['type'] == 'directory' else "📄"
                response += f"{file_type} {file_info['name']} ({file_info['size']} bytes)\n"
                
            await message.answer(response)
            
        except Exception as e:
            logger.error(f"Error in cmd_ls: {str(e)}")
            await message.answer(f"Ошибка при подключении к VM: {str(e)}")
            
        finally:
            ssh.close()
            
    except Exception as e:
        logger.error(f"Error in cmd_ls: {str(e)}")
        await message.answer("Произошла ошибка при выполнении команды")

@router.message(Command("cat"))
async def cmd_cat(message: Message):
    """
    Обработчик команды /cat.
    Выводит содержимое всех текстовых файлов в домашнем каталоге.
    """
    try:
        # Получаем информацию о подключении из БД
        session = get_db_session()
        vm_connection = session.query(VMConnection).filter_by(user_id=message.from_user.id).first()
        
        if not vm_connection:
            await message.answer("Сначала укажите параметры подключения к VM с помощью команды /vmpath")
            return
            
        # Создаем SSH-клиент
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Подключаемся к VM
            ssh.connect(
                hostname=vm_connection.host,
                username=vm_connection.username,
                password=vm_connection.password
            )
            
            # Создаем экземпляр FileOperations
            file_ops = FileOperations(ssh)
            
            # Получаем содержимое текстовых файлов
            text_files = await file_ops.read_text_files()
            
            if not text_files:
                await message.answer("В домашнем каталоге не найдено текстовых файлов")
                return
                
            # Отправляем содержимое каждого файла
            for filename, content in text_files.items():
                # Разбиваем длинные сообщения
                if len(content) > 4000:
                    chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
                    for i, chunk in enumerate(chunks, 1):
                        await message.answer(f"Файл: {filename} (часть {i}/{len(chunks)})\n\n{chunk}")
                else:
                    await message.answer(f"Файл: {filename}\n\n{content}")
                    
        except Exception as e:
            logger.error(f"Error in cmd_cat: {str(e)}")
            await message.answer(f"Ошибка при подключении к VM: {str(e)}")
            
        finally:
            ssh.close()
            
    except Exception as e:
        logger.error(f"Error in cmd_cat: {str(e)}")
        await message.answer("Произошла ошибка при выполнении команды") 