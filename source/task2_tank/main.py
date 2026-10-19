"""
main.py - Entry Point for Task 2: Tank Battle Game
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Entry point for running Tank Battle in GUI or Benchmark mode.
    Supports configuring AI algorithms, loading rival group agents dynamically,
    and running headless performance evaluation.
"""

import argparse
import sys
import os

# Add source directory to sys.path so modules can be run directly
source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from task2_tank.engine.maps import MapBuilder
from task2_tank.engine.rules import GameRules
from task2_tank.agents.minimax_agent import MinimaxAgent
from task2_tank.agents.alphabeta_agent import AlphaBetaAgent
from task2_tank.agents.heuristic_minimax_agent import HeuristicMinimaxAgent
from task2_tank.agents.heuristic_alphabeta_agent import HeuristicAlphaBetaAgent
from task2_tank.engine.actions import Action
from task2_tank.ui.pygame_ui import TankGameGUI, PYGAME_AVAILABLE
from task2_tank.agent_loader import AgentLoader


def get_agent_by_name(name: str, depth: int = 3):
    """Instantiates built-in search agent by keyword."""
    name_lower = name.lower()
    if name_lower == "minimax":
        return MinimaxAgent(depth=depth)
    elif name_lower == "alphabeta":
        return AlphaBetaAgent(depth=depth)
    elif name_lower == "heuristic_minimax":
        return HeuristicMinimaxAgent(depth=depth)
    elif name_lower in ("heuristic_alphabeta", "hab"):
        return HeuristicAlphaBetaAgent(depth=depth)
    else:
        print(f"[Warning] Unknown agent '{name}', defaulting to Heuristic Alpha-Beta.")
        return HeuristicAlphaBetaAgent(depth=depth)


def run_gui_game(agent0, agent1, max_cycles: int = 50, map_name: str = "01"):
    """
    Executes a full interactive match using Pygame GUI.
    Supports real-time telemetry, Pause/Resume, Step-by-Step debugging,
    Undo-1 state rollback, Match Reset, dynamic map cycling, and Particle FX.
    """
    from task2_tank.engine.map_loader import MapLoader
    state, display_name = MapLoader.load_by_query(map_name)
    state.max_cycles = max_cycles
    current_map_name = display_name

    gui = TankGameGUI(cell_size=46, fps=15)
    gui.current_map_title = display_name
    gui_ready = gui.init_display(state.width, state.height)

    print(f"\n=== MATCH STARTED: {agent0.name} (P0) vs {agent1.name} (P1) | Map: {display_name.upper()} ===")
    print("Controls: SPACE = Pause/Resume | S/ENTER = Step | U/Z = Undo | R = Reset | M = Next Map | 1/2/3 = Speed (0.5x, 1x, 2x)")

    # State history stack for Undo functionality
    state_history = [state.clone()]

    running = True
    while running:
        running = gui.handle_events()
        if not running:
            break

        # Handle in-game map cycling (Key M or Map button)
        if gui.map_requested:
            gui.map_requested = False
            next_map = MapLoader.get_next_map_name(current_map_name)
            current_map_name = next_map
            state, display_name = MapLoader.load_by_query(current_map_name)
            state.max_cycles = max_cycles
            gui.current_map_title = display_name
            state_history = [state.clone()]
            gui.explosions.clear()
            gui.muzzle_flashes.clear()
            gui.tracks.clear()
            print(f"[Control] Cycled to Map: {display_name.upper()}")
            gui.render(state, agent0, agent1)
            continue

        # Handle match reset
        if gui.restart_requested:
            gui.restart_requested = False
            state, display_name = MapLoader.load_by_query(current_map_name)
            state.max_cycles = max_cycles
            gui.current_map_title = display_name
            state_history = [state.clone()]
            gui.explosions.clear()
            gui.muzzle_flashes.clear()
            gui.tracks.clear()
            print(f"[Control] Match reset to initial state on map {display_name.upper()}.")
            gui.render(state, agent0, agent1)
            continue

        # Handle undo step
        if gui.undo_requested:
            gui.undo_requested = False
            if len(state_history) > 1:
                state_history.pop()  # discard current state
                state = state_history[-1].clone()
                print(f"[Control] Undo step: Restored to Cycle {state.game_cycle}, P{state.current_player} turn.")
            else:
                print("[Control] Undo ignored: Already at initial state.")
            gui.render(state, agent0, agent1)
            continue

        # If terminal, keep rendering victory modal until user exits, resets, or undos
        if state.is_terminal():
            gui.render(state, agent0, agent1)
            continue

        # If paused and no step requested, simply render idle frame
        if gui.is_paused and not gui.step_requested:
            gui.render(state, agent0, agent1)
            continue

        gui.step_requested = False

        # Current player decides move
        current_pid = state.current_player
        agent = agent0 if current_pid == 0 else agent1

        # Muzzle flash and track visual FX triggers
        tank = state.tanks.get(current_pid)
        action = agent.choose_action(state, current_pid)

        if action == Action.FIRE and tank and tank.is_alive:
            gui.add_muzzle_flash(tank.x, tank.y, tank.direction)
        elif action in (Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT) and tank and tank.is_alive:
            gui.add_tank_track(tank.x, tank.y, tank.direction)

        print(f"[Cycle {state.game_cycle:2d}] P{current_pid} ({agent.name[:18]}) -> {action.value:<10} | Nodes: {agent.stats.explored_nodes:4d} | Time: {agent.stats.execution_time:.4f}s")

        # Advance state and detect damage/hits for explosion particles
        next_state = GameRules.apply_action(state, action)

        # Detect wall damage
        for pos, wall in state.walls.items():
            next_wall = next_state.walls.get(pos)
            if not next_wall or next_wall.hp < wall.hp:
                gui.add_hit_effect(pos[0], pos[1])

        # Detect tank damage
        for pid, t in state.tanks.items():
            next_t = next_state.tanks.get(pid)
            if (next_t and next_t.hp < t.hp) or (t.is_alive and (not next_t or not next_t.is_alive)):
                gui.add_hit_effect(t.x, t.y)

        # Detect base damage
        for pid, b in state.bases.items():
            next_b = next_state.bases.get(pid)
            if (next_b and next_b.hp < b.hp) or (b.is_alive and (not next_b or not next_b.is_alive)):
                gui.add_hit_effect(b.x, b.y)

        state = next_state
        state_history.append(state.clone())
        gui.render(state, agent0, agent1)

    if PYGAME_AVAILABLE:
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass

    winner = state.get_winner()
    w_str = f"Player {winner} ({agent0.name if winner == 0 else agent1.name}) WINS!" if winner in (0, 1) else "MATCH DRAW!"
    print(f"\n=== GAME OVER: {w_str} ===")


