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
        1. Đo thời gian bắt đầu.
        2. Tiền xử lý Initial Filtering & AC-3 để thu hẹp domain tối đa trước khi duyệt.
        3. Bắt đầu đệ quy _backtrack(csp).
        4. Ghi nhận kết quả: thời gian, số nút đã duyệt, số lần backtrack.
        """
        start_time = time.time()
        self.nodes_explored = 0
        self.backtracks = 0
        # Bước 1: Lọc miền giá trị ban đầu (giao các tổ hợp của run ngang và run dọc)
        if not self.propagator.initial_filtering(csp):
            exec_time = time.time() - start_time
            return KakuroSolveResult(False, exec_time, self.nodes_explored, self.backtracks, None)
        # Bước 2: Nếu bật AC-3 thì chạy lan truyền ràng buộc toàn diện trước khi quay lui
        if self.use_ac3:
            if not self.propagator.ac3(csp):
                exec_time = time.time() - start_time
                return KakuroSolveResult(False, exec_time, self.nodes_explored, self.backtracks, None)
        # Bước 3: Đệ quy tìm kiếm
        is_solved = self._backtrack(csp)
        exec_time = time.time() - start_time
        solution_grid = csp.get_solution_grid() if is_solved else None
        return KakuroSolveResult(
            is_solved=is_solved,
            execution_time=exec_time,
            nodes_explored=self.nodes_explored,
            backtracks=self.backtracks,
            solution_grid=solution_grid
        )

    def _backtrack(self, csp: KakuroCSP) -> bool:
        """
        Đệ quy quay lui (Backtracking Search):
        1. Kiểm tra điều kiện dừng: Nếu tất cả ô đã gán -> Thành công!
        2. Chọn biến tiếp theo dùng Heuristic MRV (Minimum Remaining Values).
        3. Chọn thứ tự giá trị để thử dùng Heuristic LCV (Least Constraining Value).
        4. Với mỗi giá trị:
           - Gán giá trị vào ô.
           - Kiểm tra tính hợp lệ cục bộ (is_partially_valid).
           - Tỉa miền giá trị láng giềng (Forward Checking).
           - Nếu hợp lệ -> Gọi đệ quy tiếp tục.
           - Nếu thất bại -> Hoàn tác (Undo) và thử giá trị khác (Backtrack).
        """
        # Điều kiện dừng: Nếu đã gán hết tất cả các ô
        if all(cell.is_assigned for cell in csp.variables.values()):
            return csp.is_solved()

        # Chọn ô trắng tiếp theo bằng MRV (kết hợp Degree tie-breaker)
        var = CSPHeuristics.select_unassigned_variable(csp, use_mrv=self.use_mrv, use_degree=True)
        if var is None:
            return False

        # Sắp xếp các giá trị trong domain của ô theo thứ tự LCV
        ordered_values = CSPHeuristics.order_domain_values(csp, var, use_lcv=self.use_lcv)

        for val in ordered_values:
            self.nodes_explored += 1

            # Gán thử giá trị
            var.assign(val)
            if self.tracer:
                self.tracer.emit(EventType.ASSIGN, cell_pos=var.pos, value=val, message=f"Assign {val} to {var.pos}")

            # Kiểm tra xem các Run đi qua ô này có vi phạm không
            runs_valid = all(run.is_partially_valid() for run in csp.cell_runs.get(var, []))

            if runs_valid:
                # Tỉa nhánh miền giá trị các ô láng giềng (Forward Checking)
                pruned = self.propagator.forward_check(csp, var, val)

                # Nếu không bị bế tắc (Domain Wipeout)
                if pruned is not None:
                    # Gọi đệ quy đi tiếp
                    if self._backtrack(csp):
                        return True

                    # Hoàn tác lại miền giá trị đã bị tỉa khi quay lui
                    for neighbor, removed_vals in pruned.items():
                        neighbor.domain.update(removed_vals)

            # Nếu nhánh này thất bại -> Hoàn tác phép gán (BACKTRACK)
            var.unassign()
            self.backtracks += 1
            if self.tracer:
                self.tracer.emit(EventType.BACKTRACK, cell_pos=var.pos, value=val, message=f"Backtrack from {var.pos}")

        return False