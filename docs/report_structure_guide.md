# Hướng dẫn Báo cáo Chuẩn IEEE Conference (Tối đa 05 trang, 2 Cột)
**Môn học: Introduction to Artificial Intelligence (503043) — TDTU**

---

## 1. Quy định bắt buộc từ Giảng viên
- **Template:** IEEE Conference Proceeding (Overleaf).
- **Độ dài tối đa:** Đúng $\le$ **05 trang** (kể cả tài liệu tham khảo), bố cục 2 cột (2-column layout).
- **Tác giả:** Danh sách thành viên nhóm, **giảng viên hướng dẫn được đưa vào vị trí tác giả cuối cùng**.
- **Tài liệu tham khảo:** Chuẩn IEEE format (ví dụ: [1], [2]).

---

## 2. Bố cục chi tiết từng phần trong 5 trang

### Trang 1:
- **Tiêu đề bài báo (Title):** Ngắn gọn, học thuật (ví dụ: *Solving N-Queens, Adversarial Tank Battle, and Kakuro CSP Using Classical AI Search and Heuristics*).
- **Tác giả & Đơn vị (Authors & Affiliation):** Tên SV, MSSV, Khoa CNTT, Trường Đại học Tôn Đức Thắng; Tên giảng viên hướng dẫn.
- **Tóm tắt (Abstract):** 150 - 200 từ: Tóm tắt bài toán, phương pháp áp dụng (SAT Glucose3, Min-Conflicts, Alpha-Beta, AC-3/MRV), kết quả thực nghiệm chính và mức độ hoàn thành.
- **Từ khóa (Keywords):** N-Queens, SAT Solver, Min-Conflicts, Zero-Sum Game, Alpha-Beta Pruning, Kakuro, CSP, AC-3.
- **I. Introduction:** Giới thiệu tổng quan 3 bài toán AI trong đồ án và đóng góp chính.
- **II. Task 1 - Local Search & Propositional Logic:**
  - Mô hình hóa biến $x(r, c)$ và thuật toán sinh mệnh đề CNF (ALO, AMO).
  - Công thức tính số lượng clause lý thuyết: $2N + N^2(N-1) + \frac{N(N-1)(2N-1)}{3}$.

### Trang 2:
  - Tiếp tục Task 1: Bộ giải Glucose3 SAT Solver vs Min-Conflicts.
  - Phân tích Heuristic chọn biến đề xuất (Max-Conflict, Hybrid-Tabu).
  - **Hình 1 + Bảng 1:** Biểu đồ thời gian/số bước theo $N \ge 4$ giữa Glucose3 và Min-Conflicts.

### Trang 3:
- **III. Task 2 - Adversarial Search in Tank Battle:**
  - Mô hình hóa Zero-Sum Game: State, Players, 6 Actions, Transition (đạn bay 3 ô/cycle, va chạm cell-by-cell), Terminal, Utility.
  - Phân tích 4 cấu hình: Minimax, Alpha-Beta, Heuristic Minimax, Heuristic Alpha-Beta.
  - Thiết kế hàm Heuristic Evaluation Function (trọng số máu tank, máu base, hiểm họa đạn).
  - **Hình 2 + Bảng 2:** So sánh số node mở rộng, thời gian suy luận và tỉ lệ thắng khi thi đấu.

### Trang 4:
- **IV. Task 3 - Constraint Satisfaction Problem (Kakuro):**
  - Mô hình CSP: Biến ô trắng, miền giá trị $\{1..9\}$, ràng buộc Run (AllDifferent & Sum).
  - Thuật toán Backtracking tích hợp lan truyền ràng buộc AC-3 / Forward Checking và Heuristics (MRV, LCV).
  - **Hình 3 + Bảng 3:** Kết quả giải bảng phức tạp 9x9, nghiên cứu cắt giảm (Ablation study) chứng minh Correctness, Stability, Effectiveness.

### Trang 5:
- **V. Contributions (Đóng góp của từng thành viên):**
  - Bảng phân công chi tiết công việc của từng sinh viên trong nhóm và tỷ lệ hoàn thành (0% - 100%).
- **VI. Self-evaluation (Tự đánh giá & Điểm tự chấm):**
  - Đánh giá mức độ hoàn thành từng Task (Task 1: x/3.0, Task 2: y/3.0, Task 3: z/3.0, Task 4: t/1.0 -> Tổng điểm tự chấm).
- **VII. Conclusion (Kết luận):**
  - Đúc kết ưu nhược điểm các giải thuật, bài học kinh nghiệm và định hướng mở rộng.
- **References (Tài liệu tham khảo):** Định dạng IEEE chuẩn.