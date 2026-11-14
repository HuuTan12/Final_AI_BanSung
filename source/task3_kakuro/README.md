# Task 3: Constraint Satisfaction Problems (Kakuro CSP Solver)

Course: **Introduction to Artificial Intelligence (503043)**  
Department: Faculty of Information Technology, Ton Duc Thang University (TDTU)  

---

## 1. Objectives & Grading Breakdown (3.0 Points)

1. **Requirement 1 (1.0 pt): Formal CSP Modeling & Theoretical Foundations**
   - **Variables ($X$):** Each empty white cell $(r, c) \in \text{Variables}$.
   - **Domains ($D$):** Single digits $D_{(r, c)} \subseteq \{1, 2, \dots, 9\}$.
   - **Constraints ($C$):** For each horizontal or vertical consecutive segment (Run):
     - **Sum Constraint:** $\sum_{c_i \in \text{Run}} c_i = \text{Target Sum}$.
     - **AllDifferent Constraint:** $\text{AllDifferent}(\{c_i \mid c_i \in \text{Run}\})$.
   - **Theoretical Filtering:** Pre-filtering via valid integer partitions (Magic Sets) and arithmetic bounds pruning.
   - **Integrity Validation:** Total horizontal clue sum must strictly equal total vertical clue sum ($\sum H = \sum V$).

2. **Requirement 2 (1.0 pt): Solver Implementation & Evaluation on Complex 9x9 Benchmark**
   - **Backtracking Search** integrated with **Constraint Propagation (AC-3)** and **Forward Checking**.
   - **Variable Ordering Heuristics (MRV + Degree Heuristic):** Prioritizes white cells with minimum remaining domain values, breaking ties with the highest unassigned degree.
   - **Value Ordering Heuristic (LCV):** Selects values that rule out the fewest choices for neighboring cells.
   - **Evaluation Criteria on 9x9 Benchmark (`complex_9x9.json`):**
     - **Correctness:** 100% independent verification of all Run sums and AllDifferent uniqueness rules.
     - **Stability:** Repeated runs (5 independent trials) verifying identical solution grids and measuring runtime variance.
     - **Effectiveness (Ablation Study):** Systematic comparison between Pure Backtracking, Backtracking + MRV, Backtracking + MRV + LCV, and Full AC-3 + MRV + LCV.

3. **Requirement 3 (1.0 pt): Interactive PyGame Visualization Studio**
   - **Live Domain Pencilmarks:** Renders available candidates $\{1..9\}$ in miniature sub-cells inside each white cell.
   - **Constraint Propagation Visuals:** Color-coded flashing for pruned values (salmon red), forward checking, and dynamic domain reduction.
   - **Backtracking Animation:** Live tracking of variable assignments, dead-end detections, and undo steps.
   - **Interactive Timeline Scrubber:** Scrub back and forth across 30,000+ solver events with snapshot caching.
   - **Step Controls:** Play/Pause, Step Forward (+1), Step Backward (-1), Reset, Speed adjustment (0.5x to 4.0x), and Puzzle switching.

---

## 2. Directory Structure & OOP Architecture

```text
source/task3_kakuro/
|---- csp/
|   |---- variable.py           # Cell class: coordinates, domain {1..9}, assignment state
|   |---- constraint.py         # RunConstraint: Sum & AllDifferent, pre-computed valid partitions
|   ---- csp_problem.py        # KakuroCSP network: graph representation, integrity checker
|---- solver/
|   |---- propagators.py        # ConstraintPropagator: AC-3 and Forward Checking
|   |---- heuristics.py         # CSPHeuristics: MRV, Degree Heuristic, LCV value ordering
|   |---- tracer.py             # Observer Pattern: records solver events for live visualization
|   ---- backtracking_solver.py  # Backtracking solver engine with heuristics & timeout support
|---- puzzles/
|   |---- easy_4x4.json         # 4x4 Introductory puzzle (9 variables)
|   |---- medium_5x5.json       # 5x5 Practice puzzle (12 variables)
|   |---- sample_5x5.json       # 5x5 Benchmark from Assignment Specification (Page 4)
|   |---- test_6x6.json         # 6x6 Intermediate puzzle (22 variables)
|   |---- intermediate_7x7.json # 7x7 Intermediate puzzle (24 variables)
|   ---- complex_9x9.json      # 9x9 Complex Benchmark from Assignment Specification (Page 5)
|---- ui/
|   ---- kakuro_visualizer.py   # High-fidelity PyGame Studio (Live domains, Scrubber, HUD)
|---- experiments/
|   ---- evaluate_kakuro.py     # Independent correctness verification, stability, & ablation study
|---- kakuro.ipynb              # Executed Jupyter Notebook with 100% English outputs
|---- main.py                   # Unified CLI & GUI entry point
---- README.md                  # Comprehensive documentation
```

---

## 3. Quickstart & Execution Guide

### Prerequisites
Install the required dependencies from the root directory:
```bash
pip install pygame-ce
```

### Execution Commands

All commands can be executed from the project root directory or the `source/` folder:

#### 1. CLI Solver Mode (Solve & Print Grid in Terminal)
```bash
# Solve complex 9x9 benchmark (Page 5)
python source/task3_kakuro/main.py --cli --puzzle complex_9x9.json

# Solve 5x5 benchmark (Page 4)
python source/task3_kakuro/main.py --cli --puzzle sample_5x5.json
```

#### 2. Benchmark & Ablation Study Mode
```bash
# Run stability tests and heuristic ablation study
python source/task3_kakuro/main.py --benchmark
```

#### 3. Interactive PyGame Studio (GUI Dashboard)
```bash
# Launch interactive visualizer (defaults to sample 5x5)
python source/task3_kakuro/main.py --mode ui

# Launch visualizer directly on complex 9x9
python source/task3_kakuro/main.py --mode ui --puzzle complex_9x9.json
```

#### 4. Jupyter Notebook
Open and inspect `source/task3_kakuro/kakuro.ipynb` in VS Code or JupyterLab. All cells are pre-executed with complete English output tables.

---

## 4. Experimental Results on Complex 9x9 Benchmark

Evaluated on `complex_9x9.json` (48 white cell variables, 28 run constraints, total clue sum = 249):

| Configuration | Solved | Runtime | Explored Nodes | Backtracks | Optimization Gain |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Pure Backtracking (Arbitrary, No Heuristics)** | ❌ Timeout | > 3.0000s | > 24,000 | > 24,000 | Baseline (Exponential explosion) |
| **Backtracking + MRV** | ✅ Yes | ~0.35 - 0.45s | 35,075 | 35,027 | High pruning of search tree |
| **Backtracking + MRV + LCV** | ✅ Yes | ~0.15 - 0.18s | **11,383** | **11,335** | **67.5% reduction in explored nodes** |
| **Backtracking + AC-3 + MRV + LCV (Full)** | ✅ Yes | ~0.18 - 0.22s | **11,383** | **11,335** | Full constraint propagation |

### Key Observations:
1. **MRV (Minimum Remaining Values):** Drastically cuts down branching factor by attacking the most constrained variables first.
2. **LCV (Least Constraining Value):** Guides value assignment towards values that leave the highest flexibility for neighboring cells, reducing search nodes from 35,075 down to 11,383.
3. **Stability & Correctness:** 5/5 trials produced 100% identical solution grids with 0 constraint violations under independent verification.
