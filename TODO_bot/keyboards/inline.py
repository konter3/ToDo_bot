from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID

def main_menu(user_id: int):
    keyboard = [
        [InlineKeyboardButton(text="📋 Текущие дела", callback_data="show_tasks")],
        [InlineKeyboardButton(text="➕ Добавить дело", callback_data="add_task")],
        [InlineKeyboardButton(text="✅ Выполненные дела", callback_data="done_tasks")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton(text="👑 Пользователи", callback_data="users")]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ В меню", callback_data="menu")]]
    )

## кнопка отмены
def cancel_task():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_task")]
        ]
    )