import sys
from settings import bot_token
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from aiogram_dialog import DialogRegistry

sys.path.insert(0, '..')
admin_bot = Bot(token=bot_token, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(admin_bot, storage=storage)
registry = DialogRegistry(dp)
