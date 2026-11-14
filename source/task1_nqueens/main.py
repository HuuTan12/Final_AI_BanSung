import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from task1_nqueens.core.problem import NQueensProblem
from task1_nqueens.core.constraints import ConstraintGenerator
from task1_nqueens.solvers.sat_solver import Glucose3SATSolver
from task1_nqueens.solvers.min_conflicts import MinConflictsSolver
from task1_nqueens.solvers.heuristics import MaxConflictSelector, HybridTabuSelector, RandomSelector
from task1_nqueens.solvers.backtracking_solver import BacktrackingSolver, KNOWN_SOLUTIONS_COUNT
from task1_nqueens.ui.pygame_nqueens import NQueensGUI, PYGAME_AVAILABLE

def cnf_info(n):
    gen = ConstraintGenerator(NQueensProblem(n))
    cl = gen.generate_all_cnf()
    total = gen.get_theoretical_clause_count()
    st = gen.get_clause_statistics()
    ok = len(cl) == total
    print('\n1. CNF')
    print('size:', str(n) + 'x' + str(n))
    print('variables:', st['variables'])
    print('clauses:', len(cl), '/ expected', total, '->', 'OK' if ok else 'SAI')
    print('known solutions:', KNOWN_SOLUTIONS_COUNT.get(n, '?'))

def sat_info(n):
    r = Glucose3SATSolver().solve(n)
    print('\n2. SAT (Glucose3 PySAT)')
    print('solved:', r.is_solved)
    print('clauses:', r.num_clauses)
    print('time:', round(r.execution_time * 1000, 3), 'ms')
    print('solution:', r.solution)

def mc_info(n):
    print('\n3. Min-Conflicts')
    sels = [('random', RandomSelector()), ('max conflict', MaxConflictSelector()), ('hybrid tabu', HybridTabuSelector())]
    for name, s in sels:
        r = MinConflictsSolver(heuristic=s, init_mode='permutation').solve(n)
        print(name, '| solved:', r.is_solved, '| steps:', r.steps_taken, '| time:', round(r.execution_time * 1000, 2), 'ms')

def bt_info(n):
    sols = BacktrackingSolver(find_all=True).find_all_solutions(n)
    print('\n4. Backtracking')
    print('found', len(sols), 'solutions')

def run_cli(n=8):
    print('N-Queens, n =', n)
    cnf_info(n)
    sat_info(n)
    mc_info(n)
    bt_info(n)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=8)
    ap.add_argument('--algo', default='BACKTRACKING', choices=['BACKTRACKING', 'MIN_CONFLICTS_MAX', 'MIN_CONFLICTS_TABU', 'MIN_CONFLICTS_RANDOM', 'SAT', 'BROWSER', 'MANUAL'])
    ap.add_argument('--speed', type=int, default=2, choices=[1, 2, 5, 10, 50])
    ap.add_argument('--cli', action='store_true')
    ap.add_argument('--benchmark', action='store_true')
    a = ap.parse_args()
    if a.benchmark:
        from task1_nqueens.experiments.benchmark import BenchmarkRunner
        BenchmarkRunner().run_all()
        return
    if a.cli or not PYGAME_AVAILABLE:
        run_cli(a.n)
        return
    g = NQueensGUI(n=a.n)
    g.algorithm_mode = a.algo.upper()
    g.speed_multiplier = a.speed
    g.run()
if __name__ == '__main__':
    main()
