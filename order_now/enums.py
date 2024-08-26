from enum import StrEnum, auto


class UserAccessLevel(StrEnum):
    admin = auto()
    manager = auto()
    employee = auto()


class OrderItemStatus(StrEnum):
    preparing = auto()
    done = auto()
    served = auto()
