import argparse
import sys
import os
source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)
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

def get_agent_by_name(name: str, depth: int=3):
    if name.startswith('ext::'):
        ext_path = name[5:]
        ext_agent = AgentLoader.load_agent_from_file(ext_path, depth=depth)
        if ext_agent is not None:
            return ext_agent
        print(f"[Warning] Failed to reload external bot '{ext_path}', falling back to Heuristic Alpha-Beta.")
        return HeuristicAlphaBetaAgent(depth=depth)
    name_lower = name.lower()
    if name_lower in ('human', 'player', 'user'):
        return HumanAgent()
    elif name_lower in ('heuristic_alphabeta', 'hab'):
        return HeuristicAlphaBetaAgent(depth=depth)
    elif name_lower in ('id_ab', 'iterative_deepening', 'id', 'iterativedeepening'):
        return IterativeDeepeningAgent(max_depth=depth)
    elif name_lower in ('alphabeta', 'ab'):
        return AlphaBetaAgent(depth=depth)
    elif name_lower in ('heuristic_minimax', 'hm'):
        return HeuristicMinimaxAgent(depth=depth)
    elif name_lower == 'minimax':
        return MinimaxAgent(depth=depth)
    elif name_lower in ('greedy', 'reflex'):
        return GreedyTacticalAgent()
    elif name_lower in ('rival', 'external'):
        sample_path = os.path.join(AgentLoader.DEFAULT_EXTERNAL_DIR, 'sample_rival_agent.py')
        ext_agent = AgentLoader.load_agent_from_file(sample_path, depth=depth)
        if ext_agent is not None:
            return ext_agent
        return HeuristicAlphaBetaAgent(depth=depth)
    else:
        print(f"[Warning] Unknown agent '{name}', defaulting to Heuristic Alpha-Beta.")
        return HeuristicAlphaBetaAgent(depth=depth)

