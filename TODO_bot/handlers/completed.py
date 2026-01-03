# handlers/completed.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from config import DB_NAME
from utils.safe_edit import safe_edit
import logging

router = Router()
logger = logging.getLogger(__name__)

PAGE_SIZE = 10  # сколько выполненных задач показывать на одной странице


async def get_completed_tasks(user_id: int, page: int = 1):
    offset = (page - 1) * PAGE_SIZE
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title, completed_at FROM completed WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (user_id, PAGE_SIZE, offset)
        )
        tasks = await cursor.fetchall()

        # общее количество
        cursor2 = await db.execute(
            "SELECT COUNT(*) FROM completed WHERE user_id=?",
            (user_id,)
        )
        total_count = (await cursor2.fetchone())[0]

    return tasks, total_count


async def build_keyboard(page: int, total_count: int):
    kb = []

    # Навигация
    nav_row = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"done_tasks::{page-1}")
        )
    if page * PAGE_SIZE < total_count:
        nav_row.append(
            InlineKeyboardButton(text="➡️ Вперед", callback_data=f"done_tasks::{page+1}")
        )
    if nav_row:
        kb.append(nav_row)

    # Очистка истории
    kb.append([InlineKeyboardButton(text="🗑 Очистить историю", callback_data=f"clear_completed::{page}")])

    # Назад в меню
    kb.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(F.data.startswith("done_tasks"))
async def done_tasks(cb: CallbackQuery):
    page = 1
    try:
        page = int(cb.data.split("::")[1])
    except (IndexError, ValueError):
        page = 1

    tasks, total_count = await get_completed_tasks(cb.from_user.id, page)

    if not tasks:
        await safe_edit(cb, "❌ Выполненных дел нет", reply_markup=None)
        return

    text = "✅ Выполненные дела:\n\n"
    for _, title, date in tasks:
        text += f"• {title}\n🕒 {date}\n\n"

    keyboard = await build_keyboard(page, total_count)
    await safe_edit(cb, text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("clear_completed"))
async def clear_completed(cb: CallbackQuery):
    page = 1
    try:
        page = int(cb.data.split("::")[1])
    except (IndexError, ValueError):
        page = 1

    # Подтверждение очистки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"clear_completed_confirm::{page}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"done_tasks::{page}")
        ]
    ])
    await safe_edit(cb, "⚠️ Вы уверены, что хотите очистить всю историю выполненных дел?", keyboard)


@router.callback_query(F.data.startswith("clear_completed_confirm"))
async def confirm_clear(cb: CallbackQuery):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "DELETE FROM completed WHERE user_id=?",
                (cb.from_user.id,)
            )
            await db.commit()
        logger.info(f"Completed tasks cleared for user {cb.from_user.id}")
        await safe_edit(cb, "✅ История выполненных дел очищена", reply_markup=None)
    except Exception as e:
        logger.error(f"Failed to clear completed tasks for user {cb.from_user.id}: {e}")
        await safe_edit(cb, "❌ Не удалось очистить историю", reply_markup=None)
