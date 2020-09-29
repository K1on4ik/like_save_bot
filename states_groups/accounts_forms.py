from aiogram.dispatcher.filters.state import State, StatesGroup

class AddAccountForm(StatesGroup):
    login = State()
    password = State()
    proxy = State()
    confirm = State()

class AddTaskForm(StatesGroup):
    account = State()
    save = State()
    time = State()
