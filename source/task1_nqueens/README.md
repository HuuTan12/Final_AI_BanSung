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
├── core/
│   ├── problem.py           # NQueensProblem: board management, solution checking, DIMACS mapping
│   └── constraints.py       # ConstraintGenerator: generates CNF clauses (ALO, AMO), theoretical formula
├── solvers/
│   ├── base_solver.py       # BaseSolver (abstract interface) and SolverResult dataclass
│   ├── sat_solver.py        # Glucose3SATSolver: integrates Glucose3 from PySAT
│   ├── heuristics.py        # VariableSelector: RandomSelector, MaxConflictSelector, HybridTabuSelector
│   └── min_conflicts.py     # MinConflictsSolver: optimized local search with O(1) frequency tables
├── experiments/
│   └── benchmark.py         # BenchmarkRunner: automated benchmarking, plotting, and markdown tables
├── nqueens.ipynb            # Jupyter Notebook with all outputs fully preserved
└── README.md                # Documentation and running guide
```

---

## 3. How to Run

### A. Run Jupyter Notebook
Open `nqueens.ipynb` in VS Code or Jupyter Notebook:
```bash
jupyter notebook nqueens.ipynb
```
All cells have been pre-executed with outputs preserved as required by submission guidelines.

### B. Run Benchmark Script from Terminal
From the `source/` directory:
```bash
python -m task1_nqueens.experiments.benchmark
```
This script will:
1. Benchmark Glucose3 across $N \ge 4$.
2. Run comparative trials between Standard Min-Conflicts and Proposed Heuristics.
3. Automatically generate the comparison plot `benchmark_task1.png`.
4. Output Markdown summary tables.

---

## 4. Summary of Experimental Results

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