def run_gui_game(agent0, agent1, max_cycles: int=50, map_name: str='01'):
    from task2_tank.engine.map_loader import MapLoader
    state, display_name = MapLoader.load_by_query(map_name)
    state.max_cycles = max_cycles
    current_map_name = display_name
    gui = TankGameGUI(cell_size=46, fps=60)
    gui.current_map_title = display_name
    gui_ready = gui.init_display(state.width, state.height)
    if not gui_ready:
        print('[Error] Failed to initialize GUI display.')
        return
    gui.set_agent_presets_from_agents(agent0, agent1)
    prev_k0, prev_d0 = gui.get_selected_agent_key(0)
    prev_k1, prev_d1 = gui.get_selected_agent_key(1)
    custom_agents = {}
    if prev_k0.startswith('custom::'):
        custom_agents[prev_k0] = agent0
    if prev_k1.startswith('custom::'):
        custom_agents[prev_k1] = agent1
    print(f'\n=== MATCH READY: {agent0.name} (P0) vs {agent1.name} (P1) | Map: {display_name.upper()} ===')
    print('Click [START] button (or press SPACE/P) in the GUI window to begin the match!')
    print('Controls: P/SPACE = Start/Pause | S = Step +1 | U/Z = Undo -1 | R = Reset | M = Next Map | 1..4 = Speed')
    print('2-Human PvP Controls: P0 uses [WASD + F/SPACE fire, Q stay] | P1 uses [Arrows + / fire, . stay] | or click On-Screen D-Pad!')
    import time
    import concurrent.futures
    state_history = [state.clone()]
    last_ai_turn_time = 0.0
    ai_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    ai_future = None
    ai_think_start_time = 0.0
    running = True
    while running:
        current_pid = state.current_player
        active_agent = agent0 if current_pid == 0 else agent1
        active_is_human = getattr(active_agent, 'is_human', False)
        p0_is_human = getattr(agent0, 'is_human', False)
        p1_is_human = getattr(agent1, 'is_human', False)
        gui.active_game_state = state
        running = gui.handle_events(active_player_is_human=active_is_human, current_pid=current_pid, p0_is_human=p0_is_human, p1_is_human=p1_is_human)
        if not running or getattr(gui, 'quit_requested', False):
            break
        if gui.agent_changed:
            gui.agent_changed = False
            ai_future = None
            gui.ai_thinking = False
            gui.ai_thinking_pid = None
            gui.human_queues = {0: None, 1: None}
            k0, d0 = gui.get_selected_agent_key(0)
            k1, d1 = gui.get_selected_agent_key(1)
            if (k0, d0) != (prev_k0, prev_d0):
                agent0 = custom_agents[k0] if k0 in custom_agents else get_agent_by_name(k0, depth=d0)
                prev_k0, prev_d0 = (k0, d0)
                gui.add_combat_log(f'[MODE] P0 Blue switched to {agent0.name}.', (90, 185, 255))
            if (k1, d1) != (prev_k1, prev_d1):
                agent1 = custom_agents[k1] if k1 in custom_agents else get_agent_by_name(k1, depth=d1)
                prev_k1, prev_d1 = (k1, d1)
                gui.add_combat_log(f'[MODE] P1 Red switched to {agent1.name}.', (255, 120, 120))
            print(f"[HUD Switch] P0 updated to '{agent0.name}', P1 updated to '{agent1.name}'")
        if gui.map_requested or getattr(gui, 'map_prev_requested', False):
            is_prev = getattr(gui, 'map_prev_requested', False)
            gui.map_requested = False
            gui.map_prev_requested = False
            ai_future = None
            gui.ai_thinking = False
            gui.ai_thinking_pid = None
            next_map = MapLoader.get_prev_map_name(current_map_name) if is_prev else MapLoader.get_next_map_name(current_map_name)
            current_map_name = next_map
            state, display_name = MapLoader.load_by_query(current_map_name)
            state.max_cycles = max_cycles
            gui.current_map_title = display_name
            state_history = [state.clone()]
            gui.explosions.clear()
            gui.muzzle_flashes.clear()
            gui.tracks.clear()
            gui.animated_bullets.clear()
            gui.animated_tank_override.clear()
            gui.reset_match_wait_state()
            gui.update_map_layout(state.width, state.height)
            gui.add_combat_log(f'[MAP] Switched to {display_name.upper()}. Click START to begin.', (245, 190, 35))
            print(f'[Control] Cycled to Map: {display_name.upper()} (Waiting for START)')
            gui.render(state, agent0, agent1)
            continue
        if gui.restart_requested:
            gui.restart_requested = False
            ai_future = None
            gui.ai_thinking = False
            gui.ai_thinking_pid = None
            state, display_name = MapLoader.load_by_query(current_map_name)
            state.max_cycles = max_cycles
            gui.current_map_title = display_name
            state_history = [state.clone()]
            gui.explosions.clear()
            gui.muzzle_flashes.clear()
            gui.tracks.clear()
            gui.animated_bullets.clear()
            gui.animated_tank_override.clear()
            gui.reset_match_wait_state()
            gui.update_map_layout(state.width, state.height)
            gui.add_combat_log('[RESET] Match reset to initial positions. Click START to begin.', (245, 190, 35))
            print(f'[Control] Match reset to initial state on map {display_name.upper()} (Waiting for START).')
            gui.render(state, agent0, agent1)
            continue
        if gui.undo_requested:
            gui.undo_requested = False
            gui.step_requested = False
            gui.is_paused = True
            ai_future = None
            gui.ai_thinking = False
            gui.ai_thinking_pid = None
            gui.explosions.clear()
            gui.muzzle_flashes.clear()
            gui.animated_bullets.clear()
            gui.animated_tank_override.clear()
            gui.human_queues = {0: None, 1: None}
            if len(state_history) > 1:
                state_history.pop()
                state = state_history[-1].clone()
                gui.match_started = True
                gui.update_map_layout(state.width, state.height)
                gui.add_combat_log(f'[UNDO] Rolled back 1 step to Cycle {state.game_cycle}, P{state.current_player}. Press ENTER/SPACE to run.', (245, 190, 35))
                print(f'[Control] Undo step: Restored to Cycle {state.game_cycle}, P{state.current_player} turn (Paused).')
            else:
                gui.add_combat_log('[UNDO] Already at initial state.', (160, 175, 200))
                print('[Control] Undo ignored: Already at initial state.')
            gui.render(state, agent0, agent1)
            continue
        if state.is_terminal():
            ai_future = None
            gui.ai_thinking = False
            gui.render(state, agent0, agent1)
            continue
        if gui.is_paused and (not gui.step_requested) and (ai_future is None):
            gui.render(state, agent0, agent1)
            continue
        if active_is_human:
            if getattr(active_agent, 'turn_start_time', 0.0) == 0.0:
                if hasattr(active_agent, 'start_turn'):
                    active_agent.start_turn()
            queued_act = gui.get_queued_human_action(current_pid)
            if queued_act is None:
                queued_act = gui.poll_held_human_keys(current_pid, p0_is_human, p1_is_human)
            if queued_act is None:
                gui.render(state, agent0, agent1)
                continue
            else:
                action = queued_act
                if hasattr(active_agent, 'record_decision'):
                    active_agent.record_decision(action)
                if hasattr(active_agent, 'turn_start_time'):
                    active_agent.turn_start_time = 0.0
        else:
            if ai_future is None:
                if not (p0_is_human or p1_is_human) and (not gui.step_requested):
                    turn_delay = 0.35 / max(0.25, gui.speed_multiplier)
                    if time.perf_counter() - last_ai_turn_time < turn_delay:
                        gui.render(state, agent0, agent1)
                        continue
                gui.step_requested = False
                ai_think_start_time = time.perf_counter()
                cloned_s = state.clone()
                ai_future = ai_executor.submit(active_agent.choose_action, cloned_s, current_pid)
                concurrent.futures.wait([ai_future], timeout=0.025)
            if not ai_future.done():
                if time.perf_counter() - ai_think_start_time >= 0.25:
                    gui.ai_thinking = True
                    gui.ai_thinking_pid = current_pid
                gui.render(state, agent0, agent1)
                continue
            action = ai_future.result()
            ai_future = None
            gui.ai_thinking = False
            gui.ai_thinking_pid = None
            last_ai_turn_time = time.perf_counter()
        gui.step_requested = False
        print(f'[Cycle {state.game_cycle:2d}] P{current_pid} ({active_agent.name[:24]}) -> {action.value:<10} | Nodes: {active_agent.stats.explored_nodes:4d} | Time: {active_agent.stats.execution_time:.4f}s')
        if hasattr(gui, 'add_combat_log'):
            p_tag = 'P0 Blue' if current_pid == 0 else 'P1 Red'
            log_col = (90, 185, 255) if current_pid == 0 else (255, 120, 120)
            gui.add_combat_log(f'[C{state.game_cycle:02d}] {p_tag} -> {action.value} ({active_agent.stats.explored_nodes} nodes, {active_agent.stats.execution_time * 1000:.1f}ms)', log_col)
        next_state = gui.animate_turn(state, action, agent0, agent1)
        if getattr(gui, 'quit_requested', False):
            break
        state = next_state
        state_history.append(state.clone())
    ai_executor.shutdown(wait=False)
    if PYGAME_AVAILABLE:
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass
    winner = state.get_winner()
    w_str = f'Player {winner} ({(agent0.name if winner == 0 else agent1.name)}) WINS!' if winner in (0, 1) else 'MATCH DRAW!'
    print(f'\n=== GAME OVER: {w_str} ===')

