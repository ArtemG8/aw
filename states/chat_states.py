from aiogram.fsm.state import State, StatesGroup


class ChatFSM(StatesGroup):
    waiting_message = State()
