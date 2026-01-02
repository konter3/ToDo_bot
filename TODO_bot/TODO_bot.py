
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiosqlite

from config import BOT_TOKEN, DB_NAME
from logging_config import setup_logging
from database.db import init_db
from handlers import start, tasks, completed, admin, menu
from scheduler.daily import send_daily

setup_logging()
logger = logging.getLogger(__name__)

async def main():
    logger.info("Bot starting")
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    await init_db()

    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(completed.router)
    dp.include_router(admin.router)
    dp.include_router(menu.router)

    scheduler = AsyncIOScheduler()

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        users = await cursor.fetchall()

    for (user_id,) in users:
        scheduler.add_job(send_daily, "cron", hour=10, minute=0, args=[bot, user_id])

    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
