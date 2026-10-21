"""
Module: propagators.py
Mô tả: Cài đặt các kỹ thuật lan truyền ràng buộc (Constraint Propagation):
- AC-3 (Arc Consistency 3) / Generalized Arc Consistency (GAC) cho các ràng buộc Run
- Forward Checking (FC)
- Initial Filtering: Lấy giao các tổ hợp số khả dĩ ban đầu
Giúp thu hẹp miền giá trị của các biến và phát hiện nhánh cụt sớm.
"""

from typing import Set, Tuple, List, Dict, Optional
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.csp.variable import Cell
from task3_kakuro.csp.constraint import RunConstraint
from task3_kakuro.solver.tracer import SolverTracer, EventType


class ConstraintPropagator:
    """
    Bộ lan truyền ràng buộc cho bài toán CSP Kakuro.
    """

    def __init__(self, tracer: Optional[SolverTracer] = None):
        self.tracer = tracer

    def initial_filtering(self, csp: KakuroCSP) -> bool:
        """
        Khởi tạo miền giá trị bằng cách giao các tổ hợp hợp lệ (Valid Combinations)
        của Run ngang và Run dọc đi qua từng ô.
        
        Trả về:
        - True nếu tất cả các ô đều có domain hợp lệ.
        - False nếu xuất hiện ô bị rỗng domain (bàn cờ không thể giải).
        """
        for cell in csp.variables.values():
            runs = csp.cell_runs.get(cell, [])
            if not runs:
                continue

            # Lấy giao tập các số khả dĩ từ tất cả các Run đi qua ô này
            allowed_vals = set(range(1, 10))
            for run in runs:
                allowed_vals &= run.get_possible_digits()

            # Tỉa bớt các giá trị không hợp lệ khỏi domain hiện tại
            pruned = cell.domain - allowed_vals
            if pruned:
                cell.domain &= allowed_vals
                if self.tracer:
                    self.tracer.add_event(
                        EventType.DOMAIN_REDUCED,
                        cell=cell,
                        removed_values=pruned,
                        reason="Initial Filtering"
                    )

            # Nếu bất kỳ ô nào có domain rỗng -> Bàn cờ vô nghiệm
            if not cell.domain:
                return False

        return True

    def ac3(self, csp: KakuroCSP, queue: Optional[List[Tuple[Cell, RunConstraint]]] = None) -> bool:
        """
        Thuật toán AC-3 / GAC mở rộng cho bài toán Kakuro.
        Duyệt hàng đợi các cặp (Cell, RunConstraint) để duy trì tính nhất quán.
        
        Trả về False nếu phát hiện một biến bị rỗng miền giá trị (Domain Wipeout).
        """
        if queue is None:
            work_queue: List[Tuple[Cell, RunConstraint]] = []
            for cell in csp.variables.values():
                for run in csp.cell_runs.get(cell, []):
                    work_queue.append((cell, run))
        else:
            work_queue = list(queue)

        while work_queue:
            cell, run = work_queue.pop(0)

            revised, removed = self._revise(cell, run)
            if revised:
                if self.tracer and removed:
                    self.tracer.add_event(
                        EventType.DOMAIN_REDUCED,
                        cell=cell,
                        removed_values=removed,
                        reason=f"AC3-GAC ({run.direction} Clue {run.target_sum})"
                    )

                if not cell.domain:
                    return False  # Domain Wipeout -> Nhánh cụt

                # Thêm các ô láng giềng bị ảnh hưởng vào hàng đợi để tiếp tục lan truyền
                for other_run in csp.cell_runs.get(cell, []):
                    for other_cell in other_run.cells:
                        if other_cell != cell and not other_cell.is_assigned:
                            item = (other_cell, other_run)
                            if item not in work_queue:
                                work_queue.append(item)

        return True

    def _revise(self, cell: Cell, run: RunConstraint) -> Tuple[bool, Set[int]]:
        """
        Hàm bổ trợ cho AC-3: Loại bỏ những giá trị v trong cell.domain không 
        nằm trong bất kỳ tổ hợp hợp lệ nào của Run.
        """
        revised = False
        removed = set()
        possible_digits = run.get_possible_digits()

        for val in list(cell.domain):
            if val not in possible_digits:
                cell.domain.remove(val)
                removed.add(val)
                revised = True

        return revised, removed

    def forward_check(self, csp: KakuroCSP, var: Cell, val: int) -> Optional[Dict[Cell, Set[int]]]:
        """
        Forward Checking: Khi var được gán val, loại bỏ các giá trị không hợp lệ
        khỏi miền giá trị của các ô chưa gán thuộc cùng Run.
        
        Trả về:
        - Dict[Cell, Set[int]]: Tập các giá trị bị tỉa (dùng để hoàn tác - backtrack).
        - None: Nếu xảy ra bế tắc (Domain Wipeout).
        """
        pruned: Dict[Cell, Set[int]] = {}

        for run in csp.cell_runs.get(var, []):
            possible_digits = run.get_possible_digits()

            for neighbor in run.cells:
                if neighbor != var and not neighbor.is_assigned:
                    # Loại bỏ các giá trị không còn khả dĩ
                    invalid_vals = {v for v in neighbor.domain if v == val or v not in possible_digits}

                    if invalid_vals:
                        if neighbor not in pruned:
                            pruned[neighbor] = set()

                        pruned[neighbor].update(invalid_vals)
                        neighbor.domain -= invalid_vals

                        if self.tracer:
                            self.tracer.add_event(
                                EventType.DOMAIN_REDUCED,
                                cell=neighbor,
                                removed_values=invalid_vals,
                                reason=f"ForwardCheck from ({var.r}, {var.c})={val}"
                            )

                        # Nếu 1 ô láng giềng bị rỗng domain -> Bế tắc
                        if not neighbor.domain:
                            return None

        return pruned