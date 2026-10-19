"""
rules.py - Game Transition Function and Bullet Physics
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements the RESULT(s, a) transition function for the Tank Battle game.
    Key physics rule (from problem spec):
    - Each bullet travels at most 3 cells per game cycle.
    - Collision is checked after EACH individual cell step (cell-by-cell).
    - On collision, the target loses 1 HP and the bullet is immediately destroyed.
    (Task 2 - Req 1, 1.0 pt)
"""

from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Bullet


class GameRules:
    """
    Pure static class that applies actions and advances the physics simulation.
    """

    @staticmethod
    def apply_action(state: GameState, action: Action) -> GameState:
        """
        RESULT(s, a): Applies one action for the current player and returns
        the resulting game state.

        Steps:
        1. Clone the state (non-destructive).
        2. Apply the tank action (move, fire, or stay).
        3. Advance all active bullets by up to 3 cells (cell-by-cell collision check).
        4. Remove dead walls from the board.
        5. Switch turn to the other player and increment the cycle counter
           when both players have moved.
        """
        next_state = state.clone()
        player_id = next_state.current_player

        # --- Step 1: Apply the action for the current player ---
        if action == Action.FIRE:
            GameRules._fire_bullet(next_state, player_id)
        elif action == Action.STAY:
            pass  # Do nothing, tank stays in place
        else:
            # It is a MOVE action
            direction = Action.get_move_direction(action)
            if direction is not None:
                GameRules._move_tank(next_state, player_id, direction)

        # --- Step 2: Advance all bullets (3 cells, cell-by-cell) ---
        GameRules.step_bullets(next_state)

        # --- Step 3: Remove walls that have been destroyed ---
        dead_walls = [pos for pos, wall in next_state.walls.items()
                      if not wall.is_alive]
        for pos in dead_walls:
            del next_state.walls[pos]

        # --- Step 4: Advance turn ---
        # When player 1 finishes, a full game cycle is complete
        if player_id == 1:
            next_state.game_cycle += 1
        next_state.current_player = 1 - player_id

        return next_state

    @staticmethod
    def step_bullets(state: GameState) -> None:
        """
        Moves each active bullet one cell at a time, up to SPEED (3) cells.
        After each single-cell step:
        - If the bullet leaves the board boundary -> destroy bullet.
        - If the bullet hits a Wall       -> wall loses 1 HP, bullet destroyed.
        - If the bullet hits a Tank       -> tank loses 1 HP, bullet destroyed.
        - If the bullet hits a Base       -> base loses 1 HP, bullet destroyed.
        This ensures no entity is skipped when a bullet crosses multiple cells.
        """
        for bullet in state.bullets:
            if not bullet.is_active:
                continue

            dx, dy = bullet.direction.value

            for _ in range(Bullet.SPEED):
                if not bullet.is_active:
                    break

                # Move bullet one cell
                bullet.x += dx
                bullet.y += dy

                # Check out-of-bounds
                if not (0 <= bullet.x < state.width and
                        0 <= bullet.y < state.height):
                    bullet.is_active = False
                    break

                hit = False

                # Check collision with walls
                if (bullet.x, bullet.y) in state.walls:
                    wall = state.walls[(bullet.x, bullet.y)]
                    if wall.is_alive:
                        wall.take_damage(1)
                        bullet.is_active = False
                        hit = True

                if not hit:
                    # Check collision with tanks (both players)
                    for tank in state.tanks.values():
                        if (tank.is_alive and
                                tank.x == bullet.x and
                                tank.y == bullet.y and
                                tank.player_id != bullet.owner_id):
                            tank.take_damage(1)
                            bullet.is_active = False
                            hit = True
                            break

                if not hit:
                    # Check collision with bases (both players)
                    for base in state.bases.values():
                        if (base.is_alive and
                                base.x == bullet.x and
                                base.y == bullet.y):
                            base.take_damage(1)
                            bullet.is_active = False
                            hit = True
                            break

        # Clean up deactivated bullets
        state.bullets = [b for b in state.bullets if b.is_active]

    @staticmethod
    def _move_tank(state: GameState, player_id: int,
                   direction: Direction) -> None:
        """
        Moves the tank one cell in the given direction if the target cell
        is not blocked (boundary, living wall, any base, or enemy tank).
        Always updates the tank's facing direction regardless of whether
        the move succeeds.
        """
        if player_id not in state.tanks:
            return

        tank = state.tanks[player_id]
        tank.direction = direction  # Tank always turns to face move direction

        dx, dy = direction.value
        nx, ny = tank.x + dx, tank.y + dy

        # Check boundary
        if not (0 <= nx < state.width and 0 <= ny < state.height):
            return

        # Check living wall
        if (nx, ny) in state.walls and state.walls[(nx, ny)].is_alive:
            return

        # Check any base (cannot drive into a base)
        for base in state.bases.values():
            if base.is_alive and base.x == nx and base.y == ny:
                return

        # Check enemy tank collision
        opponent_id = 1 - player_id
        if (opponent_id in state.tanks and
                state.tanks[opponent_id].is_alive and
                state.tanks[opponent_id].x == nx and
                state.tanks[opponent_id].y == ny):
            return

        tank.x = nx
        tank.y = ny

    @staticmethod
    def _fire_bullet(state: GameState, player_id: int) -> None:
        """
        Creates a new bullet one cell ahead of the tank in its facing direction.
        The bullet's starting position is immediately in front of the nozzle.
        """
        if player_id not in state.tanks:
            return

        tank = state.tanks[player_id]
        if not tank.is_alive:
            return

        dx, dy = tank.direction.value
        bullet_x = tank.x + dx
        bullet_y = tank.y + dy

        # Bullet starts one cell ahead of the tank
        new_bullet = Bullet(bullet_x, bullet_y, tank.direction, player_id)

        # Check immediate collision at the spawn cell
        # (handles the edge case where the nozzle is right next to a wall/base/tank)
        if (0 <= bullet_x < state.width and 0 <= bullet_y < state.height):
            # Wall at spawn cell
            if (bullet_x, bullet_y) in state.walls:
                wall = state.walls[(bullet_x, bullet_y)]
                if wall.is_alive:
                    wall.take_damage(1)
                    return  # Bullet destroyed at spawn, never appended

            # Tank at spawn cell
            for tank_entity in state.tanks.values():
                if (tank_entity.is_alive and
                        tank_entity.player_id != player_id and
                        tank_entity.x == bullet_x and
                        tank_entity.y == bullet_y):
                    tank_entity.take_damage(1)
                    return

            # Base at spawn cell
            for base in state.bases.values():
                if (base.is_alive and
                        base.x == bullet_x and base.y == bullet_y):
                    base.take_damage(1)
                    return

            state.bullets.append(new_bullet)
        # If spawn cell is out of bounds the bullet simply doesn't appear
