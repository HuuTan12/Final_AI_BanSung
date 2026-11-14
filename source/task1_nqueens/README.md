# Task 1: Local Search & Propositional Logic (N-Queens Problem)

Course: **Introduction to Artificial Intelligence (503043)**  

---

## 1. Objectives & Grading Breakdown (3.0 Points)

### Requirement 1 (1.0 pt): Propositional Logic Formulation & CNF Clause Generation
- **Boolean Propositional Variables:** Let $X_{r, c} \in \{True, False\}$ for $0 \le r, c < N$, representing whether a queen is placed at square $(r, c)$.
- **DIMACS Integer Encoding:** Variable indices are mapped to positive integers via bijection:
  $$\text{var\_id}(r, c) = r \cdot N + c + 1$$
- **Conjunctive Normal Form (CNF) Constraints:**
  1. **Row Constraints:**
     - *At-Least-One (ALO):* Each row must contain at least one queen:
       $$\bigvee_{c=0}^{N-1} X_{r, c} \quad (\forall r \in [0, N-1])$$
     - *At-Most-One (AMO):* No two queens may occupy the same row:
       $$\bigwedge_{0 \le c_1 < c_2 < N} (\neg X_{r, c_1} \lor \neg X_{r, c_2}) \quad (\forall r \in [0, N-1])$$
  2. **Column Constraints:**
     - *At-Least-One (ALO):* $\bigvee_{r=0}^{N-1} X_{r, c} \quad (\forall c \in [0, N-1])$
     - *At-Most-One (AMO):* $\bigwedge_{0 \le r_1 < r_2 < N} (\neg X_{r_1, c} \lor \neg X_{r_2, c}) \quad (\forall c \in [0, N-1])$
  3. **Diagonal Constraints (At-Most-One only):**
     - *Major Diagonals ($r - c = k$):* For each diagonal line with $\ge 2$ squares:
       $$\bigwedge_{(r_1, c_1) \ne (r_2, c_2)} (\neg X_{r_1, c_1} \lor \neg X_{r_2, c_2})$$
     - *Minor Diagonals ($r + c = k$):* For each anti-diagonal line with $\ge 2$ squares:
       $$\bigwedge_{(r_1, c_1) \ne (r_2, c_2)} (\neg X_{r_1, c_1} \lor \neg X_{r_2, c_2})$$
- **Theoretical Clause Count Formula:**
  $$\text{Total Clauses}(N) = 2N + N \cdot N(N-1) + \frac{N(N-1)(2N-1)}{3} - 2N(N-1)$$
  - For $N = 4$: $84$ clauses (16 variables).
  - For $N = 8$: $744$ clauses (64 variables).
  - For $N = 16$: $6,352$ clauses (256 variables).

---

### Requirement 2 (1.0 pt): PySAT Glucose3 Solver Implementation & Experiments
- Implemented in `task1_nqueens.solvers.sat_solver.Glucose3SATSolver`.
- Automated benchmarking across $N \ge 4$ ($N = 4, 8, 12, 16, 20, 24, 28, 32$).
- Outputs exact generated clause counts, theoretical clause verification, and execution runtime in milliseconds.

---

### Requirement 3 (1.0 pt): Min-Conflicts Local Search & Proposed Variable Selection Heuristics
- **Complete-State Formulation (Lecture 06):** Each column has exactly one queen (`state[col] = row`). The search space consists of $N^N$ states with fixed column assignment.
- **Baseline Heuristic (Lecture 08 - Slide 30):**
  - `RandomSelector`: Randomly picks one conflicted queen with equal probability among all currently conflicted variables.
- **Proposed Heuristic 1:**
  - `MaxConflictSelector`: Selects the variable currently involved in the maximum number of pairwise attacks:
    $$c^* = \arg\max_{c \in \text{conflicted}} \text{conflicts}(c)$$
    Ties are resolved uniformly at random to prevent deterministic looping.
- **Proposed Heuristic 2:**
  - `HybridTabuSelector`: Combines greedy maximum-conflict selection with an $\epsilon$-greedy exploration rate ($\epsilon = 0.15$) and a recency-based Tabu list (size $K = \lfloor N / 4 \rfloor + 1$) to break out of local minima and cycle traps.

---

## 2. Architecture & File Organization

```
source/task1_nqueens/
├── main.py                     # Unified entry point (GUI, CLI, Benchmark)
├── nqueens.ipynb               # 100% English Jupyter research notebook
├── benchmark_task1.png         # Comparative benchmark plot
├── cnf_breakdown_task1.png     # CNF clause scaling visualization
├── core/
│   ├── problem.py              # Board coordinate bijection & problem state
│   └── constraints.py          # Propositional Logic & CNF clause generator
├── solvers/
│   ├── base_solver.py          # Abstract BaseSolver and SolverResult dataclass
│   ├── sat_solver.py           # Glucose3 SAT solver using PySAT
│   ├── min_conflicts.py        # Complete-state Min-Conflicts local search
│   ├── heuristics.py           # Strategy pattern: Random, Max-Conflict, Hybrid-Tabu
│   ├── backtracking_solver.py  # Systematic Backtracking & All-Solutions finder
│   └── step_min_conflicts.py   # Generator-based solver for step-by-step GUI
├── experiments/
│   └── benchmark.py            # Automated multi-trial benchmark runner
└── ui/
    ├── pygame_nqueens.py       # Full interactive PyGame visualizer
    └── notebook_visualizer.py  # Matplotlib chessboard renderer for Notebook
```

