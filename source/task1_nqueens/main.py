"""
main.py - Entry Point for Task 1: N-Queens AI Visualizer & Solvers
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Launches the high-fidelity interactive N-Queens graphical interface (PyGame)
    or runs headless automated benchmarks and propositional logic verifications.
"""

import sys
import os
import argparse

# Add source directory to sys.path so modules can be imported directly
source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from task1_nqueens.core.problem import NQueensProblem
from task1_nqueens.core.constraints import ConstraintGenerator
from task1_nqueens.solvers.sat_solver import Glucose3SATSolver
from task1_nqueens.solvers.min_conflicts import MinConflictsSolver
from task1_nqueens.solvers.heuristics import MaxConflictSelector, HybridTabuSelector, RandomSelector
from task1_nqueens.solvers.backtracking_solver import BacktrackingSolver, KNOWN_SOLUTIONS_COUNT
from task1_nqueens.ui.pygame_nqueens import NQueensGUI, PYGAME_AVAILABLE


def run_cli_demo(n: int = 8) -> None:
    """Headless terminal demo executing and displaying all solvers and formula verification."""
    print("=" * 72)
    print(f"Task 1: N-Queens Problem (N = {n}) - Headless Verification Mode")
    print("=" * 72)

    # 1. Propositional Logic & CNF Verification (Req 1)
    problem = NQueensProblem(n)
    generator = ConstraintGenerator(problem)
    clauses = generator.generate_all_cnf()
    theo_count = generator.get_theoretical_clause_count()
    stats = generator.get_clause_statistics()

    print(f"\n[1] Propositional Logic Formulation (Req 1):")
    print(f"    - Board Dimensions: {n} x {n}")
    print(f"    - Boolean Variables: {stats['variables']} (DIMACS [1..{stats['variables']}])")
    print(f"    - Generated Clauses: {len(clauses):,}")
    print(f"    - Theoretical Total: {theo_count:,}")
    print(f"    - Match Formula: {'YES (100% Correct)' if len(clauses) == theo_count else 'MISMATCH'}")
    print(f"    - Known Total Solutions (OEIS A000170): {KNOWN_SOLUTIONS_COUNT.get(n, 'Unknown')}")

    # 2. Glucose3 SAT Solver (Req 2)
    print(f"\n[2] Solving via Glucose3 PySAT Solver (Req 2):")
    sat_solver = Glucose3SATSolver()
    sat_res = sat_solver.solve(n)
    print(f"    - Solved: {sat_res.is_solved}")
    print(f"    - Runtime: {sat_res.execution_time * 1000.0:.3f} ms")
    print(f"    - First Valid Solution: {sat_res.solution}")

    # 3. Min-Conflicts Solvers Comparison (Req 3)
    print(f"\n[3] Min-Conflicts Local Search Comparison (Req 3):")
    selectors = [
        ("Standard Random", RandomSelector()),
        ("Proposed Max-Conflict", MaxConflictSelector()),
        ("Proposed Hybrid-Tabu", HybridTabuSelector()),
    ]
    for label, sel in selectors:
        mc = MinConflictsSolver(heuristic=sel, init_mode="permutation")
        mc_res = mc.solve(n)
        print(f"    - {label:<24}: Solved={mc_res.is_solved}, Steps={mc_res.steps_taken}, Time={mc_res.execution_time * 1000.0:.3f} ms")

    # 4. Backtracking All Solutions Count
    print(f"\n[4] Backtracking Search & Complete Solutions Count:")
    bt = BacktrackingSolver(find_all=True)
    all_sols = bt.find_all_solutions(n)
    print(f"    - Total Valid Solutions Found: {len(all_sols)}")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="N-Queens AI Visualizer & Solver Suite")
    parser.add_argument("--n", type=int, default=8, help="Chessboard size N (default: 8, range: 4..16)")
    parser.add_argument(
        "--algo",
        type=str,
        default="BACKTRACKING",
        choices=["BACKTRACKING", "MIN_CONFLICTS_MAX", "MIN_CONFLICTS_TABU", "MIN_CONFLICTS_RANDOM", "SAT", "BROWSER", "MANUAL"],
        help="Initial algorithm mode to visualize"
    )
    parser.add_argument("--speed", type=int, default=2, choices=[1, 2, 5, 10, 50], help="Animation speed multiplier")
    parser.add_argument("--cli", action="store_true", help="Run terminal CLI demo without opening GUI")
    parser.add_argument("--benchmark", action="store_true", help="Run comprehensive benchmark suite")

    args = parser.parse_args()

    if args.benchmark:
        from task1_nqueens.experiments.benchmark import BenchmarkRunner
        runner = BenchmarkRunner()
        runner.run_all()
        return

    if args.cli or not PYGAME_AVAILABLE:
        run_cli_demo(args.n)
        return

    # Launch Pygame GUI
    gui = NQueensGUI(n=args.n)
    gui.algorithm_mode = args.algo.upper()
    gui.speed_multiplier = args.speed
    gui.run()


if __name__ == "__main__":
    main()
