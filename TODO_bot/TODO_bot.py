import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from logging_config import setup_logging
from database.db import init_db

from handlers import cancel, complete_task, start, tasks, completed, admin, menu
from scheduler.daily import send_daily

setup_logging()
logger = logging.getLogger(__name__)


async def main():
    logger.info("Bot starting")

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    try:
        await init_db()
        dp.include_router(cancel.router)
        dp.include_router(start.router)
        dp.include_router(tasks.router)
        dp.include_router(completed.router)
        dp.include_router(complete_task.router)
        dp.include_router(admin.router)
        dp.include_router(menu.router)

        scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

        scheduler.add_job(
            send_daily,
            trigger="cron",
            hour=10,
            minute=0,
            args=[bot],
            id="daily_tasks",
            replace_existing=True
        )

        scheduler.start()
        await dp.start_polling(bot)

    finally:
        await bot.session.close()



if __name__ == "__main__":
    asyncio.run(main())
