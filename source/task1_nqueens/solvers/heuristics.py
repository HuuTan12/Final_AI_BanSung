"""
Module: heuristics.py
Mô tả: Định nghĩa các Heuristic chọn biến (variable selection) cho thuật toán Min-Conflicts.
Thực hiện yêu cầu 3 (1.0 điểm) của Task 1.
"""

from abc import ABC, abstractmethod
from typing import List


class VariableSelector(ABC):
    """
    Lớp cơ sở trừu tượng cho chiến lược chọn biến bị xung đột.
    """

    @abstractmethod
    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        """
        Chọn ra 1 cột (biến) cần thay đổi giá trị từ danh sách các biến đang bị xung đột.
        """
        pass


class RandomSelector(VariableSelector):
    """
    Chiến lược Baseline chuẩn (Standard Min-Conflicts): Chọn ngẫu nhiên đều 
    một biến trong tập các biến đang bị xung đột.
    """

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        pass


class MaxConflictSelector(VariableSelector):
    """
    Heuristic đề xuất 1: Chọn biến có số lượng xung đột lớn nhất (Max-Conflict).
    Nếu có nhiều biến hòa điểm, chọn ngẫu nhiên giữa các ứng viên này để tránh chu kỳ.
    """

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        pass


class HybridTabuSelector(VariableSelector):
    """
    Heuristic đề xuất 2 (Mở rộng): Kết hợp Max-Conflict với xác suất epsilon khám phá ngẫu nhiên
    và danh sách Tabu ngắn hạn nhằm ngăn chặn hiện tượng kẹt cực tiểu cục bộ (local minima).
    """

    def __init__(self, epsilon: float = 0.1, tabu_size: int = 5):
        self.epsilon = epsilon
        self.tabu_size = tabu_size
        self.tabu_list = []

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        pass
