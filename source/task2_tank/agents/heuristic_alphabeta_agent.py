"""
Module: heuristic_alphabeta_agent.py
Mô tả: Cấu hình 4 - Heuristic Minimax kết hợp Alpha-Beta Pruning (Lecture 07).
Cấu hình tối ưu toàn diện nhất, cho phép tìm kiếm sâu hơn trong cùng một quỹ thời gian thực thi.
"""

from typing import Tuple
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class HeuristicAlphaBetaAgent(BaseAgent):
    """
    Agent Heuristic Alpha-Beta: Kết hợp hàm đánh giá heuristic tại lá và cắt nhánh Alpha-Beta.
    """

    def __init__(self, depth: int = 5, evaluator: TankEvaluator = None):
        super().__init__(name=f"Heuristic Alpha-Beta (Depth {depth})")
        self.depth = depth
        self.evaluator = evaluator if evaluator is not None else TankEvaluator()

    def choose_action(self, state: GameState, player_id: int) -> Action:
        pass

    def _heuristic_alphabeta(self, state: GameState, depth: int, alpha: float, beta: float,
                             is_maximizing: bool, player_id: int) -> Tuple[float, Action]:
        pass
