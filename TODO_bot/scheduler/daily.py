import aiosqlite
from config import DB_NAME


async def send_daily(bot):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users"
        )
        users = await cursor.fetchall()

    for (user_id,) in users:
        await send_daily_for_user(bot, user_id)


async def send_daily_for_user(bot, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT title FROM tasks WHERE user_id=? ORDER BY id",
            (user_id,)
        )
        tasks = await cursor.fetchall()

    if not tasks:
        text = "🎉 Сегодня дел нет"
    else:
        text = "📋 Дела на сегодня:\n\n"
        for i, (title,) in enumerate(tasks, start=1):
            text += f"{i}. {title}\n"

    await bot.send_message(user_id, text)
