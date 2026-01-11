# handlers/show_checklists.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import aiosqlite
from config import DB_NAME
from handlers.states import ChecklistReminder

from texts import (
    BTN_ADD_CHECKLIST,
    BTN_BACK,
    BTN_CHECKLIST_BACK_TO_LIST,
    BTN_CHECKLIST_DELETE,
    BTN_CHECKLIST_REMINDERS,
    BTN_CHECKLIST_OPEN_REMINDERS,
    BTN_CL_DISABLE,
    BTN_CL_DONT_SEND,
    BTN_CL_MODE_DAILY,
    BTN_CL_MODE_ONCE,
    BTN_MENU,
    CHECKLIST_NOT_FOUND,
    CHECKLISTS_EMPTY,
    CHECKLISTS_HEADER,
    CHECKLIST_DELETED,
    CL_DISABLED_SHORT,
    SETTINGS_SAVED,
    TIME_INPUT_BAD,
    TIME_INPUT_PROMPT,
    CL_REMINDER_MENU,
    CL_INFO_DAILY,
    CL_INFO_OFF,
    CL_INFO_ONCE_AT,
    CL_INFO_ONCE_SENT,
    CL_PROMPT_DAILY,
    CL_PROMPT_ONCE,
)

router = Router()


# --- Показываем список чек-листов ---
@router.callback_query(F.data == "checklists")
async def show_checklists(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title FROM checklists WHERE user_id=? ORDER BY id DESC",
            (cb.from_user.id,)
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

    await cb.message.edit_text(text, reply_markup=keyboard)
    await cb.answer()


# --- Показываем конкретный чек-лист ---
@router.callback_query(F.data.startswith("checklist:"))
async def open_checklist(cb: CallbackQuery):
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title, completed FROM checklist_items WHERE checklist_id=?",
            (checklist_id,)
        )
        items = await cursor.fetchall()

        cursor = await db.execute(
            "SELECT title FROM checklists WHERE id=?",
            (checklist_id,)
        )
        checklist_title = (await cursor.fetchone())[0]

    text = f"📋 {checklist_title}\n\n"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ {title}" if completed else title,
                    callback_data=f"checklist_item:{checklist_id}:{item_id}"
                )
            ] for item_id, title, completed in items
        ] + [
            [InlineKeyboardButton(text=BTN_CHECKLIST_REMINDERS, callback_data=f"checklist_reminder_menu:{checklist_id}")],
            [InlineKeyboardButton(text=BTN_CHECKLIST_DELETE, callback_data=f"delete_checklist:{checklist_id}")],
            [InlineKeyboardButton(text=BTN_CHECKLIST_BACK_TO_LIST, callback_data="checklists")]
        ]
    )

    await cb.message.edit_text(text, reply_markup=keyboard)
    await cb.answer()


# --- Отмечаем / снимаем отметку с пункта ---
@router.callback_query(F.data.startswith("checklist_item:"))
async def toggle_checklist_item(cb: CallbackQuery):
    _, checklist_id, item_id = cb.data.split(":")
    checklist_id, item_id = int(checklist_id), int(item_id)

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT completed FROM checklist_items WHERE id=?",
            (item_id,)
        )
        completed = (await cursor.fetchone())[0]

        # Переключаем
        new_completed = 0 if completed else 1
        await db.execute(
            "UPDATE checklist_items SET completed=? WHERE id=?",
            (new_completed, item_id)
        )
        await db.commit()

    # Обновляем меню чек-листа
    await open_checklist(cb)



