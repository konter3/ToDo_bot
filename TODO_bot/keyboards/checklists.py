# keyboards/checklists.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import BTN_CANCEL

def cancel_checklist_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=BTN_CANCEL,
                callback_data="cancel_checklist"
            )]
        ]
    )