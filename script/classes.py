import paramiko
import logging
from typing import List, Dict, Optional
from pathlib import Path

class FileOperations:
    """
    Класс для работы с файловой системой через SSH.
    Обеспечивает функционал для просмотра содержимого директорий и чтения текстовых файлов.
    """
    
    def __init__(self, ssh_client: paramiko.SSHClient):
        """
        Инициализация класса FileOperations.
        
        Args:
            ssh_client (paramiko.SSHClient): Клиент SSH для подключения к удаленной машине
        """
        self.ssh = ssh_client
        self.logger = logging.getLogger(__name__)
        
    async def list_directory(self, path: str = "~") -> List[Dict[str, str]]:
        """
        Получение списка файлов в указанной директории.
        
        Args:
            path (str): Путь к директории (по умолчанию домашняя директория)
            
        Returns:
            List[Dict[str, str]]: Список словарей с информацией о файлах
            Каждый словарь содержит:
            - name: имя файла
            - type: тип (file/directory)
            - size: размер в байтах
            - permissions: права доступа
        """
        try:
            stdin, stdout, stderr = self.ssh.exec_command(f"ls -la {path}")
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                self.logger.error(f"Error listing directory {path}: {error}")
                raise Exception(f"Failed to list directory: {error}")
                
            files = []
            for line in output.splitlines()[1:]:  # Пропускаем первую строку (total)
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 8:
                        files.append({
                            'permissions': parts[0],
                            'size': parts[4],
                            'name': ' '.join(parts[7:]),
                            'type': 'directory' if parts[0].startswith('d') else 'file'
                        })
            return files
            
        except Exception as e:
            self.logger.error(f"Error in list_directory: {str(e)}")
            raise
            
    async def read_text_files(self, path: str = "~") -> Dict[str, str]:
        """
        Чтение содержимого всех текстовых файлов в указанной директории.
        
        Args:
            path (str): Путь к директории (по умолчанию домашняя директория)
            
        Returns:
            Dict[str, str]: Словарь с именами файлов и их содержимым
        """
        try:
            # Получаем список файлов
            files = await self.list_directory(path)
            text_files = {}
            
            for file_info in files:
                if file_info['type'] == 'file':
                    file_path = str(Path(path) / file_info['name'])
                    try:
                        stdin, stdout, stderr = self.ssh.exec_command(f"file {file_path}")
                        file_type = stdout.read().decode().lower()
                        
                        # Проверяем, является ли файл текстовым
                        if 'text' in file_type:
                            stdin, stdout, stderr = self.ssh.exec_command(f"cat {file_path}")
                            content = stdout.read().decode()
                            error = stderr.read().decode()
                            
                            if not error:
                                text_files[file_info['name']] = content
                            else:
                                self.logger.warning(f"Error reading file {file_path}: {error}")
                                
                    except Exception as e:
                        self.logger.error(f"Error processing file {file_path}: {str(e)}")
                        continue
                        
            return text_files
            
        except Exception as e:
            self.logger.error(f"Error in read_text_files: {str(e)}")
            raise 