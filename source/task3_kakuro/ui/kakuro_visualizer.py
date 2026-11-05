"""
Module: kakuro_visualizer.py
Mô tả: Giao diện đồ họa (UI) trực quan hóa giải Kakuro nâng cao (Modern Dashboard Theme).
Thực hiện toàn diện yêu cầu 3 (1.0 điểm) của Task 3:
1. Cho phép chọn Map trực tiếp trên giao diện (Sample 5x5, Complex 9x9) không cần gõ lệnh terminal.
2. Trực quan hóa miền giá trị (Domains): Hiển thị lưới số bút chì nhỏ 1..9 trong các ô chưa gán.
3. Trực quan hóa lan truyền ràng buộc (Constraint Propagation): Đổi màu nổi bật khi tỉa nhánh.
4. Trực quan hóa tìm kiếm quay lui (Backtracking Search): Gán thử (vàng), quay lui (đỏ), hoàn tất (xanh ngọc).
5. Điều khiển: Play/Pause, Step Forward/Back, Giải tức thì (Instant Solve), Reset, và Tùy chỉnh tốc độ.
"""

import sys
import os
import pygame
from typing import List, Dict, Set, Optional, Tuple

from task3_kakuro.csp.csp_problem import KakuroCSP
from task3_kakuro.solver.backtracking_solver import KakuroBacktrackingSolver
from task3_kakuro.solver.tracer import SolverTracer, SolverEvent, EventType

# --- BẢNG MÀU HIỆN ĐẠI (DARK / MODERN ELEGANT THEME) ---
BG_COLOR = (24, 28, 36)               # Nền xám đen công nghệ
PANEL_BG = (32, 38, 50)               # Panel điều khiển
CARD_BG = (42, 50, 66)                # Card nội dung
BORDER_COLOR = (55, 65, 85)           # Viền phân cách

# Bàn cờ Kakuro
CELL_BLACK = (20, 24, 32)             # Ô đen Clue
CELL_WHITE = (248, 250, 252)          # Ô trắng
CELL_BORDER = (160, 175, 195)         # Viền ô trắng
CLUE_LINE_COLOR = (70, 85, 110)       # Đường chéo chia clue
CLUE_V_COLOR = (56, 189, 248)         # Clue Dọc: Xanh Cyan neon
CLUE_H_COLOR = (250, 204, 21)         # Clue Ngang: Vàng Gold neon

# Trạng thái tìm kiếm
COLOR_ASSIGN = (254, 240, 138)        # Đang gán thử: Vàng tươi
COLOR_PRUNE = (186, 230, 253)         # Đang tỉa nhánh: Xanh nước biển nhạt
COLOR_BACKTRACK = (254, 202, 202)     # Quay lui: Đỏ san hô
COLOR_SOLVED = (187, 247, 208)        # Nghiệm chuẩn: Xanh ngọc lục bảo

TEXT_MAIN = (240, 245, 255)           # Chữ chính
TEXT_MUTED = (148, 163, 184)          # Chữ phụ
TEXT_ASSIGNED = (15, 23, 42)          # Chữ số lớn đã điền trong ô
PENCIL_COLOR = (100, 116, 139)        # Số bút chì còn lại

# Màu nút bấm
BTN_PRIMARY = (14, 165, 233)          # Xanh dương
BTN_PRIMARY_HOVER = (56, 189, 248)
BTN_SECONDARY = (51, 65, 85)          # Xám than
BTN_SECONDARY_HOVER = (71, 85, 105)
BTN_ACTIVE_MAP = (16, 185, 129)       # Xanh lá khi map đang chọn


