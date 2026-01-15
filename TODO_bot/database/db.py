# database/db.py
from __future__ import annotations

import logging
from datetime import datetime

import aiosqlite

from config import DB_NAME

logger = logging.getLogger(__name__)


async def _ensure_column(
    db,
    table: str,
    column: str,
    col_type: str,
    default_sql: str | None = None,
):
    """Add a column to an existing table if it doesn't exist (data-safe migration).

    We use ALTER TABLE, so existing user data is preserved.
    """
    cur = await db.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in await cur.fetchall()]
    if column in cols:
        return

    if default_sql is None:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    else:
        await db.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default_sql}"
        )


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            registered_at TEXT
        )
        """
        )

        # Data-safe migration: daily reminder settings
        await _ensure_column(db, "users", "daily_reminder_time", "TEXT", "'10:00'")
        await _ensure_column(db, "users", "daily_reminder_enabled", "INTEGER", "1")
        await _ensure_column(db, "users", "daily_last_sent_date", "TEXT")
        await db.execute(
            "UPDATE users SET daily_reminder_time='10:00' WHERE daily_reminder_time IS NULL"
        )
        await db.execute(
            "UPDATE users SET daily_reminder_enabled=1 WHERE daily_reminder_enabled IS NULL"
        )

        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """
        )

        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS completed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """
        )

        # Checklists
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """
        )

        # Data-safe migration: checklist reminders
        await _ensure_column(db, "checklists", "reminder_mode", "TEXT", "'off'")  # off|daily|once
        await _ensure_column(db, "checklists", "reminder_time", "TEXT")  # HH:MM for daily
        await _ensure_column(db, "checklists", "reminder_once_at", "TEXT")  # dd.mm.YYYY HH:MM for once
        await _ensure_column(db, "checklists", "reminder_enabled", "INTEGER", "0")
        # 0..6 (Mon..Sun) or NULL for every day (backward compatible)
        await _ensure_column(db, "checklists", "reminder_weekday", "INTEGER")
        # Bitmask of weekdays for multi-select (1<<0 is Mon ... 1<<6 is Sun). NULL means "every day" (compat).
        await _ensure_column(db, "checklists", "reminder_weekdays_mask", "INTEGER")
        await _ensure_column(db, "checklists", "last_sent_date", "TEXT")
        await _ensure_column(db, "checklists", "once_sent", "INTEGER", "0")

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
        )
        """
        )

        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_completed_user ON completed(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_checklists_user ON checklists(user_id)")
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_checklist_items_list ON checklist_items(checklist_id)"
        )

        await db.commit()


async def register_user(user):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, registered_at) VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name, datetime.now().strftime("%d.%m.%Y %H:%M")),
        )
        await db.commit()
