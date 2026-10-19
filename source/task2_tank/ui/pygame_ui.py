"""
pygame_ui.py - Professional Esports Tactical GUI for Tank Battle Game
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Implements a responsive, feature-rich PyGame GUI (Req 3 - 0.5 pt) with:
    1. Vibrant, high-contrast Battle City terrain (sand floor, green foliage canopy,
       distinct wood/metal crates, sandbags, and base radar circles).
    2. Real-time dynamic HUD updating search depth, node count, prune count,
       evaluation score gauge, execution latency (ms), and search speed (nodes/sec).
    3. Interactive Command Deck with clickable mouse buttons and keyboard shortcuts:
       - Play / Pause (SPACE)
       - Step Forward +1 (S / ENTER / Right Arrow)
       - Step Backward / Undo -1 (U / Z / Backspace / Left Arrow)
       - Match Reset / Restart (R)
       - Speed Presets: 1x, 2x, 4x (Keys 1, 2, 3)
    4. Punchy visual effects:
       - Fading tank tread tracks on sand
       - Animated smoke/hit explosions on damaged entities
       - Glowing bullet trajectories and muzzle flashes
       - Subtle grid coordinate labels (0..12) for academic review
       - Segmented battery-style health bars with color thresholds
       - Victory / Draw modal overlay banner
"""

import os
import sys
import math
from typing import Optional, Dict, List, Tuple

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action, Direction
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.agents.evaluator import TankEvaluator


