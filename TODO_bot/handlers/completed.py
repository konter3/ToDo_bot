# handlers/completed.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from config import DB_NAME
from utils.safe_edit import safe_edit
import logging

from texts import (
    BTN_BACK,
    BTN_CLEAR_HISTORY,
    BTN_MENU,
    BTN_NEXT,
    BTN_CANCEL,
    BTN_YES,
    DONE_TASKS_CLEAR_CONFIRM,
    DONE_TASKS_CLEAR_FAILED,
    DONE_TASKS_CLEARED,
    DONE_TASKS_EMPTY,
    DONE_TASKS_HEADER,
)

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
            InlineKeyboardButton(text=BTN_BACK, callback_data=f"done_tasks::{page-1}")
        )
    if page * PAGE_SIZE < total_count:
        nav_row.append(
            InlineKeyboardButton(text=BTN_NEXT, callback_data=f"done_tasks::{page+1}")
        )
    if nav_row:
        kb.append(nav_row)

    # Очистка истории
    kb.append([InlineKeyboardButton(text=BTN_CLEAR_HISTORY, callback_data=f"clear_completed::{page}")])

    # Назад в меню
    kb.append([InlineKeyboardButton(text=BTN_MENU, callback_data="menu")])

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
        # Даже если список пустой — даём пользователю выход обратно в меню.
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=BTN_MENU, callback_data="menu")]]
        )
        await safe_edit(cb, DONE_TASKS_EMPTY, reply_markup=keyboard)
        return

    text = DONE_TASKS_HEADER
    for _, title, date in tasks:
        text += f"• {title}\n🕒 {date}\n\n"

    keyboard = await build_keyboard(page, total_count)
    await safe_edit(cb, text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("clear_completed::"))
async def clear_completed(cb: CallbackQuery):
    page = 1
    try:
        page = int(cb.data.split("::")[1])
    except (IndexError, ValueError):
        page = 1

    # Подтверждение очистки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_YES, callback_data=f"clear_completed_confirm::{page}"),
            InlineKeyboardButton(text=BTN_CANCEL, callback_data=f"done_tasks::{page}")
        ]
    ])
    await safe_edit(cb, DONE_TASKS_CLEAR_CONFIRM, keyboard)


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
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=BTN_MENU, callback_data="menu")]]
        )
        await safe_edit(cb, DONE_TASKS_CLEARED, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Failed to clear completed tasks for user {cb.from_user.id}: {e}")
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=BTN_MENU, callback_data="menu")]]
        )
        await safe_edit(cb, DONE_TASKS_CLEAR_FAILED, reply_markup=keyboard)
