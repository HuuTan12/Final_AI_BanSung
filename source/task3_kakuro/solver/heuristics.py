"""
Module: heuristics.py
Mô tả: Các kỹ thuật Heuristic tối ưu hóa tìm kiếm CSP từ Lecture 08:
- Thứ tự chọn biến: MRV (Minimum Remaining Values), Degree Heuristic làm tiêu chí phụ (tie-break).
- Thứ tự chọn giá trị: LCV (Least Constraining Value).
"""

from typing import List
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.csp.variable import Cell


class CSPHeuristics:
    """
    Tập hợp các heuristic định hướng tìm kiếm cho solver Kakuro.
    """

    @staticmethod
    def select_unassigned_variable_mrv(csp: KakuroCSP) -> Cell:
        """
        Heuristic MRV (Minimum Remaining Values):
        Chọn ô chưa được gán có kích thước miền giá trị (domain size) nhỏ nhất.
        Nếu hòa, ưu tiên ô tham gia vào nhiều ràng buộc có độ dài ngắn hơn (Degree tie-break).
        """
        pass

    @staticmethod
    def order_domain_values_lcv(csp: KakuroCSP, var: Cell) -> List[int]:
        """
        Heuristic LCV (Least Constraining Value):
        Sắp xếp các giá trị trong domain của var theo thứ tự ít loại trừ giá trị
        trong miền của các biến láng giềng nhất.
        """
        pass
