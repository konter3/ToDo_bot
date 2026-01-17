# handlers/show_checklists.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import aiosqlite
from config import DB_NAME
from handlers.states import ChecklistReminder, ChecklistEdit

from texts import (
    BTN_ADD_CHECKLIST,
    BTN_BACK,
    BTN_CHECKLIST_BACK_TO_LIST,
    BTN_CHECKLIST_DELETE,
    BTN_CHECKLIST_EDIT,
    BTN_CHECKLIST_ADD_ITEM,
    BTN_CHECKLIST_DELETE_ITEM,
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
    CL_INFO_WEEKLY,
    CL_INFO_OFF,
    CL_INFO_ONCE_AT,
    CL_INFO_ONCE_SENT,
    CL_PROMPT_DAILY,
    CL_PROMPT_ONCE,
    CL_PROMPT_WEEKDAY,
    CL_DAYS_SELECTED,
    CL_DAYS_NONE,
    BTN_DONE,
    BTN_EVERY_DAY,
    WEEKDAYS_SHORT,
    WEEKDAYS,
    CHECKLIST_EDIT_PICK_ITEM,
    CHECKLIST_EDIT_ITEM_PROMPT,
    CHECKLIST_EDIT_ITEM_SAVED,
    CHECKLIST_ADD_ITEM_PROMPT,
    CHECKLIST_ADD_ITEM_SAVED,
    CHECKLIST_DELETE_PICK_ITEM,
    CHECKLIST_DELETE_ITEM_SAVED,
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
            [
                InlineKeyboardButton(text=BTN_CHECKLIST_ADD_ITEM, callback_data=f"checklist_add_item:{checklist_id}"),
            ],
            [
                InlineKeyboardButton(text=BTN_CHECKLIST_EDIT, callback_data=f"checklist_edit:{checklist_id}"),
            ],
            [
                InlineKeyboardButton(text=BTN_CHECKLIST_DELETE_ITEM, callback_data=f"checklist_delete_item:{checklist_id}"),
            ],
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


# --- Управление пунктами чек-листа ---


@router.callback_query(F.data.startswith("checklist_edit:"))
async def checklist_edit_menu(cb: CallbackQuery, state: FSMContext):
    """Show a menu to choose which item to edit."""
    await state.clear()
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT id, title FROM checklist_items WHERE checklist_id=? ORDER BY id ASC",
            (checklist_id,),
        )
        items = await cur.fetchall()

    if not items:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist:{checklist_id}")]]
        )
        await cb.message.edit_text("📭 В чек-листе пока нет пунктов.", reply_markup=kb)
        await cb.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=f"checklist_edit_item:{checklist_id}:{item_id}")]
            for item_id, title in items
        ] + [[InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist:{checklist_id}")]]
    )
    await cb.message.edit_text(CHECKLIST_EDIT_PICK_ITEM, reply_markup=keyboard)
    await cb.answer()


@router.callback_query(F.data.startswith("checklist_edit_item:"))
async def checklist_edit_item_start(cb: CallbackQuery, state: FSMContext):
    # checklist_edit_item:{checklist_id}:{item_id}
    _, checklist_id_str, item_id_str = cb.data.split(":")
    checklist_id = int(checklist_id_str)
    item_id = int(item_id_str)

    await state.set_state(ChecklistEdit.waiting_for_item_text)
    await state.update_data(checklist_id=checklist_id, item_id=item_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist_edit:{checklist_id}")]]
    )
    await cb.message.edit_text(CHECKLIST_EDIT_ITEM_PROMPT, reply_markup=kb)
    await cb.answer()


@router.message(ChecklistEdit.waiting_for_item_text)
async def checklist_edit_item_msg(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(CHECKLIST_EDIT_ITEM_PROMPT)
        return
    new_text = message.text.strip()
    if not new_text:
        await message.answer(CHECKLIST_EDIT_ITEM_PROMPT)
        return

    data = await state.get_data()
    checklist_id = int(data["checklist_id"])
    item_id = int(data["item_id"])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE checklist_items SET title=? WHERE id=? AND checklist_id=?",
            (new_text, item_id, checklist_id),
        )
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть чек-лист", callback_data=f"checklist:{checklist_id}")],
            [InlineKeyboardButton(text=BTN_MENU, callback_data="menu")],
        ]
    )
    await message.answer(CHECKLIST_EDIT_ITEM_SAVED, reply_markup=kb)


