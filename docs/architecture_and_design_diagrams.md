**Môn học:** Introduction to Artificial Intelligence (503043) — Khoa CNTT, Đại học Tôn Đức Thắng (TDTU)
> 📌 **Tài liệu này cung cấp:**
> 1. Toàn bộ sơ đồ lớp hướng đối tượng (**Class Diagram OOP**) chi tiết của cả 3 Task.
> 2. Các sơ đồ tuần tự (**Sequence Diagram**) và sơ đồ quy trình (**Flowchart**) giải thích nguyên lý hoạt động của các giải thuật.
> 3. Các mẫu thiết kế (**Design Patterns**) được áp dụng: *Strategy Pattern*, *Observer Pattern*, *Plugin/Dynamic Loading Pattern*.
> 4. Toàn bộ file nguồn chuyên dụng đã được lưu tại thư mục [docs/diagrams/]
>    - **PlantUML (`.puml`):** Chuẩn chuyên dụng cho vẽ sơ đồ kỹ thuật phần mềm (mở bằng extension PlantUML trong VS Code).
>    - **Mermaid (`.mmd`):** Hiển thị trực tiếp trong Markdown của VS Code, GitHub, Overleaf và Obsidian.

---

## 1. TỔNG THỂ KIẾN TRÚC DỰ ÁN (OVERALL ARCHITECTURE)

### 1.1 Sơ đồ Phân rã Gói (Package Architecture)
```mermaid
flowchart TD
  subgraph ProjectRoot["AI_final_project / source"]
    subgraph Task1["Task 1: N-Queens (Local Search & SAT)"]
      T1_Core["task1.core\n(NQueensProblem, ConstraintGenerator)"]
      T1_Solvers["task1.solvers\n(Glucose3 SAT, Min-Conflicts, Heuristics)"]
      T1_Exp["task1.experiments\n(BenchmarkRunner)"]
      T1_NB["nqueens.ipynb\n(Jupyter Notebook)"]
      
      T1_Core --> T1_Solvers
      T1_Solvers --> T1_Exp
      T1_Exp --> T1_NB
    end

    subgraph Task2["Task 2: Tank Battle Game (Adversarial Search)"]
      T2_Engine["task2.engine\n(GameState, 6 Actions, Rules, 3-Cell Bullets)"]
      T2_Agents["task2.agents\n(Minimax, AlphaBeta, Heuristics)"]
      T2_External["task2.agents.external\n(Rival Group AI Agents)"]
      T2_Loader["agent_loader.py\n(Dynamic Plugin Loader)"]
      T2_UI["task2.ui\n(PyGame GUI & Metrics Dashboard)"]
      T2_Exp["task2.experiments\n(4 Configurations Benchmark)"]
      
      T2_Engine <--> T2_Agents
      T2_External --> T2_Loader
      T2_Loader --> T2_Agents
      T2_Engine --> T2_UI
      T2_Agents --> T2_UI
      T2_Agents --> T2_Exp
    end

    subgraph Task3["Task 3: Kakuro Puzzle (CSP)"]
      T3_Puzzles["task3.puzzles\n(5x5 & 9x9 JSON Test Cases)"]
      T3_CSP["task3.csp\n(Cell, RunConstraint, KakuroCSP)"]
      T3_Solver["task3.solver\n(Backtracking + AC-3 + MRV/LCV)"]
      T3_Tracer["task3.solver.tracer\n(Observer Pattern Subject)"]
      T3_UI["task3.ui\n(Visualizer: Domains, AC3, Backtrack)"]
      T3_Exp["task3.experiments\n(Correctness, Stability, Effectiveness)"]
      
      T3_Puzzles --> T3_CSP
      T3_CSP --> T3_Solver
      T3_Solver --> T3_Tracer
      T3_Tracer --> T3_UI
      T3_Solver --> T3_Exp
    end
  end
```
---

## 2. TASK 1: N-QUEENS (SAT & MIN-CONFLICTS)

