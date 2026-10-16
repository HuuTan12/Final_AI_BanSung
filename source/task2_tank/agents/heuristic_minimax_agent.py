"""
Module: heuristic_minimax_agent.py
Mô tả: Cấu hình 3 - Heuristic Minimax Search (Lecture 07).
Giới hạn độ sâu d và sử dụng hàm heuristic TankEvaluator tại các lá (leaf nodes).
"""

from typing import Tuple
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class HeuristicMinimaxAgent(BaseAgent):
    """
    Agent Heuristic Minimax: Cho phép tìm kiếm trong thời gian thực
    với hàm đánh giá trạng thái thay cho duyệt toàn bộ tới terminal state.
    """

    def __init__(self, depth: int = 4, evaluator: TankEvaluator = None):
        super().__init__(name=f"Heuristic Minimax (Depth {depth})")
        self.depth = depth
        self.evaluator = evaluator if evaluator is not None else TankEvaluator()

    def choose_action(self, state: GameState, player_id: int) -> Action:
        pass

    def _heuristic_minimax(self, state: GameState, depth: int, is_maximizing: bool,
                           player_id: int) -> Tuple[float, Action]:
        pass
