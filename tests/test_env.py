import os
from pathlib import Path
from dotenv import load_dotenv

def test_env_file_exists():
    assert Path(".env").exists(), ".env file not found"

def test_logs_folder_exists():
    assert Path("logs").exists(), "logs folder not found"

def test_token_exists():
    load_dotenv()
    assert os.getenv("BOT_TOKEN"), "BOT_TOKEN is not set"
