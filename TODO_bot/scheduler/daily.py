import aiosqlite
from config import DB_NAME

async def send_daily(bot, user_id):
    tasks = await get_tasks(user_id)

    if not tasks:
        await bot.send_message(user_id, "🎉 Сегодня дел нет")
        return

    text = "📋 Дела на сегодня:\n\n"
    for i, task in enumerate(tasks, 1):
        text += f"{i}. {task}\n"

    await bot.send_message(user_id, text)
