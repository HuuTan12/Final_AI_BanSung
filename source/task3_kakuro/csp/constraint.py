"""
Module: constraint.py
Mô tả: Định nghĩa ràng buộc Run (nhóm các ô trắng liên tiếp theo hàng hoặc cột kèm tổng clue).
Bao gồm 2 ràng buộc cốt lõi:
1. Ràng buộc Tổng (Sum Constraint): Tổng các ô bằng giá trị Clue.
2. Ràng buộc Khác nhau (AllDifferent Constraint): Các chữ số từ 1..9 không được lặp lại trong cùng một Run.
"""

from typing import List, Set, Tuple
from task3_kakuro.csp.variable import Cell


class RunConstraint:
    """
    Ràng buộc của một dãy ô trắng liên tiếp theo hàng hoặc cột có ô Clue đứng đầu.
    """

    def __init__(self, direction: str, target_sum: int, cells: List[Cell]):
        self.direction = direction  # 'H' (Ngang) hoặc 'V' (Dọc)
        self.target_sum = target_sum
        self.cells = cells
        self.length = len(cells)

    def get_valid_combinations(self) -> List[Tuple[int, ...]]:
        """
        Sinh trước tất cả các bộ số phân biệt gồm length chữ số từ 1..9 có tổng bằng target_sum.
        Ví dụ: Sum = 4, Length = 2 -> Chỉ có bộ (1, 3).
        """
        pass

    def is_satisfied(self) -> bool:
        """
        Kiểm tra ràng buộc khi tất cả các ô trong Run đã được gán giá trị:
        Tổng các ô == target_sum và các giá trị đôi một khác nhau.
        """
        pass

    def is_partially_valid(self) -> bool:
        """
        Kiểm tra ràng buộc cục bộ khi một số ô đã được gán:
        Không có số trùng lặp và tổng tạm thời chưa vượt quá target_sum.
        """
        pass
