"""
constraints.py - Propositional Logic Formulation & CNF Clause Generator
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Formulates the N-Queens problem into Propositional Logic constraints
    and converts them into Conjunctive Normal Form (CNF) clauses (Task 1 - Req 1).
    Covers At-Least-One (ALO) and At-Most-One (AMO) for rows, columns, and diagonals.
"""

from typing import List, Dict
try:
    from task1_nqueens.core.problem import NQueensProblem
except ImportError:
    from core.problem import NQueensProblem


class ConstraintGenerator:
    """
    Generates CNF clauses for the N-Queens problem based on Propositional Logic.
    """

    def __init__(self, problem: NQueensProblem):
        self.problem = problem
        self.n = problem.n

    def generate_row_clauses(self) -> List[List[int]]:
        """
        Generates row constraints: each row must have exactly one queen.
        - At-Least-One (ALO): (X_r,0 V X_r,1 V ... V X_r,N-1)
        - At-Most-One (AMO): (~X_r,c1 V ~X_r,c2) for all c1 < c2
        """
        clauses: List[List[int]] = []
        for r in range(self.n):
            row_vars = [self.problem.to_var(r, c) for c in range(self.n)]

            # 1. At-Least-One (ALO)
            clauses.append(row_vars)

            # 2. At-Most-One (AMO) via pairwise encoding
            for c1 in range(self.n):
                for c2 in range(c1 + 1, self.n):
                    clauses.append([-row_vars[c1], -row_vars[c2]])

        return clauses

    def generate_col_clauses(self) -> List[List[int]]:
        """
        Generates column constraints: each column must have exactly one queen.
        - At-Least-One (ALO): (X_0,c V X_1,c V ... V X_N-1,c)
        - At-Most-One (AMO): (~X_r1,c V ~X_r2,c) for all r1 < r2
        """
        clauses: List[List[int]] = []
        for c in range(self.n):
            col_vars = [self.problem.to_var(r, c) for r in range(self.n)]

            # 1. At-Least-One (ALO)
            clauses.append(col_vars)

            # 2. At-Most-One (AMO) via pairwise encoding
            for r1 in range(self.n):
                for r2 in range(r1 + 1, self.n):
                    clauses.append([-col_vars[r1], -col_vars[r2]])

        return clauses

    def generate_diagonal_clauses(self) -> List[List[int]]:
        r"""
        Generates diagonal constraints: each diagonal has at most one queen.
        - Main diagonals (\): r - c = k for -(N - 1) <= k <= N - 1
        - Anti diagonals (/): r + c = k for 0 <= k <= 2 * N - 2
        """
        clauses: List[List[int]] = []

        # 1. Main diagonals (top-left to bottom-right): r - c = k
        for k in range(-(self.n - 1), self.n):
            diag = [
                self.problem.to_var(r, c)
                for r in range(self.n)
                for c in range(self.n)
                if r - c == k
            ]
            if len(diag) >= 2:
                for i in range(len(diag)):
                    for j in range(i + 1, len(diag)):
                        clauses.append([-diag[i], -diag[j]])

        # 2. Anti diagonals (top-right to bottom-left): r + c = k
        for k in range(0, 2 * self.n - 1):
            anti = [
                self.problem.to_var(r, c)
                for r in range(self.n)
                for c in range(self.n)
                if r + c == k
            ]
            if len(anti) >= 2:
                for i in range(len(anti)):
                    for j in range(i + 1, len(anti)):
                        clauses.append([-anti[i], -anti[j]])

        return clauses

    def generate_all_cnf(self) -> List[List[int]]:
        """
        Combines all CNF clauses for the SAT solver.
        """
        clauses = []
        clauses.extend(self.generate_row_clauses())
        clauses.extend(self.generate_col_clauses())
        clauses.extend(self.generate_diagonal_clauses())
        return clauses

    def get_theoretical_clause_count(self) -> int:
        """
        Computes the theoretical total number of clauses using the formula:
        Total = 2N + N^2*(N-1) + N*(N-1)*(2N-1)/3
        """
        n = self.n
        alo_count = 2 * n
        row_col_amo = (n ** 2) * (n - 1)
        diag_amo = (n * (n - 1) * (2 * n - 1)) // 3
        return alo_count + row_col_amo + diag_amo

    def get_clause_statistics(self) -> Dict[str, int]:
        """
        Returns a breakdown of clause counts per constraint type.
        """
        n = self.n
        row_alo = n
        row_amo = n * (n * (n - 1) // 2)
        col_alo = n
        col_amo = n * (n * (n - 1) // 2)
        diag_amo = (n * (n - 1) * (2 * n - 1)) // 3

        return {
            "n": n,
            "variables": n * n,
            "row_alo": row_alo,
            "row_amo": row_amo,
            "col_alo": col_alo,
            "col_amo": col_amo,
            "diagonal_amo": diag_amo,
            "total_clauses": row_alo + row_amo + col_alo + col_amo + diag_amo
        }