import os
from typing import List, Tuple, Optional
from task2_tank.engine.game_state import GameState
from task2_tank.engine.entities import Tank, Base, Wall
from task2_tank.engine.actions import Direction


class MapLoader:
    MAPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'maps'))

    @classmethod
    def get_available_maps(cls) -> List[str]:
        if not os.path.exists(cls.MAPS_DIR):
            return []

        all_files = os.listdir(cls.MAPS_DIR)
        txt_files = []

        for file_name in all_files:
            if file_name.endswith('.txt'):
                txt_files.append(file_name)

        txt_files = sorted(txt_files)
        return txt_files

    @classmethod
    def load_from_file(cls, filepath: str) -> GameState:
        if not os.path.isabs(filepath):
            candidate_path = os.path.join(cls.MAPS_DIR, filepath)

            if os.path.exists(candidate_path):
                filepath = candidate_path

        if not os.path.exists(filepath):
            raise FileNotFoundError('[MapLoader] Map file not found: ' + str(filepath))

        with open(filepath, 'r', encoding='utf-8') as map_file:
            content = map_file.read()

        source_name = os.path.basename(filepath)
        state = cls.load_from_string(content, source_name=source_name)
        return state

    @classmethod
    def load_from_string(cls, content: str, source_name: str = 'custom') -> GameState:
        raw_lines = []

        for line in content.splitlines():
            stripped_line = line.strip()
            raw_lines.append(stripped_line)

        lines = []

        for line in raw_lines:
            if len(line) > 0 and not line.startswith(';'):
                lines.append(line)

        if len(lines) == 0:
            raise ValueError("[MapLoader] Empty map definition in '" + str(source_name) + "'.")

        height = len(lines)
        width = len(lines[0])

        for y in range(len(lines)):
            line = lines[y]

            if len(line) != width:
                raise ValueError(
                    "[MapLoader] Inconsistent row width at row " + str(y)
                    + " in '" + str(source_name) + "': expected " + str(width)
                    + ", got " + str(len(line)) + "."
                )

        state = GameState(width, height)

        found_tank0 = False
        found_tank1 = False
        found_base0 = False
        found_base1 = False

        for y in range(len(lines)):
            row = lines[y]

            for x in range(len(row)):
                ch = row[x]

                if ch == '.':
                    continue
                elif ch in ('#', 'M', 'm', '3'):
                    state.walls[(x, y)] = Wall(x, y, hp=3)
                elif ch in ('W', 'w', '2'):
                    state.walls[(x, y)] = Wall(x, y, hp=2)
                elif ch in ('S', 's'):
                    state.walls[(x, y)] = Wall(x, y, hp=1)
                elif ch in ('B', 'b'):
                    state.foliage.add((x, y))
                elif ch == '0':
                    state.tanks[0] = Tank(x, y, player_id=0, direction=Direction.UP)
                    found_tank0 = True
                elif ch == '1':
                    state.tanks[1] = Tank(x, y, player_id=1, direction=Direction.DOWN)
                    found_tank1 = True
                elif ch in ('X', 'x'):
                    state.bases[0] = Base(x, y, player_id=0)
                    found_base0 = True
                elif ch in ('Y', 'y'):
                    state.bases[1] = Base(x, y, player_id=1)
                    found_base1 = True
                else:
                    print("[MapLoader] Warning: Unknown character '" + str(ch) + "' at (" + str(x) + ", " + str(y) + ") in '" + str(source_name) + "', treated as sand.")

        if not found_tank0 or not found_tank1:
            raise ValueError("[MapLoader] Missing tank spawn ('0' or '1') in map '" + str(source_name) + "'.")

        if not found_base0 or not found_base1:
            raise ValueError("[MapLoader] Missing base HQ ('X' or 'Y') in map '" + str(source_name) + "'.")

        state.current_player = 0
        state.game_cycle = 0

        return state

    @classmethod
    def load_by_query(cls, query: str) -> Tuple[GameState, str]:
        if os.path.exists(query):
            state = cls.load_from_file(query)
            base_name = os.path.basename(query)
            display_name = os.path.splitext(base_name)[0]
            return (state, display_name)

        available = cls.get_available_maps()
        query_lower = query.lower()

        for file_name in available:
            file_name_lower = file_name.lower()

            if file_name_lower == query_lower or file_name_lower == query_lower + '.txt':
                state = cls.load_from_file(file_name)
                display_name = os.path.splitext(file_name)[0]
                return (state, display_name)

        for file_name in available:
            file_name_lower = file_name.lower()

            if query_lower in file_name_lower:
                state = cls.load_from_file(file_name)
                display_name = os.path.splitext(file_name)[0]
                return (state, display_name)

        if len(available) > 0:
            fallback = available[0]
            print("[MapLoader] Query '" + str(query) + "' not found. Defaulting to '" + str(fallback) + "'.")
            state = cls.load_from_file(fallback)
            display_name = os.path.splitext(fallback)[0]
            return (state, display_name)

        from task2_tank.engine.maps import MapBuilder

        print('[MapLoader] Fallback to in-memory standard map.')
        state = MapBuilder.create_standard_map()
        return (state, 'standard')

    @classmethod
    def get_next_map_name(cls, current_name: str) -> str:
        available = cls.get_available_maps()

        if len(available) == 0:
            return current_name

        clean_curr = current_name.lower().replace('.txt', '')
        curr_idx = -1

        for i in range(len(available)):
            file_name = available[i]
            clean_f = os.path.splitext(file_name)[0].lower()

            if clean_curr in clean_f or clean_f in clean_curr:
                curr_idx = i
                break

        next_idx = (curr_idx + 1) % len(available)
        next_name = os.path.splitext(available[next_idx])[0]
        return next_name

    @classmethod
    def get_prev_map_name(cls, current_name: str) -> str:
        available = cls.get_available_maps()

        if len(available) == 0:
            return current_name

        clean_curr = current_name.lower().replace('.txt', '')
        curr_idx = 0

        for i in range(len(available)):
            file_name = available[i]
            clean_f = os.path.splitext(file_name)[0].lower()

            if clean_curr in clean_f or clean_f in clean_curr:
                curr_idx = i
                break

        prev_idx = (curr_idx - 1) % len(available)
        prev_name = os.path.splitext(available[prev_idx])[0]
        return prev_name