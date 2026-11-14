import json
from typing import Dict, List, Tuple, Set, Optional
from task3_kakuro.csp.variable import Cell
from task3_kakuro.csp.constraint import RunConstraint


class KakuroCSP:

    def __init__(self, rows: int = 0, cols: int = 0):
        self.rows = rows
        self.cols = cols
        self.name: str = 'Kakuro Puzzle'
        self.variables: Dict[Tuple[int, int], Cell] = {}
        self.runs: List[RunConstraint] = []
        self.cell_runs: Dict[Cell, List[RunConstraint]] = {}
        self.clue_cells: Dict[Tuple[int, int], Dict[str, Optional[int]]] = {}

    def load_from_json(self, json_path: str) -> None:
        with open(json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        self.name = data.get('name', 'Kakuro Puzzle')
        self.rows = data['rows']
        self.cols = data['cols']

        self.variables.clear()
        self.runs.clear()
        self.cell_runs.clear()
        self.clue_cells.clear()

        horizontal_clues = data.get('horizontal_clues', [])

        for h in horizontal_clues:
            r = h['r']
            c = h['c']
            clue = h['clue']

            self._record_clue(r, c, 'H', clue)

            coords = []

            if 'cells' in h:
                for pos in h['cells']:
                    coords.append(tuple(pos))
            else:
                length = h['length']

                for i in range(1, length + 1):
                    coords.append((r, c + i))

            run_cells = []

            for coord in coords:
                cr, cc = coord
                one_cell = self._get_or_create_cell(cr, cc)
                run_cells.append(one_cell)

            run = RunConstraint(direction='H', target_sum=clue, cells=run_cells)
            self.runs.append(run)

            for cell in run_cells:
                if cell not in self.cell_runs:
                    self.cell_runs[cell] = []
                self.cell_runs[cell].append(run)

        vertical_clues = data.get('vertical_clues', [])

        for v in vertical_clues:
            r = v['r']
            c = v['c']
            clue = v['clue']

            self._record_clue(r, c, 'V', clue)

            coords = []

            if 'cells' in v:
                for pos in v['cells']:
                    coords.append(tuple(pos))
            else:
                length = v['length']

                for i in range(1, length + 1):
                    coords.append((r + i, c))

            run_cells = []

            for coord in coords:
                cr, cc = coord
                one_cell = self._get_or_create_cell(cr, cc)
                run_cells.append(one_cell)

            run = RunConstraint(direction='V', target_sum=clue, cells=run_cells)
            self.runs.append(run)

            for cell in run_cells:
                if cell not in self.cell_runs:
                    self.cell_runs[cell] = []
                self.cell_runs[cell].append(run)

    def _get_or_create_cell(self, r: int, c: int) -> Cell:
        pos = (r, c)

        if pos not in self.variables:
            self.variables[pos] = Cell(r, c)

        return self.variables[pos]

    def _record_clue(self, r: int, c: int, direction: str, clue: int) -> None:
        pos = (r, c)

        if pos not in self.clue_cells:
            self.clue_cells[pos] = {'H': None, 'V': None}

        self.clue_cells[pos][direction] = clue

    def get_neighbors(self, cell: Cell) -> Set[Cell]:
        neighbors = set()

        if cell in self.cell_runs:
            runs_of_cell = self.cell_runs[cell]
        else:
            runs_of_cell = []

        for run in runs_of_cell:
            for other in run.cells:
                if other != cell:
                    neighbors.add(other)

        return neighbors

    def validate_puzzle_integrity(self) -> bool:
        sum_h = 0
        sum_v = 0

        for run in self.runs:
            if run.direction == 'H':
                sum_h = sum_h + run.target_sum

        for run in self.runs:
            if run.direction == 'V':
                sum_v = sum_v + run.target_sum

        is_valid = sum_h == sum_v
        return is_valid

    def get_clue_sums(self) -> Tuple[int, int]:
        sum_h = 0
        sum_v = 0

        for run in self.runs:
            if run.direction == 'H':
                sum_h = sum_h + run.target_sum

        for run in self.runs:
            if run.direction == 'V':
                sum_v = sum_v + run.target_sum

        return (sum_h, sum_v)

    def is_solved(self) -> bool:
        for cell in self.variables.values():
            if not cell.is_assigned:
                return False

        for run in self.runs:
            if not run.is_satisfied():
                return False

        return True

    def get_solution_grid(self) -> Dict[Tuple[int, int], int]:
        solution = {}

        for pos in self.variables:
            cell = self.variables[pos]

            if cell.is_assigned:
                solution[pos] = cell.value

        return solution

    def reset(self) -> None:
        for cell in self.variables.values():
            cell.unassign()
            cell.domain = set(range(1, 10))