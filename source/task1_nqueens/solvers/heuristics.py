"""
heuristics.py - Variable Selection Heuristics for Min-Conflicts
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements variable selection strategies for the Min-Conflicts algorithm (Task 1 - Req 3).
    - RandomSelector: Standard baseline approach (Lecture 08 - Slide 30).
    - MaxConflictSelector: Proposed Heuristic 1, inspired by the Degree Heuristic (Lecture 08 - Slide 26).
    - HybridTabuSelector: Proposed Heuristic 2, combining Random Walk (Lecture 09 - Slide 48)
      and Tabu Search (Lecture 08 - Slide 31) to prevent getting stuck in plateaux.
"""

import random
from abc import ABC, abstractmethod
from typing import List
from collections import deque


class VariableSelector(ABC):
    """
    Abstract base class for variable selection strategies in Min-Conflicts.
    """

    @abstractmethod
    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        """
        Selects one conflicted variable (column index) to reassign.
        
        Args:
            conflicted_vars: List of column indices that currently have conflicting queens.
            conflict_counts: List of conflict counts for all N columns (or matching conflicted_vars).
        """
        pass

    def reset(self) -> None:
        """Resets any internal state (e.g., when search restarts)."""
        pass


class RandomSelector(VariableSelector):
    """
    Standard Min-Conflicts approach from Lecture 08 (Slide 30):
    Randomly selects a conflicted variable uniformly at random.
    """

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        if not conflicted_vars:
            raise ValueError("Conflicted variables list is empty.")
        return random.choice(conflicted_vars)


class MaxConflictSelector(VariableSelector):
    """
    Proposed Heuristic 1: Max-Conflict Variable Selection.
    Inspired by the Degree Heuristic (Lecture 08 - Slide 26).
    Prioritizes the queen with the highest number of conflicts.
    Ties are broken uniformly at random to prevent deterministic cycles.
    """

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        if not conflicted_vars:
            raise ValueError("Conflicted variables list is empty.")

        def get_conf(var: int) -> int:
            if len(conflict_counts) > var:
                return conflict_counts[var]
            idx = conflicted_vars.index(var)
            return conflict_counts[idx]

        max_conf = max(get_conf(var) for var in conflicted_vars)
        candidates = [var for var in conflicted_vars if get_conf(var) == max_conf]
        return random.choice(candidates)


class HybridTabuSelector(VariableSelector):
    """
    Proposed Heuristic 2: Hybrid Tabu Selection.
    Combines Max-Conflict selection with an epsilon random walk (WalkSAT style, Lecture 09 - Slide 48)
    and a short-term tabu list (Tabu Search, Lecture 08 - Slide 31) to escape local plateaux.
    """

    def __init__(self, epsilon: float = 0.1, tabu_size: int = 5):
        self.epsilon = epsilon
        self.tabu_size = tabu_size
        self.tabu_list: deque = deque(maxlen=tabu_size)

    def reset(self) -> None:
        self.tabu_list.clear()

    def select_variable(self, conflicted_vars: List[int], conflict_counts: List[int]) -> int:
        if not conflicted_vars:
            raise ValueError("Conflicted variables list is empty.")

        # Epsilon-greedy: random exploration step to escape plateaux
        if random.random() < self.epsilon:
            chosen = random.choice(conflicted_vars)
            self.tabu_list.append(chosen)
            return chosen

        # Filter out variables currently in tabu list
        non_tabu = [v for v in conflicted_vars if v not in self.tabu_list]
        candidates = non_tabu if non_tabu else conflicted_vars

        def get_conf(var: int) -> int:
            if len(conflict_counts) > var:
                return conflict_counts[var]
            idx = conflicted_vars.index(var)
            return conflict_counts[idx]

        max_conf = max(get_conf(var) for var in candidates)
        best_candidates = [var for var in candidates if get_conf(var) == max_conf]
        chosen = random.choice(best_candidates)
        self.tabu_list.append(chosen)
        return chosen
