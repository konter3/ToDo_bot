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

from texts import (
    BTN_ADD_CHECKLIST,
    BTN_MENU,
    CHECKLIST_CREATE_CANCELED,
    CHECKLIST_ITEMS_MIN_1,
    CHECKLIST_ITEMS_NOT_TEXT,
    CHECKLIST_ITEMS_PROMPT,
    CHECKLISTS_EMPTY,
    CHECKLISTS_HEADER,
    CHECKLIST_TITLE_EMPTY,
    CHECKLIST_TITLE_NOT_TEXT,
    CHECKLIST_TITLE_PROMPT,
)

router = Router()


@router.callback_query(F.data == "add_checklist")
async def start_create_checklist(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(ChecklistFSM.title)

    await cb.message.edit_text(
        CHECKLIST_TITLE_PROMPT,
        reply_markup=cancel_checklist_kb()
    )
    await cb.answer()


@router.message(ChecklistFSM.title)
async def checklist_title(message: Message, state: FSMContext):
    if not message.text:  # Проверяем, что сообщение текстовое
        await message.answer(CHECKLIST_TITLE_NOT_TEXT)
        return

    title = message.text.strip()
    if not title:
        await message.answer(CHECKLIST_TITLE_EMPTY)
        return

    await state.update_data(title=title)
    await state.set_state(ChecklistFSM.items)

    await message.answer(CHECKLIST_ITEMS_PROMPT, reply_markup=cancel_checklist_kb())


@router.message(ChecklistFSM.items)
async def checklist_items(message: Message, state: FSMContext):
    if not message.text:  # Проверка на текст
        await message.answer(CHECKLIST_ITEMS_NOT_TEXT)
        return

    data = await state.get_data()
    title = data["title"]

    items = [line.strip() for line in message.text.split("\n") if line.strip()]
    if not items:
        await message.answer(CHECKLIST_ITEMS_MIN_1)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO checklists (user_id, title, created_at) VALUES (?, ?, ?)",
            (message.from_user.id, title, datetime.now().strftime("%d.%m.%Y %H:%M"))
        )
        checklist_id = cursor.lastrowid

        for item in items:
            await db.execute(
                "INSERT INTO checklist_items (checklist_id, title, completed) VALUES (?, ?, 0)",
                (checklist_id, item)
            )
        await db.commit()

    await state.clear()

    # --- Формируем список чек-листов так же, как в show_checklists ---
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title FROM checklists WHERE user_id=? ORDER BY id DESC",
            (message.from_user.id,)
        )
        rows = await cursor.fetchall()

    if not rows:
        text = CHECKLISTS_EMPTY
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=BTN_ADD_CHECKLIST, callback_data="add_checklist")],
                [InlineKeyboardButton(text=BTN_MENU, callback_data="menu")]
            ]
        )
    else:
        text = CHECKLISTS_HEADER
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=title, callback_data=f"checklist:{checklist_id}")]
                for checklist_id, title in rows
            ] + [
                [InlineKeyboardButton(text=BTN_ADD_CHECKLIST, callback_data="add_checklist")],
                [InlineKeyboardButton(text=BTN_MENU, callback_data="menu")]
            ]
        )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "cancel_checklist")
async def cancel_checklist_handler(cb: CallbackQuery, state: FSMContext):
    await state.clear()

    await cb.message.edit_text(
        CHECKLIST_CREATE_CANCELED,
        reply_markup=main_menu(cb.from_user.id)
    )
    await cb.answer()
