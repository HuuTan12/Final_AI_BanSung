"""
Module: propagators.py
Mô tả: Cài đặt các kỹ thuật lan truyền ràng buộc (Constraint Propagation):
- AC-3 (Arc Consistency 3) / Generalized Arc Consistency (GAC) cho các ràng buộc Run
- Forward Checking (FC)
Giúp thu hẹp miền giá trị của các biến và phát hiện nhánh cụt sớm.
"""

from typing import Set, Tuple, List, Dict
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.csp.variable import Cell
from task3_kakuro.csp.constraint import RunConstraint
from task3_kakuro.solver.tracer import SolverTracer, EventType


class ConstraintPropagator:
    """
    Bộ lan truyền ràng buộc cho bài toán CSP Kakuro.
    """

    def __init__(self, tracer: SolverTracer = None):
        self.tracer = tracer

    def initial_filtering(self, csp: KakuroCSP) -> bool:
        """
        Khởi tạo miền giá trị bằng cách giao các tổ hợp hợp lệ (Valid Combinations)
        của Run ngang và Run dọc đi qua từng ô.
        """
        pass

    def ac3(self, csp: KakuroCSP, queue: List[Tuple[Cell, RunConstraint]] = None) -> bool:
        """
        Thuật toán AC-3 mở rộng cho bài toán Kakuro.
        Trả về False nếu phát hiện một biến bị rỗng miền giá trị (Domain Wipeout).
        """
        pass

    def forward_check(self, csp: KakuroCSP, var: Cell, val: int) -> Dict[Cell, Set[int]]:
        """
        Forward Checking: Loại bỏ giá trị val khỏi miền giá trị các ô chưa gán trong cùng Run.
        Trả về dict các giá trị bị tỉa để hỗ trợ hoàn tác (undo).
        """
        pass
