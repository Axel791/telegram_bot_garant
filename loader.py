import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

dotenv_path = os.path.abspath(os.path.join('.env'))
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


BOT_API = os.getenv('BOT_TOKEN')
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_API, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())