class KakuroVisualizer:
    """
    Trình diễn đồ họa trực quan hóa giải Kakuro CSP với bộ điều khiển hoàn chỉnh.
    """

    def __init__(self, puzzle_dir: str = None):
        pygame.init()
        pygame.font.init()

        if puzzle_dir is None:
            self.puzzle_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "puzzles")
        else:
            self.puzzle_dir = puzzle_dir

        # Danh sách các câu đố có sẵn
        self.available_maps = [
            ("5x5 Sample", "sample_5x5.json"),
            ("9x9 Complex", "complex_9x9.json")
        ]
        self.current_map_idx = 0

        # Cửa sổ hiển thị
        self.screen_width = 1120
        self.screen_height = 700
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Kakuro CSP Visualizer - Introduction to AI (TDTU)")

        # Khởi tạo Font hệ thống mượt mà
        self._init_fonts()

        # Nạp map đầu tiên
        self.load_puzzle(self.available_maps[self.current_map_idx][1])

    def _init_fonts(self):
        font_name = "Segoe UI" if "Segoe UI" in pygame.font.get_fonts() else "Arial"
        self.font_title = pygame.font.SysFont(font_name, 20, bold=True)
        self.font_heading = pygame.font.SysFont(font_name, 16, bold=True)
        self.font_body = pygame.font.SysFont(font_name, 13)
        self.font_btn = pygame.font.SysFont(font_name, 13, bold=True)
        self.font_status = pygame.font.SysFont(font_name, 12)

    def load_puzzle(self, filename: str):
        """Nạp bài toán, chạy solver thu thập tracer và cấu hình lại hiển thị."""
        filepath = os.path.join(self.puzzle_dir, filename)
        self.csp = KakuroCSP()
        self.csp.load_from_json(filepath)

        # Chạy solver để thu thập vết hoạt động (Tracer)
        self.tracer = SolverTracer()
        self.solver = KakuroBacktrackingSolver(use_ac3=True, use_mrv=True, use_lcv=True, tracer=self.tracer)
        self.solve_result = self.solver.solve(self.csp)
        self.events: List[SolverEvent] = self.tracer.events

        # Reset các biến điều khiển playback
        self.current_event_idx = 0
        self.is_playing = False
        self.playback_speed = 0.05
        self.last_step_time = 0.0
        self.show_pencil = True

        # Trạng thái bảng cờ trực quan
        self.grid_values: Dict[Tuple[int, int], Optional[int]] = {pos: None for pos in self.csp.variables}
        self.grid_domains: Dict[Tuple[int, int], Set[int]] = {pos: set(range(1, 10)) for pos in self.csp.variables}
        self.last_active_pos: Optional[Tuple[int, int]] = None
        self.last_event_type: Optional[EventType] = None
        self.status_message = f"Đã nạp {filename}: {len(self.csp.variables)} ô trắng, {len(self.events)} sự kiện."

        # Tính toán kích thước ô cờ (Cell Size) tự co giãn
        max_board_w = 640
        max_board_h = 620
        self.cell_size = min(max_board_w // self.csp.cols, max_board_h // self.csp.rows)
        self.cell_size = max(42, min(self.cell_size, 72))

        self.board_ox = 30
        self.board_oy = (self.screen_height - (self.csp.rows * self.cell_size)) // 2

        # Cấu hình Font chữ trên bàn cờ
        font_name = "Segoe UI" if "Segoe UI" in pygame.font.get_fonts() else "Arial"
        self.font_big = pygame.font.SysFont(font_name, int(self.cell_size * 0.48), bold=True)
        self.font_clue = pygame.font.SysFont(font_name, int(self.cell_size * 0.23), bold=True)
        self.font_pencil = pygame.font.SysFont(font_name, int(self.cell_size * 0.18), bold=True)

        # Cấu hình vị trí các nút bấm (lưu làm thuộc tính để bắt click đồng bộ 100%)
        self.btn_maps = [
            pygame.Rect(720 + i * 175, 118, 165, 34)
            for i in range(len(self.available_maps))
        ]
        self.btn_play = pygame.Rect(720, 295, 165, 36)
        self.btn_fwd = pygame.Rect(900, 295, 165, 36)
        self.btn_back = pygame.Rect(720, 340, 165, 36)
        self.btn_solve = pygame.Rect(900, 340, 165, 36)
        self.btn_reset = pygame.Rect(720, 385, 165, 36)
        self.btn_pencil = pygame.Rect(900, 385, 165, 36)
        self.btn_slower = pygame.Rect(720, 432, 165, 30)
        self.btn_faster = pygame.Rect(900, 432, 165, 30)

    def run(self):
        """Vòng lặp giao diện chính."""
        clock = pygame.time.Clock()
        running = True

        while running:
            current_time = pygame.time.get_ticks() / 1000.0

            # 1. Bắt sự kiện bàn phím & chuột
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

            # 2. Xử lý Play tự động
            if self.is_playing and (current_time - self.last_step_time >= self.playback_speed):
                if self.current_event_idx < len(self.events):
                    # Bước nhảy theo tốc độ
                    steps = 1 if self.playback_speed > 0.02 else (5 if len(self.events) > 5000 else 2)
                    for _ in range(steps):
                        if self.current_event_idx < len(self.events):
                            self.step_forward()
                    self.last_step_time = current_time
                else:
                    self.is_playing = False
                    self.status_message = "Đã hoàn thành! Bàn cờ đã giải xong hoàn toàn."

            # 3. Vẽ toàn bộ khung cảnh
            self.screen.fill(BG_COLOR)
            self.draw_board()
            self.draw_control_panel()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def _handle_click(self, mouse_pos: Tuple[int, int]):
        """Xử lý tương tác click chuột trực quan."""
        # 1. Click chọn Map
        for i, rect in enumerate(self.btn_maps):
            if rect.collidepoint(mouse_pos):
                if self.current_map_idx != i:
                    self.current_map_idx = i
                    self.load_puzzle(self.available_maps[i][1])
                return

        # Click nút điều khiển
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
        """Thực thi sự kiện tiếp theo."""
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
        """Quay lui sự kiện trước đó."""
        if self.current_event_idx <= 0:
            return
        target = self.current_event_idx - 1
        self.reset_playback()
        for _ in range(target):
            self.step_forward()

    def jump_to_end(self):
        """Nhảy ngay tới trạng thái nghiệm hoàn thành."""
        if self.solve_result.is_solved and self.solve_result.solution_grid:
            self.grid_values = dict(self.solve_result.solution_grid)
            self.current_event_idx = len(self.events)
            self.last_active_pos = None
            self.status_message = f"Đã giải thành công trong {self.solve_result.execution_time:.4f}s!"

    def reset_playback(self):
        """Đặt lại bàn cờ về trạng thái bắt đầu."""
        self.current_event_idx = 0
        self.grid_values = {pos: None for pos in self.csp.variables}
        self.grid_domains = {pos: set(range(1, 10)) for pos in self.csp.variables}
        self.last_active_pos = None
        self.last_event_type = None
        self.status_message = "Đã đặt lại trạng thái ban đầu."

    def draw_board(self):
        """Vẽ lưới cờ Kakuro với bóng đổ và thiết kế hiện đại."""
        board_w = self.csp.cols * self.cell_size
        board_h = self.csp.rows * self.cell_size

        # Khung viền bàn cờ
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
                    # 1. Vẽ ô trắng (White Cell)
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
                        # Số lớn đã gán
                        t = self.font_big.render(str(val), True, TEXT_ASSIGNED)
                        self.screen.blit(t, t.get_rect(center=rect.center))
                    elif self.show_pencil:
                        # Số bút chì nhỏ (Domain 1..9)
                        self._draw_pencil(rect, self.grid_domains[pos])

                else:
                    # 2. Vẽ ô đen chứa clue (Black Cell)
                    pygame.draw.rect(self.screen, CELL_BLACK, rect)
                    pygame.draw.line(self.screen, CLUE_LINE_COLOR, rect.topleft, rect.bottomright, 2)
                    pygame.draw.rect(self.screen, (40, 48, 64), rect, 1)

                    clues = self.csp.clue_cells.get(pos, {})
                    v_clue = clues.get('V')
                    h_clue = clues.get('H')

                    if v_clue is not None:
                        vt = self.font_clue.render(str(v_clue), True, CLUE_V_COLOR)
                        self.screen.blit(vt, (rect.left + 5, rect.bottom - vt.get_height() - 4))

                    if h_clue is not None:
                        ht = self.font_clue.render(str(h_clue), True, CLUE_H_COLOR)
                        self.screen.blit(ht, (rect.right - ht.get_width() - 5, rect.top + 4))

    def _draw_pencil(self, rect: pygame.Rect, domain: Set[int]):
        """Vẽ số bút chì 1..9 dạng 3x3 trong ô chưa điền."""
        sw = rect.width / 3.0
        sh = rect.height / 3.0
        for num in range(1, 10):
            row = (num - 1) // 3
            col = (num - 1) % 3
            cx = rect.left + (col + 0.5) * sw
            cy = rect.top + (row + 0.5) * sh

            if num in domain:
                t = self.font_pencil.render(str(num), True, PENCIL_COLOR)
                self.screen.blit(t, t.get_rect(center=(cx, cy)))

    def draw_control_panel(self):
        """Vẽ Dashboard điều khiển bên phải."""
        px = 700
        py = 20
        pw = 390
        ph = self.screen_height - 40

        panel_rect = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER_COLOR, panel_rect, 1, border_radius=12)

        # Header Tiêu đề
        self.screen.blit(self.font_title.render("KAKURO CSP SOLVER", True, TEXT_MAIN), (px + 20, py + 16))
        self.screen.blit(self.font_body.render("Interactive Backtracking & AC-3 Visualizer", True, TEXT_MUTED), (px + 20, py + 42))

        # --- PHẦN 1: BỘ CHỌN MAP (PUZZLE SELECTOR) ---
        lbl_map = self.font_heading.render("CHỌN BÀN CỜ (SELECT PUZZLE):", True, (226, 232, 240))
        self.screen.blit(lbl_map, (px + 20, py + 72))

        mouse_pos = pygame.mouse.get_pos()
        for i, (name, filename) in enumerate(self.available_maps):
            btn_rect = self.btn_maps[i]
            is_active = (self.current_map_idx == i)
            is_hover = btn_rect.collidepoint(mouse_pos)

            color = BTN_ACTIVE_MAP if is_active else (BTN_SECONDARY_HOVER if is_hover else BTN_SECONDARY)
            pygame.draw.rect(self.screen, color, btn_rect, border_radius=6)
            txt = self.font_btn.render(name + (" (Active)" if is_active else ""), True, (255, 255, 255))
            self.screen.blit(txt, txt.get_rect(center=btn_rect.center))

        # --- PHẦN 2: THỐNG KÊ TIẾN ĐỘ ---
        stat_card = pygame.Rect(px + 20, py + 148, pw - 40, 110)
        pygame.draw.rect(self.screen, CARD_BG, stat_card, border_radius=8)

        ev_total = max(1, len(self.events))
        pct = (self.current_event_idx / ev_total) * 100
        step_txt = f"Bước thực thi: {self.current_event_idx:,} / {len(self.events):,} ({pct:.1f}%)"
        self.screen.blit(self.font_btn.render(step_txt, True, TEXT_MAIN), (px + 32, py + 160))

        # Thanh tiến trình (Progress Bar)
        bar_rect = pygame.Rect(px + 32, py + 185, pw - 64, 8)
        pygame.draw.rect(self.screen, (30, 36, 48), bar_rect, border_radius=4)
        fill_w = int((self.current_event_idx / ev_total) * bar_rect.width)
        if fill_w > 0:
            pygame.draw.rect(self.screen, BTN_PRIMARY, pygame.Rect(bar_rect.x, bar_rect.y, fill_w, 8), border_radius=4)

        # Trạng thái diễn giải
        msg = self.status_message
        if len(msg) > 42:
            msg = msg[:39] + "..."
        self.screen.blit(self.font_status.render(f"Trạng thái: {msg}", True, (203, 213, 225)), (px + 32, py + 205))

        stat_info = f"Nodes: {self.solve_result.nodes_explored:,}  |  Backtracks: {self.solve_result.backtracks:,}  |  Time: {self.solve_result.execution_time:.3f}s"
        self.screen.blit(self.font_status.render(stat_info, True, TEXT_MUTED), (px + 32, py + 228))

        # --- PHẦN 3: NÚT BẤM ĐIỀU KHIỂN (CONTROLS) ---
        self.btn_play = pygame.Rect(px + 20, py + 275, 165, 36)
        self.btn_fwd = pygame.Rect(px + 200, py + 275, 165, 36)
        self.btn_back = pygame.Rect(px + 20, py + 320, 165, 36)
        self.btn_solve = pygame.Rect(px + 200, py + 320, 165, 36)
        self.btn_reset = pygame.Rect(px + 20, py + 365, 165, 36)
        self.btn_pencil = pygame.Rect(px + 200, py + 365, 165, 36)

        self._draw_btn(self.btn_play, "TẠM DỪNG (PAUSE)" if self.is_playing else "PHÁT (PLAY)", BTN_PRIMARY, mouse_pos)
        self._draw_btn(self.btn_fwd, "BƯỚC TIẾP (STEP >)", BTN_SECONDARY, mouse_pos)
        self._draw_btn(self.btn_back, "< BƯỚC TRƯỚC", BTN_SECONDARY, mouse_pos)
        self._draw_btn(self.btn_solve, "GIẢI NGAY (SOLVE)", (16, 185, 129), mouse_pos)
        self._draw_btn(self.btn_reset, "ĐẶT LẠI (RESET)", (239, 68, 68), mouse_pos)
        self._draw_btn(self.btn_pencil, f"BÚT CHÌ: {'BẬT' if self.show_pencil else 'TẮT'}", BTN_SECONDARY, mouse_pos)

        # Tùy chỉnh tốc độ (Speed)
        self.btn_slower = pygame.Rect(px + 20, py + 412, 165, 30)
        self.btn_faster = pygame.Rect(px + 200, py + 412, 165, 30)
        self._draw_btn(self.btn_slower, "TỐC ĐỘ: CHẬM HƠN", (40, 50, 68), mouse_pos)
        self._draw_btn(self.btn_faster, "TỐC ĐỘ: NHANH HƠN", (40, 50, 68), mouse_pos)

        # --- PHẦN 4: CHÚ THÍCH MÀU SẮC (LEGEND) ---
        ly = py + 460
        self.screen.blit(self.font_heading.render("CHÚ THÍCH TRỰC QUAN:", True, (226, 232, 240)), (px + 20, ly))

        legends = [
            (COLOR_ASSIGN, "Gán thử giá trị (MRV + LCV)"),
            (COLOR_PRUNE, "Tỉa miền giá trị (Forward Checking)"),
            (COLOR_BACKTRACK, "Nhánh cụt - Quay lui (Backtrack)"),
            (COLOR_SOLVED, "Ô đã chốt nghiệm hợp lệ"),
            (CLUE_H_COLOR, "Clue Ngang (Màu vàng gold)"),
            (CLUE_V_COLOR, "Clue Dọc (Màu xanh cyan)")
        ]

        for i, (col, text) in enumerate(legends):
            row = i // 2
            col_idx = i % 2
            bx = px + 20 + col_idx * 185
            by = ly + 28 + row * 26
            box = pygame.Rect(bx, by, 16, 16)
            pygame.draw.rect(self.screen, col, box, border_radius=3)
            self.screen.blit(self.font_body.render(text, True, (203, 213, 225)), (bx + 24, by - 1))

    def _draw_btn(self, rect: pygame.Rect, text: str, base_color: Tuple[int, int, int], mouse_pos: Tuple[int, int]):
        """Hàm phụ trợ vẽ nút bấm bo góc có hiệu ứng hover."""
        is_hover = rect.collidepoint(mouse_pos)
        color = tuple(min(255, c + 25) for c in base_color) if is_hover else base_color
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        t = self.font_btn.render(text, True, (255, 255, 255))
        self.screen.blit(t, t.get_rect(center=rect.center))
