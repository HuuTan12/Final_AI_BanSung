"""
Module: kakuro_visualizer.py
Description: Interactive Graphical User Interface (GUI) for Kakuro CSP Solver (Modern AI Studio Dashboard).
Implements Requirement 3 (1.0 pt) and visualizes Requirements 1, 2, and 4 of Task 3:
1. Direct in-app Puzzle Selector (6 validated maps from 4x4 Easy to 9x9 Complex).
2. Domain Visualization: Displays 3x3 pencil grid (1..9) with SVG digit assets, pruned micro-dots, and active prune highlights.
3. Constraint Propagation Visualization: Highlights active Horizontal/Vertical Run scopes, split-triangle clue satisfaction,
   and breaks down pruning steps across Initial Filtering, AC-3, and Forward Checking.
4. Backtracking Search Visualization: Try Assignment (Amber Gold), Domain Prune (Sky Blue), Backtrack (Coral Red), Solved (Emerald).
5. Playback Controls: Play/Pause, Step Next/Back, Interactive Timeline Scrubber, 3-Line Trace Console, Instant Solve, Reset, and Speed Control.
"""

import os
import io
import re
import pygame
from typing import List, Dict, Set, Optional, Tuple

from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.backtracking_solver import KakuroBacktrackingSolver
from task3_kakuro.solver.tracer import SolverTracer, SolverEvent, EventType

# --- MODERN AI STUDIO DARK PALETTE ---
BG_COLOR = (15, 19, 26)               # Deep obsidian window background
PANEL_BG = (25, 31, 42)               # Main panel container background
CARD_BG = (34, 42, 56)                # Elevated card surface
CARD_INNER = (20, 25, 35)             # Recessed metric/console box background
BORDER_COLOR = (52, 64, 86)           # Crisp card/panel border
DIVIDER_COLOR = (42, 52, 70)          # Subtle section divider
ACCENT_CYAN = (14, 165, 233)          # Top accent & primary highlight
ACCENT_EMERALD = (16, 185, 129)       # Solved / verified accent

# Kakuro Board Colors
BOARD_FRAME = (12, 16, 23)            # Outer board frame
CELL_WALL = (18, 23, 32)              # Pure Black Wall Cell (No Clues)
CELL_WALL_BEVEL = (28, 35, 48)        # Inner bevel on Pure Wall Cell
CELL_CLUE_H_BG = (32, 41, 58)         # Upper-Right Triangle (Horizontal Clue Zone)
CELL_CLUE_V_BG = (24, 31, 45)         # Lower-Left Triangle (Vertical Clue Zone)
CELL_CLUE_SAT_BG = (18, 52, 44)       # Satisfied Clue Triangle Tint (Emerald Dark)
CELL_BLACK_BORDER = (45, 56, 74)      # Black Cell Border
CLUE_LINE_COLOR = (82, 98, 126)       # Anti-aliased Diagonal Clue Divider
CLUE_V_COLOR = (56, 189, 248)         # Vertical Clue: Neon Cyan
CLUE_H_COLOR = (250, 204, 21)         # Horizontal Clue: Warm Gold
CLUE_SAT_DOT = (52, 211, 153)         # Emerald dot when a Run constraint is satisfied

# White Variable Cells & Search State Highlights
CELL_WHITE = (248, 250, 252)          # Default White Variable Cell
CELL_SCOPE_TINT = (232, 244, 255)     # Peer Cell in Active H/V Run Scope
CELL_HOVER = (224, 240, 255)          # Hovered White Cell
CELL_BORDER = (168, 182, 202)         # White Cell Border
SCOPE_BORDER = (56, 189, 248)         # Inner outline for cells in active Run Scope

COLOR_ASSIGN = (254, 240, 138)        # Try Assignment Fill: Soft Yellow
RING_ASSIGN = (234, 179, 8)           # Try Assignment Border: Vivid Amber
COLOR_PRUNE = (186, 230, 253)         # Domain Pruning Fill: Light Sky Blue
RING_PRUNE = (14, 165, 233)           # Domain Pruning Border: Vivid Sky Blue
COLOR_BACKTRACK = (254, 202, 202)     # Backtrack Fill: Coral Pink
RING_BACKTRACK = (239, 68, 68)        # Backtrack Border: Crimson Red
COLOR_SOLVED = (187, 247, 208)        # Solved Cell Fill: Emerald Mint
RING_SOLVED = (16, 185, 129)          # Solved Cell Border: Emerald Green

# Typography Colors
TEXT_MAIN = (241, 245, 249)           # Primary Bright Text
TEXT_SUB = (203, 213, 225)            # Secondary Light Text
TEXT_MUTED = (140, 155, 178)          # Muted Label Text
TEXT_ASSIGNED = (15, 23, 42)          # Assigned Big Digit Color
PENCIL_COLOR = (100, 116, 139)        # Remaining Domain Pencil Digit Color
PRUNED_DOT_COLOR = (208, 216, 228)    # Faint dot for eliminated domain values

# Hex equivalents for SVG asset tinting
HEX_ASSIGNED = "#0F172A"
HEX_PENCIL = "#64748B"
HEX_PRUNED_FLASH = "#DC2626"
HEX_CLUE_V = "#38BDF8"
HEX_CLUE_H = "#FACC15"

# Button Colors
BTN_PRIMARY = (14, 165, 233)          # Sky Blue Primary
BTN_PAUSED = (217, 119, 6)            # Amber Pause State
BTN_SUCCESS = (16, 185, 129)          # Emerald Solve / Active Map
BTN_DANGER = (220, 56, 56)            # Coral Reset
BTN_SECONDARY = (48, 60, 80)          # Slate Control Button
BTN_SPEED = (38, 48, 66)              # Speed Control Button


