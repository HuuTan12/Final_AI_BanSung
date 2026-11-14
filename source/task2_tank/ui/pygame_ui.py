"""
pygame_ui.py - High-Fidelity Tactical Battle City GUI with Clean Technical HUD & 2-Human PvP Support
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements a responsive, intuitive Pygame GUI with:
    1. Smooth tank movement & cell-by-cell bullet flight animations (3 cells/cycle rule).
    2. Start-on-demand workflow: Match waits in READY state until the user clicks START.
    3. Clean, easy-to-read Technical Parameters & Telemetry HUD without visual clutter.
    4. Optimized 2-Human PvP mode with separate keyboard zones (P0: WASD+F/SPACE, P1: Arrows+[/] fire, [.] stay)
       and independent input queues so simultaneous keypresses are never lost or cross-triggered.
    5. Interactive On-Screen Control Pad and dynamic algorithm/depth switcher.
"""

import os
import sys
import math
import time
from typing import Optional, Dict, List, Tuple, Any

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Bullet
from task2_tank.engine.rules import GameRules
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.agents.human_agent import HumanAgent
from task2_tank.agent_loader import AgentLoader


# Available algorithm presets for player selection
AGENT_PRESETS = [
    ("human", "Human (Manual Controls)"),
    ("heuristic_alphabeta", "Heuristic Alpha-Beta (HAB)"),
    ("id_ab", "Iterative Deepening AB (ID-AB)"),
    ("alphabeta", "Alpha-Beta Pruning (AB)"),
    ("heuristic_minimax", "Heuristic Minimax"),
    ("minimax", "Minimax Search"),
    ("greedy", "Greedy Tactical (1-Ply)"),
    ("rival", "Rival Group Bot (External)"),
]


class TankGameGUI:
    """
    Graphical User Interface for the Tank Battle Game.
    """

    def __init__(self, cell_size: int = 46, fps: int = 60):
        self.cell_size = cell_size
        self.fps = fps
        self.speed_multiplier = 1.0  # 0.5x, 1.0x, 2.0x, 4.0x

        # Playback control flags: Start paused waiting for user to press START
        self.is_paused: bool = True
        self.match_started: bool = False
        self.step_requested: bool = False
        self.undo_requested: bool = False
        self.restart_requested: bool = False
        self.map_requested: bool = False
        self.map_prev_requested: bool = False
        self.current_map_title: str = "01_classic_battlecity"
        self.map_badge_rect: Optional[pygame.Rect] = None

        # Agent switching flags
        self.agent_changed: bool = False
        self.presets: List[Tuple[str, str]] = list(AGENT_PRESETS)
        self._load_discovered_external_presets()
        self.p0_algo_idx: int = 1     # Default: Heuristic Alpha-Beta
        self.p1_algo_idx: int = 3     # Default: Alpha-Beta Pruning
        self.last_p0_ai_idx: int = 1
        self.last_p1_ai_idx: int = 3
        self.p0_depth: int = 3
        self.p1_depth: int = 3

        # Pygame handles
        self.screen = None
        self.clock = None
        self.sidebar_width = 460
        self.sprites: Dict[str, Any] = {}
        self.anim_tick: int = 0

        # Interactive buttons
        self.buttons: List[Dict[str, Any]] = []
        self.speed_buttons: List[Dict[str, Any]] = []
        self.mode_buttons: List[Dict[str, Any]] = []
        self.dpad_buttons: List[Dict[str, Any]] = []
        self.gameover_buttons: List[Dict[str, Any]] = []
        self.start_banner_rect: Optional[pygame.Rect] = None

        # Visual FX state
        self.tracks: List[Dict[str, Any]] = []         # [{x, y, dir, life}]
        self.explosions: List[Dict[str, Any]] = []     # [{x, y, frame, max_frames}]
        self.muzzle_flashes: List[Dict[str, Any]] = [] # [{x, y, dir, frame, max_frames}]
        self.damage_flashes: Dict[str, int] = {}       # {entity_key: frames_remaining}

        # Sub-step animated tank & bullet state
        self.animated_tank_override: Dict[int, Tuple[int, int, Direction]] = {}
        self.animated_bullets: List[Dict[str, Any]] = []
        self.animating_owner_id: Optional[int] = None

        # Clean combat event log feed
        self.combat_logs: List[Dict[str, Any]] = [
            {"text": "[READY] Match loaded. Click [START] button on the right panel to begin.", "color": (46, 204, 113)},
            {"text": "[RULES] Tank: 6 HP | Base: 9 HP | Wall: 1-3 HP | Bullet: 3 cells/cycle", "color": (160, 180, 210)},
        ]

        # Telemetry & Evaluator
        self.eval_score: float = 0.0
        self.smooth_eval: float = 0.0
        self.evaluator = TankEvaluator()

        # Independent Human action queues for P0 and P1 (optimizes 2-Human PvP)
        self.human_queues: Dict[int, Optional[Action]] = {0: None, 1: None}
        self.human_action_queued: Optional[Action] = None

<<<<<<< Updated upstream
        # AI thinking state & non-blocking execution indicators
        self.ai_thinking: bool = False
        self.ai_thinking_pid: Optional[int] = None

        # Fluid continuous key-holding & arcade driving controls (per-player cooldowns)
        self.last_human_action_time: Dict[int, float] = {0: 0.0, 1: 0.0}
        self.human_repeat_delay: float = 0.16
        self.active_game_state: Optional[GameState] = None
        self.quit_requested: bool = False
=======
        # Human Mode Optimization & Juice
        self.should_quit: bool = False
        self.ai_thinking: bool = False
        self.screen_shake: int = 0
        self.shake_offset: Tuple[int, int] = (0, 0)
        self.hover_board_cell: Optional[Tuple[int, int]] = None
        self.last_input_action: Optional[Action] = None
        self.last_state: Optional[GameState] = None
        self.tactical_assist_enabled: bool = True
