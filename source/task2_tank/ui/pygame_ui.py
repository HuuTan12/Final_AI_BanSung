"""
pygame_ui.py - High-Fidelity Tactical Battle City GUI with Multi-Agent HUD & Realistic Bullet Physics
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements a responsive, esports-grade Pygame GUI with:
    1. Realistic cell-by-cell bullet flight animations with muzzle flashes, projectile smoke trails,
       and fiery impact explosions adhering strictly to the 3 cells/cycle rule.
    2. Interactive multi-agent selector: Choose between Human, Heuristic Alpha-Beta,
       Iterative Deepening Alpha-Beta (proposed), Alpha-Beta Pruning, Heuristic Minimax,
       Minimax Search, Greedy Tactical, or External Rival for both tanks.
    3. Interactive Human player mode: Keyboard controls (WASD/Arrows + SPACE) and clickable On-Screen D-Pad.
    4. Sleek tactical HUD featuring embedded Kenney asset sprites, battery-style health bars,
       live search telemetry, bidirectional heuristic advantage meter, and combat specifications.
    5. Turn-based playback deck with Play/Pause, Step +1, Undo -1, Reset, Map cycling, and Speed presets.
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
    High-Fidelity Graphical User Interface for the Tank Battle Game.
    """

    def __init__(self, cell_size: int = 46, fps: int = 60):
        self.cell_size = cell_size
        self.fps = fps
        self.speed_multiplier = 1.0  # 0.5x, 1.0x, 2.0x, 10.0x (Turbo)

        # Playback control flags
        self.is_paused: bool = False
        self.step_requested: bool = False
        self.undo_requested: bool = False
        self.restart_requested: bool = False
        self.map_requested: bool = False
        self.current_map_title: str = "01_classic_battlecity"

        # Agent switching flags
        self.agent_changed: bool = False
        self.p0_algo_idx: int = 1     # Default: Heuristic Alpha-Beta
        self.p1_algo_idx: int = 3     # Default: Alpha-Beta Pruning
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
        self.dpad_buttons: List[Dict[str, Any]] = []

        # Visual FX state
        self.tracks: List[Dict[str, Any]] = []         # [{x, y, dir, life}]
        self.explosions: List[Dict[str, Any]] = []     # [{x, y, frame, max_frames}]
        self.muzzle_flashes: List[Dict[str, Any]] = [] # [{x, y, dir, frame, max_frames}]
        self.damage_flashes: Dict[str, int] = {}       # {entity_key: frames_remaining}

        # Sub-step animated bullet flight state
        self.is_animating_turn: bool = False
        self.animated_bullets: List[Dict[str, Any]] = []

        # Real-time combat event log feed
        self.combat_logs: List[Dict[str, Any]] = [
            {"text": "[SYS] Command Deck initialized. Grid: 13x13", "color": (140, 160, 190)},
            {"text": "[RULES] Tanks (HP 6) | Bases (HP 9) | Walls (HP 1-3)", "color": (120, 140, 170)},
            {"text": "[WEAPON] Kinetic shell speed: 3 cells/cycle, cell-by-cell check", "color": (245, 185, 25)},
            {"text": "[STATUS] Match initialized. Ready for command input.", "color": (46, 204, 113)},
        ]

        # Telemetry & Evaluator
        self.eval_score: float = 0.0
        self.smooth_eval: float = 0.0
        self.evaluator = TankEvaluator()
        self.human_action_queued: Optional[Action] = None

        # Color Palette - Professional Dark Carbon & Tactical Matte Steel
        self.COLOR_BG = (15, 18, 26)
        self.COLOR_SIDEBAR_BG = (18, 22, 32)
        self.COLOR_CARD_BG = (24, 30, 44)
        self.COLOR_CARD_BORDER = (42, 54, 76)
        self.COLOR_CARD_HEADER = (30, 38, 56)
        self.COLOR_INSET_BG = (14, 18, 26)
        self.COLOR_INSET_BORDER = (32, 42, 60)
        self.COLOR_TEXT = (242, 246, 252)
        self.COLOR_TEXT_DIM = (150, 165, 188)
        self.COLOR_TEXT_MUTED = (90, 105, 125)
        self.COLOR_GOLD = (245, 185, 25)
        self.COLOR_AMBER = (230, 126, 34)
        self.COLOR_CYAN = (52, 219, 219)
        self.COLOR_EMERALD = (46, 204, 113)

        # Team Color Themes
        self.COLOR_P0_PRIMARY = (52, 152, 219)     # Electric Blue (Player 0 MAX)
        self.COLOR_P0_BG = (20, 32, 52)
        self.COLOR_P0_BORDER = (41, 128, 185)
        self.COLOR_P0_GLOW = (90, 185, 255)

        self.COLOR_P1_PRIMARY = (231, 76, 60)      # Crimson Red (Player 1 MIN)
        self.COLOR_P1_BG = (48, 24, 28)
        self.COLOR_P1_BORDER = (192, 57, 43)
        self.COLOR_P1_GLOW = (255, 110, 95)

        # Entity colors (fallback)
        self.COLOR_WALL = (165, 85, 54)
        self.COLOR_WALL_CRACK = (120, 60, 40)
        self.COLOR_HP_GREEN = (46, 204, 113)
        self.COLOR_HP_YELLOW = (241, 196, 15)
        self.COLOR_HP_RED = (231, 76, 60)

    def init_display(self, width_cells: int, height_cells: int) -> bool:
        """Initializes Pygame window, custom fonts, buttons, and visual assets."""
        if not PYGAME_AVAILABLE:
            print("[TankGameGUI] Notice: Pygame is not installed. Running in headless mode.")
            return False

        try:
            pygame.init()
            pygame.font.init()

            self.board_w = width_cells * self.cell_size
            self.board_h = height_cells * self.cell_size
            self.width_px = self.board_w + self.sidebar_width
            self.height_px = max(self.board_h, 800)

            self.screen = pygame.display.set_mode((self.width_px, self.height_px))
            pygame.display.set_caption("AI Tank Battle - Tactical Esports Command Deck (TDTU)")
            self.clock = pygame.time.Clock()

            # Typography hierarchy
            self.font_title = pygame.font.SysFont("Segoe UI,Trebuchet MS,Helvetica,Arial", 16, bold=True)
            self.font_header = pygame.font.SysFont("Segoe UI,Trebuchet MS,Helvetica,Arial", 13, bold=True)
            self.font_large = pygame.font.SysFont("Segoe UI,Trebuchet MS,Helvetica,Arial", 12, bold=True)
            self.font = pygame.font.SysFont("Segoe UI,Helvetica,Arial", 11)
            self.font_badge = pygame.font.SysFont("Consolas,Courier New,Arial", 11, bold=True)
            self.font_metric_val = pygame.font.SysFont("Consolas,Lucida Console,Courier New", 13, bold=True)
            self.font_metric_lbl = pygame.font.SysFont("Segoe UI,Helvetica,Arial", 9, bold=True)
            self.font_small = pygame.font.SysFont("Segoe UI,Helvetica,Arial", 10)
            self.font_coord = pygame.font.SysFont("Consolas,Courier New,Arial", 9, bold=True)

            self._load_sprites()
            self._init_buttons()
            return True
        except Exception as e:
            print(f"[TankGameGUI] Display initialization error: {e}")
            return False

    def _load_sprites(self) -> None:
        """Loads PNG sprites from Kenney assets with high-contrast scaling."""
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
        self.sprites["wall_3_icon"] = load_scaled("crateMetal.png", 18, 18)
        self.sprites["wall_2_icon"] = load_scaled("crateWood.png", 18, 18)
        self.sprites["wall_1_icon"] = load_scaled("sandbagBrown.png", 18, 18)

        # 5. Base HQs
        self.sprites["base_0"] = load_scaled("barrelBlack_top.png", cs - 6, cs - 6)
        self.sprites["base_1"] = load_scaled("barrelRed_top.png", cs - 6, cs - 6)
        self.sprites["base_0_icon"] = load_scaled("barrelBlack_top.png", 20, 20)
        self.sprites["base_1_icon"] = load_scaled("barrelRed_top.png", 20, 20)

        # 6. Explosions & Smoke
        for i in range(1, 6):
            self.sprites[f"exp_{i}"] = load_scaled(f"explosion{i}.png", cs + 6, cs + 6)
        for i in range(1, 4):
            self.sprites[f"smoke_{i}"] = load_scaled(f"explosionSmoke{i}.png", cs, cs)

        # 7. Dedicated Armory & Telemetry Showcase Sprites
        self.sprites["crate_metal_spec"] = load_scaled("crateMetal.png", 22, 22)
        self.sprites["crate_wood_spec"] = load_scaled("crateWood.png", 22, 22)
        self.sprites["sandbag_spec"] = load_scaled("sandbagBrown.png", 22, 22)

    def _init_buttons(self) -> None:
        """Creates interactive buttons in sidebar."""
        pad_x = self.board_w + 14
        card_w = self.sidebar_width - 28
        btn_y = 78

        # Row 1: Action Controls
        w_btn = (card_w - 20) // 5
        self.buttons = [
            {"id": "play_pause", "label": "PAUSE",   "rect": pygame.Rect(pad_x, btn_y, w_btn, 24)},
            {"id": "step",       "label": "STEP +1", "rect": pygame.Rect(pad_x + w_btn + 5, btn_y, w_btn, 24)},
            {"id": "undo",       "label": "UNDO -1", "rect": pygame.Rect(pad_x + 2 * (w_btn + 5), btn_y, w_btn, 24)},
            {"id": "restart",    "label": "RESET",   "rect": pygame.Rect(pad_x + 3 * (w_btn + 5), btn_y, w_btn, 24)},
            {"id": "next_map",   "label": "MAP >>",  "rect": pygame.Rect(pad_x + 4 * (w_btn + 5), btn_y, w_btn, 24)},
        ]

        # Row 2: Speed Toggle
        s_y = btn_y + 28
        sw_btn = (card_w - 18) // 4
        self.speed_buttons = [
            {"id": "speed_05", "label": "0.5x",   "rect": pygame.Rect(pad_x, s_y, sw_btn, 22), "val": 0.5},
            {"id": "speed_1",  "label": "1.0x",   "rect": pygame.Rect(pad_x + sw_btn + 6, s_y, sw_btn, 22), "val": 1.0},
            {"id": "speed_2",  "label": "2.0x",   "rect": pygame.Rect(pad_x + 2 * (sw_btn + 6), s_y, sw_btn, 22), "val": 2.0},
            {"id": "speed_10", "label": "TURBO",  "rect": pygame.Rect(pad_x + 3 * (sw_btn + 6), s_y, sw_btn, 22), "val": 10.0},
        ]

    def set_speed(self, multiplier: float) -> None:
        """Sets game execution speed multiplier."""
        self.speed_multiplier = float(multiplier)

    def add_combat_log(self, text: str, color: Tuple[int, int, int] = (220, 230, 245)) -> None:
        """Appends a telemetry log event to the tactical sensor feed."""
        self.combat_logs.append({"text": text, "color": color})
        if len(self.combat_logs) > 8:
            self.combat_logs.pop(0)

    def add_hit_effect(self, x: int, y: int) -> None:
        """Triggers an animated explosion effect at cell (x, y)."""
        self.explosions.append({"x": x, "y": y, "frame": 0, "max_frames": 10})
        self.damage_flashes[f"{x},{y}"] = 8
        self.add_combat_log(f"[IMPACT] Shell hit target at ({x}, {y})", (255, 120, 80))

    def add_muzzle_flash(self, x: int, y: int, direction: Direction) -> None:
        """Triggers a muzzle flash effect when tank fires."""
        self.muzzle_flashes.append({"x": x, "y": y, "dir": direction, "frame": 0, "max_frames": 6})
        self.add_combat_log(f"[FIRE] Cannon discharged facing {direction.name}", (255, 200, 100))

    def add_tank_track(self, x: int, y: int, direction: Direction) -> None:
        """Leaves fading track treads at the cell where a tank moved."""
        self.tracks.append({"x": x, "y": y, "dir": direction, "life": 120})
        if len(self.tracks) > 60:
            self.tracks.pop(0)

    def handle_events(self, active_player_is_human: bool = False) -> bool:
        """Processes mouse clicks, keyboard controls, and window events."""
        if not PYGAME_AVAILABLE or self.screen is None:
            return True

        self.step_requested = False
        self.undo_requested = False
        self.restart_requested = False
        self.map_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    if not active_player_is_human:
                        self.is_paused = not self.is_paused
                    else:
                        self.human_action_queued = Action.FIRE
                elif event.key == pygame.K_RETURN:
                    if not active_player_is_human:
                        self.step_requested = True
                        self.is_paused = True
                    else:
                        self.human_action_queued = Action.FIRE
                elif event.key == pygame.K_s and not active_player_is_human:
                    self.step_requested = True
                    self.is_paused = True
                elif event.key in (pygame.K_u, pygame.K_z, pygame.K_BACKSPACE):
                    self.undo_requested = True
                    self.is_paused = True
                elif event.key == pygame.K_r:
                    self.restart_requested = True
                elif event.key == pygame.K_m:
                    self.map_requested = True
                elif event.key == pygame.K_1:
                    self.set_speed(0.5)
                elif event.key == pygame.K_2:
                    self.set_speed(1.0)
                elif event.key == pygame.K_3:
                    self.set_speed(2.0)
                elif event.key == pygame.K_4:
                    self.set_speed(10.0)

                # Human Player Keyboard Controls
                if active_player_is_human:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        self.human_action_queued = Action.MOVE_UP
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        self.human_action_queued = Action.MOVE_DOWN
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        self.human_action_queued = Action.MOVE_LEFT
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        self.human_action_queued = Action.MOVE_RIGHT
                    elif event.key in (pygame.K_f, pygame.K_j):
                        self.human_action_queued = Action.FIRE
                    elif event.key in (pygame.K_x, pygame.K_c):
                        self.human_action_queued = Action.STAY

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Top action buttons
                for btn in self.buttons:
                    if btn["rect"].collidepoint(mx, my):
                        b_id = btn["id"]
                        if b_id == "play_pause":
                            self.is_paused = not self.is_paused
                        elif b_id == "step":
                            self.step_requested = True
                            self.is_paused = True
                        elif b_id == "undo":
                            self.undo_requested = True
                            self.is_paused = True
                        elif b_id == "restart":
                            self.restart_requested = True
                        elif b_id == "next_map":
                            self.map_requested = True

                # Speed buttons
                for sbtn in self.speed_buttons:
                    if sbtn["rect"].collidepoint(mx, my):
                        self.set_speed(sbtn["val"])

                # On-screen D-Pad buttons for human
                for dbtn in self.dpad_buttons:
                    if dbtn["rect"].collidepoint(mx, my):
                        self.human_action_queued = dbtn["action"]

                # Algorithm & Depth selectors
                self._handle_selector_clicks(mx, my)

        return True

    def _handle_selector_clicks(self, mx: int, my: int) -> None:
        """Handles clicking algorithm switchers [<] [>] and depth [-] [+]."""
        # P0 Algorithm Prev/Next
        if hasattr(self, "p0_algo_prev_rect") and self.p0_algo_prev_rect.collidepoint(mx, my):
            self.p0_algo_idx = (self.p0_algo_idx - 1) % len(AGENT_PRESETS)
            self.agent_changed = True
        elif hasattr(self, "p0_algo_next_rect") and self.p0_algo_next_rect.collidepoint(mx, my):
            self.p0_algo_idx = (self.p0_algo_idx + 1) % len(AGENT_PRESETS)
            self.agent_changed = True

        # P0 Depth Dec/Inc
        elif hasattr(self, "p0_depth_dec_rect") and self.p0_depth_dec_rect.collidepoint(mx, my):
            if self.p0_depth > 1:
                self.p0_depth -= 1
                self.agent_changed = True
        elif hasattr(self, "p0_depth_inc_rect") and self.p0_depth_inc_rect.collidepoint(mx, my):
            if self.p0_depth < 5:
                self.p0_depth += 1
                self.agent_changed = True

        # P1 Algorithm Prev/Next
        elif hasattr(self, "p1_algo_prev_rect") and self.p1_algo_prev_rect.collidepoint(mx, my):
            self.p1_algo_idx = (self.p1_algo_idx - 1) % len(AGENT_PRESETS)
            self.agent_changed = True
        elif hasattr(self, "p1_algo_next_rect") and self.p1_algo_next_rect.collidepoint(mx, my):
            self.p1_algo_idx = (self.p1_algo_idx + 1) % len(AGENT_PRESETS)
            self.agent_changed = True

        # P1 Depth Dec/Inc
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
            return AGENT_PRESETS[self.p0_algo_idx][0], self.p0_depth
        else:
            return AGENT_PRESETS[self.p1_algo_idx][0], self.p1_depth

    def set_agent_presets_from_agents(self, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """Syncs GUI selector indices to match active agents."""
        for idx, (key, _) in enumerate(AGENT_PRESETS):
            if getattr(agent0, "is_human", False) and key == "human":
                self.p0_algo_idx = idx
            elif key in agent0.name.lower():
                self.p0_algo_idx = idx

            if getattr(agent1, "is_human", False) and key == "human":
                self.p1_algo_idx = idx
            elif key in agent1.name.lower():
                self.p1_algo_idx = idx

        if hasattr(agent0, "depth"):
            self.p0_depth = agent0.depth
        elif hasattr(agent0, "max_depth"):
            self.p0_depth = agent0.max_depth

        if hasattr(agent1, "depth"):
            self.p1_depth = agent1.depth
        elif hasattr(agent1, "max_depth"):
            self.p1_depth = agent1.max_depth

    def animate_turn(
        self,
        state: GameState,
        action: Action,
        agent0: BaseAgent,
        agent1: BaseAgent
    ) -> GameState:
        """
        Executes a turn with realistic cell-by-cell bullet flight animations.
        Matches GameRules.apply_action() physics exactly while providing
        fluid visual feedback.
        """
        next_state = state.clone()
        player_id = next_state.current_player
        tank = next_state.tanks.get(player_id)

        # Phase 1: Apply Tank Action (Move, Fire, Stay)
        if action == Action.FIRE:
            if tank and tank.is_alive:
                self.add_muzzle_flash(tank.x, tank.y, tank.direction)
            GameRules._fire_bullet(next_state, player_id)
        elif action == Action.STAY:
            pass
        else:
            direction = Action.get_move_direction(action)
            if direction and tank and tank.is_alive:
                self.add_tank_track(tank.x, tank.y, tank.direction)
                GameRules._move_tank(next_state, player_id, direction)

        # Phase 2: Realistic Cell-by-Cell Bullet Flight
        if self.speed_multiplier >= 10.0:
            GameRules.step_bullets(next_state)
        else:
            frames_per_cell = max(1, int(6 / self.speed_multiplier))

            for _ in range(Bullet.SPEED):
                active_bullets = [b for b in next_state.bullets if b.is_active]
                if not active_bullets:
                    break

                bullet_paths = []
                for b in active_bullets:
                    dx, dy = b.direction.value
                    start_px = b.x * self.cell_size + self.cell_size // 2
                    start_py = b.y * self.cell_size + self.cell_size // 2
                    target_x = b.x + dx
                    target_y = b.y + dy
                    target_px = target_x * self.cell_size + self.cell_size // 2
                    target_py = target_y * self.cell_size + self.cell_size // 2
                    bullet_paths.append({
                        "bullet": b,
                        "start": (start_px, start_py),
                        "target": (target_px, target_py),
                        "target_cell": (target_x, target_y),
                        "dir": b.direction,
                        "owner": b.owner_id
                    })

                # Interpolate smoothly between cells
                for f in range(1, frames_per_cell + 1):
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
                    pygame.event.pump()

                self.animated_bullets.clear()

                # At cell arrival: Advance coordinates and perform collision check
                for bp in bullet_paths:
                    b = bp["bullet"]
                    tx, ty = bp["target_cell"]
                    b.x = tx
                    b.y = ty

                    if not (0 <= b.x < next_state.width and 0 <= b.y < next_state.height):
                        b.is_active = False
                        continue

                    hit = False
                    # Check collision with wall
                    if (b.x, b.y) in next_state.walls:
                        w = next_state.walls[(b.x, b.y)]
                        if w.is_alive:
                            w.take_damage(1)
                            b.is_active = False
                            hit = True
                            self.add_hit_effect(b.x, b.y)

                    # Check collision with tank
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
                                break

                    # Check collision with base
                    if not hit:
                        for target_base in next_state.bases.values():
                            if (target_base.is_alive and
                                target_base.x == b.x and
                                target_base.y == b.y):
                                target_base.take_damage(1)
                                b.is_active = False
                                hit = True
                                self.add_hit_effect(b.x, b.y)
                                break

                next_state.bullets = [b for b in next_state.bullets if b.is_active]

        # Phase 3: Cleanup dead walls and Advance turn
        dead_walls = [pos for pos, wall in next_state.walls.items() if not wall.is_alive]
        for pos in dead_walls:
            del next_state.walls[pos]

        if player_id == 1:
            next_state.game_cycle += 1
        next_state.current_player = 1 - player_id

        return next_state

    def render(
        self,
        state: GameState,
        agent0: BaseAgent,
        agent1: BaseAgent,
        is_interpolating: bool = False
    ) -> None:
        """Main draw routine rendering battlefield, entities, particles, and HUD."""
        if not PYGAME_AVAILABLE or self.screen is None:
            return

        self.anim_tick += 1
        self.eval_score = self.evaluator.evaluate(state, player_id=0)

        # 1. Render Battlefield Ground & Grid
        self._render_battlefield(state)

        # 2. Render Entities (Walls, Bases, Tanks, Foliage)
        self._render_entities(state)

        # 3. Render In-Flight Bullets
        self._render_bullets(state)

        # 4. Render Particles (Treads, Muzzle Flashes, Hit Explosions)
        self._render_particles()

        # 5. Render Tactical Sensor Feed & Event Log underneath grid
        self._render_combat_log(state)

        # 6. Render Game-Over Modal if Terminal
        if state.is_terminal():
            self._render_game_over_banner(state, agent0, agent1)

        # 7. Render Tactical Sidebar HUD
        self._render_hud(state, agent0, agent1)

        # Update damage flashes
        for k in list(self.damage_flashes.keys()):
            self.damage_flashes[k] -= 1
            if self.damage_flashes[k] <= 0:
                del self.damage_flashes[k]

        pygame.display.flip()
        if not is_interpolating:
            self.clock.tick(self.fps)

    def _render_battlefield(self, state: GameState) -> None:
        """Draws textured sand terrain tiles with subtle tactical coordinates."""
        cs = self.cell_size
        sand_img = self.sprites.get("tile_sand")
        sand_img2 = self.sprites.get("tile_sand2")

        # Outer border frame
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
        """Renders the tactical combat log and sensor feed under the battlefield grid."""
        log_x = 0
        log_y = self.board_h
        log_w = self.board_w
        log_h = self.height_px - self.board_h

        if log_h <= 10:
            return

        # Container
        pygame.draw.rect(self.screen, (13, 16, 23), (log_x, log_y, log_w, log_h))
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (log_x, log_y), (log_w, log_y), 2)

        # Header Bar
        hdr_rect = pygame.Rect(log_x + 8, log_y + 6, log_w - 16, 20)
        pygame.draw.rect(self.screen, (20, 26, 38), hdr_rect, border_radius=3)
        pygame.draw.rect(self.screen, (34, 44, 62), hdr_rect, 1, border_radius=3)

        h_title = self.font_metric_lbl.render("TACTICAL SENSOR FEED & COMBAT EVENT LOG", True, self.COLOR_GOLD)
        self.screen.blit(h_title, (hdr_rect.x + 8, hdr_rect.y + 3))

        live_tag = self.font_coord.render("● LIVE FEED", True, self.COLOR_EMERALD)
        self.screen.blit(live_tag, (hdr_rect.x + hdr_rect.width - live_tag.get_width() - 8, hdr_rect.y + 3))

        # Render Log lines
        line_y = log_y + 32
        for item in self.combat_logs[-8:]:
            s_txt = item["text"]
            s_col = item["color"]
            line_surf = self.font_coord.render(s_txt, True, s_col)
            self.screen.blit(line_surf, (log_x + 14, line_y))
            line_y += 20

    def _render_entities(self, state: GameState) -> None:
        """Renders bases, walls, tanks, and foliage."""
        cs = self.cell_size

        tank_angle_map = {
            Direction.UP: 180,
            Direction.DOWN: 0,
            Direction.LEFT: 270,
            Direction.RIGHT: 90,
        }

        # 1. Base Command Outposts
        for pid, base in state.bases.items():
            if base.is_alive:
                bx = base.x * cs
                by = base.y * cs
                center_x = bx + cs // 2
                center_y = by + cs // 2
                base_color = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY

                # Radar pulse
                pulse_r = int((self.anim_tick % 24) / 24 * (cs // 2 + 2))
                radar_surf = pygame.Surface((cs + 8, cs + 8), pygame.SRCALPHA)
                pygame.draw.circle(radar_surf, (*base_color, 45), (cs // 2 + 4, cs // 2 + 4), cs // 2 - 2)
                if pulse_r > 4:
                    pygame.draw.circle(radar_surf, (*base_color, 80), (cs // 2 + 4, cs // 2 + 4), pulse_r, 2)
                self.screen.blit(radar_surf, (bx - 4, by - 4))

                # Metallic base platform
                pygame.draw.rect(self.screen, (32, 40, 54), (bx + 2, by + 2, cs - 4, cs - 4), border_radius=8)
                pygame.draw.rect(self.screen, base_color, (bx + 2, by + 2, cs - 4, cs - 4), 2, border_radius=8)

                base_key = f"base_{pid}"
                if base_key in self.sprites and self.sprites[base_key]:
                    self.screen.blit(self.sprites[base_key], (bx + 3, by + 3))
                else:
                    pygame.draw.circle(self.screen, (20, 60, 110) if pid == 0 else (120, 25, 25), (center_x, center_y), cs // 2 - 5)

                hq_badge = self.font_badge.render(f"HQ {pid}", True, (255, 255, 255))
                self.screen.blit(hq_badge, (center_x - hq_badge.get_width() // 2, center_y - hq_badge.get_height() // 2))

                # Segmented 9-cell HP bar
                self._draw_segmented_hp_bar(bx + 4, by - 2, base.hp, 9, seg_w=3, seg_h=4, color=base_color)

        # 2. Destructible Walls
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

                badge = self.font_small.render(str(wall.hp), True, (255, 255, 255))
                self.screen.blit(badge, (rx + cs - 14, ry + cs - 16))

        # 3. Tanks
        for pid, tank in state.tanks.items():
            if tank.is_alive:
                tx = tank.x * cs
                ty = tank.y * cs
                center_x = tx + cs // 2
                center_y = ty + cs // 2
                t_color = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY

                ring_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (*t_color, 70), (cs // 2, cs // 2), cs // 2 - 2, 2)
                self.screen.blit(ring_surf, (tx, ty))

                tank_key = f"tank_{pid}"
                if tank_key in self.sprites and self.sprites[tank_key]:
                    angle = tank_angle_map.get(tank.direction, 0)
                    rot_sprite = pygame.transform.rotate(self.sprites[tank_key], angle)
                    r_rect = rot_sprite.get_rect(center=(center_x, center_y))
                    self.screen.blit(rot_sprite, r_rect.topleft)
                else:
                    pygame.draw.circle(self.screen, t_color, (center_x, center_y), cs // 2 - 4)

                self._draw_segmented_hp_bar(tx + 4, ty - 2, tank.hp, 6, seg_w=5, seg_h=4, color=t_color)

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
                trail_color = (255, 230, 80) if owner == 0 else (255, 100, 80)
                pygame.draw.line(self.screen, (*trail_color, 160), (bx, by), (bx - dx * tail_len, by - dy * tail_len), 3)

                if b_key in self.sprites and self.sprites[b_key]:
                    angle = bullet_angle_map.get(ab["dir"], 0)
                    rot_b = pygame.transform.rotate(self.sprites[b_key], angle)
                    r_rect = rot_b.get_rect(center=(bx, by))
                    self.screen.blit(rot_b, r_rect.topleft)
                else:
                    pygame.draw.circle(self.screen, (255, 255, 255), (bx, by), 5)
                    pygame.draw.circle(self.screen, trail_color, (bx, by), 3)
            return

        for bullet in state.bullets:
            if bullet.is_active:
                bx = bullet.x * cs + cs // 2
                by = bullet.y * cs + cs // 2
                dx, dy = bullet.direction.value

                tail_len = cs // 2
                tx_end = bx - dx * tail_len
                ty_end = by - dy * tail_len
                b_color = (255, 220, 50)
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

        # 1. Tank Tread Tracks
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

        # 2. Muzzle Flashes
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

        # 3. Hit Smoke & Fiery Explosions
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
                    smoke_key = f"smoke_{min(3, exp_step)}"
                    if smoke_key in self.sprites and self.sprites[smoke_key]:
                        self.screen.blit(self.sprites[smoke_key], (px + 3, py + 3))
                    else:
                        r = int((frame_idx / exp["max_frames"]) * (cs // 2))
                        pygame.draw.circle(self.screen, (255, 120, 30), (px + cs // 2, py + cs // 2), r)
                active_exp.append(exp)
        self.explosions = active_exp

    def _draw_segmented_hp_bar(
        self, x: int, y: int, hp: int, max_hp: int,
        seg_w: int, seg_h: int, color
    ) -> None:
        """Draws discrete battery-style health bar pips above in-game entities."""
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

    def _draw_tactical_vitals_bar(
        self, x: int, y: int, w: int, hp: int, max_hp: int,
        team_color, title: str, status_text: str
    ) -> None:
        """
        Renders a modern power-cell vitals gauge with numeric readouts
        and discrete battery segments.
        """
        # Header label line
        lbl_surf = self.font_metric_lbl.render(title.upper(), True, self.COLOR_TEXT_DIM)
        self.screen.blit(lbl_surf, (x, y))

        st_c = team_color if hp > (max_hp // 2) else (self.COLOR_HP_YELLOW if hp > 0 else self.COLOR_HP_RED)
        st_surf = self.font_coord.render(status_text, True, st_c)
        self.screen.blit(st_surf, (x + w - st_surf.get_width(), y))

        # Battery Bar Container
        bar_y = y + 13
        bar_h = 7
        pygame.draw.rect(self.screen, (12, 16, 24), (x, bar_y, w, bar_h), border_radius=2)
        pygame.draw.rect(self.screen, (32, 42, 60), (x, bar_y, w, bar_h), 1, border_radius=2)

        # Segmented pips
        gap = 2
        seg_w = max(2, (w - 4 - (max_hp - 1) * gap) // max_hp)
        start_x = x + 2
        for i in range(max_hp):
            px = start_x + i * (seg_w + gap)
            if px + seg_w > x + w - 2:
                seg_w = max(1, (x + w - 2) - px)
            if i < hp:
                ratio = hp / max_hp
                pip_c = team_color if ratio > 0.5 else (self.COLOR_HP_YELLOW if ratio > 0.25 else self.COLOR_HP_RED)
                pygame.draw.rect(self.screen, pip_c, (px, bar_y + 1, seg_w, bar_h - 2), border_radius=1)
            else:
                pygame.draw.rect(self.screen, (24, 30, 42), (px, bar_y + 1, seg_w, bar_h - 2), border_radius=1)

    def _draw_metric_chip(
        self, x: int, y: int, w: int, h: int,
        label: str, value_str: str, value_color,
        subtext: Optional[str] = None, progress_pct: Optional[float] = None
    ) -> None:
        """
        Renders a recessed digital instrument tile with monospace typography
        and optional mini progress fill bar.
        """
        chip_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BG, chip_rect, border_radius=4)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, chip_rect, 1, border_radius=4)

        # Micro header label
        lbl_surf = self.font_metric_lbl.render(label, True, (120, 140, 170))
        self.screen.blit(lbl_surf, (x + 6, y + 4))

        # Monospace digital value
        val_surf = self.font_metric_val.render(value_str, True, value_color)
        self.screen.blit(val_surf, (x + 6, y + 15))

        # Progress bar or subtext
        if progress_pct is not None:
            p_bar_w = w - 12
            p_bar_y = y + h - 6
            pygame.draw.rect(self.screen, (24, 32, 46), (x + 6, p_bar_y, p_bar_w, 3), border_radius=1)
            fill_w = int(max(0.0, min(1.0, progress_pct)) * p_bar_w)
            if fill_w > 0:
                pygame.draw.rect(self.screen, value_color, (x + 6, p_bar_y, fill_w, 3), border_radius=1)
        elif subtext:
            sub_surf = self.font_coord.render(subtext, True, self.COLOR_TEXT_MUTED)
            self.screen.blit(sub_surf, (x + 6, y + h - 13))

    def _render_hud(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """Renders the entire sidebar command dashboard with live telemetry and buttons."""
        sidebar_x = self.board_w
        sidebar_rect = (sidebar_x, 0, self.sidebar_width, self.height_px)
        pygame.draw.rect(self.screen, self.COLOR_SIDEBAR_BG, sidebar_rect)
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (sidebar_x, 0), (sidebar_x, self.height_px), 2)

        pad_x = sidebar_x + 14
        card_w = self.sidebar_width - 28
        curr_y = 10

        # 1. Header Banner & Current Map Badge
        title_surf = self.font_title.render("BATTLE CITY COMMAND DECK", True, self.COLOR_GOLD)
        self.screen.blit(title_surf, (pad_x, curr_y))

        clean_name = self.current_map_title.replace(".txt", "").replace("_", " ").upper()
        if len(clean_name) > 18:
            clean_name = clean_name[:17] + ".."
        map_surf = self.font_coord.render(clean_name, True, self.COLOR_GOLD)
        mb_w = map_surf.get_width() + 12
        mb_rect = (pad_x + card_w - mb_w, curr_y, mb_w, 20)
        pygame.draw.rect(self.screen, (28, 36, 52), mb_rect, border_radius=4)
        pygame.draw.rect(self.screen, self.COLOR_GOLD, mb_rect, 1, border_radius=4)
        self.screen.blit(map_surf, (mb_rect[0] + 6, mb_rect[1] + 3))

        curr_y += 22
        deck_sub = self.font_small.render("Adversarial Search & Multi-Agent Simulator • TDTU", True, self.COLOR_TEXT_DIM)
        self.screen.blit(deck_sub, (pad_x, curr_y))
        curr_y += 18

        # 2. Cycle Progress Bar & Match Status Pill
        cycle_pct = min(1.0, state.game_cycle / max(1, state.max_cycles))
        bar_rect = (pad_x, curr_y, card_w, 6)
        pygame.draw.rect(self.screen, (28, 36, 50), bar_rect, border_radius=3)
        if cycle_pct > 0:
            pygame.draw.rect(self.screen, self.COLOR_GOLD, (pad_x, curr_y, int(card_w * cycle_pct), 6), border_radius=3)
        curr_y += 9

        cycle_txt = self.font_badge.render(f"CYCLE {state.game_cycle} / {state.max_cycles}", True, self.COLOR_TEXT)
        self.screen.blit(cycle_txt, (pad_x, curr_y))

        # Status Pill
        active_agent = agent0 if state.current_player == 0 else agent1
        active_is_human = getattr(active_agent, "is_human", False)

        if state.is_terminal():
            status_text = "MATCH CONCLUDED"
            status_c = (190, 45, 45)
        elif self.is_paused:
            status_text = "PAUSED [SPACE]"
            status_c = self.COLOR_AMBER
        elif active_is_human:
            status_text = f"HUMAN TURN (P{state.current_player})"
            status_c = (39, 174, 96)
        else:
            turn_name = "P0 (MAX)" if state.current_player == 0 else "P1 (MIN)"
            status_text = f"THINKING: {turn_name}"
            status_c = (35, 125, 75)

        pill_surf = self.font_badge.render(status_text, True, (255, 255, 255))
        pill_w = pill_surf.get_width() + 12
        pill_rect = (pad_x + card_w - pill_w, curr_y - 2, pill_w, 18)
        pygame.draw.rect(self.screen, status_c, pill_rect, border_radius=4)
        self.screen.blit(pill_surf, (pill_rect[0] + 6, pill_rect[1] + 2))
        curr_y += 24

        # 3. Interactive Action Buttons & Speed Toggles
        curr_y = self._render_control_buttons(pad_x, curr_y, card_w)

        # 4. Smooth Heuristic Advantage Gauge (e(s))
        curr_y = self._render_eval_gauge(pad_x, curr_y, card_w)

        # 5. Player 0 Card (Blue Team MAX)
        curr_y = self._draw_player_card(
            x=pad_x, y=curr_y, width=card_w, pid=0,
            agent=agent0,
            tank=state.tanks.get(0),
            base=state.bases.get(0),
            is_active_turn=(state.current_player == 0 and not state.is_terminal()),
            primary_color=self.COLOR_P0_PRIMARY,
            bg_color=self.COLOR_P0_BG,
            border_color=self.COLOR_P0_BORDER
        )
        curr_y += 6

        # 6. Player 1 Card (Red Team MIN)
        curr_y = self._draw_player_card(
            x=pad_x, y=curr_y, width=card_w, pid=1,
            agent=agent1,
            tank=state.tanks.get(1),
            base=state.bases.get(1),
            is_active_turn=(state.current_player == 1 and not state.is_terminal()),
            primary_color=self.COLOR_P1_PRIMARY,
            bg_color=self.COLOR_P1_BG,
            border_color=self.COLOR_P1_BORDER
        )
        curr_y += 6

        # 7. Bottom Context Area: Human D-Pad OR Combat Specs
        if active_is_human and not state.is_terminal():
            curr_y = self._render_human_dpad(pad_x, curr_y, card_w, state.current_player)
        else:
            curr_y = self._render_specs_legend(pad_x, curr_y, card_w)

        # 8. Quick Shortcuts Footer
        self._render_shortcuts_footer(pad_x, curr_y, card_w)

    def _render_control_buttons(self, x: int, y: int, width: int) -> int:
        """Renders clickable interactive control buttons and speed toggles with hover feedback."""
        mx, my = pygame.mouse.get_pos()

        for btn in self.buttons:
            if btn["id"] == "play_pause":
                btn["label"] = "RESUME" if self.is_paused else "PAUSE"
                break

        # Draw Row 1: Action buttons
        for btn in self.buttons:
            r = btn["rect"]
            r.top = y
            is_hover = r.collidepoint(mx, my)
            btn_bg = (48, 62, 88) if is_hover else (28, 36, 50)
            pygame.draw.rect(self.screen, btn_bg, r, border_radius=4)
            pygame.draw.rect(self.screen, self.COLOR_GOLD if is_hover else (42, 54, 76), r, 1, border_radius=4)

            lbl = self.font_small.render(btn["label"], True, (255, 255, 255) if is_hover else self.COLOR_TEXT)
            self.screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        y += 30

        # Draw Row 2: Speed buttons
        for sbtn in self.speed_buttons:
            r = sbtn["rect"]
            r.top = y
            is_active = (self.speed_multiplier == sbtn["val"])
            is_hover = r.collidepoint(mx, my)

            s_bg = (24, 68, 42) if is_active else ((42, 54, 76) if is_hover else (24, 30, 42))
            pygame.draw.rect(self.screen, s_bg, r, border_radius=4)
            border_c = (46, 204, 113) if is_active else (self.COLOR_GOLD if is_hover else (38, 50, 70))
            pygame.draw.rect(self.screen, border_c, r, 1, border_radius=4)

            lbl_color = (255, 255, 255) if (is_active or is_hover) else self.COLOR_TEXT_DIM
            lbl = self.font_small.render(sbtn["label"], True, lbl_color)
            self.screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        return y + 26

    def _render_eval_gauge(self, x: int, y: int, width: int) -> int:
        """
        Renders a dynamic bidirectional tactical advantage gauge with smooth exponential
        interpolation (lerp), graduation tick marks, and dominance indicator.
        """
        # Smooth interpolation to eliminate sudden jitter between turns
        self.smooth_eval += (self.eval_score - self.smooth_eval) * 0.15
        clamped_score = max(-100.0, min(100.0, self.smooth_eval))

        gauge_h = 32
        container_rect = pygame.Rect(x, y, width, gauge_h)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BG, container_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, container_rect, 1, border_radius=6)

        # 1. Header line inside gauge
        lbl_surf = self.font_metric_lbl.render("TACTICAL INITIATIVE", True, (130, 150, 180))
        self.screen.blit(lbl_surf, (x + 8, y + 4))

        # Dynamic dominance status
        score_val = self.eval_score
        sign = "+" if score_val > 0 else ""
        if score_val > 10:
            dom_text = f"BLUE DOMINANCE ({sign}{score_val:.1f})"
            dom_color = self.COLOR_P0_PRIMARY
        elif score_val > 2:
            dom_text = f"BLUE ADVANTAGE ({sign}{score_val:.1f})"
            dom_color = self.COLOR_P0_PRIMARY
        elif score_val < -10:
            dom_text = f"RED DOMINANCE ({sign}{score_val:.1f})"
            dom_color = self.COLOR_P1_PRIMARY
        elif score_val < -2:
            dom_text = f"RED ADVANTAGE ({sign}{score_val:.1f})"
            dom_color = self.COLOR_P1_PRIMARY
        else:
            dom_text = f"CONTESTED EQUILIBRIUM ({sign}{score_val:.1f})"
            dom_color = self.COLOR_GOLD

        dom_surf = self.font_metric_lbl.render(dom_text, True, dom_color)
        self.screen.blit(dom_surf, (x + width - dom_surf.get_width() - 8, y + 4))

        # 2. Recessed Gauge Groove
        groove_x = x + 8
        groove_y = y + 18
        groove_w = width - 16
        groove_h = 8
        groove_rect = pygame.Rect(groove_x, groove_y, groove_w, groove_h)
        pygame.draw.rect(self.screen, (10, 14, 20), groove_rect, border_radius=3)
        pygame.draw.rect(self.screen, (28, 36, 52), groove_rect, 1, border_radius=3)

        # Center line
        center_x = groove_x + groove_w // 2
        pygame.draw.line(self.screen, (60, 72, 95), (center_x, groove_y - 2), (center_x, groove_y + groove_h + 2), 1)

        # Graduation ticks at -75, -50, -25, +25, +50, +75
        half_w = groove_w // 2
        for pct in (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75):
            tx = int(center_x + pct * half_w)
            pygame.draw.line(self.screen, (36, 44, 60), (tx, groove_y + 1), (tx, groove_y + groove_h - 1), 1)

        # Fill bar from center
        bar_len = int(abs(clamped_score) / 100.0 * half_w)
        if clamped_score > 0:
            fill_rect = pygame.Rect(center_x, groove_y + 1, bar_len, groove_h - 2)
            pygame.draw.rect(self.screen, self.COLOR_P0_PRIMARY, fill_rect, border_radius=2)
        elif clamped_score < 0:
            fill_rect = pygame.Rect(center_x - bar_len, groove_y + 1, bar_len, groove_h - 2)
            pygame.draw.rect(self.screen, self.COLOR_P1_PRIMARY, fill_rect, border_radius=2)

        # Moving needle cursor (diamond)
        cursor_x = center_x + int(clamped_score / 100.0 * half_w)
        cursor_pts = [
            (cursor_x, groove_y - 2),
            (cursor_x + 3, groove_y + groove_h // 2),
            (cursor_x, groove_y + groove_h + 2),
            (cursor_x - 3, groove_y + groove_h // 2),
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), cursor_pts)

        return y + gauge_h + 8

    def _draw_player_card(
        self, x: int, y: int, width: int, pid: int,
        agent: BaseAgent, tank, base, is_active_turn: bool,
        primary_color, bg_color, border_color
    ) -> int:
        """
        Renders a cohesive esports telemetry card featuring:
        - Embedded Kenney tank avatar & team role
        - Smooth breathing pulse for active player turn
        - Interactive algorithm carousel & depth selector
        - Segmented tactical power-cell vitals (Tank HP & Base HP)
        - 4 Monospace Digital Telemetry Chips (Depth, Nodes, Pruning %, Latency)
        """
        card_h = 180
        card_rect = pygame.Rect(x, y, width, card_h)

        # 1. Background & Pulsing Active Turn Border
        pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=6)

        import math
        pulse = (math.sin(self.anim_tick * 0.12) + 1.0) / 2.0  # 0.0 to 1.0

        if is_active_turn:
            glow_c = (
                min(255, int(primary_color[0] + pulse * 50)),
                min(255, int(primary_color[1] + pulse * 50)),
                min(255, int(primary_color[2] + pulse * 50)),
            )
            pygame.draw.rect(self.screen, glow_c, card_rect, 2, border_radius=6)
        else:
            pygame.draw.rect(self.screen, border_color, card_rect, 1, border_radius=6)

        cy = y + 7

        # 2. Top Header: Avatar Inset + Role + Turn Status Badge
        avatar_key = f"tank_{pid}_icon"
        avatar_img = self.sprites.get(avatar_key)
        avatar_rect = pygame.Rect(x + 8, cy, 28, 28)
        pygame.draw.rect(self.screen, (16, 22, 32), avatar_rect, border_radius=4)
        pygame.draw.rect(self.screen, border_color, avatar_rect, 1, border_radius=4)
        if avatar_img:
            self.screen.blit(avatar_img, (avatar_rect.centerx - avatar_img.get_width() // 2, avatar_rect.centery - avatar_img.get_height() // 2))

        # Title & Subtitle
        role_title = "PLAYER 0  [MAX]" if pid == 0 else "PLAYER 1  [MIN]"
        role_sub = "Blue Coalition • Objective MAX" if pid == 0 else "Red Regiment • Objective MIN"
        t_surf = self.font_header.render(role_title, True, primary_color)
        s_surf = self.font_coord.render(role_sub, True, self.COLOR_TEXT_DIM)
        self.screen.blit(t_surf, (x + 42, cy))
        self.screen.blit(s_surf, (x + 42, cy + 15))

        # Turn Badge
        is_human = getattr(agent, "is_human", False)
        if is_active_turn:
            badge_text = "● YOUR TURN!" if is_human else "● THINKING..."
            badge_bg = (39, 174, 96) if is_human else primary_color
            tb_surf = self.font_badge.render(badge_text, True, (255, 255, 255))
            tb_w = tb_surf.get_width() + 12
            tb_rect = pygame.Rect(x + width - tb_w - 8, cy + 3, tb_w, 20)
            pygame.draw.rect(self.screen, badge_bg, tb_rect, border_radius=4)
            self.screen.blit(tb_surf, (tb_rect.x + 6, tb_rect.y + 3))
        else:
            tb_surf = self.font_coord.render("STANDBY", True, self.COLOR_TEXT_MUTED)
            tb_w = tb_surf.get_width() + 10
            tb_rect = pygame.Rect(x + width - tb_w - 8, cy + 3, tb_w, 18)
            pygame.draw.rect(self.screen, (22, 28, 38), tb_rect, border_radius=3)
            pygame.draw.rect(self.screen, (38, 48, 64), tb_rect, 1, border_radius=3)
            self.screen.blit(tb_surf, (tb_rect.x + 5, tb_rect.y + 2))

        cy += 31

        # 3. Algorithm Selector Row: [<]  Algorithm Capsule  [>]    Depth: [-] d [+]
        mx, my = pygame.mouse.get_pos()
        sel_idx = self.p0_algo_idx if pid == 0 else self.p1_algo_idx
        sel_key, sel_label = AGENT_PRESETS[sel_idx]

        btn_prev_rect = pygame.Rect(x + 8, cy, 22, 22)
        btn_next_rect = pygame.Rect(x + 236, cy, 22, 22)
        if pid == 0:
            self.p0_algo_prev_rect = btn_prev_rect
            self.p0_algo_next_rect = btn_next_rect
        else:
            self.p1_algo_prev_rect = btn_prev_rect
            self.p1_algo_next_rect = btn_next_rect

        # Hover states
        prev_hover = btn_prev_rect.collidepoint(mx, my)
        next_hover = btn_next_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (42, 54, 76) if prev_hover else (24, 32, 46), btn_prev_rect, border_radius=3)
        pygame.draw.rect(self.screen, (42, 54, 76) if next_hover else (24, 32, 46), btn_next_rect, border_radius=3)
        pygame.draw.rect(self.screen, self.COLOR_GOLD if prev_hover else (38, 50, 70), btn_prev_rect, 1, border_radius=3)
        pygame.draw.rect(self.screen, self.COLOR_GOLD if next_hover else (38, 50, 70), btn_next_rect, 1, border_radius=3)

        lbl_prev = self.font_badge.render("<", True, (255, 255, 255))
        lbl_next = self.font_badge.render(">", True, (255, 255, 255))
        self.screen.blit(lbl_prev, (btn_prev_rect.centerx - lbl_prev.get_width() // 2, btn_prev_rect.centery - lbl_prev.get_height() // 2))
        self.screen.blit(lbl_next, (btn_next_rect.centerx - lbl_next.get_width() // 2, btn_next_rect.centery - lbl_next.get_height() // 2))

        # Central Capsule
        algo_capsule_rect = pygame.Rect(x + 34, cy, 198, 22)
        pygame.draw.rect(self.screen, (16, 22, 34), algo_capsule_rect, border_radius=3)
        pygame.draw.rect(self.screen, primary_color if is_active_turn else (38, 50, 70), algo_capsule_rect, 1, border_radius=3)
        algo_txt = sel_label[:27]
        algo_surf = self.font_small.render(algo_txt, True, (245, 248, 255))
        self.screen.blit(algo_surf, (algo_capsule_rect.centerx - algo_surf.get_width() // 2, algo_capsule_rect.centery - algo_surf.get_height() // 2))

        # Depth stepper or Mode Badge
        cur_depth = self.p0_depth if pid == 0 else self.p1_depth
        if sel_key not in ("human", "greedy"):
            d_x = x + 266
            lbl_dep = self.font_metric_lbl.render("DEPTH", True, self.COLOR_TEXT_DIM)
            self.screen.blit(lbl_dep, (d_x, cy + 5))

            d_dec = pygame.Rect(d_x + 38, cy, 20, 22)
            d_inc = pygame.Rect(d_x + 82, cy, 20, 22)
            if pid == 0:
                self.p0_depth_dec_rect = d_dec
                self.p0_depth_inc_rect = d_inc
            else:
                self.p1_depth_dec_rect = d_dec
                self.p1_depth_inc_rect = d_inc

            dec_hover = d_dec.collidepoint(mx, my)
            inc_hover = d_inc.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (42, 54, 76) if dec_hover else (24, 32, 46), d_dec, border_radius=3)
            pygame.draw.rect(self.screen, (42, 54, 76) if inc_hover else (24, 32, 46), d_inc, border_radius=3)
            pygame.draw.rect(self.screen, self.COLOR_GOLD if dec_hover else (38, 50, 70), d_dec, 1, border_radius=3)
            pygame.draw.rect(self.screen, self.COLOR_GOLD if inc_hover else (38, 50, 70), d_inc, 1, border_radius=3)

            lbl_m = self.font_small.render("-", True, (255, 255, 255))
            lbl_p = self.font_small.render("+", True, (255, 255, 255))
            self.screen.blit(lbl_m, (d_dec.centerx - lbl_m.get_width() // 2, d_dec.centery - lbl_m.get_height() // 2))
            self.screen.blit(lbl_p, (d_inc.centerx - lbl_p.get_width() // 2, d_inc.centery - lbl_p.get_height() // 2))

            val_surf = self.font_metric_val.render(str(cur_depth), True, self.COLOR_GOLD)
            self.screen.blit(val_surf, (d_x + 64, cy + 3))
        elif sel_key == "human":
            h_pill = pygame.Rect(x + 266, cy, width - 274, 22)
            pygame.draw.rect(self.screen, (20, 48, 32), h_pill, border_radius=3)
            pygame.draw.rect(self.screen, (46, 204, 113), h_pill, 1, border_radius=3)
            h_hint = self.font_coord.render("MANUAL COCKPIT", True, (46, 204, 113))
            self.screen.blit(h_hint, (h_pill.centerx - h_hint.get_width() // 2, h_pill.centery - h_hint.get_height() // 2))
        else:
            g_pill = pygame.Rect(x + 266, cy, width - 274, 22)
            pygame.draw.rect(self.screen, (48, 38, 20), g_pill, border_radius=3)
            pygame.draw.rect(self.screen, (241, 196, 15), g_pill, 1, border_radius=3)
            g_hint = self.font_coord.render("1-PLY REFLEX", True, (241, 196, 15))
            self.screen.blit(g_hint, (g_pill.centerx - g_hint.get_width() // 2, g_pill.centery - g_hint.get_height() // 2))

        cy += 28

        # 4. Vitals Gauges: Tank Hull (6 HP) & Base HQ (9 HP)
        t_hp = tank.hp if (tank and tank.is_alive) else 0
        b_hp = base.hp if (base and base.is_alive) else 0

        # Tank vitals
        t_status = f"({tank.x},{tank.y}) {tank.direction.name}" if (tank and tank.is_alive) else "DESTROYED"
        vitals_w = width - 16
        self._draw_tactical_vitals_bar(
            x=x + 8, y=cy, w=vitals_w,
            hp=t_hp, max_hp=6,
            team_color=primary_color,
            title=f"TANK HULL • {t_hp}/6 HP",
            status_text=t_status
        )
        cy += 23

        # Base vitals
        b_status = "SECURE" if b_hp >= 6 else ("UNDER ATTACK" if b_hp > 0 else "BREACHED")
        self._draw_tactical_vitals_bar(
            x=x + 8, y=cy, w=vitals_w,
            hp=b_hp, max_hp=9,
            team_color=primary_color,
            title=f"BASE HQ • {b_hp}/9 HP",
            status_text=b_status
        )
        cy += 25

        # 5. AI Digital Telemetry Hub (4 Metric Chips)
        deck_y = cy
        deck_w = width - 16
        deck_h = 44

        if is_human:
            # Human Pilot Guidance Deck
            h_deck_rect = pygame.Rect(x + 8, deck_y, deck_w, deck_h)
            pygame.draw.rect(self.screen, self.COLOR_INSET_BG, h_deck_rect, border_radius=4)
            pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, h_deck_rect, 1, border_radius=4)

            # 4 Keycap badges
            kw = (deck_w - 20) // 4
            keycaps = [
                ("[W,A,S,D]", "NAVIGATE", (52, 219, 219)),
                ("[SPACE]", "FIRE SHELL", (255, 120, 120)),
                ("[X]", "STANDBY", self.COLOR_TEXT_DIM),
                ("[D-PAD]", "TOUCH READY", (46, 204, 113)),
            ]
            for i, (k_btn, k_act, k_c) in enumerate(keycaps):
                kx = x + 10 + i * (kw + 4)
                pygame.draw.rect(self.screen, (22, 28, 40), (kx, deck_y + 4, kw, deck_h - 8), border_radius=3)
                pygame.draw.rect(self.screen, (38, 48, 66), (kx, deck_y + 4, kw, deck_h - 8), 1, border_radius=3)
                ks = self.font_metric_val.render(k_btn, True, k_c)
                as_ = self.font_metric_lbl.render(k_act, True, self.COLOR_TEXT_DIM)
                self.screen.blit(ks, (kx + (kw - ks.get_width()) // 2, deck_y + 7))
                self.screen.blit(as_, (kx + (kw - as_.get_width()) // 2, deck_y + 24))
        elif sel_key == "greedy":
            # 1-Ply Reflex Deck
            stats = agent.stats if agent else None
            t_ms = (stats.execution_time * 1000) if stats else 0.2
            gw = (deck_w - 6) // 2
            self._draw_metric_chip(
                x=x + 8, y=deck_y, w=gw, h=deck_h,
                label="ENGINE TYPE",
                value_str="1-PLY REFLEX",
                value_color=(241, 196, 15),
                subtext="Instant scoring"
            )
            self._draw_metric_chip(
                x=x + 8 + gw + 6, y=deck_y, w=gw, h=deck_h,
                label="EXECUTION TIME",
                value_str=f"{t_ms:.2f} ms",
                value_color=(160, 205, 255),
                subtext="Reactive baseline"
            )
        else:
            # Full 4-Chip Digital Telemetry Suite
            stats = agent.stats if agent else None
            d_val = stats.search_depth if stats else cur_depth
            prunes = stats.prune_count if stats else 0
            nodes = stats.explored_nodes if stats else 0
            t_ms = (stats.execution_time * 1000) if stats else 0.0

            total_branches = nodes + prunes
            prune_pct = int(prunes / total_branches * 100) if total_branches > 0 else 0
            is_ab = ("alpha" in agent.name.lower() or "ab" in agent.name.lower() or prunes > 0)

            chip_w = (deck_w - 18) // 4
            # Chip 1: Depth
            self._draw_metric_chip(
                x=x + 8, y=deck_y, w=chip_w, h=deck_h,
                label="DEPTH",
                value_str=f"d = {d_val}",
                value_color=self.COLOR_CYAN,
                subtext="Tree cutoff"
            )
            # Chip 2: Nodes
            self._draw_metric_chip(
                x=x + 8 + (chip_w + 6), y=deck_y, w=chip_w, h=deck_h,
                label="NODES",
                value_str=f"{nodes:,}",
                value_color=self.COLOR_GOLD,
                subtext="States expanded"
            )
            # Chip 3: Pruning %
            prune_val_str = f"{prune_pct}%" if is_ab else "0%"
            prune_sub = f"{prunes:,} cuts" if is_ab else "Minimax"
            self._draw_metric_chip(
                x=x + 8 + 2 * (chip_w + 6), y=deck_y, w=chip_w, h=deck_h,
                label="PRUNED",
                value_str=prune_val_str,
                value_color=self.COLOR_EMERALD if is_ab else self.COLOR_TEXT_MUTED,
                progress_pct=(prune_pct / 100.0) if is_ab else None,
                subtext=prune_sub
            )
            # Chip 4: Latency
            self._draw_metric_chip(
                x=x + 8 + 3 * (chip_w + 6), y=deck_y, w=chip_w, h=deck_h,
                label="LATENCY",
                value_str=f"{t_ms:.1f}ms",
                value_color=(160, 205, 255),
                subtext="Decision time"
            )

        return y + card_h

    def _render_human_dpad(self, x: int, y: int, width: int, active_pid: int) -> int:
        """Renders interactive clickable on-screen D-Pad and Fire buttons for human player."""
        card_h = 120
        rect = pygame.Rect(x, y, width, card_h)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BG, rect, border_radius=6)
        team_color = self.COLOR_P0_PRIMARY if active_pid == 0 else self.COLOR_P1_PRIMARY
        pygame.draw.rect(self.screen, team_color, rect, 1, border_radius=6)

        hdr_txt = f"PILOT COCKPIT: P{active_pid} CONTROLS (KEYBOARD / CLICK D-PAD)"
        hdr_surf = self.font_metric_lbl.render(hdr_txt, True, self.COLOR_GOLD)
        self.screen.blit(hdr_surf, (x + 10, y + 6))

        mx, my = pygame.mouse.get_pos()
        self.dpad_buttons = []

        # D-Pad Button Layout
        bx = x + 24
        by = y + 24
        bs = 26

        dpad_defs = [
            ("▲", Action.MOVE_UP,    pygame.Rect(bx + bs + 4, by, bs, bs)),
            ("◀", Action.MOVE_LEFT,  pygame.Rect(bx, by + bs + 4, bs, bs)),
            ("▼", Action.MOVE_DOWN,  pygame.Rect(bx + bs + 4, by + bs + 4, bs, bs)),
            ("▶", Action.MOVE_RIGHT, pygame.Rect(bx + 2 * (bs + 4), by + bs + 4, bs, bs)),
        ]

        for lbl_char, act, b_rect in dpad_defs:
            is_hover = b_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (48, 62, 88) if is_hover else (26, 34, 48), b_rect, border_radius=4)
            pygame.draw.rect(self.screen, team_color if is_hover else self.COLOR_CARD_BORDER, b_rect, 1, border_radius=4)
            s = self.font_badge.render(lbl_char, True, (255, 255, 255))
            self.screen.blit(s, (b_rect.centerx - s.get_width() // 2, b_rect.centery - s.get_height() // 2))
            self.dpad_buttons.append({"action": act, "rect": b_rect})

        # FIRE & STAY Buttons
        fire_rect = pygame.Rect(x + 150, by + 4, 130, 36)
        is_fire_hover = fire_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (190, 45, 45) if is_fire_hover else (150, 30, 30), fire_rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 120, 120) if is_fire_hover else (200, 70, 70), fire_rect, 1, border_radius=6)
        f_lbl = self.font_header.render("💥 FIRE (SPACE)", True, (255, 255, 255))
        self.screen.blit(f_lbl, (fire_rect.centerx - f_lbl.get_width() // 2, fire_rect.centery - f_lbl.get_height() // 2))
        self.dpad_buttons.append({"action": Action.FIRE, "rect": fire_rect})

        stay_rect = pygame.Rect(x + 290, by + 4, 120, 36)
        is_stay_hover = stay_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (42, 54, 76) if is_stay_hover else (26, 34, 48), stay_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_GOLD if is_stay_hover else self.COLOR_CARD_BORDER, stay_rect, 1, border_radius=6)
        st_lbl = self.font_header.render("⏸ STAY (X)", True, (240, 240, 240))
        self.screen.blit(st_lbl, (stay_rect.centerx - st_lbl.get_width() // 2, stay_rect.centery - st_lbl.get_height() // 2))
        self.dpad_buttons.append({"action": Action.STAY, "rect": stay_rect})

        hint_str = "Keys: W/A/S/D or Arrows • SPACE Fire • X Stay • Mouse Click on buttons"
        hint_surf = self.font_coord.render(hint_str, True, self.COLOR_TEXT_DIM)
        self.screen.blit(hint_surf, (x + 12, y + card_h - 18))

        return y + card_h + 6

    def _render_specs_legend(self, x: int, y: int, width: int) -> int:
        """
        Renders the Tactical Armory & Asset Specifications showcase, seamlessly embedding
        authentic Kenney sprites (Crates, Sandbags, Shells, Tanks, and Radar HQs).
        """
        card_h = 120
        rect = pygame.Rect(x, y, width, card_h)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BG, rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, rect, 1, border_radius=6)

        hdr_surf = self.font_metric_lbl.render("TACTICAL ARMORY & ASSET SPECIFICATIONS (KENNEY SPEC)", True, self.COLOR_GOLD)
        self.screen.blit(hdr_surf, (x + 10, y + 6))

        # 3x2 Matrix of Asset Tiles
        col_w = (width - 24) // 3
        row_h = 38
        y_start = y + 24

        specs_items = [
            # Row 1
            ("crate_metal_spec", "Metal Wall", "HP: 3 (Reinforced)", (x + 8, y_start)),
            ("crate_wood_spec",  "Wood Wall",  "HP: 2 (Destructible)", (x + 8 + col_w + 4, y_start)),
            ("sandbag_spec",     "Sandbag",    "HP: 1 (Light Cover)",  (x + 8 + 2 * (col_w + 4), y_start)),
            # Row 2
            ("bullet_icon",      "Kinetic Shell", "Spd: 3 cells/cycle", (x + 8, y_start + row_h + 4)),
            ("tank_0_icon",      "Combat Tank",  "HP: 6 (1 Dmg/Hit)",  (x + 8 + col_w + 4, y_start + row_h + 4)),
            ("base_0_icon",      "Command Base", "HP: 9 (Core Target)", (x + 8 + 2 * (col_w + 4), y_start + row_h + 4)),
        ]

        for sprite_key, title, spec_desc, (tx, ty) in specs_items:
            tile_rect = pygame.Rect(tx, ty, col_w, row_h)
            pygame.draw.rect(self.screen, self.COLOR_INSET_BG, tile_rect, border_radius=4)
            pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, tile_rect, 1, border_radius=4)

            sp = self.sprites.get(sprite_key)
            if sp:
                self.screen.blit(sp, (tx + 6, ty + (row_h - sp.get_height()) // 2))

            ts = self.font_small.render(title, True, self.COLOR_TEXT)
            ds = self.font_coord.render(spec_desc, True, self.COLOR_TEXT_DIM)
            self.screen.blit(ts, (tx + 32, ty + 4))
            self.screen.blit(ds, (tx + 32, ty + 18))

        return y + card_h

    def _render_shortcuts_footer(self, x: int, y: int, width: int) -> None:
        """Renders keyboard shortcuts quick guide."""
        card_h = 24
        rect = (x, y, width, card_h)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BG, rect, border_radius=4)
        pygame.draw.rect(self.screen, self.COLOR_INSET_BORDER, rect, 1, border_radius=4)

        s_txt = "[SPACE] Pause/Fire • [S] Step +1 • [U] Undo • [R] Reset • [M] Cycle Map • [1-4] Speed"
        s_surf = self.font_coord.render(s_txt, True, self.COLOR_TEXT_DIM)
        self.screen.blit(s_surf, (x + (width - s_surf.get_width()) // 2, y + 5))

    def _render_game_over_banner(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """Draws victory/draw banner."""
        winner = state.get_winner()
        b_w = self.board_w
        b_h = self.board_h

        tint = pygame.Surface((b_w, b_h), pygame.SRCALPHA)
        tint.fill((10, 14, 22, 175))
        self.screen.blit(tint, (0, 0))

        card_w = 380
        card_h = 160
        cx = (b_w - card_w) // 2
        cy = (b_h - card_h) // 2

        pygame.draw.rect(self.screen, (24, 32, 46), (cx, cy, card_w, card_h), border_radius=10)
        border_c = (self.COLOR_P0_PRIMARY if winner == 0 else
                    (self.COLOR_P1_PRIMARY if winner == 1 else self.COLOR_GOLD))
        pygame.draw.rect(self.screen, border_c, (cx, cy, card_w, card_h), 2, border_radius=10)

        if winner == 0:
            w_title = "VICTORY: PLAYER 0 (MAX)"
            w_name = agent0.name if agent0 else "Player 0"
            w_color = self.COLOR_P0_PRIMARY
        elif winner == 1:
            w_title = "VICTORY: PLAYER 1 (MIN)"
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

        hint_surf = self.font_small.render("Press [U] to Undo last move   |   [R] to Restart match", True, self.COLOR_GOLD)
        self.screen.blit(hint_surf, (cx + (card_w - hint_surf.get_width()) // 2, cy + 90))

        esc_surf = self.font_small.render("Press [ESC] to Exit", True, self.COLOR_TEXT_DIM)
        self.screen.blit(esc_surf, (cx + (card_w - esc_surf.get_width()) // 2, cy + 118))
