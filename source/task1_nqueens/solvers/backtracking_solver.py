import time
import os
import sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.abspath(os.path.join(file_dir, '..', '..'))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)
task1_dir = os.path.abspath(os.path.join(file_dir, '..'))
if task1_dir not in sys.path:
    sys.path.insert(0, task1_dir)
try:
    from task1_nqueens.solvers.base_solver import BaseSolver, SolverResult
    from task1_nqueens.core.problem import NQueensProblem
except ImportError:
    from solvers.base_solver import BaseSolver, SolverResult
    from core.problem import NQueensProblem
KNOWN_SOLUTIONS_COUNT = {4: 2, 5: 10, 6: 4, 7: 40, 8: 92, 9: 352, 10: 724, 11: 2680, 12: 14200, 13: 73712, 14: 365596, 15: 2279184, 16: 14772512}

class BacktrackStep:

    def __init__(self, event_type, col, row, board, cases_explored, solutions_found, backtracks_count, conflicts, message):
        self.event_type = event_type
        self.col = col
        self.row = row
        self.board = board
        self.cases_explored = cases_explored
        self.solutions_found = solutions_found
        self.backtracks_count = backtracks_count
        self.conflicts = conflicts
        self.message = message

class BacktrackingSolver(BaseSolver):

    def __init__(self, find_all=False, max_cases=None):
        if find_all == True:
            name = 'Backtracking-AllSolutions'
        else:
            name = 'Backtracking-FirstSolution'
        super().__init__(name=name)
        self.find_all = find_all
        self.max_cases = max_cases

    def get_known_total(self, n):
        if n in KNOWN_SOLUTIONS_COUNT:
            return KNOWN_SOLUTIONS_COUNT[n]
        else:
            return '?'

    def solve(self, n):
        problem = NQueensProblem(n)
        start_time = time.perf_counter()
        board = [-1] * n
        solutions = []
        count = {'cases': 0, 'backtracks': 0}
        rows_used = [False] * n
        diag1_used = [False] * (2 * n)
        diag2_used = [False] * (2 * n)

        def search(col):
            if col == n:
                solutions.append(list(board))
                if self.find_all == True:
                    return False
                else:
                    return True
            for r in range(n):
                count['cases'] = count['cases'] + 1
                d1 = r - col + n - 1
                d2 = r + col
                if rows_used[r] == False and diag1_used[d1] == False and (diag2_used[d2] == False):
                    board[col] = r
                    rows_used[r] = True
                    diag1_used[d1] = True
                    diag2_used[d2] = True
                    found = search(col + 1)
                    if found == True:
                        return True
                    board[col] = -1
                    rows_used[r] = False
                    diag1_used[d1] = False
                    diag2_used[d2] = False
                    count['backtracks'] = count['backtracks'] + 1
            return False
        search(0)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        if len(solutions) > 0:
            solved = True
            first_solution = solutions[0]
        else:
            solved = False
            first_solution = None
        result = SolverResult(solver_name=self.name, n=n, is_solved=solved, solution=first_solution, execution_time=elapsed_time, steps_taken=count['cases'], restarts=count['backtracks'])
        return result

    def find_all_solutions(self, n):
        board = [-1] * n
        solutions = []
        rows_used = [False] * n
        diag1_used = [False] * (2 * n)
        diag2_used = [False] * (2 * n)

        def search(col):
            if col == n:
                solutions.append(list(board))
                return
            for r in range(n):
                d1 = r - col + n - 1
                d2 = r + col
                if rows_used[r] == False and diag1_used[d1] == False and (diag2_used[d2] == False):
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

    def solve_step_generator(self, n, find_all=False, yield_conflicts=True):
        board = [-1] * n
        stats = {'cases': 0, 'solutions': 0, 'backtracks': 0}
        yield BacktrackStep(event_type='INIT', col=0, row=0, board=list(board), cases_explored=0, solutions_found=0, backtracks_count=0, conflicts=[], message=f'Initialized empty {n}x{n} chessboard. Commencing DFS backtracking search...')

        def backtrack(col):
            if col == n:
                stats['solutions'] = stats['solutions'] + 1
                known_total = self.get_known_total(n)
                msg = f"Solution #{stats['solutions']} found! ({stats['solutions']}/{known_total} configurations solved)"
                yield BacktrackStep(event_type='SOLUTION', col=col - 1, row=board[col - 1], board=list(board), cases_explored=stats['cases'], solutions_found=stats['solutions'], backtracks_count=stats['backtracks'], conflicts=[], message=msg)
                if find_all == True:
                    return False
                else:
                    return True
            for r in range(n):
                stats['cases'] = stats['cases'] + 1
                conflicts = []
                for prev_col in range(col):
                    prev_row = board[prev_col]
                    if prev_row == r or abs(prev_row - r) == abs(prev_col - col):
                        conflicts.append((prev_row, prev_col))
                if len(conflicts) > 0:
                    if yield_conflicts == True:
                        limit = len(conflicts)
                        if limit > 2:
                            limit = 2
                        c_info = ''
                        for k in range(limit):
                            if k > 0:
                                c_info = c_info + ', '
                            c_info = c_info + '(' + str(conflicts[k][0]) + ',' + str(conflicts[k][1]) + ')'
                        yield BacktrackStep(event_type='CONFLICT', col=col, row=r, board=list(board), cases_explored=stats['cases'], solutions_found=stats['solutions'], backtracks_count=stats['backtracks'], conflicts=conflicts, message=f'Square ({r}, {col}) invalid: Attacked by existing queen at {c_info}!')
                else:
                    board[col] = r
                    yield BacktrackStep(event_type='SAFE', col=col, row=r, board=list(board), cases_explored=stats['cases'], solutions_found=stats['solutions'], backtracks_count=stats['backtracks'], conflicts=[], message=f'Safely placed Queen at ({r}, {col}). Advancing to Column {col + 1}.')
                    stop_search = False
                    for step in backtrack(col + 1):
                        yield step
                        if step.event_type == 'SOLUTION' and find_all == False:
                            stop_search = True
                            break
                    if stop_search == True:
                        return True
                    board[col] = -1
                    stats['backtracks'] = stats['backtracks'] + 1
                    yield BacktrackStep(event_type='BACKTRACK', col=col, row=r, board=list(board), cases_explored=stats['cases'], solutions_found=stats['solutions'], backtracks_count=stats['backtracks'], conflicts=[], message=f'Backtracking: Removed Queen at ({r}, {col}). Exploring next candidate...')
            return False
        for step in backtrack(0):
            yield step
        known_total = self.get_known_total(n)
        yield BacktrackStep(event_type='FINISHED', col=n - 1, row=0, board=list(board), cases_explored=stats['cases'], solutions_found=stats['solutions'], backtracks_count=stats['backtracks'], conflicts=[], message=f"Search completed! Tested {stats['cases']} configurations, found {stats['solutions']}/{known_total} valid solutions.")
