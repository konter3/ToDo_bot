import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import aiosqlite
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import DB_NAME

logger = logging.getLogger(__name__)

BATCH_SIZE = 30          # сколько сообщений за раз
PAUSE_BETWEEN_BATCH = 5  # пауза между батчами (сек)


def _now_moscow() -> datetime:
    return datetime.now(ZoneInfo("Europe/Moscow"))


# ---------- текст дня (дела) ----------
async def build_daily_text(db, user_id: int) -> str:
    cursor = await db.execute(
        "SELECT title FROM tasks WHERE user_id=? ORDER BY id",
        (user_id,)
    )
    rows = await cursor.fetchall()

    if not rows:
        return "📝 На сегодня дел нет."

    text = "📝 Ваши дела на сегодня:\n\n"
    for i, (title,) in enumerate(rows, 1):
        text += f"{i}. {title}\n"
    return text


# ---------- текст чек-листа ----------
async def build_checklist_text(db, checklist_id: int) -> str:
    cur = await db.execute("SELECT title FROM checklists WHERE id=?", (checklist_id,))
    row = await cur.fetchone()
    if not row:
        return None
    (cl_title,) = row

    cur = await db.execute(
        "SELECT title, completed FROM checklist_items WHERE checklist_id=? ORDER BY id",
        (checklist_id,)
    )
    items = await cur.fetchall()

    lines = [f"🗂 Чек-лист: {cl_title}", ""]
    if not items:
        lines.append("(пусто)")
    else:
        for i, (title, completed) in enumerate(items, 1):
            mark = "✅ " if completed else "▫️ "
            lines.append(f"{mark}{i}. {title}")

    return "\n".join(lines)


async def _send_batch(bot: Bot, db, user_ids: list[int], today: str):
    for user_id in user_ids:
        try:
            text = await build_daily_text(db, user_id)
            await bot.send_message(user_id, text)

            await db.execute(
                "UPDATE users SET daily_last_sent_date=? WHERE user_id=?",
                (today, user_id)
            )
        except Exception as e:
            logger.warning(f"Failed to send daily tasks to {user_id}: {e}")


async def _send_checklist(bot: Bot, db, checklist_id: int, user_id: int, today: str, is_once: bool):
    try:
        text = await build_checklist_text(db, checklist_id)
        if not text:
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть чек-лист", callback_data=f"checklist:{checklist_id}")]
            ]
        )
        await bot.send_message(user_id, text, reply_markup=kb)

        if is_once:
            await db.execute(
                "UPDATE checklists SET once_sent=1 WHERE id=?",
                (checklist_id,)
            )
        else:
            await db.execute(
                "UPDATE checklists SET last_sent_date=? WHERE id=?",
                (today, checklist_id)
            )
    except Exception as e:
        logger.warning(f"Failed to send checklist {checklist_id} to {user_id}: {e}")


# ---------- главный тикер (каждую минуту) ----------
async def send_due(bot: Bot):
    """Вызывается планировщиком каждую минуту. Шлёт только тем, кому «пора»."""
    now = _now_moscow()
    hhmm = now.strftime("%H:%M")
    today = now.strftime("%d.%m.%Y")
    now_str = now.strftime("%d.%m.%Y %H:%M")

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        # --- ежедневные дела ---
        cur = await db.execute(
            """SELECT user_id
               FROM users
               WHERE daily_reminder_enabled=1
                 AND COALESCE(daily_reminder_time,'10:00')=?
                 AND (daily_last_sent_date IS NULL OR daily_last_sent_date<>?)""",
            (hhmm, today)
        )
        rows = await cur.fetchall()
        user_ids = [uid for (uid,) in rows]

        if user_ids:
            logger.info(f"⏰ Due daily tasks at {hhmm}: {len(user_ids)} users")

            for i in range(0, len(user_ids), BATCH_SIZE):
                batch = user_ids[i:i + BATCH_SIZE]
                await _send_batch(bot, db, batch, today)
                await db.commit()
                await asyncio.sleep(PAUSE_BETWEEN_BATCH)

        # --- чек-листы: daily ---
        cur = await db.execute(
            """SELECT id, user_id
               FROM checklists
               WHERE reminder_enabled=1
                 AND reminder_mode='daily'
                 AND reminder_time=?
                 AND (last_sent_date IS NULL OR last_sent_date<>?)""",
            (hhmm, today)
        )
        daily_lists = await cur.fetchall()

        for checklist_id, user_id in daily_lists:
            await _send_checklist(bot, db, checklist_id, user_id, today, is_once=False)

        # --- чек-листы: once ---
        cur = await db.execute(
            """SELECT id, user_id
               FROM checklists
               WHERE reminder_enabled=1
                 AND reminder_mode='once'
                 AND once_sent=0
                 AND reminder_once_at=?""",
            (now_str,)
        )
        once_lists = await cur.fetchall()

        for checklist_id, user_id in once_lists:
            await _send_checklist(bot, db, checklist_id, user_id, today, is_once=True)

        await db.commit()
