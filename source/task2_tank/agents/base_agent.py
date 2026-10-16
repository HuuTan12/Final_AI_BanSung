"""
Module: base_agent.py
Mô tả: Lớp cơ sở trừu tượng cho tất cả các AI Agent điều khiển Tank.
Đóng vai trò là Interface chuẩn chung để các nhóm sinh viên khác có thể nạp thuật toán vào thi đấu.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


@dataclass
class SearchStats:
    """Thống kê hiệu năng tìm kiếm của Agent trong mỗi lượt đi."""
    explored_nodes: int = 0
    prune_count: int = 0
    search_depth: int = 0
    execution_time: float = 0.0


class BaseAgent(ABC):
    """
    Interface Agent chuẩn bắt buộc cho mọi thuật toán điều khiển Tank.
    """

    def __init__(self, name: str):
        self.name = name
        self.stats = SearchStats()

    @abstractmethod
    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Giao diện cốt lõi: Nhận trạng thái GameState và ID người chơi (0 hoặc 1),
        trả về 1 trong 6 hành động Action hợp lệ.
        """
        pass

    def reset_stats(self) -> None:
        """Đặt lại bộ đếm thống kê trước mỗi lượt suy luận."""
        self.stats = SearchStats()
