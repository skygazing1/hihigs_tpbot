import pytest
import paramiko
from unittest.mock import Mock, patch
from ..classes import FileOperations

@pytest.fixture
def mock_ssh_client():
    """Фикстура для создания мок-объекта SSH-клиента."""
    client = Mock(spec=paramiko.SSHClient)
    return client

@pytest.fixture
def file_operations(mock_ssh_client):
    """Фикстура для создания экземпляра FileOperations."""
    return FileOperations(mock_ssh_client)

@pytest.mark.asyncio
async def test_list_directory_success(file_operations, mock_ssh_client):
    """Тест успешного получения списка файлов."""
    # Подготовка мок-данных
    mock_stdout = Mock()
    mock_stdout.read.return_value = b"""total 8
drwxr-xr-x 2 user user 4096 Mar 10 10:00 .
drwxr-xr-x 3 root root 4096 Mar 10 09:00 ..
-rw-r--r-- 1 user user   10 Mar 10 10:00 test.txt
drwxr-xr-x 2 user user 4096 Mar 10 10:00 test_dir"""
    
    mock_stderr = Mock()
    mock_stderr.read.return_value = b""
    
    mock_ssh_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    # Выполнение теста
    result = await file_operations.list_directory()
    
    # Проверки
    assert len(result) == 2  # test.txt и test_dir
    assert any(f['name'] == 'test.txt' and f['type'] == 'file' for f in result)
    assert any(f['name'] == 'test_dir' and f['type'] == 'directory' for f in result)
    mock_ssh_client.exec_command.assert_called_once_with("ls -la ~")

@pytest.mark.asyncio
async def test_list_directory_error(file_operations, mock_ssh_client):
    """Тест обработки ошибки при получении списка файлов."""
    # Подготовка мок-данных с ошибкой
    mock_stderr = Mock()
    mock_stderr.read.return_value = b"Permission denied"
    
    mock_ssh_client.exec_command.return_value = (None, Mock(), mock_stderr)
    
    # Проверка выброса исключения
    with pytest.raises(Exception) as exc_info:
        await file_operations.list_directory()
    
    assert "Failed to list directory" in str(exc_info.value)

@pytest.mark.asyncio
async def test_read_text_files_success(file_operations, mock_ssh_client):
    """Тест успешного чтения текстовых файлов."""
    # Подготовка мок-данных для list_directory
    mock_stdout_ls = Mock()
    mock_stdout_ls.read.return_value = b"""total 4
drwxr-xr-x 2 user user 4096 Mar 10 10:00 .
-rw-r--r-- 1 user user   10 Mar 10 10:00 test.txt"""
    
    mock_stderr_ls = Mock()
    mock_stderr_ls.read.return_value = b""
    
    # Подготовка мок-данных для file
    mock_stdout_file = Mock()
    mock_stdout_file.read.return_value = b"test.txt: ASCII text"
    
    # Подготовка мок-данных для cat
    mock_stdout_cat = Mock()
    mock_stdout_cat.read.return_value = b"test content"
    
    mock_stderr = Mock()
    mock_stderr.read.return_value = b""
    
    # Настройка последовательных вызовов exec_command
    mock_ssh_client.exec_command.side_effect = [
        (None, mock_stdout_ls, mock_stderr_ls),  # для ls
        (None, mock_stdout_file, mock_stderr),   # для file
        (None, mock_stdout_cat, mock_stderr)     # для cat
    ]
    
    # Выполнение теста
    result = await file_operations.read_text_files()
    
    # Проверки
    assert len(result) == 1
    assert 'test.txt' in result
    assert result['test.txt'] == 'test content'
    assert mock_ssh_client.exec_command.call_count == 3

@pytest.mark.asyncio
async def test_read_text_files_no_text_files(file_operations, mock_ssh_client):
    """Тест чтения директории без текстовых файлов."""
    # Подготовка мок-данных
    mock_stdout_ls = Mock()
    mock_stdout_ls.read.return_value = b"""total 4
drwxr-xr-x 2 user user 4096 Mar 10 10:00 .
-rw-r--r-- 1 user user   10 Mar 10 10:00 test.bin"""
    
    mock_stderr_ls = Mock()
    mock_stderr_ls.read.return_value = b""
    
    mock_stdout_file = Mock()
    mock_stdout_file.read.return_value = b"test.bin: data"
    
    mock_stderr = Mock()
    mock_stderr.read.return_value = b""
    
    mock_ssh_client.exec_command.side_effect = [
        (None, mock_stdout_ls, mock_stderr_ls),
        (None, mock_stdout_file, mock_stderr)
    ]
    
    # Выполнение теста
    result = await file_operations.read_text_files()
    
    # Проверки
    assert len(result) == 0
    assert mock_ssh_client.exec_command.call_count == 2 