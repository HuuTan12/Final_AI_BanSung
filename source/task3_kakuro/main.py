"""
main.py - Điểm khởi chạy chính cho Task 3: Kakuro CSP Solver
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group (Tân & Hiếu)

Hỗ trợ các chế độ chạy tiện lợi:
1. Chạy giao diện trực quan hóa PyGame Dashboard (mặc định):
   python main.py
   python main.py --mode ui

2. Chạy giải nhanh trong terminal và in nghiệm:
   python main.py --mode solve --puzzle complex_9x9.json

3. Chạy đánh giá toàn diện (Correctness, Stability, Ablation study):
   python main.py --mode eval
"""

import sys
import os
import argparse

# Thiết lập đường dẫn import hệ thống
current_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.abspath(os.path.join(current_dir, ".."))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.backtracking_solver import KakuroBacktrackingSolver
from task3_kakuro.solver.tracer import SolverTracer
from task3_kakuro.ui.kakuro_visualizer import KakuroVisualizer


def print_banner():
    print("=" * 65)
    print("      ĐỒ ÁN CUỐI KỲ - NHẬP MÔN TRÍ TUỆ NHÂN TẠO (503043)")
    print("           TASK 3: CONSTRAINT SATISFACTION PROBLEMS (KAKURO)")
    print("=" * 65)


def solve_terminal(puzzle_filename: str):
    print_banner()
    puzzle_path = os.path.join(current_dir, "puzzles", puzzle_filename)
    if not os.path.exists(puzzle_path):
        puzzle_path = puzzle_filename

    print(f"\n[*] Đang nạp câu đố từ: {puzzle_path}")
    csp = KakuroCSP()
    csp.load_from_json(puzzle_path)

    print(f"[*] Kích thước: {csp.rows}x{csp.cols}")
    print(f"[*] Số biến ô trắng: {len(csp.variables)}")
    print(f"[*] Số ràng buộc Run: {len(csp.runs)}")
    
    is_valid = csp.validate_puzzle_integrity()
    h_sum, v_sum = csp.get_clue_sums()
    print(f"[*] Kiểm tra tính toàn vẹn (Tổng H == Tổng V): {is_valid} (H={h_sum}, V={v_sum})")

    if not is_valid:
        print("[!] Lỗi: Bảng không đảm bảo tính toàn vẹn Clue!")
        return

    print("\n[*] Đang giải bài toán bằng Backtracking + AC-3 + MRV + LCV...")
    tracer = SolverTracer()
    solver = KakuroBacktrackingSolver(use_ac3=True, use_mrv=True, use_lcv=True, tracer=tracer)
    result = solver.solve(csp)

    print("\n" + "-" * 40)
    print(" KẾT QUẢ GIẢI (SOLVE RESULT)")
    print("-" * 40)
    print(f" - Đã giải thành công    : {result.is_solved}")
    print(f" - Thời gian thực thi    : {result.execution_time:.4f} giây")
    print(f" - Số nút mở rộng (nodes): {result.nodes_explored}")
    print(f" - Số lần quay lui       : {result.backtracks}")
    print(f" - Tổng số sự kiện tracer: {len(tracer.events)}")

    if result.is_solved:
        print("\n[*] Ma trận nghiệm tìm được:")
        for r in range(csp.rows):
            row_str = []
            for c in range(csp.cols):
                pos = (r, c)
                if pos in csp.variables:
                    val = result.solution_grid.get(pos, '.')
                    row_str.append(f" {val} ")
                else:
                    row_str.append(" # ")
            print("  " + "".join(row_str))
        print("\n[+] Toàn bộ ràng buộc Clue đều được thỏa mãn 100%!")


def run_visualizer():
    puzzles_dir = os.path.join(current_dir, "puzzles")
    print(f"[*] Khởi động giao diện PyGame Dashboard từ: {puzzles_dir}")
    vis = KakuroVisualizer(puzzle_dir=puzzles_dir)
    vis.run()


def main():
    parser = argparse.ArgumentParser(description="Kakuro CSP Runner")
    parser.add_argument(
        "--mode",
        choices=["ui", "solve", "eval"],
        default="ui",
        help="Chế độ chạy: 'ui' (Giao diện PyGame), 'solve' (Giải nhanh), 'eval' (Đánh giá benchmark)"
    )
    parser.add_argument(
        "--puzzle",
        default="complex_9x9.json",
        help="Tên file puzzle trong thư mục puzzles/ (khi chạy ở mode solve)"
    )

    args = parser.parse_args()

    if args.mode == "solve":
        solve_terminal(args.puzzle)
    elif args.mode == "ui":
        run_visualizer()
    elif args.mode == "eval":
        from task3_kakuro.experiments.evaluate_kakuro import KakuroEvaluator
        evaluator = KakuroEvaluator(puzzle_path=os.path.join(current_dir, "puzzles", args.puzzle))
        evaluator.run_all_evaluations()


if __name__ == "__main__":
    main()
