from aiogram.fsm.state import State, StatesGroup


class User(StatesGroup):
    menu = State()
    seat = State()
    payment = State()
    wait_photo = State()