### 2.1 Biểu đồ Lớp Chi tiết (Class Diagram OOP)
```mermaid
classDiagram
  class NQueensProblem {
    +int n
    +to_var(r, c) int
    +to_coords(var_id) tuple
    +is_valid_solution(queens) bool
    +display(queens) void
  }

  class ConstraintGenerator {
    -NQueensProblem problem
    -int n
    +generate_row_clauses() list
    +generate_col_clauses() list
    +generate_diagonal_clauses() list
    +generate_all_cnf() list
    +get_theoretical_clause_count() int
  }

  class BaseSolver {
    <<abstract>>
    +str name
    +solve(n)* SolverResult
  }

  class SolverResult {
    +bool is_solved
    +list solution
    +float execution_time
    +int num_clauses
    +int steps_taken
    +int restarts
  }

  class Glucose3SATSolver {
    +solve(n) SolverResult
    -_decode_model(model, n) list
  }

  class MinConflictsSolver {
    -VariableSelector heuristic
    -int max_steps
    -int max_restarts
    +solve(n) SolverResult
    -_initial_state(n) list
    -_count_conflicts(state, col, row) int
    -_get_conflicted_variables(state) tuple
  }

  class VariableSelector {
    <<abstract / Strategy>>
    +select_variable(conflicted_vars, conflict_counts)* int
  }

  class RandomSelector {
    +select_variable(conflicted_vars, conflict_counts) int
  }

  class MaxConflictSelector {
    +select_variable(conflicted_vars, conflict_counts) int
  }

  class HybridTabuSelector {
    -float epsilon
    -int tabu_size
    +select_variable(conflicted_vars, conflict_counts) int
  }

  class BenchmarkRunner {
    -list test_sizes
    -int num_trials
    +run_sat_experiments() void
    +run_min_conflicts_experiments() void
    +plot_comparisons(save_path) void
    +export_to_table() str
  }

  ConstraintGenerator o-- NQueensProblem : phân tích
  BaseSolver <|-- Glucose3SATSolver : kế thừa
  BaseSolver <|-- MinConflictsSolver : kế thừa
  VariableSelector <|-- RandomSelector : Baseline
  VariableSelector <|-- MaxConflictSelector : Heuristic đề xuất
  VariableSelector <|-- HybridTabuSelector : Heuristic mở rộng
  MinConflictsSolver o-- VariableSelector : áp dụng Strategy Pattern
  Glucose3SATSolver ..> ConstraintGenerator : sử dụng CNF
  BenchmarkRunner ..> BaseSolver : thực nghiệm
```

- **File PlantUML nguồn:** [task1_nqueens_class.puml]
- **Điểm sáng thiết kế OOP:**
  - **Strategy Pattern:** Lớp trừu tượng `VariableSelector` cho phép hoán đổi linh hoạt giữa chiến lược ngẫu nhiên `RandomSelector` (Baseline) và `MaxConflictSelector` (Heuristic đề xuất) mà không phải sửa lại giải thuật trong `MinConflictsSolver`.
  - **Polymorphism & Abstraction:** Cả SAT solver và Min-Conflicts solver đều kế thừa `BaseSolver` và trả về cấu trúc `SolverResult` đồng nhất để phục vụ tự động hóa đo lường.

### 2.2 Sơ đồ Quy trình Nguyên lý Hoạt động (Operational Flowchart)
```mermaid
flowchart TD
  subgraph SAT_Flow["Glucose3 SAT Flow (PySAT)"]
    S1["Khởi tạo NQueensProblem(N >= 4)"] --> S2["ConstraintGenerator sinh CNF"]
    S2 --> S3["1. Ràng buộc Hàng: ALO (N) + AMO (N*C(N,2))"]
    S2 --> S4["2. Ràng buộc Cột: ALO (N) + AMO (N*C(N,2))"]
    S2 --> S5["3. Ràng buộc Đường chéo: AMO 2 hướng"]
    S3 & S4 & S5 --> S6["Tổng hợp clauses và nạp vào Glucose3"]
    S6 --> S7{"Glucose3.solve()?"}
    S7 -- SAT --> S8["Lấy model, decode ID biến thành tọa độ (r, c)"]
    S7 -- UNSAT --> S9["Báo vô nghiệm"]
  end

  subgraph MinConflicts_Flow["Min-Conflicts Local Search Flow"]
    M1["Khởi tạo restarts = 0"] --> M2["Khởi tạo ngẫu nhiên state[col] = row"]
    M2 --> M3["Khởi tạo mảng đếm xung đột O(1)"]
    M3 --> M4{"Hết xung đột?"}
    M4 -- Đúng --> M5["Trả về nghiệm thành công"]
    M4 -- Sai --> M6{"Hết max_steps?"}
    M6 -- Hết --> M7{"restarts < max_restarts?"}
    M7 -- Còn --> M1
    M7 -- Hết --> M8["Thất bại (kẹt Local Minima)"]
    M6 -- Còn --> M9["Chọn biến xung đột qua HeuristicSelector"]
    M9 --> M10["Tìm hàng có ít xung đột nhất tại cột đó (Min-Conflict)"]
    M10 --> M11["Cập nhật vị trí quân hậu và mảng đếm xung đột"]
    M11 --> M4
  end
```

