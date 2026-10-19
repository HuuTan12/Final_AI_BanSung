"""
minimax_agent.py - Configuration 1: Pure Minimax Search
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements pure Minimax Search (Lecture 07 - Slide 10-14) for the Tank Battle game.
    Traverses the full game tree down to terminal states or a designated depth limit
    without any branch pruning.
"""

import time
from typing import Tuple, Optional
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action
from task2_tank.engine.rules import GameRules


from task2_tank.agents.evaluator import TankEvaluator


class MinimaxAgent(BaseAgent):
    """
    Agent that decides actions using the standard Minimax algorithm.
    """

    def __init__(self, depth: int = 3):
        super().__init__(name=f"Minimax (Depth {depth})")
        self.depth = depth

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Selects the optimal action using the Minimax decision rule.
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

        for action in legal_actions:
            self.stats.explored_nodes += 1
            successor = GameRules.apply_action(state, action)
            # Next ply is opponent (MIN)
            score = self._min_value(successor, self.depth - 1, player_id)
            if score > best_score + 1e-4:
                best_score = score
                best_action = action
            elif abs(score - best_score) <= 1e-4:
                if TankEvaluator.action_tactical_priority(state, action, player_id) > TankEvaluator.action_tactical_priority(state, best_action, player_id):
                    best_score = score
                    best_action = action

        self.stats.execution_time = time.perf_counter() - start_time
        return best_action

    def _max_value(self, state: GameState, depth: int, player_id: int) -> float:
        """
        MAX ply: attempts to maximize player_id's utility.
        """
        self.stats.explored_nodes += 1

        if state.is_terminal():
            return state.get_utility(player_id)
        if depth <= 0:
            # At depth limit for pure minimax, evaluate using utility
            return state.get_utility(player_id)

        v = float("-inf")
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return state.get_utility(player_id)

        for action in legal_actions:
            successor = GameRules.apply_action(state, action)
            v = max(v, self._min_value(successor, depth - 1, player_id))

        return v

    def _min_value(self, state: GameState, depth: int, player_id: int) -> float:
        """
        MIN ply: opponent minimizes player_id's utility.
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
            v = min(v, self._max_value(successor, depth - 1, player_id))

        return v
