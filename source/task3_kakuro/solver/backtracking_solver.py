"""
Module: backtracking_solver.py
Mô tả: Bộ giải Kakuro CSP kết hợp Backtracking Search với Lan truyền ràng buộc (AC-3 / MAC)
và các Heuristic (MRV, LCV).
Thực hiện yêu cầu 2 (1.0 điểm) của Task 3.
"""

from typing import Optional, Dict
import time
from dataclasses import dataclass
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.propagators import ConstraintPropagator
from task3_kakuro.solver.heuristics import CSPHeuristics
from task3_kakuro.solver.tracer import SolverTracer, EventType


@dataclass
class KakuroSolveResult:
    is_solved: bool
    execution_time: float
    nodes_explored: int
    backtracks: int
    solution_grid: Optional[Dict[tuple, int]] = None


class KakuroBacktrackingSolver:
    """
    Bộ giải tìm kiếm quay lui kết hợp lan truyền ràng buộc cho Kakuro.
    """

    def __init__(self, use_ac3: bool = True, use_mrv: bool = True, use_lcv: bool = True, tracer: SolverTracer = None):
        self.use_ac3 = use_ac3
        self.use_mrv = use_mrv
        self.use_lcv = use_lcv
        self.tracer = tracer
        self.propagator = ConstraintPropagator(tracer=tracer)
        self.nodes_explored = 0
        self.backtracks = 0

    def solve(self, csp: KakuroCSP) -> KakuroSolveResult:
        """
        Khởi chạy giải bài toán:
        1. Tiền xử lý lan truyền miền giá trị ban đầu (Initial Filtering & AC-3).
        2. Gọi hàm đệ quy _backtrack().
        """
        pass

    def _backtrack(self, csp: KakuroCSP) -> bool:
        """
        Đệ quy quay lui (Backtracking Search) tích hợp MRV, LCV và phát hiện thất bại sớm (MAC).
        """
        pass
