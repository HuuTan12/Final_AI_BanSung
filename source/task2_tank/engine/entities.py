"""
Module: entities.py
Mô tả: Định nghĩa các thực thể trong game theo đặc tả đề bài:
- Tank: HP khởi tạo 6, Sát thương 1
- Base: HP khởi tạo 9, Sát thương 1
- Wall: HP khởi tạo 3, Sát thương 1
- Bullet: Tốc độ 3 ô / chu kỳ (cycle), kiểm tra va chạm từng ô
"""

from typing import Tuple
from task2_tank.engine.actions import Direction


class GameEntity:
    """Lớp cơ sở cho các thực thể có máu (HP) và vị trí trên lưới."""
    def __init__(self, x: int, y: int, hp: int):
        self.x = x
        self.y = y
        self.hp = hp

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, damage: int = 1) -> None:
        self.hp = max(0, self.hp - damage)


class Tank(GameEntity):
    """
    Thực thể Tank: Máu ban đầu = 6, Sát thương nhận = 1/hit.
    """
    INITIAL_HP = 6

    def __init__(self, x: int, y: int, player_id: int, direction: Direction = Direction.UP):
        super().__init__(x, y, self.INITIAL_HP)
        self.player_id = player_id
        self.direction = direction

    def clone(self) -> 'Tank':
        tank_copy = Tank(self.x, self.y, self.player_id, self.direction)
        tank_copy.hp = self.hp
        return tank_copy


class Base(GameEntity):
    """
    Thực thể Căn cứ (Base): Máu ban đầu = 9, Sát thương nhận = 1/hit.
    """
    INITIAL_HP = 9

    def __init__(self, x: int, y: int, player_id: int):
        super().__init__(x, y, self.INITIAL_HP)
        self.player_id = player_id

    def clone(self) -> 'Base':
        base_copy = Base(self.x, self.y, self.player_id)
        base_copy.hp = self.hp
        return base_copy


class Wall(GameEntity):
    """
    Thực thể Tường gạch: Máu ban đầu = 3, Sát thương nhận = 1/hit.
    Khi HP = 0, tường biến mất và ô trở thành ô trống.
    """
    INITIAL_HP = 3

    def __init__(self, x: int, y: int):
        super().__init__(x, y, self.INITIAL_HP)

    def clone(self) -> 'Wall':
        wall_copy = Wall(self.x, self.y)
        wall_copy.hp = self.hp
        return wall_copy


class Bullet:
    """
    Thực thể Đạn: Di chuyển tối đa 3 ô/chu kỳ theo hướng bắn.
    Dừng lại và biến mất ngay khi va chạm với vật thể (Wall, Tank, Base) hoặc vượt biên.
    """
    SPEED = 3

    def __init__(self, x: int, y: int, direction: Direction, owner_id: int):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner_id = owner_id
        self.is_active = True

    def clone(self) -> 'Bullet':
        bullet_copy = Bullet(self.x, self.y, self.direction, self.owner_id)
        bullet_copy.is_active = self.is_active
        return bullet_copy
