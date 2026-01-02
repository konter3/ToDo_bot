from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite
from config import DB_NAME
from keyboards.inline import back_menu
from utils.safe_edit import safe_edit  # 🔥 импортируем

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
        await safe_edit(cb, "❌ Выполненных дел нет", back_menu())
        return

    text = "✅ Выполненные дела:\n\n"
    for title, date in rows:
        text += f"• {title}\n🕒 {date}\n\n"

    await safe_edit(cb, text, back_menu())

