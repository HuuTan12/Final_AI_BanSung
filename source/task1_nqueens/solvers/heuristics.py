import random
from abc import ABC, abstractmethod
from typing import List
from collections import deque

class VariableSelector(ABC):

    @abstractmethod
    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        pass

    def reset(self) -> None:
        pass

class RandomSelector(VariableSelector):

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        if not conflicted_vars:
            raise ValueError('Conflicted variables list is empty.')
        return random.choice(conflicted_vars)

class MaxConflictSelector(VariableSelector):

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        if not conflicted_vars:
            raise ValueError('Conflicted variables list is empty.')
        max_conf = -1
        for var in conflicted_vars:
            conf = conflict_counts[var] if var < len(conflict_counts) else 0
            if conf > max_conf:
                max_conf = conf
        candidates = [var for var in conflicted_vars if (conflict_counts[var] if var < len(conflict_counts) else 0) == max_conf]
        return random.choice(candidates)

class HybridTabuSelector(VariableSelector):

    def __init__(self, epsilon: float=0.1, tabu_size: int=4):
        self.epsilon = epsilon
        self.tabu_size = tabu_size
        self.tabu_list: deque = deque(maxlen=tabu_size)

    def reset(self) -> None:
        self.tabu_list.clear()

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        if not conflicted_vars:
            raise ValueError('Conflicted variables list is empty.')
        if random.random() < self.epsilon:
            chosen = random.choice(conflicted_vars)
            self.tabu_list.append(chosen)
            return chosen
        effective_limit = max(1, len(conflicted_vars) - 1)
        recent_tabu = list(self.tabu_list)[-effective_limit:] if len(self.tabu_list) >= len(conflicted_vars) else list(self.tabu_list)
        non_tabu = [v for v in conflicted_vars if v not in recent_tabu]
        candidates = non_tabu if non_tabu else conflicted_vars
        max_conf = -1
        for var in candidates:
            conf = conflict_counts[var] if var < len(conflict_counts) else 0
            if conf > max_conf:
                max_conf = conf
        best_candidates = [var for var in candidates if (conflict_counts[var] if var < len(conflict_counts) else 0) == max_conf]
        chosen = random.choice(best_candidates)
        self.tabu_list.append(chosen)
        return chosen
