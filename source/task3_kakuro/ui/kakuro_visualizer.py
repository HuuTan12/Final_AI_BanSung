"""
Module: kakuro_visualizer.py
Description: Interactive Graphical User Interface (GUI) for Kakuro CSP Solver (Modern Dashboard Theme).
Implements Requirement 3 (1.0 pt) of Task 3:
1. Direct in-app Puzzle Selector (5x5 Sample, 9x9 Complex).
2. Domain Visualization: Displays 3x3 pencil grid (1..9) inside unassigned white cells using SVG digit assets.
3. Constraint Propagation Visualization: Highlights domain pruning steps (Initial Filtering, AC-3, Forward Checking).
4. Backtracking Search Visualization: Try Assignment (Yellow), Backtrack (Coral Red), Solved (Emerald Green).
5. Playback Controls: Play/Pause, Step Next/Back, Instant Solve, Reset, Pencil Toggle, and Speed Control.
"""

import sys
import os
import io
import re
import pygame
from typing import List, Dict, Set, Optional, Tuple

from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.backtracking_solver import KakuroBacktrackingSolver
from task3_kakuro.solver.tracer import SolverTracer, SolverEvent, EventType

# --- MODERN DARK ELEGANT THEME PALETTE (BACKGROUND PRESERVED) ---
BG_COLOR = (24, 28, 36)               # Dark tech slate background
PANEL_BG = (32, 38, 50)               # Control panel background
CARD_BG = (42, 50, 66)                # Content card background
BORDER_COLOR = (55, 65, 85)           # Divider border

# Kakuro Board Colors
CELL_BLACK = (20, 24, 32)             # Black Clue Cell
CELL_WHITE = (248, 250, 252)          # White Variable Cell
CELL_BORDER = (160, 175, 195)         # White Cell Border
CLUE_LINE_COLOR = (70, 85, 110)       # Diagonal Clue Divider
CLUE_V_COLOR = (56, 189, 248)         # Vertical Clue: Neon Cyan
CLUE_H_COLOR = (250, 204, 21)         # Horizontal Clue: Neon Gold

# Search State Highlight Colors
COLOR_ASSIGN = (254, 240, 138)        # Try Assignment: Soft Yellow
COLOR_PRUNE = (186, 230, 253)         # Domain Pruning: Light Sky Blue
COLOR_BACKTRACK = (254, 202, 202)     # Backtrack: Coral Pink
COLOR_SOLVED = (187, 247, 208)        # Solved Cell: Emerald Mint

TEXT_MAIN = (240, 245, 255)           # Primary Text
TEXT_MUTED = (148, 163, 184)          # Secondary Muted Text
TEXT_ASSIGNED = (15, 23, 42)          # Assigned Big Digit Color
PENCIL_COLOR = (100, 116, 139)        # Remaining Domain Pencil Digit Color

# Hex equivalents for SVG asset tinting
HEX_ASSIGNED = "#0F172A"
HEX_PENCIL = "#64748B"
HEX_CLUE_V = "#38BDF8"
HEX_CLUE_H = "#FACC15"

# Button Colors
BTN_PRIMARY = (14, 165, 233)          # Sky Blue
BTN_PRIMARY_HOVER = (56, 189, 248)
BTN_SECONDARY = (51, 65, 85)          # Charcoal Slate
BTN_SECONDARY_HOVER = (71, 85, 105)
BTN_ACTIVE_MAP = (16, 185, 129)       # Active Map Emerald


