"""
base_solver.py - Abstract Base Class for N-Queens Solvers
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Defines the standard solver interface and result structure
    following Object-Oriented Programming (OOP) principles.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SolverResult:
    """
    Data structure containing experiment metrics for a solver run.
    """
    solver_name: str
    n: int
    is_solved: bool
    solution: Optional[List[int]]
    execution_time: float
    num_clauses: Optional[int] = None       # For SAT Solver
    steps_taken: Optional[int] = None        # For Min-Conflicts
    restarts: Optional[int] = None           # For Min-Conflicts

    def to_dict(self) -> Dict[str, Any]:
        """Converts results to dictionary format for tabular reporting."""
        return {
            "solver": self.solver_name,
            "n": self.n,
            "solved": self.is_solved,
            "time_sec": round(self.execution_time, 6),
            "num_clauses": self.num_clauses if self.num_clauses is not None else 0,
            "steps": self.steps_taken if self.steps_taken is not None else 0,
            "restarts": self.restarts if self.restarts is not None else 0,
        }


class BaseSolver(ABC):
    """
    Abstract base class for all N-Queens solvers.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def solve(self, n: int) -> SolverResult:
        """
        Executes the algorithm to solve N-Queens for board size n x n.
        Returns a SolverResult object.
        """
        pass
