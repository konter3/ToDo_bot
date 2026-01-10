# -*- coding: windows-1251 -*-
# database/db.py
import aiosqlite
from datetime import datetime
from config import DB_NAME
import logging

logger = logging.getLogger(__name__)

async def _ensure_column(db, table: str, column: str, col_type: str, default_sql: str | None = None):
    """Добавляет колонку в таблицу, если её нет. Без удаления данных."""
    cur = await db.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in await cur.fetchall()]
    if column in cols:
        return
    if default_sql is None:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    else:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default_sql}")


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            registered_at TEXT
        )
        """)

        # --- Мягкая миграция: настройки ежедневного напоминания ---
        await _ensure_column(db, "users", "daily_reminder_time", "TEXT", "'10:00'")
        await _ensure_column(db, "users", "daily_reminder_enabled", "INTEGER", "1")
        await _ensure_column(db, "users", "daily_last_sent_date", "TEXT")
        await db.execute("UPDATE users SET daily_reminder_time='10:00' WHERE daily_reminder_time IS NULL")
        await db.execute("UPDATE users SET daily_reminder_enabled=1 WHERE daily_reminder_enabled IS NULL")


        await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS completed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)

        # --- Чек-листы ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)

        # --- Мягкая миграция: настройки напоминаний чек-листов ---
        await _ensure_column(db, "checklists", "reminder_mode", "TEXT", "'off'")   # off | daily | once
        await _ensure_column(db, "checklists", "reminder_time", "TEXT")          # HH:MM для daily
        await _ensure_column(db, "checklists", "reminder_once_at", "TEXT")       # dd.mm.YYYY HH:MM для once
        await _ensure_column(db, "checklists", "reminder_enabled", "INTEGER", "0")
        await _ensure_column(db, "checklists", "last_sent_date", "TEXT")
        await _ensure_column(db, "checklists", "once_sent", "INTEGER", "0")


        await db.execute("""
            CREATE TABLE IF NOT EXISTS checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(checklist_id) REFERENCES checklists(id) ON DELETE CASCADE
        )
        """)


        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_completed_user ON completed(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_checklists_user ON checklists(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_checklist_items_list ON checklist_items(checklist_id)")

        await db.commit()


async def register_user(user):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, registered_at) VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name,
             datetime.now().strftime("%d.%m.%Y %H:%M"))
        )
        await db.commit()
