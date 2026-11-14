from task2_tank.engine.actions import Direction

class GameEntity:

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
    INITIAL_HP = 6

    def __init__(self, x: int, y: int, player_id: int, direction: Direction=Direction.UP):
        super().__init__(x, y, self.INITIAL_HP)
        self.player_id = player_id
        self.direction = direction

    def clone(self) -> 'Tank':
        copy = Tank(self.x, self.y, self.player_id, self.direction)
        copy.hp = self.hp
        return copy

class Base(GameEntity):
    INITIAL_HP = 9

    def __init__(self, x: int, y: int, player_id: int):
        super().__init__(x, y, self.INITIAL_HP)
        self.player_id = player_id

    def clone(self) -> 'Base':
        copy = Base(self.x, self.y, self.player_id)
        copy.hp = self.hp
        return copy

class Wall(GameEntity):
    INITIAL_HP = 3

    def __init__(self, x: int, y: int, hp: int = INITIAL_HP):
        super().__init__(x, y, hp)
        self.max_hp = hp

    def clone(self) -> 'Wall':
        copy = Wall(self.x, self.y, self.hp)
        copy.max_hp = self.max_hp
        return copy

class Bullet:
    SPEED = 3

    def __init__(self, x: int, y: int, direction: Direction, owner_id: int):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner_id = owner_id
        self.is_active = True

    def clone(self) -> 'Bullet':
        copy = Bullet(self.x, self.y, self.direction, self.owner_id)
        copy.is_active = self.is_active
        return copy