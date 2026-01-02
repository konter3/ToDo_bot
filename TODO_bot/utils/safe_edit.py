from aiogram.types import InlineKeyboardMarkup

async def safe_edit(cb, text: str, reply_markup: InlineKeyboardMarkup):
    current_text = cb.message.text
    current_markup = cb.message.reply_markup

    # Проверяем текст и клавиатуру
    if current_text != text or current_markup != reply_markup:
        await cb.message.edit_text(text, reply_markup=reply_markup)
    else:
        # Можно просто ответить на нажатие без редактирования
        await cb.answer("✅ Задачи уже показаны", show_alert=False)
