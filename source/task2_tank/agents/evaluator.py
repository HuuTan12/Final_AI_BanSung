from collections import deque
from typing import Tuple, Dict, Optional
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Direction

class TankEvaluator:
    _dist_cache: Dict[Tuple, Dict[Tuple[int, int], int]] = {}

    @classmethod
    def clear_cache(cls) -> None:
        cls._dist_cache.clear()

    def __init__(self, w_base_hp: float=120.0, w_tank_hp: float=50.0, w_dist_base: float=5.0, w_dist_tank: float=2.0, w_line_of_fire: float=30.0, w_bullet_danger: float=70.0):
        self.w_base_hp = w_base_hp
        self.w_tank_hp = w_tank_hp
        self.w_dist_base = w_dist_base
        self.w_dist_tank = w_dist_tank
        self.w_line_of_fire = w_line_of_fire
        self.w_bullet_danger = w_bullet_danger

    @classmethod
    def get_tactical_distance(cls, state: GameState, sx: int, sy: int, tx: int, ty: int) -> int:
        if sx == tx and sy == ty:
            return 0
        wall_sig = tuple(sorted(((pos, w.hp) for pos, w in state.walls.items() if w.is_alive)))
        cache_key = (state.width, state.height, tx, ty, wall_sig)
        dist_grid = cls._dist_cache.get(cache_key)
        if dist_grid is None:
            if len(cls._dist_cache) > 512:
                cls._dist_cache.clear()
            dist_grid = cls._compute_distance_field(state, tx, ty)
            cls._dist_cache[cache_key] = dist_grid
        return dist_grid.get((sx, sy), abs(sx - tx) + abs(sy - ty))

    @staticmethod
    def _compute_distance_field(state: GameState, tx: int, ty: int) -> Dict[Tuple[int, int], int]:
        w, h = (state.width, state.height)
        dist: Dict[Tuple[int, int], int] = {(tx, ty): 0}
        blocked_bases = {(b.x, b.y) for b in state.bases.values() if b.is_alive and (b.x != tx or b.y != ty)}
        max_possible = (w + h) * 4
        buckets: Dict[int, deque] = {0: deque([(tx, ty)])}
        curr_d = 0
        while buckets:
            while curr_d not in buckets and curr_d <= max_possible:
                curr_d += 1
            if curr_d > max_possible:
                break
            q = buckets[curr_d]
            cx, cy = q.popleft()
            if not q:
                del buckets[curr_d]
            if curr_d > dist.get((cx, cy), max_possible):
                continue
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = (cx + dx, cy + dy)
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                if (nx, ny) in blocked_bases:
                    continue
                wall = state.walls.get((nx, ny))
                step_cost = 1 + wall.hp if wall is not None and wall.is_alive else 1
                nd = curr_d + step_cost
                if nd < dist.get((nx, ny), max_possible):
                    dist[nx, ny] = nd
                    if nd not in buckets:
                        buckets[nd] = deque()
                    buckets[nd].append((nx, ny))
        return dist

    def _side_score(self, state: GameState, pid: int) -> float:
        opp_id = 1 - pid
        score = 0.0
        my_tank = state.tanks.get(pid)
        opp_tank = state.tanks.get(opp_id)
        my_base = state.bases.get(pid)
        opp_base = state.bases.get(opp_id)
        my_base_hp = my_base.hp if my_base and my_base.is_alive else 0
        my_tank_hp = my_tank.hp if my_tank and my_tank.is_alive else 0
        opp_tank_hp = opp_tank.hp if opp_tank and opp_tank.is_alive else 0
        score += self.w_base_hp * my_base_hp
        score += self.w_tank_hp * my_tank_hp
        if my_tank and my_tank.is_alive and opp_base and opp_base.is_alive:
            dist_to_opp_base = self.get_tactical_distance(state, my_tank.x, my_tank.y, opp_base.x, opp_base.y)
            score -= self.w_dist_base * dist_to_opp_base
        if my_tank and my_tank.is_alive and opp_tank and opp_tank.is_alive and (my_tank_hp > opp_tank_hp):
            tank_dist = abs(my_tank.x - opp_tank.x) + abs(my_tank.y - opp_tank.y)
            score -= self.w_dist_tank * 0.25 * (my_tank_hp - opp_tank_hp) * tank_dist
        if my_tank and my_tank.is_alive:
            if self._has_line_of_sight(state, my_tank.x, my_tank.y, my_tank.direction, opp_base):
                score += self.w_line_of_fire * 2.0
            if opp_tank and opp_tank.is_alive and self._has_line_of_sight(state, my_tank.x, my_tank.y, my_tank.direction, opp_tank):
                score += self.w_line_of_fire
        for bullet in state.bullets:
            if bullet.is_active and bullet.owner_id == opp_id:
                if my_tank and my_tank.is_alive and self._is_bullet_approaching(bullet, my_tank.x, my_tank.y, state):
                    score -= self.w_bullet_danger
                if my_base and my_base.is_alive and self._is_bullet_approaching(bullet, my_base.x, my_base.y, state):
                    score -= self.w_bullet_danger * 0.8
        return score

    def evaluate(self, state: GameState, player_id: int) -> float:
        if state.is_terminal():
            return state.get_utility(player_id)
        return self._side_score(state, player_id) - self._side_score(state, 1 - player_id)

    def _has_line_of_sight(self, state: GameState, x: int, y: int, direction: Direction, target) -> bool:
        if not target or not target.is_alive:
            return False
        dx, dy = direction.value
        cx, cy = (x + dx, y + dy)
        max_steps = max(state.width, state.height)
        for _ in range(max_steps):
            if not (0 <= cx < state.width and 0 <= cy < state.height):
                break
            if cx == target.x and cy == target.y:
                return True
            if (cx, cy) in state.walls and state.walls[cx, cy].is_alive:
                break
            if any((b.is_alive and b.x == cx and (b.y == cy) for b in state.bases.values())):
                break
            if any((t.is_alive and t.x == cx and (t.y == cy) for t in state.tanks.values())):
                break
            cx += dx
            cy += dy
        return False

    def _is_bullet_approaching(self, bullet, target_x: int, target_y: int, state: Optional[GameState]=None) -> bool:
        dx, dy = bullet.direction.value
        bx, by = (bullet.x, bullet.y)
        for step in range(1, 4):
            cx = bx + dx * step
            cy = by + dy * step
            if cx == target_x and cy == target_y:
                return True
            if state is not None:
                if not (0 <= cx < state.width and 0 <= cy < state.height):
                    break
                if (cx, cy) in state.walls and state.walls[cx, cy].is_alive:
                    break
                if any((b.is_alive and b.x == cx and (b.y == cy) for b in state.bases.values())):
                    break
        return False

    @staticmethod
    def action_tactical_priority(state: GameState, action, player_id: int) -> float:
        from task2_tank.engine.actions import Action
        if action == Action.STAY:
            return 0.0
        tank = state.tanks.get(player_id)
        if not tank or not tank.is_alive:
            return 0.0
        opp_base = state.bases.get(1 - player_id)
        opp_tank = state.tanks.get(1 - player_id)
        if action == Action.FIRE:
            my_base = state.bases.get(player_id)
            dx, dy = tank.direction.value
            fx, fy = (tank.x + dx, tank.y + dy)
            max_range = max(state.width, state.height)
            cx, cy = (fx, fy)
            first_hit = None
            for _ in range(max_range):
                if not (0 <= cx < state.width and 0 <= cy < state.height):
                    break
                if opp_base and opp_base.is_alive and (cx == opp_base.x) and (cy == opp_base.y):
                    first_hit = 'base'
                    break
                if opp_tank and opp_tank.is_alive and (cx == opp_tank.x) and (cy == opp_tank.y):
                    first_hit = 'tank'
                    break
                if my_base and my_base.is_alive and (cx == my_base.x) and (cy == my_base.y):
                    first_hit = 'own_base'
                    break
                if (cx, cy) in state.walls and state.walls[cx, cy].is_alive:
                    first_hit = ('wall', cx, cy)
                    break
                cx += dx
                cy += dy
            if first_hit == 'base':
                return 120.0
            if first_hit == 'tank':
                return 100.0
            if first_hit == 'own_base':
                return 1.0
            if first_hit and first_hit[0] == 'wall':
                wx, wy = (first_hit[1], first_hit[2])
                wall_dist = abs(wx - tank.x) + abs(wy - tank.y)
                wall_obj = state.walls.get((wx, wy))
                w_hp = wall_obj.hp if wall_obj else 3
                if wall_dist <= 3:
                    if opp_base and opp_base.is_alive:
                        curr_dist = TankEvaluator.get_tactical_distance(state, tank.x, tank.y, opp_base.x, opp_base.y)
                        target_dist = TankEvaluator.get_tactical_distance(state, wx, wy, opp_base.x, opp_base.y)
                        if target_dist < curr_dist or wx == opp_base.x or wy == opp_base.y:
                            return 78.0 - w_hp * 2.0 - wall_dist * 0.5
                    return 28.0 - w_hp
                return 8.0
            return 5.0
        direction = Action.get_move_direction(action)
        if direction:
            dx, dy = direction.value
            nx, ny = (tank.x + dx, tank.y + dy)
            if opp_tank and opp_tank.is_alive and (nx == opp_tank.x) and (ny == opp_tank.y):
                return 85.0
            if opp_base and opp_base.is_alive and (nx == opp_base.x) and (ny == opp_base.y):
                return 95.0
            if (nx, ny) in state.walls and state.walls[nx, ny].is_alive:
                wall_obj = state.walls[nx, ny]
                if opp_base and opp_base.is_alive:
                    curr_dist = TankEvaluator.get_tactical_distance(state, tank.x, tank.y, opp_base.x, opp_base.y)
                    wall_dist = TankEvaluator.get_tactical_distance(state, nx, ny, opp_base.x, opp_base.y)
                    if wall_dist < curr_dist:
                        return 52.0 - wall_obj.hp
                return 12.0
            priority = 40.0
            if opp_base and opp_base.is_alive:
                curr_dist = TankEvaluator.get_tactical_distance(state, tank.x, tank.y, opp_base.x, opp_base.y)
                new_dist = TankEvaluator.get_tactical_distance(state, nx, ny, opp_base.x, opp_base.y)
                if new_dist < curr_dist:
                    priority += 42.0
                elif new_dist > curr_dist:
                    priority -= 25.0
            if opp_tank and opp_tank.is_alive:
                curr_tdist = abs(tank.x - opp_tank.x) + abs(tank.y - opp_tank.y)
                new_tdist = abs(nx - opp_tank.x) + abs(ny - opp_tank.y)
                if new_tdist < curr_tdist:
                    priority += 20.0
                elif new_tdist > curr_tdist:
                    priority -= 10.0
            return priority
        return 20.0
