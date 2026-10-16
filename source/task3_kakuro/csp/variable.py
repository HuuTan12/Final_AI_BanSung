"""
Module: variable.py
Mô tả: Định nghĩa biến CSP Kakuro đại diện cho mỗi ô trắng (White Cell).
Thuộc tính gồm tọa độ (r, c), miền giá trị khả dĩ (Domain: 1..9), và giá trị hiện tại được gán.
"""

from typing import Set, Optional


class Cell:
    """
    Biến trong mô hình CSP của Kakuro:
    - pos: (row, col)
    - domain: Tập các giá trị hợp lệ còn lại {1..9}
    - value: Giá trị đã gán (None nếu chưa gán)
    """

    def __init__(self, r: int, c: int):
        self.r = r
        self.c = c
        self.pos = (r, c)
        self.domain: Set[int] = set(range(1, 10))
        self.value: Optional[int] = None

    @property
    def is_assigned(self) -> bool:
        return self.value is not None

    def assign(self, val: int) -> None:
        self.value = val

    def unassign(self) -> None:
        self.value = None

    def __repr__(self) -> str:
        return f"Cell({self.r},{self.c}, val={self.value}, d_size={len(self.domain)})"
