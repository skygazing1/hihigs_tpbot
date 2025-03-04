from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def process_start_command(message: Message):
    await message.answer("Привет!")

@dp.message(Command("info"))
async def process_start_command(message: Message):
    await message.answer("Здесь скоро будет информация о боте!")

@dp.message()
async def echo_message(message: Message):
    await message.answer(message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())