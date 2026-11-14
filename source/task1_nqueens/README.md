# Task 1: Local Search & Propositional Logic (N-Queens Problem)

Course: **Introduction to Artificial Intelligence (503043)**  
Faculty of Information Technology, Ton Duc Thang University (TDTU).

---

## 1. Objectives & Grading Breakdown (3.0 Points)

1. **Requirement 1 (1.0 pt): Propositional Logic Formulation & Constraint Discovery**
   - Boolean proposition variables $X_{r, c} \in \{True, False\}$ for each square $(r, c)$ where $0 \le r, c < N$.
   - DIMACS standard variable mapping: $\text{var\_id}(r, c) = r \cdot N + c + 1 \in [1, N^2]$.
   - Constraint groups: Row (ALO + AMO), Column (ALO + AMO), Main Diagonals (AMO), Anti Diagonals (AMO).
   - Theoretical CNF clause counting formula:
     $$\text{Total Clauses} = 2N + N^2(N - 1) + \frac{N(N - 1)(2N - 1)}{3}$$

2. **Requirement 2 (1.0 pt): Solving with Glucose3 SAT Solver (PySAT) for $N \ge 4$**
   - Implements solver using `Glucose3` from `python-sat` (`pysat`).
   - Runs benchmarks with increasing values of $N \ge 4$ ($N = 4, 8, 12, 16, 20, 24, 28, 32$).
   - Reports total number of CNF clauses and solver execution time.

3. **Requirement 3 (1.0 pt): Min-Conflicts Local Search & Proposed Heuristics**
   - Standard Min-Conflicts implementation from **Lecture 08 - Slide 30** (random variable selection).
   - **Proposed Heuristic 1:** `MaxConflictSelector`, inspired by the Degree Heuristic (**Lecture 08 - Slide 26**), prioritizing the queen with the highest conflicts.
   - **Proposed Heuristic 2:** `HybridTabuSelector`, combining Random Walk (**Lecture 09 - Slide 48**) and Tabu Search (**Lecture 08 - Slide 31**) to overcome local plateaux.
   - Comparative evaluation comparing steps, runtime, and convergence.

---

## 2. Directory Structure & OOP Architecture

```text
source/task1_nqueens/
|---- core/
|   |---- problem.py           # NQueensProblem: board management, solution checking, DIMACS mapping
|   ---- constraints.py       # ConstraintGenerator: generates CNF clauses (ALO, AMO), theoretical formula
|---- solvers/
|   |---- base_solver.py       # BaseSolver (abstract interface) and SolverResult dataclass
|   |---- sat_solver.py        # Glucose3SATSolver: integrates Glucose3 from PySAT
|   |---- heuristics.py        # VariableSelector: RandomSelector, MaxConflictSelector, HybridTabuSelector
|   |---- min_conflicts.py     # MinConflictsSolver: optimized local search with O(1) frequency tables
|   |---- step_min_conflicts.py# StepMinConflictsGenerator: step-by-step animation generator
|   ---- backtracking_solver.py # BacktrackingSolver: step-by-step DFS, all-solutions counting (OEIS A000170)
|---- ui/
|   |---- pygame_nqueens.py    # High-Fidelity Interactive Chessboard GUI with live telemetry and laser beams
|   ---- notebook_visualizer.py # Matplotlib chessboard and solution gallery for Jupyter Notebooks
|---- experiments/
|   ---- benchmark.py         # BenchmarkRunner: automated benchmarking, plotting, and markdown tables
|---- main.py                  # CLI & GUI entry point
|---- nqueens.ipynb            # Jupyter Notebook with all outputs fully preserved
---- README.md                # Documentation and running guide
```

---

## 3. High-Fidelity Interactive GUI & Visualizer (UI/UX)

The project includes an interactive graphical interface (`pygame_nqueens.py`) designed with a modern **Dark Tactical Cyber** aesthetic:

### A. Key Visual & Interactive Features
1. **Interactive Chessboard Rendering:**
   - Supports dynamic board sizes $N \in [4, 16]$ with crisp scalable vector royal crowns (Q).
   - Alternating cream/slate tiles, coordinate axes ($A..H, 1..8$ or $0..N-1$).
   - **Glowing Red Laser Beams:** Highlights attacking pairs of queens in real time with laser effect.
   - **Candidate Row Overlays:** During search, shows conflict numbers on each row of the selected column and safe green squares.

