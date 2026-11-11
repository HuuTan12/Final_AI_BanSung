# Final Project: Introduction to Artificial Intelligence (503043)
**Faculty of Information Technology - Ton Duc Thang University**

---

## 1. Project Overview
This repository contains the complete implementation for the Introduction to Artificial Intelligence Final Project, covering three fundamental AI paradigms:
- **Task 1: Local Search & Propositional Logic (N-Queens Problem)**
  - Propositional Logic formulation with $N^2$ boolean variables, ALO/AMO CNF constraints derivation.
  - SAT solver using **Glucose3** via `python-sat` (PySAT) scaling across $N \ge 4$.
  - **Min-Conflicts** local search with standard random selection vs. proposed heuristics (**Max-Conflict** and **Hybrid-Tabu**).
  - Comparative benchmarks, scaling plots, and interactive chessboard UI.
- **Task 2: Adversarial Search (Tank Battle Game)**
  - Formulated as a 2-player Zero-Sum Game with cell-by-cell bullet physics (speed 3 cells/cycle), 6 actions, and HP rules (Tank: 6, Base: 9, Wall: 3).
  - Comparative benchmark across 4 AI search configurations:
    1. Minimax Search
    2. Alpha-Beta Search
    3. Heuristic Minimax Search
    4. Heuristic Alpha-Beta Pruning
  - Head-to-head round-robin tournament and real-time execution optimization.
  - Graphical User Interface built with **PyGame** featuring live telemetry, map cycling (9 maps), step-by-step debugging, and dynamic external agent plugin loading.
- **Task 3: Constraint Satisfaction Problems (Kakuro)**
  - Formal CSP formulation with pre-computed combination tables, cell variable domains $\{1..9\}$, sum & all-different constraints.
  - Solver combining **Constraint Propagation (AC-3)** and **Backtracking Search** with **MRV** (Minimum Remaining Values) and **LCV** (Least Constraining Value).
  - Rigorous evaluation on the complex $9 \times 9$ puzzle across **Correctness** (100%), **Stability** (identical nodes and backtracks), and **Effectiveness** (Ablation study).
  - PyGame interactive visualizer displaying variable domains (3x3 pencil marks), constraint propagation, and search backtracking.
- **Task 4: IEEE Conference Report & Interview Preparation**
  - 5-page IEEE conference paper in two-column format with formal problem formulations, theoretical proofs, benchmark tables, and ablation comparisons.

---

## 2. Environment Setup & Installation
The codebase is fully compatible with **macOS 13.7.8 (Ventura) Intel Core i5**, **Windows 10/11**, and **Linux**.

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- `pip` package manager

### Installation
Clone or navigate to the repository folder:
```bash
cd Final_AI_BanSung
pip install -r requirements.txt
```

---

## 3. How to Run Each Task

### Task 1: N-Queens Problem
```bash
# Run Jupyter Notebook with preserved cell outputs:
jupyter notebook source/task1_nqueens/nqueens.ipynb

# Run automated Glucose3 and Min-Conflicts benchmark runner:
cd source/task1_nqueens
python experiments/benchmark.py

# Launch interactive Pygame UI for N-Queens:
python main.py
```

### Task 2: Tank Battle Game
```bash
cd source/task2_tank

# 1. Run full interactive PyGame GUI (P0: Heuristic Alpha-Beta vs P1: Rival Bot):
python main.py

# 2. Play as Human against Heuristic Alpha-Beta AI:
python main.py --p0 human --p1 heuristic_alphabeta

# 3. Load an external rival agent from other student groups:
python main.py --p0 heuristic_alphabeta --load_external agents/external/sample_rival_agent.py

# 4. Run automated 4-configuration benchmark and head-to-head tournament:
python main.py --mode benchmark
```

### Task 3: Kakuro CSP Solver
```bash
cd source/task3_kakuro

# 1. Run interactive PyGame Visualizer (Domains, AC-3, Backtracking):
python main.py
# (or explicitly: python main.py --mode ui)

# 2. Solve puzzles directly in terminal with full verification:
python main.py --mode solve --puzzle sample_5x5.json
python main.py --mode solve --puzzle complex_9x9.json

# 3. Run automated evaluation suite (Correctness, Stability, Ablation study):
python main.py --mode eval

# 4. Run Jupyter Notebook with preserved cell outputs:
jupyter notebook kakuro.ipynb
```

---

## 4. Repository Structure
```
Final_AI_BanSung/
├── requirements.txt         # Project dependencies
├── README.md                # General setup and running instructions
├── demo.txt                 # URL to recorded video demonstration
├── docs/
│   ├── 2627-HK1-AI-CK.pdf   # Official course assignment requirements
│   ├── report_structure_guide.md
│   └── architecture_and_design_diagrams.md
└── source/
    ├── task1_nqueens/       # Task 1: Propositional Logic & Min-Conflicts
    │   ├── core/            # Problem definitions and CNF generator
    │   ├── solvers/         # Glucose3 SAT and Min-Conflicts solvers
    │   ├── experiments/     # Benchmarks and evaluation scripts
    │   ├── ui/              # Pygame UI and Matplotlib visualizer
    │   ├── nqueens.ipynb    # Executed notebook with preserved cell outputs
    │   └── main.py
    ├── task2_tank/          # Task 2: Adversarial Search (Tank Battle)
    │   ├── engine/          # Game physics, rules, actions, entities, maps
    │   ├── agents/          # Minimax, AlphaBeta, Heuristics, External loader
    │   ├── experiments/     # Tournament and 4-agent search benchmark
    │   ├── ui/              # Pygame battle simulator and telemetry
    │   ├── maps/            # 9 ASCII map configurations
    │   └── main.py
    └── task3_kakuro/        # Task 3: Constraint Satisfaction Problems
        ├── csp/             # Variable, RunConstraint, and KakuroCSP classes
        ├── solver/          # AC-3, Forward Checking, MRV, LCV, Backtracking
        ├── experiments/     # Correctness, Stability, and Ablation study
        ├── puzzles/         # sample_5x5.json and complex_9x9.json
        ├── ui/              # Pygame Visualizer for domains and backtracking
        ├── kakuro.ipynb     # Executed notebook with preserved cell outputs
        └── main.py
```

