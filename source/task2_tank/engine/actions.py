"""
Module: actions.py
Mô tả: Định nghĩa các hướng di chuyển và 06 hành động hợp lệ của Tank theo yêu cầu đề bài.
"""

from enum import Enum
from typing import Tuple


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class Action(Enum):
    """
    06 hành động của một thực thể Tank theo yêu cầu đặc tả đề bài:
    MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, FIRE, STAY.
    """
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    FIRE = "FIRE"
    STAY = "STAY"

    @classmethod
    def get_move_direction(cls, action: 'Action') -> Direction:
        """
        Chuyển đổi hành động di chuyển thành hướng tương ứng.
        """
        mapping = {
            cls.MOVE_UP: Direction.UP,
            cls.MOVE_DOWN: Direction.DOWN,
            cls.MOVE_LEFT: Direction.LEFT,
            cls.MOVE_RIGHT: Direction.RIGHT,
        }
        return mapping.get(action, None)
