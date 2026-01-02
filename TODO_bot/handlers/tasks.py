from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.states import AddTask
import aiosqlite
import logging

from config import DB_NAME
from keyboards.inline import main_menu

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "add_task")
async def add_task(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddTask.waiting_for_text)
    await cb.message.edit_text("✏️ Введите новое дело:")

@router.message(AddTask.waiting_for_text)
async def save_task(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO tasks (user_id, title) VALUES (?, ?)",
            (message.from_user.id, message.text)
        )
        await db.commit()

    await state.clear()
    logger.info(f"Task added: {message.from_user.id}")
    await message.answer("✅ Дело добавлено", reply_markup=main_menu(message.from_user.id))

@router.callback_query(F.data == "show_tasks")
async def show_tasks(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title FROM tasks WHERE user_id=? ORDER BY id",
            (cb.from_user.id,)
        )
        tasks = await cursor.fetchall()

    if not tasks:
        await cb.message.edit_text("✅ Дел нет", reply_markup=main_menu(cb.from_user.id))
        return

    text = "📋 Текущие дела:\n\n"
    keyboard = []

    for idx, (task_id, title) in enumerate(tasks, start=1):
        text += f"{idx}. {title}\n"
        keyboard.append([
            InlineKeyboardButton(text=f"✅ {idx}", callback_data=f"complete_{task_id}")
        ])

    keyboard.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith("complete_"))
async def complete_task(cb: CallbackQuery):
    task_id = int(cb.data.split("_")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "DELETE FROM tasks WHERE id=? AND user_id=? RETURNING title",
            (task_id, cb.from_user.id)
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            await db.execute(
                "INSERT INTO completed (user_id, title, completed_at) VALUES (?, ?, datetime('now'))",
                (cb.from_user.id, row[0])
            )
            await db.commit()

    logger.info(f"Task completed: {task_id}")
    await show_tasks(cb)
