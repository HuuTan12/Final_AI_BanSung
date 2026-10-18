"""
sat_solver.py - N-Queens Solver using Glucose3 from PySAT
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Solves the N-Queens problem using the Glucose3 SAT solver from PySAT
    as required in Task 1 - Req 2 (Lecture 09 - Slide 50).
"""

import time
from typing import List, Optional

try:
    from task1_nqueens.solvers.base_solver import BaseSolver, SolverResult
    from task1_nqueens.core.problem import NQueensProblem
    from task1_nqueens.core.constraints import ConstraintGenerator
except ImportError:
    from solvers.base_solver import BaseSolver, SolverResult
    from core.problem import NQueensProblem
    from core.constraints import ConstraintGenerator

from pysat.solvers import Glucose3


class Glucose3SATSolver(BaseSolver):
    """
    SAT solver implementation utilizing Glucose3 from the PySAT library.
    """

    def __init__(self):
        super().__init__(name="Glucose3-PySAT")

    def solve(self, n: int) -> SolverResult:
        """
        Generates CNF clauses for N-Queens, feeds them to Glucose3,
        measures execution time, and decodes the satisfying model.
        """
        problem = NQueensProblem(n)
        generator = ConstraintGenerator(problem)
        clauses = generator.generate_all_cnf()

        # Initialize Glucose3 SAT solver
        solver = Glucose3()
        solver.append_formula(clauses)

        start_time = time.perf_counter()
        is_sat = solver.solve()
        elapsed_time = time.perf_counter() - start_time

        solution: Optional[List[int]] = None
        if is_sat:
            raw_model = solver.get_model()
            solution = self._decode_model(raw_model, n)
            
            # Verify solution correctness
            if not problem.is_valid_solution(solution):
                raise RuntimeError(f"Error: Solution returned by Glucose3 for N={n} violates N-Queens constraints.")

        solver.delete()

        return SolverResult(
            solver_name=self.name,
            n=n,
            is_solved=bool(is_sat),
            solution=solution,
            execution_time=elapsed_time,
            num_clauses=len(clauses)
        )

    def _decode_model(self, model: List[int], n: int) -> List[int]:
        """
        Decodes the positive literals in PySAT truth assignment
        into queen positions where solution[col] = row.
        """
        solution = [-1] * n
        for lit in model:
            if lit > 0:
                # lit = r * n + c + 1
                idx = lit - 1
                r = idx // n
                c = idx % n
                if 0 <= c < n:
                    solution[c] = r
        return solution
