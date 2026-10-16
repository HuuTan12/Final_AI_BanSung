"""
Module: minimax_agent.py
Mô tả: Cấu hình 1 - Thuật toán Minimax Search thuần (Lecture 07).
Khám phá đầy đủ cây trạng thái đến trạng thái kết thúc (hoặc độ sâu cố định).
"""

from typing import Tuple
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class MinimaxAgent(BaseAgent):
    """
    Agent điều khiển Tank sử dụng thuật toán Minimax cơ bản.
    """

    def __init__(self, depth: int = 3):
        super().__init__(name=f"Minimax (Depth {depth})")
        self.depth = depth

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Tìm kiếm nước đi tối ưu bằng Minimax Search.
        """
        pass

    def _minimax(self, state: GameState, depth: int, is_maximizing: bool, player_id: int) -> Tuple[float, Action]:
        """
        Đệ quy duyệt cây trò chơi:
        - Tầng Max: Tank của player_id
        - Tầng Min: Tank của đối thủ (1 - player_id)
        """
        pass
