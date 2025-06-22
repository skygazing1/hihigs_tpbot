"""
Пакет script для работы с файловой системой через SSH в telegram-боте.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
# Это позволяет делать абсолютные импорты от корня проекта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .classes import FileOperations, VMConfigManager, SSHConnection
from .db import init_db, get_db_session, User

__all__ = [
    'FileOperations', 'VMConfigManager', 'SSHConnection',
    'init_db', 'get_db_session', 'User'
] 