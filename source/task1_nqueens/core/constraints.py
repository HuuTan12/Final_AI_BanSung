"""
Module: constraints.py
Mô tả: Khám phá các ràng buộc vị trí quân hậu và chuyển đổi thành dạng chuẩn hội (CNF clauses).
Thực hiện yêu cầu 1 (1.0 điểm) của Task 1.
"""

from typing import List
from task1_nqueens.core.problem import NQueensProblem


class ConstraintGenerator:
    """
    Lớp chịu trách nhiệm xây dựng hệ thống ràng buộc logic mệnh đề (Propositional Logic)
    cho bài toán N-Queens và chuyển đổi sang các mệnh đề CNF (Conjunctive Normal Form).
    """

    def __init__(self, problem: NQueensProblem):
        self.problem = problem
        self.n = problem.n

    def generate_row_clauses(self) -> List[List[int]]:
        """
        Sinh các mệnh đề ràng buộc cho các hàng:
        1. Mỗi hàng có ít nhất 1 quân hậu (At-least-one: ALO).
        2. Mỗi hàng có nhiều nhất 1 quân hậu (At-most-one: AMO - pairwise encoding).
        """
        pass

    def generate_col_clauses(self) -> List[List[int]]:
        """
        Sinh các mệnh đề ràng buộc cho các cột:
        1. Mỗi cột có ít nhất 1 quân hậu (At-least-one: ALO).
        2. Mỗi cột có nhiều nhất 1 quân hậu (At-most-one: AMO - pairwise encoding).
        """
        pass

    def generate_diagonal_clauses(self) -> List[List[int]]:
        """
        Sinh các mệnh đề ràng buộc cho tất cả các đường chéo chính (r - c = k)
        và đường chéo phụ (r + c = k):
        Mỗi đường chéo có nhiều nhất 1 quân hậu (At-most-one: AMO).
        """
        pass

    def generate_all_cnf(self) -> List[List[int]]:
        """
        Tổng hợp tất cả các mệnh đề CNF của bài toán N-Queens để nạp vào SAT solver.
        """
        pass

    def get_theoretical_clause_count(self) -> int:
        """
        Tính số lượng mệnh đề lý thuyết để đối chiếu và kiểm tra tính toàn vẹn của bộ sinh:
        Formula: 2N + N^2*(N-1) + N*(N-1)*(2N-1)/3
        """
        pass
