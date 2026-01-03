# handlers/checklists_create.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import aiosqlite
from datetime import datetime

from states.checklist import ChecklistFSM
from keyboards.checklists import cancel_checklist_kb
from keyboards.inline import main_menu
from config import DB_NAME
from handlers.checklist import render_checklists
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "add_checklist")
async def start_create_checklist(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ChecklistFSM.title)

    await cb.message.edit_text(
        "Введите название чек-листа:",
        reply_markup=cancel_checklist_kb()
    )
    await cb.answer()


@router.message(ChecklistFSM.title)
async def checklist_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(ChecklistFSM.items)

    await message.answer(
        "📝 Введите пункты чек-листа.\n\n"
        "Каждый пункт — с новой строки.\n"
        "Когда закончите, отправьте сообщение.",
        reply_markup=cancel_checklist_kb()
    )

@router.message(ChecklistFSM.items)
async def checklist_items(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]

    items = [line.strip() for line in message.text.split("\n") if line.strip()]

    if not items:
        await message.answer("❌ Нужно минимум 1 пункт")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO checklists (user_id, title, created_at) VALUES (?, ?, ?)",
            (
                message.from_user.id,
                title,
                datetime.now().strftime("%d.%m.%Y %H:%M")
            )
        )
        checklist_id = cursor.lastrowid

        for item in items:
            await db.execute(
                "INSERT INTO checklist_items (checklist_id, title, completed) VALUES (?, ?, 0)",
                (checklist_id, item)
            )

        await db.commit()

    await state.clear()
    rows = await render_checklists(message.from_user.id)

    text = "✅ Чек-лист создан!\n\n📋 Ваши чек-листы:\n\n"
    for i, (_, title) in enumerate(rows, 1):
        text += f"{i}. {title}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить чек-лист", callback_data="add_checklist")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]
        ]
    )

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "cancel_checklist")
async def cancel_checklist_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await cb.message.edit_text(
        "❌ Создание чек-листа отменено",
        reply_markup=main_menu(cb.from_user.id)
    )
    await cb.answer()
