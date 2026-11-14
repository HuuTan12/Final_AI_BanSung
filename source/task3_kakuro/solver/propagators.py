from typing import Set, Tuple, List, Dict, Optional
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.csp.variable import Cell
from task3_kakuro.csp.constraint import RunConstraint
from task3_kakuro.solver.tracer import SolverTracer, EventType

class ConstraintPropagator:

    def __init__(self, tracer: Optional[SolverTracer]=None):
        self.tracer = tracer

    def initial_filtering(self, csp: KakuroCSP) -> bool:
        for cell in csp.variables.values():
            runs = csp.cell_runs.get(cell, [])
            if not runs:
                continue
            allowed_vals = set(range(1, 10))
            for run in runs:
                allowed_vals &= run.get_possible_digits()
            pruned = cell.domain - allowed_vals
            if pruned:
                cell.domain &= allowed_vals
                if self.tracer:
                    self.tracer.emit(EventType.PRUNE, cell_pos=cell.pos, pruned_domain=pruned, message=f'Initial Filtering: pruned {sorted(pruned)} from {cell.pos}')
            if not cell.domain:
                return False
        return True

    def ac3(self, csp: KakuroCSP, queue: Optional[List[Tuple[Cell, RunConstraint]]]=None) -> bool:
        if queue is None:
            work_queue: List[Tuple[Cell, RunConstraint]] = []
            for cell in csp.variables.values():
                for run in csp.cell_runs.get(cell, []):
                    work_queue.append((cell, run))
        else:
            work_queue = list(queue)
        while work_queue:
            cell, run = work_queue.pop(0)
            revised, removed = self._revise(cell, run)
            if revised:
                if self.tracer and removed:
                    self.tracer.emit(EventType.PRUNE, cell_pos=cell.pos, pruned_domain=removed, message=f'AC-3: pruned {sorted(removed)} from {cell.pos}')
                if not cell.domain:
                    return False
                for other_run in csp.cell_runs.get(cell, []):
                    for other_cell in other_run.cells:
                        if other_cell != cell and (not other_cell.is_assigned):
                            item = (other_cell, other_run)
                            if item not in work_queue:
                                work_queue.append(item)
        return True

    def _revise(self, cell: Cell, run: RunConstraint) -> Tuple[bool, Set[int]]:
        revised = False
        removed = set()
        possible_digits = run.get_possible_digits()
        for val in list(cell.domain):
            if val not in possible_digits:
                cell.domain.remove(val)
                removed.add(val)
                revised = True
        return (revised, removed)

    def forward_check(self, csp: KakuroCSP, var: Cell, val: int) -> Optional[Dict[Cell, Set[int]]]:
        pruned: Dict[Cell, Set[int]] = {}
        for run in csp.cell_runs.get(var, []):
            possible_digits = run.get_possible_digits()
            for neighbor in run.cells:
                if neighbor != var and (not neighbor.is_assigned):
                    invalid_vals = {v for v in neighbor.domain if v == val or v not in possible_digits}
                    if invalid_vals:
                        if neighbor not in pruned:
                            pruned[neighbor] = set()
                        pruned[neighbor].update(invalid_vals)
                        neighbor.domain -= invalid_vals
                        if self.tracer:
                            self.tracer.emit(EventType.PRUNE, cell_pos=neighbor.pos, pruned_domain=invalid_vals, message=f'ForwardCheck: pruned {sorted(invalid_vals)} from {neighbor.pos}')
                        if not neighbor.domain:
                            return None
        return pruned
