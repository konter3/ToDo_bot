from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.inline import main_menu
import aiosqlite
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "cancel_add_task")
async def cancel_add_task(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        "❌ Добавление дела отменено",
        reply_markup=main_menu(cb.from_user.id)
    )
