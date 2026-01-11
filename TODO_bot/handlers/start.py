from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import logging

from keyboards.inline import main_menu
from database.db import register_user
from texts import START_TITLE

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def start(message: Message):
    await register_user(message.from_user)
    logger.info(f"User start: {message.from_user.id}")
    await message.answer(START_TITLE, reply_markup=main_menu(message.from_user.id))
