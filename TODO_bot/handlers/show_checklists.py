# handlers/show_checklists.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import aiosqlite
from config import DB_NAME
from handlers.states import ChecklistReminder

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
        text = "📋 У вас пока нет чек-листов"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить чек-лист", callback_data="add_checklist")],
                [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]
            ]
        )
    else:
        text = "📋 Ваши чек-листы:"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=title, callback_data=f"checklist:{checklist_id}")]
                for checklist_id, title in rows
            ] + [
                [InlineKeyboardButton(text="➕ Добавить чек-лист", callback_data="add_checklist")],
                [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]
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
            [InlineKeyboardButton(text="⏰ Напоминания", callback_data=f"checklist_reminder_menu:{checklist_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить чек-лист", callback_data=f"delete_checklist:{checklist_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку чек-листов", callback_data="checklists")]
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
        [InlineKeyboardButton(text="📅 Ежедневно в ...", callback_data=f"cl_set_mode_daily:{checklist_id}")],
        [InlineKeyboardButton(text="⏱ Один раз в ...", callback_data=f"cl_set_mode_once:{checklist_id}")],
    ]
    if enabled:
        buttons.append([InlineKeyboardButton(text="🔕 Выключить напоминания", callback_data=f"cl_disable:{checklist_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🚫 Не присылать", callback_data=f"cl_disable:{checklist_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"checklist:{checklist_id}")])
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
        await cb.answer("Чек-лист не найден", show_alert=True)
        return

    enabled, mode, time, once_at, once_sent = row
    enabled = int(enabled or 0)
    mode = mode or "off"

    info = "выключено 🔕"
    if enabled and mode == "daily":
        info = f"ежедневно в {time or '??:??'} ✅"
    elif enabled and mode == "once":
        if once_sent:
            info = f"один раз (уже отправлено) ✅"
        else:
            info = f"один раз: {once_at or 'не задано'} ✅"

    text = f"⏰ Напоминания чек-листа\n\nТекущее: {info}\n\nВыберите режим:"
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
    await cb.answer("🔕 Выключено")


@router.callback_query(F.data.startswith("cl_set_mode_daily:"))
async def cl_set_mode_daily(cb: CallbackQuery, state: FSMContext):
    checklist_id = int(cb.data.split(":")[1])
    await state.set_state(ChecklistReminder.waiting_for_time)
    await state.update_data(checklist_id=checklist_id, mode="daily")
    await cb.message.edit_text(
        "Введите время (HH:MM), в которое присылать чек-лист ежедневно.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"checklist_reminder_menu:{checklist_id}")]
        ])
    )
    await cb.answer()


@router.callback_query(F.data.startswith("cl_set_mode_once:"))
async def cl_set_mode_once(cb: CallbackQuery, state: FSMContext):
    checklist_id = int(cb.data.split(":")[1])
    await state.set_state(ChecklistReminder.waiting_for_time)
    await state.update_data(checklist_id=checklist_id, mode="once")
    await cb.message.edit_text(
        "Введите время (HH:MM), в которое прислать чек-лист ОДИН раз (ближайшее такое время).",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"checklist_reminder_menu:{checklist_id}")]
        ])
    )
    await cb.answer()


@router.message(ChecklistReminder.waiting_for_time)
async def cl_time_message(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введите время текстом в формате HH:MM.")
        return

    t = message.text.strip()
    try:
        hh, mm = t.split(":")
        hh = int(hh); mm = int(mm)
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError()
        t = f"{hh:02d}:{mm:02d}"
    except Exception:
        await message.answer("❌ Неверный формат. Пример: 09:30")
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
    await message.answer("✅ Готово. Настройки сохранены.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Открыть настройки напоминаний", callback_data=f"checklist_reminder_menu:{checklist_id}")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]
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
    await cb.answer("🗑️ Чек-лист удалён")