def main():
    parser = argparse.ArgumentParser(description="Task 2: Tank Battle Game - Adversarial Search")
    parser.add_argument("--mode", choices=["gui", "benchmark"], default="gui", help="Run mode (gui or benchmark)")
    parser.add_argument("--p0", default="heuristic_alphabeta", help="Player 0 algorithm")
    parser.add_argument("--p1", default="alphabeta", help="Player 1 algorithm")
    parser.add_argument("--depth", type=int, default=3, help="Search depth for built-in agents")
    parser.add_argument("--map", default="01", help="Map scenario name, index (01..04), or custom .txt file path")
    parser.add_argument("--load_external", type=str, default=None, help="Path to external rival group agent .py file")
    parser.add_argument("--max_cycles", type=int, default=40, help="Max game cycles before draw")

    args = parser.parse_args()

    if args.mode == "benchmark":
        from task2_tank.experiments.benchmark_tanks import TankTournament
        print("=== RUNNING AUTOMATED BENCHMARK SUITE ===")
        tournament = TankTournament(max_cycles_per_game=args.max_cycles)
        tournament.run_single_move_benchmark(depths=[1, 2, 3])
        tournament.run_tournament()
        tournament.plot_comparisons("benchmark_task2.png")
        print("\n" + tournament.export_tables())
    else:
        agent0 = get_agent_by_name(args.p0, depth=args.depth)

        # Handle external rival agent loading
        if args.load_external:
            print(f"[Main] Loading external agent from {args.load_external}...")
            agent1 = AgentLoader.load_agent_from_file(args.load_external)
            if agent1 is None:
                print("[Main] Fallback to default Player 1 agent.")
                agent1 = get_agent_by_name(args.p1, depth=args.depth)
        else:
            agent1 = get_agent_by_name(args.p1, depth=args.depth)

        run_gui_game(agent0, agent1, max_cycles=args.max_cycles, map_name=args.map)


if __name__ == "__main__":
    main()