- **File PlantUML nguồn:** [task1_nqueens_flow.puml]

---

## 3. TASK 2: TANK BATTLE GAME (ADVERSARIAL SEARCH)

### 3.1 Biểu đồ Lớp Chi tiết (Class Diagram OOP)
```mermaid
classDiagram
  class Direction {
    <<Enum>>
    UP
    DOWN
    LEFT
    RIGHT
  }

  class Action {
    <<Enum>>
    MOVE_UP
    MOVE_DOWN
    MOVE_LEFT
    MOVE_RIGHT
    FIRE
    STAY
  }

  class GameEntity {
    <<abstract>>
    +int x
    +int y
    +int hp
    +is_alive() bool
    +take_damage(damage) void
  }

  class Tank {
    +int INITIAL_HP = 6
    +int player_id
    +Direction direction
    +clone() Tank
  }

  class Base {
    +int INITIAL_HP = 9
    +int player_id
    +clone() Base
  }

  class Wall {
    +int INITIAL_HP = 3
    +clone() Wall
  }

  class Bullet {
    +int SPEED = 3
    +int x
    +int y
    +Direction direction
    +int owner_id
    +bool is_active
    +clone() Bullet
  }

  class GameState {
    +int width
    +int height
    +dict tanks
    +dict bases
    +dict walls
    +list bullets
    +int current_player
    +int game_cycle
    +clone() GameState
    +get_legal_actions(player_id) list
    +is_terminal() bool
    +get_winner() int
    +get_utility(player_id) float
  }

  class GameRules {
    +apply_action(state, action)$ GameState
    +step_bullets(state)$ void
    -_move_tank(state, player_id, direction)$ void
    -_fire_bullet(state, player_id)$ void
  }

  class BaseAgent {
    <<abstract>>
    +str name
    +SearchStats stats
    +choose_action(state, player_id)* Action
    +reset_stats() void
  }

  class TankEvaluator {
    +evaluate(state, player_id) float
  }

  class MinimaxAgent {
    -int depth
    +choose_action(state, player_id) Action
  }

  class AlphaBetaAgent {
    -int depth
    +choose_action(state, player_id) Action
  }

  class HeuristicMinimaxAgent {
    -int depth
    -TankEvaluator evaluator
    +choose_action(state, player_id) Action
  }

  class HeuristicAlphaBetaAgent {
    -int depth
    -TankEvaluator evaluator
    +choose_action(state, player_id) Action
  }

  class RivalGroupAgent {
    +choose_action(state, player_id) Action
  }

  class AgentLoader {
    +load_agent_from_file(file_path)$ BaseAgent
    +discover_external_agents(folder_path)$ list
  }

  GameEntity <|-- Tank
  GameEntity <|-- Base
  GameEntity <|-- Wall
  GameState *-- Tank
  GameState *-- Base
  GameState *-- Wall
  GameState *-- Bullet
  BaseAgent <|-- MinimaxAgent
  BaseAgent <|-- AlphaBetaAgent
  BaseAgent <|-- HeuristicMinimaxAgent
  BaseAgent <|-- HeuristicAlphaBetaAgent
  BaseAgent <|-- RivalGroupAgent
  HeuristicMinimaxAgent o-- TankEvaluator
  HeuristicAlphaBetaAgent o-- TankEvaluator
  GameRules ..> GameState
  AgentLoader ..> BaseAgent
```

