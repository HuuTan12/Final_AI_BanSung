from enum import Enum
from typing import Optional


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class Action(Enum):
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    FIRE = "FIRE"
    STAY = "STAY"

    @classmethod
    def get_move_direction(cls, action: "Action") -> Optional[Direction]:
        mapping = {
            cls.MOVE_UP: Direction.UP,
            cls.MOVE_DOWN: Direction.DOWN,
            cls.MOVE_LEFT: Direction.LEFT,
            cls.MOVE_RIGHT: Direction.RIGHT,
        }
        return mapping.get(action, None)