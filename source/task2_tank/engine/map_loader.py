"""
map_loader.py - Dynamic Map File Loader for Tank Battle Game
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Parses human-readable ASCII text map files (.txt) from the maps/ directory
    into GameState objects. Supports dynamic map scanning, syntax validation,
    and in-game map cycling.

Legend:
    '.' : Passable sand floor
    '#' : Destructible wall (3 HP)
    'B' : Foliage / Bush canopy (concealment, passable)
    '0' : Player 0 tank spawn (starts facing UP)
    '1' : Player 1 tank spawn (starts facing DOWN)
    'X' : Player 0 Base HQ (at bottom)
    'Y' : Player 1 Base HQ (at top)
"""

import os
from typing import List, Tuple, Optional
from task2_tank.engine.game_state import GameState
from task2_tank.engine.entities import Tank, Base, Wall
from task2_tank.engine.actions import Direction


class MapLoader:
    """
    Loads, parses, and validates ASCII grid map files.
    """

    MAPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "maps"))

    @classmethod
    def get_available_maps(cls) -> List[str]:
        """
        Scans maps/ directory and returns list of map filenames in sorted order.
        """
        if not os.path.exists(cls.MAPS_DIR):
            return []
        files = [f for f in os.listdir(cls.MAPS_DIR) if f.endswith(".txt")]
        return sorted(files)

    @classmethod
    def load_from_file(cls, filepath: str) -> GameState:
        """
        Reads and parses an ASCII map file into a GameState instance.
        """
        if not os.path.isabs(filepath):
            # Check inside MAPS_DIR first
            cand = os.path.join(cls.MAPS_DIR, filepath)
            if os.path.exists(cand):
                filepath = cand

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"[MapLoader] Map file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return cls.load_from_string(content, source_name=os.path.basename(filepath))

    @classmethod
    def load_from_string(cls, content: str, source_name: str = "custom") -> GameState:
        """
        Parses multi-line ASCII grid string into a GameState.
        """
        raw_lines = [line.strip() for line in content.splitlines()]
        # Filter out empty lines or comment lines
        lines = [line for line in raw_lines if line and not line.startswith(";")]

        if not lines:
            raise ValueError(f"[MapLoader] Empty map definition in '{source_name}'.")

        height = len(lines)
        width = len(lines[0])

        for y, line in enumerate(lines):
            if len(line) != width:
                raise ValueError(
                    f"[MapLoader] Inconsistent row width at row {y} in '{source_name}': "
                    f"expected {width}, got {len(line)}."
                )

        state = GameState(width, height)

        found_tank0 = False
        found_tank1 = False
        found_base0 = False
        found_base1 = False

        for y, row in enumerate(lines):
            for x, ch in enumerate(row):
                if ch == ".":
                    continue
                elif ch == "#":
                    state.walls[(x, y)] = Wall(x, y)
                elif ch in ("B", "b"):
                    state.foliage.add((x, y))
                elif ch == "0":
                    state.tanks[0] = Tank(x, y, player_id=0, direction=Direction.UP)
                    found_tank0 = True
                elif ch == "1":
                    state.tanks[1] = Tank(x, y, player_id=1, direction=Direction.DOWN)
                    found_tank1 = True
                elif ch in ("X", "x"):
                    state.bases[0] = Base(x, y, player_id=0)
                    found_base0 = True
                elif ch in ("Y", "y"):
                    state.bases[1] = Base(x, y, player_id=1)
                    found_base1 = True
                else:
                    print(f"[MapLoader] Warning: Unknown character '{ch}' at ({x}, {y}) in '{source_name}', treated as sand.")

        # Validation
        if not found_tank0 or not found_tank1:
            raise ValueError(f"[MapLoader] Missing tank spawn ('0' or '1') in map '{source_name}'.")
        if not found_base0 or not found_base1:
            raise ValueError(f"[MapLoader] Missing base HQ ('X' or 'Y') in map '{source_name}'.")

        state.current_player = 0
        state.game_cycle = 0
        return state

    @classmethod
    def load_by_query(cls, query: str) -> Tuple[GameState, str]:
        """
        Flexible resolver for map queries (supports indices '01', names 'classic',
        or relative/absolute file paths).
        Returns (state, canonical_display_name).
        """
        # 1. Direct file path check
        if os.path.exists(query):
            state = cls.load_from_file(query)
            display = os.path.splitext(os.path.basename(query))[0]
            return state, display

        # 2. Match against available maps in maps/ directory
        available = cls.get_available_maps()
        query_lower = query.lower()

        # Exact filename match
        for f in available:
            if f.lower() == query_lower or f.lower() == f"{query_lower}.txt":
                state = cls.load_from_file(f)
                return state, os.path.splitext(f)[0]

        # Substring or index match
        for f in available:
            f_lower = f.lower()
            if query_lower in f_lower:
                state = cls.load_from_file(f)
                return state, os.path.splitext(f)[0]

        # 3. Fallback to first available map or fallback MapBuilder
        if available:
            fallback = available[0]
            print(f"[MapLoader] Query '{query}' not found. Defaulting to '{fallback}'.")
            state = cls.load_from_file(fallback)
            return state, os.path.splitext(fallback)[0]

        # Final fallback to standard in-memory map
        from task2_tank.engine.maps import MapBuilder
        print(f"[MapLoader] Fallback to in-memory standard map.")
        return MapBuilder.create_standard_map(), "standard"

    @classmethod
    def get_next_map_name(cls, current_name: str) -> str:
        """
        Given the current map name, returns the next map in cyclic order.
        """
        available = cls.get_available_maps()
        if not available:
            return current_name

        clean_curr = current_name.lower().replace(".txt", "")
        curr_idx = -1
        for i, f in enumerate(available):
            clean_f = os.path.splitext(f)[0].lower()
            if clean_curr in clean_f or clean_f in clean_curr:
                curr_idx = i
                break

        next_idx = (curr_idx + 1) % len(available)
        return os.path.splitext(available[next_idx])[0]
