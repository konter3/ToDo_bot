# handlers/reminders.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import aiosqlite

from config import DB_NAME
from keyboards.inline import main_menu
from handlers.states import DailyReminder

from texts import (
    BTN_BACK,
    BTN_DAILY_DISABLE,
    BTN_DAILY_ENABLE,
    BTN_MENU,
    BTN_SET_TIME,
    CL_DISABLED_SHORT,
    DAILY_TIME_UPDATED,
    DAILY_ENABLED_SHORT,
    TIME_INPUT_BAD,
    TIME_INPUT_PROMPT,
)

router = Router()


def _parse_hhmm(s: str) -> str | None:
    """Accepts '9:30' or '09:30' and returns normalized 'HH:MM'."""
    try:
        hh, mm = s.split(":")
        hh_i = int(hh)
        mm_i = int(mm)
        if 0 <= hh_i <= 23 and 0 <= mm_i <= 59:
            return f"{hh_i:02d}:{mm_i:02d}"
    except Exception:
        pass
    return None


def daily_settings_kb(enabled: bool):
    buttons = [
        [InlineKeyboardButton(text=BTN_SET_TIME, callback_data="daily_reminder_set_time")]
    ]
    if enabled:
        buttons.append([InlineKeyboardButton(text=BTN_DAILY_DISABLE, callback_data="daily_reminder_disable")])
    else:
        buttons.append([InlineKeyboardButton(text=BTN_DAILY_ENABLE, callback_data="daily_reminder_enable")])
    buttons.append([InlineKeyboardButton(text=BTN_MENU, callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _render_daily_settings(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT daily_reminder_time, daily_reminder_enabled FROM users WHERE user_id=?",
            (cb.from_user.id,)
        )
        row = await cur.fetchone()

    time = (row[0] if row and row[0] else "10:00")
    enabled = int(row[1] if row and row[1] is not None else 1)

    text = (
        "⏰ Ежедневное напоминание о делах\n\n"
        f"Статус: {'включено ✅' if enabled else 'выключено 🔕'}\n"
        f"Время: {time} (Мск)\n\n"
        "Вы можете изменить время или выключить/включить напоминание."
    )
    await cb.message.edit_text(text, reply_markup=daily_settings_kb(bool(enabled)))


@router.callback_query(F.data == "daily_reminder_settings")
async def daily_reminder_settings(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await _render_daily_settings(cb)
    await cb.answer()


@router.callback_query(F.data == "daily_reminder_set_time")
async def daily_reminder_set_time(cb: CallbackQuery, state: FSMContext):
    await state.set_state(DailyReminder.waiting_for_time)
    await cb.message.edit_text(
        TIME_INPUT_PROMPT,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK, callback_data="daily_reminder_settings")]
        ])
    )
    await cb.answer()


@router.message(DailyReminder.waiting_for_time)
async def daily_reminder_time_msg(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(TIME_INPUT_PROMPT)
        return

    t = message.text.strip()
    norm = _parse_hhmm(t)
    if not norm:
        await message.answer(TIME_INPUT_BAD)
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET daily_reminder_time=?, daily_reminder_enabled=1 WHERE user_id=?",
            (norm, message.from_user.id)
        )
        await db.commit()

    await state.clear()
    await message.answer(DAILY_TIME_UPDATED, reply_markup=main_menu(message.from_user.id))


@router.callback_query(F.data == "daily_reminder_disable")
async def daily_reminder_disable(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET daily_reminder_enabled=0 WHERE user_id=?",
            (cb.from_user.id,)
        )
        await db.commit()
    await _render_daily_settings(cb)
    await cb.answer(CL_DISABLED_SHORT)


@router.callback_query(F.data == "daily_reminder_enable")
async def daily_reminder_enable(cb: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET daily_reminder_enabled=1 WHERE user_id=?",
            (cb.from_user.id,)
        )
        await db.commit()
    await _render_daily_settings(cb)
    await cb.answer(DAILY_ENABLED_SHORT)
