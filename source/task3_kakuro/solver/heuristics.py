from typing import List, Optional
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.csp.variable import Cell

class CSPHeuristics:

    @staticmethod
    def select_unassigned_variable(csp: KakuroCSP, use_mrv: bool=True, use_degree: bool=True, arbitrary: bool=False) -> Optional[Cell]:
        unassigned_vars = [cell for cell in csp.variables.values() if not cell.is_assigned]
        if not unassigned_vars:
            return None
        if not use_mrv:
            if arbitrary:
                import random
                return random.choice(unassigned_vars)
            return unassigned_vars[0]
        min_domain_size = min((len(var.domain) for var in unassigned_vars))
        mrv_candidates = [var for var in unassigned_vars if len(var.domain) == min_domain_size]
        if len(mrv_candidates) == 1 or not use_degree:
            return mrv_candidates[0]
        best_var = max(mrv_candidates, key=lambda var: sum((1 for neighbor in csp.get_neighbors(var) if not neighbor.is_assigned)))
        return best_var

    @staticmethod
    def order_domain_values(csp: KakuroCSP, var: Cell, use_lcv: bool=True) -> List[int]:
        domain_vals = list(var.domain)
        if not use_lcv or len(domain_vals) <= 1:
            return domain_vals
        neighbors = [n for n in csp.get_neighbors(var) if not n.is_assigned]
        if not neighbors:
            return domain_vals

        def count_conflicts(val: int) -> int:
            conflicts = 0
            for run in csp.cell_runs.get(var, []):
                possible_digits = run.get_possible_digits()
                for neighbor in run.cells:
                    if neighbor != var and (not neighbor.is_assigned):
                        for n_val in neighbor.domain:
                            if n_val == val or n_val not in possible_digits:
                                conflicts += 1
            return conflicts
        return sorted(domain_vals, key=count_conflicts)
