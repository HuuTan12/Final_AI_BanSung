import time
from typing import Tuple, List, Optional
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action
from task2_tank.engine.rules import GameRules

class HeuristicAlphaBetaAgent(BaseAgent):

    def __init__(self, depth: int=3, evaluator: Optional[TankEvaluator]=None):
        super().__init__(name=f'Heuristic Alpha-Beta (Depth {depth})')
        self.depth = depth
        self.evaluator = evaluator if evaluator is not None else TankEvaluator()

    def choose_action(self, state: GameState, player_id: int) -> Action:
        self.reset_stats()
        self.stats.search_depth = self.depth
        start_time = time.perf_counter()
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return Action.STAY
        if len(legal_actions) == 1:
            return legal_actions[0]
        ordered_actions = self._order_moves(state, legal_actions, player_id)
        best_score = float('-inf')
        best_action = ordered_actions[0]
        alpha = float('-inf')
        beta = float('inf')
        for action in ordered_actions:
            self.stats.explored_nodes += 1
            successor = GameRules.apply_action(state, action)
            score = self._min_value(successor, self.depth - 1, alpha, beta, player_id)
            if score > best_score:
                best_score = score
                best_action = action
            alpha = max(alpha, best_score)
        self.stats.execution_time = time.perf_counter() - start_time
        return best_action

    def _max_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int) -> float:
        self.stats.explored_nodes += 1
        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)
        v = float('-inf')
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)
        ordered_actions = self._order_moves(state, legal_actions, player_id)
        for action in ordered_actions:
            successor = GameRules.apply_action(state, action)
            v = max(v, self._min_value(successor, depth - 1, alpha, beta, player_id))
            if v >= beta:
                self.stats.prune_count += 1
                return v
            alpha = max(alpha, v)
        return v

    def _min_value(self, state: GameState, depth: int, alpha: float, beta: float, player_id: int) -> float:
        self.stats.explored_nodes += 1
        if state.is_terminal() or depth <= 0:
            return self.evaluator.evaluate(state, player_id)
        opponent_id = 1 - player_id
        v = float('inf')
        legal_actions = state.get_legal_actions(opponent_id)
        if not legal_actions:
            return self.evaluator.evaluate(state, player_id)
        ordered_actions = self._order_moves(state, legal_actions, opponent_id)
        for action in ordered_actions:
            successor = GameRules.apply_action(state, action)
            v = min(v, self._max_value(successor, depth - 1, alpha, beta, player_id))
            if v <= alpha:
                self.stats.prune_count += 1
                return v
            beta = min(beta, v)
        return v

    def _order_moves(self, state: GameState, actions: List[Action], player_id: int) -> List[Action]:
        return sorted(actions, key=lambda a: TankEvaluator.action_tactical_priority(state, a, player_id), reverse=True)
