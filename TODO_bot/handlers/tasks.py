from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from handlers.states import AddTask
from utils.safe_edit import safe_edit

import aiosqlite
import logging

from config import DB_NAME
from keyboards.inline import main_menu, cancel_task

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "add_task")
async def add_task(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddTask.waiting_for_text)
    await cb.message.edit_text(
        "✏️ Введите новое дело:",
        reply_markup=cancel_task()
    )


@router.message(AddTask.waiting_for_text, F.text)
async def save_task(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO tasks (user_id, title) VALUES (?, ?)",
            (message.from_user.id, message.text.strip())
        )
        await db.commit()

    await state.clear()
    logger.info(f"Task added: {message.from_user.id}")

    await message.answer(
        "✅ Дело добавлено",
        reply_markup=main_menu(message.from_user.id)
    )

@router.message(AddTask.waiting_for_text)
async def add_task_not_text(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте текстовое сообщение.\n"
        "Фото, видео и файлы не принимаются.",
        reply_markup=cancel_task()
    )


@router.callback_query(F.data == "show_tasks")
async def show_tasks(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title FROM tasks WHERE user_id=? ORDER BY id",
            (cb.from_user.id,)
        )
        tasks = await cursor.fetchall()

    if not tasks:
        await safe_edit(cb, "✅ Дел нет", reply_markup=main_menu(cb.from_user.id))
        return

    text = "📋 Текущие дела:\n\n"

    # 🔥 Настройки кнопок
    keyboard = []
    row = []
    COLUMNS = 3  # количество кнопок в одном ряду

    for idx, (task_id, title) in enumerate(tasks, start=1):
        text += f"{idx}. {title}\n"

        row.append(
            InlineKeyboardButton(
                text=f"✅ {idx}",
                callback_data=f"complete_{task_id}"
            )
        )

        if len(row) == COLUMNS:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Кнопка "Выполнить все"
    keyboard.append([InlineKeyboardButton(text="🗑 Выполнить все", callback_data="complete_all")])

    # Кнопка "В меню"
    keyboard.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")])

    # Используем safe_edit, чтобы избежать ошибки Telegram
    await safe_edit(cb, text, InlineKeyboardMarkup(inline_keyboard=keyboard))