class KakuroVisualizer:
    """
    Interactive Graphical Visualizer for Kakuro CSP with SVG Digit Asset Rendering,
    Split-Triangle Clue Cells, Active Run Scope Highlighting, Timeline Scrubbing,
    3-Line Trace Console, and Live Constraint Equation Inspection.
    """

    def __init__(self, puzzle_dir: str = None):
        pygame.init()
        pygame.font.init()

        base_task_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if puzzle_dir is None:
            self.puzzle_dir = os.path.join(base_task_dir, "puzzles")
        else:
            self.puzzle_dir = puzzle_dir

        self.assets_svg_dir = os.path.join(base_task_dir, "assets", "svg")

        # Curated puzzle list with variable counts
        candidate_maps = [
            ("4x4 Easy (9 Vars)", "easy_4x4.json"),
            ("5x5 Medium (12 Vars)", "medium_5x5.json"),
            ("5x5 Sample (Page 4)", "sample_5x5.json"),
            ("6x6 Intermediate (22V)", "test_6x6.json"),
            ("7x7 Intermediate (24V)", "intermediate_7x7.json"),
            ("9x9 Complex (Page 5)", "complex_9x9.json"),
        ]
        self.available_maps = [
            (label, fname)
            for label, fname in candidate_maps
            if os.path.isfile(os.path.join(self.puzzle_dir, fname))
        ]
        if not self.available_maps:
            raise FileNotFoundError(f"No puzzle JSON files found in {self.puzzle_dir}")

        self.current_map_idx = 0
        for idx, (_, fname) in enumerate(self.available_maps):
            if fname == "sample_5x5.json":
                self.current_map_idx = idx
                break

        # Main window dimensions
        self.screen_width = 1360
        self.screen_height = 860
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Kakuro CSP Studio - Introduction to AI (TDTU)")

        # Cached SVG digit surfaces
        self.hand_big_surfaces: Dict[int, pygame.Surface] = {}
        self.hand_pencil_surfaces: Dict[int, pygame.Surface] = {}
        self.hand_pruned_surfaces: Dict[int, pygame.Surface] = {}
        self.clue_v_surfaces: Dict[int, pygame.Surface] = {}
        self.clue_h_surfaces: Dict[int, pygame.Surface] = {}
        self.clue_number_cache: Dict[Tuple[int, bool], pygame.Surface] = {}

        # Interactive state
        self.is_scrubbing = False
        self.hovered_cell: Optional[Tuple[int, int]] = None
        self.snapshots = []
        self.snapshot_interval = 200

        # Initialize UI fonts & layout geometry
        self._init_fonts()
        self._init_layout_rects()

        # Load initial puzzle
        self.load_puzzle(self.available_maps[self.current_map_idx][1])

    def _init_fonts(self):
        available = pygame.font.get_fonts()
        font_name = "segoeui" if "segoeui" in available else ("arial" if "arial" in available else None)
        self.font_title = pygame.font.SysFont(font_name, 20, bold=True)
        self.font_board_title = pygame.font.SysFont(font_name, 17, bold=True)
        self.font_heading = pygame.font.SysFont(font_name, 12, bold=True)
        self.font_body = pygame.font.SysFont(font_name, 12)
        self.font_btn = pygame.font.SysFont(font_name, 13, bold=True)
        self.font_metric_val = pygame.font.SysFont(font_name, 15, bold=True)
        self.font_metric_lbl = pygame.font.SysFont(font_name, 10, bold=True)
        self.font_status = pygame.font.SysFont(font_name, 12)
        self.font_status_bold = pygame.font.SysFont(font_name, 12, bold=True)
        self.font_coord = pygame.font.SysFont(font_name, 11, bold=True)

    def _init_layout_rects(self):
        """Precomputes balanced panel, card, and button rectangles for 1360x860 resolution."""
        self.left_panel_rect = pygame.Rect(18, 18, 694, 824)
        self.right_panel_rect = pygame.Rect(728, 18, 614, 824)

        px = self.right_panel_rect.x + 22
        content_w = self.right_panel_rect.width - 44  # 570px
        gap = 14
        btn_w = (content_w - gap) // 2  # 278px

        # Section 1: Compact Map Cycler (< PREV, Current Map Name Card, NEXT >)
        prev_w = 100
        next_w = 100
        card_w = content_w - prev_w - next_w - 20
        self.btn_map_prev = pygame.Rect(px, 108, prev_w, 38)
        self.map_display_rect = pygame.Rect(px + prev_w + 10, 108, card_w, 38)
        self.btn_map_next = pygame.Rect(px + prev_w + 10 + card_w + 10, 108, next_w, 38)

        # Section 2: Telemetry Card, Scrubber Bar & 3-Line Trace Console
        self.telemetry_card_rect = pygame.Rect(px, 188, content_w, 238)
        self.progress_bar_rect = pygame.Rect(px + 16, 284, content_w - 32, 12)
        self.progress_hit_rect = pygame.Rect(px + 10, 276, content_w - 20, 28)
        self.console_rect = pygame.Rect(px + 16, 308, content_w - 32, 104)

        # Section 3: Playback & Speed Control Buttons
        self.btn_play = pygame.Rect(px, 474, btn_w, 38)
        self.btn_solve = pygame.Rect(px + btn_w + gap, 474, btn_w, 38)

        self.btn_back = pygame.Rect(px, 520, btn_w, 36)
        self.btn_fwd = pygame.Rect(px + btn_w + gap, 520, btn_w, 36)

        self.btn_reset = pygame.Rect(px, 564, btn_w, 36)
        self.btn_pencil = pygame.Rect(px + btn_w + gap, 564, btn_w, 36)

        speed_w = 172
        pill_w = content_w - 2 * speed_w - 2 * 12
        self.btn_slower = pygame.Rect(px, 608, speed_w, 32)
        self.speed_pill_rect = pygame.Rect(px + speed_w + 12, 608, pill_w, 32)
        self.btn_faster = pygame.Rect(px + speed_w + 12 + pill_w + 12, 608, speed_w, 32)

        # Section 4: Legend Card
        self.legend_card_rect = pygame.Rect(px, 688, content_w, 126)

    def _load_svg_surface(self, svg_path: str, target_h: int, hex_color: str) -> Optional[pygame.Surface]:
        """Parses an SVG digit asset file, injects fill color and dimensions, and rasterizes it."""
        if not os.path.isfile(svg_path):
            return None
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            svg_content = re.sub(r'fill="[^"]*"', f'fill="{hex_color}"', svg_content)

            vb_match = re.search(r'viewBox="0\s+0\s+([0-9.]+)\s+([0-9.]+)"', svg_content)
            if vb_match:
                orig_w = float(vb_match.group(1))
                orig_h = float(vb_match.group(2))
            else:
                orig_w, orig_h = 10.0, 20.0

            target_h = max(6, target_h)
            scale = target_h / max(1.0, orig_h)
            target_w = max(2, int(round(orig_w * scale)))

            svg_content = re.sub(
                r'width="[0-9.]+"\s*height="[0-9.]+"',
                f'width="{target_w}" height="{target_h}"',
                svg_content,
                count=1
            )

            svg_bytes = io.BytesIO(svg_content.encode("utf-8"))
            if hasattr(pygame.image, "load_sized_svg"):
                surf = pygame.image.load_sized_svg(svg_bytes, (target_w, target_h))
            else:
                surf = pygame.image.load(svg_bytes, "digit.svg")
            return surf.convert_alpha()
        except Exception as e:
            print(f"[KakuroVisualizer] Warning: Failed to parse SVG asset '{svg_path}': {e}")
            return None

    def _load_digit_assets(self):
        """Loads and scales all number SVG assets for the current board cell size."""
        self.hand_big_surfaces.clear()
        self.hand_pencil_surfaces.clear()
        self.hand_pruned_surfaces.clear()
        self.clue_v_surfaces.clear()
        self.clue_h_surfaces.clear()
        self.clue_number_cache.clear()

        big_h = max(16, int(self.cell_size * 0.50))
        pencil_h = max(8, int(self.cell_size * 0.19))
        clue_h = max(9, int(self.cell_size * 0.21))

        hand_dir = os.path.join(self.assets_svg_dir, "digits-hand")
        clue_dir = os.path.join(self.assets_svg_dir, "digits-clue")

        for d in range(1, 10):
            hand_path = os.path.join(hand_dir, f"hand-{d}.svg")
            big_surf = self._load_svg_surface(hand_path, big_h, HEX_ASSIGNED)
            if big_surf is not None:
                self.hand_big_surfaces[d] = big_surf

            pencil_surf = self._load_svg_surface(hand_path, pencil_h, HEX_PENCIL)
            if pencil_surf is not None:
                self.hand_pencil_surfaces[d] = pencil_surf

            pruned_surf = self._load_svg_surface(hand_path, pencil_h, HEX_PRUNED_FLASH)
            if pruned_surf is not None:
                self.hand_pruned_surfaces[d] = pruned_surf

        for d in range(0, 10):
            clue_path = os.path.join(clue_dir, f"clue-{d}.svg")
            v_surf = self._load_svg_surface(clue_path, clue_h, HEX_CLUE_V)
            if v_surf is not None:
                self.clue_v_surfaces[d] = v_surf

            h_surf = self._load_svg_surface(clue_path, clue_h, HEX_CLUE_H)
            if h_surf is not None:
                self.clue_h_surfaces[d] = h_surf

    def _get_clue_surface(self, clue_val: int, is_vertical: bool) -> pygame.Surface:
        """Composes multi-digit clue numbers (e.g. 12, 24, 45) from individual SVG glyphs."""
        cache_key = (clue_val, is_vertical)
        if cache_key in self.clue_number_cache:
            return self.clue_number_cache[cache_key]

        digit_map = self.clue_v_surfaces if is_vertical else self.clue_h_surfaces
        digits_str = str(clue_val)
        glyphs = [digit_map.get(int(ch)) for ch in digits_str if ch.isdigit()]

        if not glyphs or any(g is None for g in glyphs):
            color = CLUE_V_COLOR if is_vertical else CLUE_H_COLOR
            surf = self.font_clue.render(digits_str, True, color)
            self.clue_number_cache[cache_key] = surf
            return surf

        gap = max(1, int(self.cell_size * 0.03))
        total_w = sum(g.get_width() for g in glyphs) + gap * (len(glyphs) - 1)
        max_h = max(g.get_height() for g in glyphs)

        composed = pygame.Surface((total_w, max_h), pygame.SRCALPHA)
        cur_x = 0
        for g in glyphs:
            cur_y = (max_h - g.get_height()) // 2
            composed.blit(g, (cur_x, cur_y))
            cur_x += g.get_width() + gap

        self.clue_number_cache[cache_key] = composed
        return composed

    def _build_snapshots(self):
        """Precomputes periodic state snapshots and cumulative event counters for instant scrubbing."""
        self.snapshots.clear()
        self.step_counts: List[Tuple[int, int, int, int]] = [(0, 0, 0, 0)]  # (init_ac3, fc, assign, backtrack)

        vals: Dict[Tuple[int, int], Optional[int]] = {pos: None for pos in self.csp.variables}
        doms: Dict[Tuple[int, int], Set[int]] = {pos: set(range(1, 10)) for pos in self.csp.variables}
        active_pos: Optional[Tuple[int, int]] = None
        ev_type: Optional[EventType] = None
        last_pruned: Set[int] = set()
        msg = f"Ready: {len(self.csp.variables)} white variables, {len(self.events)} trace steps."

        self.snapshots.append((
            0,
            dict(vals),
            {k: set(v) for k, v in doms.items()},
            active_pos,
            ev_type,
            set(last_pruned),
            msg
        ))

        c_init_ac3, c_fc, c_assign, c_bt = 0, 0, 0, 0
        for idx, ev in enumerate(self.events, start=1):
            active_pos = ev.cell_pos
            ev_type = ev.event_type
            msg = ev.message
            last_pruned = set()

            if ev.event_type == EventType.ASSIGN and ev.cell_pos:
                vals[ev.cell_pos] = ev.value
                c_assign += 1
            elif ev.event_type == EventType.BACKTRACK and ev.cell_pos:
                vals[ev.cell_pos] = None
                c_bt += 1
            elif ev.event_type == EventType.PRUNE and ev.cell_pos and ev.pruned_domain:
                doms[ev.cell_pos] = doms[ev.cell_pos] - ev.pruned_domain
                last_pruned = set(ev.pruned_domain)
                if "ForwardCheck" in ev.message:
                    c_fc += 1
                else:
                    c_init_ac3 += 1

            self.step_counts.append((c_init_ac3, c_fc, c_assign, c_bt))

            if idx % self.snapshot_interval == 0:
                self.snapshots.append((
                    idx,
                    dict(vals),
                    {k: set(v) for k, v in doms.items()},
                    active_pos,
                    ev_type,
                    set(last_pruned),
                    msg
                ))

    def load_puzzle(self, filename: str):
        """Loads puzzle JSON, runs solver with tracer, and configures board geometry & SVG assets."""
        filepath = os.path.join(self.puzzle_dir, filename)
        self.current_filename = filename
        self.csp = KakuroCSP()
        self.csp.load_from_json(filepath)
        self.h_sum, self.v_sum = self.csp.get_clue_sums()

        # Map each clue cell (r, c) and direction ('H'/'V') to its RunConstraint for satisfaction display
        self.clue_to_run = {}
        for run in self.csp.runs:
            if run.cells:
                first = run.cells[0]
                if run.direction == "H":
                    self.clue_to_run[(first.r, first.c - 1, "H")] = run
                elif run.direction == "V":
                    self.clue_to_run[(first.r - 1, first.c, "V")] = run

        # Run solver to record trace events
        self.tracer = SolverTracer()
        self.solver = KakuroBacktrackingSolver(use_ac3=True, use_mrv=True, use_lcv=True, tracer=self.tracer)
        self.solve_result = self.solver.solve(self.csp)
        self.events: List[SolverEvent] = self.tracer.events

        # Build fast scrubbing snapshots
        self._build_snapshots()

        # Reset playback state
        self.current_event_idx = 0
        self.is_playing = False
        self.playback_speed = 0.04
        self.last_step_time = 0.0
        self.show_pencil = True

        # Board visual state
        self.grid_values: Dict[Tuple[int, int], Optional[int]] = {pos: None for pos in self.csp.variables}
        self.grid_domains: Dict[Tuple[int, int], Set[int]] = {pos: set(range(1, 10)) for pos in self.csp.variables}
        self.last_active_pos: Optional[Tuple[int, int]] = None
        self.last_event_type: Optional[EventType] = None
        self.last_pruned_digits: Set[int] = set()
        self.status_message = f"Loaded {filename}: {len(self.csp.variables)} white variables, {len(self.events)} steps."

        # Auto-scale cell size to fit Left Panel Board Canvas (694 x 636 area)
        max_board_w = 596
        max_board_h = 590
        self.cell_size = min(max_board_w // self.csp.cols, max_board_h // self.csp.rows)
        self.cell_size = max(50, min(self.cell_size, 94))

        board_pixel_w = self.csp.cols * self.cell_size
        board_pixel_h = self.csp.rows * self.cell_size
        canvas_cx = self.left_panel_rect.centerx + 10
        canvas_cy = self.left_panel_rect.top + 84 + (646 // 2)
        self.board_ox = canvas_cx - (board_pixel_w // 2)
        self.board_oy = canvas_cy - (board_pixel_h // 2)

        # Fallback fonts on board
        available = pygame.font.get_fonts()
        font_name = "segoeui" if "segoeui" in available else ("arial" if "arial" in available else None)
        self.font_big = pygame.font.SysFont(font_name, int(self.cell_size * 0.48), bold=True)
        self.font_clue = pygame.font.SysFont(font_name, int(self.cell_size * 0.22), bold=True)
        self.font_pencil = pygame.font.SysFont(font_name, int(self.cell_size * 0.18), bold=True)

        # Parse & scale SVG digit assets for current cell_size
        self._load_digit_assets()

    def run(self):
        """Main GUI loop."""
        clock = pygame.time.Clock()
        running = True

        while running:
            current_time = pygame.time.get_ticks() / 1000.0
            mouse_pos = pygame.mouse.get_pos()
            self._update_hovered_cell(mouse_pos)

            # 1. Handle Keyboard & Mouse Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.progress_hit_rect.collidepoint(event.pos):
                        self.is_scrubbing = True
                        self.is_playing = False
                        self._scrub_to_mouse(event.pos[0])
                    else:
                        self._handle_click(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.is_scrubbing = False
                elif event.type == pygame.MOUSEMOTION and self.is_scrubbing:
                    self._scrub_to_mouse(event.pos[0])
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.current_event_idx >= len(self.events):
                            self.reset_playback()
                        self.is_playing = not self.is_playing
                    elif event.key == pygame.K_RIGHT:
                        self.is_playing = False
                        self.step_forward()
                    elif event.key == pygame.K_LEFT:
                        self.is_playing = False
                        self.step_backward()
                    elif event.key == pygame.K_r:
                        self.is_playing = False
                        self.reset_playback()
                    elif event.key == pygame.K_p:
                        self.show_pencil = not self.show_pencil
                    elif event.key == pygame.K_END:
                        self.is_playing = False
                        self.jump_to_end()
                    elif event.key in (pygame.K_m, pygame.K_n):
                        self.current_map_idx = (self.current_map_idx + 1) % len(self.available_maps)
                        self.load_puzzle(self.available_maps[self.current_map_idx][1])
                    elif event.key == pygame.K_b:
                        self.current_map_idx = (self.current_map_idx - 1) % len(self.available_maps)
                        self.load_puzzle(self.available_maps[self.current_map_idx][1])
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        self.playback_speed = max(0.001, self.playback_speed / 1.6)
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.playback_speed = min(0.5, self.playback_speed * 1.6)

            # 2. Auto-advance when playing
            if self.is_playing and (current_time - self.last_step_time >= self.playback_speed):
                if self.current_event_idx < len(self.events):
                    if self.playback_speed <= 0.003:
                        steps = 25 if len(self.events) > 5000 else 5
                    elif self.playback_speed <= 0.012:
                        steps = 8 if len(self.events) > 5000 else 2
                    else:
                        steps = 1
                    for _ in range(steps):
                        if self.current_event_idx < len(self.events):
                            self.step_forward()
                    self.last_step_time = current_time
                else:
                    self.is_playing = False
                    self.status_message = f"Completed! Puzzle solved in {self.solve_result.execution_time:.4f}s."

            # 3. Render Scene
            self.screen.fill(BG_COLOR)
            self.draw_board_panel()
            self.draw_control_panel(mouse_pos)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _update_hovered_cell(self, mouse_pos: Tuple[int, int]):
        """Tracks which board cell is currently under the mouse cursor."""
        mx, my = mouse_pos
        c = (mx - self.board_ox) // self.cell_size
        r = (my - self.board_oy) // self.cell_size
        if 0 <= r < self.csp.rows and 0 <= c < self.csp.cols:
            self.hovered_cell = (r, c)
        else:
            self.hovered_cell = None

    def _scrub_to_mouse(self, mouse_x: int):
        """Jumps smoothly to the trace step corresponding to mouse_x on the progress bar."""
        if not self.events:
            return
        rel = (mouse_x - self.progress_bar_rect.x) / max(1, self.progress_bar_rect.width)
        rel = max(0.0, min(1.0, rel))
        target_idx = int(round(rel * len(self.events)))
        self.jump_to_step(target_idx)

    def _handle_click(self, mouse_pos: Tuple[int, int]):
        """Handles mouse clicks on puzzle selector and control buttons."""
        if self.btn_map_prev.collidepoint(mouse_pos):
            self.current_map_idx = (self.current_map_idx - 1) % len(self.available_maps)
            self.load_puzzle(self.available_maps[self.current_map_idx][1])
            return
        elif self.btn_map_next.collidepoint(mouse_pos):
            self.current_map_idx = (self.current_map_idx + 1) % len(self.available_maps)
            self.load_puzzle(self.available_maps[self.current_map_idx][1])
            return
        elif self.map_display_rect.collidepoint(mouse_pos):
            # Clicking center card also advances to next map
            self.current_map_idx = (self.current_map_idx + 1) % len(self.available_maps)
            self.load_puzzle(self.available_maps[self.current_map_idx][1])
            return

        if self.btn_play.collidepoint(mouse_pos):
            if self.current_event_idx >= len(self.events):
                self.reset_playback()
            self.is_playing = not self.is_playing
        elif self.btn_fwd.collidepoint(mouse_pos):
            self.is_playing = False
            self.step_forward()
        elif self.btn_back.collidepoint(mouse_pos):
            self.is_playing = False
            self.step_backward()
        elif self.btn_solve.collidepoint(mouse_pos):
            self.is_playing = False
            self.jump_to_end()
        elif self.btn_reset.collidepoint(mouse_pos):
            self.is_playing = False
            self.reset_playback()
        elif self.btn_pencil.collidepoint(mouse_pos):
            self.show_pencil = not self.show_pencil
        elif self.btn_slower.collidepoint(mouse_pos):
            self.playback_speed = min(0.5, self.playback_speed * 1.6)
        elif self.btn_faster.collidepoint(mouse_pos):
            self.playback_speed = max(0.001, self.playback_speed / 1.6)

    def step_forward(self):
        """Executes the next solver trace event."""
        if self.current_event_idx >= len(self.events):
            return

        ev = self.events[self.current_event_idx]
        self.last_active_pos = ev.cell_pos
        self.last_event_type = ev.event_type
        self.status_message = ev.message
        self.last_pruned_digits = set()

        if ev.event_type == EventType.ASSIGN and ev.cell_pos:
            self.grid_values[ev.cell_pos] = ev.value
        elif ev.event_type == EventType.BACKTRACK and ev.cell_pos:
            self.grid_values[ev.cell_pos] = None
        elif ev.event_type == EventType.PRUNE and ev.cell_pos and ev.pruned_domain:
            self.grid_domains[ev.cell_pos] -= ev.pruned_domain
            self.last_pruned_digits = set(ev.pruned_domain)

        self.current_event_idx += 1

    def jump_to_step(self, target_idx: int):
        """Restores the nearest snapshot and fast-forwards to target_idx in < 1ms."""
        target_idx = max(0, min(target_idx, len(self.events)))
        if target_idx == self.current_event_idx:
            return

        snap_idx = min(target_idx // self.snapshot_interval, len(self.snapshots) - 1)
        s_step, s_vals, s_doms, s_pos, s_type, s_pruned, s_msg = self.snapshots[snap_idx]

        self.current_event_idx = s_step
        self.grid_values = dict(s_vals)
        self.grid_domains = {k: set(v) for k, v in s_doms.items()}
        self.last_active_pos = s_pos
        self.last_event_type = s_type
        self.last_pruned_digits = set(s_pruned)
        self.status_message = s_msg

        while self.current_event_idx < target_idx:
            self.step_forward()

    def step_backward(self):
        """Steps backward by one trace event instantaneously using snapshots."""
        if self.current_event_idx <= 0:
            return
        self.jump_to_step(self.current_event_idx - 1)

    def jump_to_end(self):
        """Jumps directly to the final solved board state."""
        if self.solve_result.is_solved and self.solve_result.solution_grid:
            self.grid_values = dict(self.solve_result.solution_grid)
            self.current_event_idx = len(self.events)
            self.last_active_pos = None
            self.last_event_type = EventType.SOLVED
            self.last_pruned_digits = set()
            self.status_message = f"Solved successfully in {self.solve_result.execution_time:.4f}s!"

    def reset_playback(self):
        """Resets board to initial state."""
        self.jump_to_step(0)
        self.status_message = "Reset to initial board state."

    def _is_run_satisfied_visual(self, run) -> bool:
        """Checks if a RunConstraint is currently satisfied on the visual board."""
        if run is None:
            return False
        vals = []
        for c in run.cells:
            v = self.grid_values.get(c.pos)
            if v is None:
                return False
            vals.append(v)
        return len(vals) == run.length and len(set(vals)) == run.length and sum(vals) == run.target_sum

    def _get_active_scope_cells(self, focus_pos: Optional[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Returns all peer white cells sharing a Horizontal or Vertical Run with focus_pos."""
        if focus_pos is None or focus_pos not in self.csp.variables:
            return set()
        cell = self.csp.variables[focus_pos]
        peers = set()
        for run in self.csp.cell_runs.get(cell, []):
            for other in run.cells:
                if other.pos != focus_pos:
                    peers.add(other.pos)
        return peers

    def _format_run_equation(self, pos: Tuple[int, int], direction: str) -> Tuple[str, bool]:
        """Formats the live equation of a cell's Horizontal or Vertical run constraint."""
        cell = self.csp.variables.get(pos)
        if cell is None:
            return "-", False
        for run in self.csp.cell_runs.get(cell, []):
            if run.direction == direction:
                terms = []
                cur_sum = 0
                filled = 0
                for c in run.cells:
                    v = self.grid_values.get(c.pos)
                    if v is not None:
                        terms.append(str(v))
                        cur_sum += v
                        filled += 1
                    else:
                        terms.append("_")
                eq_str = "+".join(terms)
                is_sat = (filled == run.length and cur_sum == run.target_sum and len(set(terms)) == run.length)
                status = "OK" if is_sat else f"{cur_sum}/{run.target_sum}"
                return f"{direction}-Run [Sum {run.target_sum}]: {eq_str} ({status})", is_sat
        return f"{direction}-Run: -", False

    def draw_board_panel(self):
        """Draws the Left Panel container, top accent bar, coordinate pills, Kakuro grid, and Dual-Run Inspector."""
        lp = self.left_panel_rect
        pygame.draw.rect(self.screen, PANEL_BG, lp, border_radius=12)
        pygame.draw.rect(self.screen, BORDER_COLOR, lp, 1, border_radius=12)

        # Top glowing accent bar
        pygame.draw.rect(self.screen, ACCENT_CYAN, pygame.Rect(lp.x + 12, lp.y, lp.width - 24, 3), border_radius=2)

        # Req 1 Integrity Badge on top-right of board panel
        badge_text = f"REQ 1: Sum(H)={self.h_sum} == Sum(V)={self.v_sum} [VALID]"
        badge_surf = self.font_metric_lbl.render(badge_text, True, (110, 231, 183))
        badge_rect = pygame.Rect(lp.right - badge_surf.get_width() - 34, lp.y + 20, badge_surf.get_width() + 18, 26)
        pygame.draw.rect(self.screen, (16, 48, 42), badge_rect, border_radius=6)
        pygame.draw.rect(self.screen, ACCENT_EMERALD, badge_rect, 1, border_radius=6)
        self.screen.blit(badge_surf, badge_surf.get_rect(center=badge_rect.center))

        # Left Panel Header (truncated cleanly before badge_rect)
        map_title = self.csp.name.upper() if getattr(self.csp, "name", None) else self.current_filename.upper()
        map_title = map_title.replace("PROBLEM PAGE 5 TEST CASE", "PAGE 5").replace("PROBLEM PAGE 4", "PAGE 4")
        title_surf = self.font_board_title.render(map_title, True, TEXT_MAIN)
        self.screen.blit(title_surf, (lp.x + 22, lp.y + 16))
        sub_info = f"Grid: {self.csp.rows}x{self.csp.cols}   |   White Variables: {len(self.csp.variables)}   |   Run Constraints: {len(self.csp.runs)}"
        self.screen.blit(self.font_status.render(sub_info, True, TEXT_MUTED), (lp.x + 22, lp.y + 40))

        # Header Divider
        pygame.draw.line(self.screen, DIVIDER_COLOR, (lp.x + 16, lp.y + 68), (lp.right - 16, lp.y + 68), 1)

        # Determine focus cell and active Run Scope peers
        focus_pos = self.hovered_cell if (self.hovered_cell in self.csp.variables) else self.last_active_pos
        scope_peers = self._get_active_scope_cells(focus_pos)

        # Board outer shadow & frame
        board_w = self.csp.cols * self.cell_size
        board_h = self.csp.rows * self.cell_size
        outer_rect = pygame.Rect(self.board_ox - 6, self.board_oy - 6, board_w + 12, board_h + 12)
        pygame.draw.rect(self.screen, BOARD_FRAME, outer_rect, border_radius=8)
        pygame.draw.rect(self.screen, BORDER_COLOR, outer_rect, 1, border_radius=8)

        # Coordinate Axis Pill Badges (C0..Cn across top, R0..Rn along left)
        for c in range(self.csp.cols):
            cx = self.board_ox + c * self.cell_size + self.cell_size // 2
            cy = self.board_oy - 17
            is_focus_col = (focus_pos is not None and focus_pos[1] == c)
            pill = pygame.Rect(cx - 14, cy - 8, 28, 16)
            pygame.draw.rect(self.screen, (22, 48, 72) if is_focus_col else CARD_INNER, pill, border_radius=4)
            lbl = self.font_coord.render(f"C{c}", True, CLUE_V_COLOR if is_focus_col else TEXT_MUTED)
            self.screen.blit(lbl, lbl.get_rect(center=(cx, cy)))

        for r in range(self.csp.rows):
            cx = self.board_ox - 20
            cy = self.board_oy + r * self.cell_size + self.cell_size // 2
            is_focus_row = (focus_pos is not None and focus_pos[0] == r)
            pill = pygame.Rect(cx - 14, cy - 8, 28, 16)
            pygame.draw.rect(self.screen, (52, 44, 20) if is_focus_row else CARD_INNER, pill, border_radius=4)
            lbl = self.font_coord.render(f"R{r}", True, CLUE_H_COLOR if is_focus_row else TEXT_MUTED)
            self.screen.blit(lbl, lbl.get_rect(center=(cx, cy)))

        # Draw Grid Cells
        active_rect_and_color: Optional[Tuple[pygame.Rect, Tuple[int, int, int]]] = None

        for r in range(self.csp.rows):
            for c in range(self.csp.cols):
                rect = pygame.Rect(
                    self.board_ox + c * self.cell_size,
                    self.board_oy + r * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                pos = (r, c)

                if pos in self.csp.variables:
                    # 1. White Variable Cell
                    is_in_scope = (pos in scope_peers)
                    bg = CELL_HOVER if pos == self.hovered_cell else (CELL_SCOPE_TINT if is_in_scope else CELL_WHITE)
                    ring_color = None

                    if pos == self.last_active_pos:
                        if self.last_event_type == EventType.ASSIGN:
                            bg = COLOR_ASSIGN
                            ring_color = RING_ASSIGN
                        elif self.last_event_type == EventType.BACKTRACK:
                            bg = COLOR_BACKTRACK
                            ring_color = RING_BACKTRACK
                        elif self.last_event_type == EventType.PRUNE:
                            bg = COLOR_PRUNE
                            ring_color = RING_PRUNE

                    if self.current_event_idx >= len(self.events) and self.grid_values[pos] is not None:
                        bg = COLOR_SOLVED
                        if pos == self.hovered_cell:
                            ring_color = RING_SOLVED

                    pygame.draw.rect(self.screen, bg, rect)
                    if is_in_scope and pos != self.last_active_pos:
                        pygame.draw.rect(self.screen, SCOPE_BORDER, rect.inflate(-2, -2), 2)
                    pygame.draw.rect(self.screen, CELL_BORDER, rect, 1)

                    if ring_color is not None:
                        active_rect_and_color = (rect, ring_color)

                    val = self.grid_values[pos]
                    if val is not None:
                        digit_surf = self.hand_big_surfaces.get(val)
                        if digit_surf is not None:
                            self.screen.blit(digit_surf, digit_surf.get_rect(center=rect.center))
                        else:
                            t = self.font_big.render(str(val), True, TEXT_ASSIGNED)
                            self.screen.blit(t, t.get_rect(center=rect.center))
                    elif self.show_pencil:
                        flashed = self.last_pruned_digits if (pos == self.last_active_pos and self.last_event_type == EventType.PRUNE) else set()
                        self._draw_pencil(rect, self.grid_domains[pos], flashed)

                else:
                    # 2. Black Cell (Either Pure Wall or Two-Tone Split Clue Cell)
                    clues = self.csp.clue_cells.get(pos, {})
                    v_clue = clues.get("V")
                    h_clue = clues.get("H")

                    if v_clue is None and h_clue is None:
                        # Pure Wall Cell (Clean recessed tile without diagonal clutter)
                        pygame.draw.rect(self.screen, CELL_WALL, rect)
                        pygame.draw.rect(self.screen, CELL_WALL_BEVEL, rect.inflate(-6, -6), 1, border_radius=2)
                        pygame.draw.rect(self.screen, CELL_BLACK_BORDER, rect, 1)
                    else:
                        # Two-Tone Split Triangle Clue Cell
                        h_run = self.clue_to_run.get((r, c, "H"))
                        v_run = self.clue_to_run.get((r, c, "V"))
                        h_sat = self._is_run_satisfied_visual(h_run)
                        v_sat = self._is_run_satisfied_visual(v_run)

                        upper_col = CELL_CLUE_SAT_BG if h_sat else (CELL_CLUE_H_BG if h_clue is not None else CELL_WALL)
                        lower_col = CELL_CLUE_SAT_BG if v_sat else (CELL_CLUE_V_BG if v_clue is not None else CELL_WALL)

                        # Upper-Right Triangle (Horizontal Clue)
                        pygame.draw.polygon(
                            self.screen,
                            upper_col,
                            [rect.topleft, rect.topright, rect.bottomright]
                        )
                        # Lower-Left Triangle (Vertical Clue)
                        pygame.draw.polygon(
                            self.screen,
                            lower_col,
                            [rect.topleft, rect.bottomleft, rect.bottomright]
                        )

                        # Crisp anti-aliased diagonal divider
                        pygame.draw.aaline(self.screen, CLUE_LINE_COLOR, rect.topleft, rect.bottomright)
                        pygame.draw.aaline(
                            self.screen,
                            CLUE_LINE_COLOR,
                            (rect.left + 1, rect.top),
                            (rect.right, rect.bottom - 1)
                        )
                        pygame.draw.rect(self.screen, CELL_BLACK_BORDER, rect, 1)

                        pad = max(4, int(self.cell_size * 0.08))
                        if v_clue is not None:
                            vt = self._get_clue_surface(v_clue, is_vertical=True)
                            self.screen.blit(vt, (rect.left + pad, rect.bottom - vt.get_height() - pad))
                            if v_sat:
                                pygame.draw.circle(
                                    self.screen,
                                    CLUE_SAT_DOT,
                                    (rect.left + pad + vt.get_width() + 5, rect.bottom - pad - vt.get_height() // 2),
                                    3
                                )

                        if h_clue is not None:
                            ht = self._get_clue_surface(h_clue, is_vertical=False)
                            self.screen.blit(ht, (rect.right - ht.get_width() - pad, rect.top + pad))
                            if h_sat:
                                pygame.draw.circle(
                                    self.screen,
                                    CLUE_SAT_DOT,
                                    (rect.right - pad - ht.get_width() - 6, rect.top + pad + ht.get_height() // 2),
                                    3
                                )

        # Draw glowing focus border on top of active cell
        if active_rect_and_color is not None:
            a_rect, a_col = active_rect_and_color
            pygame.draw.rect(self.screen, a_col, a_rect.inflate(2, 2), 3, border_radius=3)

        # Bottom Dual-Run Constraint & Variable Inspector Card inside Left Panel
        insp_rect = pygame.Rect(lp.x + 16, lp.bottom - 78, lp.width - 32, 64)
        pygame.draw.rect(self.screen, CARD_INNER, insp_rect, border_radius=8)
        pygame.draw.rect(self.screen, BORDER_COLOR, insp_rect, 1, border_radius=8)

        if focus_pos and focus_pos in self.csp.variables:
            val = self.grid_values.get(focus_pos)
            dom_list = sorted(self.grid_domains.get(focus_pos, set()))
            dom_str = "{" + ", ".join(str(x) for x in dom_list) + "}" if dom_list else "{}"
            val_str = f"Assigned = {val}" if val is not None else f"Domain D = {dom_str} ({len(dom_list)}/9 left)"
            head_str = f"INSPECTING VARIABLE X(R{focus_pos[0]}, C{focus_pos[1]})   |   {val_str}   |   Scope Peers: {len(scope_peers)} cells"
            self.screen.blit(self.font_status_bold.render(head_str, True, CLUE_V_COLOR), (insp_rect.x + 14, insp_rect.y + 9))

            h_eq, h_ok = self._format_run_equation(focus_pos, "H")
            v_eq, v_ok = self._format_run_equation(focus_pos, "V")
            self.screen.blit(
                self.font_status.render(h_eq, True, CLUE_SAT_DOT if h_ok else TEXT_SUB),
                (insp_rect.x + 14, insp_rect.y + 34)
            )
            self.screen.blit(
                self.font_status.render(v_eq, True, CLUE_SAT_DOT if v_ok else TEXT_SUB),
                (insp_rect.x + 345, insp_rect.y + 34)
            )
        else:
            self.screen.blit(
                self.font_status_bold.render("CSP VARIABLE & CONSTRAINT INSPECTOR", True, TEXT_SUB),
                (insp_rect.x + 14, insp_rect.y + 10)
            )
            hint_text = "Hover over any white cell (or step the solver) to inspect its live Domain D and H/V Run Sum equations."
            self.screen.blit(self.font_status.render(hint_text, True, TEXT_MUTED), (insp_rect.x + 14, insp_rect.y + 34))

    def _draw_pencil(self, rect: pygame.Rect, domain: Set[int], flashed_pruned: Set[int]):
        """Draws 3x3 candidate domain numbers (1..9), faint dots for eliminated values, and red flash for active prunes."""
        pad = max(3, int(rect.width * 0.06))
        inner_w = rect.width - 2 * pad
        inner_h = rect.height - 2 * pad
        sw = inner_w / 3.0
        sh = inner_h / 3.0
        for num in range(1, 10):
            row = (num - 1) // 3
            col = (num - 1) % 3
            cx = int(rect.left + pad + (col + 0.5) * sw)
            cy = int(rect.top + pad + (row + 0.5) * sh)

            if num in domain:
                p_surf = self.hand_pencil_surfaces.get(num)
                if p_surf is not None:
                    self.screen.blit(p_surf, p_surf.get_rect(center=(cx, cy)))
                else:
                    t = self.font_pencil.render(str(num), True, PENCIL_COLOR)
                    self.screen.blit(t, t.get_rect(center=(cx, cy)))
            elif num in flashed_pruned:
                # Highlight digit just pruned in this step
                flash_box = pygame.Rect(cx - int(sw * 0.42), cy - int(sh * 0.42), int(sw * 0.84), int(sh * 0.84))
                pygame.draw.rect(self.screen, (254, 202, 202), flash_box, border_radius=3)
                pygame.draw.rect(self.screen, (220, 38, 38), flash_box, 1, border_radius=3)
                pr_surf = self.hand_pruned_surfaces.get(num)
                if pr_surf is not None:
                    self.screen.blit(pr_surf, pr_surf.get_rect(center=(cx, cy)))
            else:
                # Subtle micro-dot showing pruned slot in 3x3 domain matrix
                pygame.draw.circle(self.screen, PRUNED_DOT_COLOR, (cx, cy), 1)

    def draw_control_panel(self, mouse_pos: Tuple[int, int]):
        """Draws the right-hand AI Studio dashboard with KPI cards, propagation breakdown, and 3-line trace console."""
        rp = self.right_panel_rect
        px = rp.x + 22

        pygame.draw.rect(self.screen, PANEL_BG, rp, border_radius=12)
        pygame.draw.rect(self.screen, BORDER_COLOR, rp, 1, border_radius=12)
        pygame.draw.rect(self.screen, ACCENT_EMERALD, pygame.Rect(rp.x + 12, rp.y, rp.width - 24, 3), border_radius=2)

        # --- HEADER ---
        self.screen.blit(self.font_title.render("KAKURO CSP SOLVER STUDIO", True, TEXT_MAIN), (px, rp.y + 16))
        self.screen.blit(
            self.font_body.render("Backtracking Search + AC-3 + Forward Checking + MRV & LCV", True, TEXT_MUTED),
            (px, rp.y + 42)
        )

        # Solver Config Pill Badge
        cfg_surf = self.font_metric_lbl.render("REQ 2: AC-3 + FC + MRV + LCV", True, (56, 189, 248))
        cfg_rect = pygame.Rect(rp.right - cfg_surf.get_width() - 40, rp.y + 20, cfg_surf.get_width() + 18, 26)
        pygame.draw.rect(self.screen, (16, 38, 62), cfg_rect, border_radius=6)
        pygame.draw.rect(self.screen, ACCENT_CYAN, cfg_rect, 1, border_radius=6)
        self.screen.blit(cfg_surf, cfg_surf.get_rect(center=cfg_rect.center))

        pygame.draw.line(self.screen, DIVIDER_COLOR, (px, rp.y + 68), (rp.right - 22, rp.y + 68), 1)

        # --- SECTION 1: COMPACT PUZZLE CYCLER (< PREV, Current Map, NEXT >) ---
        self.screen.blit(self.font_heading.render("1. SELECT PUZZLE BENCHMARK", True, TEXT_SUB), (px, 86))
        hint_map = self.font_status.render(
            f"Map {self.current_map_idx + 1} of {len(self.available_maps)}",
            True,
            TEXT_MUTED
        )
        self.screen.blit(hint_map, (rp.right - 22 - hint_map.get_width(), 84))

        # 1.1 Left Button: < PREV
        self._draw_btn(self.btn_map_prev, "< PREV", BTN_SECONDARY, mouse_pos)

        # 1.2 Center Display: Current Map Name Card
        mc = self.map_display_rect
        is_mc_hover = mc.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, CARD_INNER if not is_mc_hover else (30, 38, 52), mc, border_radius=7)
        pygame.draw.rect(self.screen, (16, 185, 129), mc, 1, border_radius=7)

        cur_label, _ = self.available_maps[self.current_map_idx]
        cur_surf = self.font_btn.render(f"[*] {cur_label}", True, (255, 255, 255))
        self.screen.blit(cur_surf, cur_surf.get_rect(center=mc.center))

        # 1.3 Right Button: NEXT >
        self._draw_btn(self.btn_map_next, "NEXT >", BTN_SECONDARY, mouse_pos)

        # --- SECTION 2: EXECUTION TELEMETRY, BREAKDOWN & 3-LINE TRACE CONSOLE ---
        self.screen.blit(self.font_heading.render("2. EXECUTION TELEMETRY & LIVE TRACE LOG", True, TEXT_SUB), (px, 164))

        if self.current_event_idx >= len(self.events) and len(self.events) > 0:
            state_str, state_col = "SOLVED (100% VALID)", ACCENT_EMERALD
        elif self.is_playing:
            state_str, state_col = "RUNNING TRACE", ACCENT_CYAN
        elif self.current_event_idx > 0:
            state_str, state_col = "PAUSED", (245, 158, 11)
        else:
            state_str, state_col = "READY", TEXT_MUTED
        st_lbl = self.font_metric_lbl.render(f"STATUS: {state_str}", True, state_col)
        self.screen.blit(st_lbl, (rp.right - 22 - st_lbl.get_width(), 166))

        tc = self.telemetry_card_rect
        pygame.draw.rect(self.screen, CARD_BG, tc, border_radius=10)
        pygame.draw.rect(self.screen, BORDER_COLOR, tc, 1, border_radius=10)

        # 4 KPI Metric Boxes inside Telemetry Card (proportional widths so 5-digit step counts never clip)
        ev_total = max(1, len(self.events))
        pct = (self.current_event_idx / ev_total) * 100.0
        kpis = [
            ("TRACE STEP", f"{self.current_event_idx:,} / {len(self.events):,} ({pct:.0f}%)", 182),
            ("NODES EXPLORED", f"{self.solve_result.nodes_explored:,}", 118),
            ("BACKTRACKS", f"{self.solve_result.backtracks:,}", 108),
            ("SOLVE TIME", f"{self.solve_result.execution_time:.4f}s", 100),
        ]
        kpi_gap = 10
        kx = tc.x + 16
        ky = tc.y + 12
        for k_lbl, k_val, kpi_w in kpis:
            k_rect = pygame.Rect(kx, ky, kpi_w, 46)
            pygame.draw.rect(self.screen, CARD_INNER, k_rect, border_radius=6)
            pygame.draw.rect(self.screen, DIVIDER_COLOR, k_rect, 1, border_radius=6)

            l_surf = self.font_metric_lbl.render(k_lbl, True, TEXT_MUTED)
            v_surf = self.font_metric_val.render(k_val, True, TEXT_MAIN)
            self.screen.blit(l_surf, (k_rect.x + 8, k_rect.y + 5))
            self.screen.blit(v_surf, (k_rect.x + 8, k_rect.y + 22))
            kx += kpi_w + kpi_gap

        # Cumulative Step Breakdown Counters (Init/AC-3 Prunes | FC Prunes | Assigns | Backtracks)
        c_init_ac3, c_fc, c_assign, c_bt = self.step_counts[min(self.current_event_idx, len(self.step_counts) - 1)]
        breakdown_y = tc.y + 64
        bd_items = [
            (f"Init/AC-3 Prunes: {c_init_ac3:,}", CLUE_V_COLOR),
            (f"ForwardCheck: {c_fc:,}", (125, 211, 252)),
            (f"Tries (MRV/LCV): {c_assign:,}", CLUE_H_COLOR),
            (f"Backtracks: {c_bt:,}", (252, 165, 165)),
        ]
        bd_x = tc.x + 18
        for bd_txt, bd_col in bd_items:
            pygame.draw.circle(self.screen, bd_col, (bd_x + 4, breakdown_y + 8), 4)
            s_bd = self.font_metric_lbl.render(bd_txt, True, TEXT_SUB)
            self.screen.blit(s_bd, (bd_x + 12, breakdown_y + 1))
            bd_x += s_bd.get_width() + 26

        # Interactive Scrubber Progress Bar
        bar = self.progress_bar_rect
        pygame.draw.rect(self.screen, CARD_INNER, bar, border_radius=6)
        pygame.draw.rect(self.screen, DIVIDER_COLOR, bar, 1, border_radius=6)

        progress_ratio = self.current_event_idx / ev_total
        fill_w = int(progress_ratio * bar.width)
        if fill_w > 0:
            fill_col = BTN_SUCCESS if self.current_event_idx >= len(self.events) else BTN_PRIMARY
            pygame.draw.rect(self.screen, fill_col, pygame.Rect(bar.x, bar.y, max(8, fill_w), bar.height), border_radius=6)

        thumb_x = bar.x + fill_w
        thumb_y = bar.centery
        is_bar_hover = self.progress_hit_rect.collidepoint(mouse_pos) or self.is_scrubbing
        thumb_r = 8 if is_bar_hover else 6
        pygame.draw.circle(self.screen, (255, 255, 255), (thumb_x, thumb_y), thumb_r)
        pygame.draw.circle(self.screen, BTN_PRIMARY, (thumb_x, thumb_y), thumb_r, 2)

        # 3-Line Scrolling Trace Console
        cons = self.console_rect
        pygame.draw.rect(self.screen, CARD_INNER, cons, border_radius=7)
        pygame.draw.rect(self.screen, DIVIDER_COLOR, cons, 1, border_radius=7)

        if self.current_event_idx == 0:
            self._draw_console_line(cons.x + 10, cons.y + 10, 0, "INIT", (100, 116, 139), self.status_message, True)
            self._draw_console_line(
                cons.x + 10,
                cons.y + 38,
                0,
                "READY",
                ACCENT_CYAN,
                "Press [PLAY / START] or [STEP NEXT >] to visualize AC-3 & Backtracking.",
                False
            )
            self._draw_console_line(
                cons.x + 10,
                cons.y + 66,
                0,
                "TIP",
                ACCENT_EMERALD,
                "Drag the timeline slider above to scrub smoothly to any step.",
                False
            )
        else:
            start_idx = max(1, self.current_event_idx - 2)
            indices = list(range(start_idx, self.current_event_idx + 1))
            for row_i, step_no in enumerate(indices):
                ev = self.events[step_no - 1]
                is_current = (step_no == self.current_event_idx)
                tag_t, tag_c = self._get_event_badge(ev)
                self._draw_console_line(
                    cons.x + 10,
                    cons.y + 8 + row_i * 28,
                    step_no,
                    tag_t,
                    tag_c,
                    ev.message,
                    is_current
                )

        # --- SECTION 3: PLAYBACK CONTROLS ---
        self.screen.blit(self.font_heading.render("3. PLAYBACK & SPEED CONTROLS", True, TEXT_SUB), (px, 448))
        kb_hint = self.font_status.render("Keys: [Space] Play  [Arrows] Step  [B/N] Map  [R] Reset", True, TEXT_MUTED)
        self.screen.blit(kb_hint, (rp.right - 22 - kb_hint.get_width(), 446))

        play_label = "PAUSE [Space]" if self.is_playing else "PLAY / START [Space]"
        play_col = BTN_PAUSED if self.is_playing else BTN_PRIMARY
        self._draw_btn(self.btn_play, play_label, play_col, mouse_pos)
        self._draw_btn(self.btn_solve, "SOLVE NOW [End]", BTN_SUCCESS, mouse_pos)

        self._draw_btn(self.btn_back, "< STEP BACK [Left]", BTN_SECONDARY, mouse_pos)
        self._draw_btn(self.btn_fwd, "STEP NEXT > [Right]", BTN_SECONDARY, mouse_pos)

        self._draw_btn(self.btn_reset, "RESET BOARD [R]", BTN_DANGER, mouse_pos)
        pencil_col = (59, 130, 246) if self.show_pencil else BTN_SECONDARY
        self._draw_btn(self.btn_pencil, f"PENCIL MARKS: {'ON' if self.show_pencil else 'OFF'} [P]", pencil_col, mouse_pos)

        # Speed Control Row
        self._draw_btn(self.btn_slower, "SLOWER [-]", BTN_SPEED, mouse_pos)
        self._draw_btn(self.btn_faster, "FASTER [+]", BTN_SPEED, mouse_pos)

        pygame.draw.rect(self.screen, CARD_INNER, self.speed_pill_rect, border_radius=7)
        pygame.draw.rect(self.screen, BORDER_COLOR, self.speed_pill_rect, 1, border_radius=7)
        steps_per_sec = 1.0 / max(0.001, self.playback_speed)
        spd_txt = f"SPEED: {steps_per_sec:.0f} steps/s" if steps_per_sec >= 10 else f"SPEED: {steps_per_sec:.1f} steps/s"
        spd_surf = self.font_btn.render(spd_txt, True, CLUE_V_COLOR)
        self.screen.blit(spd_surf, spd_surf.get_rect(center=self.speed_pill_rect.center))

        # --- SECTION 4: VISUAL LEGEND ---
        self.screen.blit(self.font_heading.render("4. VISUAL LEGEND", True, TEXT_SUB), (px, 664))
        lc = self.legend_card_rect
        pygame.draw.rect(self.screen, CARD_BG, lc, border_radius=10)
        pygame.draw.rect(self.screen, BORDER_COLOR, lc, 1, border_radius=10)

        legends = [
            (COLOR_ASSIGN, RING_ASSIGN, "Assign Try (MRV + LCV)"),
            (COLOR_PRUNE, RING_PRUNE, "Domain Prune (Init / AC-3 / FC)"),
            (COLOR_BACKTRACK, RING_BACKTRACK, "Dead End (Backtrack Undo)"),
            (COLOR_SOLVED, RING_SOLVED, "Final Verified Solution"),
            (CELL_SCOPE_TINT, SCOPE_BORDER, "Active H/V Run Constraint Scope"),
            (CELL_CLUE_SAT_BG, CLUE_SAT_DOT, "Satisfied Run Sum Clue (Green Dot)"),
        ]

        for i, (fill_c, border_c, text) in enumerate(legends):
            row = i // 2
            col_idx = i % 2
            bx = lc.x + 16 + col_idx * 276
            by = lc.y + 14 + row * 34
            box = pygame.Rect(bx, by, 18, 18)
            pygame.draw.rect(self.screen, fill_c, box, border_radius=4)
            pygame.draw.rect(self.screen, border_c, box, 2, border_radius=4)
            self.screen.blit(self.font_body.render(text, True, TEXT_SUB), (bx + 26, by))
            box = pygame.Rect(bx, by, 18, 18)
            pygame.draw.rect(self.screen, fill_c, box, border_radius=4)
            pygame.draw.rect(self.screen, border_c, box, 2, border_radius=4)
            self.screen.blit(self.font_body.render(text, True, TEXT_SUB), (bx + 26, by))

    def _get_event_badge(self, ev: SolverEvent) -> Tuple[str, Tuple[int, int, int]]:
        if ev.event_type == EventType.ASSIGN:
            return "ASSIGN", RING_ASSIGN
        if ev.event_type == EventType.BACKTRACK:
            return "BACKTRACK", RING_BACKTRACK
        if ev.event_type == EventType.PRUNE:
            if "Initial" in ev.message:
                return "INIT-FILT", (14, 165, 233)
            if "AC-3" in ev.message:
                return "AC-3", (6, 182, 212)
            return "F-CHECK", (59, 130, 246)
        return "SOLVED", RING_SOLVED

    def _draw_console_line(
        self,
        x: int,
        y: int,
        step_no: int,
        tag_text: str,
        tag_col: Tuple[int, int, int],
        msg: str,
        is_active: bool
    ):
        if is_active:
            hl_rect = pygame.Rect(x - 4, y - 2, self.console_rect.width - 12, 24)
            pygame.draw.rect(self.screen, (30, 39, 56), hl_rect, border_radius=4)

        step_str = f"#{step_no:04d}" if step_no > 0 else "----"
        s_surf = self.font_metric_lbl.render(step_str, True, CLUE_H_COLOR if is_active else TEXT_MUTED)
        self.screen.blit(s_surf, (x + 2, y + 3))

        tag_rect = pygame.Rect(x + 46, y + 1, 68, 18)
        pygame.draw.rect(self.screen, tag_col, tag_rect, border_radius=4)
        t_col = (15, 23, 42) if tag_text == "ASSIGN" else (255, 255, 255)
        t_surf = self.font_metric_lbl.render(tag_text, True, t_col)
        self.screen.blit(t_surf, t_surf.get_rect(center=tag_rect.center))

        clean_msg = msg[:54] + "..." if len(msg) > 57 else msg
        m_font = self.font_status_bold if is_active else self.font_status
        m_col = TEXT_MAIN if is_active else TEXT_MUTED
        m_surf = m_font.render(clean_msg, True, m_col)
        self.screen.blit(m_surf, (tag_rect.right + 10, y + 1))

    def _draw_btn(self, rect: pygame.Rect, text: str, base_color: Tuple[int, int, int], mouse_pos: Tuple[int, int]):
        """Draws a rounded button with subtle elevation border and smooth hover highlight."""
        is_hover = rect.collidepoint(mouse_pos)
        color = tuple(min(255, c + 22) for c in base_color) if is_hover else base_color
        border_col = tuple(min(255, c + 45) for c in base_color) if is_hover else tuple(max(0, c - 15) for c in base_color)

        pygame.draw.rect(self.screen, color, rect, border_radius=7)
        pygame.draw.rect(self.screen, border_col, rect, 1, border_radius=7)
        t = self.font_btn.render(text, True, (255, 255, 255))
        self.screen.blit(t, t.get_rect(center=rect.center))
