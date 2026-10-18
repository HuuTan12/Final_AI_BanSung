"""
min_conflicts.py - Min-Conflicts Local Search Algorithm
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements the Min-Conflicts local search algorithm for N-Queens (Lecture 08 - Slide 29-30).
    Features O(1) conflict counting using frequency lookup arrays, pluggable variable
    selection heuristics, and random restart support.
"""

import time
import random
from typing import List, Tuple, Optional

try:
    from task1_nqueens.solvers.base_solver import BaseSolver, SolverResult
    from task1_nqueens.solvers.heuristics import VariableSelector, RandomSelector
    from task1_nqueens.core.problem import NQueensProblem
except ImportError:
    from solvers.base_solver import BaseSolver, SolverResult
    from solvers.heuristics import VariableSelector, RandomSelector
    from core.problem import NQueensProblem


class MinConflictsSolver(BaseSolver):
    """
    Min-Conflicts local search solver for N-Queens.
    State representation: 1D list where state[col] = row.
    """

    def __init__(
        self,
        heuristic: Optional[VariableSelector] = None,
        max_steps: Optional[int] = None,
        max_restarts: int = 30,
        init_mode: str = "random"
    ):
        selector = heuristic if heuristic is not None else RandomSelector()
        name = f"MinConflicts-{selector.__class__.__name__}"
        super().__init__(name=name)
        self.heuristic = selector
        self.max_steps = max_steps
        self.max_restarts = max_restarts
        self.init_mode = init_mode

    def solve(self, n: int) -> SolverResult:
        """
        Executes Min-Conflicts search with maximum allowed steps and random restarts.
        """
        problem = NQueensProblem(n)
        steps_limit = self.max_steps if self.max_steps is not None else max(1000, 50 * n)

        start_time = time.perf_counter()
        total_steps = 0
        solution: Optional[List[int]] = None
        solved = False

        for restart_count in range(self.max_restarts):
            self.heuristic.reset()
            state = self._initial_state(n)

            # Frequency count arrays for O(1) conflict queries
            row_counts = [0] * n
            diag1_counts = [0] * (2 * n)  # r - c + n - 1
            diag2_counts = [0] * (2 * n)  # r + c

            for c in range(n):
                r = state[c]
                row_counts[r] += 1
                diag1_counts[r - c + n - 1] += 1
                diag2_counts[r + c] += 1

            for step in range(1, steps_limit + 1):
                total_steps += 1

                # 1. Identify conflicted variables
                conflicted_vars, conflict_counts = self._get_conflicted_variables(
                    state, n, row_counts, diag1_counts, diag2_counts
                )

                # Goal test: no conflicts remaining
                if not conflicted_vars:
                    solved = True
                    solution = list(state)
                    break

                # 2. Variable Selection via chosen heuristic
                col_to_move = self.heuristic.select_variable(conflicted_vars, conflict_counts)
                current_row = state[col_to_move]

                # 3. Value Selection: choose row that minimizes conflicts
                best_rows = []
                min_c = float("inf")

                for r in range(n):
                    if r == current_row:
                        c_count = (
                            (row_counts[r] - 1)
                            + (diag1_counts[r - col_to_move + n - 1] - 1)
                            + (diag2_counts[r + col_to_move] - 1)
                        )
                    else:
                        c_count = (
                            row_counts[r]
                            + diag1_counts[r - col_to_move + n - 1]
                            + diag2_counts[r + col_to_move]
                        )

                    if c_count < min_c:
                        min_c = c_count
                        best_rows = [r]
                    elif c_count == min_c:
                        best_rows.append(r)

                # Break ties uniformly at random
                chosen_row = random.choice(best_rows)

                # Update state and frequency tables in O(1)
                if chosen_row != current_row:
                    row_counts[current_row] -= 1
                    diag1_counts[current_row - col_to_move + n - 1] -= 1
                    diag2_counts[current_row + col_to_move] -= 1

                    state[col_to_move] = chosen_row

                    row_counts[chosen_row] += 1
                    diag1_counts[chosen_row - col_to_move + n - 1] += 1
                    diag2_counts[chosen_row + col_to_move] += 1

            if solved:
                break

        elapsed_time = time.perf_counter() - start_time

        # Validate solution
        if solved and solution is not None:
            if not problem.is_valid_solution(solution):
                solved = False
                solution = None

        return SolverResult(
            solver_name=self.name,
            n=n,
            is_solved=solved,
            solution=solution,
            execution_time=elapsed_time,
            steps_taken=total_steps,
            restarts=restart_count if solved else self.max_restarts
        )

    def _initial_state(self, n: int) -> List[int]:
        """
        Generates initial complete assignment.
        - "random": random row for each column.
        - "permutation": random permutation of [0..n-1] (zero initial row conflicts).
        """
        if self.init_mode == "permutation":
            state = list(range(n))
            random.shuffle(state)
            return state
        return [random.randint(0, n - 1) for _ in range(n)]

    def _get_conflicted_variables(
        self,
        state: List[int],
        n: int,
        row_counts: List[int],
        diag1_counts: List[int],
        diag2_counts: List[int]
    ) -> Tuple[List[int], List[int]]:
        """
        Finds all column indices currently with conflicting queens.
        Time complexity: O(N) using frequency lookup arrays.
        """
        conflicted_vars = []
        conflict_counts = [0] * n

        for c in range(n):
            r = state[c]
            c_conflicts = (
                (row_counts[r] - 1)
                + (diag1_counts[r - c + n - 1] - 1)
                + (diag2_counts[r + c] - 1)
            )
            conflict_counts[c] = c_conflicts
            if c_conflicts > 0:
                conflicted_vars.append(c)

        return conflicted_vars, conflict_counts