def main():
    parser = argparse.ArgumentParser(description = 'Task 2: Tank Battle Game - Adversarial Search')
    parser.add_argument('--mode', choices = ['gui', 'benchmark'], default = 'gui', help='Run mode (gui or benchmark)')
    parser.add_argument('--benchmark', action = 'store_true', help='Chay nhanh che do benchmark tuong thich nhu Task 1')
    parser.add_argument('--p0', default = 'heuristic_alphabeta', help='Player 0 algorithm (human, heuristic_alphabeta, id_ab, alphabeta, heuristic_minimax, minimax, greedy, rival)')
    parser.add_argument('--p1', default = 'alphabeta', help='Player 1 algorithm (human, heuristic_alphabeta, id_ab, alphabeta, heuristic_minimax, minimax, greedy, rival)')
    parser.add_argument('--depth', type = int, default = 3, help='Search depth for built-in agents')
    parser.add_argument('--map', default = '01', help='Map scenario name, index (01..09), or custom .txt file path')
    parser.add_argument('--load_external', type=str, default=None, help='Path to external rival group agent .py file')
    parser.add_argument('--max_cycles', type=int, default=40, help='Max game cycles before draw')
    args = parser.parse_args()
    if args.benchmark:
        args.mode = 'benchmark'
    if args.mode == 'benchmark':
        from task2_tank.experiments.benchmark_tanks import TankTournament
        print('=== RUNNING AUTOMATED BENCHMARK SUITE ===')
        tournament = TankTournament(max_cycles_per_game = args.max_cycles)
        tournament.run_single_move_benchmark(depths = [1, 2, 3])
        tournament.run_tournament()
        tournament.plot_comparisons('benchmark_task2.png')
        print('\n' + tournament.export_tables())
    else:
        agent0 = get_agent_by_name(args.p0, depth = args.depth)
        if args.load_external:
            print(f'[Main] Loading external agent from {args.load_external}...')
            agent1 = AgentLoader.load_agent_from_file(args.load_external)
            if agent1 is None:
                print('[Main] Fallback to default Player 1 agent.')
                agent1 = get_agent_by_name(args.p1, depth = args.depth)
        else:
            agent1 = get_agent_by_name(args.p1, depth = args.depth)
        run_gui_game(agent0, agent1, max_cycles=args.max_cycles, map_name = args.map)
        
if __name__ == '__main__':
    main()