"""
benchmark.py - Automated Benchmark and Comparison Runner
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Runs performance evaluations for Glucose3 SAT solver and Min-Conflicts variants
    with increasing values of N (N >= 4). Outputs markdown tables and visualization charts.
"""

import time
import os
import sys

# Ensure UTF-8 output across Windows, macOS and Linux consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from typing import List, Dict, Any, Optional

try:
    from task1_nqueens.solvers.sat_solver import Glucose3SATSolver
    from task1_nqueens.solvers.min_conflicts import MinConflictsSolver
    from task1_nqueens.solvers.heuristics import RandomSelector, MaxConflictSelector, HybridTabuSelector
    from task1_nqueens.core.problem import NQueensProblem
    from task1_nqueens.core.constraints import ConstraintGenerator
except ImportError:
    from solvers.sat_solver import Glucose3SATSolver
    from solvers.min_conflicts import MinConflictsSolver
    from solvers.heuristics import RandomSelector, MaxConflictSelector, HybridTabuSelector
    from core.problem import NQueensProblem
    from core.constraints import ConstraintGenerator

import matplotlib
matplotlib.use("Agg")  # Safe for headless execution across macOS, Windows and Linux
import matplotlib.pyplot as plt


class BenchmarkRunner:
    """
    Automated benchmark coordinator for Task 1 experiments.
    """

    def __init__(
        self,
        sat_sizes: Optional[List[int]] = None,
        mc_sizes: Optional[List[int]] = None,
        num_trials: int = 5
    ):
        self.sat_sizes = sat_sizes if sat_sizes is not None else [4, 6, 8, 10, 12, 16, 20, 24, 28, 32]
        self.mc_sizes = mc_sizes if mc_sizes is not None else [8, 16, 32, 64, 100]
        self.num_trials = num_trials
        self.sat_results: List[Dict[str, Any]] = []
        self.mc_results: List[Dict[str, Any]] = []

    def run_sat_experiments(self) -> List[Dict[str, Any]]:
        """
        Evaluates Glucose3 SAT Solver across increasing N >= 4.
        Records: N, Variables, Total CNF Clauses, Solve Time, and Status.
        """
        print("=== STARTING GLUCOSE3 SAT SOLVER EXPERIMENTS (PySAT) ===")
        self.sat_results = []
        solver = Glucose3SATSolver()

        for n in self.sat_sizes:
            prob = NQueensProblem(n)
            gen = ConstraintGenerator(prob)
            theo_clauses = gen.get_theoretical_clause_count()

            times = []
            res = None
            for _ in range(self.num_trials):
                res = solver.solve(n)
                times.append(res.execution_time)

            avg_time = sum(times) / len(times)
            entry = {
                "n": n,
                "variables": n * n,
                "clauses": res.num_clauses,
                "theoretical_clauses": theo_clauses,
                "is_solved": res.is_solved,
                "avg_time_sec": avg_time
            }
            self.sat_results.append(entry)
            print(f"-> [SAT] N={n:2d} | Clauses: {entry['clauses']:6d} | Avg Time: {avg_time:.6f}s | Solved: {res.is_solved}")

        return self.sat_results

    def run_min_conflicts_experiments(self) -> List[Dict[str, Any]]:
        """
        Compares Standard Min-Conflicts (Random) with Proposed Heuristics (Max-Conflict, Hybrid-Tabu).
        Records: Average Steps, Average Runtime, and Success Rate.
        """
        print("\n=== STARTING MIN-CONFLICTS HEURISTIC COMPARISONS ===")
        self.mc_results = []

        selectors = [
            ("Standard (Random)", RandomSelector),
            ("Proposed Heuristic 1 (Max-Conflict)", MaxConflictSelector),
            ("Proposed Heuristic 2 (Hybrid-Tabu)", HybridTabuSelector),
        ]

        for n in self.mc_sizes:
            for label, sel_cls in selectors:
                steps_list = []
                times_list = []
                success_count = 0

                for _ in range(self.num_trials):
                    solver = MinConflictsSolver(heuristic=sel_cls(), max_steps=max(1500, 80 * n), max_restarts=20)
                    res = solver.solve(n)
                    if res.is_solved:
                        success_count += 1
                        steps_list.append(res.steps_taken)
                    times_list.append(res.execution_time)

                avg_steps = (sum(steps_list) / len(steps_list)) if steps_list else float("nan")
                avg_time = sum(times_list) / len(times_list)
                success_rate = (success_count / self.num_trials) * 100.0

                entry = {
                    "n": n,
                    "method": label,
                    "avg_steps": round(avg_steps, 2),
                    "avg_time_sec": round(avg_time, 6),
                    "success_rate": success_rate
                }
                self.mc_results.append(entry)
                print(f"-> [MC] N={n:3d} | {label:35s} | Steps: {avg_steps:8.1f} | Time: {avg_time:.5f}s | Success: {success_rate:.0f}%")

        return self.mc_results

    def plot_comparisons(self, save_path: str = "benchmark_task1.png") -> str:
        """
        Generates comparison figures:
        1. CNF Clause Count vs N (O(N^3) growth).
        2. Glucose3 SAT Solver Runtime vs N.
        3. Min-Conflicts Average Steps (Random vs Proposed Heuristics).
        4. Min-Conflicts Average Runtime (Random vs Proposed Heuristics).
        """
        if not self.sat_results or not self.mc_results:
            print("Warning: Please run experiments prior to plotting.")
            return ""

        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        # 1. CNF Clause count
        sat_n = [r["n"] for r in self.sat_results]
        sat_clauses = [r["clauses"] for r in self.sat_results]
        axs[0, 0].plot(sat_n, sat_clauses, marker="o", color="#1f77b4", linewidth=2, label="CNF Clauses")
        axs[0, 0].set_title("Total CNF Clauses vs Board Size N ($O(N^3)$)", fontsize=12, fontweight="bold")
        axs[0, 0].set_xlabel("Board Size N")
        axs[0, 0].set_ylabel("Total CNF Clauses")
        axs[0, 0].grid(True, linestyle="--", alpha=0.6)
        axs[0, 0].legend()

        # 2. Glucose3 Runtime
        sat_times = [r["avg_time_sec"] for r in self.sat_results]
        axs[0, 1].plot(sat_n, sat_times, marker="s", color="#d62728", linewidth=2, label="Glucose3 Solve Time")
        axs[0, 1].set_title("Glucose3 SAT Solver Execution Time (seconds)", fontsize=12, fontweight="bold")
        axs[0, 1].set_xlabel("Board Size N")
        axs[0, 1].set_ylabel("Time (seconds)")
        axs[0, 1].grid(True, linestyle="--", alpha=0.6)
        axs[0, 1].legend()

        # 3. Min-Conflicts Steps
        mc_methods = list(dict.fromkeys(r["method"] for r in self.mc_results))
        colors = ["#7f7f7f", "#2ca02c", "#ff7f0e"]
        markers = ["o", "^", "D"]

        for idx, method in enumerate(mc_methods):
            m_data = [r for r in self.mc_results if r["method"] == method]
            ns = [r["n"] for r in m_data]
            steps = [r["avg_steps"] for r in m_data]
            axs[1, 0].plot(ns, steps, marker=markers[idx], color=colors[idx], linewidth=2, label=method)

        axs[1, 0].set_title("Min-Conflicts: Average Steps to Solution", fontsize=12, fontweight="bold")
        axs[1, 0].set_xlabel("Board Size N")
        axs[1, 0].set_ylabel("Average Steps")
        axs[1, 0].grid(True, linestyle="--", alpha=0.6)
        axs[1, 0].legend()

        # 4. Min-Conflicts Runtime
        for idx, method in enumerate(mc_methods):
            m_data = [r for r in self.mc_results if r["method"] == method]
            ns = [r["n"] for r in m_data]
            times = [r["avg_time_sec"] for r in m_data]
            axs[1, 1].plot(ns, times, marker=markers[idx], color=colors[idx], linewidth=2, label=method)

        axs[1, 1].set_title("Min-Conflicts: Average Execution Time (seconds)", fontsize=12, fontweight="bold")
        axs[1, 1].set_xlabel("Board Size N")
        axs[1, 1].set_ylabel("Time (seconds)")
        axs[1, 1].grid(True, linestyle="--", alpha=0.6)
        axs[1, 1].legend()

        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"\n[Visual] Benchmark comparison plot saved to: {os.path.abspath(save_path)}")
        return os.path.abspath(save_path)

    def export_to_table(self) -> str:
        """
        Exports experimental results as GitHub/IEEE formatted Markdown tables.
        """
        md = []
        md.append("### Table 1: Glucose3 SAT Solver Performance (PySAT) - Req 2\n")
        md.append("| N | Variables ($N^2$) | Generated Clauses | Theoretical Clauses | Avg Runtime (s) | Status |")
        md.append("|:---:|:---:|:---:|:---:|:---:|:---:|")
        for r in self.sat_results:
            md.append(f"| {r['n']} | {r['variables']} | {r['clauses']} | {r['theoretical_clauses']} | {r['avg_time_sec']:.6f} | {'SAT' if r['is_solved'] else 'UNSAT'} |")

        md.append("\n### Table 2: Min-Conflicts Baseline vs Proposed Heuristics - Req 3\n")
        md.append("| N | Variable Selection Heuristic | Avg Steps | Avg Runtime (s) | Success Rate |")
        md.append("|:---:|:---|:---:|:---:|:---:|")
        for r in self.mc_results:
            md.append(f"| {r['n']} | {r['method']} | {r['avg_steps']} | {r['avg_time_sec']:.6f} | {r['success_rate']:.0f}% |")

        return "\n".join(md)


if __name__ == "__main__":
    runner = BenchmarkRunner(sat_sizes=[4, 8, 12, 16, 20], mc_sizes=[8, 16, 32, 64], num_trials=3)
    runner.run_sat_experiments()
    runner.run_min_conflicts_experiments()
    runner.plot_comparisons("benchmark_task1.png")
    print("\n" + runner.export_to_table())