- **File PlantUML nguồn:** [task2_tank_class.puml]
- **Điểm sáng thiết kế OOP:**
  - **Kế thừa & Đóng gói Entity:** `GameEntity` đóng gói `x`, `y`, `hp`, `take_damage()` giúp tái sử dụng mã cho `Tank` (HP 6), `Base` (HP 9), và `Wall` (HP 3).
  - **Interface chuẩn `BaseAgent`:** Cung cấp hàm `choose_action(state, player_id)`. Mọi thuật toán (của nhóm hay của nhóm sinh viên khác) đều kế thừa từ lớp này.
  - **Dynamic Plugin Loader (`AgentLoader`):** Sử dụng thư viện `importlib` của Python để nạp động các file `.py` ngoài mà không cần sửa code hệ thống.

### 3.2 Sơ đồ Tuần tự Một Chu kỳ Game (Game Cycle Sequence Diagram)
Sơ đồ minh họa nguyên lý xử lý đạn bay **3 ô / cycle** và **kiểm tra va chạm cell-by-cell**:

```mermaid
sequenceDiagram
  autonumber
  participant Loop as GameEngine / Main
  participant GUI as PygameUI
  participant S as GameState
  participant P0 as Agent P0 (MAX)
  participant P1 as Agent P1 (MIN)
  participant R as GameRules
  participant E as Entities (Wall/Tank/Base)

  loop Mỗi Game Cycle
    Loop->>P0: choose_action(state, 0)
    P0-->>Loop: action_p0 (ví dụ FIRE hoặc MOVE_UP)
    Loop->>R: apply_action(state, action_p0)
    
    Loop->>P1: choose_action(state, 1)
    P1-->>Loop: action_p1
    Loop->>R: apply_action(state, action_p1)
    
    rect rgb(240, 248, 255)
      note over R, E: Xử lý đạn: Tối đa 3 ô, kiểm tra va chạm TỪNG Ô (Cell-by-Cell)
      loop Bước k = 1, 2, 3
        R->>R: Di chuyển đạn 1 ô theo hướng bắn
        R->>S: check_collision(bullet.x, bullet.y)
        alt Trúng Tường (Wall)
          R->>E: wall.take_damage(1)
          R->>R: Đạn dừng & biến mất ngay lập tức (is_active = False)
        else Trúng Tank
          R->>E: tank.take_damage(1)
          R->>R: Đạn dừng & biến mất ngay lập tức
        else Trúng Base
          R->>E: base.take_damage(1)
          R->>R: Đạn dừng & biến mất ngay lập tức
        else Vượt biên
          R->>R: Đạn biến mất
        end
      end
    end
    
    Loop->>S: is_terminal()
    alt Game Kết Thúc (Base hoặc Tank HP <= 0)
      S-->>Loop: True (Game Over)
      Loop->>GUI: render_game_over(winner)
    else Tiếp tục
      Loop->>GUI: render(state, p0, p1)
    end
  end
```

- **File PlantUML nguồn:** [task2_tank_sequence.puml]

---

## 4. TASK 3: KAKURO PUZZLE (CSP)

### 4.1 Biểu đồ Lớp Chi tiết (Class Diagram OOP)
```mermaid
classDiagram
  class Cell {
    +int r
    +int c
    +tuple pos
    +set domain
    +int value
    +is_assigned() bool
    +assign(val) void
    +unassign() void
  }

  class RunConstraint {
    +str direction
    +int target_sum
    +list cells
    +int length
    +get_valid_combinations() list
    +is_satisfied() bool
    +is_partially_valid() bool
  }

  class KakuroCSP {
    +int rows
    +int cols
    +dict variables
    +list runs
    +load_from_json(path) void
    +validate_puzzle_integrity() bool
    +is_solved() bool
  }

  class EventType {
    <<Enum>>
    INITIAL_DOMAINS
    ASSIGN
    PRUNE
    RESTORE
    BACKTRACK
    SOLVED
    NO_SOLUTION
  }

  class SolverEvent {
    +EventType event_type
    +tuple cell_pos
    +int value
    +set pruned_domain
    +str message
  }

  class SolverTracer {
    <<Subject / Observer Pattern>>
    +list events
    +emit(event_type, ...) void
    +clear() void
  }

  class ConstraintPropagator {
    -SolverTracer tracer
    +initial_filtering(csp) bool
    +ac3(csp, queue) bool
    +forward_check(csp, var, val) dict
  }

  class CSPHeuristics {
    +select_unassigned_variable_mrv(csp)$ Cell
    +order_domain_values_lcv(csp, var)$ list
  }

  class KakuroBacktrackingSolver {
    -bool use_ac3
    -bool use_mrv
    -bool use_lcv
    -SolverTracer tracer
    +int nodes_explored
    +int backtracks
    +solve(csp) KakuroSolveResult
    -_backtrack(csp) bool
  }

  class KakuroVisualizer {
    <<Observer>>
    -KakuroCSP csp
    -SolverTracer tracer
    +run() void
    +draw_board() void
    +step_forward() void
    +step_backward() void
  }

  class KakuroEvaluator {
    +verify_correctness(solution, csp) bool
    +test_stability(num_runs) dict
    +run_ablation_study() list
  }

  KakuroCSP *-- Cell
  KakuroCSP *-- RunConstraint
  RunConstraint o-- Cell
  KakuroBacktrackingSolver o-- ConstraintPropagator
  KakuroBacktrackingSolver ..> CSPHeuristics
  KakuroBacktrackingSolver o-- SolverTracer
  SolverTracer *-- SolverEvent
  SolverEvent o-- EventType
  KakuroVisualizer o-- SolverTracer : Observer lắng nghe sự kiện
  KakuroVisualizer o-- KakuroCSP
  KakuroEvaluator ..> KakuroCSP
  KakuroEvaluator ..> KakuroBacktrackingSolver
```

