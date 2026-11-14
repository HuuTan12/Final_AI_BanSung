from typing import Optional, Dict
import time
from dataclasses import dataclass
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.propagators import ConstraintPropagator
from task3_kakuro.solver.heuristics import CSPHeuristics
from task3_kakuro.solver.tracer import SolverTracer, EventType


@dataclass
class KakuroSolveResult:
    is_solved: bool
    execution_time: float
    nodes_explored: int
    backtracks: int
    solution_grid: Optional[Dict[tuple, int]] = None


class KakuroBacktrackingSolver:

    def __init__(self, use_ac3: bool = True, use_mrv: bool = True, use_lcv: bool = True,
                 tracer: SolverTracer = None, timeout: Optional[float] = None,
                 arbitrary_var: bool = False):
        self.use_ac3 = use_ac3
        self.use_mrv = use_mrv
        self.use_lcv = use_lcv
        self.tracer = tracer
        self.timeout = timeout
        self.arbitrary_var = arbitrary_var

        self.propagator = ConstraintPropagator(tracer=tracer)

        self.nodes_explored = 0
        self.backtracks = 0
        self.start_time = 0.0

    def solve(self, csp: KakuroCSP) -> KakuroSolveResult:
        self.start_time = time.time()
        self.nodes_explored = 0
        self.backtracks = 0

        filtering_ok = self.propagator.initial_filtering(csp)

        if not filtering_ok:
            exec_time = time.time() - self.start_time
            return KakuroSolveResult(False, exec_time, self.nodes_explored, self.backtracks, None)

        if self.use_ac3:
            ac3_ok = self.propagator.ac3(csp)

            if not ac3_ok:
                exec_time = time.time() - self.start_time
                return KakuroSolveResult(False, exec_time, self.nodes_explored, self.backtracks, None)

        is_solved = self._backtrack(csp)
        exec_time = time.time() - self.start_time

        if is_solved:
            solution_grid = csp.get_solution_grid()
        else:
            solution_grid = None

        result = KakuroSolveResult(
            is_solved=is_solved,
            execution_time=exec_time,
            nodes_explored=self.nodes_explored,
            backtracks=self.backtracks,
            solution_grid=solution_grid
        )
        return result

    def _backtrack(self, csp: KakuroCSP) -> bool:
        if self.timeout is not None:
            elapsed = time.time() - self.start_time

            if elapsed > self.timeout:
                return False

        all_assigned = True

        for cell in csp.variables.values():
            if not cell.is_assigned:
                all_assigned = False
                break

        if all_assigned:
            return csp.is_solved()

        var = CSPHeuristics.select_unassigned_variable(
            csp,
            use_mrv=self.use_mrv,
            use_degree=True,
            arbitrary=self.arbitrary_var
        )

        if var is None:
            return False

        ordered_values = CSPHeuristics.order_domain_values(csp, var, use_lcv=self.use_lcv)

        for val in ordered_values:
            self.nodes_explored = self.nodes_explored + 1

            var.assign(val)

            if self.tracer:
                assign_message = 'Assign ' + str(val) + ' to ' + str(var.pos)
                self.tracer.emit(EventType.ASSIGN, cell_pos=var.pos, value=val, message=assign_message)

            if var in csp.cell_runs:
                runs_of_var = csp.cell_runs[var]
            else:
                runs_of_var = []

            runs_valid = True

            for run in runs_of_var:
                if not run.is_partially_valid():
                    runs_valid = False
                    break

            if runs_valid:
                pruned = self.propagator.forward_check(csp, var, val)

                if pruned is not None:
                    found_solution = self._backtrack(csp)

                    if found_solution:
                        return True

                    for neighbor in pruned:
                        removed_vals = pruned[neighbor]
                        neighbor.domain.update(removed_vals)

            var.unassign()
            self.backtracks = self.backtracks + 1

            if self.tracer:
                backtrack_message = 'Backtrack from ' + str(var.pos)
                self.tracer.emit(EventType.BACKTRACK, cell_pos=var.pos, value=val, message=backtrack_message)

        return False