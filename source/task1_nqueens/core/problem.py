"""
Module: problem.py
Mô tả: Định nghĩa lớp NQueensProblem đại diện cho bài toán N-Queens theo chuẩn OOP.
Quản lý kích thước bàn cờ, chuyển đổi định danh biến Propositional Logic (1-based index)
và kiểm tra tính hợp lệ của nghiệm.
"""

from typing import List, Tuple, Optional


class NQueensProblem:
    """
    Lớp biểu diễn bài toán N-Queens.
    
    Thuộc tính:
        n (int): Kích thước bàn cờ N x N (Yêu cầu đề: N >= 4).
    """

    def __init__(self, n: int):
        if n < 4:
            raise ValueError(f"Đề bài yêu cầu N >= 4. Giá trị hiện tại: N = {n}")
        self.n = n

    def to_var(self, r: int, c: int) -> int:
        """
        Chuyển tọa độ ô cờ (r, c) thành định danh biến nguyên dương (1-based ID) cho SAT solver.
        Công thức: id = r * N + c + 1
        """
        pass

    def to_coords(self, var_id: int) -> Tuple[int, int]:
        """
        Chuyển ngược định danh biến SAT (1-based ID) về tọa độ (r, c) trên bàn cờ.
        """
        pass

    def is_valid_solution(self, queen_positions: List[int]) -> bool:
        """
        Kiểm tra trạng thái nghiệm dạng queen_positions[col] = row có hợp lệ hay không
        (không có bất kỳ 2 quân hậu nào tấn công nhau theo hàng, cột hoặc đường chéo).
        """
        pass

    def display(self, queen_positions: List[int]) -> None:
        """
        Hiển thị trực quan bàn cờ N x N với các quân hậu 'Q' và ô trống '.'.
        """
        pass