- **File PlantUML nguồn:** [task3_kakuro_class.puml]
- **Điểm sáng thiết kế OOP:**
  - **Observer Pattern:** Tách rời hoàn toàn thuật toán tìm kiếm (`KakuroBacktrackingSolver`) khỏi giao diện đồ họa (`KakuroVisualizer`). Khi solver thực hiện gán (`ASSIGN`), tỉa miền giá trị (`PRUNE`), hoặc quay lui (`BACKTRACK`), nó phát sự kiện tới `SolverTracer`. `KakuroVisualizer` chỉ cần duyệt danh sách sự kiện này để vẽ trực quan hóa từng bước mượt mà (có thể Pause, Step, Reverse).

### 4.2 Sơ đồ Tuần tự Observer Pattern giữa Solver, Tracer và UI
```mermaid
sequenceDiagram
  autonumber
  participant Client as Evaluator / Main
  participant CSP as KakuroCSP
  participant Tracer as SolverTracer (Subject)
  participant Solver as KakuroBacktrackingSolver
  participant Prop as ConstraintPropagator (AC-3)
  participant UI as KakuroVisualizer (Observer)

  Client->>CSP: load_from_json("complex_9x9.json")
  Client->>CSP: validate_puzzle_integrity()
  Client->>Tracer: new SolverTracer()
  Client->>Solver: new Solver(tracer=Tracer)
  Client->>UI: new KakuroVisualizer(csp, tracer=Tracer)

  Client->>Solver: solve(csp)
  activate Solver
  Solver->>Prop: initial_filtering() + ac3()
  Prop->>Tracer: emit(PRUNE, cell=(1,2), {6,7,8,9})
  
  loop Quá trình Backtracking
    Solver->>Solver: select_variable_mrv()
    Solver->>Solver: order_domain_values_lcv()
    Solver->>CSP: cell.assign(val)
    Solver->>Tracer: emit(ASSIGN, cell=(r,c), val)
    Solver->>Prop: forward_check() / ac3()
    alt Domain Wipeout (Bế tắc)
      Prop-->>Solver: False
      Solver->>CSP: cell.unassign()
      Solver->>Tracer: emit(BACKTRACK, cell=(r,c))
    else Hợp lệ
      Prop-->>Solver: True
      Solver->>Solver: _backtrack(csp) [Đệ quy tiếp]
    end
  end
  
  Solver->>Tracer: emit(SOLVED)
  Solver-->>Client: Result(is_solved=True)
  deactivate Solver

  Client->>UI: run() (Phát lại trực quan)
  loop Duyệt qua từng sự kiện trong Tracer (Step / Play)
    UI->>Tracer: get_event(idx)
    Tracer-->>UI: SolverEvent (ASSIGN / PRUNE / BACKTRACK)
    UI->>UI: Render màu sắc (Vàng: Assign, Đỏ: Prune, Cam: Backtrack)
  end
```

