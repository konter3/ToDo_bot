from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline import main_menu
from texts import START_TITLE

router = Router()

@router.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery):
    await cb.message.edit_text(START_TITLE, reply_markup=main_menu(cb.from_user.id))
