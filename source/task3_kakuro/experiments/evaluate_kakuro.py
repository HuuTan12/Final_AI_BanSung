import sys
import os
import time
from typing import Dict, Any, List
current_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.backtracking_solver import KakuroBacktrackingSolver

class KakuroEvaluator:

    def __init__(self, puzzle_path: str=None):
        if puzzle_path is None:
            self.puzzle_path = os.path.join(os.path.dirname(current_dir), 'puzzles', 'complex_9x9.json')
        else:
            self.puzzle_path = puzzle_path

    def verify_correctness(self, solution: Dict[tuple, int], csp: KakuroCSP) -> bool:
        if not solution:
            return False
        for run in csp.runs:
            vals = [solution.get(cell.pos) for cell in run.cells]
            if None in vals:
                return False
            if any((v < 1 or v > 9 for v in vals)):
                return False
            if len(vals) != len(set(vals)):
                return False
            if sum(vals) != run.target_sum:
                return False
        return True

    def test_stability(self, num_runs: int=5) -> Dict[str, Any]:
        print(f'\n[*] Stability Test across {num_runs} independent runs:')
        times = []
        nodes = []
        backtracks = []
        first_solution = None
        all_matched = True
        for i in range(num_runs):
            csp = KakuroCSP()
            csp.load_from_json(self.puzzle_path)
            solver = KakuroBacktrackingSolver(use_ac3=True, use_mrv=True, use_lcv=True)
            res = solver.solve(csp)
            times.append(res.execution_time)
            nodes.append(res.nodes_explored)
            backtracks.append(res.backtracks)
            if first_solution is None:
                first_solution = res.solution_grid
            elif res.solution_grid != first_solution:
                all_matched = False
            print(f'  - Run {i + 1}: Time={res.execution_time:.4f}s, Nodes={res.nodes_explored}, Backtracks={res.backtracks}')
        avg_time = sum(times) / len(times)
        is_correct = self.verify_correctness(first_solution, csp)
        print(f"[+] Correctness (Independent Verification): {('VALID 100%' if is_correct else 'FAILED')}")
        print(f"[+] Solution Consistency: {('100% IDENTICAL' if all_matched else 'DIFFERENT')}")
        print(f'[+] Average Time: {avg_time:.4f} seconds')
        return {'num_runs': num_runs, 'all_matched': all_matched, 'is_correct': is_correct, 'avg_time': avg_time, 'min_time': min(times), 'max_time': max(times)}

    def run_ablation_study(self) -> List[Dict[str, Any]]:
        print('\n[*] Ablation Study - Comparing Heuristic Configurations:')
        configs = [{'name': 'Pure Backtracking (No Heuristics, Arbitrary)', 'ac3': False, 'mrv': False, 'lcv': False, 'arbitrary': True, 'timeout': 3.0}, {'name': 'Backtracking + MRV', 'ac3': False, 'mrv': True, 'lcv': False, 'arbitrary': False, 'timeout': None}, {'name': 'Backtracking + MRV + LCV', 'ac3': False, 'mrv': True, 'lcv': True, 'arbitrary': False, 'timeout': None}, {'name': 'Backtracking + AC-3 + MRV + LCV (Full)', 'ac3': True, 'mrv': True, 'lcv': True, 'arbitrary': False, 'timeout': None}]
        results = []
        for cfg in configs:
            csp = KakuroCSP()
            csp.load_from_json(self.puzzle_path)
            solver = KakuroBacktrackingSolver(use_ac3=cfg['ac3'], use_mrv=cfg['mrv'], use_lcv=cfg['lcv'], arbitrary_var=cfg['arbitrary'], timeout=cfg['timeout'])
            res = solver.solve(csp)
            time_str = f'{res.execution_time:.4f}s' if res.is_solved else f"Timeout (>{cfg['timeout']}s)"
            nodes_str = f'{res.nodes_explored:,}' if res.is_solved else f'>{res.nodes_explored:,}'
            backtracks_str = f'{res.backtracks:,}' if res.is_solved else f'>{res.backtracks:,}'
            row = {'Configuration': cfg['name'], 'Solved': res.is_solved, 'Time': time_str, 'Nodes Explored': nodes_str, 'Backtracks': backtracks_str}
            results.append(row)
            print(f"  * {cfg['name']}: {time_str} | Nodes: {nodes_str} | Backtracks: {backtracks_str}")
        return results

    def run_all_evaluations(self):
        print('=' * 65)
        print('     KAKURO CSP SOLVER PERFORMANCE & STABILITY EVALUATION')
        print('=' * 65)
        self.test_stability(num_runs=5)
        self.run_ablation_study()
if __name__ == '__main__':
    evaluator = KakuroEvaluator()
    evaluator.run_all_evaluations()