class TankGameGUI:
    """
    High-Fidelity Graphical User Interface for the Tank Battle Game.
    """

    def __init__(self, cell_size: int = 46, fps: int = 15):
        self.cell_size = cell_size
        self.base_fps = fps
        self.fps = fps
        self.speed_multiplier = 1  # 1x, 2x, 4x

        # Playback control flags
        self.is_paused: bool = False
        self.step_requested: bool = False
        self.undo_requested: bool = False
        self.restart_requested: bool = False
        self.map_requested: bool = False
        self.current_map_title: str = "01_classic_battlecity"

        self.screen = None
        self.clock = None
        self.sidebar_width = 380
        self.sprites: Dict[str, any] = {}

        # Interactive UI buttons: list of dicts with rect, label, id, active
        self.buttons: List[Dict[str, any]] = []

        # Visual FX state
        self.tracks: List[Dict[str, any]] = []        # [{x, y, dir, alpha}]
        self.explosions: List[Dict[str, any]] = []    # [{x, y, frame}]
        self.muzzle_flashes: List[Dict[str, any]] = []# [{x, y, dir, frame}]
        self.anim_tick: int = 0

        # Last known agent decisions for display
        self.last_action: Dict[int, str] = {0: "INIT", 1: "INIT"}
        self.eval_score: float = 0.0
        self.evaluator = TankEvaluator()

        # Color Palette - Modern Cyber / Tactical
        self.COLOR_BG = (18, 22, 30)
        self.COLOR_GRID = (34, 42, 56)
        self.COLOR_GRID_TEXT = (110, 125, 145)
        self.COLOR_SIDEBAR_BG = (22, 27, 37)
        self.COLOR_CARD_BG = (28, 35, 48)
        self.COLOR_CARD_BORDER = (46, 58, 80)
        self.COLOR_TEXT = (240, 244, 252)
        self.COLOR_TEXT_DIM = (145, 155, 175)
        self.COLOR_GOLD = (245, 185, 25)
        self.COLOR_AMBER = (230, 126, 34)

        # Player Color Themes
        self.COLOR_P0_PRIMARY = (52, 152, 219)     # Electric Blue
        self.COLOR_P0_BG = (24, 42, 66)
        self.COLOR_P0_BORDER = (41, 128, 185)

        self.COLOR_P1_PRIMARY = (231, 76, 60)      # Crimson Red
        self.COLOR_P1_BG = (60, 28, 32)
        self.COLOR_P1_BORDER = (192, 57, 43)

        # Entity colors (fallback)
        self.COLOR_WALL = (165, 85, 54)
        self.COLOR_WALL_CRACK = (120, 60, 40)
        self.COLOR_BULLET = (241, 196, 15)
        self.COLOR_HP_GREEN = (46, 204, 113)
        self.COLOR_HP_YELLOW = (241, 196, 15)
        self.COLOR_HP_RED = (231, 76, 60)
        self.COLOR_FOLIAGE = (34, 139, 34)

    def init_display(self, width_cells: int, height_cells: int) -> bool:
        """
        Initializes Pygame window, custom fonts, buttons, and visual assets.
        """
        if not PYGAME_AVAILABLE:
            print("[TankGameGUI] Notice: Pygame is not installed. Running in headless mode.")
            return False

        try:
            pygame.init()
            pygame.font.init()

            self.board_w = width_cells * self.cell_size
            self.board_h = height_cells * self.cell_size
            self.width_px = self.board_w + self.sidebar_width
            self.height_px = max(self.board_h, 680)

            self.screen = pygame.display.set_mode((self.width_px, self.height_px))
            pygame.display.set_caption("AI Tank Battle - Adversarial Search Esports Deck (TDTU)")
            self.clock = pygame.time.Clock()

            # Cross-platform fonts with seamless fallbacks for macOS, Windows, and Linux
            self.font_title = pygame.font.SysFont("Trebuchet MS,Helvetica,Arial", 20, bold=True)
            self.font_large = pygame.font.SysFont("Helvetica,Arial,DejaVu Sans", 15, bold=True)
            self.font = pygame.font.SysFont("Helvetica,Arial,DejaVu Sans", 13)
            self.font_badge = pygame.font.SysFont("Helvetica,Arial,DejaVu Sans", 11, bold=True)
            self.font_small = pygame.font.SysFont("Helvetica,Arial,DejaVu Sans", 10)
            self.font_coord = pygame.font.SysFont("Helvetica,Arial,DejaVu Sans", 9, bold=True)

            # Load custom sprites
            self._load_sprites()

            # Build interactive control deck buttons
            self._init_buttons()
            return True
        except Exception as e:
            print(f"[TankGameGUI] Display initialization error: {e}. Falling back to console.")
            return False

    def _load_sprites(self) -> None:
        """
        Loads PNG sprites from Kenney assets with high-contrast scaling.
        """
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

        # 2. Tanks & Tracks
        self.sprites["tank_0"] = load_scaled("tank_blue.png", cs - 6, cs - 6)
        self.sprites["tank_1"] = load_scaled("tank_red.png", cs - 6, cs - 6)
        self.sprites["track"] = load_scaled("tracksSmall.png", cs // 2, cs // 2)

        # 3. Bullets & Muzzle Flash
        self.sprites["bullet_0"] = load_scaled("bulletBlue1_outline.png", 16, 20)
        self.sprites["bullet_1"] = load_scaled("bulletRed1_outline.png", 16, 20)
        self.sprites["shot_flash"] = load_scaled("shotOrange.png", 16, 24)

        # 4. Walls by HP level (Metal = 3, Wood = 2, Sandbag = 1)
        self.sprites["wall_3"] = load_scaled("crateMetal.png", cs - 4, cs - 4)
        self.sprites["wall_2"] = load_scaled("crateWood.png", cs - 4, cs - 4)
        self.sprites["wall_1"] = load_scaled("sandbagBrown.png", cs - 4, cs - 4)

        # 5. Bases
        self.sprites["base_0"] = load_scaled("barrelBlack_top.png", cs - 6, cs - 6)
        self.sprites["base_1"] = load_scaled("barrelRed_top.png", cs - 6, cs - 6)

        # 6. Smoke / Explosion Animation Frames
        self.sprites["smoke_1"] = load_scaled("explosionSmoke1.png", cs, cs)
        self.sprites["smoke_2"] = load_scaled("explosionSmoke2.png", cs, cs)
        self.sprites["smoke_3"] = load_scaled("explosionSmoke3.png", cs, cs)

    def _init_buttons(self) -> None:
        """
        Creates clickable buttons inside the sidebar control panel.
        """
        sidebar_x = self.board_w
        pad_x = sidebar_x + 16
        card_w = self.sidebar_width - 32
        btn_y = 100

        # Row 1: Action Controls (Play/Pause, Step, Undo, Reset, Map Switcher)
        w_btn = (card_w - 20) // 5
        self.buttons = [
            {"id": "play_pause", "label": "Play/Pause", "rect": pygame.Rect(pad_x, btn_y, w_btn, 26), "tooltip": "SPACE"},
            {"id": "step",       "label": "Step +1",    "rect": pygame.Rect(pad_x + w_btn + 5, btn_y, w_btn, 26), "tooltip": "S / ENTER"},
            {"id": "undo",       "label": "Undo -1",    "rect": pygame.Rect(pad_x + 2 * (w_btn + 5), btn_y, w_btn, 26), "tooltip": "U / Z"},
            {"id": "restart",    "label": "Reset",      "rect": pygame.Rect(pad_x + 3 * (w_btn + 5), btn_y, w_btn, 26), "tooltip": "R"},
            {"id": "next_map",   "label": "Map ⟳",      "rect": pygame.Rect(pad_x + 4 * (w_btn + 5), btn_y, w_btn, 26), "tooltip": "M (Next Map)"},
        ]

        # Row 2: Speed Toggle (0.5x, 1.0x, 2.0x)
        s_y = btn_y + 32
        sw_btn = (card_w - 12) // 3
        self.speed_buttons = [
            {"id": "speed_05", "label": "0.5x Slow",   "rect": pygame.Rect(pad_x, s_y, sw_btn, 22), "val": 0.5},
            {"id": "speed_1",  "label": "1.0x Normal", "rect": pygame.Rect(pad_x + sw_btn + 6, s_y, sw_btn, 22), "val": 1.0},
            {"id": "speed_2",  "label": "2.0x Fast",   "rect": pygame.Rect(pad_x + 2 * (sw_btn + 6), s_y, sw_btn, 22), "val": 2.0},
        ]

    def set_speed(self, multiplier: float) -> None:
        """Sets game execution speed multiplier (0.5x, 1.0x, 2.0x)."""
        self.speed_multiplier = float(multiplier)
        self.fps = max(1, int(self.base_fps * self.speed_multiplier))

    def add_hit_effect(self, x: int, y: int) -> None:
        """Triggers an animated explosion effect at cell (x, y)."""
        self.explosions.append({"x": x, "y": y, "frame": 0, "max_frames": 6})

    def add_muzzle_flash(self, x: int, y: int, direction: Direction) -> None:
        """Triggers a muzzle flash effect when tank fires."""
        self.muzzle_flashes.append({"x": x, "y": y, "dir": direction, "frame": 0, "max_frames": 3})

    def add_tank_track(self, x: int, y: int, direction: Direction) -> None:
        """Leaves fading track treads at the cell where a tank moved."""
        self.tracks.append({"x": x, "y": y, "dir": direction, "life": 120})
        if len(self.tracks) > 50:
            self.tracks.pop(0)

    def handle_events(self) -> bool:
        """
        Processes mouse clicks, keyboard controls, and window events.
        Returns False to quit, True to continue.
        """
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
                    self.is_paused = not self.is_paused
                elif event.key in (pygame.K_s, pygame.K_RETURN, pygame.K_RIGHT):
                    self.step_requested = True
                    self.is_paused = True
                elif event.key in (pygame.K_u, pygame.K_z, pygame.K_BACKSPACE, pygame.K_LEFT):
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

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
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

                for sbtn in self.speed_buttons:
                    if sbtn["rect"].collidepoint(mx, my):
                        self.set_speed(sbtn["val"])

        return True

    def render(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """
        Main draw routine rendering terrain, entities, FX particles, and sidebar HUD.
        """
        if not PYGAME_AVAILABLE or self.screen is None:
            return

        self.anim_tick += 1

        # Calculate live evaluation score
        self.eval_score = self.evaluator.evaluate(state, player_id=0)

        # 1. Render Battlefield Ground & Grid
        self._render_battlefield(state)

        # 2. Render Entities (Walls, Bases, Tanks, Bullets, Foliage Canopy)
        self._render_entities(state)

        # 3. Render Visual FX (Treads, Muzzle Flashes, Hit Explosions)
        self._render_particles()

        # 4. Render Game-Over Modal Overlay if Terminal
        if state.is_terminal():
            self._render_game_over_banner(state, agent0, agent1)

        # 5. Render Esports Tactical Sidebar HUD
        self._render_hud(state, agent0, agent1)

        pygame.display.flip()
        self.clock.tick(self.fps)

    def _render_battlefield(self, state: GameState) -> None:
        """
        Draws textured sand terrain tiles with subtle grid coordinates.
        """
        cs = self.cell_size
        sand_img = self.sprites.get("tile_sand")
        sand_img2 = self.sprites.get("tile_sand2")

        for x in range(state.width):
            for y in range(state.height):
                px = x * cs
                py = y * cs
                if sand_img:
                    # Checkerboard subtle variation for vibrant ground
                    img = sand_img2 if ((x + y) % 5 == 0 and sand_img2) else sand_img
                    self.screen.blit(img, (px, py))
                else:
                    color = (218, 192, 145) if (x + y) % 2 == 0 else (210, 182, 135)
                    pygame.draw.rect(self.screen, color, (px, py, cs, cs))

                # Subtle tactical grid lines
                pygame.draw.rect(self.screen, (0, 0, 0, 30), (px, py, cs, cs), 1)

                # Grid coordinate markers (along top edge row 0 and left edge col 0)
                if y == 0:
                    lbl = self.font_coord.render(str(x), True, (130, 110, 80))
                    self.screen.blit(lbl, (px + 3, 2))
                if x == 0:
                    lbl = self.font_coord.render(str(y), True, (130, 110, 80))
                    self.screen.blit(lbl, (3, py + 3))

    def _render_entities(self, state: GameState) -> None:
        """
        Renders walls, bases, tanks, bullets, and foreground foliage.
        """
        cs = self.cell_size

        # Kenney tank sprites (tank_blue.png, tank_red.png) have their barrel pointing DOWN at y=44.
        # Pygame rotates counter-clockwise.
        # To face UP: rotate 180 deg.
        # To face DOWN: rotate 0 deg.
        # To face RIGHT: rotate 90 deg.
        # To face LEFT: rotate 270 deg.
        tank_angle_map = {
            Direction.UP: 180,
            Direction.DOWN: 0,
            Direction.LEFT: 270,
            Direction.RIGHT: 90,
        }

        # Bullet sprites have their tip at top (y=0) pointing UP.
        bullet_angle_map = {
            Direction.UP: 0,
            Direction.DOWN: 180,
            Direction.LEFT: 90,
            Direction.RIGHT: 270,
        }

        # 1. Base Command Outposts (Distinct colors: P0 Electric Blue vs P1 Crimson Red)
        for pid, base in state.bases.items():
            if base.is_alive:
                bx = base.x * cs
                by = base.y * cs
                center_x = bx + cs // 2
                center_y = by + cs // 2

                # Animated radar beacon pulse
                pulse_r = int((self.anim_tick % 24) / 24 * (cs // 2 + 2))
                ring_c = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY
                radar_surf = pygame.Surface((cs + 8, cs + 8), pygame.SRCALPHA)
                pygame.draw.circle(radar_surf, (*ring_c, 50), (cs // 2 + 4, cs // 2 + 4), cs // 2 - 2)
                if pulse_r > 4:
                    pygame.draw.circle(radar_surf, (*ring_c, 90), (cs // 2 + 4, cs // 2 + 4), pulse_r, 2)
                self.screen.blit(radar_surf, (bx - 4, by - 4))

                # Distinct Fortress Styling for each Base Outpost
                base_color = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY
                inner_color = (20, 60, 110) if pid == 0 else (120, 25, 25)
                core_color = (80, 190, 255) if pid == 0 else (255, 100, 80)

                # Metallic base platform
                pygame.draw.rect(self.screen, (32, 40, 54), (bx + 2, by + 2, cs - 4, cs - 4), border_radius=8)
                pygame.draw.rect(self.screen, base_color, (bx + 2, by + 2, cs - 4, cs - 4), 2, border_radius=8)

                # Glowing circular inner shield
                pygame.draw.circle(self.screen, inner_color, (center_x, center_y), cs // 2 - 5)
                pygame.draw.circle(self.screen, core_color, (center_x, center_y), cs // 2 - 9)

                # Bold White Text Badge on Base (HQ 0 vs HQ 1)
                hq_badge = self.font_badge.render(f"HQ {pid}", True, (255, 255, 255))
                self.screen.blit(hq_badge, (center_x - hq_badge.get_width() // 2, center_y - hq_badge.get_height() // 2))

                # Segmented 9-cell health bar in the base's OWN team color (Blue for P0, Red for P1)
                self._draw_segmented_hp_bar(bx + 4, by - 2, base.hp, 9, seg_w=3, seg_h=4, color=base_color)

        # 2. Destructible Walls
        for (wx, wy), wall in state.walls.items():
            if wall.is_alive:
                rx = wx * cs + 2
                ry = wy * cs + 2
                sprite_key = f"wall_{wall.hp}"

                if sprite_key in self.sprites and self.sprites[sprite_key]:
                    self.screen.blit(self.sprites[sprite_key], (rx, ry))
                else:
                    w_color = (self.COLOR_WALL if wall.hp == 3 else
                               ((145, 75, 45) if wall.hp == 2 else self.COLOR_WALL_CRACK))
                    pygame.draw.rect(self.screen, w_color, (rx, ry, cs - 4, cs - 4), border_radius=4)

                # Numeric HP pill on wall
                badge = self.font_small.render(str(wall.hp), True, (255, 255, 255))
                self.screen.blit(badge, (rx + cs - 14, ry + cs - 16))

        # 3. Tanks with Corrected Heading Rotation and Status Rings
        for pid, tank in state.tanks.items():
            if tank.is_alive:
                tx = tank.x * cs
                ty = tank.y * cs
                center_x = tx + cs // 2
                center_y = ty + cs // 2
                t_color = self.COLOR_P0_PRIMARY if pid == 0 else self.COLOR_P1_PRIMARY

                # Glowing tactical base ring
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
                    dx, dy = tank.direction.value
                    pygame.draw.line(self.screen, (255, 255, 255), (center_x, center_y),
                                     (center_x + dx * (cs // 2 - 2), center_y + dy * (cs // 2 - 2)), 4)

                # Segmented 6-cell battery HP bar above tank
                self._draw_segmented_hp_bar(tx + 4, ty - 2, tank.hp, 6, seg_w=5, seg_h=4, color=t_color)

        # 4. Foliage / Bush Canopy (Rendered with slight transparency so tanks inside are visible)
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

        # 5. Bullets with High-Speed Motion Trails
        for bullet in state.bullets:
            if bullet.is_active:
                bx = bullet.x * cs + cs // 2
                by = bullet.y * cs + cs // 2
                dx, dy = bullet.direction.value

                # Bullet speed tail trail (3 cells backward)
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
        """
        Draws animated smoke puffs, muzzle flashes, and tracks.
        """
        cs = self.cell_size

        bullet_angle_map = {
            Direction.UP: 0,
            Direction.DOWN: 180,
            Direction.LEFT: 90,
            Direction.RIGHT: 270,
        }

        # Muzzle flashes positioned at the tip of the gun barrel
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

        # Hit smoke explosions
        active_exp = []
        for exp in self.explosions:
            exp["frame"] += 1
            frame_idx = exp["frame"]
            if frame_idx <= exp["max_frames"]:
                px = exp["x"] * cs
                py = exp["y"] * cs
                smoke_key = f"smoke_{(frame_idx % 3) + 1}"
                if smoke_key in self.sprites and self.sprites[smoke_key]:
                    self.screen.blit(self.sprites[smoke_key], (px, py))
                else:
                    r = int((frame_idx / exp["max_frames"]) * (cs // 2))
                    pygame.draw.circle(self.screen, (255, 120, 30), (px + cs // 2, py + cs // 2), r)
                active_exp.append(exp)
        self.explosions = active_exp

    def _draw_segmented_hp_bar(self, x: int, y: int, hp: int, max_hp: int,
                               seg_w: int, seg_h: int, color) -> None:
        """
        Draws clean, discrete battery-style health bar pips.
        """
        gap = 1
        total_w = max_hp * (seg_w + gap) + 2
        pygame.draw.rect(self.screen, (20, 24, 32), (x - 1, y - 1, total_w, seg_h + 2), border_radius=2)

        for i in range(max_hp):
            sx = x + i * (seg_w + gap)
            if i < hp:
                # Color transitions to yellow / red when low
                ratio = hp / max_hp
                pip_c = color if ratio > 0.5 else (self.COLOR_HP_YELLOW if ratio > 0.25 else self.COLOR_HP_RED)
                pygame.draw.rect(self.screen, pip_c, (sx, y, seg_w, seg_h), border_radius=1)
            else:
                pygame.draw.rect(self.screen, (40, 48, 60), (sx, y, seg_w, seg_h), border_radius=1)

    def _render_hud(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """
        Renders the entire sidebar command dashboard with live telemetry and buttons.
        """
        sidebar_x = self.board_w
        sidebar_rect = (sidebar_x, 0, self.sidebar_width, self.height_px)
        pygame.draw.rect(self.screen, self.COLOR_SIDEBAR_BG, sidebar_rect)
        pygame.draw.line(self.screen, self.COLOR_CARD_BORDER, (sidebar_x, 0), (sidebar_x, self.height_px), 2)

        pad_x = sidebar_x + 16
        card_w = self.sidebar_width - 32
        curr_y = 12

        # 1. Header Banner
        title_surf = self.font_title.render("BATTLE CITY AI", True, self.COLOR_GOLD)
        self.screen.blit(title_surf, (pad_x, curr_y))

        # Active Map Pill Badge
        clean_map = self.current_map_title.replace(".txt", "")
        if len(clean_map) > 16:
            clean_map = clean_map[:15] + ".."
        map_surf = self.font_badge.render(clean_map.upper(), True, self.COLOR_GOLD)
        mb_w = map_surf.get_width() + 10
        mb_rect = (pad_x + card_w - mb_w, curr_y + 1, mb_w, 20)
        pygame.draw.rect(self.screen, (34, 42, 58), mb_rect, border_radius=4)
        pygame.draw.rect(self.screen, self.COLOR_GOLD, mb_rect, 1, border_radius=4)
        self.screen.blit(map_surf, (mb_rect[0] + 5, mb_rect[1] + 3))

        curr_y += 22

        deck_sub = self.font_small.render("Tactical Adversarial Search Command Deck", True, self.COLOR_TEXT_DIM)
        self.screen.blit(deck_sub, (pad_x, curr_y))
        curr_y += 18

        # 2. Cycle Progress Bar
        cycle_pct = min(1.0, state.game_cycle / max(1, state.max_cycles))
        bar_rect = (pad_x, curr_y, card_w, 6)
        pygame.draw.rect(self.screen, (36, 44, 60), bar_rect, border_radius=3)
        if cycle_pct > 0:
            pygame.draw.rect(self.screen, self.COLOR_GOLD, (pad_x, curr_y, int(card_w * cycle_pct), 6), border_radius=3)
        curr_y += 9

        cycle_txt = self.font_badge.render(f"CYCLE {state.game_cycle} / {state.max_cycles}", True, self.COLOR_TEXT)
        self.screen.blit(cycle_txt, (pad_x, curr_y))

        # Status Pill
        if state.is_terminal():
            status_text = "MATCH FINISHED"
            status_c = (180, 40, 40)
        elif self.is_paused:
            status_text = "PAUSED [SPACE]"
            status_c = self.COLOR_AMBER
        else:
            turn_name = "P0 (MAX)" if state.current_player == 0 else "P1 (MIN)"
            status_text = f"LIVE: {turn_name}"
            status_c = (35, 125, 75)

        pill_surf = self.font_badge.render(status_text, True, (255, 255, 255))
        pill_w = pill_surf.get_width() + 12
        pill_rect = (pad_x + card_w - pill_w, curr_y - 2, pill_w, 18)
        pygame.draw.rect(self.screen, status_c, pill_rect, border_radius=4)
        self.screen.blit(pill_surf, (pill_rect[0] + 6, pill_rect[1] + 2))
        curr_y += 26

        # 3. Interactive Buttons (Play/Pause, Step, Undo, Reset)
        curr_y = self._render_control_buttons(pad_x, curr_y, card_w)

        # 4. Live Heuristic Advantage Score Gauge
        curr_y = self._render_eval_gauge(pad_x, curr_y, card_w)

        # 5. Player 0 Card (Blue MAX)
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
        curr_y += 8

        # 6. Player 1 Card (Red MIN)
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
        curr_y += 8

        # 7. Combat Specs & Entity HP Legend
        curr_y = self._render_specs_legend(pad_x, curr_y, card_w)

        # 8. Quick Shortcuts Chip Footer
        self._render_shortcuts_footer(pad_x, curr_y, card_w)

    def _render_control_buttons(self, x: int, y: int, width: int) -> int:
        """
        Renders clickable interactive control buttons and speed toggles.
        """
        mx, my = pygame.mouse.get_pos()

        # Update button label for play/pause
        for btn in self.buttons:
            if btn["id"] == "play_pause":
                btn["label"] = "▶ Resume" if self.is_paused else "⏸ Pause"
                break

        # Draw Row 1: Action buttons
        for btn in self.buttons:
            r = btn["rect"]
            r.top = y
            is_hover = r.collidepoint(mx, my)
            btn_bg = (45, 55, 75) if is_hover else (32, 40, 56)
            pygame.draw.rect(self.screen, btn_bg, r, border_radius=4)
            pygame.draw.rect(self.screen, self.COLOR_GOLD if is_hover else self.COLOR_CARD_BORDER, r, 1, border_radius=4)

            lbl = self.font_small.render(btn["label"], True, (255, 255, 255) if is_hover else self.COLOR_TEXT)
            self.screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        y += 30

        # Draw Row 2: Speed buttons
        for sbtn in self.speed_buttons:
            r = sbtn["rect"]
            r.top = y
            is_active = (self.speed_multiplier == sbtn["val"])
            is_hover = r.collidepoint(mx, my)

            s_bg = (50, 100, 60) if is_active else ((45, 55, 72) if is_hover else (28, 35, 48))
            pygame.draw.rect(self.screen, s_bg, r, border_radius=4)
            border_c = (76, 175, 80) if is_active else (self.COLOR_GOLD if is_hover else self.COLOR_CARD_BORDER)
            pygame.draw.rect(self.screen, border_c, r, 1, border_radius=4)

            lbl = self.font_small.render(sbtn["label"], True, (255, 255, 255) if is_active else self.COLOR_TEXT_DIM)
            self.screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        return y + 28

    def _render_eval_gauge(self, x: int, y: int, width: int) -> int:
        """
        Renders a dynamic visual heuristic advantage score meter.
        """
        h = 24
        gauge_rect = (x, y, width, h)
        pygame.draw.rect(self.screen, (26, 32, 45), gauge_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, gauge_rect, 1, border_radius=5)

        # Center line (neutral 0.0)
        center_x = x + width // 2
        pygame.draw.line(self.screen, (70, 80, 100), (center_x, y + 2), (center_x, y + h - 2), 1)

        # Fill bar towards blue (MAX advantage) or red (MIN advantage)
        # Clamped to range [-100, +100] for visual display
        clamped_score = max(-100.0, min(100.0, self.eval_score))
        half_w = (width // 2) - 4
        bar_len = int(abs(clamped_score) / 100.0 * half_w)

        if clamped_score > 0:
            fill_rect = (center_x, y + 4, bar_len, h - 8)
            pygame.draw.rect(self.screen, self.COLOR_P0_PRIMARY, fill_rect, border_radius=2)
        elif clamped_score < 0:
            fill_rect = (center_x - bar_len, y + 4, bar_len, h - 8)
            pygame.draw.rect(self.screen, self.COLOR_P1_PRIMARY, fill_rect, border_radius=2)

        # Text label
        sign = "+" if self.eval_score > 0 else ""
        eval_txt = f"EVAL: {sign}{self.eval_score:.1f}"
        score_surf = self.font_badge.render(eval_txt, True, (255, 255, 255))
        self.screen.blit(score_surf, (x + 8, y + 5))

        adv_txt = "MAX LEAD" if self.eval_score > 5 else ("MIN LEAD" if self.eval_score < -5 else "EVEN")
        adv_surf = self.font_small.render(adv_txt, True, self.COLOR_TEXT_DIM)
        self.screen.blit(adv_surf, (x + width - adv_surf.get_width() - 8, y + 6))

        return y + h + 8

    def _draw_player_card(
        self, x: int, y: int, width: int, pid: int,
        agent: BaseAgent, tank, base, is_active_turn: bool,
        primary_color, bg_color, border_color
    ) -> int:
        """
        Renders an esports telemetry card displaying live search statistics
        and annotated entity health bars.
        """
        card_h = 144
        card_rect = (x, y, width, card_h)

        pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=6)
        border_c = primary_color if is_active_turn else border_color
        thickness = 2 if is_active_turn else 1
        pygame.draw.rect(self.screen, border_c, card_rect, thickness, border_radius=6)

        cy = y + 6
        # Top Row: Player Role + Live Turn Indicator
        role_str = "PLAYER 0  [MAX]" if pid == 0 else "PLAYER 1  [MIN]"
        role_surf = self.font_large.render(role_str, True, primary_color)
        self.screen.blit(role_surf, (x + 10, cy))

        if is_active_turn:
            turn_pill = self.font_badge.render("DECIDING...", True, (255, 255, 255))
            tb_w = turn_pill.get_width() + 10
            tb_rect = (x + width - tb_w - 8, cy, tb_w, 18)
            pygame.draw.rect(self.screen, primary_color, tb_rect, border_radius=4)
            self.screen.blit(turn_pill, (tb_rect[0] + 5, tb_rect[1] + 2))
        cy += 18

        # Algorithm Name badge
        a_name = agent.name if agent else "Unknown Agent"
        if len(a_name) > 30:
            a_name = a_name[:28] + ".."
        name_surf = self.font_badge.render(a_name, True, self.COLOR_TEXT)
        self.screen.blit(name_surf, (x + 10, cy))
        cy += 16

        # Health & Position with explicit annotations
        t_hp = tank.hp if (tank and tank.is_alive) else 0
        b_hp = base.hp if (base and base.is_alive) else 0

        # Tank HP line with "(1 dmg/hit)" annotation
        t_str = f"Tank: {t_hp}/6 HP (1 dmg/hit)"
        t_lbl = self.font_small.render(t_str, True, self.COLOR_TEXT)
        self.screen.blit(t_lbl, (x + 10, cy))
        self._draw_segmented_hp_pips(x + 165, cy + 2, t_hp, 6, 8, primary_color)

        if tank and tank.is_alive:
            coord_str = f"({tank.x},{tank.y}) {tank.direction.name}"
            coord_surf = self.font_small.render(coord_str, True, self.COLOR_TEXT_DIM)
            self.screen.blit(coord_surf, (x + 235, cy))
        else:
            dead_surf = self.font_small.render("DESTROYED", True, self.COLOR_HP_RED)
            self.screen.blit(dead_surf, (x + 235, cy))
        cy += 16

        # Base HP line with "(1 dmg/hit)" and team-specific color pips
        b_str = f"Base: {b_hp}/9 HP (1 dmg/hit)"
        b_lbl = self.font_small.render(b_str, True, self.COLOR_TEXT)
        self.screen.blit(b_lbl, (x + 10, cy))
        self._draw_segmented_hp_pips(x + 165, cy + 2, b_hp, 9, 5, primary_color)
        cy += 18

        # Divider
        pygame.draw.line(self.screen, border_color, (x + 10, cy), (x + width - 10, cy), 1)
        cy += 4

        # HIGH-TECH AI SEARCH TELEMETRY SUB-PANEL
        stats = agent.stats if agent else None
        d_val = stats.search_depth if stats else 0
        prunes = stats.prune_count if stats else 0
        nodes = stats.explored_nodes if stats else 0
        t_ms = (stats.execution_time * 1000) if stats else 0.0

        # Calculate pruning percentage
        total_branches = nodes + prunes
        prune_pct = int(prunes / total_branches * 100) if total_branches > 0 else 0

        # Telemetry container box
        tele_box_h = 42
        tele_rect = (x + 8, cy, width - 16, tele_box_h)
        pygame.draw.rect(self.screen, (14, 18, 27), tele_rect, border_radius=4)
        pygame.draw.rect(self.screen, (40, 52, 72), tele_rect, 1, border_radius=4)

        # Line 1: Depth | Nodes | Pruned %
        t_y = cy + 4
        lbl_d = self.font_small.render(f"depth={d_val}", True, (52, 219, 219))
        lbl_n = self.font_small.render(f"nodes={nodes:,}", True, self.COLOR_GOLD)

        is_ab_agent = ("alpha" in a_name.lower() or "ab" in a_name.lower() or prunes > 0)
        if is_ab_agent:
            prune_str = f"pruned={prune_pct}% ({prunes:,} cuts)"
            lbl_p = self.font_small.render(prune_str, True, (46, 204, 113))
        else:
            lbl_p = self.font_small.render("pruned=0% (Minimax)", True, (140, 150, 165))

        self.screen.blit(lbl_d, (x + 14, t_y))
        self.screen.blit(lbl_n, (x + 85, t_y))
        self.screen.blit(lbl_p, (x + 185, t_y))

        # Line 2: Alpha-Beta cut efficiency bar + Time
        t_y += 18
        bar_w = 120
        bar_h = 7
        bar_x = x + 14
        pygame.draw.rect(self.screen, (32, 40, 54), (bar_x, t_y + 3, bar_w, bar_h), border_radius=2)
        if is_ab_agent and prune_pct > 0:
            prune_bar_w = int(bar_w * (prune_pct / 100.0))
            pygame.draw.rect(self.screen, (46, 204, 113), (bar_x, t_y + 3, prune_bar_w, bar_h), border_radius=2)
            eff_txt = f"α-β speedup: +{prune_pct}%"
            eff_surf = self.font_coord.render(eff_txt, True, (46, 204, 113))
        else:
            pygame.draw.rect(self.screen, self.COLOR_GOLD, (bar_x, t_y + 3, bar_w, bar_h), border_radius=2)
            eff_surf = self.font_coord.render("Standard Game Tree", True, self.COLOR_TEXT_DIM)

        self.screen.blit(eff_surf, (bar_x + bar_w + 8, t_y + 1))

        # Execution time in ms at right corner
        time_surf = self.font_coord.render(f"{t_ms:.1f}ms", True, (200, 215, 230))
        self.screen.blit(time_surf, (x + width - 16 - time_surf.get_width() - 4, t_y + 1))

        return y + card_h

    def _render_specs_legend(self, x: int, y: int, width: int) -> int:
        """
        Renders the combat specifications and entity HP legend
        from the course project specification (2627-HK1-AI-CK.pdf).
        """
        card_h = 72
        rect = (x, y, width, card_h)
        pygame.draw.rect(self.screen, (24, 30, 42), rect, border_radius=6)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, rect, 1, border_radius=6)

        # Title
        t_surf = self.font_badge.render("HEALTH & COMBAT SPECS (COURSE SPEC)", True, self.COLOR_GOLD)
        self.screen.blit(t_surf, (x + 10, y + 6))

        # Specs lines
        l1 = self.font_small.render("Tank: 6 HP (1 dmg/hit)   |   Base: 9 HP (1 dmg/hit)", True, self.COLOR_TEXT)
        self.screen.blit(l1, (x + 10, y + 22))

        l2 = self.font_small.render("Walls: 3 HP max (Metal = 3 | Wood = 2 | Sandbag = 1)", True, (215, 175, 130))
        self.screen.blit(l2, (x + 10, y + 38))

        l3 = self.font_small.render("Bullet: Speed = 3 cells/cycle  |  Stops on entity impact", True, self.COLOR_TEXT_DIM)
        self.screen.blit(l3, (x + 10, y + 54))

        return y + card_h + 6

    def _draw_segmented_hp_pips(self, x: int, y: int, hp: int, max_hp: int, seg_w: int, active_color) -> None:
        """Draws compact health pips."""
        seg_h = 6
        gap = 2
        for i in range(max_hp):
            sx = x + i * (seg_w + gap)
            color = active_color if i < hp else (40, 48, 60)
            pygame.draw.rect(self.screen, color, (sx, y, seg_w, seg_h), border_radius=1)

    def _render_shortcuts_footer(self, x: int, y: int, width: int) -> None:
        """
        Renders keyboard shortcuts quick guide.
        """
        card_h = 28
        rect = (x, y, width, card_h)
        pygame.draw.rect(self.screen, (20, 24, 34), rect, border_radius=5)
        pygame.draw.rect(self.screen, self.COLOR_CARD_BORDER, rect, 1, border_radius=5)

        s_txt = "[SPACE] Pause | [S] Step | [U] Undo | [R] Reset | [M] Map | [1-3] Spd"
        s_surf = self.font_small.render(s_txt, True, self.COLOR_TEXT_DIM)
        self.screen.blit(s_surf, (x + (width - s_surf.get_width()) // 2, y + 7))

    def _render_game_over_banner(self, state: GameState, agent0: BaseAgent, agent1: BaseAgent) -> None:
        """
        Draws high-impact victory / draw overlay ribbon on the battlefield.
        """
        winner = state.get_winner()
        b_w = self.board_w
        b_h = self.board_h

        # Translucent tint
        tint = pygame.Surface((b_w, b_h), pygame.SRCALPHA)
        tint.fill((10, 14, 22, 175))
        self.screen.blit(tint, (0, 0))

        # Modal Dialog Card
        card_w = 360
        card_h = 150
        cx = (b_w - card_w) // 2
        cy = (b_h - card_h) // 2

        pygame.draw.rect(self.screen, (24, 32, 46), (cx, cy, card_w, card_h), border_radius=10)
        border_c = (self.COLOR_P0_PRIMARY if winner == 0 else
                    (self.COLOR_P1_PRIMARY if winner == 1 else self.COLOR_GOLD))
        pygame.draw.rect(self.screen, border_c, (cx, cy, card_w, card_h), 2, border_radius=10)

        # Title & Winner Details
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

        # Action hint
        hint_surf = self.font_small.render("Press [U] to Undo last move   |   [R] to Restart match", True, self.COLOR_GOLD)
        self.screen.blit(hint_surf, (cx + (card_w - hint_surf.get_width()) // 2, cy + 86))

        esc_surf = self.font_small.render("Press [ESC] to Quit", True, self.COLOR_TEXT_DIM)
        self.screen.blit(esc_surf, (cx + (card_w - esc_surf.get_width()) // 2, cy + 112))
