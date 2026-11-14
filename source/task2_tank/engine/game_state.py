from typing import List, Dict, Tuple, Optional
from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Tank, Base, Wall, Bullet


class GameState:

    def __init__(self, width: int = 13, height: int = 13):
        self.width = width
        self.height = height

        self.tanks: Dict[int, Tank] = {}
        self.bases: Dict[int, Base] = {}
        self.walls: Dict[Tuple[int, int], Wall] = {}
        self.bullets: List[Bullet] = []
        self.foliage: set = set()

        self.current_player: int = 0
        self.game_cycle: int = 0
        self.max_cycles: int = 200

    def clone(self) -> 'GameState':
        new_state = GameState(self.width, self.height)

        new_state.current_player = self.current_player
        new_state.game_cycle = self.game_cycle
        new_state.max_cycles = self.max_cycles
        new_state.foliage = self.foliage

        for player_id in self.tanks:
            old_tank = self.tanks[player_id]
            new_tank = old_tank.clone()
            new_state.tanks[player_id] = new_tank

        for player_id in self.bases:
            old_base = self.bases[player_id]
            new_base = old_base.clone()
            new_state.bases[player_id] = new_base

        for position in self.walls:
            old_wall = self.walls[position]
            new_wall = old_wall.clone()
            new_state.walls[position] = new_wall

        for old_bullet in self.bullets:
            new_bullet = old_bullet.clone()
            new_state.bullets.append(new_bullet)

        return new_state

    def get_legal_actions(self, player_id: int) -> List[Action]:
        if player_id not in self.tanks:
            return [Action.STAY]

        tank = self.tanks[player_id]

        if not tank.is_alive:
            return [Action.STAY]

        legal_actions = []

        move_actions = [Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT]
        opponent_id = 1 - player_id

        for action in move_actions:
            direction = Action.get_move_direction(action)
            dx, dy = direction.value

            new_x = tank.x + dx
            new_y = tank.y + dy

            if new_x < 0 or new_x >= self.width:
                continue
            if new_y < 0 or new_y >= self.height:
                continue

            new_position = (new_x, new_y)
            is_blocked = False

            if new_position in self.walls and self.walls[new_position].is_alive:
                is_blocked = True
            else:
                blocked_by_base = False

                for base in self.bases.values():
                    if base.x == new_x and base.y == new_y and base.is_alive:
                        blocked_by_base = True

                if blocked_by_base:
                    is_blocked = True
                else:
                    if opponent_id in self.tanks:
                        opponent_tank = self.tanks[opponent_id]

                        if opponent_tank.is_alive and opponent_tank.x == new_x and opponent_tank.y == new_y:
                            is_blocked = True

            if is_blocked and tank.direction == direction:
                continue

            legal_actions.append(action)

        legal_actions.append(Action.FIRE)
        legal_actions.append(Action.STAY)

        return legal_actions

    def is_terminal(self) -> bool:
        for base in self.bases.values():
            if not base.is_alive:
                return True

        for tank in self.tanks.values():
            if not tank.is_alive:
                return True

        if self.game_cycle >= self.max_cycles:
            return True

        return False

    def get_winner(self) -> Optional[int]:
        if not self.is_terminal():
            return None

        player1_base_dead = 1 in self.bases and not self.bases[1].is_alive
        player1_tank_dead = 1 in self.tanks and not self.tanks[1].is_alive
        player0_base_dead = 0 in self.bases and not self.bases[0].is_alive
        player0_tank_dead = 0 in self.tanks and not self.tanks[0].is_alive

        player0_lost = player0_base_dead or player0_tank_dead
        player1_lost = player1_base_dead or player1_tank_dead

        if player0_lost and player1_lost:
            return -1

        if player0_lost:
            return 1

        if player1_lost:
            return 0

        if self.game_cycle >= self.max_cycles:
            return -1

        return -1

    def get_utility(self, player_id: int) -> float:
        if self.is_terminal():
            winner = self.get_winner()
            opponent_id = 1 - player_id

            if winner == player_id:
                return 10000.0
            elif winner == opponent_id:
                return -10000.0
            else:
                return 0.0

        return 0.0

    def is_cell_blocked(self, x: int, y: int) -> bool:
        if x < 0 or x >= self.width:
            return True
        if y < 0 or y >= self.height:
            return True

        position = (x, y)

        if position in self.walls and self.walls[position].is_alive:
            return True

        for base in self.bases.values():
            if base.x == x and base.y == y and base.is_alive:
                return True

        for tank in self.tanks.values():
            if tank.x == x and tank.y == y and tank.is_alive:
                return True

        return False