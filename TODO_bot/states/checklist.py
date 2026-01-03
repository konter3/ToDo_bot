# states/checklist.py
from aiogram.fsm.state import State, StatesGroup

class ChecklistFSM(StatesGroup):
    title = State()
    items = State()
