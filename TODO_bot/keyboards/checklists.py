# keyboards/checklists.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def cancel_checklist_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_checklist"
            )]
        ]
    )