from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Bullet


def inside(state, x, y):
    if x >= 0 and x < state.width and y >= 0 and y < state.height:
        return True
    return False


def hit_at_detail(state, x, y, owner):
    """Checks bullet collision at (x, y) and returns (hit, damaged)."""
    if (x, y) in state.walls:
        w = state.walls[(x, y)]
        if w.is_alive:
            w.take_damage(1)
            return True, True

    for key in state.tanks:
        t = state.tanks[key]
        if t.is_alive and t.x == x and t.y == y and t.player_id != owner:
            t.take_damage(1)
            return True, True

    for key in state.bases:
        b = state.bases[key]
        if b.is_alive and b.x == x and b.y == y:
            # Own base blocks the shot without taking friendly-fire damage
            if b.player_id != owner:
                b.take_damage(1)
                return True, True
            return True, False

    return False, False


def hit_at(state, x, y, owner):
    hit, _ = hit_at_detail(state, x, y, owner)
    return hit


class GameRules:
    @staticmethod
    def apply_action(state, action):
        new_state = state.clone()
        player = new_state.current_player

        if action == Action.FIRE:
            GameRules._fire_bullet(new_state, player)
        elif action == Action.STAY:
            pass
        else:
            d = Action.get_move_direction(action)
            if d is not None:
                GameRules._move_tank(new_state, player, d)

        # Each bullet moves at most 3 cells per full cycle (1 cycle = P0 turn + P1 turn)
        GameRules.step_bullets(new_state, active_owner=player)
        GameRules.finish_turn(new_state, player)

        return new_state

    @staticmethod
    def finish_turn(state, player):
        dead = []
        for pos in state.walls:
            if not state.walls[pos].is_alive:
                dead.append(pos)
        for pos in dead:
            del state.walls[pos]

        if player == 1:
            state.game_cycle = state.game_cycle + 1
        state.current_player = 1 - player

    @staticmethod
    def step_bullets_one_cell(state, active_owner=None):
        """Advances active bullets by 1 cell and returns [(x, y, damaged), ...] for hits."""
        hits = []
        for bullet in state.bullets:
            if not bullet.is_active:
                continue
            if active_owner is not None and bullet.owner_id != active_owner:
                continue

            dx = bullet.direction.value[0]
            dy = bullet.direction.value[1]
            bullet.x = bullet.x + dx
            bullet.y = bullet.y + dy

            if not inside(state, bullet.x, bullet.y):
                bullet.is_active = False
            else:
                hit, damaged = hit_at_detail(state, bullet.x, bullet.y, bullet.owner_id)
                if hit:
                    bullet.is_active = False
                    hits.append((bullet.x, bullet.y, damaged))

        state.bullets = [b for b in state.bullets if b.is_active]
        return hits

    @staticmethod
    def step_bullets(state, active_owner=None):
        for _ in range(Bullet.SPEED):
            has_moving = any(
                b.is_active and (active_owner is None or b.owner_id == active_owner)
                for b in state.bullets
            )
            if not has_moving:
                break
            GameRules.step_bullets_one_cell(state, active_owner=active_owner)

    @staticmethod
    def _move_tank(state, player, direction):
        if player not in state.tanks:
            return

        tank = state.tanks[player]
        tank.direction = direction

        nx = tank.x + direction.value[0]
        ny = tank.y + direction.value[1]

        if not inside(state, nx, ny):
            return

        if (nx, ny) in state.walls:
            if state.walls[(nx, ny)].is_alive:
                return

        for key in state.bases:
            base = state.bases[key]
            if base.is_alive and base.x == nx and base.y == ny:
                return

        other = 1 - player
        if other in state.tanks:
            ot = state.tanks[other]
            if ot.is_alive and ot.x == nx and ot.y == ny:
                return

        tank.x = nx
        tank.y = ny

        # If tank steps onto a cell occupied by an active enemy bullet, collide immediately
        for bullet in state.bullets:
            if bullet.is_active and bullet.x == nx and bullet.y == ny and bullet.owner_id != player:
                tank.take_damage(1)
                bullet.is_active = False
                if not tank.is_alive:
                    break
        state.bullets = [b for b in state.bullets if b.is_active]

    @staticmethod
    def _fire_bullet(state, player):
        if player not in state.tanks:
            return

        tank = state.tanks[player]
        if not tank.is_alive:
            return

        # Spawn at tank cell so step_bullets moves 1..Bullet.SPEED (max 3 cells) cell-by-cell
        new_bullet = Bullet(tank.x, tank.y, tank.direction, player)
        state.bullets.append(new_bullet)