@router.callback_query(F.data.startswith("checklist_add_item:"))
async def checklist_add_item_start(cb: CallbackQuery, state: FSMContext):
    checklist_id = int(cb.data.split(":")[1])
    await state.set_state(ChecklistEdit.waiting_for_new_item_text)
    await state.update_data(checklist_id=checklist_id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist:{checklist_id}")]]
    )
    await cb.message.edit_text(CHECKLIST_ADD_ITEM_PROMPT, reply_markup=kb)
    await cb.answer()


@router.message(ChecklistEdit.waiting_for_new_item_text)
async def checklist_add_item_msg(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(CHECKLIST_ADD_ITEM_PROMPT)
        return
    title = message.text.strip()
    if not title:
        await message.answer(CHECKLIST_ADD_ITEM_PROMPT)
        return

    data = await state.get_data()
    checklist_id = int(data["checklist_id"])

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO checklist_items (checklist_id, title, completed) VALUES (?, ?, 0)",
            (checklist_id, title),
        )
        await db.commit()

    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть чек-лист", callback_data=f"checklist:{checklist_id}")],
            [InlineKeyboardButton(text=BTN_MENU, callback_data="menu")],
        ]
    )
    await message.answer(CHECKLIST_ADD_ITEM_SAVED, reply_markup=kb)


@router.callback_query(F.data.startswith("checklist_delete_item:"))
async def checklist_delete_item_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT id, title FROM checklist_items WHERE checklist_id=? ORDER BY id ASC",
            (checklist_id,),
        )
        items = await cur.fetchall()

    if not items:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist:{checklist_id}")]]
        )
        await cb.message.edit_text("📭 В чек-листе пока нет пунктов.", reply_markup=kb)
        await cb.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=f"checklist_delete_item_do:{checklist_id}:{item_id}")]
            for item_id, title in items
        ] + [[InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist:{checklist_id}")]]
    )

    await cb.message.edit_text(CHECKLIST_DELETE_PICK_ITEM, reply_markup=keyboard)
    await cb.answer()


@router.callback_query(F.data.startswith("checklist_delete_item_do:"))
async def checklist_delete_item_do(cb: CallbackQuery):
    # checklist_delete_item_do:{checklist_id}:{item_id}
    _, checklist_id_str, item_id_str = cb.data.split(":")
    checklist_id = int(checklist_id_str)
    item_id = int(item_id_str)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM checklist_items WHERE id=? AND checklist_id=?",
            (item_id, checklist_id),
        )
        await db.commit()

    # Back to checklist
    cb.data = f"checklist:{checklist_id}"
    await open_checklist(cb)
    await cb.answer(CHECKLIST_DELETE_ITEM_SAVED)



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


def _mask_to_days(mask: int) -> str:
    days = [WEEKDAYS_SHORT[i] for i in range(7) if (mask & (1 << i))]
    return ", ".join(days) if days else "—"


