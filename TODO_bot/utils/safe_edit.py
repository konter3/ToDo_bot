# utils/safe_edit.py
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

async def safe_edit(cb: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup = None):
    """Редактирует сообщение только если есть изменения"""
    try:
        current_text = cb.message.text or ""
        current_markup = cb.message.reply_markup

        if text == current_text and reply_markup == current_markup:
            return  # не трогаем сообщение, чтобы Telegram не ругался

        await cb.message.edit_text(text, reply_markup=reply_markup)
    except Exception as e:
        if "message is not modified" in str(e):
            return
        raise
