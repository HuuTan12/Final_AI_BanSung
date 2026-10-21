"""
Module: heuristics.py
Mô tả: Cài đặt các Heuristic chọn biến và chọn giá trị cho bài toán CSP Kakuro:
- MRV (Minimum Remaining Values): Ưu tiên ô có miền giá trị nhỏ nhất.
- Degree Heuristic: Tie-breaker cho MRV, ưu tiên ô có nhiều láng giềng chưa gán nhất.
- LCV (Least Constraining Value): Ưu tiên thử giá trị ít ảnh hưởng đến miền giá trị láng giềng nhất.
"""

from typing import List, Optional
from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.csp.variable import Cell


class CSPHeuristics:
    """
    Tập hợp các heuristic hỗ trợ tối ưu hóa quy trình Backtracking Search.
    """

    @staticmethod
    def select_unassigned_variable(
        csp: KakuroCSP, 
        use_mrv: bool = True, 
        use_degree: bool = True
    ) -> Optional[Cell]:
        """
        Chọn ô trắng chưa gán tiếp theo bằng MRV kết hợp Degree Heuristic.
        """
        unassigned_vars = [cell for cell in csp.variables.values() if not cell.is_assigned]
        if not unassigned_vars:
            return None

        if not use_mrv:
            return unassigned_vars[0]

        # 1. Tìm kích thước miền giá trị nhỏ nhất (MRV)
        min_domain_size = min(len(var.domain) for var in unassigned_vars)
        mrv_candidates = [var for var in unassigned_vars if len(var.domain) == min_domain_size]

        # Nếu chỉ có 1 ứng viên hoặc không bật Degree Heuristic -> Trả về ngay
        if len(mrv_candidates) == 1 or not use_degree:
            return mrv_candidates[0]

        # 2. Tie-breaker bằng Degree Heuristic (chọn ô liên kề với nhiều ô chưa gán nhất)
        best_var = max(
            mrv_candidates,
            key=lambda var: sum(
                1 for neighbor in csp.get_neighbors(var) if not neighbor.is_assigned
            )
        )
        return best_var

    @staticmethod
    def order_domain_values(
        csp: KakuroCSP, 
        var: Cell, 
        use_lcv: bool = True
    ) -> List[int]:
        """
        Sắp xếp các giá trị trong domain của var theo thứ tự LCV (Least Constraining Value).
        Ưu tiên các giá trị ít làm suy giảm miền giá trị của các ô láng giềng.
        """
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
                    if neighbor != var and not neighbor.is_assigned:
                        # Đếm số giá trị trong domain láng giềng sẽ bị tỉa nếu var = val
                        for n_val in neighbor.domain:
                            if n_val == val or n_val not in possible_digits:
                                conflicts += 1
            return conflicts

        # Sắp xếp tăng dần theo số lượng xung đột (ít xung đột đứng trước)
        return sorted(domain_vals, key=count_conflicts)