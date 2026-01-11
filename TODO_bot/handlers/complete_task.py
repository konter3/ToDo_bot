from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.inline import main_menu
from handlers.tasks import show_tasks
from config import DB_NAME

from texts import TASK_NOT_FOUND, TASK_DONE, TASKS_NONE_TO_COMPLETE, TASKS_ALL_DONE

import aiosqlite
import logging

router = Router()
logger = logging.getLogger(__name__)

# --- выполнить одну задачу ---
@router.callback_query(F.data.startswith("complete_") & ~F.data.endswith("_all"))
async def complete_task(cb: CallbackQuery):
    task_id = int(cb.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        # Сначала получаем заголовок задачи
        cursor = await db.execute(
            "SELECT title FROM tasks WHERE id=? AND user_id=?",
            (task_id, cb.from_user.id)
        )
        row = await cursor.fetchone()

        if not row:
            await cb.answer(TASK_NOT_FOUND, show_alert=True)
            return

        title = row[0]

        # Удаляем задачу из tasks
        await db.execute(
            "DELETE FROM tasks WHERE id=? AND user_id=?",
            (task_id, cb.from_user.id)
        )

        # Добавляем в completed
        await db.execute(
            "INSERT INTO completed (user_id, title, completed_at) VALUES (?, ?, datetime('now'))",
            (cb.from_user.id, title)
        )
        await db.commit()

    await cb.answer(TASK_DONE)

    # Обновляем список задач после выполнения
    await show_tasks(cb)


# --- выполнить все задачи ---
@router.callback_query(F.data == "complete_all")
async def complete_all_tasks(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        # Берем все задачи пользователя
        cursor = await db.execute(
            "SELECT id, title FROM tasks WHERE user_id=?",
            (cb.from_user.id,)
        )
        tasks = await cursor.fetchall()

        if not tasks:
            await cb.answer(TASKS_NONE_TO_COMPLETE, show_alert=True)
            return

        # Переносим все в completed
        for task_id, title in tasks:
            await db.execute(
                "INSERT INTO completed (user_id, title, completed_at) VALUES (?, ?, datetime('now'))",
                (cb.from_user.id, title)
            )

        # Удаляем из tasks
        await db.execute(
            "DELETE FROM tasks WHERE user_id=?",
            (cb.from_user.id,)
        )
        await db.commit()

    logger.info(f"All tasks completed for user {cb.from_user.id}")
    await cb.answer(TASKS_ALL_DONE)
    await show_tasks(cb)
