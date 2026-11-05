"""
solvers - Solvers and Search Algorithms for N-Queens
Course: Introduction to Artificial Intelligence (503043)
"""

from task1_nqueens.solvers.base_solver import BaseSolver, SolverResult
from task1_nqueens.solvers.sat_solver import Glucose3SATSolver
from task1_nqueens.solvers.min_conflicts import MinConflictsSolver
from task1_nqueens.solvers.heuristics import (
    VariableSelector,
    RandomSelector,
    MaxConflictSelector,
    HybridTabuSelector,
)
from task1_nqueens.solvers.backtracking_solver import (
    BacktrackingSolver,
    BacktrackStep,
    KNOWN_SOLUTIONS_COUNT,
)
from task1_nqueens.solvers.step_min_conflicts import (
    StepMinConflictsGenerator,
    MinConflictsStep,
)

__all__ = [
    "BaseSolver",
    "SolverResult",
    "Glucose3SATSolver",
    "MinConflictsSolver",
    "VariableSelector",
    "RandomSelector",
    "MaxConflictSelector",
    "HybridTabuSelector",
    "BacktrackingSolver",
    "BacktrackStep",
    "KNOWN_SOLUTIONS_COUNT",
    "StepMinConflictsGenerator",
    "MinConflictsStep",
]
