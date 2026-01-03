# handlers/show_checklists.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from config import DB_NAME

from handlers.checklist import render_checklists

router = Router()

@router.callback_query(F.data == "checklists")
async def show_checklists(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title FROM checklists WHERE user_id=? ORDER BY id DESC",
            (cb.from_user.id,)
        )
        rows = await cursor.fetchall()

    if not rows:
        text = "📋 У вас пока нет чек-листов"
    else:
        text = "📋 Ваши чек-листы:\n\n"
        for i, (_, title) in enumerate(rows, 1):
            text += f"{i}. {title}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить чек-лист",
                    callback_data="add_checklist"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ В меню",
                    callback_data="menu"
                )
            ]
        ]
    )

    await cb.message.edit_text(text, reply_markup=keyboard)
    await cb.answer()





