import time
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Bullet
from task2_tank.engine.game_state import GameState
from task2_tank.engine.maps import MapBuilder
from task2_tank.engine.rules import GameRules
from task2_tank.agents.evaluator import TankEvaluator
from task2_tank.agents.minimax_agent import MinimaxAgent
from task2_tank.agents.alphabeta_agent import AlphaBetaAgent
from task2_tank.agents.heuristic_minimax_agent import HeuristicMinimaxAgent
from task2_tank.agents.heuristic_alphabeta_agent import HeuristicAlphaBetaAgent

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class TankTournament:

    def __init__(self, max_cycles_per_game = 40):
        self.max_cycles = max_cycles_per_game
        self.single_move_results = []
        self.match_results = []

    def _build_scenarios(self):
        """Creates varied game scenarios (opening, maze, midgame, endgame) for fair testing."""
        s_open = MapBuilder.create_standard_map()
        s_maze = MapBuilder.create_chokepoint_map()

        s_mid = MapBuilder.create_standard_map()
        s_mid.tanks[0].x, s_mid.tanks[0].y, s_mid.tanks[0].direction = 6, 7, Direction.UP
        s_mid.tanks[1].x, s_mid.tanks[1].y, s_mid.tanks[1].direction = 6, 3, Direction.DOWN
        s_mid.tanks[1].hp = 4
        s_mid.bullets.append(Bullet(6, 4, Direction.DOWN, owner_id=1))

        s_end = MapBuilder.create_standard_map()
        s_end.walls.pop((6, 1), None)
        s_end.tanks[0].x, s_end.tanks[0].y, s_end.tanks[0].direction = 6, 2, Direction.UP
        s_end.tanks[1].x, s_end.tanks[1].y, s_end.tanks[1].direction = 4, 2, Direction.RIGHT
        s_end.tanks[1].hp = 2
        s_end.bases[1].hp = 2

        return [
            ("Opening", s_open),
            ("Chokepoint", s_maze),
            ("Midgame", s_mid),
            ("Endgame", s_end),
        ]

    def run_single_move_benchmark(self, depths=None):
        if depths is None:
            depths = [1, 2, 3]

        print("1. RUNNING SINGLE-MOVE SEARCH BENCHMARK (FAIR MULTI-SCENARIO)")
        self.single_move_results = []
        scenarios = self._build_scenarios()

        for d in depths:
            agent_list = [
                ("1. Minimax Search", MinimaxAgent(depth = d)),
                ("2. Alpha-Beta Search", AlphaBetaAgent(depth = d)),
                ("3. Heuristic Minimax", HeuristicMinimaxAgent(depth = d)),
                ("4. Heuristic Alpha-Beta", HeuristicAlphaBetaAgent(depth = d)),
            ]

            for name, ag in agent_list:
                # Clear shared BFS distance cache so every agent starts under identical cold conditions
                TankEvaluator.clear_cache()

                t_list = []
                n_list = []
                p_list = []
                first_act = None

                for _, sc_state in scenarios:
                    act = ag.choose_action(sc_state, player_id = 0)
                    if first_act is None:
                        first_act = act
                    t_list.append(ag.stats.execution_time)
                    n_list.append(ag.stats.explored_nodes)
                    p_list.append(ag.stats.prune_count)

                t_avg = sum(t_list) / len(t_list)
                n_avg = sum(n_list) / len(n_list)
                p_avg = sum(p_list) / len(p_list)

                row = {}
                row["depth"] = d
                row["agent"] = name
                row["avg_time"] = t_avg
                row["avg_nodes"] = n_avg
                row["avg_prunes"] = p_avg
                row["action"] = first_act.value if first_act else Action.STAY.value
                self.single_move_results.append(row)

                print(f"-> [Depth {d}] {name:26s} | Time: {t_avg:8.5f}s | Nodes: {n_avg:6.0f} | Prunes: {p_avg:4.0f} | Opening Move: {row['action']}")

        return self.single_move_results

    def run_head_to_head_match(self, agent0, agent1, max_cycles = 40):
        state = MapBuilder.create_standard_map()
        state.max_cycles = max_cycles

        t0 = []
        t1 = []

        while not state.is_terminal():
            pid = state.current_player
            if pid == 0:
                ag = agent0
            else:
                ag = agent1

            act = ag.choose_action(state, pid)

            if pid == 0:
                t0.append(ag.stats.execution_time)
            else:
                t1.append(ag.stats.execution_time)

            state = GameRules.apply_action(state, act)

        winner = state.get_winner()
        avg0 = sum(t0) / max(1, len(t0))
        avg1 = sum(t1) / max(1, len(t1))
        return winner, state.game_cycle, avg0, avg1

    def run_tournament(self, depth = 3):
        print(f"2. RUNNING HEAD-TO-HEAD ROUND-ROBIN TOURNAMENT (EQUAL DEPTH d={depth})")
        self.match_results = []

        # Equal search depth across all 4 configurations for a fair comparison (Req 2)
        configs = [
            (f"1. Minimax (d={depth})", MinimaxAgent(depth = depth)),
            (f"2. Alpha-Beta (d={depth})", AlphaBetaAgent(depth = depth)),
            (f"3. Heuristic Minimax (d={depth})", HeuristicMinimaxAgent(depth = depth)),
            (f"4. Heuristic Alpha-Beta (d={depth})", HeuristicAlphaBetaAgent(depth = depth)),
        ]

        for i in range(len(configs)):
            for j in range(i + 1, len(configs)):
                name_a = configs[i][0]
                agent_a = configs[i][1]
                name_b = configs[j][0]
                agent_b = configs[j][1]

                TankEvaluator.clear_cache()
                win1, cyc1, a1, b1 = self.run_head_to_head_match(agent_a, agent_b, self.max_cycles)
                if win1 == 0:
                    ws1 = name_a
                elif win1 == 1:
                    ws1 = name_b
                else:
                    ws1 = "Draw"

                TankEvaluator.clear_cache()
                win2, cyc2, a2, b2 = self.run_head_to_head_match(agent_b, agent_a, self.max_cycles)
                if win2 == 0:
                    ws2 = name_b
                elif win2 == 1:
                    ws2 = name_a
                else:
                    ws2 = "Draw"

                m1 = {"match": f"{name_a} vs {name_b}", "p0": name_a, "p1": name_b, "winner": ws1, "cycles": cyc1}
                m2 = {"match": f"{name_b} vs {name_a}", "p0": name_b, "p1": name_a, "winner": ws2, "cycles": cyc2}
                self.match_results.append(m1)
                self.match_results.append(m2)

                print(f"-> Match 1: {name_a} (P0) vs {name_b} (P1) -> Winner: {ws1} ({cyc1} cycles)")
                print(f"-> Match 2: {name_b} (P0) vs {name_a} (P1) -> Winner: {ws2} ({cyc2} cycles)")

        return self.match_results

    def plot_comparisons(self, save_path="benchmark_task2.png"):
        if len(self.single_move_results) == 0:
            print("[Warning] No single-move benchmark data available to plot.")
            return ""

        if not os.path.isabs(save_path):
            folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            save_path = os.path.join(folder, save_path)

        fig, axs = plt.subplots(1, 2, figsize=(14, 5))
        if "seaborn-v0_8-whitegrid" in plt.style.available:
            plt.style.use("seaborn-v0_8-whitegrid")
        else:
            plt.style.use("default")

        names = []
        for r in self.single_move_results:
            if r["agent"] not in names:
                names.append(r["agent"])

        colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
        markers = ["o", "s", "^", "D"]

        for k in range(len(names)):
            xs = []
            ys = []
            for r in self.single_move_results:
                if r["agent"] == names[k]:
                    xs.append(r["depth"])
                    ys.append(r["avg_nodes"])
            axs[0].plot(xs, ys, marker = markers[k], color = colors[k], linewidth = 2, label = names[k])
        axs[0].set_title("Explored States (Nodes) vs Search Depth", fontsize = 12, fontweight = "bold")
        axs[0].set_xlabel("Search Depth")
        axs[0].set_ylabel("Explored States (Nodes)")
        axs[0].set_yscale("log")
        axs[0].grid(True, linestyle ="--", alpha = 0.6)
        axs[0].legend()

        for k in range(len(names)):
            xs = []
            ys = []
            for r in self.single_move_results:
                if r["agent"] == names[k]:
                    xs.append(r["depth"])
                    ys.append(r["avg_time"])
            axs[1].plot(xs, ys, marker = markers[k], color = colors[k], linewidth = 2, label = names[k])
        axs[1].set_title("Average Execution Time (Seconds) vs Depth", fontsize = 12, fontweight = "bold")
        axs[1].set_xlabel("Search Depth")
        axs[1].set_ylabel("Execution Time (s)")
        axs[1].grid(True, linestyle = "--", alpha = 0.6)
        axs[1].legend()

        plt.tight_layout()
        plt.savefig(save_path, dpi = 300)
        plt.close()
        print(f"\n[Visual] Benchmark comparison plot saved to: {os.path.abspath(save_path)}")
        return os.path.abspath(save_path)

    def export_tables(self):
        lines = []
        lines.append("Table 1: Search Performance Comparison Across 4 Configurations (Task 2 - Req 2)\n")
        lines.append("| Depth | Algorithm Configuration | Explored Nodes | Prune Count | Execution Time (s) | Chosen Action |")
        lines.append("|:---:|:---|:---:|:---:|:---:|:---:|")
        for r in self.single_move_results:
            lines.append(f"| {r['depth']} | {r['agent']} | {r['avg_nodes']:.0f} | {r['avg_prunes']:.0f} | {r['avg_time']:.5f} | `{r['action']}` |")

        lines.append("\nTable 2: Head-to-Head Tournament Results\n")
        lines.append("| Match Scenario | Player 0 (MAX) | Player 1 (MIN) | Winner | Game Cycles |")
        lines.append("|:---|:---|:---|:---|:---:|")
        for r in self.match_results:
            lines.append(f"| {r['match']} | {r['p0']} | {r['p1']} | **{r['winner']}** | {r['cycles']} |")

        return "\n".join(lines)

TankBenchmarkRunner = TankTournament

if __name__ == "__main__":
    bm = TankTournament(max_cycles_per_game = 25)
    bm.run_single_move_benchmark(depths=[1, 2, 3])
    bm.run_tournament()
    bm.plot_comparisons("benchmark_task2.png")
    print("\n" + bm.export_tables())