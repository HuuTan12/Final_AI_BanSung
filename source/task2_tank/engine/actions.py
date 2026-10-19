"""
actions.py - Tank Actions and Movement Directions
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Defines the 6 legal actions and 4 movement directions for
    the Tank Battle game (Task 2 - Adversarial Search).
"""

from enum import Enum
from typing import Optional


class Direction(Enum):
    """
    Four compass directions. The value is (dx, dy) where
    x increases to the right and y increases downward.
    """
    UP    = (0, -1)
    DOWN  = (0,  1)
    LEFT  = (-1, 0)
    RIGHT = (1,  0)


class Action(Enum):
    """
    Six legal actions a tank can perform each turn, as required by the spec:
    MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, FIRE, STAY.
    """
    MOVE_UP    = "MOVE_UP"
    MOVE_DOWN  = "MOVE_DOWN"
    MOVE_LEFT  = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    FIRE       = "FIRE"
    STAY       = "STAY"

    @classmethod
    def get_move_direction(cls, action: "Action") -> Optional[Direction]:
        """
        Maps a movement action to its corresponding Direction.
        Returns None for FIRE and STAY.
        """
        mapping = {
            cls.MOVE_UP:    Direction.UP,
            cls.MOVE_DOWN:  Direction.DOWN,
            cls.MOVE_LEFT:  Direction.LEFT,
            cls.MOVE_RIGHT: Direction.RIGHT,
        }
        return mapping.get(action, None)