class KakuroVisualizer:
    """
    Interactive Graphical Visualizer for Kakuro CSP with SVG Digit Asset Rendering.
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

        # Available puzzles
        self.available_maps = [
            ("5x5 Sample", "sample_5x5.json"),
            ("9x9 Complex", "complex_9x9.json")
        ]
        self.current_map_idx = 0

        # Main window dimensions
        self.screen_width = 1260
        self.screen_height = 760
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Kakuro CSP Visualizer - Introduction to AI (TDTU)")

        # Cached SVG digit surfaces
        self.hand_big_surfaces: Dict[int, pygame.Surface] = {}
        self.hand_pencil_surfaces: Dict[int, pygame.Surface] = {}
        self.clue_v_surfaces: Dict[int, pygame.Surface] = {}
        self.clue_h_surfaces: Dict[int, pygame.Surface] = {}
        self.clue_number_cache: Dict[Tuple[int, bool], pygame.Surface] = {}

        # Initialize UI fonts
        self._init_fonts()

        # Load initial puzzle
        self.load_puzzle(self.available_maps[self.current_map_idx][1])

    def _init_fonts(self):
        font_name = "Segoe UI" if "Segoe UI" in pygame.font.get_fonts() else "Arial"
        self.font_title = pygame.font.SysFont(font_name, 20, bold=True)
        self.font_heading = pygame.font.SysFont(font_name, 16, bold=True)
        self.font_body = pygame.font.SysFont(font_name, 13)
        self.font_btn = pygame.font.SysFont(font_name, 13, bold=True)
        self.font_status = pygame.font.SysFont(font_name, 12)

    def _load_svg_surface(self, svg_path: str, target_h: int, hex_color: str) -> Optional[pygame.Surface]:
        """
        Parses an SVG digit asset file, injects the desired fill color and scaled dimensions,
        and rasterizes it into a crisp anti-aliased Pygame Surface.
        """
        if not os.path.isfile(svg_path):
            return None
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            # Replace CSS var() or existing fill color with target hex color
            svg_content = re.sub(r'fill="[^"]*"', f'fill="{hex_color}"', svg_content)

            # Parse viewBox or width/height to preserve exact glyph aspect ratio
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
        """
        Loads and scales all number SVG assets from source/task3_kakuro/assets/svg:
        - digits-hand/hand-1.svg .. hand-9.svg for assigned numbers and 3x3 pencil domains.
        - digits-clue/clue-0.svg .. clue-9.svg for vertical and horizontal sum clues.
        """
        self.hand_big_surfaces.clear()
        self.hand_pencil_surfaces.clear()
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

        for d in range(0, 10):
            clue_path = os.path.join(clue_dir, f"clue-{d}.svg")
            v_surf = self._load_svg_surface(clue_path, clue_h, HEX_CLUE_V)
            if v_surf is not None:
                self.clue_v_surfaces[d] = v_surf

            h_surf = self._load_svg_surface(clue_path, clue_h, HEX_CLUE_H)
            if h_surf is not None:
                self.clue_h_surfaces[d] = h_surf

    def _get_clue_surface(self, clue_val: int, is_vertical: bool) -> pygame.Surface:
        """
        Composes multi-digit clue numbers (e.g. 12, 21, 45) from individual clue-0..9 SVG glyphs.
        """
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

    def load_puzzle(self, filename: str):
        """Loads puzzle JSON, runs solver with tracer, and configures board geometry & SVG assets."""
        filepath = os.path.join(self.puzzle_dir, filename)
        self.csp = KakuroCSP()
        self.csp.load_from_json(filepath)

        # Run solver to record trace events
        self.tracer = SolverTracer()
        self.solver = KakuroBacktrackingSolver(use_ac3=True, use_mrv=True, use_lcv=True, tracer=self.tracer)
        self.solve_result = self.solver.solve(self.csp)
        self.events: List[SolverEvent] = self.tracer.events

        # Reset playback state
        self.current_event_idx = 0
        self.is_playing = False
        self.playback_speed = 0.05
        self.last_step_time = 0.0
        self.show_pencil = True

        # Board visual state
        self.grid_values: Dict[Tuple[int, int], Optional[int]] = {pos: None for pos in self.csp.variables}
        self.grid_domains: Dict[Tuple[int, int], Set[int]] = {pos: set(range(1, 10)) for pos in self.csp.variables}
        self.last_active_pos: Optional[Tuple[int, int]] = None
        self.last_event_type: Optional[EventType] = None
        self.status_message = f"Loaded {filename}: {len(self.csp.variables)} white cells, {len(self.events)} trace events."

        # Auto-scale cell size to fit board area
        max_board_w = 680
        max_board_h = 680
        self.cell_size = min(max_board_w // self.csp.cols, max_board_h // self.csp.rows)
        self.cell_size = max(48, min(self.cell_size, 76))

        self.board_ox = 35
        self.board_oy = (self.screen_height - (self.csp.rows * self.cell_size)) // 2

        # Fallback fonts on board
        font_name = "Segoe UI" if "Segoe UI" in pygame.font.get_fonts() else "Arial"
        self.font_big = pygame.font.SysFont(font_name, int(self.cell_size * 0.48), bold=True)
        self.font_clue = pygame.font.SysFont(font_name, int(self.cell_size * 0.23), bold=True)
        self.font_pencil = pygame.font.SysFont(font_name, int(self.cell_size * 0.18), bold=True)

        # Parse & scale SVG digit assets for current cell_size
        self._load_digit_assets()

        # Right control panel button layout
        px = 750
        self.btn_maps = [
            pygame.Rect(px + i * 270, 118, 255, 38)
            for i in range(len(self.available_maps))
        ]
        self.btn_play = pygame.Rect(px, 305, 255, 38)
        self.btn_fwd = pygame.Rect(px + 270, 305, 255, 38)
        self.btn_back = pygame.Rect(px, 355, 255, 38)
        self.btn_solve = pygame.Rect(px + 270, 355, 255, 38)
        self.btn_reset = pygame.Rect(px, 405, 255, 38)
        self.btn_pencil = pygame.Rect(px + 270, 405, 255, 38)
        self.btn_slower = pygame.Rect(px, 455, 255, 32)
        self.btn_faster = pygame.Rect(px + 270, 455, 255, 32)

    def run(self):
        """Main GUI loop."""
        clock = pygame.time.Clock()
        running = True

        while running:
            current_time = pygame.time.get_ticks() / 1000.0

            # 1. Handle Keyboard & Mouse Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_playing = not self.is_playing
                    elif event.key == pygame.K_RIGHT:
                        self.step_forward()
                    elif event.key == pygame.K_LEFT:
                        self.step_backward()
                    elif event.key == pygame.K_r:
                        self.reset_playback()
                    elif event.key == pygame.K_p:
                        self.show_pencil = not self.show_pencil

            # 2. Auto-advance when playing
            if self.is_playing and (current_time - self.last_step_time >= self.playback_speed):
                if self.current_event_idx < len(self.events):
                    steps = 1 if self.playback_speed > 0.02 else (5 if len(self.events) > 5000 else 2)
                    for _ in range(steps):
                        if self.current_event_idx < len(self.events):
                            self.step_forward()
                    self.last_step_time = current_time
                else:
                    self.is_playing = False
                    self.status_message = "Completed! Puzzle solved successfully."

            # 3. Render Scene
            self.screen.fill(BG_COLOR)
            self.draw_board()
            self.draw_control_panel()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _handle_click(self, mouse_pos: Tuple[int, int]):
        """Handles mouse clicks on puzzle selector and control buttons."""
        for i, rect in enumerate(self.btn_maps):
            if rect.collidepoint(mouse_pos):
                if self.current_map_idx != i:
                    self.current_map_idx = i
                    self.load_puzzle(self.available_maps[i][1])
                return

        if self.btn_play.collidepoint(mouse_pos):
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
            self.playback_speed = min(0.5, self.playback_speed * 1.8)
        elif self.btn_faster.collidepoint(mouse_pos):
            self.playback_speed = max(0.001, self.playback_speed / 1.8)

    def step_forward(self):
        """Executes the next solver trace event."""
        if self.current_event_idx >= len(self.events):
            return

        ev = self.events[self.current_event_idx]
        self.last_active_pos = ev.cell_pos
        self.last_event_type = ev.event_type
        self.status_message = ev.message

        if ev.event_type == EventType.ASSIGN:
            if ev.cell_pos:
                self.grid_values[ev.cell_pos] = ev.value
        elif ev.event_type == EventType.BACKTRACK:
            if ev.cell_pos:
                self.grid_values[ev.cell_pos] = None
        elif ev.event_type == EventType.PRUNE:
            if ev.cell_pos and ev.pruned_domain:
                self.grid_domains[ev.cell_pos] -= ev.pruned_domain

        self.current_event_idx += 1

    def step_backward(self):
        """Steps backward by one trace event."""
        if self.current_event_idx <= 0:
            return
        target = self.current_event_idx - 1
        self.reset_playback()
        for _ in range(target):
            self.step_forward()

    def jump_to_end(self):
        """Jumps directly to the final solved board state."""
        if self.solve_result.is_solved and self.solve_result.solution_grid:
            self.grid_values = dict(self.solve_result.solution_grid)
            self.current_event_idx = len(self.events)
            self.last_active_pos = None
            self.status_message = f"Solved successfully in {self.solve_result.execution_time:.4f}s!"

    def reset_playback(self):
        """Resets board to initial state."""
        self.current_event_idx = 0
        self.grid_values = {pos: None for pos in self.csp.variables}
        self.grid_domains = {pos: set(range(1, 10)) for pos in self.csp.variables}
        self.last_active_pos = None
        self.last_event_type = None
        self.status_message = "Reset to initial state."

    def draw_board(self):
        """Draws the Kakuro grid preserving the original background and rendering SVG digit assets."""
        board_w = self.csp.cols * self.cell_size
        board_h = self.csp.rows * self.cell_size

        # Board outer frame
        outer_rect = pygame.Rect(self.board_ox - 4, self.board_oy - 4, board_w + 8, board_h + 8)
        pygame.draw.rect(self.screen, (15, 20, 28), outer_rect, border_radius=6)

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
                    bg = CELL_WHITE

                    if pos == self.last_active_pos:
                        if self.last_event_type == EventType.ASSIGN:
                            bg = COLOR_ASSIGN
                        elif self.last_event_type == EventType.BACKTRACK:
                            bg = COLOR_BACKTRACK
                        elif self.last_event_type == EventType.PRUNE:
                            bg = COLOR_PRUNE

                    if self.current_event_idx >= len(self.events) and self.grid_values[pos] is not None:
                        bg = COLOR_SOLVED

                    pygame.draw.rect(self.screen, bg, rect)
                    pygame.draw.rect(self.screen, CELL_BORDER, rect, 1)

                    val = self.grid_values[pos]
                    if val is not None:
                        # Assigned value rendered using hand-1..9.svg asset
                        digit_surf = self.hand_big_surfaces.get(val)
                        if digit_surf is not None:
                            self.screen.blit(digit_surf, digit_surf.get_rect(center=rect.center))
                        else:
                            t = self.font_big.render(str(val), True, TEXT_ASSIGNED)
                            self.screen.blit(t, t.get_rect(center=rect.center))
                    elif self.show_pencil:
                        # 3x3 Pencil Marks rendered using hand-1..9.svg assets
                        self._draw_pencil(rect, self.grid_domains[pos])

                else:
                    # 2. Black Clue Cell
                    pygame.draw.rect(self.screen, CELL_BLACK, rect)
                    pygame.draw.line(self.screen, CLUE_LINE_COLOR, rect.topleft, rect.bottomright, 2)
                    pygame.draw.rect(self.screen, (40, 48, 64), rect, 1)

                    clues = self.csp.clue_cells.get(pos, {})
                    v_clue = clues.get('V')
                    h_clue = clues.get('H')

                    if v_clue is not None:
                        vt = self._get_clue_surface(v_clue, is_vertical=True)
                        self.screen.blit(vt, (rect.left + 6, rect.bottom - vt.get_height() - 5))

                    if h_clue is not None:
                        ht = self._get_clue_surface(h_clue, is_vertical=False)
                        self.screen.blit(ht, (rect.right - ht.get_width() - 6, rect.top + 5))

    def _draw_pencil(self, rect: pygame.Rect, domain: Set[int]):
        """Draws 3x3 candidate domain numbers (1..9) inside unassigned cells using SVG hand assets."""
        sw = rect.width / 3.0
        sh = rect.height / 3.0
        for num in range(1, 10):
            if num in domain:
                row = (num - 1) // 3
                col = (num - 1) % 3
                cx = int(rect.left + (col + 0.5) * sw)
                cy = int(rect.top + (row + 0.5) * sh)

                p_surf = self.hand_pencil_surfaces.get(num)
                if p_surf is not None:
                    self.screen.blit(p_surf, p_surf.get_rect(center=(cx, cy)))
                else:
                    t = self.font_pencil.render(str(num), True, PENCIL_COLOR)
                    self.screen.blit(t, t.get_rect(center=(cx, cy)))

    def draw_control_panel(self):
        """Draws the right-hand control dashboard in pure English to avoid font encoding issues."""
        px = 730
        py = 20
        pw = 590
        ph = self.screen_height - 40

        panel_rect = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER_COLOR, panel_rect, 1, border_radius=12)

        # Header Title
        self.screen.blit(self.font_title.render("KAKURO CSP SOLVER", True, TEXT_MAIN), (px + 20, py + 16))
        self.screen.blit(self.font_body.render("Interactive Backtracking & AC-3 Visualizer", True, TEXT_MUTED), (px + 20, py + 42))

        # --- SECTION 1: PUZZLE SELECTOR ---
        lbl_map = self.font_heading.render("SELECT PUZZLE:", True, (226, 232, 240))
        self.screen.blit(lbl_map, (px + 20, py + 74))

        mouse_pos = pygame.mouse.get_pos()
        for i, (name, filename) in enumerate(self.available_maps):
            btn_rect = self.btn_maps[i]
            is_active = (self.current_map_idx == i)
            is_hover = btn_rect.collidepoint(mouse_pos)

            color = BTN_ACTIVE_MAP if is_active else (BTN_SECONDARY_HOVER if is_hover else BTN_SECONDARY)
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=6)
            txt = self.font_btn.render(name + (" (Active)" if is_active else ""), True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=btn_rect.center))

        # --- SECTION 2: PROGRESS & TELEMETRY ---
        stat_card = pygame.Rect(px + 20, py + 168, pw - 40, 115)
        pygame.draw.rect(self.screen, CARD_BG, stat_card, border_radius=8)

        ev_total = max(1, len(self.events))
        pct = (self.current_event_idx / ev_total) * 100
        step_txt = f"Execution Step: {self.current_event_idx:,} / {len(self.events):,} ({pct:.1f}%)"
        self.screen.blit(self.font_btn.render(step_txt, True, TEXT_MAIN), (px + 32, py + 180))

        # Progress Bar
        bar_rect = pygame.Rect(px + 32, py + 208, pw - 64, 10)
        pygame.draw.rect(self.screen, (30, 36, 48), bar_rect, border_radius=5)
        fill_w = int((self.current_event_idx / ev_total) * bar_rect.width)
        if fill_w > 0:
            pygame.draw.rect(self.screen, BTN_PRIMARY, pygame.Rect(bar_rect.x, bar_rect.y, fill_w, 10), border_radius=5)

        # Status description
        msg = self.status_message
        if len(msg) > 54:
            msg = msg[:51] + "..."
        self.screen.blit(self.font_status.render(f"Status: {msg}", True, (203, 213, 225)), (px + 32, py + 228))

        stat_info = f"Nodes: {self.solve_result.nodes_explored:,}  |  Backtracks: {self.solve_result.backtracks:,}  |  Time: {self.solve_result.execution_time:.3f}s"
        self.screen.blit(self.font_status.render(stat_info, True, TEXT_MUTED), (px + 32, py + 252))

        # --- SECTION 3: PLAYBACK CONTROLS ---
        self._draw_btn(self.btn_play, "PAUSE" if self.is_playing else "PLAY / START", BTN_PRIMARY, mouse_pos)
        self._draw_btn(self.btn_fwd, "STEP NEXT >", BTN_SECONDARY, mouse_pos)
        self._draw_btn(self.btn_back, "< STEP BACK", BTN_SECONDARY, mouse_pos)
        self._draw_btn(self.btn_solve, "SOLVE NOW", (16, 185, 129), mouse_pos)
        self._draw_btn(self.btn_reset, "RESET", (239, 68, 68), mouse_pos)
        self._draw_btn(self.btn_pencil, f"PENCIL: {'ON' if self.show_pencil else 'OFF'}", BTN_SECONDARY, mouse_pos)

        # Speed Controls
        self._draw_btn(self.btn_slower, "SPEED: SLOWER", (40, 50, 68), mouse_pos)
        self._draw_btn(self.btn_faster, "SPEED: FASTER", (40, 50, 68), mouse_pos)

        # --- SECTION 4: VISUAL LEGEND ---
        ly = py + 505
        self.screen.blit(self.font_heading.render("VISUAL LEGEND:", True, (226, 232, 240)), (px + 20, ly))

        legends = [
            (COLOR_ASSIGN, "Assign Try (MRV + LCV)"),
            (COLOR_PRUNE, "Domain Pruning (Forward Check)"),
            (COLOR_BACKTRACK, "Dead End (Backtrack)"),
            (COLOR_SOLVED, "Final Solution Assigned"),
            (CLUE_H_COLOR, "Horizontal Clue (Gold)"),
            (CLUE_V_COLOR, "Vertical Clue (Cyan)")
        ]

        for i, (col, text) in enumerate(legends):
            row = i // 2
            col_idx = i % 2
            bx = px + 20 + col_idx * 285
            by = ly + 28 + row * 28
            box = pygame.Rect(bx, by, 18, 18)
            pygame.draw.rect(self.screen, col, box, border_radius=4)
            self.screen.blit(self.font_body.render(text, True, (203, 213, 225)), (bx + 26, by))

    def _draw_btn(self, rect: pygame.Rect, text: str, base_color: Tuple[int, int, int], mouse_pos: Tuple[int, int]):
        """Draws a rounded button with hover highlight."""
        is_hover = rect.collidepoint(mouse_pos)
        color = tuple(min(255, c + 25) for c in base_color) if is_hover else base_color
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        t = self.font_btn.render(text, True, (255, 255, 255))
        self.screen.blit(t, t.get_rect(center=rect.center))
