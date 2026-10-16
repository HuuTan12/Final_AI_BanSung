# Task 3: Constraint Satisfaction Problems (Kakuro)

## 1. Mục tiêu và Yêu cầu
1. **(1.0 điểm): Mô hình hóa CSP:**
   - Xác định biến: Mỗi ô trắng (White Cell).
   - Miền giá trị (Domain): $\{1, 2, \dots, 9\}$.
   - Ràng buộc: Với mỗi dãy ô liên tiếp (Run): Ràng buộc tổng (Sum) và ràng buộc đôi một khác nhau (AllDifferent).
   - Biện luận lý thuyết và phương pháp: Pre-filtering các tổ hợp (combinations), AC-3, Backtracking, MRV, LCV.
2. **(1.0 điểm): Cài đặt Solver & Đánh giá trên Bảng 9x9:**
   - Kết hợp Lan truyền ràng buộc (Constraint Propagation - AC-3) với Tìm kiếm quay lui (Backtracking Search).
   - Tích hợp các Heuristic từ Lecture 08 (MRV, LCV).
   - Đánh giá trên test case phức tạp 9x9 qua 3 tiêu chuẩn:
     - **Tính đúng đắn (Correctness):** Xác minh độc lập mọi hàng và cột.
     - **Tính ổn định (Stability):** Chạy nhiều lần kiểm chứng tính nhất quán.
     - **Tính hiệu quả (Effectiveness):** Nghiên cứu cắt giảm (Ablation study) số nodes, số lần backtrack và thời gian.
3. **(1.0 điểm): Giao diện trực quan hóa (UI):**
   - Trực quan hóa miền giá trị (Domains) của các biến (hiển thị số bút chì nhỏ).
   - Trực quan hóa quá trình lan truyền ràng buộc (đổi màu giá trị bị tỉa).
   - Trực quan hóa quá trình tìm kiếm quay lui (gán giá trị, thử sai, quay lui).

## 2. Cấu trúc thư mục Task 3
```
task3_kakuro/
├── csp/
│   ├── variable.py          # Biến Cell (ô trắng, tọa độ, miền giá trị {1..9})
│   ├── constraint.py        # Ràng buộc Run (Sum & AllDifferent, pre-computed combinations)
│   └── csp_problem.py       # Quản lý mạng ràng buộc KakuroCSP, kiểm tra cân bằng clue
├── solver/
│   ├── propagators.py       # AC-3 và Forward Checking thu hẹp miền giá trị
│   ├── heuristics.py        # MRV (Minimum Remaining Values), Degree, LCV (Least Constraining Value)
│   ├── tracer.py            # Observer pattern ghi lại các sự kiện (Assign, Prune, Backtrack) cho UI
│   └── backtracking_solver.py # Thuật toán Backtracking tích hợp AC-3 và Heuristics
├── puzzles/
│   ├── sample_5x5.json      # Bảng 5x5 mẫu từ trang 4 của đề
│   └── complex_9x9.json     # Bảng 9x9 test case phức tạp từ trang 5 của đề
├── ui/
│   └── kakuro_visualizer.py # Giao diện trực quan hóa (Domains, Propagation, Backtracking)
├── experiments/
│   └── evaluate_kakuro.py   # Kịch bản kiểm thử Correctness, Stability và Effectiveness
├── kakuro.ipynb             # Notebook giữ output cells theo quy định nộp bài
└── README.md
```