2. **Step-by-step Queen Placement & Solvers:**
   - **Backtracking Search:** Watches the AI place queens column by column, tests safe squares, flashes red on conflicts, and visually backtracks (lifts queen) on dead ends.
   - **Min-Conflicts Local Search:** Visualizes variable selection (via Random, Max-Conflict, or Hybrid-Tabu), row conflict evaluations, moves, and random restarts on plateaux.
   - **Glucose3 PySAT Solver:** Visualizes satisfying model decoding and step-placement.
   - **All Solutions Browser:** Instantly navigates through all valid solutions (e.g., 92 solutions for $N=8$, 2 for $N=4$, 10 for $N=5$, 4 for $N=6$, 40 for $N=7$, 352 for $N=9$).
   - **Interactive Manual Sandbox:** Click any square to place, move, or remove queens by hand, with live conflict count and attack lines!

3. **Telemetry & Live Metrics Panel:**
   - **Cases Tested (Explored Assignments):** Real-time dynamic counter of candidate positions tested.
   - **Solutions Found:** Dynamic solution count with reference total (e.g., `92/92`).
   - **Current Conflicts:** Counts attacking pairs ($0$ = Solved!).
   - **Search Steps & Backtrack / Restart Counters.**
   - **Propositional Logic CNF Model:** Number of variables ($N^2$), ALO/AMO clauses, theoretical formula match check ($2N + N^2(N-1) + \frac{N(N-1)(2N-1)}{3}$).
   - **Execution Latency (in ms).**

### B. Controls & Keyboard Shortcuts
| Control | Shortcut | Description |
|:---|:---:|:---|
| **Play / Pause** | `SPACE` | Automatically advance / pause step-by-step queen placement animation |
| **Step Forward (+1)** | `RIGHT` / `S` | Execute exactly one forward search step |
| **Step Backward (-1)** | `LEFT` / `A` | Rewind one step back in history (Step History Undo) |
| **Reset** | `R` | Reset chessboard and re-initialize active solver |
| **Speed Multiplier** | `1` .. `5` | 1x, 2x, 5x, 10x, or  Max (Instant) |
| **Change Algorithm** | Click `<` / `>` or `TAB` / `M` | Cycle through available algorithms (DFS, SAT, Min-Conflicts, Browser, Manual) |
| **Select Board Size N** | Click `[-]` / `[+]` | Change chessboard dimension $N = 4, 6, 8, 10, 12, 16$ |
| **Browse Solutions** | Click `LEFT / RIGHT` | Cycle through distinct valid solution configurations |
| **Manual Placement** | Left Click | Click any square to place, move, or remove a queen |

---

## 4. How to Run

### A. Run Interactive Pygame GUI
From the project root:
```bash
python source/task1_nqueens/main.py
```
Or with custom arguments:
```bash
# Run 8x8 chessboard with Backtracking algorithm
python source/task1_nqueens/main.py --n 8 --algo BACKTRACKING --speed 5

# Run Min-Conflicts with proposed Max-Conflict heuristic
python source/task1_nqueens/main.py --n 8 --algo MIN_CONFLICTS_MAX --speed 2

# Browse all 92 solutions for N=8
python source/task1_nqueens/main.py --n 8 --algo BROWSER
```

### B. Run Headless CLI Demo (No Display Required)
```bash
python source/task1_nqueens/main.py --cli --n 8
```

### C. Run Jupyter Notebook
Open `nqueens.ipynb` in VS Code or Jupyter Notebook:
```bash
jupyter notebook source/task1_nqueens/nqueens.ipynb
```

### D. Run Benchmark Experiments from Terminal
```bash
python -m task1_nqueens.experiments.benchmark
```

---

## 5. Summary of Experimental Results

### A. Glucose3 SAT Solver Performance (Req 2)
| N | Variables ($N^2$) | Generated Clauses | Theoretical Clauses | Avg Runtime (s) | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 4 | 16 | 84 | 84 | 0.000033 | SAT |
| 8 | 64 | 744 | 744 | 0.000190 | SAT |
| 12 | 144 | 2620 | 2620 | 0.000494 | SAT |
| 16 | 256 | 6352 | 6352 | 0.002631 | SAT |
| 20 | 400 | 12580 | 12580 | 0.003148 | SAT |
| 32 | 1024 | 52832 | 52832 | 0.015200 | SAT |

### B. Min-Conflicts Benchmark Comparison (Req 3)
* The proposed heuristics (`MaxConflictSelector` and `HybridTabuSelector`) achieve **35% - 70% reduction in search steps** compared to the baseline random selection from Lecture 08, scaling effectively up to $N = 64$ and $N = 100$.
* Plots are saved at `benchmark_task1.png`.
