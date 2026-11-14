"""
pygame_nqueens.py - High-Fidelity Interactive Chessboard GUI for N-Queens
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Provides an esports-grade, responsive Pygame GUI for the N-Queens problem:
    1. Real-time animated placement of queens step-by-step:
       - Backtracking search (DFS with candidate testing, conflict flashes, and backtracking).
       - Min-Conflicts local search (variable selection, conflict row evaluation, moves, restarts).
       - Glucose3 PySAT solver (CNF model decoding and step-placement).
    2. Comprehensive Telemetry Panel:
       - Total Cases Tested (Explored game states / assignments)
       - Solutions Found (e.g. 92/92 for N=8)
       - Active Conflicts (Attacking queen pairs count)
       - Search Steps & Backtrack / Random Restart counters
       - Propositional Logic CNF Model statistics (ALO + AMO formulas per Req 1)
       - Runtime Latency (ms)
    3. Interactive Controls:
       - Play / Pause (SPACE)
       - Step Forward +1 (Right Arrow / S)
       - Step Backward -1 (Left Arrow / A) with complete undo history stack
       - Reset (R)
       - Speed Presets: 1x, 2x, 5x, 10x, Instant (Keys 1..5)
    4. Advanced Features:
       - Authentic high-resolution PNG piece assets and chessboard textures
       - Solution Browser: Navigate all valid solutions with < Prev / Next >
       - Glowing laser attack beams with impact spark flares connecting conflicting queens
       - Interactive Sandbox Mode: Click any square on the board to place/remove queens manually
       - Dynamic chessboard dimension scaling (N = 4, 5, 6, 7, 8, 9, 10, 12, 16)
"""

import os
import sys
import math
import time
from typing import List, Tuple, Optional, Dict, Any

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Ensure source directory is in sys.path
_file_dir = os.path.dirname(os.path.abspath(__file__))
_source_dir = os.path.abspath(os.path.join(_file_dir, "..", ".."))
if _source_dir not in sys.path:
    sys.path.insert(0, _source_dir)
_task1_dir = os.path.abspath(os.path.join(_file_dir, ".."))
if _task1_dir not in sys.path:
    sys.path.insert(0, _task1_dir)

try:
    from task1_nqueens.core.problem import NQueensProblem
    from task1_nqueens.core.constraints import ConstraintGenerator
    from task1_nqueens.solvers.backtracking_solver import BacktrackingSolver, KNOWN_SOLUTIONS_COUNT
    from task1_nqueens.solvers.step_min_conflicts import StepMinConflictsGenerator
    from task1_nqueens.solvers.sat_solver import Glucose3SATSolver
    from task1_nqueens.solvers.heuristics import MaxConflictSelector, HybridTabuSelector, RandomSelector
except ImportError:
    from core.problem import NQueensProblem
    from core.constraints import ConstraintGenerator
    from solvers.backtracking_solver import BacktrackingSolver, KNOWN_SOLUTIONS_COUNT
    from solvers.step_min_conflicts import StepMinConflictsGenerator
    from solvers.sat_solver import Glucose3SATSolver
    from solvers.heuristics import MaxConflictSelector, HybridTabuSelector, RandomSelector


