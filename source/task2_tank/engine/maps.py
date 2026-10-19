"""
maps.py - Standard Map Layouts for Tank Battle
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Provides pre-built symmetric map configurations used in all experiments
    so results are reproducible and fair across all 4 AI configurations.
"""

from task2_tank.engine.game_state import GameState
from task2_tank.engine.entities import Tank, Base, Wall
from task2_tank.engine.actions import Direction


class MapBuilder:
    """
    Builds deterministic, symmetric battle maps.
    """

    @staticmethod
    def create_standard_map(width: int = 13, height: int = 13) -> GameState:
        """
        Creates the authentic Battle City symmetric 13x13 benchmark map.
        Features 3 clear tactical lanes (Left col 2, Center col 6, Right col 10)
        with protective base bunkers, flanking brick barriers, and center foliage.

        Coordinate system: x = column (0..12), y = row (0..12).
          Player 0 (bottom): Tank at (6, 10) facing UP, Base at (6, 12)
          Player 1 (top):    Tank at (6,  2) facing DOWN, Base at (6,  0)
        """
        state = GameState(width, height)

        # ---- Tanks: Center forward spawns ready for immediate tactical engagement ----
        state.tanks[0] = Tank(6, 10, player_id=0, direction=Direction.UP)
        state.tanks[1] = Tank(6,  2, player_id=1, direction=Direction.DOWN)

        # ---- Bases: Center bottom & center top ----
        state.bases[0] = Base(6, 12, player_id=0)
        state.bases[1] = Base(6,  0, player_id=1)

        def add_wall(x: int, y: int):
            if 0 <= x < width and 0 <= y < height:
                state.walls[(x, y)] = Wall(x, y)

        # 1. Base Fortifications (U-shaped bunkers)
        # Player 0 Base Bunker (Bottom)
        for x in [5, 7]:
            add_wall(x, 12)
            add_wall(x, 11)
        add_wall(6, 11)

        # Player 1 Base Bunker (Top)
        for x in [5, 7]:
            add_wall(x, 0)
            add_wall(x, 1)
        add_wall(6, 1)

        # 2. Outer Flanking Barriers (Columns 1 & 11)
        for y in [3, 4, 8, 9]:
            add_wall(1, y)
            add_wall(11, y)

        # 3. Inner Column Barriers (Columns 3 & 9)
        for y in [3, 5, 7, 9]:
            add_wall(3, y)
            add_wall(9, y)

        # 4. Midfield Flanks (Columns 4 & 8) around Central Foliage
        for x in [4, 8]:
            add_wall(x, 5)
            add_wall(x, 7)

        # 5. Central Foliage / Bush Zone (Passable terrain)
        for fx in range(4, 9):
            for fy in [5, 6, 7]:
                state.foliage.add((fx, fy))

        state.current_player = 0
        state.game_cycle = 0
        return state

    @staticmethod
    def create_open_map(width: int = 13, height: int = 13) -> GameState:
        """
        Creates an open (minimal walls) map for direct aggression benchmark.
        Useful for testing agents when cover is scarce.
        """
        state = GameState(width, height)

        state.tanks[0] = Tank(2, 10, player_id=0, direction=Direction.UP)
        state.tanks[1] = Tank(10, 2, player_id=1, direction=Direction.DOWN)

        state.bases[0] = Base(6, 12, player_id=0)
        state.bases[1] = Base(6,  0, player_id=1)

        # Only a few central walls
        for wpos in [(5, 6), (6, 6), (7, 6)]:
            state.walls[wpos] = Wall(*wpos)

        state.current_player = 0
        state.game_cycle = 0
        return state

    @staticmethod
    def create_chokepoint_map(width: int = 13, height: int = 13) -> GameState:
        """
        Creates a tactical corridor / labyrinth map with narrow chokepoints.
        Tests pathfinding, obstacle breaching, and ambush tactics under tight cover.
        """
        state = GameState(width, height)

        state.tanks[0] = Tank(6, 10, player_id=0, direction=Direction.UP)
        state.tanks[1] = Tank(6,  2, player_id=1, direction=Direction.DOWN)

        state.bases[0] = Base(6, 12, player_id=0)
        state.bases[1] = Base(6,  0, player_id=1)

        def add_wall(x: int, y: int):
            if 0 <= x < width and 0 <= y < height:
                state.walls[(x, y)] = Wall(x, y)

        # Base bunkers
        for x in [5, 7]:
            add_wall(x, 12)
            add_wall(x, 11)
            add_wall(x, 0)
            add_wall(x, 1)
        add_wall(6, 11)
        add_wall(6, 1)

        # Horizontal partition walls creating zigzag corridors (columns 1..9 and 3..11)
        for x in range(1, 10):
            if x != 6:
                add_wall(x, 4)
        for x in range(3, 12):
            if x != 6:
                add_wall(x, 8)

        # Middle foliage cover
        for fx in range(4, 9):
            state.foliage.add((fx, 6))

        state.current_player = 0
        state.game_cycle = 0
        return state

    @classmethod
    def get_map_by_name(cls, name: str, width: int = 13, height: int = 13) -> GameState:
        """
        Helper to get a map configuration by keyword or file.
        Attempts to load from maps/*.txt via MapLoader first, with in-memory fallbacks.
        """
        try:
            from task2_tank.engine.map_loader import MapLoader
            state, _ = MapLoader.load_by_query(name)
            return state
        except Exception as e:
            # Fallback to in-memory builder if file lookup fails
            name_lower = name.lower()
            if "open" in name_lower:
                return cls.create_open_map(width, height)
            elif "choke" in name_lower or "maze" in name_lower or "corridor" in name_lower:
                return cls.create_chokepoint_map(width, height)
            else:
                return cls.create_standard_map(width, height)
