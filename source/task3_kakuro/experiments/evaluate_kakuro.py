"""
Module: evaluate_kakuro.py
Mô tả: Đánh giá bộ giải Kakuro trên test case phức tạp 9x9 theo yêu cầu 2 (1.0 điểm) của Task 3:
1. Tính đúng đắn (Correctness): Hàm verify độc lập kiểm tra tổng từng run và tính duy nhất (AllDifferent).
2. Tính ổn định (Stability): Kiểm thử lặp lại qua nhiều lần chạy để xác nhận tính nhất quán của nghiệm và thời gian.
3. Tính hiệu quả (Effectiveness): Bảng so sánh (Ablation study) giữa các cấu hình:
   - Pure Backtracking (Không dùng AC-3, không Heuristic)
   - Backtracking + MRV
   - Backtracking + MRV + LCV
   - Backtracking + AC-3 + MRV + LCV (Đầy đủ)
"""

import sys
import os
import time
from typing import Dict, Any, List

current_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.backtracking_solver import KakuroBacktrackingSolver


class KakuroEvaluator:
    """
    Bộ đánh giá toàn diện bộ giải CSP Kakuro.
    """

    def __init__(self, puzzle_path: str = None):
        if puzzle_path is None:
            self.puzzle_path = os.path.join(os.path.dirname(current_dir), "puzzles", "complex_9x9.json")
        else:
            self.puzzle_path = puzzle_path

    def verify_correctness(self, solution: Dict[tuple, int], csp: KakuroCSP) -> bool:
        """
        Xác minh độc lập: Kiểm tra nghiệm tìm được có vi phạm bất kỳ ràng buộc nào hay không:
        1. Tất cả các ô trắng đều có số trong khoảng 1..9.
        2. Mọi Run đều có tổng bằng target_sum.
        3. Không có chữ số nào bị trùng lặp trong cùng một Run (AllDifferent).
        """
        if not solution:
            return False

        for run in csp.runs:
            vals = [solution.get(cell.pos) for cell in run.cells]
            if None in vals:
                return False
            # Kiểm tra luật chữ số từ 1 đến 9
            if any(v < 1 or v > 9 for v in vals):
                return False
            # Kiểm tra luật AllDifferent
            if len(vals) != len(set(vals)):
                return False
            # Kiểm tra luật Tổng
            if sum(vals) != run.target_sum:
                return False

        return True

    def test_stability(self, num_runs: int = 5) -> Dict[str, Any]:
        """
        Đánh giá tính ổn định qua num_runs lần chạy liên tiếp:
        Kiểm tra nghiệm có đồng nhất 100% không và đo độ lệch chuẩn thời gian.
        """
        print(f"\n[*] Kiểm thử tính ổn định (Stability Test) qua {num_runs} lần chạy độc lập:")
        times = []
        nodes = []
        backtracks = []
        first_solution = None
        all_matched = True

        for i in range(num_runs):
            csp = KakuroCSP()
            csp.load_from_json(self.puzzle_path)
            solver = KakuroBacktrackingSolver(use_ac3=True, use_mrv=True, use_lcv=True)
            res = solver.solve(csp)

            times.append(res.execution_time)
            nodes.append(res.nodes_explored)
            backtracks.append(res.backtracks)

            if first_solution is None:
                first_solution = res.solution_grid
            else:
                if res.solution_grid != first_solution:
                    all_matched = False

            print(f"  - Lần {i+1}: Thời gian={res.execution_time:.4f}s, Nodes={res.nodes_explored}, Backtracks={res.backtracks}")

        avg_time = sum(times) / len(times)
        is_correct = self.verify_correctness(first_solution, csp)

        print(f"[+] Tính đúng đắn (Independent Verification): {'HỢP LỆ 100%' if is_correct else 'THẤT BẠI'}")
        print(f"[+] Tính nhất quán của nghiệm: {'ĐỒNG NHẤT 100%' if all_matched else 'KHÁC NHAU'}")
        print(f"[+] Thời gian trung bình: {avg_time:.4f} giây")

        return {
            "num_runs": num_runs,
            "all_matched": all_matched,
            "is_correct": is_correct,
            "avg_time": avg_time,
            "min_time": min(times),
            "max_time": max(times)
        }

    def run_ablation_study(self) -> List[Dict[str, Any]]:
        """
        Nghiên cứu cắt giảm (Ablation Study) để chứng minh tính hiệu quả của từng Heuristic:
        1. Backtracking cơ bản
        2. Backtracking + MRV
        3. Backtracking + MRV + LCV
        4. Backtracking + AC-3 + MRV + LCV (Full Optimization)
        """
        print("\n[*] Nghiên cứu cắt giảm (Ablation Study) - So sánh hiệu quả các cấu hình:")
        configs = [
            {"name": "Pure Backtracking (No AC3, No MRV, No LCV)", "ac3": False, "mrv": False, "lcv": False},
            {"name": "Backtracking + MRV", "ac3": False, "mrv": True, "lcv": False},
            {"name": "Backtracking + MRV + LCV", "ac3": False, "mrv": True, "lcv": True},
            {"name": "Backtracking + AC-3 + MRV + LCV (Full)", "ac3": True, "mrv": True, "lcv": True},
        ]

        results = []
        for cfg in configs:
            csp = KakuroCSP()
            csp.load_from_json(self.puzzle_path)
            solver = KakuroBacktrackingSolver(use_ac3=cfg["ac3"], use_mrv=cfg["mrv"], use_lcv=cfg["lcv"])
            res = solver.solve(csp)

            row = {
                "Cấu hình": cfg["name"],
                "Đã giải": res.is_solved,
                "Thời gian (s)": round(res.execution_time, 4),
                "Số Nodes": res.nodes_explored,
                "Số Backtracks": res.backtracks,
            }
            results.append(row)
            print(f"  * {cfg['name']}: {row['Thời gian (s)']}s | Nodes: {row['Số Nodes']} | Backtracks: {row['Số Backtracks']}")

        return results

    def run_all_evaluations(self):
        print("=" * 65)
        print("     ĐÁNH GIÁ HIỆU NĂNG & ĐỘ ỔN ĐỊNH SOLVER KAKURO CSP")
        print("=" * 65)
        self.test_stability(num_runs=5)
        self.run_ablation_study()


if __name__ == "__main__":
    evaluator = KakuroEvaluator()
    evaluator.run_all_evaluations()
