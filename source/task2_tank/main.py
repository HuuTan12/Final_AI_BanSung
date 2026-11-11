"""
main.py - Entry Point for Task 2: Tank Battle Game
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Entry point for running Tank Battle in GUI or Benchmark mode.
    Supports configuring AI algorithms, Human player mode, dynamic algorithm
    switching during matches, loading rival group agents, and running
    realistic cell-by-cell turn-based bullet flight animations.
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
from task2_tank.agents.iterative_deepening_agent import IterativeDeepeningAgent
from task2_tank.agents.greedy_agent import GreedyTacticalAgent
from task2_tank.agents.human_agent import HumanAgent
from task2_tank.engine.actions import Action
from task2_tank.ui.pygame_ui import TankGameGUI, PYGAME_AVAILABLE
from task2_tank.agent_loader import AgentLoader


def get_agent_by_name(name: str, depth: int = 3):
    """Instantiates search agent, human controller, or proposed algorithm by keyword."""
    name_lower = name.lower()
    if name_lower in ("human", "player", "user"):
        return HumanAgent()
    elif name_lower in ("heuristic_alphabeta", "hab"):
        return HeuristicAlphaBetaAgent(depth=depth)
    elif name_lower in ("id_ab", "iterative_deepening", "id", "iterativedeepening"):
        return IterativeDeepeningAgent(max_depth=depth)
    elif name_lower in ("alphabeta", "ab"):
        return AlphaBetaAgent(depth=depth)
    elif name_lower in ("heuristic_minimax", "hm"):
        return HeuristicMinimaxAgent(depth=depth)
    elif name_lower == "minimax":
        return MinimaxAgent(depth=depth)
    elif name_lower in ("greedy", "reflex"):
        return GreedyTacticalAgent()
    elif name_lower in ("rival", "external"):
        try:
            from task2_tank.agents.external.sample_rival_agent import RivalGroupAgent
            return RivalGroupAgent()
        except Exception:
            return HeuristicAlphaBetaAgent(depth=depth)
    else:
        print(f"[Warning] Unknown agent '{name}', defaulting to Heuristic Alpha-Beta.")
        return HeuristicAlphaBetaAgent(depth=depth)


def run_gui_game(agent0, agent1, max_cycles: int = 50, map_name: str = "01"):
    """
    Executes a full interactive match using Pygame GUI.
    Supports real-time telemetry, Human player mode, dynamic algorithm switching,
    Pause/Resume, Step-by-Step debugging, Undo-1 state rollback, Match Reset,
    dynamic map cycling, and realistic cell-by-cell bullet flight animations.
    """
    from task2_tank.engine.map_loader import MapLoader
    state, display_name = MapLoader.load_by_query(map_name)
    state.max_cycles = max_cycles
    current_map_name = display_name

    gui = TankGameGUI(cell_size=46, fps=60)
    gui.current_map_title = display_name
    gui_ready = gui.init_display(state.width, state.height)
    if not gui_ready:
        print("[Error] Failed to initialize GUI display.")
        return

    gui.set_agent_presets_from_agents(agent0, agent1)

    print(f"\n=== MATCH READY: {agent0.name} (P0) vs {agent1.name} (P1) | Map: {display_name.upper()} ===")
    print("Click [START] button (or press SPACE/P) in the GUI window to begin the match!")
    print("Controls: P/SPACE = Start/Pause | S = Step +1 | U/Z = Undo -1 | R = Reset | M = Next Map | 1..4 = Speed")
    print("2-Human PvP Controls: P0 uses [WASD + F/SPACE fire, Q stay] | P1 uses [Arrows + / fire, . stay] | or click On-Screen D-Pad!")

    import time
    state_history = [state.clone()]
    last_ai_turn_time = 0.0

    running = True
    while running:
        current_pid = state.current_player
        active_agent = agent0 if current_pid == 0 else agent1
        active_is_human = getattr(active_agent, "is_human", False)
        p0_is_human = getattr(agent0, "is_human", False)
        p1_is_human = getattr(agent1, "is_human", False)

        running = gui.handle_events(
            active_player_is_human=active_is_human,
            current_pid=current_pid,
            p0_is_human=p0_is_human,
            p1_is_human=p1_is_human,
        )
        if not running:
            break

        # Check if user switched algorithms or depth on the HUD
        if gui.agent_changed:
            gui.agent_changed = False
            k0, d0 = gui.get_selected_agent_key(0)
            k1, d1 = gui.get_selected_agent_key(1)
            agent0 = get_agent_by_name(k0, depth=d0)
            agent1 = get_agent_by_name(k1, depth=d1)
            print(f"[HUD Switch] P0 updated to '{agent0.name}', P1 updated to '{agent1.name}'")

        # Handle in-game map cycling (Key M / N or Map button / badge)
        if gui.map_requested or getattr(gui, "map_prev_requested", False):
            is_prev = getattr(gui, "map_prev_requested", False)
            gui.map_requested = False
            gui.map_prev_requested = False
            next_map = (
                MapLoader.get_prev_map_name(current_map_name)
                if is_prev else MapLoader.get_next_map_name(current_map_name)
            )
            current_map_name = next_map
            state, display_name = MapLoader.load_by_query(current_map_name)
            state.max_cycles = max_cycles
            gui.current_map_title = display_name
            state_history = [state.clone()]
            gui.explosions.clear()
            gui.muzzle_flashes.clear()
            gui.tracks.clear()
            gui.reset_match_wait_state()
            gui.add_combat_log(f"[MAP] Switched to {display_name.upper()}. Click START to begin.", (245, 190, 35))
            print(f"[Control] Cycled to Map: {display_name.upper()} (Waiting for START)")
            gui.render(state, agent0, agent1)
            continue

        # Handle match reset (Key R or Reset button)
        if gui.restart_requested:
            gui.restart_requested = False
            state, display_name = MapLoader.load_by_query(current_map_name)
            state.max_cycles = max_cycles
            gui.current_map_title = display_name
            state_history = [state.clone()]
            gui.explosions.clear()
            gui.muzzle_flashes.clear()
            gui.tracks.clear()
            gui.reset_match_wait_state()
            gui.add_combat_log("[RESET] Match reset to initial positions. Click START to begin.", (245, 190, 35))
            print(f"[Control] Match reset to initial state on map {display_name.upper()} (Waiting for START).")
            gui.render(state, agent0, agent1)
            continue

        # Handle undo step (Key U or Undo button)
        if gui.undo_requested:
            gui.undo_requested = False
            if len(state_history) > 1:
                state_history.pop()
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

        # If paused (or waiting for START) and no step requested, render idle frame
        if gui.is_paused and not gui.step_requested:
            gui.render(state, agent0, agent1)
            continue

        # Handle Human Player Turn: Wait for human input from active player's queue
        if active_is_human:
            queued_act = gui.get_queued_human_action(current_pid)
            if queued_act is None:
                gui.render(state, agent0, agent1)
                continue
            else:
                action = queued_act
        else:
            # Slower, visually intuitive pacing between AI turns (without freezing GUI events)
            if not gui.step_requested:
                turn_delay = 0.35 / max(0.25, gui.speed_multiplier)
                if time.perf_counter() - last_ai_turn_time < turn_delay:
                    gui.render(state, agent0, agent1)
                    continue
            gui.step_requested = False
            action = active_agent.choose_action(state, current_pid)
            last_ai_turn_time = time.perf_counter()

        gui.step_requested = False

        print(f"[Cycle {state.game_cycle:2d}] P{current_pid} ({active_agent.name[:24]}) -> {action.value:<10} | Nodes: {active_agent.stats.explored_nodes:4d} | Time: {active_agent.stats.execution_time:.4f}s")

        if hasattr(gui, "add_combat_log"):
            p_tag = "P0 Blue" if current_pid == 0 else "P1 Red"
            log_col = (90, 185, 255) if current_pid == 0 else (255, 120, 120)
            gui.add_combat_log(f"[C{state.game_cycle:02d}] {p_tag} -> {action.value} ({active_agent.stats.explored_nodes} nodes, {active_agent.stats.execution_time*1000:.1f}ms)", log_col)

        next_state = gui.animate_turn(state, action, agent0, agent1)

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
    parser.add_argument("--p0", default="heuristic_alphabeta", help="Player 0 algorithm (human, heuristic_alphabeta, id_ab, alphabeta, heuristic_minimax, minimax, greedy, rival)")
    parser.add_argument("--p1", default="alphabeta", help="Player 1 algorithm (human, heuristic_alphabeta, id_ab, alphabeta, heuristic_minimax, minimax, greedy, rival)")
    parser.add_argument("--depth", type=int, default=3, help="Search depth for built-in agents")
    parser.add_argument("--map", default="01", help="Map scenario name, index (01..09), or custom .txt file path")
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
