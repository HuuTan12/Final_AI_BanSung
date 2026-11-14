from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SolverResult:
    solver_name: str
    n: int
    is_solved: bool
    solution: Optional[List[int]]
    execution_time: float
    num_clauses: Optional[int] = None
    steps_taken: Optional[int] = None
    restarts: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {'solver': self.solver_name, 'n': self.n, 'solved': self.is_solved, 'time_sec': round(self.execution_time, 6), 'num_clauses': self.num_clauses if self.num_clauses is not None else 0, 'steps': self.steps_taken if self.steps_taken is not None else 0, 'restarts': self.restarts if self.restarts is not None else 0}

class BaseSolver(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def solve(self, n: int) -> SolverResult:
        pass
