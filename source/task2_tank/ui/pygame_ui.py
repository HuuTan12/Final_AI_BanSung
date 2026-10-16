"""
Module: pygame_ui.py
Mô tả: Giao diện đồ họa người dùng bằng thư viện PyGame cho trò chơi Tank Battle.
Thực hiện yêu cầu 3 (0.5 điểm) của Task 2:
- Hiển thị trực quan bàn cờ, Tank, Base, Wall, đường đạn di chuyển.
- Bảng điều khiển: Thanh máu HP, số nodes duyệt, thời gian suy nghĩ của từng Agent.
- Chế độ: Play, Pause, Step-by-step, điều chỉnh tốc độ, chọn Agent thi đấu.
"""

from typing import Optional
from task2_tank.engine.game_state import GameState
from task2_tank.agents.base_agent import BaseAgent


class TankGameGUI:
    """
    Trình diễn đồ họa PyGame cho trận chiến Tank Battle giữa 2 Agent AI.
    """

    def __init__(self, cell_size: int = 40, fps: int = 30):
        self.cell_size = cell_size
        self.fps = fps
        self.is_paused: bool = False
        self.step_mode: bool = False

    def init_display(self, width_cells: int, height_cells: int) -> None:
        """Khởi tạo cửa sổ PyGame, font chữ, icon và bảng màu."""
        pass

    def render(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """
        Vẽ toàn bộ khung hình: Lưới chiến trường + Bảng thống kê (Metrics Dashboard).
        """
        pass

    def handle_events(self) -> bool:
        """
        Xử lý sự kiện bàn phím/chuột: Phím Space (Pause/Resume), Phím mũi tên (Step), Esc (Thoát).
        Trả về True nếu tiếp tục, False nếu đóng cửa sổ.
        """
        pass
