from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Bullet


def inside(state, x, y):
    if x >= 0 and x < state.width and y >= 0 and y < state.height:
        return True
    return False


def hit_at(state, x, y, owner):
    if (x, y) in state.walls:
        w = state.walls[(x, y)]
        if w.is_alive:
            w.take_damage(1)
            return True

    for key in state.tanks:
        t = state.tanks[key]
        if t.is_alive and t.x == x and t.y == y and t.player_id != owner:
            t.take_damage(1)
            return True

    for key in state.bases:
        b = state.bases[key]
        if b.is_alive and b.x == x and b.y == y:
            b.take_damage(1)
            return True

    return False


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

        GameRules.step_bullets(new_state)

        dead = []
        for pos in new_state.walls:
            if not new_state.walls[pos].is_alive:
                dead.append(pos)
        for pos in dead:
            del new_state.walls[pos]

        if player == 1:
            new_state.game_cycle = new_state.game_cycle + 1
        new_state.current_player = 1 - player

        return new_state

    @staticmethod
    def step_bullets(state):
        for bullet in state.bullets:
            if bullet.is_active == False:
                continue

            dx = bullet.direction.value[0]
            dy = bullet.direction.value[1]

            i = 0
            while i < Bullet.SPEED and bullet.is_active:
                bullet.x = bullet.x + dx
                bullet.y = bullet.y + dy

                if not inside(state, bullet.x, bullet.y):
                    bullet.is_active = False
                else:
                    if hit_at(state, bullet.x, bullet.y, bullet.owner_id):
                        bullet.is_active = False

                i += 1

        remain = []
        for bullet in state.bullets:
            if bullet.is_active:
                remain.append(bullet)
        state.bullets = remain

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

    @staticmethod
    def _fire_bullet(state, player):
        if player not in state.tanks:
            return

        tank = state.tanks[player]
        if not tank.is_alive:
            return

        bx = tank.x + tank.direction.value[0]
        by = tank.y + tank.direction.value[1]
        new_bullet = Bullet(bx, by, tank.direction, player)

        if inside(state, bx, by):
            if hit_at(state, bx, by, player):
                return
            state.bullets.append(new_bullet)