"""
experiments - Performance Benchmarks and Comparative Evaluations
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Provides automated benchmarking suites comparing Glucose3 SAT Solver
    and Min-Conflicts variants across increasing board sizes N >= 4.
"""

from task1_nqueens.experiments.benchmark import BenchmarkRunner

__all__ = ["BenchmarkRunner"]
