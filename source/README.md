# Đồ án Cuối kỳ - Nhập môn Trí tuệ Nhân tạo (503043)
**Trường Đại học Tôn Đức Thắng (TDTU) - Khoa Công nghệ Thông tin**

---

## 1. Cấu hình môi trường đánh giá
- Môi trường chuẩn kiểm thử theo đề: **macOS 13.7.8 (Ventura) với chip Intel Core i5** / Windows / Linux.
- Phiên bản Python: **Python 3.9+**
- Thiết kế hệ thống: Tuân thủ nghiêm ngặt nguyên lý Lập trình Hướng đối tượng (**OOP**).

## 2. Hướng dẫn cài đặt
Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## 3. Cấu trúc các Task
- **Task 1: Local Search & Propositional Logic (N-Queens)** (`task1_nqueens/`)
  - Giải bài toán N-Queens bằng Logic mệnh đề với bộ giải SAT **Glucose3** (thư viện PySAT).
  - Thuật toán tìm kiếm cục bộ **Min-Conflicts** với đề xuất Heuristic chọn biến.
  - Sổ tay thí nghiệm lưu vết: `nqueens.ipynb`.
- **Task 2: Adversarial Search (Tank Battle Game)** (`task2_tank/`)
  - Trò chơi đối kháng theo lượt (Zero-Sum) với 4 cấu hình:
    1. Minimax Search
    2. Alpha-Beta Pruning
    3. Heuristic Minimax Search
    4. Heuristic Minimax Search with Alpha-Beta Pruning
  - Giao diện đồ họa bằng **PyGame** (`main.py`).
  - Hỗ trợ cơ chế nạp động thuật toán từ nhóm sinh viên khác (`agent_loader.py`).
- **Task 3: Constraint Satisfaction Problems (Kakuro)** (`task3_kakuro/`)
  - Mô hình hóa bài toán CSP (biến, miền giá trị, ràng buộc theo run).
  - Thuật toán tìm kiếm quay lui (Backtracking) kết hợp lan truyền ràng buộc (AC-3) và heuristics (MRV, LCV).
  - Giao diện trực quan hóa quá trình giải, miền giá trị và bước quay lui trên bảng test case 9x9.
  - Sổ tay kiểm thử và đánh giá: `kakuro.ipynb`.