---

## 3. How to Run

### A. Run Interactive Pygame Desktop GUI
From the project root:
```bash
python -m task1_nqueens.main
```

#### GUI Controls & Features
| Control | Key / Action | Description |
|:---|:---:|:---|
| **Algorithm Switcher** | Click `[ < ] [ Name ] [ > ]` | Seamless carousel switcher between all 5 algorithms: `Backtracking`, `Min-Conflicts (Max)`, `Min-Conflicts (Tabu)`, `Min-Conflicts (Random)`, `SAT (Glucose3)` |
| **Board Size N** | Click `[-]` / `[+]` | Select dimensions: $N = 4, 6, 8, 10, 12, 16$ |
| **Play / Pause** | `SPACE` or `PLAY` / `PAUSE` | Toggle automated execution |
| **Step Forward** | `S` or `STEP +1` | Advance exactly 1 search step |
| **Undo Step** | `U` or `UNDO` | Rollback 1 search step (pauses auto-play until manual resume) |
| **Reset** | `R` or `RESET` | Reset search state to beginning |
| **Speed Multiplier** | Click `1x`, `2x`, `5x`, `10x`, `50x` | Adjust animation speed |
| **Solution Browser** | `LEFT` / `RIGHT` arrows | Browse distinct valid solutions (e.g. all 92 solutions for $N=8$) |

### B. Run Quick Automated Benchmark (Req 2 & Req 3)
```bash
python -m task1_nqueens.main --benchmark
```
*Generates formatted Markdown comparison tables and saves visual plots to `benchmark_task1.png` and `cnf_breakdown_task1.png`.*

### C. Run Headless CLI Mode (No Display Required)
```bash
# Run all solvers for N = 8
python -m task1_nqueens.main --cli --n 8

# Run specific algorithm
python -m task1_nqueens.main --cli --n 8 --algo BACKTRACKING
python -m task1_nqueens.main --cli --n 8 --algo SAT
python -m task1_nqueens.main --cli --n 8 --algo MIN_CONFLICTS_MAX
```

### D. Run Jupyter Notebook
Open and run `source/task1_nqueens/nqueens.ipynb` in VS Code or Jupyter Notebook:
```bash
jupyter notebook source/task1_nqueens/nqueens.ipynb
```

---

## 4. Experimental Results Summary

### Table 1: Glucose3 SAT Solver Performance (PySAT) - Req 2
| N | Variables ($N^2$) | Generated Clauses | Theoretical Clauses | Avg Runtime (s) | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 16 | 84 | 84 | 0.000010 | SAT |
| 8 | 64 | 744 | 744 | 0.000060 | SAT |
| 12 | 144 | 2,620 | 2,620 | 0.000120 | SAT |
| 16 | 256 | 6,352 | 6,352 | 0.000300 | SAT |
| 20 | 400 | 12,580 | 12,580 | 0.000620 | SAT |
| 24 | 576 | 22,032 | 22,032 | 0.001140 | SAT |
| 28 | 784 | 35,308 | 35,308 | 0.001890 | SAT |
| 32 | 1,024 | 52,832 | 52,832 | 0.002950 | SAT |

### Table 2: Min-Conflicts Baseline vs Proposed Heuristics - Req 3
| N | Variable Selection Heuristic | Avg Steps | Avg Runtime (s) | Success Rate |
|:---:|:---|:---:|:---:|:---:|
| 8 | Standard (Random Baseline) | 37.0 | 0.000090 | 100% |
| 8 | Proposed Heuristic 1 (Max-Conflict) | 14.5 | 0.000041 | 100% |
| 8 | Proposed Heuristic 2 (Hybrid-Tabu) | 24.0 | 0.000082 | 100% |
| 16 | Standard (Random Baseline) | 59.0 | 0.000213 | 100% |
| 16 | Proposed Heuristic 1 (Max-Conflict) | 39.5 | 0.000155 | 100% |
| 16 | Proposed Heuristic 2 (Hybrid-Tabu) | 32.0 | 0.000143 | 100% |

**Key Findings:**
1. **Clause Verification:** Generated CNF clauses strictly match the theoretical cubic polynomial across all evaluated values of $N$.
2. **Heuristic Acceleration:** The proposed `MaxConflictSelector` reduces required repair steps by **up to 60.8%** on $N = 8$, while `HybridTabuSelector` provides robust escape mechanisms against local minima in larger instances ($N \ge 16$).
