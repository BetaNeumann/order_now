from enum import Enum, auto


class UserAccessLevel(Enum):
    admin = auto()
    manager = auto()
    employee = auto()
