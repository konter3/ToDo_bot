# utils/safe_edit.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

async def safe_edit(cb: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup = None):
    """Редактирует сообщение только если есть изменения, чтобы не было ошибки Telegram."""
    try:
        # Telegram кидает ошибку, если текст и клавиатура не изменились
        await cb.message.edit_text(text, reply_markup=reply_markup)
    except Exception as e:
        # Игнорируем ошибку "message is not modified"
        if "message is not modified" in str(e):
            return
        raise
