"""
alphabeta_agent.py - Configuration 2: Alpha-Beta Pruning Search
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements Minimax with Alpha-Beta Pruning (Lecture 07 - Slide 16-25).
    Prunes provably sub-optimal subtrees whenever v >= beta (at MAX)
    or v <= alpha (at MIN), returning identical decisions to Minimax
    while evaluating significantly fewer nodes.
"""

import time
from typing import Tuple, Optional
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action
from task2_tank.engine.rules import GameRules


from task2_tank.agents.evaluator import TankEvaluator


class AlphaBetaAgent(BaseAgent):
    """
    Agent that decides actions using Minimax with Alpha-Beta Pruning.
    """

    def __init__(self, depth: int = 3):
        super().__init__(name=f"Alpha-Beta (Depth {depth})")
        self.depth = depth

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Chooses optimal action using Alpha-Beta search.
        """
        self.reset_stats()
        self.stats.search_depth = self.depth
        start_time = time.perf_counter()

        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return Action.STAY
        if len(legal_actions) == 1:
            return legal_actions[0]

        best_score = float("-inf")
        best_action = legal_actions[0]
        alpha = float("-inf")
        beta = float("inf")

        for action in legal_actions:
            self.stats.explored_nodes += 1
            successor = GameRules.apply_action(state, action)
            score = self._min_value(successor, self.depth - 1, alpha, beta, player_id)

            if score > best_score + 1e-4:
                best_score = score
                best_action = action
            elif abs(score - best_score) <= 1e-4:
                if TankEvaluator.action_tactical_priority(state, action, player_id) > TankEvaluator.action_tactical_priority(state, best_action, player_id):
                    best_score = score
                    best_action = action
            alpha = max(alpha, best_score)

        self.stats.execution_time = time.perf_counter() - start_time
        return best_action

    def _max_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int) -> float:
        """
        MAX ply with alpha-beta pruning.
        """
        self.stats.explored_nodes += 1

        if state.is_terminal():
            return state.get_utility(player_id)
        if depth <= 0:
            return state.get_utility(player_id)

        v = float("-inf")
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return state.get_utility(player_id)

        for action in legal_actions:
            successor = GameRules.apply_action(state, action)
            v = max(v, self._min_value(successor, depth - 1, alpha, beta, player_id))
            if v >= beta:
                self.stats.prune_count += 1
                return v  # Beta cut-off
            alpha = max(alpha, v)

        return v

    def _min_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int) -> float:
        """
        MIN ply with alpha-beta pruning.
        """
        self.stats.explored_nodes += 1

        if state.is_terminal():
            return state.get_utility(player_id)
        if depth <= 0:
            return state.get_utility(player_id)

        opponent_id = 1 - player_id
        v = float("inf")
        legal_actions = state.get_legal_actions(opponent_id)
        if not legal_actions:
            return state.get_utility(player_id)

        for action in legal_actions:
            successor = GameRules.apply_action(state, action)
            v = min(v, self._max_value(successor, depth - 1, alpha, beta, player_id))
            if v <= alpha:
                self.stats.prune_count += 1
                return v  # Alpha cut-off
            beta = min(beta, v)

        return v