# --- Меню напоминаний чек-листа ---
def _cl_reminder_kb(checklist_id: int, enabled: bool):
    buttons = [
        [InlineKeyboardButton(text=BTN_CL_MODE_DAILY, callback_data=f"cl_set_mode_daily:{checklist_id}")],
        [InlineKeyboardButton(text=BTN_CL_MODE_ONCE, callback_data=f"cl_set_mode_once:{checklist_id}")],
    ]
    if enabled:
        buttons.append([InlineKeyboardButton(text=BTN_CL_DISABLE, callback_data=f"cl_disable:{checklist_id}")])
    else:
        buttons.append([InlineKeyboardButton(text=BTN_CL_DONT_SEND, callback_data=f"cl_disable:{checklist_id}")])
    buttons.append([InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist:{checklist_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("checklist_reminder_menu:"))
async def checklist_reminder_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT reminder_enabled, reminder_mode, reminder_time, reminder_once_at, once_sent FROM checklists WHERE id=?",
            (checklist_id,)
        )
        row = await cur.fetchone()

    if not row:
        await cb.answer(CHECKLIST_NOT_FOUND, show_alert=True)
        return

    enabled, mode, time, once_at, once_sent = row
    enabled = int(enabled or 0)
    mode = mode or "off"

    info = CL_INFO_OFF
    if enabled and mode == "daily":
        info = CL_INFO_DAILY.format(time=(time or "??:??"))
    elif enabled and mode == "once":
        if once_sent:
            info = CL_INFO_ONCE_SENT
        else:
            info = CL_INFO_ONCE_AT.format(once_at=(once_at or "не задано"))

    text = CL_REMINDER_MENU.format(info=info)
    await cb.message.edit_text(text, reply_markup=_cl_reminder_kb(checklist_id, bool(enabled)))
    await cb.answer()


@router.callback_query(F.data.startswith("cl_disable:"))
async def cl_disable(cb: CallbackQuery, state: FSMContext):
    checklist_id = int(cb.data.split(":")[1])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE checklists SET reminder_enabled=0, reminder_mode='off', reminder_time=NULL, reminder_once_at=NULL, once_sent=0 WHERE id=?",
            (checklist_id,)
        )
        await db.commit()

    await checklist_reminder_menu(cb, state)
    await cb.answer(CL_DISABLED_SHORT)


@router.callback_query(F.data.startswith("cl_set_mode_daily:"))
async def cl_set_mode_daily(cb: CallbackQuery, state: FSMContext):
    checklist_id = int(cb.data.split(":")[1])
    await state.set_state(ChecklistReminder.waiting_for_time)
    await state.update_data(checklist_id=checklist_id, mode="daily")
    await cb.message.edit_text(
        CL_PROMPT_DAILY,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist_reminder_menu:{checklist_id}")]
        ])
    )
    await cb.answer()


@router.callback_query(F.data.startswith("cl_set_mode_once:"))
async def cl_set_mode_once(cb: CallbackQuery, state: FSMContext):
    checklist_id = int(cb.data.split(":")[1])
    await state.set_state(ChecklistReminder.waiting_for_time)
    await state.update_data(checklist_id=checklist_id, mode="once")
    await cb.message.edit_text(
        CL_PROMPT_ONCE,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist_reminder_menu:{checklist_id}")]
        ])
    )
    await cb.answer()


@router.message(ChecklistReminder.waiting_for_time)
async def cl_time_message(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(TIME_INPUT_PROMPT)
        return

    t = message.text.strip()
    try:
        hh, mm = t.split(":")
        hh = int(hh); mm = int(mm)
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError()
        t = f"{hh:02d}:{mm:02d}"
    except Exception:
        await message.answer(TIME_INPUT_BAD)
        return

    data = await state.get_data()
    checklist_id = int(data["checklist_id"])
    mode = data.get("mode", "daily")

    async with aiosqlite.connect(DB_NAME) as db:
        if mode == "daily":
            await db.execute(
                "UPDATE checklists SET reminder_enabled=1, reminder_mode='daily', reminder_time=?, reminder_once_at=NULL, once_sent=0 WHERE id=?",
                (t, checklist_id)
            )
        else:
            from datetime import datetime, timedelta
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo("Europe/Moscow"))
            target = now.replace(hour=int(t[:2]), minute=int(t[3:]), second=0, microsecond=0)
            if target <= now:
                target = target + timedelta(days=1)
            once_at = target.strftime("%d.%m.%Y %H:%M")

            await db.execute(
                "UPDATE checklists SET reminder_enabled=1, reminder_mode='once', reminder_time=NULL, reminder_once_at=?, once_sent=0 WHERE id=?",
                (once_at, checklist_id)
            )
        await db.commit()

    await state.clear()

    # возвращаем в меню напоминаний
    fake_cb = type("FakeCb", (), {"from_user": message.from_user, "message": message, "answer": (lambda *a, **k: None)})
    # не используем fake_cb, просто показываем текст
    await message.answer(SETTINGS_SAVED, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_CHECKLIST_OPEN_REMINDERS, callback_data=f"checklist_reminder_menu:{checklist_id}")],
        [InlineKeyboardButton(text=BTN_MENU, callback_data="menu")]
    ]))
# --- Удаляем чек-лист ---
@router.callback_query(F.data.startswith("delete_checklist:"))
async def delete_checklist(cb: CallbackQuery):
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM checklist_items WHERE checklist_id=?", (checklist_id,))
        await db.execute("DELETE FROM checklists WHERE id=?", (checklist_id,))
        await db.commit()

    await show_checklists(cb)
    await cb.answer(CHECKLIST_DELETED)