- **File PlantUML nguồn:** [task3_kakuro_sequence.puml]
### 4.3 Sơ đồ Quy trình Thuật toán CSP Kakuro (Solver Flowchart)
```mermaid
flowchart TD
  Start["Bắt đầu: Đọc file JSON (5x5 hoặc 9x9)"] --> Val{"Tổng Clue Ngang == Tổng Clue Dọc?"}
  Val -- Không --> Err["Báo lỗi sai đề (Clue Inconsistency)"]
  Val -- Đúng --> Pre["Tiền xử lý: Sinh các bộ số hợp lệ (Valid Combinations) theo Run"]
  
  Pre --> AC3_Init["Chạy AC-3 ban đầu thu hẹp miền giá trị của từng ô"]
  AC3_Init --> CheckEmpty{"Có ô nào bị rỗng Domain?"}
  CheckEmpty -- Có --> Unsat["Bài toán vô nghiệm ngay từ đầu"]
  CheckEmpty -- Không --> BT["Bắt đầu Backtracking Search"]
  
  BT --> Complete{"Tất cả ô đã được gán?"}
  Complete -- Đúng --> Solved["Kiểm tra Correctness độc lập -> Trả về Nghiệm"]
  Complete -- Chưa --> MRV["Chọn biến có ít giá trị nhất (Heuristic MRV)"]
  MRV --> LCV["Sắp xếp thứ tự thử giá trị (Heuristic LCV)"]
  
  LCV --> TryVal["Gán cell.assign(v) + lưu snapshot Domain"]
  TryVal --> MAC["Lan truyền ràng buộc (MAC / Forward Checking)"]
  MAC --> Wipeout{"Domain Wipeout?"}
  Wipeout -- Có (Nhánh chết) --> Undo["Undo gán + Undo Prune -> Ghi nhận BACKTRACK"]
  Undo --> MoreVal{"Còn giá trị khác trong LCV?"}
  MoreVal -- Còn --> TryVal
  MoreVal -- Hết --> BackPrevious["Quay lui lên tầng đệ quy trước"]
  
  Wipeout -- Không --> Recurse["Đệ quy _backtrack() tầng tiếp theo"]
  Recurse --> Found{"Tìm thấy nghiệm ở nhánh con?"}
  Found -- Có --> Solved
  Found -- Không --> Undo
```

- **File PlantUML nguồn:** [task3_kakuro_flow.puml]

---

## 5. BẢNG TỔNG HỢP CÁC FILE SƠ ĐỒ CHUYÊN DỤNG TRONG THƯ MỤC `docs/diagrams/`

| Tên File | Định dạng | Nội dung sơ đồ |
| :--- | :---: | :--- |
| [overall_architecture.puml]| PlantUML | Kiến trúc tổng thể toàn bộ hệ thống dự án |
| [overall_architecture.mmd]| Mermaid | Kiến trúc tổng thể dạng sơ đồ Mermaid |
| [task1_nqueens_class.puml]| PlantUML | Biểu đồ lớp chi tiết Task 1 (Strategy Pattern Heuristic) |
| [task1_nqueens_flow.puml]| PlantUML | Quy trình Glucose3 SAT & Min-Conflicts Local Search |
| [task1_diagrams.mmd]| Mermaid | Sơ đồ lớp Task 1 hiển thị bằng Mermaid |
| [task2_tank_class.puml]| PlantUML | Biểu đồ lớp chi tiết Task 2 (Entities, 4 AI Agents, Loader) |
| [task2_tank_sequence.puml]| PlantUML | Sơ đồ tuần tự 1 Game Cycle & va chạm đạn cell-by-cell |
| [task2_diagrams.mmd]| Mermaid | Sơ đồ lớp Task 2 hiển thị bằng Mermaid |
| [task3_kakuro_class.puml]| PlantUML | Biểu đồ lớp chi tiết Task 3 (CSP, Observer Pattern, UI) |
| [task3_kakuro_sequence.puml]| PlantUML | Sơ đồ tuần tự Observer Pattern giữa Solver, Tracer và UI |
| [task3_kakuro_flow.puml]| PlantUML | Quy trình giải CSP: AC-3, MRV, LCV và Backtracking |
| [task3_diagrams.mmd]| Mermaid | Sơ đồ lớp Task 3 hiển thị bằng Mermaid |
| [architecture_and_design_diagrams.md]| Markdown | Toàn bộ tài liệu phân tích thiết kế kèm preview Mermaid trực quan |