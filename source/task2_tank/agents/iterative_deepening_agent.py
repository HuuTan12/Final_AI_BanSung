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


class _SearchTimeout(Exception):
    """Raised when iterative deepening exceeds time_limit mid-iteration."""
    pass


class IterativeDeepeningAgent(BaseAgent):
    """
    Advanced tournament agent implementing Iterative Deepening Alpha-Beta
    with a Transposition Table and Principal Variation Move Ordering.
    """

    def __init__(self, max_depth: int = 3, time_limit: float = 0.5, evaluator: Optional[TankEvaluator] = None):
        super().__init__(name=f"Iterative Deepening AB (Max-D {max_depth})")
        self.max_depth = max_depth
        self.depth = max_depth
        self.time_limit = time_limit
        self.evaluator = evaluator if evaluator is not None else TankEvaluator()
        # TT stores key -> (depth, flag, value, best_action) where flag in {"EXACT", "LOWER", "UPPER"}
        self.transposition_table: Dict[Tuple, Tuple[int, str, float, Optional[Action]]] = {}
        self.tt_hits: int = 0

    def _state_key(self, state: GameState, player_id: int) -> Tuple:
        """Exact hashable state key including wall coordinates and cycle count."""
        tanks_key = tuple(
            (pid, t.x, t.y, t.hp, t.direction)
            for pid, t in sorted(state.tanks.items()) if t.is_alive
        )
        bases_key = tuple(
            (pid, b.x, b.y, b.hp)
            for pid, b in sorted(state.bases.items()) if b.is_alive
        )
        bullets_key = tuple(
            (b.x, b.y, b.direction, b.owner_id)
            for b in state.bullets if b.is_active
        )
        walls_key = tuple(
            sorted((pos[0], pos[1], w.hp) for pos, w in state.walls.items() if w.is_alive)
        )
        return (
            player_id,
            state.current_player,
            state.game_cycle,
            state.max_cycles,
            state.width,
            state.height,
            tanks_key,
            bases_key,
            bullets_key,
            walls_key,
        )

    def _check_timeout(self, start_time: float) -> None:
        if (self.stats.explored_nodes & 127) == 0:
            if time.perf_counter() - start_time >= self.time_limit:
                raise _SearchTimeout()

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Executes iterative deepening search up to max_depth or time cutoff.
        """
        self.reset_stats()
        self.tt_hits = 0
        self.transposition_table.clear()
        start_time = time.perf_counter()

        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return Action.STAY
        if len(legal_actions) == 1:
            self.stats.search_depth = 1
            return legal_actions[0]

        best_action = legal_actions[0]
        pv_move: Optional[Action] = None
        completed_depth = 0

        for current_depth in range(1, self.max_depth + 1):
            # Sort by tactical priority first, then promote best move from depth d-1
            ordered_actions = sorted(
                legal_actions,
                key=lambda a: TankEvaluator.action_tactical_priority(state, a, player_id),
                reverse=True
            )
            if pv_move and pv_move in ordered_actions:
                ordered_actions.remove(pv_move)
                ordered_actions.insert(0, pv_move)

            alpha = float("-inf")
            beta = float("inf")
            iter_best_score = float("-inf")
            iter_best_action = ordered_actions[0]

            try:
                for action in ordered_actions:
                    self.stats.explored_nodes += 1
                    self._check_timeout(start_time)
                    successor = GameRules.apply_action(state, action)
                    score = self._min_value(successor, current_depth - 1, alpha, beta, player_id, start_time)

                    if score > iter_best_score:
                        iter_best_score = score
                        iter_best_action = action
                    alpha = max(alpha, iter_best_score)

                best_action = iter_best_action
                pv_move = iter_best_action
                completed_depth = current_depth
                self.stats.search_depth = completed_depth
            except _SearchTimeout:
                if completed_depth == 0:
                    best_action = iter_best_action
                    self.stats.search_depth = 1
                break

            if time.perf_counter() - start_time >= self.time_limit:
                break

        self.stats.execution_time = time.perf_counter() - start_time
        return best_action

    def _order_with_tt(self, state: GameState, legal_actions: List[Action], pid: int, tt_move: Optional[Action]) -> List[Action]:
        ordered = sorted(
            legal_actions,
            key=lambda a: TankEvaluator.action_tactical_priority(state, a, pid),
            reverse=True
        )
        if tt_move and tt_move in ordered:
            ordered.remove(tt_move)
            ordered.insert(0, tt_move)
        return ordered

    def _max_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int, start_time: float) -> float:
        """MAX ply with alpha-beta pruning and bound-aware transposition table lookup."""
        self.stats.explored_nodes += 1
        self._check_timeout(start_time)

        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)

        orig_alpha = alpha
        orig_beta = beta
        tt_move: Optional[Action] = None

        s_key = self._state_key(state, player_id)
        if s_key in self.transposition_table:
            tt_depth, tt_flag, tt_val, tt_move = self.transposition_table[s_key]
            if tt_depth >= depth:
                self.tt_hits += 1
                if tt_flag == "EXACT":
                    return tt_val
                elif tt_flag == "LOWER":
                    alpha = max(alpha, tt_val)
                elif tt_flag == "UPPER":
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val

        v = float("-inf")
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)

        ordered_actions = self._order_with_tt(state, legal_actions, player_id, tt_move)
        best_a = ordered_actions[0]

        for action in ordered_actions:
            successor = GameRules.apply_action(state, action)
            score = self._min_value(successor, depth - 1, alpha, beta, player_id, start_time)
            if score > v:
                v = score
                best_a = action

            if v >= beta:
                self.stats.prune_count += 1
                break
            alpha = max(alpha, v)

        if v <= orig_alpha:
            flag = "UPPER"
        elif v >= orig_beta:
            flag = "LOWER"
        else:
            flag = "EXACT"
        self.transposition_table[s_key] = (depth, flag, v, best_a)
        return v

    def _min_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int, start_time: float) -> float:
        """MIN ply with alpha-beta pruning and bound-aware transposition table lookup."""
        self.stats.explored_nodes += 1
        self._check_timeout(start_time)

        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)

        orig_alpha = alpha
        orig_beta = beta
        tt_move: Optional[Action] = None

        s_key = self._state_key(state, player_id)
        if s_key in self.transposition_table:
            tt_depth, tt_flag, tt_val, tt_move = self.transposition_table[s_key]
            if tt_depth >= depth:
                self.tt_hits += 1
                if tt_flag == "EXACT":
                    return tt_val
                elif tt_flag == "LOWER":
                    alpha = max(alpha, tt_val)
                elif tt_flag == "UPPER":
                    beta = min(beta, tt_val)
                if alpha >= beta:
                    return tt_val

        v = float("inf")
        opponent_id = 1 - player_id
        legal_actions = state.get_legal_actions(opponent_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)

        ordered_actions = self._order_with_tt(state, legal_actions, opponent_id, tt_move)
        best_a = ordered_actions[0]

        for action in ordered_actions:
            successor = GameRules.apply_action(state, action)
            score = self._max_value(successor, depth - 1, alpha, beta, player_id, start_time)
            if score < v:
                v = score
                best_a = action

            if v <= alpha:
                self.stats.prune_count += 1
                break
            beta = min(beta, v)

        if v <= orig_alpha:
            flag = "UPPER"
        elif v >= orig_beta:
            flag = "LOWER"
        else:
            flag = "EXACT"
        self.transposition_table[s_key] = (depth, flag, v, best_a)
        return v
