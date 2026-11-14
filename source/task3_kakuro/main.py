import sys
import os
import argparse
current_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.abspath(os.path.join(current_dir, '..'))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.backtracking_solver import KakuroBacktrackingSolver
from task3_kakuro.solver.tracer import SolverTracer
from task3_kakuro.ui.kakuro_visualizer import KakuroVisualizer

def print_banner():
    print('=' * 65)
    print('      FINAL PROJECT - INTRODUCTION TO ARTIFICIAL INTELLIGENCE')
    print('           TASK 3: CONSTRAINT SATISFACTION PROBLEMS (KAKURO)')
    print('=' * 65)

def solve_terminal(puzzle_filename: str):
    print_banner()
    puzzle_path = os.path.join(current_dir, 'puzzles', puzzle_filename)
    if not os.path.exists(puzzle_path):
        puzzle_path = puzzle_filename
    print(f'\n[*] Loading puzzle from: {puzzle_path}')
    csp = KakuroCSP()
    csp.load_from_json(puzzle_path)
    print(f'[*] Board Dimensions: {csp.rows}x{csp.cols}')
    print(f'[*] White Cell Variables: {len(csp.variables)}')
    print(f'[*] Run Constraints: {len(csp.runs)}')
    is_valid = csp.validate_puzzle_integrity()
    h_sum, v_sum = csp.get_clue_sums()
    print(f'[*] Integrity Check (Total H == Total V): {is_valid} (H={h_sum}, V={v_sum})')
    if not is_valid:
        print('[!] Error: Clue integrity check failed!')
        return
    print('\n[*] Solving Kakuro CSP via Backtracking + AC-3 + MRV + LCV...')
    tracer = SolverTracer()
    solver = KakuroBacktrackingSolver(use_ac3=True, use_mrv=True, use_lcv=True, tracer=tracer)
    result = solver.solve(csp)
    print('\n' + '-' * 40)
    print(' SOLVE RESULT')
    print('-' * 40)
    print(f' - Solved successfully   : {result.is_solved}')
    print(f' - Execution time        : {result.execution_time:.4f} seconds')
    print(f' - Explored nodes        : {result.nodes_explored}')
    print(f' - Backtracks count      : {result.backtracks}')
    print(f' - Tracer events logged  : {len(tracer.events)}')
    if result.is_solved:
        print('\n[*] Solution Grid:')
        for r in range(csp.rows):
            row_str = []
            for c in range(csp.cols):
                pos = (r, c)
                if pos in csp.variables:
                    val = result.solution_grid.get(pos, '.')
                    row_str.append(f' {val} ')
                else:
                    row_str.append(' # ')
            print('  ' + ''.join(row_str))
        print('\n[+] All clue constraints satisfied 100%!')

def run_visualizer(puzzle_name: str=None):
    puzzles_dir = os.path.join(current_dir, 'puzzles')
    print(f'[*] Launching Kakuro PyGame CSP Studio from: {puzzles_dir}')
    vis = KakuroVisualizer(puzzle_dir=puzzles_dir, initial_puzzle=puzzle_name)
    vis.run()

def main():
    parser = argparse.ArgumentParser(description='Kakuro CSP Runner')
    parser.add_argument('--mode', choices=['ui', 'solve', 'eval'], default='ui', help="Execution mode: 'ui' (PyGame visualizer), 'solve' (CLI solver), 'eval' (benchmark evaluation)")
    parser.add_argument('--puzzle', default='complex_9x9.json', help='Puzzle JSON filename in puzzles/ or custom path')
    parser.add_argument('--cli', action='store_true', help='Run in CLI solver mode (alias for --mode solve)')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark and ablation study (alias for --mode eval)')
    args = parser.parse_args()
    if args.cli:
        args.mode = 'solve'
    elif args.benchmark:
        args.mode = 'eval'
    if args.mode == 'solve':
        solve_terminal(args.puzzle)
    elif args.mode == 'ui':
        run_visualizer(args.puzzle)
    elif args.mode == 'eval':
        from task3_kakuro.experiments.evaluate_kakuro import KakuroEvaluator
        evaluator = KakuroEvaluator(puzzle_path=os.path.join(current_dir, 'puzzles', args.puzzle))
        evaluator.run_all_evaluations()
if __name__ == '__main__':
    main()
