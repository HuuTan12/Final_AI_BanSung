"""
Module: constraint.py
Mô tả: Định nghĩa ràng buộc Run (nhóm các ô trắng liên tiếp theo hàng hoặc cột kèm tổng clue).
Bao gồm 2 ràng buộc cốt lõi:
1. Ràng buộc Tổng (Sum Constraint): Tổng các ô bằng giá trị Clue.
2. Ràng buộc Khác nhau (AllDifferent Constraint): Các chữ số từ 1..9 không được lặp lại trong cùng một Run.
"""

import itertools
from functools import lru_cache
from typing import List, Set, Tuple
from task3_kakuro.csp.variable import Cell


class RunConstraint:
    """
    Ràng buộc của một dãy ô trắng liên tiếp theo hàng hoặc cột có ô Clue đứng đầu.
    """

    def __init__(self, direction: str, target_sum: int, cells: List[Cell]):
        self.direction = direction  # 'H' (Ngang) hoặc 'V' (Dọc)
        self.target_sum = target_sum # số clue  
        self.cells = cells # danh sách các ô trong run
        self.length = len(cells) # số lượng ô

    @staticmethod
    @lru_cache(maxsize=512)
    def get_valid_combinations(target_sum: int, length: int) -> List[Tuple[int, ...]]:
        """
        Sinh trước tất cả các bộ số phân biệt gồm length chữ số từ 1..9 có tổng bằng target_sum.
        Ví dụ: Sum = 4, Length = 2 -> Chỉ có bộ (1, 3).
        """
        if length < 1 or length > 9:
            return []
        valid_combos = []
        for combo in itertools.combinations(range(1,10),length):
            if sum(combo) == target_sum:
                valid_combos.append(combo)
        return valid_combos


        
        

    def is_satisfied(self) -> bool:
        """
        Kiểm tra ràng buộc khi tất cả các ô trong Run đã được gán giá trị:
        Tổng các ô == target_sum và các giá trị đôi một khác nhau.
        """
        vals = []
        for c in self.cells:
            if not c.is_assigned:  # Nếu còn ô chưa điền thì chưa thể coi là hoàn thành
               return False
            vals.append(c.value)
        # Thỏa mãn khi: đủ số lượng, không có số trùng và tổng đúng bằng target_sum
        return len(vals) == self.length and len(set(vals)) == self.length and sum(vals) == self.target_sum

    def is_partially_valid(self) -> bool:
        """
        Kiểm tra ràng buộc cục bộ khi một số ô đã được gán:
        Không có số trùng lặp và tổng tạm thời chưa vượt quá target_sum.
        """
        assigned_vals = [] #ds các ô đã điền
        unassigned_count = 0 # còn trống
        for c in self.cells:
            if c.is_assigned:
                assigned_vals.append(c.value)
            else:
                unassigned_count += 1

        # 1. Nếu các ô vừa điền bị trùng số -> lỗi
        if len(assigned_vals) != len(set(assigned_vals)):
            return False

        current_sum = sum(assigned_vals)
        # 2. Nếu tổng các ô đã điền vượt quá target_sum -> lỗi
        if current_sum > self.target_sum:
            return False

        # Nếu tất cả đã điền xong thì kiểm tra tổng có vừa khớp không
        if unassigned_count == 0:
            return current_sum == self.target_sum

        # 3. Kỹ thuật Cận Trên - Cận Dưới (Bound Pruning):
        remaining_sum = self.target_sum - current_sum
        used_digits = set(assigned_vals)
        # Lấy các số còn lại trong tập {1..9} chưa bị dùng
        available_digits = [d for d in range(1, 10) if d not in used_digits]

        if len(available_digits) < unassigned_count:
            return False

        # Tổng nhỏ nhất có thể tạo ra từ các số còn lại
        min_possible = sum(available_digits[:unassigned_count])
        # Tổng lớn nhất có thể tạo ra từ các số còn lại
        max_possible = sum(available_digits[-unassigned_count:])

        # Phần tổng còn thiếu BẮT BUỘC phải nằm trong khoảng [min_possible, max_possible]
        return min_possible <= remaining_sum <= max_possible
