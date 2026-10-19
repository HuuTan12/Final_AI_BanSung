# Task 2: Adversarial Search (Tank Battle Game)

Course: **Introduction to Artificial Intelligence (503043)**  
Faculty of Information Technology, Ton Duc Thang University (TDTU).

---

## 1. Objectives & Grading Breakdown (3.0 Points)

1. **Requirement 1 (1.0 pt): Zero-Sum Game Formulation & Theoretical Foundations**
   - Formal mathematical formulation: $\mathcal{G} = \langle S_0, PLAYER, ACTIONS, RESULT, TERMINAL\text{-}TEST, UTILITY \rangle$.
   - Entities and attributes:
     - **Tank**: Initial HP = 6, damage taken = 1/hit, 4 compass directions.
     - **Base**: Initial HP = 9, damage taken = 1/hit.
     - **Wall**: Initial HP = 3, damage taken = 1/hit (destroyed when HP = 0).
     - **Bullet**: Speed = 3 cells per game cycle, collision checked **cell-by-cell**.
   - 6 Legal Tank Actions: `MOVE_UP`, `MOVE_DOWN`, `MOVE_LEFT`, `MOVE_RIGHT`, `FIRE`, `STAY`.
   - Adversarial search algorithm review (Lecture 07): Minimax, Alpha-Beta Pruning, Heuristic Minimax.

2. **Requirement 2 (1.5 pt): Implementation & Benchmark of 4 AI Configurations**
   - **Configuration 1:** `MinimaxAgent` - Pure depth-first minimax tree search.
   - **Configuration 2:** `AlphaBetaAgent` - Minimax with $[\alpha, \beta]$ branch pruning.
   - **Configuration 3:** `HeuristicMinimaxAgent` - Depth cutoff with linear heuristic evaluation $EVAL(s)$.
   - **Configuration 4:** `HeuristicAlphaBetaAgent` - Heuristic Minimax with Alpha-Beta pruning and move ordering.
   - Comparative benchmark on identical scenarios measuring: execution time, explored states (nodes), search depth, and match performance.

3. **Requirement 3 (0.5 pt): PyGame Graphical Interface & External Agent Plugin System**
   - Responsive PyGame GUI rendering grid, entities, health bars, active bullets, and live search HUD.
   - Dynamic plugin loader (`AgentLoader`) using Python's `importlib` and `inspect` to import external rival group agents (`agents/external/*.py`) without modifying game code.

---

## 2. Directory Structure & OOP Architecture

```text
source/task2_tank/
├── maps/                    # Human-readable ASCII maps (.txt)
│   ├── 01_classic_battlecity.txt
│   ├── 02_open_duel.txt
│   ├── 03_tactical_maze.txt
│   └── 04_fortress_siege.txt
├── engine/
│   ├── actions.py           # 6 Actions (MOVE_*, FIRE, STAY) and Direction enum
│   ├── entities.py          # Tank (HP 6), Base (HP 9), Wall (HP 3), Bullet (Speed 3)
│   ├── game_state.py        # GameState: grid, entities, turn management, terminal test, utility
│   ├── rules.py             # GameRules: transition function RESULT(s, a), cell-by-cell collision
│   ├── map_loader.py        # MapLoader: dynamic ASCII parser, validation, and map cycling
│   └── maps.py              # MapBuilder: programmatic map generators and fallback builders
├── agents/
│   ├── base_agent.py        # Abstract BaseAgent interface and SearchStats dataclass
│   ├── evaluator.py         # TankEvaluator: linear weighted heuristic EVAL(s)
│   ├── minimax_agent.py     # Config 1: Pure Minimax Search
│   ├── alphabeta_agent.py   # Config 2: Alpha-Beta Pruning Search
│   ├── heuristic_minimax_agent.py   # Config 3: Heuristic Minimax Search
│   ├── heuristic_alphabeta_agent.py # Config 4: Heuristic Alpha-Beta Search (Optimal)
│   └── external/
│       └── sample_rival_agent.py    # Example rival agent from another student group
├── agent_loader.py          # Dynamic plugin loader for external student code
├── ui/
│   └── pygame_ui.py         # Pygame GUI with live HUD, in-game map switcher, particle FX
├── experiments/
│   └── benchmark_tanks.py   # Comparative benchmark and tournament runner
├── main.py                  # CLI entrypoint for GUI and Benchmark modes
└── README.md                # Task 2 documentation
```

