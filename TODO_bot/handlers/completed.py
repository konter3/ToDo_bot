from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite
from config import DB_NAME
from keyboards.inline import back_menu

router = Router()

@router.callback_query(F.data == "done_tasks")
async def done_tasks(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT title, completed_at FROM completed WHERE user_id=? ORDER BY id DESC",
            (cb.from_user.id,)
        )
        rows = await cursor.fetchall()

    if not rows:
        await cb.message.edit_text("❌ Выполненных дел нет", reply_markup=back_menu())
        return

    text = "✅ Выполненные дела:\n\n"
    for title, date in rows:
        text += f"• {title}\n🕒 {date}\n\n"

    await cb.message.edit_text(text, reply_markup=back_menu())