class NQueensGUI:
    """
    High-Fidelity Graphical User Interface for N-Queens.
    Supports authentic asset rendering, animated step-by-step search, and real-time telemetry.
    """

    def __init__(self, n: int = 8, width: int = 1280, height: int = 820):
        self.n = max(4, min(16, n))
        self.width = width
        self.height = height
        self.sidebar_width = 460

        # Board rendering geometry
        self.board_margin = 35
        self.board_rect = pygame.Rect(0, 0, 1, 1)  # recalculated on layout
        self.cell_size = 60

        # State tracking
        self.board: List[int] = [-1] * self.n  # board[col] = row (-1 means empty)
        self.algorithm_mode = "BACKTRACKING"   # "BACKTRACKING", "MIN_CONFLICTS_MAX", "MIN_CONFLICTS_TABU", "MIN_CONFLICTS_RANDOM", "SAT", "BROWSER", "MANUAL"
        self.is_playing = False
        self.speed_multiplier = 2              # 1x, 2x, 5x, 10x, 50x (Instant)
        self.anim_tick = 0
        self.last_step_time = 0.0

        # Step generators and history stack
        self.step_generator = None
        self.step_history: List[Dict[str, Any]] = []
        self.history_index: int = -1

        # Real-time Metrics & Telemetry
        self.cases_explored = 0
        self.solutions_found = 0
        self.backtracks_count = 0
        self.steps_count = 0
        self.restarts_count = 0
        self.current_conflicts = 0
        self.execution_time_ms = 0.0
        self.start_perf_time = 0.0
        self.status_message = "Ready. Click PLAY or STEP +1 to start visual execution."

        # Candidate overlay
        self.candidate_col: int = -1
        self.candidate_row: int = -1
        self.candidate_type: str = ""          # "SAFE", "CONFLICT", "BACKTRACK", "EVAL_ROWS"
        self.candidate_conflicts: List[Tuple[int, int]] = []
        self.row_conflicts_eval: List[int] = []
        self.active_conflicts: List[Tuple[int, int]] = []
        self.hovered_cell: Optional[Tuple[int, int]] = None
        self.search_finished: bool = False

        # All-solutions browser state
        self.cached_all_solutions: List[List[int]] = []
        self.current_solution_idx: int = 0
        self.browser_generator = None

        # CNF Propositional Logic stats cache
        self.cnf_stats: Dict[str, Any] = {}
        self._update_cnf_stats()

        # UI Color Theme - Modern Cyberpunk / Tactical Dark Command Center
        self.COLOR_BG = (14, 18, 26)
        self.COLOR_SIDEBAR_BG = (20, 26, 38)
        self.COLOR_CARD_BG = (26, 34, 48)
        self.COLOR_CARD_BORDER = (42, 54, 76)
        self.COLOR_CARD_HEADER = (32, 42, 60)

        # Chessboard Colors (Fallbacks if assets are unavailable)
        self.COLOR_TILE_LIGHT = (236, 240, 246)
        self.COLOR_TILE_DARK = (78, 102, 134)
        self.COLOR_TILE_BORDER = (32, 42, 58)
        self.COLOR_COORD_TEXT = (120, 140, 168)

        # Queen and Highlight Colors
        self.COLOR_QUEEN_GOLD = (250, 195, 30)
        self.COLOR_QUEEN_SHADOW = (180, 130, 10)
        self.COLOR_QUEEN_CONFLICT = (235, 65, 65)
        self.COLOR_QUEEN_CYAN = (46, 204, 250)
        self.COLOR_QUEEN_GREEN = (46, 213, 115)

        self.COLOR_LASER_BEAM = (245, 60, 60)
        self.COLOR_SUCCESS_GREEN = (46, 204, 113)
        self.COLOR_AMBER_ALERT = (241, 196, 15)
        self.COLOR_TEXT = (240, 244, 252)
        self.COLOR_TEXT_DIM = (140, 154, 175)
        self.COLOR_TEXT_MUTED = (90, 102, 122)

        # Interactive UI Buttons registry
        self.buttons: List[Dict[str, Any]] = []

        # Pygame handles and assets
        self.screen = None
        self.clock = None
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.raw_assets: Dict[str, pygame.Surface] = {}
        self.scaled_assets: Dict[str, pygame.Surface] = {}
        self.assets_loaded = False

    def _update_cnf_stats(self) -> None:
        """Calculates theoretical CNF clause statistics for the current N."""
        problem = NQueensProblem(self.n)
        generator = ConstraintGenerator(problem)
        self.cnf_stats = generator.get_clause_statistics()
        self.cnf_stats["theoretical_total"] = generator.get_theoretical_clause_count()

    def _load_assets(self) -> None:
        """Loads graphical PNG assets from assets directory."""
        assets_dir = os.path.join(_task1_dir, "assets")
        asset_files = {
            "queen_gold": "queen_gold.png",
            "queen_conflict": "queen_conflict.png",
            "queen_safe": "queen_safe.png",
            "queen_candidate": "queen_candidate.png",
            "crown_emblem": "crown_emblem.png",
            "tile_light": "tile_light.png",
            "tile_dark": "tile_dark.png",
            "spark_flare": "spark_flare.png",
        }

        self.raw_assets.clear()
        for key, fname in asset_files.items():
            fpath = os.path.join(assets_dir, fname)
            if os.path.isfile(fpath):
                try:
                    surf = pygame.image.load(fpath).convert_alpha()
                    self.raw_assets[key] = surf
                except Exception as e:
                    print(f"[NQueensGUI] Warning: Failed to load asset '{fname}': {e}")

        self.assets_loaded = len(self.raw_assets) > 0
        if self.assets_loaded:
            self._rescale_assets()

    def _rescale_assets(self) -> None:
        """Caches scaled versions of the assets matching the current cell size."""
        if not self.assets_loaded:
            return

        cs = max(16, self.cell_size)
        piece_size = max(14, int(cs * 0.85))

        # Scale queen pieces
        for q_key in ("queen_gold", "queen_conflict", "queen_safe", "queen_candidate"):
            if q_key in self.raw_assets:
                self.scaled_assets[q_key] = pygame.transform.smoothscale(
                    self.raw_assets[q_key], (piece_size, piece_size)
                )

        # Scale board tiles
        for t_key in ("tile_light", "tile_dark"):
            if t_key in self.raw_assets:
                self.scaled_assets[t_key] = pygame.transform.smoothscale(
                    self.raw_assets[t_key], (cs, cs)
                )

        # Scale spark flare
        if "spark_flare" in self.raw_assets:
            flare_size = max(12, int(cs * 0.4))
            self.scaled_assets["spark_flare"] = pygame.transform.smoothscale(
                self.raw_assets["spark_flare"], (flare_size, flare_size)
            )

        # Header crown emblem
        if "crown_emblem" in self.raw_assets:
            self.scaled_assets["crown_emblem"] = pygame.transform.smoothscale(
                self.raw_assets["crown_emblem"], (36, 36)
            )

    def init_display(self) -> bool:
        """Initializes Pygame display, cross-platform fonts, assets, and UI buttons."""
        if not PYGAME_AVAILABLE:
            print("[NQueensGUI] Notice: Pygame is not installed. Run 'pip install pygame' to use GUI.")
            return False

        try:
            pygame.init()
            pygame.font.init()

            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            pygame.display.set_caption(f"N-Queens AI Tactical Visualizer (N={self.n}) - Propositional Logic & Local Search")
            self.clock = pygame.time.Clock()

            # Cross-platform fonts with fallback chains
            self.fonts["title"] = pygame.font.SysFont("Segoe UI,Trebuchet MS,Helvetica,Arial", 18, bold=True)
            self.fonts["header"] = pygame.font.SysFont("Segoe UI,Trebuchet MS,Helvetica,Arial", 13, bold=True)
            self.fonts["body_bold"] = pygame.font.SysFont("Segoe UI,Helvetica,Arial", 11, bold=True)
            self.fonts["body"] = pygame.font.SysFont("Segoe UI,Helvetica,Arial", 11)
            self.fonts["small"] = pygame.font.SysFont("Segoe UI,Helvetica,Arial", 10)
            self.fonts["badge"] = pygame.font.SysFont("Consolas,Courier New,Arial", 11, bold=True)
            self.fonts["mono_val"] = pygame.font.SysFont("Consolas,Courier New,Arial", 13, bold=True)
            self.fonts["coords"] = pygame.font.SysFont("Consolas,Courier New,Arial", 11, bold=True)
            self.fonts["large_stat"] = pygame.font.SysFont("Consolas,Courier New,Arial", 20, bold=True)

            self._load_assets()
            self._update_layout()
            self._init_buttons()
            self._init_solver()
            return True
        except Exception as e:
            print(f"[NQueensGUI] Display initialization error: {e}")
            return False

    def _update_layout(self) -> None:
        """Recalculates board sizing and cell positions to keep board crisp and centered."""
        w, h = self.screen.get_size()
        self.width = w
        self.height = h

        board_area_w = w - self.sidebar_width
        board_area_h = h - 28
        max_board_dim = min(board_area_w - 2 * self.board_margin, board_area_h - 2 * self.board_margin)
        max_board_dim = max(240, max_board_dim)

        self.cell_size = max_board_dim // self.n
        actual_board_px = self.cell_size * self.n

        offset_x = self.board_margin + (board_area_w - 2 * self.board_margin - actual_board_px) // 2
        offset_y = self.board_margin + (board_area_h - 2 * self.board_margin - actual_board_px) // 2

        self.board_rect = pygame.Rect(offset_x, offset_y, actual_board_px, actual_board_px)
        self._rescale_assets()

    def _init_buttons(self) -> None:
        """Builds all clickable controls in the right sidebar."""
        self.buttons.clear()
        sb_x = self.width - self.sidebar_width + 16
        sb_w = self.sidebar_width - 32

        # 1. Playback Deck (Row 1)
        btn_y = 66
        gap = 5
        play_w = 84
        other_w = (sb_w - play_w - 4 * gap) // 4
        reset_w = sb_w - play_w - 3 * other_w - 4 * gap
        play_lbl = "PAUSE" if self.is_playing else "PLAY"
        self.buttons.append({"id": "btn_play", "label": play_lbl, "rect": pygame.Rect(sb_x, btn_y, play_w, 32), "category": "control"})
        self.buttons.append({"id": "btn_step_back", "label": "< STEP", "rect": pygame.Rect(sb_x + play_w + gap, btn_y, other_w, 32), "category": "control"})
        self.buttons.append({"id": "btn_step_fwd", "label": "STEP >", "rect": pygame.Rect(sb_x + play_w + gap + (other_w + gap), btn_y, other_w, 32), "category": "control"})
        self.buttons.append({"id": "btn_solve", "label": "SOLVE >>", "rect": pygame.Rect(sb_x + play_w + gap + 2 * (other_w + gap), btn_y, other_w, 32), "category": "control"})
        self.buttons.append({"id": "btn_reset", "label": "RESET", "rect": pygame.Rect(sb_x + play_w + gap + 3 * (other_w + gap), btn_y, reset_w, 32), "category": "control"})

        # 2. Speed Controls (Row 2)
        btn_y += 38
        speeds = [("1x", 1), ("2x", 2), ("5x", 5), ("10x", 10), ("MAX", 50)]
        sp_w = (sb_w - (len(speeds) - 1) * 6) // len(speeds)
        for i, (label, val) in enumerate(speeds):
            self.buttons.append({
                "id": f"speed_{val}",
                "label": label,
                "rect": pygame.Rect(sb_x + i * (sp_w + 6), btn_y, sp_w, 26),
                "val": val,
                "category": "speed"
            })

        # 3. Board Size N Selector (Row 3)
        btn_y += 32
        n_sizes = [4, 6, 8, 10, 12, 16]
        n_w = (sb_w - 56 - (len(n_sizes) - 1) * 4) // len(n_sizes)
        self.buttons.append({"id": "n_dec", "label": "-", "rect": pygame.Rect(sb_x, btn_y, 24, 26), "category": "n_change"})
        for i, val in enumerate(n_sizes):
            self.buttons.append({
                "id": f"n_{val}",
                "label": f"N={val}",
                "rect": pygame.Rect(sb_x + 28 + i * (n_w + 4), btn_y, n_w, 26),
                "n_val": val,
                "category": "n_select"
            })
        self.buttons.append({"id": "n_inc", "label": "+", "rect": pygame.Rect(sb_x + sb_w - 24, btn_y, 24, 26), "category": "n_change"})

        # 4. Algorithm Selector (Clean 2-Column Grid)
        btn_y = 190
        algos = [
            ("BACKTRACKING", "Backtracking (DFS)"),
            ("SAT", "PySAT Glucose3 (CNF)"),
            ("MIN_CONFLICTS_MAX", "Min-Conflicts (Max)"),
            ("MIN_CONFLICTS_TABU", "Min-Conflicts (Tabu)"),
            ("MIN_CONFLICTS_RANDOM", "Min-Conflicts (Random)"),
            ("MANUAL", "Manual Sandbox"),
        ]
        half_w = (sb_w - 8) // 2
        algo_btn_h = 28
        for idx, (algo_id, label) in enumerate(algos):
            r_idx = idx // 2
            c_idx = idx % 2
            bx = sb_x + c_idx * (half_w + 8)
            by = btn_y + r_idx * (algo_btn_h + 6)
            self.buttons.append({
                "id": f"algo_{algo_id}",
                "label": label,
                "rect": pygame.Rect(bx, by, half_w, algo_btn_h),
                "algo": algo_id,
                "category": "algo"
            })

        # 5. All-Solutions Browser Row
        browser_y = btn_y + 3 * (algo_btn_h + 6)
        self.buttons.append({
            "id": "algo_BROWSER",
            "label": "Solutions Browser",
            "rect": pygame.Rect(sb_x, browser_y, half_w, algo_btn_h),
            "algo": "BROWSER",
            "category": "algo"
        })
        nav_w = (half_w - 6) // 2
        self.buttons.append({"id": "btn_sol_prev", "label": "< PREV", "rect": pygame.Rect(sb_x + half_w + 8, browser_y, nav_w, algo_btn_h), "category": "browser_nav"})
        self.buttons.append({"id": "btn_sol_next", "label": "NEXT >", "rect": pygame.Rect(sb_x + half_w + 8 + nav_w + 6, browser_y, nav_w, algo_btn_h), "category": "browser_nav"})

    def _is_board_complete_and_valid(self) -> bool:
        """Returns True iff all N columns have a queen placed and zero attacking pairs exist."""
        return len(self.board) == self.n and all(r != -1 for r in self.board) and self.current_conflicts == 0

    def _init_solver(self) -> None:
        """Initializes or resets the active solver generator and state."""
        self.board = [-1] * self.n
        self.step_history.clear()
        self.history_index = -1
        self.cases_explored = 0
        self.solutions_found = 0
        self.backtracks_count = 0
        self.steps_count = 0
        self.restarts_count = 0
        self.current_conflicts = 0
        self.candidate_col = -1
        self.candidate_row = -1
        self.candidate_type = ""
        self.candidate_conflicts.clear()
        self.row_conflicts_eval.clear()
        self.active_conflicts.clear()
        self.browser_generator = None
        self.search_finished = False
        self.start_perf_time = time.perf_counter()
        self.execution_time_ms = 0.0

        self._update_cnf_stats()
        if PYGAME_AVAILABLE and pygame.display.get_init():
            pygame.display.set_caption(f"N-Queens AI Tactical Visualizer (N={self.n}) - Propositional Logic & Local Search")

        if self.algorithm_mode == "BACKTRACKING":
            solver = BacktrackingSolver(find_all=True)
            self.step_generator = solver.solve_step_generator(self.n, find_all=True)
            self.status_message = f"Initialized Backtracking for N={self.n}. Press PLAY [SPACE] or SOLVE [F]."

        elif self.algorithm_mode == "MIN_CONFLICTS_MAX":
            gen = StepMinConflictsGenerator(heuristic=MaxConflictSelector(), max_steps=1500)
            self.step_generator = gen.run(self.n)
            self.status_message = f"Min-Conflicts (Max-Conflict). Initialized permutation board, O(1) conflict delta."

        elif self.algorithm_mode == "MIN_CONFLICTS_TABU":
            gen = StepMinConflictsGenerator(heuristic=HybridTabuSelector(), max_steps=1500)
            self.step_generator = gen.run(self.n)
            self.status_message = f"Min-Conflicts (Hybrid-Tabu). Combining Random Walk & Tabu tenure to prevent cycling."

        elif self.algorithm_mode == "MIN_CONFLICTS_RANDOM":
            gen = StepMinConflictsGenerator(heuristic=RandomSelector(), max_steps=1500)
            self.step_generator = gen.run(self.n)
            self.status_message = f"Standard Min-Conflicts (Russell & Norvig). Selecting random conflicted queen."

        elif self.algorithm_mode == "SAT":
            self._run_sat_solver()

        elif self.algorithm_mode == "BROWSER":
            self._load_all_solutions_for_browser()

        elif self.algorithm_mode == "MANUAL":
            self.board = [-1] * self.n
            self.step_generator = None
            self.status_message = "Manual Sandbox: L-Click place/move, R-Click remove, [F] Quick Solve!"

        # Save initial state in history
        self._record_history()

    def _run_sat_solver(self) -> None:
        """Solves N-Queens with Glucose3 and prepares animated step-in of queens."""
        sat_solver = Glucose3SATSolver()
        res = sat_solver.solve(self.n)
        if res.is_solved and res.solution is not None:
            final_sol = res.solution
            self.execution_time_ms = res.execution_time * 1000.0
            self.solutions_found = 0
            self.cases_explored = res.num_clauses if getattr(res, "num_clauses", 0) else self.cnf_stats["theoretical_total"]

            # Create generator to place queens one by one
            def sat_gen():
                current_board = [-1] * self.n
                for c in range(self.n):
                    current_board[c] = final_sol[c]
                    yield {
                        "event": "PLACE_SAT",
                        "board": list(current_board),
                        "col": c,
                        "row": final_sol[c],
                        "msg": f"Glucose3 Model: Boolean variable X_{final_sol[c]},{c} = TRUE (Col {c})."
                    }
                yield {
                    "event": "SOLVED",
                    "board": list(final_sol),
                    "col": -1,
                    "row": -1,
                    "msg": f"PySAT Glucose3 solved successfully in {self.execution_time_ms:.3f} ms!"
                }

            self.step_generator = sat_gen()
            self.status_message = f"Glucose3 PySAT solved in {self.execution_time_ms:.3f} ms. Click PLAY or SOLVE to place queens."
        else:
            self.step_generator = None
            self.search_finished = True
            self.status_message = f"Glucose3 SAT could not find a valid solution for N={self.n}."

    def _fetch_more_browser_solutions(self, limit: int = 100) -> int:
        """Lazily pulls up to `limit` additional solutions from the browser generator."""
        if self.browser_generator is None:
            return 0
        added = 0
        while added < limit:
            try:
                step = next(self.browser_generator)
                if step.event_type == "SOLUTION":
                    self.cached_all_solutions.append(list(step.board))
                    added += 1
            except StopIteration:
                self.browser_generator = None
                break
        return added

    def _load_all_solutions_for_browser(self) -> None:
        """Computes or lazily caches valid solutions without freezing the UI on large N."""
        t0 = time.perf_counter()
        bt = BacktrackingSolver(find_all=True)
        self.cached_all_solutions = []
        self.browser_generator = None
        self.current_solution_idx = 0

        if self.n <= 10:
            self.cached_all_solutions = bt.find_all_solutions(self.n)
        else:
            self.browser_generator = bt.solve_step_generator(self.n, find_all=True, yield_conflicts=False)
            self._fetch_more_browser_solutions(limit=25)

        t_elapsed = (time.perf_counter() - t0) * 1000.0
        self.execution_time_ms = t_elapsed
        self.solutions_found = len(self.cached_all_solutions)

        if self.cached_all_solutions:
            self.board = list(self.cached_all_solutions[0])
            known_total = KNOWN_SOLUTIONS_COUNT.get(self.n, len(self.cached_all_solutions))
            more_hint = " (lazy streaming)" if self.browser_generator is not None else ""
            self.status_message = (
                f"Loaded {len(self.cached_all_solutions):,} solutions in {t_elapsed:.1f} ms{more_hint}. "
                f"Viewing 1 / {known_total:,}."
            )
        else:
            self.board = [-1] * self.n
            self.status_message = "No valid solutions exist for this configuration."

    def _browser_next_solution(self) -> bool:
        """Advances to the next cached/streamed solution in Browser mode."""
        if not self.cached_all_solutions:
            return False
        if self.current_solution_idx + 1 >= len(self.cached_all_solutions) and self.browser_generator is not None:
            self._fetch_more_browser_solutions(limit=25)
            self.solutions_found = len(self.cached_all_solutions)

        self.current_solution_idx = (self.current_solution_idx + 1) % len(self.cached_all_solutions)
        self.board = list(self.cached_all_solutions[self.current_solution_idx])
        known_total = KNOWN_SOLUTIONS_COUNT.get(self.n, len(self.cached_all_solutions))
        total_str = f"{known_total:,}" if isinstance(known_total, int) else str(known_total)
        self.status_message = (
            f"Viewing solution {self.current_solution_idx + 1:,} / {total_str} "
            f"(Use Left/Right or Mouse Wheel)."
        )
        self._update_conflicts()
        self._record_history()
        return True

    def _browser_prev_solution(self) -> bool:
        """Navigates to the previous solution in Browser mode, wrapping cleanly."""
        if not self.cached_all_solutions:
            return False
        self.current_solution_idx = (self.current_solution_idx - 1) % len(self.cached_all_solutions)
        self.board = list(self.cached_all_solutions[self.current_solution_idx])
        known_total = KNOWN_SOLUTIONS_COUNT.get(self.n, len(self.cached_all_solutions))
        total_str = f"{known_total:,}" if isinstance(known_total, int) else str(known_total)
        self.status_message = (
            f"Viewing solution {self.current_solution_idx + 1:,} / {total_str} "
            f"(Use Left/Right or Mouse Wheel)."
        )
        self._update_conflicts()
        self._record_history()
        return True

    def _toggle_play(self) -> None:
        """Toggles playback; restarts automatically if current search already finished."""
        if self.algorithm_mode == "MANUAL":
            self.is_playing = False
            self.status_message = "Manual Sandbox: Click squares to place queens or press SOLVE [F]."
            return

        if not self.is_playing:
            if self.search_finished and self.history_index >= len(self.step_history) - 1:
                self._init_solver()
            self.is_playing = True
        else:
            self.is_playing = False

    def solve_instant(self) -> bool:
        """Fast-forwards current mode to the next solution or solves Manual board via SAT."""
        self.is_playing = False

        if self.algorithm_mode == "BROWSER":
            return self._browser_next_solution()

        if self.algorithm_mode == "MANUAL":
            sat_solver = Glucose3SATSolver()
            res = sat_solver.solve(self.n)
            if res.is_solved and res.solution is not None:
                self.board = list(res.solution)
                self.execution_time_ms = res.execution_time * 1000.0
                self.cases_explored = res.num_clauses if getattr(res, "num_clauses", 0) else self.cnf_stats["theoretical_total"]
                self.solutions_found = 1
                self.candidate_col = -1
                self.candidate_row = -1
                self.candidate_type = "SOLVED"
                self.candidate_conflicts.clear()
                self.row_conflicts_eval.clear()
                self._update_conflicts()
                self.status_message = f"Solved N={self.n} sandbox board via Glucose3 SAT in {self.execution_time_ms:.3f} ms!"
                self._record_history()
                return True
            self.status_message = f"Could not solve N={self.n} via Glucose3 SAT."
            return False

        if self.search_finished and self.history_index >= len(self.step_history) - 1:
            self._init_solver()

        if self.step_generator is None:
            return False

        t_start = time.perf_counter()
        max_iters = 50000 if self.algorithm_mode == "BACKTRACKING" else 5000
        for _ in range(max_iters):
            adv = self.step_forward()
            if not adv:
                return False
            if self.algorithm_mode == "BACKTRACKING" and self.candidate_type in ("SOLUTION", "FINISHED"):
                return True
            if self.algorithm_mode.startswith("MIN_CONFLICTS") and self.candidate_type in ("SOLVED", "TIMEOUT"):
                return True
            if self.algorithm_mode == "SAT" and self.candidate_type == "SOLVED":
                return True
            if (time.perf_counter() - t_start) > 1.2:
                self.status_message = "Fast-forward paused at time budget. Click SOLVE again to continue."
                return True
        return True

    def _record_history(self) -> None:
        """Saves current frame snapshot to enable step-by-step backward undo."""
        snapshot = {
            "board": list(self.board),
            "cases_explored": self.cases_explored,
            "solutions_found": self.solutions_found,
            "backtracks_count": self.backtracks_count,
            "steps_count": self.steps_count,
            "restarts_count": self.restarts_count,
            "current_conflicts": self.current_conflicts,
            "candidate_col": self.candidate_col,
            "candidate_row": self.candidate_row,
            "candidate_type": self.candidate_type,
            "candidate_conflicts": list(self.candidate_conflicts),
            "row_conflicts_eval": list(self.row_conflicts_eval),
            "status_message": self.status_message,
            "search_finished": self.search_finished,
        }
        if self.history_index < len(self.step_history) - 1:
            self.step_history = self.step_history[: self.history_index + 1]
        self.step_history.append(snapshot)
        self.history_index = len(self.step_history) - 1

    def step_forward(self) -> bool:
        """Executes one step from the active generator or advances solution index."""
        if self.history_index < len(self.step_history) - 1:
            self.history_index += 1
            self._restore_history(self.history_index)
            if self.algorithm_mode == "BACKTRACKING" and self.candidate_type in ("SOLUTION", "FINISHED"):
                self.is_playing = False
            elif self.algorithm_mode.startswith("MIN_CONFLICTS") and self.candidate_type in ("SOLVED", "TIMEOUT"):
                self.is_playing = False
            elif self.algorithm_mode == "SAT" and self.candidate_type == "SOLVED":
                self.is_playing = False
            return True

        if self.algorithm_mode == "BROWSER":
            return self._browser_next_solution()

        if self.step_generator is None:
            return False

        try:
            step = next(self.step_generator)
            self.steps_count += 1
            if self.algorithm_mode != "SAT":
                self.execution_time_ms = (time.perf_counter() - self.start_perf_time) * 1000.0

            if self.algorithm_mode == "BACKTRACKING":
                self.board = list(step.board)
                self.cases_explored = step.cases_explored
                self.solutions_found = step.solutions_found
                self.backtracks_count = step.backtracks_count
                self.candidate_col = step.col
                self.candidate_row = step.row
                self.candidate_type = step.event_type
                self.candidate_conflicts = list(getattr(step, "conflicts", []))
                self.status_message = step.message

                if step.event_type == "SOLUTION":
                    self.is_playing = False
                    known_total = KNOWN_SOLUTIONS_COUNT.get(self.n, "?")
                    self.status_message = (
                        f"Solution #{self.solutions_found}/{known_total} found! "
                        f"Press SPACE/PLAY or SOLVE to continue to next solution."
                    )
                elif step.event_type == "FINISHED":
                    self.is_playing = False
                    self.search_finished = True

            elif self.algorithm_mode.startswith("MIN_CONFLICTS"):
                self.board = list(step.board)
                self.candidate_col = step.selected_col
                self.candidate_row = step.chosen_row
                self.candidate_type = step.event_type
                self.candidate_conflicts.clear()
                self.row_conflicts_eval = list(step.row_conflicts)
                self.current_conflicts = step.total_conflicts
                self.restarts_count = step.restarts_count
                self.cases_explored = step.step_num
                self.status_message = step.message

                if step.event_type == "SOLVED":
                    self.solutions_found = 1
                    self.is_playing = False
                    self.search_finished = True
                elif step.event_type == "TIMEOUT":
                    self.is_playing = False
                    self.search_finished = True

            elif self.algorithm_mode == "SAT":
                self.board = list(step["board"])
                self.candidate_col = step["col"]
                self.candidate_row = step["row"]
                self.candidate_type = step["event"]
                self.candidate_conflicts.clear()
                self.status_message = step["msg"]
                if step["event"] == "SOLVED":
                    self.solutions_found = 1
                    self.is_playing = False
                    self.search_finished = True

            self._update_conflicts()
            self._record_history()
            return True
        except StopIteration:
            self.is_playing = False
            self.search_finished = True
            self.status_message = "Search algorithm completed the entire exploration tree."
            return False

    def step_backward(self) -> bool:
        """Rewinds the visualizer one step back in history (or previous solution in Browser mode)."""
        if self.algorithm_mode == "BROWSER" and self.history_index == 0:
            return self._browser_prev_solution()
        if self.history_index > 0:
            self.history_index -= 1
            self._restore_history(self.history_index)
            return True
        return False

    def _restore_history(self, index: int) -> None:
        """Applies a recorded snapshot to current state."""
        if 0 <= index < len(self.step_history):
            snap = self.step_history[index]
            self.board = list(snap["board"])
            self.cases_explored = snap["cases_explored"]
            self.solutions_found = snap["solutions_found"]
            self.backtracks_count = snap["backtracks_count"]
            self.steps_count = snap["steps_count"]
            self.restarts_count = snap["restarts_count"]
            self.current_conflicts = snap["current_conflicts"]
            self.candidate_col = snap["candidate_col"]
            self.candidate_row = snap["candidate_row"]
            self.candidate_type = snap["candidate_type"]
            self.candidate_conflicts = list(snap.get("candidate_conflicts", []))
            self.row_conflicts_eval = list(snap["row_conflicts_eval"])
            self.status_message = snap["status_message"]
            self.search_finished = snap.get("search_finished", False)
            self._update_conflicts()

    def _update_conflicts(self) -> None:
        """Finds all attacking pairs on current board for laser rendering."""
        self.active_conflicts.clear()
        conflicts_count = 0
        for c1 in range(self.n):
            r1 = self.board[c1]
            if r1 == -1:
                continue
            for c2 in range(c1 + 1, self.n):
                r2 = self.board[c2]
                if r2 == -1:
                    continue
                # Check row or diagonal conflict
                if r1 == r2 or abs(r1 - r2) == abs(c1 - c2):
                    self.active_conflicts.append(((r1, c1), (r2, c2)))
                    conflicts_count += 1
        self.current_conflicts = conflicts_count

    def handle_click(self, pos: Tuple[int, int], button: int = 1) -> None:
        """Handles mouse clicks on buttons and chessboard squares."""
        x, y = pos

        # Check UI Buttons (Left-click)
        if button == 1:
            for btn in self.buttons:
                if btn["rect"].collidepoint(x, y):
                    self._on_button_press(btn)
                    return

        # Check Chessboard Square Click (Pause running search or Manual placement / sandbox)
        if self.board_rect.collidepoint(x, y):
            if self.is_playing:
                self.is_playing = False
                self.status_message = "Paused by board click. Click PLAY to resume or click again to edit."
                return

            rel_x = x - self.board_rect.x
            rel_y = y - self.board_rect.y
            col = rel_x // self.cell_size
            row = rel_y // self.cell_size

            if 0 <= col < self.n and 0 <= row < self.n:
                if button == 3:
                    if self.board[col] != -1:
                        self.board[col] = -1
                        col_lbl = chr(ord('A') + col) if self.n <= 26 else str(col)
                        self.status_message = f"Removed Queen from Column {col_lbl}."
                    else:
                        return
                else:
                    if self.board[col] == row:
                        self.board[col] = -1
                        self.status_message = f"Removed Queen from square ({row}, {col})."
                    else:
                        self.board[col] = row
                        self.status_message = f"Placed Queen onto square ({row}, {col})."

                self.algorithm_mode = "MANUAL"
                self.step_generator = None
                self.search_finished = False
                self.candidate_col = -1
                self.candidate_row = -1
                self.candidate_type = ""
                self.candidate_conflicts.clear()
                self.row_conflicts_eval.clear()
                self._update_conflicts()
                if self._is_board_complete_and_valid():
                    self.solutions_found = 1
                    self.status_message = f"Solved! All {self.n} queens placed safely with 0 conflicts!"
                else:
                    self.solutions_found = 0
                self._record_history()

    def _on_button_press(self, btn: Dict[str, Any]) -> None:
        """Action handler for sidebar buttons."""
        bid = btn["id"]

        if bid == "btn_play":
            self._toggle_play()
            btn["label"] = "PAUSE" if self.is_playing else "PLAY"

        elif bid == "btn_step_fwd":
            self.is_playing = False
            self.step_forward()

        elif bid == "btn_step_back":
            self.is_playing = False
            self.step_backward()

        elif bid == "btn_solve":
            self.solve_instant()

        elif bid == "btn_reset":
            self.is_playing = False
            self._init_solver()

        elif btn.get("category") == "speed":
            self.speed_multiplier = btn["val"]

        elif btn.get("category") == "algo":
            self.is_playing = False
            self.algorithm_mode = btn["algo"]
            self._init_solver()

        elif btn.get("category") == "n_select":
            self.is_playing = False
            self.n = btn["n_val"]
            self._update_layout()
            self._init_buttons()
            self._init_solver()

        elif bid == "n_inc":
            if self.n < 16:
                self.is_playing = False
                self.n += 1
                self._update_layout()
                self._init_buttons()
                self._init_solver()

        elif bid == "n_dec":
            if self.n > 4:
                self.is_playing = False
                self.n -= 1
                self._update_layout()
                self._init_buttons()
                self._init_solver()

        elif bid == "btn_sol_prev":
            self.is_playing = False
            if self.algorithm_mode != "BROWSER":
                self.algorithm_mode = "BROWSER"
                self._init_solver()
            else:
                self._browser_prev_solution()

        elif bid == "btn_sol_next":
            self.is_playing = False
            if self.algorithm_mode != "BROWSER":
                self.algorithm_mode = "BROWSER"
                self._init_solver()
            else:
                self._browser_next_solution()

    def run(self) -> None:
        """Main graphical event loop running at 60 FPS."""
        if not self.init_display():
            return

        running = True
        while running:
            cur_time = time.perf_counter()
            step_interval = 0.45 / self.speed_multiplier if self.speed_multiplier < 50 else 0.005

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE:
                    self._update_layout()
                    self._init_buttons()

                elif event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    if self.board_rect.collidepoint(mx, my):
                        c = (mx - self.board_rect.x) // self.cell_size
                        r = (my - self.board_rect.y) // self.cell_size
                        self.hovered_cell = (r, c) if (0 <= r < self.n and 0 <= c < self.n) else None
                    else:
                        self.hovered_cell = None

                elif event.type == pygame.MOUSEWHEEL:
                    if self.algorithm_mode == "BROWSER":
                        self.is_playing = False
                        if event.y < 0:
                            self._browser_next_solution()
                        elif event.y > 0:
                            self._browser_prev_solution()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in (1, 3):
                        self.handle_click(event.pos, button=event.button)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self._toggle_play()
                    elif event.key in (pygame.K_RIGHT, pygame.K_s, pygame.K_d):
                        self.is_playing = False
                        if self.algorithm_mode == "BROWSER":
                            self._browser_next_solution()
                        elif event.key != pygame.K_d:
                            self.step_forward()
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.is_playing = False
                        if self.algorithm_mode == "BROWSER":
                            self._browser_prev_solution()
                        else:
                            self.step_backward()
                    elif event.key in (pygame.K_f, pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.solve_instant()
                    elif event.key == pygame.K_r:
                        self.is_playing = False
                        self._init_solver()
                    elif event.key == pygame.K_1:
                        self.speed_multiplier = 1
                    elif event.key == pygame.K_2:
                        self.speed_multiplier = 2
                    elif event.key == pygame.K_3:
                        self.speed_multiplier = 5
                    elif event.key == pygame.K_4:
                        self.speed_multiplier = 10
                    elif event.key == pygame.K_5:
                        self.speed_multiplier = 50
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            # Auto-advance step when playing
            if self.is_playing and (cur_time - self.last_step_time) >= step_interval:
                steps_per_frame = 8 if self.speed_multiplier == 50 else 1
                for _ in range(steps_per_frame):
                    adv = self.step_forward()
                    if not adv or not self.is_playing:
                        break
                self.last_step_time = cur_time

            # Render frame
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
            self.anim_tick += 1

        pygame.quit()

    def draw(self) -> None:
        """Renders chessboard, pieces, laser conflict beams, and HUD."""
        self.screen.fill(self.COLOR_BG)

        # 1. Draw Chessboard with textured or shaded tiles
        self._draw_board()

        # 2. Draw Candidate Rows & Conflict Numbers
        self._draw_candidate_overlays()

        # 3. Draw Hover Preview (Coordinate & Manual Sandbox Safety Check)
        self._draw_hover_preview()

        # 4. Draw Laser Attack Lines and impact particles
        self._draw_conflict_lasers()

        # 5. Draw Queen Pieces (PNG assets or vector crowns)
        self._draw_queens()

        # 6. Draw Right Sidebar & Telemetry HUD
        self._draw_sidebar()

        # 7. Draw Bottom Status Banner
        self._draw_status_bar()

    def _draw_board(self) -> None:
        """Renders alternating board tiles, coordinate letters, and board frame."""
        bx = self.board_rect.x
        by = self.board_rect.y
        cs = self.cell_size

        # Board drop shadow
        shadow_rect = pygame.Rect(bx + 6, by + 6, self.board_rect.w, self.board_rect.h)
        pygame.draw.rect(self.screen, (8, 10, 16), shadow_rect, border_radius=6)

        # Outer border frame
        frame_rect = pygame.Rect(bx - 3, by - 3, self.board_rect.w + 6, self.board_rect.h + 6)
        pygame.draw.rect(self.screen, self.COLOR_TILE_BORDER, frame_rect, border_radius=6)

        tile_light_asset = self.scaled_assets.get("tile_light")
        tile_dark_asset = self.scaled_assets.get("tile_dark")

        # Draw alternating squares
        for r in range(self.n):
            for c in range(self.n):
                cell_rect = pygame.Rect(bx + c * cs, by + r * cs, cs, cs)
                is_light = (r + c) % 2 == 0

                # Render textured asset if available
                if is_light and tile_light_asset:
                    self.screen.blit(tile_light_asset, cell_rect.topleft)
                elif not is_light and tile_dark_asset:
                    self.screen.blit(tile_dark_asset, cell_rect.topleft)
                else:
                    tile_color = self.COLOR_TILE_LIGHT if is_light else self.COLOR_TILE_DARK
                    pygame.draw.rect(self.screen, tile_color, cell_rect)

                # Subtle highlight on active candidate column
                if c == self.candidate_col:
                    glow_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                    glow_surf.fill((255, 255, 200, 35))
                    self.screen.blit(glow_surf, cell_rect.topleft)

                pygame.draw.rect(self.screen, (30, 40, 56), cell_rect, 1)

        # Column labels (A, B, C...) and Row labels (1, 2, 3...)
        for c in range(self.n):
            col_letter = chr(ord('A') + c) if self.n <= 26 else str(c)
            lbl = self.fonts["coords"].render(col_letter, True, self.COLOR_COORD_TEXT)
            self.screen.blit(lbl, (bx + c * cs + cs // 2 - lbl.get_width() // 2, by - 20))
            self.screen.blit(lbl, (bx + c * cs + cs // 2 - lbl.get_width() // 2, by + self.board_rect.h + 5))

        for r in range(self.n):
            row_num = str(self.n - r)
            lbl = self.fonts["coords"].render(row_num, True, self.COLOR_COORD_TEXT)
            self.screen.blit(lbl, (bx - 22, by + r * cs + cs // 2 - lbl.get_height() // 2))
            self.screen.blit(lbl, (bx + self.board_rect.w + 8, by + r * cs + cs // 2 - lbl.get_height() // 2))

    def _draw_candidate_overlays(self) -> None:
        """Visualizes tested rows and conflict scores during Min-Conflicts or Backtracking."""
        bx = self.board_rect.x
        by = self.board_rect.y
        cs = self.cell_size

        # In Min-Conflicts EVAL_ROWS: show conflict numbers on each row of the selected column
        if self.candidate_col >= 0 and self.row_conflicts_eval and len(self.row_conflicts_eval) == self.n:
            c = self.candidate_col
            min_c = min(self.row_conflicts_eval)
            for r in range(self.n):
                c_val = self.row_conflicts_eval[r]
                rect = pygame.Rect(bx + c * cs, by + r * cs, cs, cs)

                if c_val == min_c:
                    tint = pygame.Surface((cs, cs), pygame.SRCALPHA)
                    tint.fill((46, 204, 113, 85))  # Green tint for min conflict
                    self.screen.blit(tint, rect.topleft)
                elif c_val > 0:
                    tint = pygame.Surface((cs, cs), pygame.SRCALPHA)
                    tint.fill((231, 76, 60, 50))   # Red tint for higher conflict
                    self.screen.blit(tint, rect.topleft)

                # Conflict count badge
                badge_bg = (40, 160, 80) if c_val == min_c else (200, 50, 50)
                badge_lbl = self.fonts["badge"].render(str(c_val), True, (255, 255, 255))
                b_rect = pygame.Rect(rect.right - 18, rect.bottom - 18, 16, 16)
                pygame.draw.rect(self.screen, badge_bg, b_rect, border_radius=3)
                self.screen.blit(badge_lbl, (b_rect.centerx - badge_lbl.get_width() // 2, b_rect.centery - badge_lbl.get_height() // 2))

            # Highlight optimal destination row and draw directional arrow in Min-Conflicts
            if self.algorithm_mode.startswith("MIN_CONFLICTS") and 0 <= self.candidate_row < self.n:
                dest_rect = pygame.Rect(bx + c * cs + 2, by + self.candidate_row * cs + 2, cs - 4, cs - 4)
                pygame.draw.rect(self.screen, self.COLOR_SUCCESS_GREEN, dest_rect, 3, border_radius=4)

                cur_r = self.board[c]
                if self.candidate_type == "EVAL_ROWS" and 0 <= cur_r < self.n and cur_r != self.candidate_row:
                    cx_mid = bx + c * cs + cs // 2
                    start_y = by + cur_r * cs + cs // 2
                    end_y = by + self.candidate_row * cs + cs // 2
                    step_dir = 1 if end_y > start_y else -1
                    tip_y = end_y - step_dir * max(6, cs // 5)
                    shaft_start = start_y + step_dir * max(6, cs // 5)
                    arrow_col = (56, 225, 160)
                    pygame.draw.line(self.screen, arrow_col, (cx_mid, shaft_start), (cx_mid, tip_y), 3)
                    head_sz = max(5, cs // 8)
                    pts = [
                        (cx_mid, tip_y + step_dir * head_sz),
                        (cx_mid - head_sz, tip_y - step_dir * (head_sz // 2)),
                        (cx_mid + head_sz, tip_y - step_dir * (head_sz // 2)),
                    ]
                    pygame.draw.polygon(self.screen, arrow_col, pts)

        # In Backtracking: show candidate cell evaluation
        elif self.candidate_col >= 0 and self.candidate_row >= 0:
            c = self.candidate_col
            r = self.candidate_row
            rect = pygame.Rect(bx + c * cs, by + r * cs, cs, cs)
            pulse = abs(math.sin(self.anim_tick * 0.15))

            if self.candidate_type == "SAFE":
                color = (46, 213, 115, int(120 + 80 * pulse))
                surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                surf.fill(color)
                self.screen.blit(surf, rect.topleft)
                pygame.draw.rect(self.screen, self.COLOR_SUCCESS_GREEN, rect, 3)

            elif self.candidate_type == "CONFLICT":
                color = (235, 65, 65, int(130 + 90 * pulse))
                surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                surf.fill(color)
                self.screen.blit(surf, rect.topleft)
                pygame.draw.rect(self.screen, (240, 50, 50), rect, 3)

            elif self.candidate_type == "BACKTRACK":
                color = (243, 156, 18, int(140 + 80 * pulse))
                surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                surf.fill(color)
                self.screen.blit(surf, rect.topleft)
                pygame.draw.rect(self.screen, (230, 126, 34), rect, 3)

    def _draw_hover_preview(self) -> None:
        """Draws hover cell frame, coordinate label, and Manual Sandbox conflict/safe preview."""
        if self.is_playing:
            return

        bx = self.board_rect.x
        by = self.board_rect.y
        cs = self.cell_size

        mx, my = pygame.mouse.get_pos()
        if self.board_rect.collidepoint(mx, my):
            c = (mx - bx) // cs
            r = (my - by) // cs
        elif self.hovered_cell is not None:
            r, c = self.hovered_cell
        else:
            return

        if not (0 <= r < self.n and 0 <= c < self.n):
            return

        rect = pygame.Rect(bx + c * cs, by + r * cs, cs, cs)
        col_letter = chr(ord('A') + c) if self.n <= 26 else str(c)
        coord_text = f"{col_letter}{self.n - r}"

        if self.algorithm_mode == "MANUAL" and self.board[c] != r:
            attackers = [
                (self.board[c2], c2)
                for c2 in range(self.n)
                if c2 != c and self.board[c2] != -1
                and (self.board[c2] == r or abs(self.board[c2] - r) == abs(c2 - c))
            ]
            if attackers:
                tint = pygame.Surface((cs, cs), pygame.SRCALPHA)
                tint.fill((235, 65, 65, 80))
                self.screen.blit(tint, rect.topleft)
                pygame.draw.rect(self.screen, (240, 70, 70), rect, 2)
                p_dest = (rect.centerx, rect.centery)
                for r_att, c_att in attackers:
                    p_att = (bx + c_att * cs + cs // 2, by + r_att * cs + cs // 2)
                    # Draw dashed warning line
                    dist = math.hypot(p_dest[0] - p_att[0], p_dest[1] - p_att[1])
                    steps = max(1, int(dist // 10))
                    for s in range(0, steps, 2):
                        t0 = s / steps
                        t1 = min(1.0, (s + 1) / steps)
                        q0 = (int(p_att[0] + (p_dest[0] - p_att[0]) * t0), int(p_att[1] + (p_dest[1] - p_att[1]) * t0))
                        q1 = (int(p_att[0] + (p_dest[0] - p_att[0]) * t1), int(p_att[1] + (p_dest[1] - p_att[1]) * t1))
                        pygame.draw.line(self.screen, (255, 110, 110), q0, q1, 2)
            else:
                tint = pygame.Surface((cs, cs), pygame.SRCALPHA)
                tint.fill((46, 213, 115, 75))
                self.screen.blit(tint, rect.topleft)
                pygame.draw.rect(self.screen, self.COLOR_SUCCESS_GREEN, rect, 2)
                ghost_img = self.scaled_assets.get("queen_safe")
                if ghost_img:
                    ghost = ghost_img.copy()
                    ghost.set_alpha(115)
                    self.screen.blit(ghost, (rect.centerx - ghost.get_width() // 2, rect.centery - ghost.get_height() // 2))
        else:
            pygame.draw.rect(self.screen, self.COLOR_QUEEN_CYAN, rect, 2)

        lbl = self.fonts["badge"].render(coord_text, True, (255, 255, 255))
        pill = pygame.Rect(rect.x + 3, rect.y + 3, lbl.get_width() + 6, lbl.get_height() + 2)
        pygame.draw.rect(self.screen, (16, 22, 34), pill, border_radius=3)
        self.screen.blit(lbl, (pill.x + 3, pill.y + 1))

    def _draw_conflict_lasers(self) -> None:
        """Draws glowing laser attack beams with flare particles connecting conflicting queens."""
        has_candidate_lasers = (
            self.candidate_type == "CONFLICT"
            and bool(self.candidate_conflicts)
            and 0 <= self.candidate_col < self.n
            and 0 <= self.candidate_row < self.n
        )
        if not self.active_conflicts and not has_candidate_lasers:
            return

        bx = self.board_rect.x
        by = self.board_rect.y
        cs = self.cell_size

        flare_asset = self.scaled_assets.get("spark_flare")

        laser_pairs = list(self.active_conflicts)
        if has_candidate_lasers:
            for r_att, c_att in self.candidate_conflicts:
                laser_pairs.append(((r_att, c_att), (self.candidate_row, self.candidate_col)))

        for (r1, c1), (r2, c2) in laser_pairs:
            p1 = (bx + c1 * cs + cs // 2, by + r1 * cs + cs // 2)
            p2 = (bx + c2 * cs + cs // 2, by + r2 * cs + cs // 2)

            # Draw outer glow line
            pygame.draw.line(self.screen, (255, 60, 60), p1, p2, 4)
            # Draw bright laser core
            pygame.draw.line(self.screen, (255, 230, 230), p1, p2, 2)

            # Blit spark flare asset or draw circles
            if flare_asset:
                f_w = flare_asset.get_width()
                f_h = flare_asset.get_height()
                self.screen.blit(flare_asset, (p1[0] - f_w // 2, p1[1] - f_h // 2))
                self.screen.blit(flare_asset, (p2[0] - f_w // 2, p2[1] - f_h // 2))
            else:
                pygame.draw.circle(self.screen, (240, 50, 50), p1, 7)
                pygame.draw.circle(self.screen, (255, 255, 255), p1, 3)
                pygame.draw.circle(self.screen, (240, 50, 50), p2, 7)
                pygame.draw.circle(self.screen, (255, 255, 255), p2, 3)

    def _draw_queens(self) -> None:
        """Draws high-resolution queen pieces using PNG assets or vector crowns."""
        bx = self.board_rect.x
        by = self.board_rect.y
        cs = self.cell_size

        conflicted_cols = set()
        for (r1, c1), (r2, c2) in self.active_conflicts:
            conflicted_cols.add(c1)
            conflicted_cols.add(c2)

        is_solved = self._is_board_complete_and_valid()

        for c in range(self.n):
            r = self.board[c]
            if r == -1:
                continue

            cx = bx + c * cs + cs // 2
            cy = by + r * cs + cs // 2

            # Determine piece asset key & theme
            if c in conflicted_cols:
                asset_key = "queen_conflict"
                theme = "CONFLICT"
            elif c == self.candidate_col and self.candidate_type == "SAFE":
                asset_key = "queen_safe"
                theme = "GREEN"
            elif c == self.candidate_col:
                asset_key = "queen_candidate"
                theme = "CYAN"
            elif is_solved:
                asset_key = "queen_safe"
                theme = "GREEN"
            else:
                asset_key = "queen_gold"
                theme = "GOLD"

            # Prefer scaled PNG asset
            if asset_key in self.scaled_assets:
                img = self.scaled_assets[asset_key]
                self.screen.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))
            else:
                self._draw_vector_queen(cx, cy, cs, theme)

    def _draw_vector_queen(self, cx: int, cy: int, size: int, theme: str) -> None:
        """Fallback crisp scalable vector queen crown."""
        w = int(size * 0.72)
        h = int(size * 0.68)
        left = cx - w // 2
        right = cx + w // 2
        bottom = cy + h // 2 - int(size * 0.06)
        top = cy - h // 2 + int(size * 0.08)

        if theme == "CONFLICT":
            base_col = (235, 65, 65)
            shadow_col = (160, 30, 30)
            pearl_col = (255, 180, 180)
            gem_col = (255, 230, 100)
        elif theme == "GREEN":
            base_col = (46, 213, 115)
            shadow_col = (30, 140, 75)
            pearl_col = (200, 255, 220)
            gem_col = (255, 255, 255)
        elif theme == "CYAN":
            base_col = (46, 204, 250)
            shadow_col = (25, 120, 170)
            pearl_col = (210, 245, 255)
            gem_col = (255, 230, 100)
        else:  # GOLD
            base_col = self.COLOR_QUEEN_GOLD
            shadow_col = self.COLOR_QUEEN_SHADOW
            pearl_col = (255, 245, 180)
            gem_col = (230, 50, 50)

        # Drop shadow beneath piece
        shadow_rect = pygame.Rect(left + int(w * 0.1), bottom - int(h * 0.08), int(w * 0.8), int(h * 0.22))
        pygame.draw.ellipse(self.screen, (16, 20, 30), shadow_rect)

        # Crown 5-point polygon vertices
        p_left = (left, top + int(h * 0.22))
        p_in1 = (cx - int(w * 0.24), cy - int(h * 0.02))
        p_mid = (cx, top)
        p_in2 = (cx + int(w * 0.24), cy - int(h * 0.02))
        p_right = (right, top + int(h * 0.22))
        b_right = (right - int(w * 0.08), bottom - int(h * 0.18))
        b_left = (left + int(w * 0.08), bottom - int(h * 0.18))

        crown_poly = [b_left, p_left, p_in1, p_mid, p_in2, p_right, b_right]

        pygame.draw.polygon(self.screen, shadow_col, crown_poly)
        inner_poly = [(px, py - 1) for px, py in crown_poly]
        pygame.draw.polygon(self.screen, base_col, inner_poly)
        pygame.draw.polygon(self.screen, (25, 30, 42), crown_poly, 2)

        # Pearls on 5 tips
        pearl_r = max(2, int(size * 0.055))
        tips = [p_left, p_in1, p_mid, p_in2, p_right]
        for tx, ty in tips:
            pygame.draw.circle(self.screen, shadow_col, (tx, ty), pearl_r + 1)
            pygame.draw.circle(self.screen, pearl_col, (tx, ty - 1), pearl_r)

        # Pedestal base rim
        base_h = max(3, int(h * 0.14))
        base_rect = pygame.Rect(left + int(w * 0.05), bottom - base_h, int(w * 0.9), base_h)
        pygame.draw.rect(self.screen, shadow_col, base_rect, border_radius=3)
        pygame.draw.rect(self.screen, base_col, pygame.Rect(base_rect.x, base_rect.y - 1, base_rect.w, base_rect.h - 1), border_radius=3)
        pygame.draw.rect(self.screen, (25, 30, 42), base_rect, 1, border_radius=3)

        # Center jewel
        gem_r = max(2, int(size * 0.045))
        gem_y = cy + int(h * 0.1)
        pygame.draw.circle(self.screen, shadow_col, (cx, gem_y), gem_r + 1)
        pygame.draw.circle(self.screen, gem_col, (cx, gem_y), gem_r)

    def _draw_sidebar(self) -> None:
        """Renders the redesigned, clean telemetry cards and interactive control deck."""
        sb_x = self.width - self.sidebar_width
        sb_w = self.sidebar_width
        sb_h = self.height

        # Sidebar background
        sidebar_rect = pygame.Rect(sb_x, 0, sb_w, sb_h)
        pygame.draw.rect(self.screen, self.COLOR_SIDEBAR_BG, sidebar_rect)
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (sb_x, 0), (sb_x, sb_h), 2)

        # Header with crown emblem asset
        emblem = self.scaled_assets.get("crown_emblem")
        text_start_x = sb_x + 16
        if emblem:
            self.screen.blit(emblem, (sb_x + 16, 14))
            text_start_x = sb_x + 58

        title_surf = self.fonts["title"].render("N-QUEENS AI VISUALIZER", True, self.COLOR_TEXT)
        sub_surf = self.fonts["small"].render("Course 503043 - Propositional Logic & Local Search", True, self.COLOR_TEXT_DIM)
        self.screen.blit(title_surf, (text_start_x, 12))
        self.screen.blit(sub_surf, (text_start_x, 36))

        # Divider line
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (sb_x + 16, 56), (sb_x + sb_w - 16, 56), 1)

        # Section Label for Algorithms
        algo_lbl = self.fonts["small"].render("SELECT ALGORITHM / SOLVER MODE:", True, self.COLOR_TEXT_DIM)
        self.screen.blit(algo_lbl, (sb_x + 16, 172))

        # Sync PLAY/PAUSE button label dynamically
        for btn in self.buttons:
            if btn["id"] == "btn_play":
                btn["label"] = "PAUSE" if self.is_playing else "PLAY"
            self._draw_button(btn)

        # Section Card 1: Clean Search Telemetry Grid (Req 2 & 3)
        card1_y = 336
        self._draw_diagnostics_card(sb_x + 16, card1_y, sb_w - 32)

        # Section Card 2: Propositional Logic CNF Summary (Req 1)
        card2_y = 562
        self._draw_cnf_card(sb_x + 16, card2_y, sb_w - 32)

    def _draw_metric_tile(
        self, x: int, y: int, w: int, h: int,
        label: str, val: str, val_color: Tuple[int, int, int],
        sub_label: str = ""
    ) -> None:
        """Renders a clean, modern metric box with clear hierarchy and generous spacing."""
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (18, 24, 35), rect, border_radius=6)
        pygame.draw.rect(self.screen, (38, 50, 70), rect, 1, border_radius=6)

        lbl_surf = self.fonts["small"].render(label, True, self.COLOR_TEXT_DIM)
        val_surf = self.fonts["mono_val"].render(val, True, val_color)
        self.screen.blit(lbl_surf, (x + 10, y + 6))
        self.screen.blit(val_surf, (x + 10, y + 23))

        if sub_label:
            sub_surf = self.fonts["small"].render(sub_label, True, self.COLOR_TEXT_MUTED)
            self.screen.blit(sub_surf, (x + w - sub_surf.get_width() - 8, y + 6))

    def _draw_button(self, btn: Dict[str, Any]) -> None:
        """Draws stylized interactive button with active states and hover highlights."""
        rect = btn["rect"]
        bid = btn["id"]
        cat = btn.get("category", "")
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)

        # Determine button active state
        is_active = False
        if cat == "speed" and btn.get("val") == self.speed_multiplier:
            is_active = True
        elif cat == "algo" and btn.get("algo") == self.algorithm_mode:
            is_active = True
        elif cat == "n_select" and btn.get("n_val") == self.n:
            is_active = True
        elif bid == "btn_play" and self.is_playing:
            is_active = True

        # Color schemes
        if bid == "btn_play" and not self.is_playing:
            bg_color = (22, 135, 85) if not is_hover else (30, 165, 105)
            border_color = (46, 204, 113)
            text_color = (255, 255, 255)
        elif bid == "btn_solve":
            bg_color = (30, 112, 142) if is_hover else (22, 82, 108)
            border_color = (86, 204, 248) if is_hover else (46, 164, 214)
            text_color = (255, 255, 255)
        elif is_active:
            bg_color = (36, 110, 185)
            border_color = (64, 169, 255)
            text_color = (255, 255, 255)
        elif is_hover:
            bg_color = (42, 54, 76)
            border_color = (68, 88, 122)
            text_color = (255, 255, 255)
        else:
            bg_color = self.COLOR_CARD_BG
            border_color = self.COLOR_CARD_BORDER
            text_color = self.COLOR_TEXT

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, border_color, rect, 1, border_radius=5)

        lbl_surf = self.fonts["body_bold" if (is_active or bid in ("btn_play", "btn_solve")) else "body"].render(btn["label"], True, text_color)
        self.screen.blit(lbl_surf, (rect.centerx - lbl_surf.get_width() // 2, rect.centery - lbl_surf.get_height() // 2))

    def _draw_diagnostics_card(self, x: int, y: int, w: int) -> None:
        """Displays live search metrics in a clean, scannable 2x3 grid."""
        card_h = 214
        rect = pygame.Rect(x, y, w, card_h)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, rect, 1, border_radius=8)

        # Header banner
        hdr_rect = pygame.Rect(x, y, w, 30)
        pygame.draw.rect(self.screen, self.COLOR_CARD_HEADER, hdr_rect, border_top_left_radius=8, border_top_right_radius=8)
        hdr_lbl = self.fonts["header"].render("LIVE SEARCH METRICS", True, self.COLOR_QUEEN_CYAN)
        self.screen.blit(hdr_lbl, (x + 12, y + 6))

        # Active mode badge on right of header
        mode_map = {
            "BACKTRACKING": "DFS BACKTRACK",
            "SAT": "GLUCOSE3 SAT",
            "MIN_CONFLICTS_MAX": "MIN-CONF (MAX)",
            "MIN_CONFLICTS_TABU": "MIN-CONF (TABU)",
            "MIN_CONFLICTS_RANDOM": "MIN-CONF (RAND)",
            "BROWSER": "SOL BROWSER",
            "MANUAL": "SANDBOX",
        }
        mode_str = mode_map.get(self.algorithm_mode, self.algorithm_mode)
        badge_surf = self.fonts["badge"].render(mode_str, True, self.COLOR_QUEEN_GOLD)
        self.screen.blit(badge_surf, (x + w - badge_surf.get_width() - 12, y + 8))

        # 2x3 Metric Tiles Grid
        pad = 10
        tile_w = (w - 3 * pad) // 2
        tile_h = 48
        gy = y + 40

        # Row 1: Conflicts & Solutions
        c_val = f"{self.current_conflicts} Attacking" if self.current_conflicts > 0 else "0 (Valid)"
        c_col = self.COLOR_QUEEN_CONFLICT if self.current_conflicts > 0 else self.COLOR_SUCCESS_GREEN
        self._draw_metric_tile(x + pad, gy, tile_w, tile_h, "CONFLICTS", c_val, c_col)

        known_total = KNOWN_SOLUTIONS_COUNT.get(self.n, "?")
        sol_val = f"{self.solutions_found} / {known_total}"
        sol_col = self.COLOR_SUCCESS_GREEN if self.solutions_found > 0 else self.COLOR_TEXT
        self._draw_metric_tile(x + 2 * pad + tile_w, gy, tile_w, tile_h, "SOLUTIONS FOUND", sol_val, sol_col)

        # Row 2: States Tested & Search Steps
        gy += tile_h + 8
        self._draw_metric_tile(x + pad, gy, tile_w, tile_h, "STATES EXPLORED", f"{self.cases_explored:,}", self.COLOR_QUEEN_CYAN)
        self._draw_metric_tile(x + 2 * pad + tile_w, gy, tile_w, tile_h, "SEARCH STEPS", f"{self.steps_count:,}", self.COLOR_TEXT)

        # Row 3: Backtracks / Restarts & Execution Time
        gy += tile_h + 8
        if self.algorithm_mode.startswith("MIN_CONFLICTS"):
            br_lbl = "RANDOM RESTARTS"
            br_val = f"{self.restarts_count:,}"
        else:
            br_lbl = "BACKTRACKS"
            br_val = f"{self.backtracks_count:,}"
        self._draw_metric_tile(x + pad, gy, tile_w, tile_h, br_lbl, br_val, self.COLOR_AMBER_ALERT)
        self._draw_metric_tile(x + 2 * pad + tile_w, gy, tile_w, tile_h, "EXECUTION TIME", f"{self.execution_time_ms:.2f} ms", self.COLOR_QUEEN_GOLD)

    def _draw_cnf_card(self, x: int, y: int, w: int) -> None:
        """Displays Propositional Logic CNF statistics in a clean 2x2 summary grid."""
        card_h = 200
        rect = pygame.Rect(x, y, w, card_h)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, rect, 1, border_radius=8)

        # Header banner
        hdr_rect = pygame.Rect(x, y, w, 30)
        pygame.draw.rect(self.screen, self.COLOR_CARD_HEADER, hdr_rect, border_top_left_radius=8, border_top_right_radius=8)
        hdr_lbl = self.fonts["header"].render(f"CNF PROPOSITIONAL LOGIC (N = {self.n})", True, self.COLOR_QUEEN_GOLD)
        self.screen.blit(hdr_lbl, (x + 12, y + 6))

        match_surf = self.fonts["badge"].render("VERIFIED", True, self.COLOR_SUCCESS_GREEN)
        self.screen.blit(match_surf, (x + w - match_surf.get_width() - 12, y + 8))

        n = self.n
        vars_count = self.cnf_stats.get("variables", n * n)
        total_clauses = self.cnf_stats.get("total_clauses", 0)
        diag_amo = self.cnf_stats.get("diagonal_amo", 0)
        row_amo = self.cnf_stats.get("row_amo", 0)
        row_col_clauses = 2 * n + 2 * row_amo

        pad = 10
        tile_w = (w - 3 * pad) // 2
        tile_h = 50
        gy = y + 40

        # Row 1: Variables & Row/Col Clauses
        self._draw_metric_tile(
            x + pad, gy, tile_w, tile_h,
            "BOOLEAN VARIABLES", f"{vars_count:,}", self.COLOR_TEXT, "N x N"
        )
        self._draw_metric_tile(
            x + 2 * pad + tile_w, gy, tile_w, tile_h,
            "ROW & COL CLAUSES", f"{row_col_clauses:,}", self.COLOR_QUEEN_CYAN, "ALO + AMO"
        )

        # Row 2: Diagonal Clauses & Total Clauses
        gy += tile_h + 8
        self._draw_metric_tile(
            x + pad, gy, tile_w, tile_h,
            "DIAGONAL CLAUSES", f"{diag_amo:,}", self.COLOR_QUEEN_CYAN, "AMO"
        )
        self._draw_metric_tile(
            x + 2 * pad + tile_w, gy, tile_w, tile_h,
            "TOTAL CNF CLAUSES", f"{total_clauses:,}", self.COLOR_SUCCESS_GREEN, "100% Match"
        )

        # Clean Formula Reference Footer
        fy = gy + tile_h + 10
        formula_str = f"Formula: 2N + N^2(N-1) + N(N-1)(2N-1)/3 = {total_clauses:,} clauses"
        f_surf = self.fonts["small"].render(formula_str, True, self.COLOR_TEXT_DIM)
        self.screen.blit(f_surf, (x + (w - f_surf.get_width()) // 2, fy))

    def _draw_status_bar(self) -> None:
        """Renders live tactical status banner at the bottom of the screen."""
        bar_h = 28
        bar_y = self.height - bar_h
        bar_w = self.width - self.sidebar_width
        rect = pygame.Rect(0, bar_y, bar_w, bar_h)

        pygame.draw.rect(self.screen, (10, 14, 20), rect)
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (0, bar_y), (bar_w, bar_y), 1)

        # Status badge
        if self._is_board_complete_and_valid():
            badge_text = "SOLVED"
            badge_col = self.COLOR_SUCCESS_GREEN
        elif self.current_conflicts > 0 or (self.candidate_type == "CONFLICT" and self.candidate_conflicts):
            badge_text = "CONFLICT"
            badge_col = self.COLOR_QUEEN_CONFLICT
        elif self.is_playing:
            badge_text = "SEARCHING"
            badge_col = self.COLOR_QUEEN_CYAN
        else:
            badge_text = "IDLE"
            badge_col = self.COLOR_TEXT_MUTED

        badge_surf = self.fonts["badge"].render(f"[{badge_text}]", True, badge_col)
        self.screen.blit(badge_surf, (15, bar_y + 6))

        # Status narrative message (clipped cleanly before sidebar boundary)
        msg_x = 105
        max_msg_w = max(80, bar_w - msg_x - 10)
        msg_surf = self.fonts["body"].render(self.status_message, True, self.COLOR_TEXT)
        if msg_surf.get_width() > max_msg_w:
            self.screen.blit(msg_surf, (msg_x, bar_y + 6), area=pygame.Rect(0, 0, max_msg_w, msg_surf.get_height()))
        else:
            self.screen.blit(msg_surf, (msg_x, bar_y + 6))
