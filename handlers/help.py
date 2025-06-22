import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("help"))
async def help_handler(message: Message):
    logger.info(f"User {message.from_user.id} requested /help")
    
    help_text = (
        "<b>Доступные команды:</b>\n\n"
        "<b>Основные:</b>\n"
        "▫️ /start - Регистрация и запуск бота\n"
        "▫️ /help - Показать это сообщение\n"
        "▫️ /status - Узнать свой ID и статус\n\n"
        "<b>Работа с VM:</b>\n"
        "▫️ /vmpath <code>host user pass</code> - Сохранить данные для подключения\n"
        "   <i>Пример: /vmpath 1.2.3.4 myuser mypass</i>\n"
        "▫️ /check - Проверить соединение с VM\n"
        "▫️ /ls [путь] - Показать содержимое директории\n"
        "   <i>Пример: /ls или /ls /home/user/docs</i>\n"
        "▫️ /cat <code>путь_к_файлу</code> - Прочитать текстовый файл\n"
        "   <i>Пример: /cat /etc/hosts</i>"
    )
    
    await message.answer(help_text)
