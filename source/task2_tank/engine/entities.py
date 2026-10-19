"""
entities.py - Game Entities: Tank, Base, Wall, Bullet
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Defines all game entities with exact HP values specified in the problem:
    - Tank  : Initial HP = 6, damage per hit = 1
    - Base  : Initial HP = 9, damage per hit = 1
    - Wall  : Initial HP = 3, damage per hit = 1
    - Bullet: Speed = 3 cells per game cycle, cell-by-cell collision check
"""

from task2_tank.engine.actions import Direction


class GameEntity:
    """
    Abstract base class for any entity that occupies a cell and has hit points.
    """

    def __init__(self, x: int, y: int, hp: int):
        self.x = x
        self.y = y
        self.hp = hp

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, damage: int = 1) -> None:
        """Reduces HP by damage, clamped to 0."""
        self.hp = max(0, self.hp - damage)


class Tank(GameEntity):
    """
    Player tank entity.
    - Initial HP = 6 (as required by the problem spec)
    - Stores current facing direction for firing logic
    """
    INITIAL_HP = 6

    def __init__(self, x: int, y: int, player_id: int,
                 direction: Direction = Direction.UP):
        super().__init__(x, y, self.INITIAL_HP)
        self.player_id = player_id
        self.direction = direction

    def clone(self) -> "Tank":
        """Creates an independent deep copy for search tree expansion."""
        copy = Tank(self.x, self.y, self.player_id, self.direction)
        copy.hp = self.hp
        return copy


class Base(GameEntity):
    """
    Player base / headquarters entity.
    - Initial HP = 9 (as required by the problem spec)
    - Destroying the enemy base wins the game
    """
    INITIAL_HP = 9

    def __init__(self, x: int, y: int, player_id: int):
        super().__init__(x, y, self.INITIAL_HP)
        self.player_id = player_id

    def clone(self) -> "Base":
        copy = Base(self.x, self.y, self.player_id)
        copy.hp = self.hp
        return copy


class Wall(GameEntity):
    """
    Destructible wall / obstacle.
    - Initial HP = 3 (as required by the problem spec)
    - When HP reaches 0 the wall disappears, clearing the cell
    """
    INITIAL_HP = 3

    def __init__(self, x: int, y: int):
        super().__init__(x, y, self.INITIAL_HP)

    def clone(self) -> "Wall":
        copy = Wall(self.x, self.y)
        copy.hp = self.hp
        return copy


class Bullet:
    """
    Projectile fired by a tank.
    - Speed = 3 cells per game cycle (as required by the problem spec)
    - Collision is checked after EACH cell moved (cell-by-cell), not jump 3 at once
    - Bullet is destroyed immediately upon hitting any entity or crossing the border
    """
    SPEED = 3  # maximum cells traveled per cycle

    def __init__(self, x: int, y: int, direction: Direction, owner_id: int):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner_id = owner_id
        self.is_active = True

    def clone(self) -> "Bullet":
        copy = Bullet(self.x, self.y, self.direction, self.owner_id)
        copy.is_active = self.is_active
        return copy