---

## 3. How to Run

### A. Run in Benchmark Mode (Headless / Performance Evaluation)
```bash
python -m task2_tank.main --mode benchmark --max_cycles 25
```
This runs:
1. Single-move search benchmark across depths $d = 1, 2, 3$.
2. Round-robin tournament between all pairs of configurations.
3. Automatically generates the comparison plot `benchmark_task2.png`.
4. Outputs Markdown summary tables for the IEEE report.

### B. Run Interactive PyGame GUI Match
```bash
# Standard Battle City Map (Default)
python -m task2_tank.main --mode gui --p0 heuristic_alphabeta --p1 alphabeta --map standard

# Open Duel Map (Minimal cover)
python -m task2_tank.main --mode gui --p0 heuristic_alphabeta --p1 alphabeta --map open

# Tactical Chokepoint / Labyrinth Map (Corridors & breaches)
python -m task2_tank.main --mode gui --p0 heuristic_alphabeta --p1 alphabeta --map chokepoint
```
**Interactive Command Deck & Keyboard Controls:**
- `SPACE`: Pause / Resume match.
- `S` or `ENTER` or `Right Arrow`: Step one action forward (+1).
- `U` or `Z` or `Backspace` or `Left Arrow`: Undo last action (-1 state rollback).
- `R`: Reset match to initial state.
- `1` / `2` / `3`: Speed presets (1x = 15 FPS, 2x = 30 FPS, 4x Turbo = 60 FPS).
- `ESC`: Exit game.

### C. Play Against External Rival Group Agent (Plugin System)
```bash
python -m task2_tank.main --mode gui --p0 heuristic_alphabeta --load_external source/task2_tank/agents/external/sample_rival_agent.py
```

---

## 4. Summary of Experimental Results (Req 2)

### A. Search Efficiency (Single Decision Move at Root)
| Depth | Algorithm Configuration | Explored Nodes | Prune Count | Execution Time (s) | Chosen Action |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | 1. Minimax Search | 6 | 0 | 0.00015 | `MOVE_LEFT` |
| 1 | 2. Alpha-Beta Search | 6 | 0 | 0.00015 | `MOVE_LEFT` |
| 1 | 3. Heuristic Minimax | 6 | 0 | 0.00030 | `MOVE_LEFT` |
| 1 | 4. Heuristic Alpha-Beta | 6 | 0 | 0.00028 | `MOVE_LEFT` |
| 2 | 1. Minimax Search | 36 | 0 | 0.00095 | `MOVE_LEFT` |
| 2 | 2. Alpha-Beta Search | 22 | 4 | 0.00058 | `MOVE_LEFT` |
| 2 | 3. Heuristic Minimax | 36 | 0 | 0.00192 | `MOVE_LEFT` |
| 2 | 4. Heuristic Alpha-Beta | 18 | 6 | 0.00092 | `MOVE_LEFT` |
| 3 | 1. Minimax Search | 216 | 0 | 0.00620 | `MOVE_LEFT` |
| 3 | 2. Alpha-Beta Search | 68 | 24 | 0.00198 | `MOVE_LEFT` |
| 3 | 3. Heuristic Minimax | 216 | 0 | 0.01250 | `MOVE_LEFT` |
| 3 | 4. Heuristic Alpha-Beta | 44 | 32 | 0.00245 | `MOVE_LEFT` |

**Key Observations:**
1. **Identical Optimal Decisions:** Both Minimax and Alpha-Beta choose the exact same actions at every depth, confirming the mathematical soundness of Alpha-Beta pruning (Lecture 07 - Slide 16).
2. **Exponential Node Reduction:** Alpha-Beta reduces explored nodes by **68% - 80%** at depth 3, cutting execution time accordingly.
3. **Move Ordering Advantage:** Heuristic Alpha-Beta with move ordering explores the fewest states (44 nodes vs 216 nodes for Minimax), operating well within the real-time threshold ($< 5\text{ms}$ per move).
