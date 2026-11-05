"""
backtracking_solver.py - Step-by-Step Backtracking Solver with Generator Support
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements a full-featured Backtracking Search for the N-Queens problem.
    Supports:
    1. Single solution search (stop at first valid assignment).
    2. All-solutions enumeration (finding all valid configurations, e.g., 92 for N=8).
    3. Step-by-step generator yielding rich events (TRY, SAFE, CONFLICT, BACKTRACK, SOLUTION)
       for interactive graphical visualization and metric telemetry.
"""

import time
import os
import sys
from typing import List, Optional, Tuple, Generator, Dict, Any
from dataclasses import dataclass

# Ensure source directory is in sys.path
_file_dir = os.path.dirname(os.path.abspath(__file__))
_source_dir = os.path.abspath(os.path.join(_file_dir, "..", ".."))
if _source_dir not in sys.path:
    sys.path.insert(0, _source_dir)
_task1_dir = os.path.abspath(os.path.join(_file_dir, ".."))
if _task1_dir not in sys.path:
    sys.path.insert(0, _task1_dir)

try:
    from task1_nqueens.solvers.base_solver import BaseSolver, SolverResult
    from task1_nqueens.core.problem import NQueensProblem
except ImportError:
    from solvers.base_solver import BaseSolver, SolverResult
    from core.problem import NQueensProblem


# Reference known counts of distinct valid solutions for N-Queens (OEIS A000170)
KNOWN_SOLUTIONS_COUNT: Dict[int, int] = {
    4: 2,
    5: 10,
    6: 4,
    7: 40,
    8: 92,
    9: 352,
    10: 724,
    11: 2680,
    12: 14200,
    13: 73712,
    14: 365596,
    15: 2279184,
    16: 14772512,
}


@dataclass
class BacktrackStep:
    """
    Data payload for an individual step in the backtracking search.
    Used by graphical visualizers to animate placement and display live metrics.
    """
    event_type: str            # "TRY", "SAFE", "CONFLICT", "BACKTRACK", "SOLUTION", "FINISHED"
    col: int                   # Current column being inspected [0..N-1]
    row: int                   # Current row candidate [0..N-1]
    board: List[int]           # Current queen assignments (board[col] = row, or -1 if unplaced)
    cases_explored: int        # Cumulative number of candidate cell checks
    solutions_found: int       # Total number of complete valid solutions found so far
    backtracks_count: int      # Cumulative number of backtrack operations
    conflicts: List[Tuple[int, int]]  # Coordinates of attacking queens causing conflict
    message: str               # Human-readable description for UI status bar