def _weekdays_multi_kb(checklist_id: int, mask: int):
    # mask: bitmask of selected weekdays (1<<0 is Mon ... 1<<6 is Sun). 0 means none.
    rows = []

    # Top row: every day shortcut
    rows.append([InlineKeyboardButton(text=BTN_EVERY_DAY, callback_data=f"cl_days_all:{checklist_id}")])

    # Days grid (2 columns)
    day_buttons = []
    for i in range(7):
        checked = "✅ " if (mask & (1 << i)) else "▫️ "
        day_buttons.append(InlineKeyboardButton(text=f"{checked}{WEEKDAYS_SHORT[i]}", callback_data=f"cl_days_toggle:{checklist_id}:{i}"))

    for i in range(0, 6, 2):
        rows.append([day_buttons[i], day_buttons[i + 1]])
    rows.append([day_buttons[6]])

    # Actions
    rows.append([InlineKeyboardButton(text=BTN_DONE, callback_data=f"cl_days_done:{checklist_id}")])
    rows.append([InlineKeyboardButton(text=BTN_BACK, callback_data=f"checklist_reminder_menu:{checklist_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("checklist_reminder_menu:"))
async def checklist_reminder_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    checklist_id = int(cb.data.split(":")[1])

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT reminder_enabled, reminder_mode, reminder_time, reminder_once_at, once_sent, reminder_weekday, reminder_weekdays_mask FROM checklists WHERE id=?",
            (checklist_id,)
        )
        row = await cur.fetchone()

    if not row:
        await cb.answer(CHECKLIST_NOT_FOUND, show_alert=True)
        return

    enabled, mode, time, once_at, once_sent, wd, wd_mask = row
    enabled = int(enabled or 0)
    mode = mode or "off"

    info = CL_INFO_OFF
    if enabled and mode == "daily":
        if wd_mask is not None:
            days = _mask_to_days(int(wd_mask))
            info = f"по дням: {days} в {(time or '??:??')} ✅"
        elif wd is None:
            info = CL_INFO_DAILY.format(time=(time or "??:??"))
        else:
            info = CL_INFO_WEEKLY.format(weekday=WEEKDAYS[int(wd)], time=(time or "??:??"))
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
            "UPDATE checklists SET reminder_enabled=0, reminder_mode='off', reminder_time=NULL, reminder_once_at=NULL, once_sent=0, reminder_weekday=NULL, reminder_weekdays_mask=NULL WHERE id=?",
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

    t_raw = message.text.strip()
    try:
        hh, mm = t_raw.split(":")
        hh_i = int(hh)
        mm_i = int(mm)
        if not (0 <= hh_i <= 23 and 0 <= mm_i <= 59):
            raise ValueError()
        t = f"{hh_i:02d}:{mm_i:02d}"
    except Exception:
        await message.answer(TIME_INPUT_BAD)
        return

    data = await state.get_data()
    checklist_id = int(data["checklist_id"])
    mode = data.get("mode", "daily")

    # Ask weekdays (multi-select) after time
    await state.update_data(time=t, mode=mode, days_mask=0)
    await state.set_state(ChecklistReminder.waiting_for_days)
    await message.answer(
        f"{CL_PROMPT_WEEKDAY}\n\n{CL_DAYS_NONE}",
        reply_markup=_weekdays_multi_kb(checklist_id, 0),
    )


@router.callback_query(F.data.startswith("cl_days_toggle:"))
async def cl_days_toggle(cb: CallbackQuery, state: FSMContext):
    # cl_days_toggle:{checklist_id}:{weekday}
    _, checklist_id_str, wd_str = cb.data.split(":")
    checklist_id = int(checklist_id_str)
    try:
        weekday = int(wd_str)
    except Exception:
        await cb.answer()
        return
    if not (0 <= weekday <= 6):
        await cb.answer()
        return

    data = await state.get_data()
    mask = int(data.get("days_mask", 0))
    mask ^= (1 << weekday)
    await state.update_data(days_mask=mask)

    days_text = CL_DAYS_SELECTED.format(days=_mask_to_days(mask)) if mask else CL_DAYS_NONE
    await cb.message.edit_text(
        f"{CL_PROMPT_WEEKDAY}\n\n{days_text}",
        reply_markup=_weekdays_multi_kb(checklist_id, mask),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("cl_days_all:"))
async def cl_days_all(cb: CallbackQuery, state: FSMContext):
    # cl_days_all:{checklist_id}
    checklist_id = int(cb.data.split(":")[1])
    mask = (1 << 7) - 1  # all days
    await state.update_data(days_mask=mask)

    days_text = CL_DAYS_SELECTED.format(days=_mask_to_days(mask))
    await cb.message.edit_text(
        f"{CL_PROMPT_WEEKDAY}\n\n{days_text}",
        reply_markup=_weekdays_multi_kb(checklist_id, mask),
    )
    await cb.answer()


def _next_occurrence_for_mask(now, hhmm: str, mask: int):
    """Return datetime of the next occurrence at hhmm on one of selected weekdays."""
    from datetime import timedelta

    target_base = now.replace(hour=int(hhmm[:2]), minute=int(hhmm[3:]), second=0, microsecond=0)
    best = None
    for wd in range(7):
        if not (mask & (1 << wd)):
            continue
        days_ahead = (wd - now.weekday()) % 7
        cand = target_base + timedelta(days=days_ahead)
        if cand <= now:
            cand = cand + timedelta(days=7)
        if best is None or cand < best:
            best = cand
    return best


@router.callback_query(F.data.startswith("cl_days_done:"))
async def cl_days_done(cb: CallbackQuery, state: FSMContext):
    # cl_days_done:{checklist_id}
    checklist_id = int(cb.data.split(":")[1])
    data = await state.get_data()
    mode = data.get("mode", "daily")
    t = data.get("time")
    mask = int(data.get("days_mask", 0))
    if not t:
        await cb.answer("Время не задано", show_alert=True)
        return
    if mask == 0:
        await cb.answer("Выберите хотя бы один день", show_alert=True)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        if mode == "daily":
            # NULL mask means "every day" (compat). We store explicit mask for selected days.
            store_mask = None if mask == ((1 << 7) - 1) else mask
            await db.execute(
                "UPDATE checklists SET reminder_enabled=1, reminder_mode='daily', reminder_time=?, reminder_weekday=NULL, reminder_weekdays_mask=?, reminder_once_at=NULL, once_sent=0, last_sent_date=NULL WHERE id=?",
                (t, store_mask, checklist_id),
            )
        else:
            from zoneinfo import ZoneInfo
            from datetime import datetime

            now = datetime.now(ZoneInfo("Europe/Moscow"))
            if mask == ((1 << 7) - 1):
                # as before: ближайшее такое время
                from datetime import timedelta
                target = now.replace(hour=int(t[:2]), minute=int(t[3:]), second=0, microsecond=0)
                if target <= now:
                    target = target + timedelta(days=1)
            else:
                target = _next_occurrence_for_mask(now, t, mask)

            once_at = target.strftime("%d.%m.%Y %H:%M")
            await db.execute(
                "UPDATE checklists SET reminder_enabled=1, reminder_mode='once', reminder_time=NULL, reminder_once_at=?, reminder_weekday=NULL, reminder_weekdays_mask=?, once_sent=0 WHERE id=?",
                (once_at, None if mask == ((1 << 7) - 1) else mask, checklist_id),
            )
        await db.commit()

    await state.clear()
    await cb.message.edit_text(
        SETTINGS_SAVED,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=BTN_CHECKLIST_OPEN_REMINDERS, callback_data=f"checklist_reminder_menu:{checklist_id}")],
                [InlineKeyboardButton(text=BTN_MENU, callback_data="menu")],
            ]
        ),
    )
    await cb.answer()


# Backward compatibility: old single weekday selector callbacks.
@router.callback_query(F.data.startswith("cl_weekday:"))
async def cl_set_weekday_legacy(cb: CallbackQuery, state: FSMContext):
    # cl_weekday:{checklist_id}:{weekday|any}
    _, checklist_id_str, wd_str = cb.data.split(":")
    checklist_id = int(checklist_id_str)
    if wd_str == "any":
        mask = (1 << 7) - 1
    else:
        try:
            wd = int(wd_str)
            mask = (1 << wd)
        except Exception:
            await cb.answer()
            return
    await state.update_data(days_mask=mask)
    # Reuse the new "done" flow
    cb.data = f"cl_days_done:{checklist_id}"
    await cl_days_done(cb, state)


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

