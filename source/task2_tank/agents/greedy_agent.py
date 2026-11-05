"""
greedy_agent.py - Proposed Baseline: Greedy Tactical Reflex Agent
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements a greedy 1-ply tactical reflex agent using the linear evaluation function.
    Provides a fast, reactive baseline to demonstrate the performance gain of deeper
    game tree lookahead (Minimax, Alpha-Beta, Iterative Deepening).
"""

import time
from typing import Optional
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action
from task2_tank.engine.rules import GameRules


class GreedyTacticalAgent(BaseAgent):
    """
    Greedy 1-ply tactical agent that evaluates immediate successors.
    """

    def __init__(self, evaluator: Optional[TankEvaluator] = None):
        super().__init__(name="Greedy Tactical (1-Ply)")
        self.evaluator = evaluator if evaluator is not None else TankEvaluator()

    def choose_action(self, state: GameState, player_id: int) -> Action:
        self.reset_stats()
        self.stats.search_depth = 1
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
            score = self.evaluator.evaluate(successor, player_id)

            tactical_bonus = TankEvaluator.action_tactical_priority(state, action, player_id) * 0.1
            total_score = score + tactical_bonus

            if total_score > best_score:
                best_score = total_score
                best_action = action

        self.stats.execution_time = time.perf_counter() - start_time
        return best_action