class BacktrackingSolver(BaseSolver):
    """
    Depth-First Search (DFS) with Backtracking and Forward Checking
    for the N-Queens problem.
    """

    def __init__(self, find_all: bool = False, max_cases: Optional[int] = None):
        name = "Backtracking-AllSolutions" if find_all else "Backtracking-FirstSolution"
        super().__init__(name=name)
        self.find_all = find_all
        self.max_cases = max_cases

    def solve(self, n: int) -> SolverResult:
        """
        Executes standard non-visual backtracking search and returns SolverResult.
        """
        problem = NQueensProblem(n)
        start_time = time.perf_counter()

        board = [-1] * n
        solutions: List[List[int]] = []
        cases_count = 0
        backtracks_count = 0

        # Frequency bitmasks / sets for fast diagonal and row attack checks
        rows_used = [False] * n
        diag1_used = [False] * (2 * n)  # r - c + n - 1
        diag2_used = [False] * (2 * n)  # r + c

        def search(col: int) -> bool:
            nonlocal cases_count, backtracks_count

            if col == n:
                solutions.append(list(board))
                return not self.find_all  # return True to stop if find_all is False

            for r in range(n):
                cases_count += 1
                d1 = r - col + n - 1
                d2 = r + col

                if not rows_used[r] and not diag1_used[d1] and not diag2_used[d2]:
                    # Place queen
                    board[col] = r
                    rows_used[r] = True
                    diag1_used[d1] = True
                    diag2_used[d2] = True

                    # Recurse
                    if search(col + 1):
                        return True

                    # Backtrack
                    board[col] = -1
                    rows_used[r] = False
                    diag1_used[d1] = False
                    diag2_used[d2] = False
                    backtracks_count += 1

            return False

        search(0)
        elapsed_time = time.perf_counter() - start_time
        solved = len(solutions) > 0
        first_solution = solutions[0] if solved else None

        return SolverResult(
            solver_name=self.name,
            n=n,
            is_solved=solved,
            solution=first_solution,
            execution_time=elapsed_time,
            steps_taken=cases_count,
            restarts=backtracks_count
        )

    def find_all_solutions(self, n: int) -> List[List[int]]:
        """
        Enumerates all valid solution assignments for an N x N board.
        """
        board = [-1] * n
        solutions: List[List[int]] = []
        rows_used = [False] * n
        diag1_used = [False] * (2 * n)
        diag2_used = [False] * (2 * n)

        def search(col: int):
            if col == n:
                solutions.append(list(board))
                return
            for r in range(n):
                d1 = r - col + n - 1
                d2 = r + col
                if not rows_used[r] and not diag1_used[d1] and not diag2_used[d2]:
                    board[col] = r
                    rows_used[r] = True
                    diag1_used[d1] = True
                    diag2_used[d2] = True

                    search(col + 1)

                    board[col] = -1
                    rows_used[r] = False
                    diag1_used[d1] = False
                    diag2_used[d2] = False

        search(0)
        return solutions

    def solve_step_generator(
        self,
        n: int,
        find_all: bool = False,
        yield_conflicts: bool = True
    ) -> Generator[BacktrackStep, None, None]:
        """
        Step-by-step generator for UI animation.
        Yields BacktrackStep events for each placement trial, conflict, backtrack, and solution.
        """
        board = [-1] * n
        cases_count = 0
        solutions_count = 0
        backtracks_count = 0

        # Initial empty board step
        yield BacktrackStep(
            event_type="INIT",
            col=0,
            row=0,
            board=list(board),
            cases_explored=0,
            solutions_found=0,
            backtracks_count=0,
            conflicts=[],
            message=f"Khởi tạo bàn cờ {n}x{n} trống. Bắt đầu duyệt quay lui..."
        )

        def backtrack(col: int) -> Generator[BacktrackStep, None, bool]:
            nonlocal cases_count, solutions_count, backtracks_count

            if col == n:
                solutions_count += 1
                known_total = KNOWN_SOLUTIONS_COUNT.get(n, "?")
                msg = (f"🎉 Tìm thấy nghiệm #{solutions_count}! "
                       f"({solutions_count}/{known_total} trường hợp nghiệm)")
                yield BacktrackStep(
                    event_type="SOLUTION",
                    col=col - 1,
                    row=board[col - 1],
                    board=list(board),
                    cases_explored=cases_count,
                    solutions_found=solutions_count,
                    backtracks_count=backtracks_count,
                    conflicts=[],
                    message=msg
                )
                return not find_all

            for r in range(n):
                cases_count += 1
                # Check conflicts with previously placed queens
                conflicts: List[Tuple[int, int]] = []
                for prev_col in range(col):
                    prev_row = board[prev_col]
                    if prev_row == r or abs(prev_row - r) == abs(prev_col - col):
                        conflicts.append((prev_row, prev_col))

                if conflicts:
                    if yield_conflicts:
                        c_info = ", ".join([f"({cr},{cc})" for cr, cc in conflicts[:2]])
                        yield BacktrackStep(
                            event_type="CONFLICT",
                            col=col,
                            row=r,
                            board=list(board),
                            cases_explored=cases_count,
                            solutions_found=solutions_count,
                            backtracks_count=backtracks_count,
                            conflicts=conflicts,
                            message=f"Thử ô ({r}, {col}) thất bại: Xung đột với hậu tại {c_info}!"
                        )
                else:
                    # Safe to place
                    board[col] = r
                    yield BacktrackStep(
                        event_type="SAFE",
                        col=col,
                        row=r,
                        board=list(board),
                        cases_explored=cases_count,
                        solutions_found=solutions_count,
                        backtracks_count=backtracks_count,
                        conflicts=[],
                        message=f"Đặt con hậu an toàn tại ({r}, {col})! Tiến tới cột {col + 1}."
                    )

                    # Recurse to next column
                    stop_search = False
                    for step in backtrack(col + 1):
                        yield step
                        if step.event_type == "SOLUTION" and not find_all:
                            stop_search = True
                            break

                    if stop_search:
                        return True

                    # Backtrack: lift queen
                    board[col] = -1
                    backtracks_count += 1
                    yield BacktrackStep(
                        event_type="BACKTRACK",
                        col=col,
                        row=r,
                        board=list(board),
                        cases_explored=cases_count,
                        solutions_found=solutions_count,
                        backtracks_count=backtracks_count,
                        conflicts=[],
                        message=f"Rút hậu khỏi ({r}, {col}). Quay lui để thử trường hợp khác..."
                    )

            return False

        # Run generator
        for step in backtrack(0):
            yield step

        known_total = KNOWN_SOLUTIONS_COUNT.get(n, "?")
        yield BacktrackStep(
            event_type="FINISHED",
            col=n - 1,
            row=0,
            board=list(board),
            cases_explored=cases_count,
            solutions_found=solutions_count,
            backtracks_count=backtracks_count,
            conflicts=[],
            message=f"Hoàn tất tìm kiếm! Đã duyệt {cases_count} trường hợp, tìm thấy {solutions_count}/{known_total} nghiệm."
        )
