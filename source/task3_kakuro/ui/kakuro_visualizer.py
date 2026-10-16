"""
Module: kakuro_visualizer.py
Mô tả: Giao diện người dùng (UI) trực quan hóa giải Kakuro bằng PyGame hoặc Tkinter.
Thực hiện yêu cầu 3 (1.0 điểm) của Task 3:
1. Trực quan hóa miền giá trị (Domains): Hiển thị các số khả dĩ (1..9) dạng bút chì nhỏ trong ô chưa điền.
2. Trực quan hóa lan truyền ràng buộc (Constraint Propagation): Đổi màu các giá trị bị tỉa (Pruned values).
3. Trực quan hóa tìm kiếm quay lui (Backtracking Search): Hiển thị quá trình gán, thử sai và quay lui (Backtrack).
"""

from typing import List
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.tracer import SolverTracer, SolverEvent


class KakuroVisualizer:
    """
    Trình diễn đồ họa trực quan hóa quá trình giải bài toán Kakuro CSP.
    """

    def __init__(self, csp: KakuroCSP, tracer: SolverTracer):
        self.csp = csp
        self.tracer = tracer
        self.current_event_idx: int = 0
        self.is_playing: bool = False
        self.playback_speed: float = 1.0  # seconds per step

    def run(self) -> None:
        """
        Khởi tạo cửa sổ giao diện chính và vòng lặp đồ họa.
        """
        pass

    def draw_board(self) -> None:
        """
        Vẽ lưới Kakuro:
        - Ô đen chứa Clue (chia đôi chéo: Clue Dọc \\ Clue Ngang).
        - Ô trắng: Hiển thị giá trị đã gán (số lớn) hoặc miền giá trị Domain (lưới 3x3 nhỏ).
        """
        pass

    def step_forward(self) -> None:
        """Thực thi sự kiện tiếp theo trong danh sách tracer.events."""
        pass

    def step_backward(self) -> None:
        """Hoàn tác lại sự kiện trước đó."""
        pass
