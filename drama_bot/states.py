"""FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class UserSG(StatesGroup):
    by_code = State()
    by_name = State()


class AddDrama(StatesGroup):
    title = State()
    year = State()
    genre = State()
    description = State()
    poster = State()


class AddEp(StatesGroup):
    code = State()
    upload = State()


class DelDrama(StatesGroup):
    code = State()


class DelEp(StatesGroup):
    code = State()
    number = State()


class EditDrama(StatesGroup):
    code = State()
    field = State()
    value = State()


class PostSG(StatesGroup):
    query = State()
    confirm = State()
    edit = State()


class ChannelSG(StatesGroup):
    add = State()


class AdminSG(StatesGroup):
    add = State()
