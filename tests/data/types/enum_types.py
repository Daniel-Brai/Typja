from enum import Enum, IntEnum


class Status(str, Enum):

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class Priority(IntEnum):

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Color(Enum):

    RED = "red"
    GREEN = "green"
    BLUE = "blue"
