"""
Module: base_solver.py
Mô tả: Lớp trừu tượng định nghĩa giao diện chung cho mọi thuật toán giải N-Queens.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dataclasses import dataclass


@dataclass
class SolverResult:
    """
    Cấu trúc dữ liệu lưu kết quả chạy thuật toán để phục vụ báo cáo và thí nghiệm.
    """
    is_solved: bool
    solution: Optional[List[int]]
    execution_time: float
    num_clauses: Optional[int] = None      # Dành cho SAT Solver
    steps_taken: Optional[int] = None       # Dành cho Min-Conflicts
    restarts: Optional[int] = None          # Dành cho Min-Conflicts


class BaseSolver(ABC):
    """
    Lớp cơ sở trừu tượng cho tất cả các solver bài toán N-Queens.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def solve(self, n: int) -> SolverResult:
        """
        Thực thi thuật toán giải bài toán N-Queens kích thước n x n.
        Trả về đối tượng SolverResult.
        """
        pass
