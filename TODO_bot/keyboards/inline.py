# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID

from texts import (
    BTN_ADD_TASK,
    BTN_CANCEL,
    BTN_CHECKLISTS,
    BTN_DAILY_REMINDER,
    BTN_DONE_TASKS,
    BTN_MENU,
    BTN_TASKS,
    BTN_USERS,
)

def main_menu(user_id: int):
    keyboard = [
        [InlineKeyboardButton(text=BTN_TASKS, callback_data="show_tasks")],
        [InlineKeyboardButton(text=BTN_ADD_TASK, callback_data="add_task")],
        [InlineKeyboardButton(text=BTN_DONE_TASKS, callback_data="done_tasks")],
        [InlineKeyboardButton(text=BTN_DAILY_REMINDER, callback_data="daily_reminder_settings")],
        [InlineKeyboardButton(text=BTN_CHECKLISTS, callback_data="checklists")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton(text=BTN_USERS, callback_data="users")]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_MENU, callback_data="menu")]]
    )

## кнопка отмены
def cancel_task():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_add_task")]
        ]
    )