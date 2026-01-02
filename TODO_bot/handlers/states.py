from aiogram.fsm.state import StatesGroup, State

class AddTask(StatesGroup):
    waiting_for_text = State()
