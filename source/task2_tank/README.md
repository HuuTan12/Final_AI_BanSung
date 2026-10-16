# Task 2: Adversarial Search (Tank Battle Game)

## 1. Mục tiêu và Yêu cầu
1. **(1.0 điểm): Mô hình hóa Zero-Sum Game:**
   - Định nghĩa các thành phần: Trạng thái (Game State), Người chơi (Players: 0 và 1), Tập hành động (Actions: 6 hành động), Hàm chuyển trạng thái (Transition Function), Trạng thái kết thúc (Terminal States) và Hàm độ lợi (Utility Function).
   - Thảo luận các thuật toán tìm kiếm đối kháng: Minimax, Alpha-Beta Pruning, Heuristic Minimax.
2. **(1.5 điểm): Cài đặt & So sánh 4 Cấu hình:**
   - Minimax Search
   - Alpha-Beta Search
   - Heuristic Minimax Search
   - Heuristic Minimax Search with Alpha-Beta Pruning
   - Đo lường và so sánh: Thời gian thực thi, Số trạng thái đã khám phá (Explored Nodes), Độ sâu tìm kiếm (Search Depth), Tỷ lệ thắng/thua.
3. **(0.5 điểm): Giao diện PyGame & Nạp thuật toán nhóm khác:**
   - GUI bằng PyGame hiển thị trực quan bản đồ, máu, đạn và các thông số tìm kiếm.
   - Cơ chế nạp động file `.py` của nhóm sinh viên khác (`agent_loader.py`) qua giao diện chung `choose_action(state, player_id)`.

## 2. Cấu trúc thư mục Task 2
```
task2_tank/
├── engine/
│   ├── actions.py           # 06 hành động (MOVE_UP/DOWN/LEFT/RIGHT, FIRE, STAY) & Direction
│   ├── entities.py          # Tank (HP 6), Base (HP 9), Wall (HP 3), Bullet (Speed 3)
│   ├── game_state.py        # Quản lý trạng thái bàn cờ, clone, terminal, utility
│   ├── rules.py             # Luật chuyển trạng thái, xử lý đạn bay và va chạm từng ô (cell-by-cell)
│   └── maps.py              # Bộ dựng bản đồ chuẩn 13x13 đối xứng
├── agents/
│   ├── base_agent.py        # Interface chung BaseAgent cho mọi AI (chuẩn tích hợp)
│   ├── evaluator.py         # Hàm đánh giá trạng thái Heuristic (HP, khoảng cách, hiểm họa đạn)
│   ├── minimax_agent.py     # Cấu hình 1: Minimax thuần
│   ├── alphabeta_agent.py   # Cấu hình 2: Minimax cắt tỉa Alpha-Beta
│   ├── heuristic_minimax_agent.py   # Cấu hình 3: Heuristic Minimax
│   ├── heuristic_alphabeta_agent.py # Cấu hình 4: Heuristic Alpha-Beta
│   └── external/
│       └── sample_rival_agent.py    # Mẫu AI của nhóm sinh viên khác
├── agent_loader.py          # Bộ nạp động plugin agent từ bên ngoài
├── ui/
│   └── pygame_ui.py         # Giao diện đồ họa PyGame điều khiển và theo dõi
├── experiments/
│   └── benchmark_tanks.py   # Kịch bản thi đấu vòng tròn 4 cấu hình và trích xuất bảng số liệu
├── main.py                  # File khởi chạy chính
└── README.md
```