>>>>>>> Stashed changes

        # Color Palette - Clean Modern Dark Slate
        self.COLOR_BG = (15, 18, 26)
        self.COLOR_SIDEBAR_BG = (20, 25, 36)
        self.COLOR_CARD_BG = (28, 35, 50)
        self.COLOR_CARD_BORDER = (45, 58, 82)
        self.COLOR_CARD_HEADER = (34, 43, 62)
        self.COLOR_INSET_BG = (16, 21, 30)
        self.COLOR_INSET_BORDER = (36, 46, 66)
        self.COLOR_TEXT = (242, 246, 252)
        self.COLOR_TEXT_DIM = (155, 170, 195)
        self.COLOR_TEXT_MUTED = (100, 115, 140)
        self.COLOR_GOLD = (245, 190, 35)
        self.COLOR_AMBER = (230, 126, 34)
        self.COLOR_CYAN = (56, 189, 248)
        self.COLOR_EMERALD = (46, 204, 113)

        # Team Color Themes
        self.COLOR_P0_PRIMARY = (56, 165, 245)     # Blue (Player 0 MAX)
        self.COLOR_P0_BG = (22, 32, 48)
        self.COLOR_P0_BORDER = (45, 130, 195)

        self.COLOR_P1_PRIMARY = (235, 85, 70)      # Red (Player 1 MIN)
        self.COLOR_P1_BG = (44, 24, 30)
        self.COLOR_P1_BORDER = (190, 65, 55)

        # Entity colors (fallback)
        self.COLOR_WALL = (165, 85, 54)
        self.COLOR_WALL_CRACK = (120, 60, 40)
        self.COLOR_HP_GREEN = (46, 204, 113)
        self.COLOR_HP_YELLOW = (241, 196, 15)
        self.COLOR_HP_RED = (231, 76, 60)

    def update_map_layout(self, width_cells: int, height_cells: int) -> None:
        """
        Dynamically adapts cell size, board dimensions, and window resolution:
        - Prevents map clipping (Map 04 15x15, Map 05 21x11, etc. are 100% visible).
        - Automatically shrinks window for smaller maps (no empty black voids).
        - Perfectly aligns sidebar HUD to the right edge of the battlefield.
        - Reloads scaled sprites and repositions interactive control buttons.
        """
        max_board_w = 930
        max_board_h = 660
        cs_w = max_board_w // width_cells
        cs_h = max_board_h // height_cells
        target_cs = max(36, min(46, cs_w, cs_h))

        cs_changed = (target_cs != self.cell_size)
        self.cell_size = target_cs

        new_board_w = width_cells * self.cell_size
        new_board_h = height_cells * self.cell_size
        new_width_px = new_board_w + self.sidebar_width
        new_height_px = max(new_board_h + 120, 760)

        dim_changed = (
            new_board_w != getattr(self, "board_w", 0) or
            new_board_h != getattr(self, "board_h", 0) or
            new_width_px != getattr(self, "width_px", 0) or
            new_height_px != getattr(self, "height_px", 0)
        )

        self.board_w = new_board_w
        self.board_h = new_board_h
        self.width_px = new_width_px
        self.height_px = new_height_px
        self._last_map_dim = (width_cells, height_cells)

        if PYGAME_AVAILABLE:
            if self.screen is None:
                self.screen = pygame.display.set_mode((self.width_px, self.height_px))
            elif dim_changed:
                self.screen = pygame.display.set_mode((self.width_px, self.height_px))

        if cs_changed and hasattr(self, "sprites") and self.sprites:
            self._load_sprites()

        self._init_buttons()

    def init_display(self, width_cells: int, height_cells: int) -> bool:
        """Initializes Pygame window, fonts, buttons, and visual assets."""
        if not PYGAME_AVAILABLE:
            print("[TankGameGUI] Notice: Pygame is not installed. Running in headless mode.")
            return False

        try:
            pygame.init()
            pygame.font.init()
            pygame.key.set_repeat(220, 60)

            self.update_map_layout(width_cells, height_cells)

            pygame.display.set_caption("AI Tank Battle - Adversarial Search Visualizer (TDTU)")
            self.clock = pygame.time.Clock()

            font_family = "Segoe UI,Arial"
            mono_family = "Consolas,Courier New,Arial"
            self.font_title = pygame.font.SysFont(font_family, 17, bold=True)
            self.font_header = pygame.font.SysFont(font_family, 13, bold=True)
            self.font_large = pygame.font.SysFont(font_family, 14, bold=True)
            self.font = pygame.font.SysFont(font_family, 12)
            self.font_bold = pygame.font.SysFont(font_family, 12, bold=True)
            self.font_badge = pygame.font.SysFont(mono_family, 11, bold=True)
            self.font_metric_val = pygame.font.SysFont(mono_family, 15, bold=True)
            self.font_metric_lbl = pygame.font.SysFont(font_family, 10, bold=True)
            self.font_small = pygame.font.SysFont(font_family, 11)
            self.font_coord = pygame.font.SysFont(mono_family, 11, bold=True)

            self._load_sprites()
            self._init_buttons()
            return True
        except Exception as e:
            print(f"[TankGameGUI] Display initialization error: {e}")
            return False

    def _load_sprites(self) -> None:
        """Loads PNG sprites from Kenney assets."""
        asset_dir = os.path.join(
            os.path.dirname(__file__), "..", "assets", "tanks-task2", "PNG", "Default size"
        )
        if not os.path.exists(asset_dir):
            return

        def load_scaled(filename: str, w: int, h: int):
            path = os.path.join(asset_dir, filename)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    return pygame.transform.smoothscale(img, (w, h))
                except Exception:
                    return None
            return None

        cs = self.cell_size

        # 1. Terrain & Foliage
        self.sprites["tile_sand"] = load_scaled("tileSand1.png", cs, cs)
        self.sprites["tile_sand2"] = load_scaled("tileSand2.png", cs, cs)
        self.sprites["tree"] = load_scaled("treeGreen_small.png", cs - 2, cs - 2)

        # 2. Tanks & Icons
        self.sprites["tank_0"] = load_scaled("tank_blue.png", cs - 6, cs - 6)
        self.sprites["tank_1"] = load_scaled("tank_red.png", cs - 6, cs - 6)
        self.sprites["tank_0_icon"] = load_scaled("tank_blue.png", 26, 26)
        self.sprites["tank_1_icon"] = load_scaled("tank_red.png", 26, 26)
        self.sprites["track"] = load_scaled("tracksSmall.png", cs // 2, cs // 2)

        # 3. Bullets & Muzzle Flash
        self.sprites["bullet_0"] = load_scaled("bulletBlue1_outline.png", 14, 18)
        self.sprites["bullet_1"] = load_scaled("bulletRed1_outline.png", 14, 18)
        self.sprites["bullet_icon"] = load_scaled("bulletBlue1_outline.png", 12, 16)
        self.sprites["shot_flash"] = load_scaled("shotOrange.png", 20, 26)

        # 4. Destructible Obstacles
        self.sprites["wall_3"] = load_scaled("crateMetal.png", cs - 4, cs - 4)
        self.sprites["wall_2"] = load_scaled("crateWood.png", cs - 4, cs - 4)
        self.sprites["wall_1"] = load_scaled("sandbagBrown.png", cs - 4, cs - 4)

        # 5. Base HQs (Fortified Command Citadels - "Cứ điểm")
        self.sprites["base_0"] = self._create_citadel_surface(cs - 4, pid=0)
        self.sprites["base_1"] = self._create_citadel_surface(cs - 4, pid=1)
        self.sprites["base_0_icon"] = self._create_citadel_surface(24, pid=0)
        self.sprites["base_1_icon"] = self._create_citadel_surface(24, pid=1)

        # 6. Explosions & Smoke
        for i in range(1, 6):
            self.sprites[f"exp_{i}"] = load_scaled(f"explosion{i}.png", cs + 6, cs + 6)
        for i in range(1, 4):
            self.sprites[f"smoke_{i}"] = load_scaled(f"explosionSmoke{i}.png", cs, cs)

        # 7. Rules Showcase Sprites
        self.sprites["crate_metal_spec"] = load_scaled("crateMetal.png", 20, 20)
        self.sprites["crate_wood_spec"] = load_scaled("crateWood.png", 20, 20)
        self.sprites["sandbag_spec"] = load_scaled("sandbagBrown.png", 20, 20)

    @staticmethod
    def _draw_star_polygon(
        surf: Any,
        cx: float,
        cy: float,
        outer_r: float,
        inner_r: float,
        fill_color: Tuple[int, int, int],
        border_color: Optional[Tuple[int, int, int]] = None
    ) -> None:
        """Draws a crisp 5-pointed military command star centered at (cx, cy)."""
        pts = []
        for i in range(10):
            angle = -math.pi / 2 + i * (math.pi / 5)
            r = outer_r if i % 2 == 0 else inner_r
            pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        pygame.draw.polygon(surf, fill_color, pts)
        if border_color is not None:
            pygame.draw.polygon(surf, border_color, pts, 1)

    def _create_citadel_surface(self, size: int, pid: int) -> Any:
        """
        Generates a fortified Command Citadel ('Cứ điểm') surface with:
        - Reinforced steel bunker baseplate & 4 corner bastion turrets
        - Cardinal armor embrasures & radar crosshairs
        - Team-colored energy shield ring (Blue MAX / Red MIN)
        - Central 5-pointed Golden Command Star emblem
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size / 2.0, size / 2.0

        if pid == 0:
            team_main = (45, 160, 245)
            team_dark = (16, 56, 105)
            team_glow = (110, 215, 255)
        else:
            team_main = (235, 75, 65)
            team_dark = (108, 22, 26)
            team_glow = (255, 155, 95)

        # 1. Outer reinforced steel bunker plate
        pad = max(1, size // 14)
        base_rect = pygame.Rect(pad, pad, size - 2 * pad, size - 2 * pad)
        pygame.draw.rect(surf, (24, 31, 44), base_rect, border_radius=max(3, size // 7))
        pygame.draw.rect(surf, (78, 94, 122), base_rect, 1, border_radius=max(3, size // 7))

        # 2. Four Corner Bastion Turrets (Fortress Pillars)
        tw = max(4, int(size * 0.24))
        corners = [
            (0, 0),
            (size - tw, 0),
            (0, size - tw),
            (size - tw, size - tw),
        ]
        for tx, ty in corners:
            t_rect = pygame.Rect(tx, ty, tw, tw)
            pygame.draw.rect(surf, (38, 48, 66), t_rect, border_radius=2)
            pygame.draw.rect(surf, (110, 128, 158), t_rect, 1, border_radius=2)
            if size >= 32:
                pygame.draw.circle(surf, team_glow, (tx + tw // 2, ty + tw // 2), 1)

        # 3. Cardinal Armor Embrasures & Crosshair Struts
        pygame.draw.line(surf, (58, 74, 100), (pad + 2, int(cy)), (size - pad - 3, int(cy)), 2)
        pygame.draw.line(surf, (58, 74, 100), (int(cx), pad + 2), (int(cx), size - pad - 3), 2)

        # 4. Fortified Team Shield Ring & Command Dome
        outer_ring_r = int(size * 0.36)
        inner_dome_r = int(size * 0.28)
        pygame.draw.circle(surf, team_dark, (int(cx), int(cy)), outer_ring_r)
        pygame.draw.circle(surf, team_main, (int(cx), int(cy)), outer_ring_r, max(1, size // 18))
        pygame.draw.circle(surf, (18, 24, 36), (int(cx), int(cy)), inner_dome_r)
        pygame.draw.circle(surf, team_glow, (int(cx), int(cy)), inner_dome_r, 1)

        # 5. Central 5-Pointed Golden Command Star ("Cứ điểm")
        star_outer = max(4.0, size * 0.22)
        star_inner = max(2.0, size * 0.095)
        self._draw_star_polygon(surf, cx, cy, star_outer, star_inner, (250, 200, 40), (255, 242, 175))
        if size >= 32:
            self._draw_star_polygon(surf, cx, cy, star_outer * 0.52, star_inner * 0.52, (255, 248, 210))

        return surf

    def _init_buttons(self) -> None:
        """Creates interactive buttons in the sidebar."""
        pad_x = self.board_w + 16
        card_w = self.sidebar_width - 32
        btn_y = 70

        # Row 1: Action Controls (Prominent START/PAUSE + 4 actions)
        w_btn = (card_w - 20) // 5
        self.buttons = [
            {"id": "play_pause", "label": "START",   "rect": pygame.Rect(pad_x, btn_y, w_btn + 8, 30)},
            {"id": "step",       "label": "STEP +1", "rect": pygame.Rect(pad_x + w_btn + 13, btn_y, w_btn - 2, 30)},
            {"id": "undo",       "label": "UNDO",    "rect": pygame.Rect(pad_x + 2 * w_btn + 16, btn_y, w_btn - 2, 30)},
            {"id": "restart",    "label": "RESET",   "rect": pygame.Rect(pad_x + 3 * w_btn + 19, btn_y, w_btn - 2, 30)},
            {"id": "next_map",   "label": "MAP >>",  "rect": pygame.Rect(pad_x + 4 * w_btn + 22, btn_y, w_btn - 2, 30)},
        ]

        # Row 2: Speed Toggles (Slower, intuitive defaults)
        s_y = btn_y + 36
        sw_btn = (card_w - 18) // 4
        self.speed_buttons = [
            {"id": "speed_05", "label": "0.5x Slow",   "rect": pygame.Rect(pad_x, s_y, sw_btn, 25), "val": 0.5},
            {"id": "speed_1",  "label": "1.0x Normal", "rect": pygame.Rect(pad_x + sw_btn + 6, s_y, sw_btn, 25), "val": 1.0},
            {"id": "speed_2",  "label": "2.0x Fast",   "rect": pygame.Rect(pad_x + 2 * (sw_btn + 6), s_y, sw_btn, 25), "val": 2.0},
            {"id": "speed_4",  "label": "4.0x Turbo",  "rect": pygame.Rect(pad_x + 3 * (sw_btn + 6), s_y, sw_btn, 25), "val": 4.0},
        ]

        # Row 3: 1-Click Mode Presets (1P vs AI, 2P PvP, AI vs AI)
        m_y = s_y + 30
        mw_btn = (card_w - 12) // 3
        self.mode_buttons = [
            {"id": "mode_1p",     "label": "1P vs AI", "rect": pygame.Rect(pad_x, m_y, mw_btn, 24), "mode": "1P"},
            {"id": "mode_2p",     "label": "2P PvP",   "rect": pygame.Rect(pad_x + mw_btn + 6, m_y, mw_btn, 24), "mode": "2P"},
            {"id": "mode_aivsai", "label": "AI vs AI", "rect": pygame.Rect(pad_x + 2 * (mw_btn + 6), m_y, card_w - 2 * (mw_btn + 6), 24), "mode": "AI"},
        ]

    def set_speed(self, multiplier: float) -> None:
        """Sets game execution speed multiplier."""
        self.speed_multiplier = float(multiplier)

    def reset_match_wait_state(self) -> None:
        """Resets playback state to wait for the user to click START."""
        self.is_paused = True
        self.match_started = False
        self.human_queues = {0: None, 1: None}
        self.human_action_queued = None

    def add_combat_log(self, text: str, color: Tuple[int, int, int] = (220, 230, 245)) -> None:
        """Appends a log event to the match log feed."""
        self.combat_logs.append({"text": text, "color": color})
        if len(self.combat_logs) > 4:
            self.combat_logs.pop(0)

    def add_hit_effect(self, x: int, y: int, damaged: bool = True) -> None:
        """Triggers an animated explosion effect at cell (x, y)."""
        self.explosions.append({"x": x, "y": y, "frame": 0, "max_frames": 12})
        if damaged:
            self.damage_flashes[f"{x},{y}"] = 10
            self.add_combat_log(f"[HIT] Target hit at cell ({x}, {y}) (-1 HP)", (255, 130, 90))
        else:
            self.add_combat_log(f"[SHIELD] Own base blocked friendly shot at ({x}, {y})", (140, 190, 255))

    def add_muzzle_flash(self, x: int, y: int, direction: Direction) -> None:
        """Triggers a muzzle flash effect when tank fires."""
        self.muzzle_flashes.append({"x": x, "y": y, "dir": direction, "frame": 0, "max_frames": 8})

    def add_tank_track(self, x: int, y: int, direction: Direction) -> None:
        """Leaves fading track treads at the cell where a tank moved."""
        self.tracks.append({"x": x, "y": y, "dir": direction, "life": 120})
        if len(self.tracks) > 60:
            self.tracks.pop(0)

    def _load_discovered_external_presets(self) -> None:
        """Adds extra .py external agent files discovered in agents/external/ into the selector."""
        for fpath in AgentLoader.discover_external_agent_files():
            if os.path.basename(fpath) == "sample_rival_agent.py":
                continue
            ext_key = f"ext::{os.path.abspath(fpath)}"
            if any(k == ext_key for k, _ in self.presets):
                continue
            bot = AgentLoader.load_agent_from_file(fpath)
            if bot is not None:
                self.presets.append((ext_key, f"Ext: {bot.name[:22]}"))

    def _find_preset_idx(self, key: str) -> int:
        """Finds preset index matching `key` in self.presets."""
        for idx, (preset_key, _) in enumerate(self.presets):
            if preset_key == key:
                return idx
        return 1

    def _record_last_ai_indices(self) -> None:
        """Remembers the latest non-human algorithm preset selected for each player."""
        if self.presets[self.p0_algo_idx][0] != "human":
            self.last_p0_ai_idx = self.p0_algo_idx
        if self.presets[self.p1_algo_idx][0] != "human":
            self.last_p1_ai_idx = self.p1_algo_idx

    def _apply_mode_preset(self, mode: str) -> None:
        """Applies a 1-click game mode preset: '1P', '2P', or 'AI'."""
        self._record_last_ai_indices()
        human_idx = self._find_preset_idx("human")
        if mode == "1P":
            self.p0_algo_idx = human_idx
            if self.presets[self.p1_algo_idx][0] == "human":
                hab_idx = self._find_preset_idx("heuristic_alphabeta")
                self.p1_algo_idx = self.last_p1_ai_idx if self.presets[self.last_p1_ai_idx][0] != "human" else hab_idx
        elif mode == "2P":
            self.p0_algo_idx = human_idx
            self.p1_algo_idx = human_idx
        elif mode == "AI":
            if self.presets[self.p0_algo_idx][0] == "human":
                hab_idx = self._find_preset_idx("heuristic_alphabeta")
                self.p0_algo_idx = self.last_p0_ai_idx if self.presets[self.last_p0_ai_idx][0] != "human" else hab_idx
            if self.presets[self.p1_algo_idx][0] == "human":
                ab_idx = self._find_preset_idx("alphabeta")
                self.p1_algo_idx = self.last_p1_ai_idx if self.presets[self.last_p1_ai_idx][0] != "human" else ab_idx

        self._record_last_ai_indices()
        self.human_queues = {0: None, 1: None}
        self.agent_changed = True

    def _route_human_key(
        self,
        key: int,
        current_pid: int,
        p0_is_human: bool,
        p1_is_human: bool
    ) -> bool:
        """
        Routes keyboard actions cleanly for 1-Human vs AI or 2-Human PvP.
        Returns True if the key mapped to a valid control for an active human player.
        """
        both_humans = p0_is_human and p1_is_human

        # Player 0 Dedicated Keyset (Left side of keyboard)
        p0_map = {
            pygame.K_w: Action.MOVE_UP,
            pygame.K_s: Action.MOVE_DOWN,
            pygame.K_a: Action.MOVE_LEFT,
            pygame.K_d: Action.MOVE_RIGHT,
            pygame.K_f: Action.FIRE,
            pygame.K_SPACE: Action.FIRE,
            pygame.K_q: Action.STAY,
            pygame.K_x: Action.STAY,
        }

        # Player 1 Dedicated Keyset (Right side of keyboard, clustered around the arrow keys)
        p1_map = {
            pygame.K_UP: Action.MOVE_UP,
            pygame.K_DOWN: Action.MOVE_DOWN,
            pygame.K_LEFT: Action.MOVE_LEFT,
            pygame.K_RIGHT: Action.MOVE_RIGHT,
<<<<<<< Updated upstream
            pygame.K_SLASH: Action.FIRE,       # [/]
            pygame.K_KP0: Action.FIRE,         # [Numpad 0]
            pygame.K_RCTRL: Action.FIRE,       # [Right Ctrl]
            pygame.K_RSHIFT: Action.FIRE,      # [Right Shift]
            pygame.K_RETURN: Action.FIRE,      # [Enter]
            pygame.K_KP_ENTER: Action.FIRE,    # [Numpad Enter]
            pygame.K_PERIOD: Action.STAY,      # [.]
            pygame.K_KP_PERIOD: Action.STAY,   # [Numpad .]
            pygame.K_COMMA: Action.STAY,       # [,]
            pygame.K_BACKSLASH: Action.STAY,   # [\]
=======
            pygame.K_SLASH: Action.FIRE,       # [/]  - directly above the arrow cluster
            pygame.K_KP0: Action.FIRE,         # [Numpad 0] - for full-size keyboards
            pygame.K_RCTRL: Action.FIRE,       # [Right Ctrl] - next to LEFT arrow on laptops
            pygame.K_RETURN: Action.FIRE,      # [Enter] - convenient right hand fire
            pygame.K_RSHIFT: Action.FIRE,      # [Right Shift]
            pygame.K_PERIOD: Action.STAY,      # [.]  - right next to [/]
            pygame.K_KP_PERIOD: Action.STAY,   # [Numpad .]
            pygame.K_COMMA: Action.STAY,       # [,]
            pygame.K_RALT: Action.STAY,        # [Right Alt]
>>>>>>> Stashed changes
        }

        chosen_action = None
        if both_humans:
            if key in p0_map:
<<<<<<< Updated upstream
                self.human_queues[0] = p0_map[key]
                return True
            elif key in p1_map:
                self.human_queues[1] = p1_map[key]
                return True
        elif p0_is_human or p1_is_human:
            target_pid = 0 if p0_is_human else 1
            if key in p0_map:
                self.human_queues[target_pid] = p0_map[key]
                return True
            elif key in p1_map:
                self.human_queues[target_pid] = p1_map[key]
                return True
        return False
=======
                chosen_action = p0_map[key]
                self.human_queues[0] = chosen_action
            elif key in p1_map:
                chosen_action = p1_map[key]
                self.human_queues[1] = chosen_action
        else:
            target_pid = 0 if p0_is_human else (1 if p1_is_human else current_pid)
            if key in p0_map:
                chosen_action = p0_map[key]
                self.human_queues[target_pid] = chosen_action
            elif key in p1_map:
                chosen_action = p1_map[key]
                self.human_queues[target_pid] = chosen_action

        if chosen_action is not None:
            self.last_input_action = chosen_action
>>>>>>> Stashed changes

    def get_queued_human_action(self, pid: int) -> Optional[Action]:
        """Retrieves and clears the queued action for human player `pid`."""
        if self.human_queues.get(pid) is not None:
            act = self.human_queues[pid]
            self.human_queues[pid] = None
            self.last_human_action_time[pid] = time.perf_counter()
            return act
        if self.human_action_queued is not None:
            act = self.human_action_queued
            self.human_action_queued = None
            self.last_human_action_time[pid] = time.perf_counter()
            return act
        return None

<<<<<<< Updated upstream
    def poll_held_human_keys(
        self,
        current_pid: int,
        p0_is_human: bool,
        p1_is_human: bool
    ) -> Optional[Action]:
        """
        Polls continuously held keys for smooth, fluid tank driving without key mashing.
        Enforces a balanced per-player repeat cooldown (~160ms) so single taps move 1 cell
        while holding drives smoothly.
        """
        if not self.match_started or self.is_paused:
            return None

        now = time.perf_counter()
        repeat_interval = 0.16 / max(0.5, self.speed_multiplier)
        if now - self.last_human_action_time.get(current_pid, 0.0) < repeat_interval:
=======
    def get_held_human_move_action(
        self, pid: int, p0_is_human: bool, p1_is_human: bool
    ) -> Optional[Action]:
        """
        Polls keyboard state for held movement keys (WASD / Arrows).
        Enables ultra-smooth continuous driving without requiring frantic key mashing.
        Does NOT auto-repeat FIRE (fire must be tapped deliberately for precision).
        """
        if not PYGAME_AVAILABLE or self.screen is None:
            return None
        if self.is_paused or not self.match_started:
>>>>>>> Stashed changes
            return None

        keys = pygame.key.get_pressed()
        both_humans = p0_is_human and p1_is_human

<<<<<<< Updated upstream
        # Dedicated P0 left keys
        if (current_pid == 0 and p0_is_human) or (not both_humans and p0_is_human):
            if keys[pygame.K_w]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_UP
            if keys[pygame.K_s]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_DOWN
            if keys[pygame.K_a]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_LEFT
            if keys[pygame.K_d]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_RIGHT

        # Dedicated P1 right keys
        if (current_pid == 1 and p1_is_human) or (not both_humans and p1_is_human):
            if keys[pygame.K_UP]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_UP
            if keys[pygame.K_DOWN]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_DOWN
            if keys[pygame.K_LEFT]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_LEFT
            if keys[pygame.K_RIGHT]:
                self.last_human_action_time[current_pid] = now
                return Action.MOVE_RIGHT

        # In 1-Human vs AI, allow arrow keys for P0 or WASD for P1 as well
        if not both_humans:
            target_pid = 0 if p0_is_human else 1
            if current_pid == target_pid:
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.last_human_action_time[current_pid] = now
                    return Action.MOVE_UP
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.last_human_action_time[current_pid] = now
                    return Action.MOVE_DOWN
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.last_human_action_time[current_pid] = now
                    return Action.MOVE_LEFT
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.last_human_action_time[current_pid] = now
                    return Action.MOVE_RIGHT

        return None

    def _queue_battlefield_click(
        self,
        mx: int,
        my: int,
        button: int,
        target_pid: int
    ) -> None:
        """Queues a movement, stay, or fire action from a battlefield mouse click."""
        if button == 3:
            self.human_queues[target_pid] = Action.FIRE
            return
        if button == 1 and self.active_game_state and target_pid in self.active_game_state.tanks:
            t = self.active_game_state.tanks[target_pid]
            if t.is_alive:
                cx = mx // self.cell_size
                cy = my // self.cell_size
                if cx == t.x and cy == t.y:
                    self.human_queues[target_pid] = Action.STAY
                elif cx == t.x and cy == t.y - 1:
                    self.human_queues[target_pid] = Action.MOVE_UP
                elif cx == t.x and cy == t.y + 1:
                    self.human_queues[target_pid] = Action.MOVE_DOWN
                elif cx == t.x - 1 and cy == t.y:
                    self.human_queues[target_pid] = Action.MOVE_LEFT
                elif cx == t.x + 1 and cy == t.y:
                    self.human_queues[target_pid] = Action.MOVE_RIGHT
                else:
                    tdx, tdy = t.direction.value
                    in_line = (tdx != 0 and cy == t.y and (cx - t.x) * tdx > 0) or (tdy != 0 and cx == t.x and (cy - t.y) * tdy > 0)
                    if in_line:
                        self.human_queues[target_pid] = Action.FIRE
                    else:
                        off_x = cx - t.x
                        off_y = cy - t.y
                        if abs(off_x) > abs(off_y):
                            self.human_queues[target_pid] = Action.MOVE_RIGHT if off_x > 0 else Action.MOVE_LEFT
                        else:
                            self.human_queues[target_pid] = Action.MOVE_DOWN if off_y > 0 else Action.MOVE_UP

=======
        if both_humans:
            if pid == 0:
                if keys[pygame.K_w]: return Action.MOVE_UP
                if keys[pygame.K_s]: return Action.MOVE_DOWN
                if keys[pygame.K_a]: return Action.MOVE_LEFT
                if keys[pygame.K_d]: return Action.MOVE_RIGHT
            elif pid == 1:
                if keys[pygame.K_UP]: return Action.MOVE_UP
                if keys[pygame.K_DOWN]: return Action.MOVE_DOWN
                if keys[pygame.K_LEFT]: return Action.MOVE_LEFT
                if keys[pygame.K_RIGHT]: return Action.MOVE_RIGHT
        else:
            # 1-Human vs AI: Player can use WASD OR Arrow keys freely
            if keys[pygame.K_w] or keys[pygame.K_UP]: return Action.MOVE_UP
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: return Action.MOVE_DOWN
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: return Action.MOVE_LEFT
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: return Action.MOVE_RIGHT

        return None

>>>>>>> Stashed changes
    def handle_events(
        self,
        active_player_is_human: bool = False,
        current_pid: int = 0,
        p0_is_human: bool = False,
        p1_is_human: bool = False
    ) -> bool:
        """Processes mouse clicks, keyboard controls, and window events."""
        if not PYGAME_AVAILABLE or self.screen is None:
            return True

        if self.quit_requested:
            return False

        self.step_requested = False
        self.undo_requested = False
        self.restart_requested = False
        self.map_requested = False
        self.map_prev_requested = False

        any_human = p0_is_human or p1_is_human or active_player_is_human
        is_terminal = bool(self.active_game_state and self.active_game_state.is_terminal())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_p:
                    if is_terminal:
                        self.restart_requested = True
                    else:
                        self.is_paused = not self.is_paused
                        if not self.is_paused:
                            self.match_started = True
                elif event.key == pygame.K_SPACE:
                    if is_terminal:
                        self.restart_requested = True
                    elif not any_human or not self.match_started or self.is_paused:
                        self.is_paused = not self.is_paused
                        if not self.is_paused:
                            self.match_started = True
                            self.add_combat_log("[START] Match running.", (46, 204, 113))
                    else:
                        self._route_human_key(event.key, current_pid, p0_is_human, p1_is_human)
                elif event.key in (pygame.K_u, pygame.K_z, pygame.K_BACKSPACE):
                    self.undo_requested = True
                    self.is_paused = True
                    self.step_requested = False
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if is_terminal:
                        self.restart_requested = True
                    elif not self.match_started or self.is_paused:
                        self.is_paused = False
                        self.match_started = True
                        self.add_combat_log("[RESUME] Match running.", (46, 204, 113))
                    elif any_human:
                        self._route_human_key(event.key, current_pid, p0_is_human, p1_is_human)
                elif event.key == pygame.K_r:
                    self.restart_requested = True
                elif event.key == pygame.K_m and not (p1_is_human and self.match_started and not self.is_paused):
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.map_prev_requested = True
                    else:
                        self.map_requested = True
                elif event.key == pygame.K_n and not (any_human and self.match_started and not self.is_paused):
                    self.map_prev_requested = True
                elif event.key == pygame.K_1:
                    self.set_speed(0.5)
                elif event.key == pygame.K_2:
                    self.set_speed(1.0)
                elif event.key == pygame.K_3:
                    self.set_speed(2.0)
                elif event.key == pygame.K_4:
                    self.set_speed(4.0)
                elif event.key == pygame.K_t:
                    self.tactical_assist_enabled = not getattr(self, "tactical_assist_enabled", True)
                    status_lbl = "ENABLED" if self.tactical_assist_enabled else "DISABLED"
                    self.add_combat_log(f"[TACTICAL SIGHT] {status_lbl}", self.COLOR_CYAN)
                else:
                    if any_human and not is_terminal:
                        if not self.match_started or self.is_paused:
                            if self._route_human_key(event.key, current_pid, p0_is_human, p1_is_human):
                                self.match_started = True
                                self.is_paused = False
                                self.add_combat_log("[RESUME] Match running.", (46, 204, 113))
                        else:
                            self._route_human_key(event.key, current_pid, p0_is_human, p1_is_human)
                    elif (not any_human or not active_player_is_human) and not is_terminal and event.key == pygame.K_s:
                        self.step_requested = True
                        self.is_paused = True
                        self.match_started = True

<<<<<<< Updated upstream
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                mx, my = event.pos

                # Game Over Modal buttons (click directly on Victory/Draw card)
                if is_terminal and event.button == 1 and self.gameover_buttons:
                    for gbtn in self.gameover_buttons:
                        if gbtn["rect"].collidepoint(mx, my):
                            gid = gbtn["id"]
                            if gid == "go_restart":
                                self.restart_requested = True
                            elif gid == "go_undo":
                                self.undo_requested = True
                                self.is_paused = True
                                self.step_requested = False
                            elif gid == "go_next_map":
                                self.map_requested = True
                            return True

                # Check floating START banner on battlefield before battlefield actions
                if event.button == 1 and not self.match_started and not is_terminal and self.start_banner_rect and self.start_banner_rect.collidepoint(mx, my):
                    self.match_started = True
                    self.is_paused = False
                    self.add_combat_log("[START] Match started! Tanks engaging.", (46, 204, 113))
                    return True

                # Check Battlefield Click (Direct Tactical Mouse Navigation + Auto-Start)
                if mx < self.board_w and my < self.board_h:
                    if any_human and not is_terminal:
                        if not self.match_started or self.is_paused:
                            self.match_started = True
                            self.is_paused = False
                            self.add_combat_log("[RESUME] Match running.", (46, 204, 113))
                        target_pid = current_pid if (current_pid == 0 and p0_is_human) or (current_pid == 1 and p1_is_human) else (0 if p0_is_human else 1)
                        self._queue_battlefield_click(mx, my, event.button, target_pid)
                        return True
=======
                # Also handle SPACE for firing when match IS started and not paused
                if event.key == pygame.K_SPACE and any_human and self.match_started and not self.is_paused:
                    self._route_human_key(event.key, current_pid, p0_is_human, p1_is_human)

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if 0 <= mx < self.board_w and 0 <= my < self.board_h:
                    self.hover_board_cell = (mx // self.cell_size, my // self.cell_size)
                else:
                    self.hover_board_cell = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                mx, my = event.pos

                # Check battlefield grid clicks for direct interactive tank control
                if 0 <= mx < self.board_w and 0 <= my < self.board_h:
                    if not self.match_started:
                        self.match_started = True
                        self.is_paused = False
                        self.add_combat_log("[START] Match engaged via battlefield click.", (46, 204, 113))
                        return True
                    elif active_player_is_human and not self.is_paused and getattr(self, "last_state", None):
                        tank = self.last_state.tanks.get(current_pid)
                        if tank and tank.is_alive:
                            cx = mx // self.cell_size
                            cy = my // self.cell_size
                            dx = cx - tank.x
                            dy = cy - tank.y

                            if event.button == 3:  # Right-click anywhere on battlefield -> STAY
                                self.human_queues[current_pid] = Action.STAY
                                self.last_input_action = Action.STAY
                                return True
                            elif dx == 0 and dy == 0:  # Click on tank -> FIRE
                                self.human_queues[current_pid] = Action.FIRE
                                self.last_input_action = Action.FIRE
                                return True
                            elif (tank.direction == Direction.UP and dx == 0 and dy < 0) or \
                                 (tank.direction == Direction.DOWN and dx == 0 and dy > 0) or \
                                 (tank.direction == Direction.LEFT and dy == 0 and dx < 0) or \
                                 (tank.direction == Direction.RIGHT and dy == 0 and dx > 0):
                                # Clicked along line of fire -> FIRE
                                self.human_queues[current_pid] = Action.FIRE
                                self.last_input_action = Action.FIRE
                                return True
                            elif dx == 0 and dy == -1:
                                self.human_queues[current_pid] = Action.MOVE_UP
                                self.last_input_action = Action.MOVE_UP
                                return True
                            elif dx == 0 and dy == 1:
                                self.human_queues[current_pid] = Action.MOVE_DOWN
                                self.last_input_action = Action.MOVE_DOWN
                                return True
                            elif dx == -1 and dy == 0:
                                self.human_queues[current_pid] = Action.MOVE_LEFT
                                self.last_input_action = Action.MOVE_LEFT
                                return True
                            elif dx == 1 and dy == 0:
                                self.human_queues[current_pid] = Action.MOVE_RIGHT
                                self.last_input_action = Action.MOVE_RIGHT
                                return True
                            else:
                                if abs(dx) >= abs(dy):
                                    act = Action.MOVE_RIGHT if dx > 0 else Action.MOVE_LEFT
                                else:
                                    act = Action.MOVE_DOWN if dy > 0 else Action.MOVE_UP
                                self.human_queues[current_pid] = act
                                self.last_input_action = act
                                return True
>>>>>>> Stashed changes

                # Top-right Map Badge click (Left-click = Next Map, Right-click = Prev Map)
                if self.map_badge_rect and self.map_badge_rect.collidepoint(mx, my):
                    if event.button == 3:
                        self.map_prev_requested = True
                    else:
                        self.map_requested = True
                    return True

                if event.button == 3:
                    for btn in self.buttons:
                        if btn["id"] == "next_map" and btn["rect"].collidepoint(mx, my):
                            self.map_prev_requested = True
                            return True
                    self._handle_selector_clicks(mx, my, button=3)
                    continue

                # Top action buttons
                for btn in self.buttons:
                    if btn["rect"].collidepoint(mx, my):
                        b_id = btn["id"]
                        if b_id == "play_pause":
                            if is_terminal:
                                self.restart_requested = True
                            else:
                                self.is_paused = not self.is_paused
                                if not self.is_paused:
                                    self.match_started = True
                                    self.add_combat_log("[START] Match running.", (46, 204, 113))
                                else:
                                    self.add_combat_log("[PAUSE] Match paused.", (245, 190, 35))
                        elif b_id == "step":
                            if not is_terminal:
                                self.step_requested = True
                                self.is_paused = True
                                self.match_started = True
                        elif b_id == "undo":
                            self.undo_requested = True
                            self.is_paused = True
                            self.step_requested = False
                        elif b_id == "restart":
                            self.restart_requested = True
                        elif b_id == "next_map":
                            self.map_requested = True

                # Speed buttons
                for sbtn in self.speed_buttons:
                    if sbtn["rect"].collidepoint(mx, my):
                        self.set_speed(sbtn["val"])

                # 1-Click Mode Preset buttons
                for mbtn in self.mode_buttons:
                    if mbtn["rect"].collidepoint(mx, my):
                        self._apply_mode_preset(mbtn["mode"])

                # On-screen D-Pad buttons for human
                for dbtn in self.dpad_buttons:
                    if dbtn["rect"].collidepoint(mx, my):
                        if not self.match_started or self.is_paused:
                            self.match_started = True
                            self.is_paused = False
                        target_pid = current_pid if (current_pid == 0 and p0_is_human) or (current_pid == 1 and p1_is_human) else (0 if p0_is_human else 1)
                        self.human_queues[target_pid] = dbtn["action"]

                # Algorithm & Depth selectors
                self._handle_selector_clicks(mx, my, button=1)

        return True

    def register_external_agent(self, pid: int, file_path: str) -> bool:
        """Loads an external .py bot file, registers it in self.presets, and assigns it to player pid."""
        loaded = AgentLoader.load_agent_from_file(file_path)
        if loaded is None:
            self.add_combat_log("[EXT] Failed to load bot (must inherit from BaseAgent).", (255, 110, 90))
            return False

        abs_path = os.path.abspath(file_path)
        ext_key = f"ext::{abs_path}"
        label = f"Ext: {loaded.name[:22]}"

        found_idx = None
        for idx, (k, _) in enumerate(self.presets):
            if k == ext_key:
                found_idx = idx
                self.presets[idx] = (ext_key, label)
                break
        if found_idx is None:
            self.presets.append((ext_key, label))
            found_idx = len(self.presets) - 1

        if pid == 0:
            self.p0_algo_idx = found_idx
        else:
            self.p1_algo_idx = found_idx

        self._record_last_ai_indices()
        self.agent_changed = True
        self.add_combat_log(f"[EXT] P{pid} loaded '{loaded.name}'.", self.COLOR_GOLD)
        return True

    def _open_external_bot_dialog(self, pid: int) -> None:
        """Opens a file chooser dialog to import an external student bot (.py) into player pid."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            picked = filedialog.askopenfilename(
                title=f"Import External Agent (.py) for Player {pid}",
                initialdir=AgentLoader.DEFAULT_EXTERNAL_DIR,
                filetypes=[("Python Agent Files", "*.py"), ("All Files", "*.*")],
            )
            root.destroy()
            if picked:
                self.register_external_agent(pid, picked)
        except Exception as exc:
            self.add_combat_log(f"[EXT] File dialog unavailable ({exc}); use --load_external.", (255, 150, 90))

    def _handle_selector_clicks(self, mx: int, my: int, button: int = 1) -> None:
        """Handles clicking algorithm switchers [<] [>] / capsule, depth [-] [+], and [+ .PY] load buttons."""
        n_presets = len(self.presets)
        if button == 3:
            if hasattr(self, "p0_algo_capsule_rect") and self.p0_algo_capsule_rect.collidepoint(mx, my):
                self.p0_algo_idx = (self.p0_algo_idx - 1) % n_presets
                self._record_last_ai_indices()
                self.agent_changed = True
            elif hasattr(self, "p1_algo_capsule_rect") and self.p1_algo_capsule_rect.collidepoint(mx, my):
                self.p1_algo_idx = (self.p1_algo_idx - 1) % n_presets
                self._record_last_ai_indices()
                self.agent_changed = True
            return

        if hasattr(self, "p0_load_ext_rect") and self.p0_load_ext_rect.collidepoint(mx, my):
            self._open_external_bot_dialog(0)
            return
        elif hasattr(self, "p1_load_ext_rect") and self.p1_load_ext_rect.collidepoint(mx, my):
            self._open_external_bot_dialog(1)
            return

        if hasattr(self, "p0_algo_prev_rect") and self.p0_algo_prev_rect.collidepoint(mx, my):
            self.p0_algo_idx = (self.p0_algo_idx - 1) % n_presets
            self._record_last_ai_indices()
            self.agent_changed = True
        elif hasattr(self, "p0_algo_next_rect") and self.p0_algo_next_rect.collidepoint(mx, my):
            self.p0_algo_idx = (self.p0_algo_idx + 1) % n_presets
            self._record_last_ai_indices()
            self.agent_changed = True
        elif hasattr(self, "p0_algo_capsule_rect") and self.p0_algo_capsule_rect.collidepoint(mx, my):
            self.p0_algo_idx = (self.p0_algo_idx + 1) % n_presets
            self._record_last_ai_indices()
            self.agent_changed = True
        elif hasattr(self, "p0_depth_dec_rect") and self.p0_depth_dec_rect.collidepoint(mx, my):
            if self.p0_depth > 1:
                self.p0_depth -= 1
                self.agent_changed = True
        elif hasattr(self, "p0_depth_inc_rect") and self.p0_depth_inc_rect.collidepoint(mx, my):
            if self.p0_depth < 5:
                self.p0_depth += 1
                self.agent_changed = True
        elif hasattr(self, "p1_algo_prev_rect") and self.p1_algo_prev_rect.collidepoint(mx, my):
            self.p1_algo_idx = (self.p1_algo_idx - 1) % n_presets
            self._record_last_ai_indices()
            self.agent_changed = True
        elif hasattr(self, "p1_algo_next_rect") and self.p1_algo_next_rect.collidepoint(mx, my):
            self.p1_algo_idx = (self.p1_algo_idx + 1) % n_presets
            self._record_last_ai_indices()
            self.agent_changed = True
        elif hasattr(self, "p1_algo_capsule_rect") and self.p1_algo_capsule_rect.collidepoint(mx, my):
            self.p1_algo_idx = (self.p1_algo_idx + 1) % n_presets
            self._record_last_ai_indices()
            self.agent_changed = True
        elif hasattr(self, "p1_depth_dec_rect") and self.p1_depth_dec_rect.collidepoint(mx, my):
            if self.p1_depth > 1:
                self.p1_depth -= 1
                self.agent_changed = True
        elif hasattr(self, "p1_depth_inc_rect") and self.p1_depth_inc_rect.collidepoint(mx, my):
            if self.p1_depth < 5:
                self.p1_depth += 1
                self.agent_changed = True

    def get_selected_agent_key(self, pid: int) -> Tuple[str, int]:
        """Returns (algo_name, depth) for the specified player."""
        if pid == 0:
            return self.presets[self.p0_algo_idx][0], self.p0_depth
        else:
            return self.presets[self.p1_algo_idx][0], self.p1_depth

    def _match_or_register_preset(self, agent: BaseAgent) -> int:
        """Maps an active BaseAgent instance cleanly to its preset index (registering external bots)."""
        if getattr(agent, "is_human", False):
            return self._find_preset_idx("human")

        cls_to_key = {
            "HumanAgent": "human",
            "HeuristicAlphaBetaAgent": "heuristic_alphabeta",
            "IterativeDeepeningAgent": "id_ab",
            "AlphaBetaAgent": "alphabeta",
            "HeuristicMinimaxAgent": "heuristic_minimax",
            "MinimaxAgent": "minimax",
            "GreedyTacticalAgent": "greedy",
        }
        cls_name = type(agent).__name__
        if cls_name in cls_to_key:
            return self._find_preset_idx(cls_to_key[cls_name])

        ext_path = getattr(agent, "external_file_path", None)
        if ext_path:
            abs_path = os.path.abspath(ext_path)
            if os.path.basename(abs_path) == "sample_rival_agent.py":
                return self._find_preset_idx("rival")
            key = f"ext::{abs_path}"
            label = f"Ext: {agent.name[:22]}"
        elif cls_name == "RivalGroupAgent":
            return self._find_preset_idx("rival")
        else:
            key = f"custom::{cls_name}"
            label = f"Bot: {agent.name[:22]}"

        for idx, (k, _) in enumerate(self.presets):
            if k == key:
                return idx
        self.presets.append((key, label))
        return len(self.presets) - 1

    def set_agent_presets_from_agents(self, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """Syncs GUI selector indices to match active agents accurately."""
        self.p0_algo_idx = self._match_or_register_preset(agent0)
        self.p1_algo_idx = self._match_or_register_preset(agent1)

        self._record_last_ai_indices()

        if hasattr(agent0, "depth"):
            self.p0_depth = agent0.depth
        elif hasattr(agent0, "max_depth"):
            self.p0_depth = agent0.max_depth

        if hasattr(agent1, "depth"):
            self.p1_depth = agent1.depth
        elif hasattr(agent1, "max_depth"):
            self.p1_depth = agent1.max_depth

<<<<<<< Updated upstream
    def _pump_during_animation(self, next_pid: int, agent0: BaseAgent, agent1: BaseAgent) -> bool:
        """
        Pumps events during animations so human controls feel instantaneous and hotkeys remain responsive.
        Returns False if the user closed the window or hit ESC.
        """
        p0_h = getattr(agent0, "is_human", False)
        p1_h = getattr(agent1, "is_human", False)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_requested = True
                    return False
                elif event.key == pygame.K_p:
                    self.is_paused = not self.is_paused
                elif (p0_h or p1_h):
                    self._route_human_key(event.key, next_pid, p0_h, p1_h)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                mx, my = event.pos
                if mx < self.board_w and my < self.board_h and (p0_h or p1_h):
                    target_pid = next_pid if (next_pid == 0 and p0_h) or (next_pid == 1 and p1_h) else (0 if p0_h else 1)
                    self._queue_battlefield_click(mx, my, event.button, target_pid)
                elif p0_h or p1_h:
                    target_pid = next_pid if (next_pid == 0 and p0_h) or (next_pid == 1 and p1_h) else (0 if p0_h else 1)
                    for dbtn in self.dpad_buttons:
                        if dbtn["rect"].collidepoint(mx, my):
                            self.human_queues[target_pid] = dbtn["action"]

=======
    def _pump_during_animation(self, current_pid: int, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """Captures human inputs during animations so gameplay feels super responsive and never lags."""
        p0_h = getattr(agent0, "is_human", False)
        p1_h = getattr(agent1, "is_human", False)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.should_quit = True
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.should_quit = True
                    return
                elif event.key == pygame.K_p:
                    self.is_paused = not self.is_paused
                elif event.key == pygame.K_1:
                    self.set_speed(0.5)
                elif event.key == pygame.K_2:
                    self.set_speed(1.0)
                elif event.key == pygame.K_3:
                    self.set_speed(2.0)
                elif event.key == pygame.K_4:
                    self.set_speed(4.0)
                elif p0_h or p1_h:
                    self._route_human_key(event.key, current_pid, p0_h, p1_h)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for sbtn in self.speed_buttons:
                    if sbtn["rect"].collidepoint(mx, my):
                        self.set_speed(sbtn["val"])
                if p0_h or p1_h:
                    for dbtn in self.dpad_buttons:
                        if dbtn["rect"].collidepoint(mx, my):
                            self.human_queues[current_pid] = dbtn["action"]
>>>>>>> Stashed changes
        pygame.event.pump()
        return True

    def animate_turn(
        self,
        state: GameState,
        action: Action,
        agent0: BaseAgent,
        agent1: BaseAgent
    ) -> GameState:
        """
        Executes a turn with smooth tank movement interpolation and cell-by-cell bullet flight.
<<<<<<< Updated upstream
        Dynamically paced: Snappy, fluid, and responsive when a human is playing,
        with obstacle bump recoil and eased trajectory interpolation.
=======
        Dynamically optimized: snappy and responsive for Human players, cinematic for AI.
>>>>>>> Stashed changes
        """
        next_state = state.clone()
        player_id = next_state.current_player
        tank = next_state.tanks.get(player_id)
        cs = self.cell_size
        any_human = getattr(agent0, "is_human", False) or getattr(agent1, "is_human", False)

        p0_h = getattr(agent0, "is_human", False)
        p1_h = getattr(agent1, "is_human", False)
        any_human = p0_h or p1_h

        # Optimized human animation speeds: snappy, crisp, responsive
        if any_human:
            move_frames = max(3, int(7 / self.speed_multiplier))
            frames_per_cell = max(2, int(4 / self.speed_multiplier))
            fire_pause_frames = max(2, int(4 / self.speed_multiplier))
            stay_frames = max(2, int(3 / self.speed_multiplier))
            explosion_frames = max(2, int(4 / self.speed_multiplier))
        else:
            move_frames = max(3, int(12 / self.speed_multiplier))
            frames_per_cell = max(3, int(9 / self.speed_multiplier))
            fire_pause_frames = max(2, int(7 / self.speed_multiplier))
            stay_frames = max(2, int(5 / self.speed_multiplier))
            explosion_frames = max(2, int(6 / self.speed_multiplier))

        # Phase 1: Apply Tank Action with smooth visual interpolation
        if action == Action.FIRE:
            if tank and tank.is_alive:
                self.add_muzzle_flash(tank.x, tank.y, tank.direction)
<<<<<<< Updated upstream
            fire_pause_frames = max(1, int((2 if any_human else 4) / self.speed_multiplier))
=======
            GameRules._fire_bullet(next_state, player_id)
>>>>>>> Stashed changes
            for _ in range(fire_pause_frames):
                if self.should_quit:
                    return next_state
                self.render(next_state, agent0, agent1, is_interpolating=True)
                if not self._pump_during_animation(1 - player_id, agent0, agent1):
                    return next_state
                self.clock.tick(self.fps)
            GameRules._fire_bullet(next_state, player_id)

        elif action == Action.STAY:
<<<<<<< Updated upstream
            stay_frames = max(1, int((2 if any_human else 5) / self.speed_multiplier))
=======
>>>>>>> Stashed changes
            for _ in range(stay_frames):
                if self.should_quit:
                    return next_state
                self.render(next_state, agent0, agent1, is_interpolating=True)
                if not self._pump_during_animation(1 - player_id, agent0, agent1):
                    return next_state
                self.clock.tick(self.fps)

        else:
            direction = Action.get_move_direction(action)
            if direction and tank and tank.is_alive:
                old_x, old_y = tank.x, tank.y
                prev_bullet_count = len([b for b in next_state.bullets if b.is_active])
                GameRules._move_tank(next_state, player_id, direction)
                new_x, new_y = tank.x, tank.y
                stepped_on_bullet = len(next_state.bullets) < prev_bullet_count

<<<<<<< Updated upstream
                if new_x == old_x and new_y == old_y:
                    # Obstacle bump recoil animation (fast 3-frame tactile feedback)
                    dx, dy = direction.value
                    bump_frames = max(2, int((3 if any_human else 5) / self.speed_multiplier))
                    for f in range(1, bump_frames + 1):
                        bump_mag = int(math.sin(f / bump_frames * math.pi) * 3)
                        self.animated_tank_override[player_id] = (old_x * cs + dx * bump_mag, old_y * cs + dy * bump_mag, tank.direction)
                        self.render(next_state, agent0, agent1, is_interpolating=True)
                        if not self._pump_during_animation(1 - player_id, agent0, agent1):
                            self.animated_tank_override.clear()
                            return next_state
                        self.clock.tick(self.fps)
                    self.animated_tank_override.clear()
                else:
                    self.add_tank_track(old_x, old_y, tank.direction)
                    move_frames = max(2, int((7 if any_human else 12) / self.speed_multiplier))
                    start_px, start_py = old_x * cs, old_y * cs
                    end_px, end_py = new_x * cs, new_y * cs

                    for f in range(1, move_frames + 1):
                        # Smooth sine ease-out interpolation
                        alpha = math.sin((f / move_frames) * (math.pi / 2))
=======
                start_px, start_py = old_x * cs, old_y * cs
                end_px, end_py = new_x * cs, new_y * cs

                # If blocked (wall/base/boundary collision), execute snappy micro-bump recoil
                if new_x == old_x and new_y == old_y:
                    bump_frames = max(2, int(4 / self.speed_multiplier))
                    dx, dy = direction.value
                    for f in range(1, bump_frames + 1):
                        if self.should_quit:
                            return next_state
                        bump_mag = 4.0 * math.sin((f / bump_frames) * math.pi)
                        cur_px = int(start_px + dx * bump_mag)
                        cur_py = int(start_py + dy * bump_mag)
                        self.animated_tank_override[player_id] = (cur_px, cur_py, tank.direction)
                        self.render(next_state, agent0, agent1, is_interpolating=True)
                        self._pump_during_animation(1 - player_id, agent0, agent1)
                        self.clock.tick(self.fps)
                    self.animated_tank_override.clear()
                else:
                    # Smooth ease-out glide to target cell
                    for f in range(1, move_frames + 1):
                        if self.should_quit:
                            return next_state
                        prog = f / move_frames
                        alpha = math.sin(prog * math.pi * 0.5)
>>>>>>> Stashed changes
                        cur_px = int(start_px + (end_px - start_px) * alpha)
                        cur_py = int(start_py + (end_py - start_py) * alpha)
                        self.animated_tank_override[player_id] = (cur_px, cur_py, tank.direction)
                        self.render(next_state, agent0, agent1, is_interpolating=True)
<<<<<<< Updated upstream
                        if not self._pump_during_animation(1 - player_id, agent0, agent1):
                            self.animated_tank_override.clear()
                            return next_state
                        self.clock.tick(self.fps)

                    self.animated_tank_override.clear()
                    if stepped_on_bullet:
                        self.add_hit_effect(new_x, new_y, damaged=True)

        # Phase 2: Realistic Cell-by-Cell Bullet Flight (uses exact GameRules collision helper)
        frames_per_cell = max(2, int((5 if any_human else 10) / self.speed_multiplier))
        self.animating_owner_id = player_id

=======
                        self._pump_during_animation(1 - player_id, agent0, agent1)
                        self.clock.tick(self.fps)
                    self.animated_tank_override.clear()

        # Phase 2: Realistic Cell-by-Cell Bullet Flight (3 cells per cycle)
>>>>>>> Stashed changes
        for _ in range(Bullet.SPEED):
            active_bullets = [
                b for b in next_state.bullets if b.is_active and b.owner_id == player_id
            ]
            if not active_bullets:
                break

            bullet_paths = []
            for b in active_bullets:
                dx, dy = b.direction.value
                start_px = b.x * cs + cs // 2
                start_py = b.y * cs + cs // 2
                target_x = b.x + dx
                target_y = b.y + dy
                target_px = target_x * cs + cs // 2
                target_py = target_y * cs + cs // 2
                bullet_paths.append({
                    "start": (start_px, start_py),
                    "target": (target_px, target_py),
                    "dir": b.direction,
                    "owner": b.owner_id
                })

            for f in range(1, frames_per_cell + 1):
                if self.should_quit:
                    return next_state
                alpha = f / frames_per_cell
                self.animated_bullets = []
                for bp in bullet_paths:
                    curr_x = int(bp["start"][0] + (bp["target"][0] - bp["start"][0]) * alpha)
                    curr_y = int(bp["start"][1] + (bp["target"][1] - bp["start"][1]) * alpha)
                    self.animated_bullets.append({
                        "px": curr_x,
                        "py": curr_y,
                        "dir": bp["dir"],
                        "owner": bp["owner"]
                    })

                self.render(next_state, agent0, agent1, is_interpolating=True)
                if not self._pump_during_animation(1 - player_id, agent0, agent1):
                    self.animating_owner_id = None
                    self.animated_bullets.clear()
                    return next_state
                self.clock.tick(self.fps)

            self.animated_bullets.clear()
            hits = GameRules.step_bullets_one_cell(next_state, active_owner=player_id)
            for hx, hy, damaged in hits:
                self.add_hit_effect(hx, hy, damaged=damaged)

<<<<<<< Updated upstream
        self.animating_owner_id = None

        # Animate any hit explosions briefly so the user sees the impact
        if self.explosions:
            exp_frames = max(2, int((3 if any_human else 6) / self.speed_multiplier))
            for _ in range(exp_frames):
=======
            # Check cell arrival collisions (Wall, Tank, Base)
            for bp in bullet_paths:
                b = bp["bullet"]
                tx, ty = bp["target_cell"]
                b.x = tx
                b.y = ty

                if not (0 <= b.x < next_state.width and 0 <= b.y < next_state.height):
                    b.is_active = False
                    continue

                hit = False
                if (b.x, b.y) in next_state.walls:
                    w = next_state.walls[(b.x, b.y)]
                    if w.is_alive:
                        w.take_damage(1)
                        b.is_active = False
                        hit = True
                        self.add_hit_effect(b.x, b.y)
                        self.screen_shake = max(self.screen_shake, 3)

                if not hit:
                    for target_tank in next_state.tanks.values():
                        if (target_tank.is_alive and
                            target_tank.x == b.x and
                            target_tank.y == b.y and
                            target_tank.player_id != b.owner_id):
                            target_tank.take_damage(1)
                            b.is_active = False
                            hit = True
                            self.add_hit_effect(b.x, b.y)
                            self.screen_shake = max(self.screen_shake, 4)
                            break

                if not hit:
                    for target_base in next_state.bases.values():
                        if (target_base.is_alive and
                            target_base.x == b.x and
                            target_base.y == b.y):
                            target_base.take_damage(1)
                            b.is_active = False
                            hit = True
                            self.add_hit_effect(b.x, b.y)
                            self.screen_shake = max(self.screen_shake, 4)
                            break

            next_state.bullets = [b for b in next_state.bullets if b.is_active]

        # Animate any hit explosions briefly so the user sees the impact
        if self.explosions:
            for _ in range(explosion_frames):
                if self.should_quit:
                    return next_state
                self.render(next_state, agent0, agent1, is_interpolating=True)
                self._pump_during_animation(1 - player_id, agent0, agent1)
                self.clock.tick(self.fps)
>>>>>>> Stashed changes
                self.render(next_state, agent0, agent1, is_interpolating=True)
                if not self._pump_during_animation(1 - player_id, agent0, agent1):
                    return next_state
                self.clock.tick(self.fps)

        # Phase 3: Cleanup dead walls and advance turn identically to GameRules.apply_action
        GameRules.finish_turn(next_state, player_id)
        self.last_human_action_time[player_id] = time.perf_counter()

        return next_state

    def render(
        self,
        state: GameState,
        agent0: BaseAgent,
        agent1: BaseAgent,
        is_interpolating: bool = False
    ) -> None:
        """Main draw routine rendering battlefield, entities, particles, and clean HUD."""
        if not PYGAME_AVAILABLE or self.screen is None:
            return

        self.active_game_state = state

        # Adaptive layout safeguard: auto-update layout if state dimensions changed
        if not is_interpolating:
            if getattr(self, "_last_map_dim", None) != (state.width, state.height):
                self.update_map_layout(state.width, state.height)

        self.anim_tick += 1
        self.eval_score = self.evaluator.evaluate(state, player_id=0)

        # 1. Render Battlefield Ground & Grid
        self._render_battlefield(state)

        # 2. Render Entities (Walls, Bases, Tanks, Foliage)
        self._render_entities(state, agent0, agent1, is_interpolating=is_interpolating)

        # 3. Render In-Flight Bullets
        self._render_bullets(state)

        # 4. Render Particles (Treads, Muzzle Flashes, Hit Explosions)
        self._render_particles()

        # 5. Render Ready-to-Start Overlay if match hasn't started yet
        if not self.match_started and not state.is_terminal():
            self._render_start_overlay()
        else:
            self.start_banner_rect = None

        # 6. Render Clean Match Action Log underneath grid
        self._render_combat_log(state)

        # 7. Render Game-Over Modal if Terminal
        if state.is_terminal():
            self._render_game_over_banner(state, agent0, agent1)
        else:
            self.gameover_buttons.clear()

        # 8. Render Redesigned Sidebar HUD
        self._render_hud(state, agent0, agent1)

        # Update damage flashes
        for k in list(self.damage_flashes.keys()):
            self.damage_flashes[k] -= 1
            if self.damage_flashes[k] <= 0:
                del self.damage_flashes[k]

        pygame.display.flip()
        if not is_interpolating:
            self.clock.tick(self.fps)

    def _render_start_overlay(self) -> None:
        """Draws a clickable 'READY TO START' banner in the center of the battlefield before match start."""
        bw = min(380, max(220, self.board_w - 40))
        bh = 46
        bx = (self.board_w - bw) // 2
        by = (self.board_h - bh) // 2

        self.start_banner_rect = pygame.Rect(bx, by, bw, bh)
        mx, my = pygame.mouse.get_pos()
        is_hover = self.start_banner_rect.collidepoint(mx, my)

        bg_col = (28, 145, 90) if is_hover else (20, 115, 72)
        pygame.draw.rect(self.screen, (10, 14, 22), pygame.Rect(bx + 3, by + 3, bw, bh), border_radius=8)
        pygame.draw.rect(self.screen, bg_col, self.start_banner_rect, border_radius=8)
        pygame.draw.rect(self.screen, (80, 235, 145), self.start_banner_rect, 2, border_radius=8)

        txt_str = "CLICK HERE OR [START] TO BEGIN MATCH"
        txt = self.font_large.render(txt_str, True, (255, 255, 255))
        if txt.get_width() > bw - 20:
            txt = self.font_bold.render("CLICK HERE OR [START] TO BEGIN", True, (255, 255, 255))
        if txt.get_width() > bw - 20:
            txt = self.font_bold.render("CLICK TO START", True, (255, 255, 255))
        self.screen.blit(txt, (bx + (bw - txt.get_width()) // 2, by + (bh - txt.get_height()) // 2))

    def _render_battlefield(self, state: GameState) -> None:
        """Draws textured sand terrain tiles with subtle tactical coordinates."""
        cs = self.cell_size
        sand_img = self.sprites.get("tile_sand")
        sand_img2 = self.sprites.get("tile_sand2")

        frame_rect = pygame.Rect(0, 0, self.board_w, self.board_h)
        pygame.draw.rect(self.screen, self.COLOR_BG, frame_rect)

        for x in range(state.width):
            for y in range(state.height):
                px = x * cs
                py = y * cs
                if sand_img:
                    img = sand_img2 if ((x + y) % 5 == 0 and sand_img2) else sand_img
                    self.screen.blit(img, (px, py))
                else:
                    color = (218, 192, 145) if (x + y) % 2 == 0 else (210, 182, 135)
                    pygame.draw.rect(self.screen, color, (px, py, cs, cs))

                pygame.draw.rect(self.screen, (0, 0, 0, 30), (px, py, cs, cs), 1)

                if y == 0:
                    lbl = self.font_coord.render(str(x), True, (130, 110, 80))
                    self.screen.blit(lbl, (px + 3, 2))
                if x == 0:
                    lbl = self.font_coord.render(str(y), True, (130, 110, 80))
                    self.screen.blit(lbl, (3, py + 3))

    def _render_combat_log(self, state: GameState) -> None:
        """Renders a clean, readable match action log underneath the battlefield."""
        log_x = 0
        log_y = self.board_h
        log_w = self.board_w
        log_h = self.height_px - self.board_h

        if log_h <= 10:
            return

        pygame.draw.rect(self.screen, (14, 18, 26), (log_x, log_y, log_w, log_h))
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (log_x, log_y), (log_w, log_y), 2)

        hdr_title = self.font_metric_lbl.render("RECENT MATCH EVENTS & TURN LOG", True, self.COLOR_GOLD)
        self.screen.blit(hdr_title, (log_x + 14, log_y + 8))

        line_y = log_y + 28
        max_lines = max(1, min(6, (log_h - 32) // 20))
        for item in self.combat_logs[-max_lines:]:
            line_surf = self.font.render(item["text"], True, item["color"])
            self.screen.blit(line_surf, (log_x + 14, line_y))
            line_y += 20

    def _render_entities(self, state: GameState, agent0: BaseAgent = None, agent1: BaseAgent = None, is_interpolating: bool = False) -> None:
        """Renders bases, walls, tanks (with smooth position override and turn indicator), and foliage."""
        cs = self.cell_size

        tank_angle_map = {
            Direction.UP: 180,
            Direction.DOWN: 0,
            Direction.LEFT: 270,
            Direction.RIGHT: 90,
        }

        # 1. Base Command Citadels ("Cứ điểm")
        for pid, base in state.bases.items():
            if base.is_alive:
                bx = base.x * cs
                by = base.y * cs
                center_x = bx + cs // 2
                center_y = by + cs // 2
                base_color = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY
                hp_ratio = base.hp / 9.0
                flash_active = f"{base.x},{base.y}" in self.damage_flashes

                # Animated perimeter shield glow around the Citadel
                pulse_a = int(65 + 45 * math.sin(self.anim_tick * 0.12))
                shield_col = (
                    base_color if hp_ratio > 0.55
                    else (self.COLOR_HP_YELLOW if hp_ratio > 0.3 else self.COLOR_HP_RED)
                )
                aura_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                pygame.draw.rect(aura_surf, (*shield_col, pulse_a), (0, 0, cs, cs), border_radius=8)
                self.screen.blit(aura_surf, (bx, by))

                # Citadel Sprite (Fortified Bastion with 4 Corner Turrets & Central Golden Star)
                base_key = f"base_{pid}"
                if base_key in self.sprites and self.sprites[base_key]:
                    self.screen.blit(self.sprites[base_key], (bx + 2, by + 2))
                else:
                    pygame.draw.rect(self.screen, (28, 36, 50), (bx + 2, by + 2, cs - 4, cs - 4), border_radius=6)
                    pygame.draw.circle(self.screen, (20, 60, 110) if pid == 0 else (120, 25, 25), (center_x, center_y), cs // 2 - 5)

                # Outer armored frame
                pygame.draw.rect(self.screen, shield_col, (bx + 1, by + 1, cs - 2, cs - 2), 2, border_radius=7)

                if flash_active:
                    flash_surf = pygame.Surface((cs - 4, cs - 4), pygame.SRCALPHA)
                    flash_surf.fill((255, 255, 255, 135))
                    self.screen.blit(flash_surf, (bx + 2, by + 2))

                # Unclipped Top 9-Plate Citadel Shield Bar (3x3 Bastion Tiers inside top edge of cell)
                self._draw_citadel_board_hp_bar(bx + 3, by + 2, cs - 6, base.hp, 9, base_color)

                # Sleek Bottom Tactical Crest Plate ("HQ 0" / "HQ 1") leaving Central Star unobstructed
                hq_tag = self.font_coord.render(f"HQ {pid}", True, (255, 255, 255))
                tag_w = hq_tag.get_width() + 8
                tag_h = 12
                tag_rect = pygame.Rect(center_x - tag_w // 2, by + cs - tag_h - 1, tag_w, tag_h)
                pygame.draw.rect(self.screen, (14, 19, 28), tag_rect, border_radius=3)
                pygame.draw.rect(self.screen, shield_col, tag_rect, 1, border_radius=3)
                self.screen.blit(hq_tag, (tag_rect.centerx - hq_tag.get_width() // 2, tag_rect.y - 1))

        # 2. Destructible Walls (3 HP Metal, 2 HP Wood Crate, 1 HP Sandbag)
        for (wx, wy), wall in state.walls.items():
            if wall.is_alive:
                rx = wx * cs + 2
                ry = wy * cs + 2
                sprite_key = f"wall_{wall.hp}"
                flash_active = f"{wx},{wy}" in self.damage_flashes

                if sprite_key in self.sprites and self.sprites[sprite_key]:
                    self.screen.blit(self.sprites[sprite_key], (rx, ry))
                else:
                    w_color = (self.COLOR_WALL if wall.hp == 3 else ((145, 75, 45) if wall.hp == 2 else self.COLOR_WALL_CRACK))
                    pygame.draw.rect(self.screen, w_color, (rx, ry, cs - 4, cs - 4), border_radius=4)

                if flash_active:
                    flash_surf = pygame.Surface((cs - 4, cs - 4), pygame.SRCALPHA)
                    flash_surf.fill((255, 255, 255, 120))
                    self.screen.blit(flash_surf, (rx, ry))

                # Color-coded mini armor badge for obstacle HP (3=Metal Cyan, 2=Wood Gold, 1=Sandbag Orange)
                badge_border = (
                    (90, 200, 255) if wall.hp == 3
                    else ((245, 195, 45) if wall.hp == 2 else (245, 125, 65))
                )
                b_rect = pygame.Rect(rx + cs - 17, ry + cs - 17, 13, 13)
                pygame.draw.rect(self.screen, (14, 18, 26), b_rect, border_radius=3)
                pygame.draw.rect(self.screen, badge_border, b_rect, 1, border_radius=3)
                badge = self.font_coord.render(str(wall.hp), True, badge_border)
                self.screen.blit(badge, (b_rect.centerx - badge.get_width() // 2, b_rect.centery - badge.get_height() // 2 - 1))

        # 3. Tanks
        for pid, tank in state.tanks.items():
            if tank.is_alive:
                if pid in self.animated_tank_override:
                    tx, ty, t_dir = self.animated_tank_override[pid]
                else:
                    tx, ty, t_dir = tank.x * cs, tank.y * cs, tank.direction

                center_x = tx + cs // 2
                center_y = ty + cs // 2
                t_color = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY
                is_active_turn = (state.current_player == pid and not state.is_terminal())
                agent_obj = agent0 if pid == 0 else agent1
                is_human_player = getattr(agent_obj, "is_human", False)

                # Highlight ring (pulsing when it's this tank's turn)
                ring_surf = pygame.Surface((cs + 8, cs + 8), pygame.SRCALPHA)
                if is_active_turn and self.match_started:
                    pulse_alpha = int(140 + 90 * math.sin(self.anim_tick * 0.15))
                    pygame.draw.circle(ring_surf, (*t_color, pulse_alpha), (cs // 2 + 4, cs // 2 + 4), cs // 2 + 1, 3)
                else:
                    pygame.draw.circle(ring_surf, (*t_color, 75), (cs // 2 + 4, cs // 2 + 4), cs // 2 - 2, 2)
                self.screen.blit(ring_surf, (tx - 4, ty - 4))

                tank_key = f"tank_{pid}"
                if tank_key in self.sprites and self.sprites[tank_key]:
                    angle = tank_angle_map.get(t_dir, 0)
                    rot_sprite = pygame.transform.rotate(self.sprites[tank_key], angle)
                    r_rect = rot_sprite.get_rect(center=(center_x, center_y))
                    self.screen.blit(rot_sprite, r_rect.topleft)
                else:
                    pygame.draw.circle(self.screen, t_color, (center_x, center_y), cs // 2 - 4)

                self._draw_segmented_hp_bar(tx + 4, ty - 2, tank.hp, 6, seg_w=5, seg_h=4, color=t_color)

                # Tactical Laser Aim Line & Mouse Reticle for Human Players
                if not is_interpolating and is_human_player and not state.is_terminal():
                    self._check_and_draw_threat_warning(state, tank, pid, cs)
                    if is_active_turn and self.match_started and not self.is_paused:
                        self._draw_tactical_aim_line(state, tank, pid, cs)
                        self._draw_mouse_hover_controls(state, tank, pid, cs)

                # Floating Turn Indicator for Human Players
                if not is_interpolating and is_active_turn and self.match_started and is_human_player:
                    tag_surf = self.font_badge.render(f"P{pid} TURN", True, (255, 255, 255))
                    tw = tag_surf.get_width() + 8
                    th = 15
                    tag_rect = pygame.Rect(center_x - tw // 2, ty + cs - 2, tw, th)
                    pygame.draw.rect(self.screen, t_color, tag_rect, border_radius=3)
                    self.screen.blit(tag_surf, (tag_rect.x + 4, tag_rect.y + 1))

        # 4. Foliage Canopy
        if hasattr(state, "foliage"):
            for (fx, fy) in state.foliage:
                px = fx * cs
                py = fy * cs
                tree_img = self.sprites.get("tree")
                if tree_img:
                    self.screen.blit(tree_img, (px + 1, py + 1))
                else:
                    f_surf = pygame.Surface((cs - 4, cs - 4), pygame.SRCALPHA)
                    pygame.draw.circle(f_surf, (46, 125, 50, 200), (cs // 2 - 2, cs // 2 - 2), cs // 2 - 4)
                    self.screen.blit(f_surf, (px + 2, py + 2))

    def _check_and_draw_threat_warning(self, state: GameState, tank, pid: int, cs: int) -> None:
        """Draws a pulsing hazard border and alert badge if the opponent tank has line of sight."""
        opp_id = 1 - pid
        opp_tank = state.tanks.get(opp_id)
        if not opp_tank or not opp_tank.is_alive:
            return

        odx, ody = opp_tank.direction.value
        rx, ry = opp_tank.x + odx, opp_tank.y + ody
        targeted = False
        while 0 <= rx < state.width and 0 <= ry < state.height:
            if rx == tank.x and ry == tank.y:
                targeted = True
                break
            if (rx, ry) in state.walls and state.walls[(rx, ry)].is_alive:
                break
            if any(b.x == rx and b.y == ry and b.is_alive for b in state.bases.values()):
                break
            rx += odx
            ry += ody

        if targeted:
            pulse_a = int(140 + 90 * math.sin(self.anim_tick * 0.25))
            warn_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
            pygame.draw.rect(warn_surf, (255, 50, 50, pulse_a), (0, 0, cs, cs), 2, border_radius=4)
            self.screen.blit(warn_surf, (tank.x * cs, tank.y * cs))

            alert_lbl = self.font_coord.render("! DANGER", True, (255, 230, 230))
            aw = alert_lbl.get_width() + 6
            ar = pygame.Rect(tank.x * cs + cs // 2 - aw // 2, tank.y * cs - 14, aw, 13)
            pygame.draw.rect(self.screen, (200, 30, 30), ar, border_radius=2)
            self.screen.blit(alert_lbl, (ar.x + 3, ar.y))

    def _draw_tactical_aim_line(self, state: GameState, tank, pid: int, cs: int) -> None:
        """
        Draws a high-tech tactical laser line from tank muzzle to first collision object,
        with impact reticle indicating whether it hits an enemy, wall, or base.
        """
        dx, dy = tank.direction.value
        cx = tank.x * cs + cs // 2
        cy = tank.y * cs + cs // 2

        muzzle_x = cx + dx * (cs // 2 - 2)
        muzzle_y = cy + dy * (cs // 2 - 2)

        tx = tank.x + dx
        ty = tank.y + dy
        hit_type = "boundary"
        hit_cell = (tx, ty)

        while 0 <= tx < state.width and 0 <= ty < state.height:
            hit_cell = (tx, ty)
            if (tx, ty) in state.walls and state.walls[(tx, ty)].is_alive:
                hit_type = "wall"
                break
            if any(b.x == tx and b.y == ty and b.is_alive for b_id, b in state.bases.items() if b_id != pid):
                hit_type = "enemy_base"
                break
            if any(b.x == tx and b.y == ty and b.is_alive for b_id, b in state.bases.items() if b_id == pid):
                hit_type = "own_base"
                break
            if any(t.x == tx and t.y == ty and t.is_alive for t_id, t in state.tanks.items() if t_id != pid):
                hit_type = "enemy_tank"
                break
            tx += dx
            ty += dy

        end_px = hit_cell[0] * cs + cs // 2
        end_py = hit_cell[1] * cs + cs // 2

        if hit_type in ("enemy_tank", "enemy_base"):
            laser_col = (255, 60, 60)
            glow_col = (255, 120, 120)
        elif hit_type == "wall":
            laser_col = (56, 189, 248)
            glow_col = (140, 225, 255)
        elif hit_type == "own_base":
            laser_col = (230, 80, 80)
            glow_col = (255, 140, 140)
        else:
            laser_col = (56, 189, 248)
            glow_col = (140, 225, 255)

        pulse_alpha = int(120 + 80 * math.sin(self.anim_tick * 0.2))
        laser_surf = pygame.Surface((self.board_w, self.board_h), pygame.SRCALPHA)
        pygame.draw.line(laser_surf, (*glow_col, pulse_alpha // 2), (muzzle_x, muzzle_y), (end_px, end_py), 3)
        pygame.draw.line(laser_surf, (*laser_col, pulse_alpha), (muzzle_x, muzzle_y), (end_px, end_py), 1)
        self.screen.blit(laser_surf, (0, 0))

        rx = hit_cell[0] * cs
        ry = hit_cell[1] * cs
        if 0 <= hit_cell[0] < state.width and 0 <= hit_cell[1] < state.height:
            ret_rect = pygame.Rect(rx + 4, ry + 4, cs - 8, cs - 8)
            pygame.draw.rect(self.screen, laser_col, ret_rect, 1, border_radius=4)
            pygame.draw.line(self.screen, laser_col, (end_px - 8, end_py), (end_px + 8, end_py), 1)
            pygame.draw.line(self.screen, laser_col, (end_px, end_py - 8), (end_px, end_py + 8), 1)

            if hit_type in ("enemy_tank", "enemy_base"):
                badge = self.font_coord.render("TARGET LOCK", True, (255, 255, 255))
                b_w = badge.get_width() + 6
                b_r = pygame.Rect(end_px - b_w // 2, ry - 14, b_w, 13)
                pygame.draw.rect(self.screen, (220, 40, 40), b_r, border_radius=2)
                self.screen.blit(badge, (b_r.x + 3, b_r.y))

    def _is_cell_blocked_for_tank(self, state: GameState, nx: int, ny: int, pid: int) -> bool:
        """Checks whether cell (nx, ny) is blocked by a wall, base, or opponent tank."""
        if not (0 <= nx < state.width and 0 <= ny < state.height):
            return True
        if (nx, ny) in state.walls and state.walls[(nx, ny)].is_alive:
            return True
        if any(b.x == nx and b.y == ny and b.is_alive for b in state.bases.values()):
            return True
        opp_tank = state.tanks.get(1 - pid)
        if opp_tank and opp_tank.is_alive and opp_tank.x == nx and opp_tank.y == ny:
            return True
        return False

    def _draw_hover_pill(self, cell_rect: pygame.Rect, text: str, bg_color: Tuple[int, int, int] = (16, 22, 34)) -> None:
        """Draws a clamped action badge centered over `cell_rect`."""
        lbl_surf = self.font_coord.render(text, True, (255, 255, 255))
        lw = lbl_surf.get_width() + 8
        pill_x = max(4, min(self.board_w - lw - 4, cell_rect.centerx - lw // 2))
        pill_y = max(4, min(self.board_h - 18, cell_rect.centery - 7))
        lr = pygame.Rect(pill_x, pill_y, lw, 14)
        pygame.draw.rect(self.screen, bg_color, lr, border_radius=3)
        self.screen.blit(lbl_surf, (lr.x + 4, lr.y))

    def _draw_mouse_hover_controls(self, state: GameState, tank, pid: int, cs: int) -> None:
        """
        Renders tactical hover indicators across the battlefield:
        - Adjacent open cells -> MOVE <DIR>
        - Adjacent blocked cells -> AIM <DIR> (rotates turret)
        - Own tank cell -> STAY
        - Cells along current line of fire -> CLICK TO FIRE!
        - Remote cells -> STEP <DIR>
        """
        mx, my = pygame.mouse.get_pos()
        if not (0 <= mx < self.board_w and 0 <= my < self.board_h):
            return

        hover_x = mx // cs
        hover_y = my // cs
        if not (0 <= hover_x < state.width and 0 <= hover_y < state.height):
            return

        neighbors = [
            (tank.x, tank.y - 1, "UP"),
            (tank.x, tank.y + 1, "DOWN"),
            (tank.x - 1, tank.y, "LEFT"),
            (tank.x + 1, tank.y, "RIGHT"),
        ]

        team_col = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY

        for nx, ny, label in neighbors:
            if hover_x == nx and hover_y == ny:
                cell_rect = pygame.Rect(nx * cs + 2, ny * cs + 2, cs - 4, cs - 4)
                is_blocked = self._is_cell_blocked_for_tank(state, nx, ny, pid)
                box_col = team_col
                h_surf = pygame.Surface((cs - 4, cs - 4), pygame.SRCALPHA)
                pygame.draw.rect(h_surf, (*box_col, 80), (0, 0, cs - 4, cs - 4), border_radius=4)
                self.screen.blit(h_surf, (cell_rect.x, cell_rect.y))
                pygame.draw.rect(self.screen, box_col, cell_rect, 2, border_radius=4)
                pill_text = f"AIM {label}" if is_blocked else f"MOVE {label}"
                self._draw_hover_pill(cell_rect, pill_text)
                return

        if hover_x == tank.x and hover_y == tank.y:
            cell_rect = pygame.Rect(tank.x * cs + 2, tank.y * cs + 2, cs - 4, cs - 4)
            pygame.draw.rect(self.screen, team_col, cell_rect, 2, border_radius=4)
            self._draw_hover_pill(cell_rect, "STAY")
            return

        cell_rect = pygame.Rect(hover_x * cs + 2, hover_y * cs + 2, cs - 4, cs - 4)
        tdx, tdy = tank.direction.value
        in_line = (tdx != 0 and hover_y == tank.y and (hover_x - tank.x) * tdx > 0) or (tdy != 0 and hover_x == tank.x and (hover_y - tank.y) * tdy > 0)
        if in_line:
            fire_col = (235, 65, 65)
            h_surf = pygame.Surface((cs - 4, cs - 4), pygame.SRCALPHA)
            pygame.draw.rect(h_surf, (*fire_col, 70), (0, 0, cs - 4, cs - 4), border_radius=4)
            self.screen.blit(h_surf, (cell_rect.x, cell_rect.y))
            pygame.draw.rect(self.screen, fire_col, cell_rect, 2, border_radius=4)
            pygame.draw.line(self.screen, fire_col, (cell_rect.centerx - 8, cell_rect.centery), (cell_rect.centerx + 8, cell_rect.centery), 1)
            pygame.draw.line(self.screen, fire_col, (cell_rect.centerx, cell_rect.centery - 8), (cell_rect.centerx, cell_rect.centery + 8), 1)
            self._draw_hover_pill(cell_rect, "CLICK TO FIRE!", bg_color=(180, 32, 32))
        else:
            off_x = hover_x - tank.x
            off_y = hover_y - tank.y
            if abs(off_x) > abs(off_y):
                step_dir = "RIGHT" if off_x > 0 else "LEFT"
            else:
                step_dir = "DOWN" if off_y > 0 else "UP"
            h_surf = pygame.Surface((cs - 4, cs - 4), pygame.SRCALPHA)
            pygame.draw.rect(h_surf, (*team_col, 45), (0, 0, cs - 4, cs - 4), border_radius=4)
            self.screen.blit(h_surf, (cell_rect.x, cell_rect.y))
            pygame.draw.rect(self.screen, team_col, cell_rect, 1, border_radius=4)
            self._draw_hover_pill(cell_rect, f"STEP {step_dir}")

    def _render_bullets(self, state: GameState) -> None:
        """Renders bullets either at interpolated flight positions or static cell positions."""
        cs = self.cell_size
        bullet_angle_map = {
            Direction.UP: 0,
            Direction.DOWN: 180,
            Direction.LEFT: 90,
            Direction.RIGHT: 270,
        }

        if self.animated_bullets:
            for ab in self.animated_bullets:
                bx = ab["px"]
                by = ab["py"]
                owner = ab["owner"]
                b_key = f"bullet_{owner}"

                dx, dy = ab["dir"].value
                tail_len = int(cs * 0.45)
                trail_color = (90, 200, 255) if owner == 0 else (255, 100, 80)
                pygame.draw.line(self.screen, (*trail_color, 160), (bx, by), (bx - dx * tail_len, by - dy * tail_len), 3)

                if b_key in self.sprites and self.sprites[b_key]:
                    angle = bullet_angle_map.get(ab["dir"], 0)
                    rot_b = pygame.transform.rotate(self.sprites[b_key], angle)
                    r_rect = rot_b.get_rect(center=(bx, by))
                    self.screen.blit(rot_b, r_rect.topleft)
                else:
                    pygame.draw.circle(self.screen, (255, 255, 255), (bx, by), 5)
                    pygame.draw.circle(self.screen, trail_color, (bx, by), 3)

        for bullet in state.bullets:
            if self.animated_bullets and bullet.owner_id == self.animating_owner_id:
                continue
            if bullet.is_active:
                bx = bullet.x * cs + cs // 2
                by = bullet.y * cs + cs // 2
                dx, dy = bullet.direction.value

                tail_len = cs // 2
                tx_end = bx - dx * tail_len
                ty_end = by - dy * tail_len
                b_color = (90, 200, 255) if bullet.owner_id == 0 else (255, 100, 80)
                pygame.draw.line(self.screen, (*b_color, 140), (bx, by), (tx_end, ty_end), 3)

                b_key = f"bullet_{bullet.owner_id}"
                if b_key in self.sprites and self.sprites[b_key]:
                    angle = bullet_angle_map.get(bullet.direction, 0)
                    rot_b = pygame.transform.rotate(self.sprites[b_key], angle)
                    b_rect = rot_b.get_rect(center=(bx, by))
                    self.screen.blit(rot_b, b_rect.topleft)
                else:
                    pygame.draw.circle(self.screen, (255, 255, 255), (bx, by), 5)
                    pygame.draw.circle(self.screen, b_color, (bx, by), 3)

    def _render_particles(self) -> None:
        """Renders smoke explosions, muzzle flashes, and tank tread tracks."""
        cs = self.cell_size
        bullet_angle_map = {
            Direction.UP: 0,
            Direction.DOWN: 180,
            Direction.LEFT: 90,
            Direction.RIGHT: 270,
        }

        active_tracks = []
        for tr in self.tracks:
            tr["life"] -= 1
            if tr["life"] > 0:
                px = tr["x"] * cs + cs // 4
                py = tr["y"] * cs + cs // 4
                tr_img = self.sprites.get("track")
                if tr_img:
                    alpha = min(200, tr["life"] * 2)
                    tr_copy = tr_img.copy()
                    tr_copy.set_alpha(alpha)
                    self.screen.blit(tr_copy, (px, py))
                active_tracks.append(tr)
        self.tracks = active_tracks

        active_flashes = []
        for mf in self.muzzle_flashes:
            mf["frame"] += 1
            if mf["frame"] < mf["max_frames"]:
                dx, dy = mf["dir"].value
                cx = mf["x"] * cs + cs // 2 + int(dx * cs * 0.45)
                cy = mf["y"] * cs + cs // 2 + int(dy * cs * 0.45)
                flash_img = self.sprites.get("shot_flash")
                if flash_img:
                    angle = bullet_angle_map.get(mf["dir"], 0)
                    rot_f = pygame.transform.rotate(flash_img, angle)
                    r = rot_f.get_rect(center=(cx, cy))
                    self.screen.blit(rot_f, r.topleft)
                else:
                    pygame.draw.circle(self.screen, (255, 200, 50), (cx, cy), 8)
                active_flashes.append(mf)
        self.muzzle_flashes = active_flashes

        active_exp = []
        for exp in self.explosions:
            exp["frame"] += 1
            frame_idx = exp["frame"]
            if frame_idx <= exp["max_frames"]:
                px = exp["x"] * cs - 3
                py = exp["y"] * cs - 3
                exp_step = min(5, max(1, int(frame_idx / exp["max_frames"] * 5) + 1))
                exp_key = f"exp_{exp_step}"

                if exp_key in self.sprites and self.sprites[exp_key]:
                    self.screen.blit(self.sprites[exp_key], (px, py))
                else:
                    r = int((frame_idx / exp["max_frames"]) * (cs // 2))
                    pygame.draw.circle(self.screen, (255, 120, 30), (px + cs // 2, py + cs // 2), r)
                active_exp.append(exp)
        self.explosions = active_exp

    def _draw_segmented_hp_bar(
        self, x: int, y: int, hp: int, max_hp: int,
        seg_w: int, seg_h: int, color
    ) -> None:
        """Draws discrete health bar pips above in-game entities."""
        gap = 1
        total_w = max_hp * (seg_w + gap) + 2
        pygame.draw.rect(self.screen, (16, 20, 28), (x - 1, y - 1, total_w, seg_h + 2), border_radius=2)

        for i in range(max_hp):
            sx = x + i * (seg_w + gap)
            if i < hp:
                ratio = hp / max_hp
                pip_c = color if ratio > 0.5 else (self.COLOR_HP_YELLOW if ratio > 0.25 else self.COLOR_HP_RED)
                pygame.draw.rect(self.screen, pip_c, (sx, y, seg_w, seg_h), border_radius=1)
            else:
                pygame.draw.rect(self.screen, (34, 42, 56), (sx, y, seg_w, seg_h), border_radius=1)

    def _draw_citadel_board_hp_bar(
        self, x: int, y: int, total_w: int, hp: int, max_hp: int, color
    ) -> None:
        """
        Draws a fortified 9-plate Citadel shield bar grouped into 3 tiers of 3 HP
        inside the top edge of the Base HQ cell (never clips off-screen at y=0).
        """
        bar_h = 6
        pygame.draw.rect(self.screen, (12, 16, 24), (x - 1, y - 1, total_w + 2, bar_h + 2), border_radius=2)
        pygame.draw.rect(self.screen, (52, 66, 90), (x - 1, y - 1, total_w + 2, bar_h + 2), 1, border_radius=2)

        ratio = hp / max(1, max_hp)
        pip_c = color if ratio > 0.55 else (self.COLOR_HP_YELLOW if ratio > 0.3 else self.COLOR_HP_RED)
        hi_c = (
            min(255, pip_c[0] + 55),
            min(255, pip_c[1] + 55),
            min(255, pip_c[2] + 55),
        )

        # 9 pips with 1px gap and 3px tier divider after pip 3 and pip 6
        seg_w = max(2, (total_w - 12) // max_hp)
        used_w = seg_w * max_hp + 12
        cur_x = x + (total_w - used_w) // 2
        for i in range(max_hp):
            if i in (3, 6):
                pygame.draw.line(self.screen, self.COLOR_GOLD, (cur_x + 1, y), (cur_x + 1, y + bar_h - 1), 1)
                cur_x += 3
            if i < hp:
                pygame.draw.rect(self.screen, pip_c, (cur_x, y, seg_w, bar_h), border_radius=1)
                pygame.draw.line(self.screen, hi_c, (cur_x, y), (cur_x + seg_w - 1, y), 1)
            else:
                pygame.draw.rect(self.screen, (28, 35, 48), (cur_x, y, seg_w, bar_h), border_radius=1)
            cur_x += seg_w + 1

    def _draw_clean_hp_box(
        self, x: int, y: int, w: int, h: int,
        label: str, hp: int, max_hp: int, color
    ) -> None:
        """Draws a clean, armored Tank Health box with 6 beveled armor plates."""
        box_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BG, box_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, box_rect, 1, border_radius=6)

        lbl_surf = self.font_metric_lbl.render(label, True, self.COLOR_TEXT_DIM)
        self.screen.blit(lbl_surf, (x + 8, y + 5))

        ratio = max(0.0, min(1.0, hp / max(1, max_hp)))
        bar_col = color if ratio > 0.5 else (self.COLOR_HP_YELLOW if ratio > 0.25 else self.COLOR_HP_RED)
        val_str = f"{hp}/{max_hp} HP" if hp > 0 else "DESTROYED"
        val_surf = self.font_bold.render(val_str, True, bar_col if hp > 0 else self.COLOR_HP_RED)
        self.screen.blit(val_surf, (x + w - val_surf.get_width() - 8, y + 4))

        # 6 Segmented Tank Armor Plates
        bar_x = x + 8
        bar_y = y + h - 14
        bar_w = w - 16
        bar_h = 8
        pygame.draw.rect(self.screen, (12, 16, 24), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=3)

        gap = 3
        seg_w = (bar_w - gap * (max_hp - 1)) // max_hp
        hi_col = (min(255, bar_col[0] + 50), min(255, bar_col[1] + 50), min(255, bar_col[2] + 50))
        for i in range(max_hp):
            sx = bar_x + i * (seg_w + gap)
            sw = seg_w if i < max_hp - 1 else (bar_x + bar_w - sx)
            if i < hp:
                pygame.draw.rect(self.screen, bar_col, (sx, bar_y, sw, bar_h), border_radius=2)
                pygame.draw.line(self.screen, hi_col, (sx + 1, bar_y + 1), (sx + sw - 2, bar_y + 1), 1)
            else:
                pygame.draw.rect(self.screen, (26, 33, 46), (sx, bar_y, sw, bar_h), border_radius=2)

    def _draw_citadel_hp_box(
        self, x: int, y: int, w: int, h: int,
        hp: int, max_hp: int, color, pid: int = 0
    ) -> None:
        """
        Draws a custom-designed Fortified Command Base ('Cứ điểm') Health Box:
        - Double-beveled bunker frame with 4 metallic corner bastion brackets
        - Mini Golden Command Star shield emblem + 'BASE HQ HEALTH' header
        - Pill-framed HP readout badge
        - 9-Plate Citadel Armor Bar organized into 3 Bastion Tiers ([■■■ | ■■■ | ■■■])
        """
        box_rect = pygame.Rect(x, y, w, h)
        ratio = max(0.0, min(1.0, hp / max(1, max_hp)))
        bar_col = color if ratio > 0.55 else (self.COLOR_HP_YELLOW if ratio > 0.3 else self.COLOR_HP_RED)
        border_col = (75, 95, 130) if ratio > 0.55 else bar_col

        # 1. Fortified Bunker Background & Inner Frame
        pygame.draw.rect(self.screen, (13, 18, 28), box_rect, border_radius=6)
        pygame.draw.rect(self.screen, border_col, box_rect, 1, border_radius=6)

        # 2. Four L-Shaped Corner Bastion Brackets (Fortress Reinforcement Accents)
        blen = 6
        b_accent = self.COLOR_GOLD if hp > 0 else self.COLOR_HP_RED
        # Top-Left
        pygame.draw.line(self.screen, b_accent, (x, y + 2), (x, y + blen), 2)
        pygame.draw.line(self.screen, b_accent, (x + 2, y), (x + blen, y), 2)
        # Top-Right
        pygame.draw.line(self.screen, b_accent, (x + w - 1, y + 2), (x + w - 1, y + blen), 2)
        pygame.draw.line(self.screen, b_accent, (x + w - 1 - blen, y), (x + w - 3, y), 2)
        # Bottom-Left
        pygame.draw.line(self.screen, b_accent, (x, y + h - 1 - blen), (x, y + h - 3), 2)
        pygame.draw.line(self.screen, b_accent, (x + 2, y + h - 1), (x + blen, y + h - 1), 2)
        # Bottom-Right
        pygame.draw.line(self.screen, b_accent, (x + w - 1, y + h - 1 - blen), (x + w - 1, y + h - 3), 2)
        pygame.draw.line(self.screen, b_accent, (x + w - 1 - blen, y + h - 1), (x + w - 3, y + h - 1), 2)

        # 3. Mini Citadel Shield & Golden 5-Pointed Command Star Emblem
        emblem_cx = x + 13
        emblem_cy = y + 12
        pygame.draw.circle(self.screen, (24, 34, 52), (emblem_cx, emblem_cy), 6)
        pygame.draw.circle(self.screen, color, (emblem_cx, emblem_cy), 6, 1)
        self._draw_star_polygon(self.screen, emblem_cx, emblem_cy, 4.5, 2.0, self.COLOR_GOLD)

        # 4. Header Title & Fortified HP Pill Badge
        lbl_surf = self.font_metric_lbl.render("BASE HQ HEALTH", True, (220, 230, 248))
        self.screen.blit(lbl_surf, (x + 23, y + 5))

        val_str = f"{hp}/{max_hp} HP" if hp > 0 else "DESTROYED"
        val_surf = self.font_badge.render(val_str, True, (255, 255, 255) if hp > 0 else self.COLOR_HP_RED)
        pw = val_surf.get_width() + 10
        ph = 15
        pill_rect = pygame.Rect(x + w - pw - 6, y + 4, pw, ph)
        pill_bg = (24, 42, 66) if (pid == 0 and hp > 6) else ((64, 24, 30) if (pid == 1 and hp > 6) else (48, 34, 18))
        pygame.draw.rect(self.screen, pill_bg, pill_rect, border_radius=3)
        pygame.draw.rect(self.screen, bar_col, pill_rect, 1, border_radius=3)
        self.screen.blit(val_surf, (pill_rect.centerx - val_surf.get_width() // 2, pill_rect.y + 1))

        # 5. 9-Plate Citadel Armor Trough (3 Bastion Tiers of 3 HP: [■■■ | ■■■ | ■■■])
        trough_x = x + 7
        trough_y = y + h - 15
        trough_w = w - 14
        trough_h = 10
        pygame.draw.rect(self.screen, (9, 12, 19), (trough_x, trough_y, trough_w, trough_h), border_radius=3)
        pygame.draw.rect(self.screen, (40, 52, 74), (trough_x, trough_y, trough_w, trough_h), 1, border_radius=3)

        inner_y = trough_y + 2
        inner_h = trough_h - 4
        avail_w = trough_w - 6
        # 6 normal 2px gaps (12px) + 2 bastion tier dividers (6px each = 12px) = 24px total spacing
        seg_w = max(8, (avail_w - 24) // max_hp)
        used_w = seg_w * max_hp + 24
        cx_pos = trough_x + (trough_w - used_w) // 2
        hi_col = (min(255, bar_col[0] + 65), min(255, bar_col[1] + 65), min(255, bar_col[2] + 65))

        for i in range(max_hp):
            if i in (3, 6):
                # Bastion Tier Structural Divider
                div_x = cx_pos + 2
                pygame.draw.line(self.screen, self.COLOR_GOLD, (div_x, trough_y + 1), (div_x, trough_y + trough_h - 2), 2)
                cx_pos += 6

            plate_rect = pygame.Rect(cx_pos, inner_y, seg_w, inner_h)
            if i < hp:
                pygame.draw.rect(self.screen, bar_col, plate_rect, border_radius=1)
                pygame.draw.line(self.screen, hi_col, (cx_pos + 1, inner_y), (cx_pos + seg_w - 2, inner_y), 1)
            else:
                pygame.draw.rect(self.screen, (22, 28, 40), plate_rect, border_radius=1)
                pygame.draw.rect(self.screen, (34, 42, 58), plate_rect, 1, border_radius=1)

            cx_pos += seg_w + 2

    def _draw_clean_metric_box(
        self, x: int, y: int, w: int, h: int,
        label: str, value_str: str, value_color
    ) -> None:
        """Draws a clean, uncluttered technical metric box with bold value readout."""
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BG, rect, border_radius=5)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, rect, 1, border_radius=5)

        lbl_surf = self.font_metric_lbl.render(label, True, self.COLOR_TEXT_DIM)
        val_surf = self.font_metric_val.render(value_str, True, value_color)
        self.screen.blit(lbl_surf, (x + 8, y + 5))
        self.screen.blit(val_surf, (x + 8, y + 20))

    def _render_hud(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """Renders the redesigned, clean sidebar dashboard."""
        sidebar_x = self.board_w
        sidebar_rect = (sidebar_x, 0, self.sidebar_width, self.height_px)
        pygame.draw.rect(self.screen, self.COLOR_SIDEBAR_BG, sidebar_rect)
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (sidebar_x, 0), (sidebar_x, self.height_px), 2)

        pad_x = sidebar_x + 16
        card_w = self.sidebar_width - 32
        curr_y = 12

        # 1. Header Banner & Map Badge
        title_surf = self.font_title.render("TANK BATTLE AI", True, self.COLOR_TEXT)
        self.screen.blit(title_surf, (pad_x, curr_y))

        clean_name = self.current_map_title.replace(".txt", "").replace("_", " ").upper()
        if len(clean_name) > 20:
            clean_name = clean_name[:19] + ".."
        map_surf = self.font_coord.render(f"MAP: {clean_name}", True, self.COLOR_GOLD)
        mb_w = map_surf.get_width() + 14
        mb_rect = pygame.Rect(pad_x + card_w - mb_w, curr_y + 1, mb_w, 22)
        self.map_badge_rect = mb_rect
        mx, my = pygame.mouse.get_pos()
        mb_hover = mb_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (42, 54, 78) if mb_hover else (28, 36, 52), mb_rect, border_radius=4)
        pygame.draw.rect(self.screen, (255, 225, 95) if mb_hover else self.COLOR_GOLD, mb_rect, 1, border_radius=4)
        self.screen.blit(map_surf, (mb_rect.x + 7, mb_rect.y + 4))

        curr_y += 28

        # 2. Cycle Counter & Match Status Pill
        cycle_txt = self.font_bold.render(f"Cycle: {state.game_cycle} / {state.max_cycles}", True, self.COLOR_TEXT_DIM)
        self.screen.blit(cycle_txt, (pad_x, curr_y))

        active_agent = agent0 if state.current_player == 0 else agent1
        active_is_human = getattr(active_agent, "is_human", False)

        if state.is_terminal():
            status_text = "GAME OVER"
            status_c = (190, 45, 45)
        elif not self.match_started:
            status_text = "READY - PRESS START"
            status_c = (22, 135, 85)
        elif self.is_paused:
            status_text = "PAUSED - PRESS ENTER"
            status_c = self.COLOR_AMBER
        elif active_is_human:
            status_text = f"P{state.current_player} HUMAN TURN"
            status_c = self.COLOR_P0_PRIMARY if state.current_player == 0 else self.COLOR_P1_PRIMARY
        else:
            status_text = f"P{state.current_player} AI TURN"
            status_c = self.COLOR_P0_PRIMARY if state.current_player == 0 else self.COLOR_P1_PRIMARY

        pill_surf = self.font_badge.render(status_text, True, (255, 255, 255))
        pill_w = pill_surf.get_width() + 14
        pill_rect = (pad_x + card_w - pill_w, curr_y - 1, pill_w, 20)
        pygame.draw.rect(self.screen, status_c, pill_rect, border_radius=4)
        self.screen.blit(pill_surf, (pill_rect[0] + 7, pill_rect[1] + 3))
        curr_y += 28

        # 3. Interactive Action Buttons & Speed Toggles
        curr_y = self._render_control_buttons(pad_x, curr_y, card_w)

        # 4. Clean Heuristic Evaluation Bar
        curr_y = self._render_eval_gauge(pad_x, curr_y, card_w)

        p0_is_human = getattr(agent0, "is_human", False)
        p1_is_human = getattr(agent1, "is_human", False)
        both_humans = p0_is_human and p1_is_human

        # 5. Player 0 Card (Blue Team MAX)
        curr_y = self._draw_player_card(
            x=pad_x, y=curr_y, width=card_w, pid=0,
            agent=agent0,
            tank=state.tanks.get(0),
            base=state.bases.get(0),
            is_active_turn=(state.current_player == 0 and not state.is_terminal()),
            primary_color=self.COLOR_P0_PRIMARY,
            bg_color=self.COLOR_P0_BG,
            border_color=self.COLOR_P0_BORDER,
            both_humans=both_humans
        )
        curr_y += 10

        # 6. Player 1 Card (Red Team MIN)
        curr_y = self._draw_player_card(
            x=pad_x, y=curr_y, width=card_w, pid=1,
            agent=agent1,
            tank=state.tanks.get(1),
            base=state.bases.get(1),
            is_active_turn=(state.current_player == 1 and not state.is_terminal()),
            primary_color=self.COLOR_P1_PRIMARY,
            bg_color=self.COLOR_P1_BG,
            border_color=self.COLOR_P1_BORDER,
            both_humans=both_humans
        )
        curr_y += 10

        # 7. Bottom Context Area: Human D-Pad OR Clean Rules Summary
        if (p0_is_human or p1_is_human) and not state.is_terminal():
            curr_y = self._render_human_dpad(pad_x, curr_y, card_w, state.current_player, both_humans)
        else:
            curr_y = self._render_specs_legend(pad_x, curr_y, card_w)

    def _render_control_buttons(self, x: int, y: int, width: int) -> int:
        """Renders control buttons with prominent START/PAUSE highlight and speed presets."""
        mx, my = pygame.mouse.get_pos()

        for btn in self.buttons:
            if btn["id"] == "play_pause":
                if not self.match_started:
                    btn["label"] = "START"
                elif self.is_paused:
                    btn["label"] = "RESUME"
                else:
                    btn["label"] = "PAUSE"
                break

        # Row 1: Action buttons
        w_btn = (width - 20) // 5
        offsets = [0, w_btn + 13, 2 * w_btn + 16, 3 * w_btn + 19, 4 * w_btn + 22]
        for idx, btn in enumerate(self.buttons):
            r = btn["rect"]
            if idx < len(offsets):
                r.left = x + offsets[idx]
            r.top = y
            is_hover = r.collidepoint(mx, my)
            is_start = btn["id"] == "play_pause"

            if is_start:
                if self.is_paused:
                    btn_bg = (30, 165, 100) if is_hover else (22, 135, 82)
                    b_col = (80, 235, 145)
                else:
                    btn_bg = (210, 130, 30) if is_hover else (180, 105, 20)
                    b_col = self.COLOR_GOLD
            else:
                btn_bg = (48, 62, 88) if is_hover else (28, 36, 52)
                b_col = self.COLOR_GOLD if is_hover else (45, 58, 82)

            pygame.draw.rect(self.screen, btn_bg, r, border_radius=5)
            pygame.draw.rect(self.screen, b_col, r, 1, border_radius=5)

            font_to_use = self.font_bold if is_start else self.font_small
            lbl = font_to_use.render(btn["label"], True, (255, 255, 255))
            self.screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        y += 36

        # Row 2: Speed buttons
        sw_btn = (width - 18) // 4
        for idx, sbtn in enumerate(self.speed_buttons):
            r = sbtn["rect"]
            r.left = x + idx * (sw_btn + 6)
            r.top = y
            is_active = (self.speed_multiplier == sbtn["val"])
            is_hover = r.collidepoint(mx, my)

            s_bg = (36, 105, 175) if is_active else ((42, 54, 76) if is_hover else (24, 30, 44))
            pygame.draw.rect(self.screen, s_bg, r, border_radius=5)
            border_c = (80, 175, 255) if is_active else (self.COLOR_GOLD if is_hover else (40, 52, 72))
            pygame.draw.rect(self.screen, border_c, r, 1, border_radius=5)

            lbl_color = (255, 255, 255) if (is_active or is_hover) else self.COLOR_TEXT_DIM
            lbl = self.font_small.render(sbtn["label"], True, lbl_color)
            self.screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        y += 30

        # Row 3: 1-Click Mode Preset buttons (1P vs AI, 2P PvP, AI vs AI)
        p0_key = self.presets[self.p0_algo_idx % len(self.presets)][0]
        p1_key = self.presets[self.p1_algo_idx % len(self.presets)][0]
        if p0_key == "human" and p1_key == "human":
            cur_mode = "2P"
        elif p0_key == "human" or p1_key == "human":
            cur_mode = "1P"
        else:
            cur_mode = "AI"

        mw_btn = (width - 12) // 3
        for idx, mbtn in enumerate(self.mode_buttons):
            r = mbtn["rect"]
            r.left = x + idx * (mw_btn + 6)
            r.width = mw_btn if idx < 2 else (width - 2 * (mw_btn + 6))
            r.top = y
            is_active = (cur_mode == mbtn["mode"])
            is_hover = r.collidepoint(mx, my)

            m_bg = (22, 125, 82) if is_active else ((42, 54, 76) if is_hover else (24, 30, 44))
            border_c = (72, 225, 140) if is_active else (self.COLOR_GOLD if is_hover else (40, 52, 72))
            pygame.draw.rect(self.screen, m_bg, r, border_radius=5)
            pygame.draw.rect(self.screen, border_c, r, 1, border_radius=5)

            lbl_color = (255, 255, 255) if (is_active or is_hover) else self.COLOR_TEXT_DIM
            lbl = self.font_bold.render(mbtn["label"], True, lbl_color) if is_active else self.font_small.render(mbtn["label"], True, lbl_color)
            self.screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        return y + 30

    def _render_eval_gauge(self, x: int, y: int, width: int) -> int:
        """Renders a clean, uncluttered Heuristic Evaluation Bar."""
        self.smooth_eval += (self.eval_score - self.smooth_eval) * 0.15
        clamped_score = max(-100.0, min(100.0, self.smooth_eval))

        gauge_h = 34
        container_rect = pygame.Rect(x, y, width, gauge_h)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BG, container_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, container_rect, 1, border_radius=6)

        lbl_surf = self.font_metric_lbl.render("HEURISTIC EVAL(s)", True, self.COLOR_TEXT_DIM)
        self.screen.blit(lbl_surf, (x + 10, y + 4))

        score_val = self.eval_score
        sign = "+" if score_val > 0 else ""
        if score_val > 3:
            dom_text = f"P0 Blue Advantage ({sign}{score_val:.1f})"
            dom_color = self.COLOR_P0_PRIMARY
        elif score_val < -3:
            dom_text = f"P1 Red Advantage ({sign}{score_val:.1f})"
            dom_color = self.COLOR_P1_PRIMARY
        else:
            dom_text = f"Balanced ({sign}{score_val:.1f})"
            dom_color = self.COLOR_GOLD

        dom_surf = self.font_metric_lbl.render(dom_text, True, dom_color)
        self.screen.blit(dom_surf, (x + width - dom_surf.get_width() - 10, y + 4))

        groove_x = x + 10
        groove_y = y + 20
        groove_w = width - 20
        groove_h = 7
        pygame.draw.rect(self.screen, (14, 18, 26), (groove_x, groove_y, groove_w, groove_h), border_radius=3)

        center_x = groove_x + groove_w // 2
        half_w = groove_w // 2
        bar_len = int(abs(clamped_score) / 100.0 * half_w)
        if clamped_score > 0:
            pygame.draw.rect(self.screen, self.COLOR_P0_PRIMARY, (center_x, groove_y, bar_len, groove_h), border_radius=2)
        elif clamped_score < 0:
            pygame.draw.rect(self.screen, self.COLOR_P1_PRIMARY, (center_x - bar_len, groove_y, bar_len, groove_h), border_radius=2)

        pygame.draw.line(self.screen, (255, 255, 255), (center_x, groove_y - 2), (center_x, groove_y + groove_h + 2), 2)
        return y + gauge_h + 10

    def _draw_player_card(
        self, x: int, y: int, width: int, pid: int,
        agent: BaseAgent, tank, base, is_active_turn: bool,
        primary_color, bg_color, border_color, both_humans: bool = False
    ) -> int:
        """
        Renders a clean, well-organized player card:
        - Row 1: Tank Icon + Player Name + Turn Status Badge
        - Row 2: Algorithm Selector [<] Name [>] + Depth [-] d [+]
        - Row 3: Side-by-side Tank HP & Base HP boxes
        - Row 4: 3 Clean Technical Metric Tiles (Depth, Nodes/Pruned, Time) OR Human Key Guide
        """
        card_h = 186
        card_rect = pygame.Rect(x, y, width, card_h)
        pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=8)
        pygame.draw.rect(self.screen, primary_color if is_active_turn else border_color, card_rect, 2 if is_active_turn else 1, border_radius=8)

        cy = y + 8

        # 1. Header Row
        avatar_img = self.sprites.get(f"tank_{pid}_icon")
        avatar_rect = pygame.Rect(x + 10, cy, 26, 26)
        pygame.draw.rect(self.screen, (16, 22, 32), avatar_rect, border_radius=4)
        if avatar_img:
            self.screen.blit(avatar_img, (avatar_rect.x, avatar_rect.y))

        role_title = f"PLAYER {pid}  ({'BLUE - MAX' if pid == 0 else 'RED - MIN'})"
        t_surf = self.font_header.render(role_title, True, primary_color)
        self.screen.blit(t_surf, (x + 44, cy + 3))

        mx, my = pygame.mouse.get_pos()

        # Import external .py bot button (Req 3)
        ext_btn_rect = pygame.Rect(x + width - 178, cy + 3, 62, 20)
        if pid == 0:
            self.p0_load_ext_rect = ext_btn_rect
        else:
            self.p1_load_ext_rect = ext_btn_rect
        ext_hov = ext_btn_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (45, 58, 82) if ext_hov else (22, 30, 44), ext_btn_rect, border_radius=4)
        pygame.draw.rect(self.screen, self.COLOR_GOLD if ext_hov else (55, 72, 100), ext_btn_rect, 1, border_radius=4)
        ext_lbl = self.font_badge.render("+ .PY", True, self.COLOR_GOLD)
        self.screen.blit(ext_lbl, (ext_btn_rect.centerx - ext_lbl.get_width() // 2, ext_btn_rect.centery - ext_lbl.get_height() // 2))

        is_human = getattr(agent, "is_human", False)
        if is_active_turn and self.match_started:
            if not is_human and self.ai_thinking and self.ai_thinking_pid == pid:
                badge_text = "AI THINKING..."
                pulse_val = int(140 + 80 * math.sin(self.anim_tick * 0.2))
                badge_bg = (230, pulse_val, 34)
            else:
                badge_text = "YOUR TURN" if is_human else "ACTIVE TURN"
                badge_bg = (39, 174, 96) if is_human else primary_color
            tb_surf = self.font_badge.render(badge_text, True, (255, 255, 255))
            tb_w = tb_surf.get_width() + 12
            tb_rect = pygame.Rect(x + width - tb_w - 10, cy + 3, tb_w, 20)
            pygame.draw.rect(self.screen, badge_bg, tb_rect, border_radius=4)
            self.screen.blit(tb_surf, (tb_rect.x + 6, tb_rect.y + 3))
        else:
            tb_surf = self.font_coord.render("STANDBY", True, self.COLOR_TEXT_MUTED)
            self.screen.blit(tb_surf, (x + width - tb_surf.get_width() - 12, cy + 5))

        cy += 32

        # 2. Algorithm Selector Row
        sel_idx = (self.p0_algo_idx if pid == 0 else self.p1_algo_idx) % len(self.presets)
        sel_key, sel_label = self.presets[sel_idx]

        btn_prev_rect = pygame.Rect(x + 10, cy, 24, 24)
        btn_next_rect = pygame.Rect(x + 242, cy, 24, 24)
        if pid == 0:
            self.p0_algo_prev_rect = btn_prev_rect
            self.p0_algo_next_rect = btn_next_rect
        else:
            self.p1_algo_prev_rect = btn_prev_rect
            self.p1_algo_next_rect = btn_next_rect

        for b_rect, ch in ((btn_prev_rect, "<"), (btn_next_rect, ">")):
            hov = b_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (45, 58, 82) if hov else (24, 32, 46), b_rect, border_radius=4)
            pygame.draw.rect(self.screen, self.COLOR_GOLD if hov else (40, 52, 72), b_rect, 1, border_radius=4)
            s = self.font_badge.render(ch, True, (255, 255, 255))
            self.screen.blit(s, (b_rect.centerx - s.get_width() // 2, b_rect.centery - s.get_height() // 2))

        algo_capsule_rect = pygame.Rect(x + 38, cy, 200, 24)
        if pid == 0:
            self.p0_algo_capsule_rect = algo_capsule_rect
        else:
            self.p1_algo_capsule_rect = algo_capsule_rect
        cap_hov = algo_capsule_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (24, 32, 48) if cap_hov else (16, 22, 34), algo_capsule_rect, border_radius=4)
        cap_border = self.COLOR_GOLD if cap_hov else (primary_color if is_active_turn else (40, 52, 72))
        pygame.draw.rect(self.screen, cap_border, algo_capsule_rect, 1, border_radius=4)
        algo_surf = self.font_small.render(sel_label[:26], True, (245, 248, 255))
        self.screen.blit(algo_surf, (algo_capsule_rect.centerx - algo_surf.get_width() // 2, algo_capsule_rect.centery - algo_surf.get_height() // 2))

        cur_depth = self.p0_depth if pid == 0 else self.p1_depth
        uses_depth = sel_key in ("heuristic_alphabeta", "id_ab", "alphabeta", "heuristic_minimax", "minimax") or hasattr(agent, "depth") or hasattr(agent, "max_depth")
        if uses_depth and sel_key not in ("human", "greedy"):
            d_x = x + 276
            lbl_dep = self.font_metric_lbl.render("DEPTH:", True, self.COLOR_TEXT_DIM)
            self.screen.blit(lbl_dep, (d_x, cy + 5))

            d_dec = pygame.Rect(d_x + 48, cy, 22, 24)
            d_inc = pygame.Rect(d_x + 98, cy, 22, 24)
            if pid == 0:
                self.p0_depth_dec_rect = d_dec
                self.p0_depth_inc_rect = d_inc
            else:
                self.p1_depth_dec_rect = d_dec
                self.p1_depth_inc_rect = d_inc

            for b_rect, ch in ((d_dec, "-"), (d_inc, "+")):
                hov = b_rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, (45, 58, 82) if hov else (24, 32, 46), b_rect, border_radius=4)
                pygame.draw.rect(self.screen, self.COLOR_GOLD if hov else (40, 52, 72), b_rect, 1, border_radius=4)
                s = self.font_bold.render(ch, True, (255, 255, 255))
                self.screen.blit(s, (b_rect.centerx - s.get_width() // 2, b_rect.centery - s.get_height() // 2))

            val_surf = self.font_metric_val.render(str(cur_depth), True, self.COLOR_GOLD)
            self.screen.blit(val_surf, (d_x + 80, cy + 3))
        else:
            empty_rect = pygame.Rect(-1, -1, 0, 0)
            if pid == 0:
                self.p0_depth_dec_rect = empty_rect
                self.p0_depth_inc_rect = empty_rect
            else:
                self.p1_depth_dec_rect = empty_rect
                self.p1_depth_inc_rect = empty_rect

            mode_pill = pygame.Rect(x + 274, cy, width - 284, 24)
            if sel_key == "human":
                m_bg, m_txt, m_col = (20, 46, 34), "MANUAL MODE", self.COLOR_EMERALD
            elif sel_key == "greedy":
                m_bg, m_txt, m_col = (48, 38, 20), "1-PLY GREEDY", self.COLOR_GOLD
            else:
                m_bg, m_txt, m_col = (34, 38, 62), "EXTERNAL BOT", self.COLOR_CYAN
            pygame.draw.rect(self.screen, m_bg, mode_pill, border_radius=4)
            m_surf = self.font_coord.render(m_txt, True, m_col)
            self.screen.blit(m_surf, (mode_pill.centerx - m_surf.get_width() // 2, mode_pill.centery - m_surf.get_height() // 2))

        cy += 32

        # 3. Side-by-Side Health Boxes (Tank HP & Fortified Citadel Base HQ HP)
        t_hp = tank.hp if (tank and tank.is_alive) else 0
        b_hp = base.hp if (base and base.is_alive) else 0
        half_w = (width - 28) // 2

        self._draw_clean_hp_box(x + 10, cy, half_w, 42, "TANK HEALTH", t_hp, 6, primary_color)
        self._draw_citadel_hp_box(x + 18 + half_w, cy, half_w, 42, b_hp, 9, primary_color, pid=pid)

        cy += 50

        # 4. Technical Metrics Row (3 Clean Boxes for AI, or Dedicated Keyboard Controls for Human)
        if is_human:
            kb_rect = pygame.Rect(x + 10, cy, width - 20, 52)
            pygame.draw.rect(self.screen, self.COLOR_INSET_BG, kb_rect, border_radius=5)
            pygame.draw.rect(self.screen, primary_color if is_active_turn else self.COLOR_INSET_BORDER, kb_rect, 1, border_radius=5)

            reac_ms = getattr(agent, "last_reaction_time", 0.0) * 1000.0
            reac_str = f"{reac_ms:.0f} ms" if reac_ms > 0 else "Ready"
            if reac_ms > 0:
                if reac_ms < 250:
                    speed_rank = "LIGHTNING"
                    rank_col = self.COLOR_CYAN
                elif reac_ms < 500:
                    speed_rank = "FAST"
                    rank_col = self.COLOR_EMERALD
                elif reac_ms < 1000:
                    speed_rank = "TACTICAL"
                    rank_col = self.COLOR_GOLD
                else:
                    speed_rank = "CALCULATED"
                    rank_col = self.COLOR_AMBER
            else:
                speed_rank = "READY"
                rank_col = self.COLOR_EMERALD

            moves_cnt = getattr(agent, "total_moves", 0)
            shots_cnt = getattr(agent, "total_shots", 0)

            # Left block: Reaction time tile
            reac_lbl = self.font_metric_lbl.render("REACTION TIME", True, self.COLOR_TEXT_DIM)
            self.screen.blit(reac_lbl, (x + 18, cy + 7))
            reac_val = self.font_metric_val.render(reac_str, True, rank_col)
            self.screen.blit(reac_val, (x + 18, cy + 24))

            rank_badge = self.font_badge.render(speed_rank, True, (255, 255, 255))
            rb_w = rank_badge.get_width() + 8
            rb_rect = pygame.Rect(x + 105, cy + 25, rb_w, 16)
            pygame.draw.rect(self.screen, rank_col, rb_rect, border_radius=3)
            self.screen.blit(rank_badge, (rb_rect.x + 4, rb_rect.y + 1))

            # Right block: Guidance & Stats
            if both_humans:
                if pid == 0:
                    k_desc = "P0: [WASD] move, [F/SPACE] fire, [Q] stay"
                else:
                    k_desc = "P1: [Arrows] move, [/] fire, [.] stay"
            else:
                k_desc = "[WASD / Click Map] Move | [SPACE / R-Click] Fire"
            kd_surf = self.font_bold.render(k_desc, True, (245, 248, 255))
            self.screen.blit(kd_surf, (x + 185, cy + 7))

            tip_str = f"Stats: {moves_cnt} moves, {shots_cnt} shots | Hold key to drive continuously!"
            tip_surf = self.font_small.render(tip_str, True, self.COLOR_GOLD)
            self.screen.blit(tip_surf, (x + 185, cy + 26))
        else:
            stats = agent.stats if agent else None
            d_val = stats.search_depth if (stats and stats.search_depth > 0) else (1 if sel_key == "greedy" else cur_depth)
            nodes = stats.explored_nodes if stats else 0
            prunes = stats.prune_count if stats else 0
            t_ms = (stats.execution_time * 1000) if stats else 0.0

            box_w = (width - 32) // 3
            box_h = 52
            self._draw_clean_metric_box(x + 10, cy, box_w, box_h, "SEARCH DEPTH", f"d = {d_val}", self.COLOR_CYAN)
            nodes_str = f"{nodes:,} ({prunes} cut)" if prunes > 0 else f"{nodes:,} nodes"
            self._draw_clean_metric_box(x + 16 + box_w, cy, box_w, box_h, "NODES / PRUNED", nodes_str, self.COLOR_GOLD)
            self._draw_clean_metric_box(x + 22 + 2 * box_w, cy, box_w, box_h, "DECISION TIME", f"{t_ms:.1f} ms", self.COLOR_EMERALD)

        return y + card_h

    def _render_human_dpad(self, x: int, y: int, width: int, active_pid: int, both_humans: bool = False) -> int:
        """Renders a clean, clickable on-screen control pad without unsupported symbols."""
        card_h = 128
        rect = pygame.Rect(x, y, width, card_h)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BG, rect, border_radius=8)
        team_color = self.COLOR_P0_PRIMARY if active_pid == 0 else self.COLOR_P1_PRIMARY
        pygame.draw.rect(self.screen, team_color, rect, 1, border_radius=8)

        mode_tag = "2-PLAYER PVP MODE" if both_humans else f"P{active_pid} MANUAL CONTROLS"
        hdr_txt = f"ON-SCREEN CONTROL PAD ({mode_tag} - ACTIVE: P{active_pid})"
        hdr_surf = self.font_metric_lbl.render(hdr_txt, True, self.COLOR_GOLD)
        self.screen.blit(hdr_surf, (x + 12, y + 7))

        mx, my = pygame.mouse.get_pos()
        self.dpad_buttons = []

        bx = x + 16
        by = y + 28
        bw = 54
        bh = 28

        dpad_defs = [
            ("UP",    Action.MOVE_UP,    pygame.Rect(bx + bw + 4, by, bw, bh)),
            ("LEFT",  Action.MOVE_LEFT,  pygame.Rect(bx, by + bh + 4, bw, bh)),
            ("DOWN",  Action.MOVE_DOWN,  pygame.Rect(bx + bw + 4, by + bh + 4, bw, bh)),
            ("RIGHT", Action.MOVE_RIGHT, pygame.Rect(bx + 2 * (bw + 4), by + bh + 4, bw, bh)),
        ]

        for lbl_txt, act, b_rect in dpad_defs:
            is_hover = b_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (48, 62, 88) if is_hover else (24, 32, 46), b_rect, border_radius=5)
            pygame.draw.rect(self.screen, team_color if is_hover else self.COLOR_CARD_BORDER, b_rect, 1, border_radius=5)
            s = self.font_badge.render(lbl_txt, True, (255, 255, 255))
            self.screen.blit(s, (b_rect.centerx - s.get_width() // 2, b_rect.centery - s.get_height() // 2))
            self.dpad_buttons.append({"action": act, "rect": b_rect})

        # FIRE & STAY Buttons
        fire_rect = pygame.Rect(x + 200, by + 2, 118, 56)
        is_fire_hover = fire_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (205, 55, 55) if is_fire_hover else (165, 38, 38), fire_rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 130, 130), fire_rect, 1, border_radius=6)
        f_lbl = self.font_header.render("FIRE CANNON", True, (255, 255, 255))
        self.screen.blit(f_lbl, (fire_rect.centerx - f_lbl.get_width() // 2, fire_rect.centery - f_lbl.get_height() // 2))
        self.dpad_buttons.append({"action": Action.FIRE, "rect": fire_rect})

        stay_rect = pygame.Rect(x + 326, by + 2, 90, 56)
        is_stay_hover = stay_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (48, 62, 88) if is_stay_hover else (26, 34, 48), stay_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_GOLD if is_stay_hover else self.COLOR_CARD_BORDER, stay_rect, 1, border_radius=6)
        st_lbl = self.font_header.render("STAY", True, (240, 240, 240))
        self.screen.blit(st_lbl, (stay_rect.centerx - st_lbl.get_width() // 2, stay_rect.centery - st_lbl.get_height() // 2))
        self.dpad_buttons.append({"action": Action.STAY, "rect": stay_rect})

        if both_humans:
            hint_str = "P0: [WASD + F/SPACE]  |  P1: [Arrows + / / Enter / .]"
        else:
            hint_str = "Hold WASD/Arrows to drive | Click map cells | R-Click Fire"
        hint_surf = self.font_small.render(hint_str, True, self.COLOR_TEXT_DIM)
        self.screen.blit(hint_surf, (x + 12, y + card_h - 22))

        return y + card_h + 6

    def _render_specs_legend(self, x: int, y: int, width: int) -> int:
        """Renders a clean, easy-to-read Game Parameters & Entities summary card."""
        card_h = 128
        rect = pygame.Rect(x, y, width, card_h)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, rect, 1, border_radius=8)

        hdr_surf = self.font_metric_lbl.render("GAME ENTITIES & TECHNICAL SPECIFICATIONS", True, self.COLOR_GOLD)
        self.screen.blit(hdr_surf, (x + 12, y + 7))

        col_w = (width - 28) // 2
        row_h = 38
        y_start = y + 26

        specs_items = [
            ("tank_0_icon",      "Combat Tank: 6 HP",     "6 Legal Actions (1 Dmg/hit)", (x + 10, y_start)),
            ("base_0_icon",      "Command Base: 9 HP",    "Destroy enemy HQ to win",     (x + 18 + col_w, y_start)),
            ("crate_metal_spec", "Obstacle Walls: 1-3 HP", "Metal (3), Wood (2), Bag (1)", (x + 10, y_start + row_h + 6)),
            ("bullet_icon",      "Bullet Speed: 3 Cells", "Cell-by-cell collision check", (x + 18 + col_w, y_start + row_h + 6)),
        ]

        for sprite_key, title, spec_desc, (tx, ty) in specs_items:
            tile_rect = pygame.Rect(tx, ty, col_w, row_h)
            pygame.draw.rect(self.screen, self.COLOR_INSET_BG, tile_rect, border_radius=5)
            pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, tile_rect, 1, border_radius=5)

            sp = self.sprites.get(sprite_key)
            if sp:
                self.screen.blit(sp, (tx + 8, ty + (row_h - sp.get_height()) // 2))

            ts = self.font_bold.render(title, True, self.COLOR_TEXT)
            ds = self.font_small.render(spec_desc, True, self.COLOR_TEXT_DIM)
            self.screen.blit(ts, (tx + 34, ty + 3))
            self.screen.blit(ds, (tx + 34, ty + 19))

        return y + card_h

    def _render_game_over_banner(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """Draws victory/draw banner with interactive Replay, Undo, and Next Map buttons."""
        winner = state.get_winner()
        b_w = self.board_w
        b_h = self.board_h

        tint = pygame.Surface((b_w, b_h), pygame.SRCALPHA)
        tint.fill((10, 14, 22, 175))
        self.screen.blit(tint, (0, 0))

        card_w = min(430, max(280, b_w - 24))
        card_h = 184
        cx = (b_w - card_w) // 2
        cy = (b_h - card_h) // 2

        pygame.draw.rect(self.screen, (24, 32, 46), (cx, cy, card_w, card_h), border_radius=10)
        border_c = (self.COLOR_P0_PRIMARY if winner == 0 else
                    (self.COLOR_P1_PRIMARY if winner == 1 else self.COLOR_GOLD))
        pygame.draw.rect(self.screen, border_c, (cx, cy, card_w, card_h), 2, border_radius=10)

        if winner == 0:
            w_title = "VICTORY: PLAYER 0 (BLUE - MAX)"
            w_name = agent0.name if agent0 else "Player 0"
            w_color = self.COLOR_P0_PRIMARY
        elif winner == 1:
            w_title = "VICTORY: PLAYER 1 (RED - MIN)"
            w_name = agent1.name if agent1 else "Player 1"
            w_color = self.COLOR_P1_PRIMARY
        else:
            w_title = "MATCH DRAW"
            w_name = f"Cycle Limit Reached ({state.game_cycle} Cycles)"
            w_color = self.COLOR_GOLD

        t_surf = self.font_large.render(w_title, True, w_color)
        self.screen.blit(t_surf, (cx + (card_w - t_surf.get_width()) // 2, cy + 20))

        n_surf = self.font.render(w_name, True, self.COLOR_TEXT)
        self.screen.blit(n_surf, (cx + (card_w - n_surf.get_width()) // 2, cy + 50))

        # 3 Interactive Action Buttons on the Game Over Modal
        mx, my = pygame.mouse.get_pos()
        self.gameover_buttons = []
        btn_y = cy + 88
        btn_h = 34
        pad_in = 16
        gap = 8
        bw = (card_w - 2 * pad_in - 2 * gap) // 3
        compact = (bw < 110)
        defs = [
            ("go_restart",  "AGAIN (R)" if compact else "PLAY AGAIN (R)", (22, 135, 82),  (32, 168, 102), (80, 235, 145)),
            ("go_undo",     "UNDO (U)",                                     (48, 62, 88),   (66, 84, 118),  self.COLOR_GOLD),
            ("go_next_map", "MAP (M)" if compact else "NEXT MAP (M)",       (36, 105, 175), (48, 130, 210), (80, 175, 255)),
        ]
        for idx, (gid, glbl, bg_norm, bg_hov, b_col) in enumerate(defs):
            bx = cx + pad_in + idx * (bw + gap)
            rect = pygame.Rect(bx, btn_y, bw, btn_h)
            hov = rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, bg_hov if hov else bg_norm, rect, border_radius=6)
            pygame.draw.rect(self.screen, b_col, rect, 1, border_radius=6)
            lbl_s = self.font_bold.render(glbl, True, (255, 255, 255))
            self.screen.blit(lbl_s, (rect.centerx - lbl_s.get_width() // 2, rect.centery - lbl_s.get_height() // 2))
            self.gameover_buttons.append({"id": gid, "rect": rect})

        esc_surf = self.font_small.render("Press [SPACE/R] Replay  |  [U] Undo  |  [ESC] Exit", True, self.COLOR_TEXT_DIM)
        self.screen.blit(esc_surf, (cx + (card_w - esc_surf.get_width()) // 2, cy + 142))
