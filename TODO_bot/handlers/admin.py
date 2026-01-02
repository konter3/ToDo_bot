from aiogram import Router
from aiogram.types import CallbackQuery
import aiosqlite
import logging

from config import DB_NAME, ADMIN_ID
from keyboards.inline import back_menu

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(lambda c: c.data == "users")
async def users(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("⛔ Нет доступа", show_alert=True)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id, username, first_name FROM users"
        )
        users = await cursor.fetchall()

    logger.warning("Admin requested users list")

    text = "👑 Пользователи:\n\n"
    for uid, username, name in users:
        text += f"👤 {name} | @{username} | {uid}\n"

    await cb.message.edit_text(text, reply_markup=back_menu())
