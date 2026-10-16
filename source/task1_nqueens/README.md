# Task 1: Local Search & Propositional Logic (N-Queens)

## 1. Mục tiêu và Yêu cầu
1. **(1.0 điểm): Mô hình hóa Propositional Logic & Khám phá Ràng buộc:**
   - Đặt biến logic $x(r, c) \in \{True, False\}$ cho mỗi ô cờ.
   - Trình bày thuật toán khám phá ràng buộc và quy trình chuyển đổi sang dạng CNF (At-least-one, At-most-one cho hàng, cột, đường chéo).
2. **(1.0 điểm): Giải bằng Glucose3 SAT Solver (PySAT):**
   - Thực nghiệm với $N \ge 4$ (ví dụ: $N \in \{4, 8, 16, 32, 64, 100\}$).
   - Thống kê tổng số lượng mệnh đề CNF và thời gian giải của solver.
3. **(1.0 điểm): Thuật toán Min-Conflicts & Heuristic chọn biến:**
   - Cài đặt Min-Conflicts (Lecture 08).
   - Đề xuất Heuristic chọn biến (ví dụ: Max-Conflict variable selector, Tabu-Hybrid).
   - So sánh thực nghiệm hiệu năng giữa Heuristic đề xuất và Standard Min-Conflicts (Random).

## 2. Cấu trúc thư mục Task 1
```
task1_nqueens/
├── core/
│   ├── problem.py           # Biểu diễn bàn cờ N-Queens, chuyển đổi biến SAT <-> tọa độ
│   └── constraints.py       # Bộ sinh và tối ưu hóa các mệnh đề CNF (ALO, AMO)
├── solvers/
│   ├── base_solver.py       # Lớp cơ sở trừu tượng Solver và SolverResult
│   ├── sat_solver.py        # Glucose3 solver từ PySAT
│   ├── heuristics.py        # Các chiến lược chọn biến: Random, Max-Conflict, Tabu-Hybrid
│   └── min_conflicts.py     # Cài đặt Min-Conflicts với mảng đếm xung đột O(1)
├── experiments/
│   └── benchmark.py         # Kịch bản benchmark tự động, đo đạc thống kê và vẽ biểu đồ
├── nqueens.ipynb            # Jupyter notebook trình bày bài giải và giữ nguyên output cells
└── README.md
```
