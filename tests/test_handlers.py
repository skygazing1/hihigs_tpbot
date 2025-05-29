import pytest
from aiogram.types import Message, CallbackQuery
from types import SimpleNamespace
from models import User, async_session, Base
from sqlalchemy import text

from handlers.help import help_handler
from handlers.status import status_handler, status_callback
from handlers.start import cmd_start, process_role_selection

class FakeMessage:
    def __init__(self, user_id=123456789, username="test_user", text="/command"):
        self.from_user = SimpleNamespace(id=user_id, username=username)
        self.text = text
        self.response = None

    async def answer(self, text, reply_markup=None, **kwargs):
        self.response = text

class FakeCallback:
    def __init__(self, user_id=123456789, username="test_user", data="callback_data"):
        self.from_user = SimpleNamespace(id=user_id, username=username)
        self.message = FakeMessage(user_id, username)
        self.data = data
        self.response = None

    async def answer(self):
        self.response = "callback answered"

@pytest.fixture(autouse=True)
async def cleanup_database():
    """Clean up the database before each test."""
    async with async_session() as session:
        # Delete all records from all tables
        await session.execute(text("DELETE FROM submissions"))
        await session.execute(text("DELETE FROM tasks"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()

@pytest.mark.asyncio
async def test_help_handler():
    msg = FakeMessage(text="/help")
    await help_handler(msg)
    assert "Справка" in msg.response

@pytest.mark.asyncio
async def test_status_handler():
    # Create test user
    async with async_session() as session:
        user = User(userid=123456789, username="test_user")
        session.add(user)
        await session.commit()

    msg = FakeMessage(text="/status")
    await status_handler(msg)
    assert "Твой ID" in msg.response

@pytest.mark.asyncio
async def test_status_callback():
    # Create test user
    async with async_session() as session:
        user = User(userid=123456789, username="test_user")
        session.add(user)
        await session.commit()

    callback = FakeCallback()
    await status_callback(callback)
    assert "Твой ID" in callback.message.response

@pytest.mark.asyncio
async def test_start_handler():
    msg = FakeMessage(text="/start")
    await cmd_start(msg)
    assert "Добро пожаловать" in msg.response

@pytest.mark.asyncio
async def test_role_selection_tutor():
    callback = FakeCallback(data="role_tutor")
    await process_role_selection(callback)
    assert "Вы зарегистрированы как преподаватель" in callback.message.response

@pytest.mark.asyncio
async def test_role_selection_student():
    callback = FakeCallback(data="role_student")
    await process_role_selection(callback)
    assert "Введите код преподавателя" in callback.message.response
