import asyncio
import logging
import aiosqlite
from aiogram import Bot
from config import DB_NAME

logger = logging.getLogger(__name__)

BATCH_SIZE = 30          # сколько сообщений за раз
PAUSE_BETWEEN_BATCH = 5 # пауза между батчами (сек)

# ---------- текст дня ----------
async def build_daily_text(db, user_id: int) -> str:
    cursor = await db.execute(
        "SELECT title FROM tasks WHERE user_id=? ORDER BY id",
        (user_id,)
    )
    tasks = await cursor.fetchall()

    if not tasks:
        return "🎉 Сегодня дел нет"

    text = "📋 Дела на сегодня:\n\n"
    for i, (title,) in enumerate(tasks, start=1):
        text += f"{i}. {title}\n"

    return text


# ---------- отправка батча ----------
async def send_batch(bot: Bot, db, user_ids: list[int]):
    tasks = []

    for user_id in user_ids:
        text = await build_daily_text(db, user_id)
        tasks.append(bot.send_message(user_id, text))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = 0
    failed = 0

    for r in results:
        if isinstance(r, Exception):
            failed += 1
            logger.warning(f"❌ Send failed: {r}")
        else:
            success += 1

    logger.info(f"📦 Batch done: ✅ {success} | ❌ {failed}")


# ---------- основная задача ----------
async def send_daily(bot: Bot):
    logger.info("⏰ Daily sending started")

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()

        user_ids = [uid for (uid,) in rows]

        logger.info(f"👥 Users total: {len(user_ids)}")

        for i in range(0, len(user_ids), BATCH_SIZE):
            batch = user_ids[i:i + BATCH_SIZE]

            logger.info(
                f"🚀 Sending batch {i // BATCH_SIZE + 1} "
                f"({len(batch)} users)"
            )

            await send_batch(bot, db, batch)
            await asyncio.sleep(PAUSE_BETWEEN_BATCH)

    logger.info("✅ Daily sending finished")
