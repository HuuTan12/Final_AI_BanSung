"""
Module: alphabeta_agent.py
Mô tả: Cấu hình 2 - Thuật toán Alpha-Beta Pruning (Lecture 07).
Cắt tỉa các nhánh cây trò chơi không ảnh hưởng đến quyết định tối ưu.
"""

from typing import Tuple
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class AlphaBetaAgent(BaseAgent):
    """
    Agent điều khiển Tank sử dụng thuật toán Minimax kết hợp cắt tỉa Alpha-Beta.
    """

    def __init__(self, depth: int = 3):
        super().__init__(name=f"Alpha-Beta (Depth {depth})")
        self.depth = depth

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Tìm kiếm nước đi tối ưu có áp dụng cắt tỉa Alpha-Beta.
        """
        pass

    def _alphabeta(self, state: GameState, depth: int, alpha: float, beta: float,
                   is_maximizing: bool, player_id: int) -> Tuple[float, Action]:
        """
        Cắt tỉa:
        - Max node: Cập nhật alpha, cắt nhánh khi val >= beta
        - Min node: Cập nhật beta, cắt nhánh khi val <= alpha
        """
        pass
