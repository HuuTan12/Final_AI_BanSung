"""
heuristic_minimax_agent.py - Configuration 3: Heuristic Minimax Search
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements Heuristic Minimax (H-Minimax) with depth cutoff (Lecture 07 - Slide 27-29).
    Replaces TERMINAL-TEST with CUTOFF-TEST(s, d) and terminal UTILITY with
    the heuristic evaluation function EVAL(s) from TankEvaluator, enabling real-time
    decision making without evaluating the game to completion.
"""

import time
from typing import Tuple, Optional
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action
from task2_tank.engine.rules import GameRules


class HeuristicMinimaxAgent(BaseAgent):
    """
    Agent that decides actions using Heuristic Minimax with depth cutoff.
    """

    def __init__(self, depth: int = 3, evaluator: Optional[TankEvaluator] = None):
        super().__init__(name=f"Heuristic Minimax (Depth {depth})")
        self.depth = depth
        self.evaluator = evaluator if evaluator is not None else TankEvaluator()

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Selects action by evaluating the game tree up to depth limit with EVAL(s).
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
        MAX ply: recursively maximizes heuristic evaluation.
        """
        self.stats.explored_nodes += 1

        # CUTOFF-TEST (Lecture 07 - Slide 29)
        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)

        v = float("-inf")
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)

        for action in legal_actions:
            successor = GameRules.apply_action(state, action)
            v = max(v, self._min_value(successor, depth - 1, player_id))

        return v

    def _min_value(self, state: GameState, depth: int, player_id: int) -> float:
        """
        MIN ply: recursively minimizes player_id's heuristic evaluation.
        """
        self.stats.explored_nodes += 1

        # CUTOFF-TEST (Lecture 07 - Slide 29)
        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)

        opponent_id = 1 - player_id
        v = float("inf")
        legal_actions = state.get_legal_actions(opponent_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)

        for action in legal_actions:
            successor = GameRules.apply_action(state, action)
            v = min(v, self._max_value(successor, depth - 1, player_id))

        return v
