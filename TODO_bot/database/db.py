# database/db.py
import aiosqlite
from datetime import datetime
from config import DB_NAME
import logging

logger = logging.getLogger(__name__)

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
            "INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name,
             datetime.now().strftime("%d.%m.%Y %H:%M"))
        )
        await db.commit()
