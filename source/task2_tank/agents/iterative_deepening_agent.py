"""
iterative_deepening_agent.py - Proposed Algorithm: Iterative Deepening Alpha-Beta Search
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Proposed Advanced Adversarial Search Algorithm (Extension to Lecture 07):
    Combines:
    1. Iterative Deepening (ID): Progressively searches depths 1, 2, ..., max_depth.
       Ensures anytime-readiness and uses the best action from depth d-1 to order
       moves at depth d for near-optimal alpha-beta pruning (O(b^(d/2))).
    2. Transposition Table (TT): Caches evaluated board states to avoid re-searching
       duplicate game paths reached via different action permutations.
"""

import time
from typing import Dict, Tuple, Optional, List
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action
from task2_tank.engine.rules import GameRules


class IterativeDeepeningAgent(BaseAgent):
    """
    Advanced tournament agent implementing Iterative Deepening Alpha-Beta
    with a Transposition Table and Principal Variation Move Ordering.
    """

    def __init__(self, max_depth: int = 4, time_limit: float = 0.5, evaluator: Optional[TankEvaluator] = None):
        super().__init__(name=f"Iterative Deepening AB (Max-D {max_depth})")
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.evaluator = evaluator if evaluator is not None else TankEvaluator()
        self.transposition_table: Dict[str, Tuple[int, float, Optional[Action]]] = {}
        self.tt_hits: int = 0

    def _state_key(self, state: GameState, player_id: int) -> str:
        """Compact state key for transposition table hashing."""
        tank_str = "|".join(
            f"{pid}:{t.x},{t.y},{t.hp},{t.direction.name}"
            for pid, t in sorted(state.tanks.items()) if t.is_alive
        )
        base_str = "|".join(
            f"{pid}:{b.hp}"
            for pid, b in sorted(state.bases.items()) if b.is_alive
        )
        bullet_str = "|".join(
            f"{b.x},{b.y},{b.direction.name},{b.owner_id}"
            for b in state.bullets if b.is_active
        )
        wall_hp_sum = sum(w.hp for w in state.walls.values() if w.is_alive)
        return f"{player_id}_{state.current_player}_{tank_str}_{base_str}_{bullet_str}_{len(state.walls)}_{wall_hp_sum}"

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Executes iterative deepening search up to max_depth or time cutoff.
        """
        self.reset_stats()
        self.tt_hits = 0
        start_time = time.perf_counter()

        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return Action.STAY
        if len(legal_actions) == 1:
            return legal_actions[0]

        best_action = legal_actions[0]
        pv_move: Optional[Action] = None

        for current_depth in range(1, self.max_depth + 1):
            self.stats.search_depth = current_depth

            # Order moves with the best move from the previous iteration at the front
            ordered_actions = list(legal_actions)
            if pv_move and pv_move in ordered_actions:
                ordered_actions.remove(pv_move)
                ordered_actions.insert(0, pv_move)
            else:
                ordered_actions.sort(
                    key=lambda a: TankEvaluator.action_tactical_priority(state, a, player_id),
                    reverse=True
                )

            alpha = float("-inf")
            beta = float("inf")
            iter_best_score = float("-inf")
            iter_best_action = ordered_actions[0]

            for action in ordered_actions:
                self.stats.explored_nodes += 1
                successor = GameRules.apply_action(state, action)
                score = self._min_value(successor, current_depth - 1, alpha, beta, player_id, start_time)

                if score > iter_best_score + 1e-4:
                    iter_best_score = score
                    iter_best_action = action
                elif abs(score - iter_best_score) <= 1e-4:
                    if TankEvaluator.action_tactical_priority(state, action, player_id) > TankEvaluator.action_tactical_priority(state, iter_best_action, player_id):
                        iter_best_score = score
                        iter_best_action = action

                alpha = max(alpha, iter_best_score)

            best_action = iter_best_action
            pv_move = iter_best_action

            # Time cutoff check
            if time.perf_counter() - start_time >= self.time_limit:
                break

        self.stats.execution_time = time.perf_counter() - start_time
        return best_action

    def _max_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int, start_time: float) -> float:
        """MAX ply with alpha-beta pruning and transposition table lookup."""
        self.stats.explored_nodes += 1

        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)

        # Transposition table probe
        s_key = self._state_key(state, player_id)
        if s_key in self.transposition_table:
            tt_depth, tt_val, _ = self.transposition_table[s_key]
            if tt_depth >= depth:
                self.tt_hits += 1
                return tt_val

        v = float("-inf")
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)

        # Tactical move ordering
        legal_actions.sort(
            key=lambda a: TankEvaluator.action_tactical_priority(state, a, player_id),
            reverse=True
        )

        best_a = None
        for action in legal_actions:
            successor = GameRules.apply_action(state, action)
            score = self._min_value(successor, depth - 1, alpha, beta, player_id, start_time)
            if score > v:
                v = score
                best_a = action

            if v >= beta:
                self.stats.prune_count += 1
                self.transposition_table[s_key] = (depth, v, best_a)
                return v
            alpha = max(alpha, v)

        self.transposition_table[s_key] = (depth, v, best_a)
        return v

    def _min_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int, start_time: float) -> float:
        """MIN ply with alpha-beta pruning and transposition table lookup."""
        self.stats.explored_nodes += 1

        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)

        s_key = self._state_key(state, player_id)
        if s_key in self.transposition_table:
            tt_depth, tt_val, _ = self.transposition_table[s_key]
            if tt_depth >= depth:
                self.tt_hits += 1
                return tt_val

        v = float("inf")
        opponent_id = 1 - player_id
        legal_actions = state.get_legal_actions(opponent_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)

        legal_actions.sort(
            key=lambda a: TankEvaluator.action_tactical_priority(state, a, opponent_id),
            reverse=True
        )

        best_a = None
        for action in legal_actions:
            successor = GameRules.apply_action(state, action)
            score = self._max_value(successor, depth - 1, alpha, beta, player_id, start_time)
            if score < v:
                v = score
                best_a = action

            if v <= alpha:
                self.stats.prune_count += 1
                self.transposition_table[s_key] = (depth, v, best_a)
                return v
            beta = min(beta, v)

        self.transposition_table[s_key] = (depth, v, best_a)
        return v
