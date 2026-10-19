"""
evaluator.py - State Evaluation Function for Heuristic Search
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Computes a heuristic score EVAL(s) for non-terminal states as required
    by Heuristic Minimax and Heuristic Alpha-Beta (Lecture 07 - Slide 28).
    Uses a linear combination of strategic features:
    - Base HP difference (highest priority)
    - Tank HP difference
    - Distance advantage to enemy base
    - Line-of-fire opportunity (can we hit enemy tank/base?)
    - Bullet incoming threat penalty (must dodge incoming bullets)
"""

from typing import Tuple
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Direction


class TankEvaluator:
    """
    Heuristic Evaluation Function for the Tank Battle zero-sum game.
    Higher score indicates greater advantage for player_id.
    """

    def __init__(
        self,
        w_base_hp: float = 120.0,
        w_tank_hp: float = 50.0,
        w_dist_base: float = 5.0,
        w_dist_tank: float = 2.0,
        w_line_of_fire: float = 30.0,
        w_bullet_danger: float = 70.0
    ):
        self.w_base_hp = w_base_hp
        self.w_tank_hp = w_tank_hp
        self.w_dist_base = w_dist_base
        self.w_dist_tank = w_dist_tank
        self.w_line_of_fire = w_line_of_fire
        self.w_bullet_danger = w_bullet_danger

    def evaluate(self, state: GameState, player_id: int) -> float:
        """
        Evaluates the game state from player_id's perspective.
        """
        # If terminal, return exact zero-sum utility
        if state.is_terminal():
            return state.get_utility(player_id)

        opponent_id = 1 - player_id
        score = 0.0

        my_tank = state.tanks.get(player_id)
        opp_tank = state.tanks.get(opponent_id)
        my_base = state.bases.get(player_id)
        opp_base = state.bases.get(opponent_id)

        # 1. Base HP difference (most critical factor)
        my_base_hp = my_base.hp if (my_base and my_base.is_alive) else 0
        opp_base_hp = opp_base.hp if (opp_base and opp_base.is_alive) else 0
        score += self.w_base_hp * (my_base_hp - opp_base_hp)

        # 2. Tank HP difference
        my_tank_hp = my_tank.hp if (my_tank and my_tank.is_alive) else 0
        opp_tank_hp = opp_tank.hp if (opp_tank and opp_tank.is_alive) else 0
        score += self.w_tank_hp * (my_tank_hp - opp_tank_hp)

        # 3. Distance to enemy base (Manhattan distance)
        if my_tank and my_tank.is_alive and opp_base and opp_base.is_alive:
            my_dist_to_opp_base = abs(my_tank.x - opp_base.x) + abs(my_tank.y - opp_base.y)
            score -= self.w_dist_base * my_dist_to_opp_base

        if opp_tank and opp_tank.is_alive and my_base and my_base.is_alive:
            opp_dist_to_my_base = abs(opp_tank.x - my_base.x) + abs(opp_tank.y - my_base.y)
            score += self.w_dist_base * opp_dist_to_my_base

        # 4. Tank to Tank distance
        if my_tank and my_tank.is_alive and opp_tank and opp_tank.is_alive:
            tank_dist = abs(my_tank.x - opp_tank.x) + abs(my_tank.y - opp_tank.y)
            score -= self.w_dist_tank * tank_dist

        # 5. Line of fire bonus / penalty
        if my_tank and my_tank.is_alive:
            if self._has_line_of_sight(state, my_tank.x, my_tank.y, my_tank.direction, opp_base):
                score += self.w_line_of_fire * 2.0
            if opp_tank and opp_tank.is_alive and self._has_line_of_sight(state, my_tank.x, my_tank.y, my_tank.direction, opp_tank):
                score += self.w_line_of_fire

        if opp_tank and opp_tank.is_alive:
            if self._has_line_of_sight(state, opp_tank.x, opp_tank.y, opp_tank.direction, my_base):
                score -= self.w_line_of_fire * 2.0
            if my_tank and my_tank.is_alive and self._has_line_of_sight(state, opp_tank.x, opp_tank.y, opp_tank.direction, my_tank):
                score -= self.w_line_of_fire

        # 6. Incoming bullet danger (threat evasion)
        if my_tank and my_tank.is_alive:
            for bullet in state.bullets:
                if bullet.is_active and bullet.owner_id == opponent_id:
                    if self._is_bullet_approaching(bullet, my_tank.x, my_tank.y):
                        score -= self.w_bullet_danger

        return score

    def _has_line_of_sight(self, state: GameState, x: int, y: int, direction: Direction, target) -> bool:
        """
        Raycasts from (x, y) along direction up to max board dimension to check if target is visible.
        Returns True if target is in direct line of fire without blocking walls.
        """
        if not target or not target.is_alive:
            return False

        dx, dy = direction.value
        cx, cy = x + dx, y + dy
        max_steps = max(state.width, state.height)

        for _ in range(max_steps):
            if not (0 <= cx < state.width and 0 <= cy < state.height):
                break
            if cx == target.x and cy == target.y:
                return True
            # Blocked by living wall
            if (cx, cy) in state.walls and state.walls[(cx, cy)].is_alive:
                break
            cx += dx
            cy += dy

        return False

    def _is_bullet_approaching(self, bullet, target_x: int, target_y: int) -> bool:
        """
        Checks whether an active bullet is within 3 cells heading directly at (target_x, target_y).
        """
        dx, dy = bullet.direction.value
        bx, by = bullet.x, bullet.y

        for step in range(1, 4):
            if bx + dx * step == target_x and by + dy * step == target_y:
                return True
        return False

    @staticmethod
    def action_tactical_priority(state: GameState, action, player_id: int) -> float:
        """
        Evaluates immediate tactical merit of an action for move ordering and tie-breaking:
        1. FIRE with direct, unobstructed shot at enemy base -> 120.0
        2. FIRE with direct, unobstructed shot at enemy tank -> 100.0
        3. MOVE reducing distance to enemy base -> 80.0 - new_dist
        4. MOVE reducing distance to enemy tank -> 70.0 - new_tdist
        5. FIRE breaking immediately adjacent wall that blocks path to enemy -> 45.0
        6. Other legal moves (maneuvering / flanking) -> 40.0
        7. FIRE at distant wall or empty air -> 5.0
        8. STAY -> 0.0 (lowest priority)
        """
        from task2_tank.engine.actions import Action
        if action == Action.STAY:
            return 0.0

        tank = state.tanks.get(player_id)
        if not tank or not tank.is_alive:
            return 0.0

        opp_base = state.bases.get(1 - player_id)
        opp_tank = state.tanks.get(1 - player_id)

        if action == Action.FIRE:
            dx, dy = tank.direction.value
            fx, fy = tank.x + dx, tank.y + dy

            # Raycast along bullet trajectory to find first hit
            max_range = max(state.width, state.height)
            cx, cy = fx, fy
            first_hit = None

            for _ in range(max_range):
                if not (0 <= cx < state.width and 0 <= cy < state.height):
                    break
                if opp_base and opp_base.is_alive and cx == opp_base.x and cy == opp_base.y:
                    first_hit = "base"
                    break
                if opp_tank and opp_tank.is_alive and cx == opp_tank.x and cy == opp_tank.y:
                    first_hit = "tank"
                    break
                if (cx, cy) in state.walls and state.walls[(cx, cy)].is_alive:
                    first_hit = ("wall", cx, cy)
                    break
                cx += dx
                cy += dy

            if first_hit == "base":
                return 120.0  # Clear shot at enemy base!
            if first_hit == "tank":
                return 100.0  # Clear shot at enemy tank!

            # If hitting a wall directly 1 step ahead that blocks path to enemy
            if first_hit and first_hit[0] == "wall":
                wx, wy = first_hit[1], first_hit[2]
                if abs(wx - tank.x) <= 1 and abs(wy - tank.y) <= 1:
                    # Wall is directly in front
                    if opp_base and opp_base.is_alive:
                        curr_dist = abs(tank.x - opp_base.x) + abs(tank.y - opp_base.y)
                        target_dist = abs(wx - opp_base.x) + abs(wy - opp_base.y)
                        if target_dist < curr_dist:
                            return 75.0  # Breaching obstacle towards enemy base
                    return 25.0
                return 5.0  # Firing at a distant wall is low priority

            return 5.0  # Firing into empty space

        # For MOVE actions
        direction = Action.get_move_direction(action)
        if direction:
            dx, dy = direction.value
            nx, ny = tank.x + dx, tank.y + dy

            # If this action turns the tank to face an adjacent enemy entity directly
            if opp_tank and opp_tank.is_alive and nx == opp_tank.x and ny == opp_tank.y:
                return 85.0  # Aim directly at adjacent enemy tank!
            if opp_base and opp_base.is_alive and nx == opp_base.x and ny == opp_base.y:
                return 95.0  # Aim directly at adjacent enemy base!

            priority = 40.0

            if opp_base and opp_base.is_alive:
                curr_dist = abs(tank.x - opp_base.x) + abs(tank.y - opp_base.y)
                new_dist = abs(nx - opp_base.x) + abs(ny - opp_base.y)
                if new_dist < curr_dist:
                    priority += 40.0  # +40 for closing in on base (total 80)
                elif new_dist > curr_dist:
                    priority -= 25.0

            if opp_tank and opp_tank.is_alive:
                curr_tdist = abs(tank.x - opp_tank.x) + abs(tank.y - opp_tank.y)
                new_tdist = abs(nx - opp_tank.x) + abs(ny - opp_tank.y)
                if new_tdist < curr_tdist:
                    priority += 25.0  # +25 for approaching enemy tank
                elif new_tdist > curr_tdist:
                    priority -= 10.0

            return priority

        return 20.0
