# handlers/checklist.py
import aiosqlite
from config import DB_NAME

async def render_checklists(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, title FROM checklists WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        )
        return await cursor.fetchall()
