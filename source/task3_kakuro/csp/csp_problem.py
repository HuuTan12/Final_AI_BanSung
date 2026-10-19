"""
Module: csp_problem.py
Mô tả: Quản lý toàn bộ bài toán CSP Kakuro: danh sách các ô biến, các ràng buộc Run,
quan hệ láng giềng giữa các biến và kiểm tra tính nhất quán ban đầu (Tổng ngang == Tổng dọc).
"""

import json
from typing import Dict, List, Tuple, Set, Optional
from task3_kakuro.csp.variable import Cell
from task3_kakuro.csp.constraint import RunConstraint


class KakuroCSP:
    """
    Mô hình mạng ràng buộc (Constraint Network) cho bàn cờ Kakuro.
    """

    def __init__(self, rows: int = 0, cols: int = 0):
        self.rows = rows
        self.cols = cols
        self.name: str = "Kakuro Puzzle"
        self.variables: Dict[Tuple[int, int], Cell] = {} # tập hợp các ô trắng
        self.runs: List[RunConstraint] = [] # ds tất cả run
        self.cell_runs: Dict[Cell, List[RunConstraint]] = {}
        # Lưu thông tin ô đen chứa clue để phục vụ vẽ UI: {(r, c): {'H': int, 'V': int}}
        self.clue_cells: Dict[Tuple[int, int], Dict[str, Optional[int]]] = {} # lưu số clue

    #nạp dữ liệu
    def load_from_json(self, json_path: str) -> None:
        """
        Nạp cấu hình bảng cờ (kích thước, các ô đen chứa clue và các ô trắng) từ file JSON.
        Tương thích linh hoạt với cả định dạng có danh sách 'cells' hoặc dùng 'length'.
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.name = data.get("name", "Kakuro Puzzle")
        self.rows = data["rows"]
        self.cols = data["cols"]
        self.variables.clear()
        self.runs.clear()
        self.cell_runs.clear()
        self.clue_cells.clear()

        # 1. Nạp các ràng buộc hàng ngang (Horizontal Clues)
        for h in data.get("horizontal_clues", []):
            r, c, clue = h["r"], h["c"], h["clue"]
            self._record_clue(r, c, 'H', clue)

            if "cells" in h:
                coords = [tuple(pos) for pos in h["cells"]]
            else:
                length = h["length"]
                coords = [(r, c + i) for i in range(1, length + 1)]

            run_cells = [self._get_or_create_cell(cr, cc) for cr, cc in coords]
            run = RunConstraint(direction='H', target_sum=clue, cells=run_cells)
            self.runs.append(run)
            for cell in run_cells:
                self.cell_runs.setdefault(cell, []).append(run)

        # 2. Nạp các ràng buộc hàng dọc (Vertical Clues)
        for v in data.get("vertical_clues", []):
            r, c, clue = v["r"], v["c"], v["clue"]
            self._record_clue(r, c, 'V', clue)

            if "cells" in v:
                coords = [tuple(pos) for pos in v["cells"]]
            else:
                length = v["length"]
                coords = [(r + i, c) for i in range(1, length + 1)]

            run_cells = [self._get_or_create_cell(cr, cc) for cr, cc in coords]
            run = RunConstraint(direction='V', target_sum=clue, cells=run_cells)
            self.runs.append(run)
            for cell in run_cells:
                self.cell_runs.setdefault(cell, []).append(run)

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
        """
        Lấy tập hợp tất cả các ô chia sẻ chung ít nhất một Run (ngang hoặc dọc) với cell.
        Dùng cho AC-3 và Heuristic LCV.
        """
        neighbors = set()
        for run in self.cell_runs.get(cell, []):
            for other in run.cells:
                if other != cell:
                    neighbors.add(other)
        return neighbors

    def validate_puzzle_integrity(self) -> bool:
        """
        Kiểm tra tính nhất quán toàn vẹn của đề bài:
        Tổng tất cả các Clue hàng ngang phải bằng Tổng tất cả các Clue hàng dọc.
        """
        sum_h = sum(run.target_sum for run in self.runs if run.direction == 'H')
        sum_v = sum(run.target_sum for run in self.runs if run.direction == 'V')
        is_valid = (sum_h == sum_v)
        return is_valid

    def get_clue_sums(self) -> Tuple[int, int]:
        """Trả về (Tổng ngang, Tổng dọc) để in báo cáo."""
        sum_h = sum(run.target_sum for run in self.runs if run.direction == 'H')
        sum_v = sum(run.target_sum for run in self.runs if run.direction == 'V')
        return sum_h, sum_v

    def is_solved(self) -> bool:
        """
        Kiểm tra trạng thái nghiệm: Tất cả các biến đã gán và mọi ràng buộc Run đều thỏa mãn.
        """
        if not all(cell.is_assigned for cell in self.variables.values()):
            return False
        return all(run.is_satisfied() for run in self.runs)

    def get_solution_grid(self) -> Dict[Tuple[int, int], int]:
        """Lấy dict ánh xạ tọa độ (r, c) -> giá trị nghiệm đã điền."""
        return {pos: cell.value for pos, cell in self.variables.items() if cell.is_assigned}

    def reset(self) -> None:
        """Đặt lại trạng thái các ô về ban đầu."""
        for cell in self.variables.values():
            cell.unassign()
            cell.domain = set(range(1, 10))
