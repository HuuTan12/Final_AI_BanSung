import random
import os
import sys
from typing import List, Tuple, Optional, Generator, Dict
from dataclasses import dataclass
_file_dir = os.path.dirname(os.path.abspath(__file__))
_source_dir = os.path.abspath(os.path.join(_file_dir, '..', '..'))
if _source_dir not in sys.path:
    sys.path.insert(0, _source_dir)
_task1_dir = os.path.abspath(os.path.join(_file_dir, '..'))
if _task1_dir not in sys.path:
    sys.path.insert(0, _task1_dir)
try:
    from task1_nqueens.core.problem import NQueensProblem
    from task1_nqueens.solvers.heuristics import VariableSelector, RandomSelector, MaxConflictSelector, HybridTabuSelector
except ImportError:
    from core.problem import NQueensProblem
    from solvers.heuristics import VariableSelector, RandomSelector, MaxConflictSelector, HybridTabuSelector

@dataclass
class MinConflictsStep:
    event_type: str
    board: List[int]
    selected_col: int
    row_conflicts: List[int]
    chosen_row: int
    total_conflicts: int
    step_num: int
    restarts_count: int
    conflicted_cols: List[int]
    message: str

class StepMinConflictsGenerator:

    def __init__(self, heuristic: Optional[VariableSelector]=None, max_steps: int=1000, max_restarts: int=30, init_mode: str='permutation'):
        self.heuristic = heuristic if heuristic is not None else MaxConflictSelector()
        self.max_steps = max_steps
        self.max_restarts = max_restarts
        self.init_mode = init_mode

    def run(self, n: int) -> Generator[MinConflictsStep, None, None]:
        problem = NQueensProblem(n)
        total_steps = 0
        for restart_idx in range(self.max_restarts):
            self.heuristic.reset()
            if self.init_mode == 'permutation':
                state = list(range(n))
                random.shuffle(state)
            else:
                state = [random.randint(0, n - 1) for _ in range(n)]
            row_counts = [0] * n
            diag1_counts = [0] * (2 * n)
            diag2_counts = [0] * (2 * n)
            for c in range(n):
                r = state[c]
                row_counts[r] += 1
                diag1_counts[r - c + n - 1] += 1
                diag2_counts[r + c] += 1
            init_conflicts = problem.count_attacking_pairs(state)
            conflicted_cols, conflict_counts = self._get_conflicted_variables(state, n, row_counts, diag1_counts, diag2_counts)
            yield MinConflictsStep(event_type='INIT' if restart_idx == 0 else 'RESTART', board=list(state), selected_col=-1, row_conflicts=[], chosen_row=-1, total_conflicts=init_conflicts, step_num=total_steps, restarts_count=restart_idx, conflicted_cols=conflicted_cols, message=f'Initial board configuration ({self.init_mode}): {init_conflicts} conflicts.' if restart_idx == 0 else f'Random Restart triggered (Restart #{restart_idx}): {init_conflicts} conflicts.')
            if init_conflicts == 0:
                yield MinConflictsStep(event_type='SOLVED', board=list(state), selected_col=-1, row_conflicts=[], chosen_row=-1, total_conflicts=0, step_num=total_steps, restarts_count=restart_idx, conflicted_cols=[], message='Initial state is already a valid peaceful solution!')
                return
            steps_this_run = min(self.max_steps, max(500, 40 * n))
            stuck_count = 0
            prev_conflicts = init_conflicts
            for step in range(1, steps_this_run + 1):
                total_steps += 1
                conflicted_cols, conflict_counts = self._get_conflicted_variables(state, n, row_counts, diag1_counts, diag2_counts)
                cur_total_conflicts = problem.count_attacking_pairs(state)
                if not conflicted_cols or cur_total_conflicts == 0:
                    yield MinConflictsStep(event_type='SOLVED', board=list(state), selected_col=-1, row_conflicts=[], chosen_row=-1, total_conflicts=0, step_num=total_steps, restarts_count=restart_idx, conflicted_cols=[], message=f'SOLVED! Zero conflicts achieved after {total_steps} steps.')
                    return
                if cur_total_conflicts >= prev_conflicts:
                    stuck_count += 1
                else:
                    stuck_count = 0
                prev_conflicts = cur_total_conflicts
                if stuck_count > max(60, 3 * n):
                    break
                col_to_move = self.heuristic.select_variable(conflicted_cols, conflict_counts)
                current_row = state[col_to_move]
                cur_queen_conflicts = conflict_counts[col_to_move]
                row_c = [0] * n
                best_rows = []
                min_c = float('inf')
                for r in range(n):
                    if r == current_row:
                        c_count = row_counts[r] - 1 + (diag1_counts[r - col_to_move + n - 1] - 1) + (diag2_counts[r + col_to_move] - 1)
                    else:
                        c_count = row_counts[r] + diag1_counts[r - col_to_move + n - 1] + diag2_counts[r + col_to_move]
                    row_c[r] = c_count
                    if c_count < min_c:
                        min_c = c_count
                        best_rows = [r]
                    elif c_count == min_c:
                        best_rows.append(r)
                other_best_rows = [r for r in best_rows if r != current_row]
                if other_best_rows:
                    chosen_row = random.choice(other_best_rows)
                else:
                    chosen_row = current_row
                h_name = self.heuristic.__class__.__name__
                yield MinConflictsStep(event_type='EVAL_ROWS', board=list(state), selected_col=col_to_move, row_conflicts=row_c, chosen_row=chosen_row, total_conflicts=cur_total_conflicts, step_num=total_steps, restarts_count=restart_idx, conflicted_cols=conflicted_cols, message=f'[{h_name}] Selected Column {col_to_move} ({cur_queen_conflicts} conflicts). Optimal Row: {chosen_row} (conflicts = {min_c}).')
                if chosen_row != current_row:
                    row_counts[current_row] -= 1
                    diag1_counts[current_row - col_to_move + n - 1] -= 1
                    diag2_counts[current_row + col_to_move] -= 1
                    state[col_to_move] = chosen_row
                    row_counts[chosen_row] += 1
                    diag1_counts[chosen_row - col_to_move + n - 1] += 1
                    diag2_counts[chosen_row + col_to_move] += 1
                new_total_conflicts = problem.count_attacking_pairs(state)
                yield MinConflictsStep(event_type='MOVE', board=list(state), selected_col=col_to_move, row_conflicts=row_c, chosen_row=chosen_row, total_conflicts=new_total_conflicts, step_num=total_steps, restarts_count=restart_idx, conflicted_cols=[c for c in conflicted_cols if c != col_to_move], message=f'Moved Queen in Col {col_to_move} to Row {chosen_row}. Total conflicts: {new_total_conflicts}.')
                if new_total_conflicts == 0:
                    yield MinConflictsStep(event_type='SOLVED', board=list(state), selected_col=-1, row_conflicts=[], chosen_row=-1, total_conflicts=0, step_num=total_steps, restarts_count=restart_idx, conflicted_cols=[], message=f'SOLVED! Zero conflicts achieved after {total_steps} steps.')
                    return
        yield MinConflictsStep(event_type='TIMEOUT', board=list(state), selected_col=-1, row_conflicts=[], chosen_row=-1, total_conflicts=problem.count_attacking_pairs(state), step_num=total_steps, restarts_count=self.max_restarts, conflicted_cols=conflicted_cols, message=f'Max step limit reached ({total_steps} steps). Retrying or switch algorithm!')

    def _get_conflicted_variables(self, state: List[int], n: int, row_counts: List[int], diag1_counts: List[int], diag2_counts: List[int]) -> Tuple[List[int], List[int]]:
        conflicted_vars = []
        conflict_counts = [0] * n
        for c in range(n):
            r = state[c]
            c_conflicts = row_counts[r] - 1 + (diag1_counts[r - c + n - 1] - 1) + (diag2_counts[r + c] - 1)
            conflict_counts[c] = c_conflicts
            if c_conflicts > 0:
                conflicted_vars.append(c)
        return (conflicted_vars, conflict_counts)
