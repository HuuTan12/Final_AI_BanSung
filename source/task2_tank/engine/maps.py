from task2_tank.engine.game_state import GameState
from task2_tank.engine.entities import Tank, Base, Wall
from task2_tank.engine.actions import Direction


class MapBuilder:

    @staticmethod
    def create_standard_map(width: int = 13, height: int = 13) -> GameState:
        state = GameState(width, height)

        state.tanks[0] = Tank(6, 10, player_id=0, direction=Direction.UP)
        state.tanks[1] = Tank(6, 2, player_id=1, direction=Direction.DOWN)

        state.bases[0] = Base(6, 12, player_id=0)
        state.bases[1] = Base(6, 0, player_id=1)

        def add_wall(x: int, y: int):
            if x >= 0 and x < width and y >= 0 and y < height:
                state.walls[(x, y)] = Wall(x, y)

        for x in [5, 7]:
            add_wall(x, 12)
            add_wall(x, 11)
        add_wall(6, 11)

        for x in [5, 7]:
            add_wall(x, 0)
            add_wall(x, 1)
        add_wall(6, 1)

        for y in [3, 4, 8, 9]:
            add_wall(1, y)
            add_wall(11, y)

        for y in [3, 5, 7, 9]:
            add_wall(3, y)
            add_wall(9, y)

        for x in [4, 8]:
            add_wall(x, 5)
            add_wall(x, 7)

        for fx in range(4, 9):
            for fy in [5, 6, 7]:
                state.foliage.add((fx, fy))

        state.current_player = 0
        state.game_cycle = 0

        return state

    @staticmethod
    def create_open_map(width: int = 13, height: int = 13) -> GameState:
        state = GameState(width, height)

        state.tanks[0] = Tank(2, 10, player_id=0, direction=Direction.UP)
        state.tanks[1] = Tank(10, 2, player_id=1, direction=Direction.DOWN)

        state.bases[0] = Base(6, 12, player_id=0)
        state.bases[1] = Base(6, 0, player_id=1)

        wall_positions = [(5, 6), (6, 6), (7, 6)]

        for wpos in wall_positions:
            wall_x = wpos[0]
            wall_y = wpos[1]
            state.walls[wpos] = Wall(wall_x, wall_y)

        state.current_player = 0
        state.game_cycle = 0

        return state

    @staticmethod
    def create_chokepoint_map(width: int = 13, height: int = 13) -> GameState:
        state = GameState(width, height)

        state.tanks[0] = Tank(6, 10, player_id=0, direction=Direction.UP)
        state.tanks[1] = Tank(6, 2, player_id=1, direction=Direction.DOWN)

        state.bases[0] = Base(6, 12, player_id=0)
        state.bases[1] = Base(6, 0, player_id=1)

        def add_wall(x: int, y: int):
            if x >= 0 and x < width and y >= 0 and y < height:
                state.walls[(x, y)] = Wall(x, y)

        for x in [5, 7]:
            add_wall(x, 12)
            add_wall(x, 11)
            add_wall(x, 0)
            add_wall(x, 1)

        add_wall(6, 11)
        add_wall(6, 1)

        for x in range(1, 10):
            if x != 6:
                add_wall(x, 4)

        for x in range(3, 12):
            if x != 6:
                add_wall(x, 8)

        for fx in range(4, 9):
            state.foliage.add((fx, 6))

        state.current_player = 0
        state.game_cycle = 0

        return state

    @staticmethod
    def create_citadel_gauntlet_map(width: int = 13, height: int = 13) -> GameState:
        from task2_tank.engine.map_loader import MapLoader

        layout_rows = [
            '#.S.W#Y#W.S.#',
            '.##W.###.W##.',
            '.#B.S.1.S.B#.',
            '.W.#B###B#.W.',
            'S..W.S#S.W..S',
            '.#WB.BWB.BW#.',
            'B.S##BSB##S.B',
            '.#WB.BWB.BW#.',
            'S..W.S#S.W..S',
            '.W.#B###B#.W.',
            '.#B.S.0.S.B#.',
            '.##W.###.W##.',
            '#.S.W#X#W.S.#'
        ]

        ascii_layout = '\n'.join(layout_rows)

        state = MapLoader.load_from_string(ascii_layout, source_name='09_citadel_gauntlet')
        return state

    @classmethod
    def get_map_by_name(cls, name: str, width: int = 13, height: int = 13) -> GameState:
        try:
            from task2_tank.engine.map_loader import MapLoader

            state, map_display_name = MapLoader.load_by_query(name)
            return state
        except Exception as e:
            name_lower = name.lower()

            if 'open' in name_lower:
                return cls.create_open_map(width, height)
            elif 'citadel' in name_lower or 'gauntlet' in name_lower or '09' in name_lower:
                return cls.create_citadel_gauntlet_map(width, height)
            elif 'choke' in name_lower or 'maze' in name_lower or 'corridor' in name_lower:
                return cls.create_chokepoint_map(width, height)
            else:
                return cls.create_standard_map(width, height)