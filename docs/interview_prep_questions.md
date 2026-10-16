# Cẩm nang Chuẩn bị Phỏng vấn Đồ án AI (TDTU Final Interview)
> ⚠️ **Quy chế môn học:** "Students must take an interview to justify your work in the project. If you can not explain clearly and exactly ideas nor implementations, then you get 0.0 points for related tasks."

---

## 1. Task 1: N-Queens (SAT & Min-Conflicts)
- **Câu hỏi 1:** *Tại sao số mệnh đề CNF cho hàng là $N + N \cdot \frac{N(N-1)}{2}$?*
  - **Trả lời:** Gồm 2 phần: (1) Ràng buộc có ít nhất 1 hậu (At-least-one): $x_{r,0} \lor \dots \lor x_{r,N-1}$ cho mỗi hàng $\rightarrow N$ mệnh đề. (2) Ràng buộc có nhiều nhất 1 hậu (At-most-one): Cứ mỗi cặp ô trên cùng một hàng $(\neg x_{r,i} \lor \neg x_{r,j})$ với $i < j \rightarrow \binom{N}{2} = \frac{N(N-1)}{2}$ cặp/hàng $\rightarrow N \cdot \binom{N}{2}$ mệnh đề.
- **Câu hỏi 2:** *Tại sao Min-Conflicts biểu diễn trạng thái bằng mảng 1 chiều `state[col] = row` mà không dùng ma trận $N \times N$?*
  - **Trả lời:** Biểu diễn `state[col] = row` tự động thỏa mãn ràng buộc "mỗi cột có đúng 1 quân hậu", giúp giảm không gian tìm kiếm từ $2^{N^2}$ trạng thái nhị phân xuống chỉ còn $N^N$ trạng thái.
- **Câu hỏi 3:** *Heuristic chọn biến mà bạn đề xuất hoạt động ra sao và vì sao nó tốt hơn chọn ngẫu nhiên?*
  - **Trả lời:** Baseline chọn ngẫu nhiên một biến xung đột. Heuristic đề xuất (Max-Conflict) chọn biến có số lượng xung đột lớn nhất để điều chỉnh trước, giúp giải quyết nút thắt lớn nhất của đồ thị xung đột nhanh hơn. Khi hòa điểm, chọn ngẫu nhiên giữa các ứng viên để tránh lặp chu kỳ.

---

## 2. Task 2: Tank Battle (Adversarial Search)
- **Câu hỏi 1:** *Vì sao kết quả của Alpha-Beta Pruning và Minimax thuần phải luôn luôn giống hệt nhau?*
  - **Trả lời:** Alpha-Beta chỉ cắt bỏ những nhánh con đã được chứng minh bằng toán học là không thể làm thay đổi giá trị tối ưu tại nút gốc (nhánh quá tệ cho Max hoặc quá tốt cho Min). Do đó, giá trị trả về và nước đi được chọn tại gốc luôn đồng nhất 100%, chỉ khác nhau ở số lượng node đã duyệt.
- **Câu hỏi 2:** *Cơ chế xử lý va chạm đạn 3 ô/cycle được thực hiện như thế nào trong mã nguồn?*
  - **Trả lời:** Đạn không nhảy cóc một lần 3 ô. Thuật toán duyệt qua từng ô một (bước 1, 2, 3). Sau mỗi ô di chuyển, kiểm tra va chạm ngay lập tức với Wall, Tank hoặc Base. Nếu trúng, thực thể bị trừ 1 HP và đạn bị tiêu hủy ngay, không tiếp tục bay các ô còn lại.
- **Câu hỏi 3:** *Hàm đánh giá Heuristic (Evaluation Function) của bạn gồm những yếu tố nào và trọng số được phân bổ ra sao?*
  - **Trả lời:** Dựa trên tổ hợp tuyến tính: Chênh lệch máu Tank (trọng số 50), chênh lệch máu Base (trọng số 100), khoảng cách Manhattan tới Base đối thủ, vị trí thẳng hàng bắn trúng (Line of fire), và hình phạt nặng nếu Tank đang đứng trong tầm đạn bay của đối thủ.

---

## 3. Task 3: Kakuro (CSP)
- **Câu hỏi 1:** *Tại sao kết hợp AC-3 và Backtracking (MAC) lại nhanh hơn Backtracking thuần rất nhiều lần trên bảng 9x9?*
  - **Trả lời:** Backtracking thuần chỉ phát hiện sai lầm khi đã đi sâu vào nhánh cụt (Fail late). AC-3 lan truyền các ràng buộc tổng và loại trừ các giá trị không thỏa mãn tổ hợp ngay từ đầu, giúp thu hẹp miền giá trị của các biến và phát hiện rỗng miền giá trị (Domain wipeout) trước khi mở rộng nhánh, giảm lũy thừa không gian tìm kiếm.
- **Câu hỏi 2:** *Heuristic MRV và LCV hoạt động khác nhau thế nào trong solver Kakuro?*
  - **Trả lời:** 
    - **MRV (Minimum Remaining Values):** Dùng để chọn BIẾN (Variable Ordering) — ưu tiên chọn ô có ít giá trị hợp lệ còn lại nhất ("Fail-first principle" để nếu sai thì nhận ra ngay).
    - **LCV (Least Constraining Value):** Dùng để chọn GIÁ TRỊ (Value Ordering) — ưu tiên thử giá trị nào ít loại bỏ các lựa chọn của các ô láng giềng nhất ("Succeed-first principle" để tối đa hóa cơ hội tìm thấy nghiệm).
- **Câu hỏi 3:** *Làm thế nào để bạn đảm bảo tính đúng đắn (Correctness) của nghiệm Kakuro?*
  - **Trả lời:** Sử dụng hàm kiểm tra độc lập (Verifier) duyệt qua từng Run: Kiểm tra tổng các giá trị có đúng bằng Clue ghi trên bảng không và tập hợp các giá trị có đảm bảo AllDifferent (không trùng lặp) hay không.
