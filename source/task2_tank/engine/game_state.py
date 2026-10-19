"""
game_state.py - Game State Representation (Zero-Sum Game Formulation)
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Represents the complete state of the Tank Battle game at any given point
    in the adversarial search tree. Implements the formal Zero-Sum game
    tuple: S0, PLAYER, ACTIONS, RESULT, TERMINAL-TEST, UTILITY.
    (Task 2 - Req 1, 1.0 pt)
"""

from typing import List, Dict, Tuple, Optional
from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Tank, Base, Wall, Bullet


class GameState:
    """
    Complete snapshot of the Tank Battle game world.

    Attributes:
        width, height  : Board grid dimensions
        tanks          : {player_id -> Tank}
        bases          : {player_id -> Base}
        walls          : {(x, y) -> Wall}
        bullets        : List of active Bullet objects
        current_player : 0 or 1, whose turn it is (PLAYER function)
        game_cycle     : Number of full turns elapsed so far
        max_cycles     : Draw condition when game_cycle >= this value
    """

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

    # ------------------------------------------------------------------
    # Deep copy - needed to expand the search tree without side effects
    # ------------------------------------------------------------------
    def clone(self) -> "GameState":
        """
        Creates a fully independent deep copy of the game state.
        Every entity is cloned so that modifications in a child node
        do not affect the parent node.
        """
        new_state = GameState(self.width, self.height)
        new_state.current_player = self.current_player
        new_state.game_cycle = self.game_cycle
        new_state.max_cycles = self.max_cycles
        new_state.foliage = self.foliage

        # Clone all entities individually
        for pid, tank in self.tanks.items():
            new_state.tanks[pid] = tank.clone()
        for pid, base in self.bases.items():
            new_state.bases[pid] = base.clone()
        for pos, wall in self.walls.items():
            new_state.walls[pos] = wall.clone()
        for bullet in self.bullets:
            new_state.bullets.append(bullet.clone())

        return new_state

    # ------------------------------------------------------------------
    # ACTIONS(s) - Returns all legal actions for player_id
    # ------------------------------------------------------------------
    def get_legal_actions(self, player_id: int) -> List[Action]:
        """
        Returns the list of legal actions for the tank belonging to player_id.
        Move actions are illegal if the target cell is blocked by:
        - A living Wall
        - Any Base (own or enemy)
        - The enemy Tank
        - The board border
        FIRE and STAY are always legal.
        """
        if player_id not in self.tanks:
            return [Action.STAY]

        tank = self.tanks[player_id]
        if not tank.is_alive:
            return [Action.STAY]

        legal = []

        move_actions = [
            Action.MOVE_UP,
            Action.MOVE_DOWN,
            Action.MOVE_LEFT,
            Action.MOVE_RIGHT,
        ]

        opponent_id = 1 - player_id

        for action in move_actions:
            direction = Action.get_move_direction(action)
            dx, dy = direction.value
            nx, ny = tank.x + dx, tank.y + dy

            # Check board boundaries
            if not (0 <= nx < self.width and 0 <= ny < self.height):
                continue

            # Check if destination cell is blocked by entity
            is_blocked = False
            if (nx, ny) in self.walls and self.walls[(nx, ny)].is_alive:
                is_blocked = True
            elif any(base.x == nx and base.y == ny and base.is_alive for base in self.bases.values()):
                is_blocked = True
            elif (opponent_id in self.tanks and
                  self.tanks[opponent_id].is_alive and
                  self.tanks[opponent_id].x == nx and
                  self.tanks[opponent_id].y == ny):
                is_blocked = True

            # If blocked and tank is already facing this direction, action is redundant with STAY
            if is_blocked and tank.direction == direction:
                continue

            # Legal move: either advances tank into free cell or turns tank towards target/obstacle
            legal.append(action)

        # FIRE and STAY are always legal, with STAY as the final fallback
        legal.append(Action.FIRE)
        legal.append(Action.STAY)

        return legal

    # ------------------------------------------------------------------
    # TERMINAL-TEST(s)
    # ------------------------------------------------------------------
    def is_terminal(self) -> bool:
        """
        The game ends when:
        1. Either base is destroyed (hp <= 0)
        2. Either tank is destroyed (hp <= 0)
        3. Max cycles reached (draw)
        """
        # Check bases
        for base in self.bases.values():
            if not base.is_alive:
                return True

        # Check tanks
        for tank in self.tanks.values():
            if not tank.is_alive:
                return True

        # Check cycle limit (draw condition)
        if self.game_cycle >= self.max_cycles:
            return True

        return False

    # ------------------------------------------------------------------
    # get_winner - identifies which player won
    # ------------------------------------------------------------------
    def get_winner(self) -> Optional[int]:
        """
        Returns:
          0 if player 0 wins, 1 if player 1 wins,
          -1 for draw, None if game is not over.
        """
        if not self.is_terminal():
            return None

        # Draw when cycle limit reached and both still alive
        if self.game_cycle >= self.max_cycles:
            return -1  # Draw

        # Check if player 1's base or tank was destroyed -> player 0 wins
        p1_base_dead = 1 in self.bases and not self.bases[1].is_alive
        p1_tank_dead = 1 in self.tanks and not self.tanks[1].is_alive

        # Check if player 0's base or tank was destroyed -> player 1 wins
        p0_base_dead = 0 in self.bases and not self.bases[0].is_alive
        p0_tank_dead = 0 in self.tanks and not self.tanks[0].is_alive

        p0_lost = p0_base_dead or p0_tank_dead
        p1_lost = p1_base_dead or p1_tank_dead

        if p0_lost and p1_lost:
            return -1   # Simultaneous mutual destruction -> draw
        if p0_lost:
            return 1    # Player 1 wins
        if p1_lost:
            return 0    # Player 0 wins

        return -1  # Fallback draw

    # ------------------------------------------------------------------
    # UTILITY(s, p) - Zero-Sum utility function
    # ------------------------------------------------------------------
    def get_utility(self, player_id: int) -> float:
        """
        Terminal state utility from player_id's perspective (Lecture 07 - Slide 10).
        Zero-Sum property: UTILITY(s, MAX) = -UTILITY(s, MIN)
          +10000.0 if player_id wins
          -10000.0 if player_id loses
           0.0     if draw (or undecided / non-terminal cutoff for pure search)
        """
        if self.is_terminal():
            winner = self.get_winner()
            if winner == player_id:
                return 10000.0
            elif winner == 1 - player_id:
                return -10000.0
            return 0.0

        # Undecided state in pure search without heuristic evaluation
        return 0.0

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def is_cell_blocked(self, x: int, y: int) -> bool:
        """Returns True if cell (x, y) cannot be entered by a tank."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True
        if (x, y) in self.walls and self.walls[(x, y)].is_alive:
            return True
        for base in self.bases.values():
            if base.x == x and base.y == y and base.is_alive:
                return True
        for tank in self.tanks.values():
            if tank.x == x and tank.y == y and tank.is_alive:
                return True
        return False
