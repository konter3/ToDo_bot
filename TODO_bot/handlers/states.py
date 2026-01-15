from aiogram.fsm.state import StatesGroup, State

class AddTask(StatesGroup):
    waiting_for_text = State()


class DailyReminder(StatesGroup):
    waiting_for_time = State()

class ChecklistReminder(StatesGroup):
    waiting_for_time = State()
    waiting_for_days = State()


class ChecklistEdit(StatesGroup):
    waiting_for_items = State()
