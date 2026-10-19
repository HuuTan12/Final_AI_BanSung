"""
benchmark_tanks.py - Comprehensive Benchmark for Task 2 (4 AI Configurations)
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Conducts comparative experiments for the 4 required search configurations (Req 2 - 1.5 pt):
    1. Minimax Search
    2. Alpha-Beta Search
    3. Heuristic Minimax Search
    4. Heuristic Minimax Search with Alpha-Beta Pruning
    Evaluates execution time, explored game states, search depth, and match performance.
    Exports Markdown / LaTeX tables and comparison plots.
"""

import time
import os
import sys

# Ensure UTF-8 output across Windows, macOS, and Linux
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add parent source directory to sys.path
source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from typing import List, Dict, Any, Tuple

from task2_tank.engine.game_state import GameState
from task2_tank.engine.maps import MapBuilder
from task2_tank.engine.rules import GameRules
from task2_tank.agents.minimax_agent import MinimaxAgent
from task2_tank.agents.alphabeta_agent import AlphaBetaAgent
from task2_tank.agents.heuristic_minimax_agent import HeuristicMinimaxAgent
from task2_tank.agents.heuristic_alphabeta_agent import HeuristicAlphaBetaAgent

import matplotlib
matplotlib.use("Agg")  # Safe for headless execution
import matplotlib.pyplot as plt


class TankTournament:
    """
    Automated benchmark suite for adversarial search algorithms in Tank Battle.
    """

    def __init__(self, max_cycles_per_game: int = 40):
        self.max_cycles = max_cycles_per_game
        self.single_move_results: List[Dict[str, Any]] = []
        self.match_results: List[Dict[str, Any]] = []

    def run_single_move_benchmark(self, depths: List[int] = None) -> List[Dict[str, Any]]:
        """
        Evaluates the 4 configurations on identical game scenarios across varying depths.
        Measures exact computation time and explored game states (nodes).
        """
        if depths is None:
            depths = [1, 2, 3]

        print("=== 1. RUNNING SINGLE-MOVE SEARCH BENCHMARK ===")
        self.single_move_results = []
        state = MapBuilder.create_standard_map()

        for d in depths:
            agents = [
                ("1. Minimax Search", MinimaxAgent(depth=d)),
                ("2. Alpha-Beta Search", AlphaBetaAgent(depth=d)),
                ("3. Heuristic Minimax", HeuristicMinimaxAgent(depth=d)),
                ("4. Heuristic Alpha-Beta", HeuristicAlphaBetaAgent(depth=d)),
            ]

            for label, agent in agents:
                # Run 3 trials to obtain reliable average runtime
                times = []
                nodes = []
                prunes = []

                for _ in range(3):
                    action = agent.choose_action(state, player_id=0)
                    times.append(agent.stats.execution_time)
                    nodes.append(agent.stats.explored_nodes)
                    prunes.append(agent.stats.prune_count)

                avg_time = sum(times) / len(times)
                avg_nodes = sum(nodes) / len(nodes)
                avg_prunes = sum(prunes) / len(prunes)

                entry = {
                    "depth": d,
                    "agent": label,
                    "avg_time": avg_time,
                    "avg_nodes": avg_nodes,
                    "avg_prunes": avg_prunes,
                    "action": action.value
                }
                self.single_move_results.append(entry)
                print(f"-> [Depth {d}] {label:32s} | Time: {avg_time:8.5f}s | Nodes: {avg_nodes:6.0f} | Prunes: {avg_prunes:4.0f} | Move: {action.value}")

        return self.single_move_results

    def run_head_to_head_match(self, agent0, agent1, max_cycles: int = 40) -> Tuple[Optional[int], int, float, float]:
        """
        Runs a complete match between agent0 (Player 0) and agent1 (Player 1).
        Returns: (winner_id, total_cycles, avg_time_p0, avg_time_p1).
        """
        state = MapBuilder.create_standard_map()
        state.max_cycles = max_cycles

        times_p0 = []
        times_p1 = []

        while not state.is_terminal():
            current_pid = state.current_player
            agent = agent0 if current_pid == 0 else agent1

            action = agent.choose_action(state, current_pid)

            if current_pid == 0:
                times_p0.append(agent.stats.execution_time)
            else:
                times_p1.append(agent.stats.execution_time)

            state = GameRules.apply_action(state, action)

        winner = state.get_winner()
        avg_t0 = sum(times_p0) / max(1, len(times_p0))
        avg_t1 = sum(times_p1) / max(1, len(times_p1))
        return winner, state.game_cycle, avg_t0, avg_t1

    def run_tournament(self) -> List[Dict[str, Any]]:
        """
        Executes round-robin matches between all pairs of AI configurations.
        Both sides switch positions (P0/P1) to guarantee fair evaluation.
        """
        print("\n=== 2. RUNNING HEAD-TO-HEAD ROUND-ROBIN TOURNAMENT ===")
        self.match_results = []

        configs = [
            ("Minimax (d=2)", MinimaxAgent(depth=2)),
            ("Alpha-Beta (d=2)", AlphaBetaAgent(depth=2)),
            ("Heuristic Minimax (d=3)", HeuristicMinimaxAgent(depth=3)),
            ("Heuristic Alpha-Beta (d=3)", HeuristicAlphaBetaAgent(depth=3)),
        ]

        for i in range(len(configs)):
            for j in range(i + 1, len(configs)):
                name_a, agent_a = configs[i]
                name_b, agent_b = configs[j]

                # Match 1: A as P0, B as P1
                winner1, cycles1, t0_1, t1_1 = self.run_head_to_head_match(agent_a, agent_b, self.max_cycles)
                w_str1 = name_a if winner1 == 0 else (name_b if winner1 == 1 else "Draw")

                # Match 2: B as P0, A as P1 (swapped sides)
                winner2, cycles2, t0_2, t1_2 = self.run_head_to_head_match(agent_b, agent_a, self.max_cycles)
                w_str2 = name_b if winner2 == 0 else (name_a if winner2 == 1 else "Draw")

                entry1 = {"match": f"{name_a} vs {name_b}", "p0": name_a, "p1": name_b, "winner": w_str1, "cycles": cycles1}
                entry2 = {"match": f"{name_b} vs {name_a}", "p0": name_b, "p1": name_a, "winner": w_str2, "cycles": cycles2}
                self.match_results.extend([entry1, entry2])

                print(f"-> Match 1: {name_a} (P0) vs {name_b} (P1) -> Winner: {w_str1} ({cycles1} cycles)")
                print(f"-> Match 2: {name_b} (P0) vs {name_a} (P1) -> Winner: {w_str2} ({cycles2} cycles)")

        return self.match_results

    def plot_comparisons(self, save_path: str = "benchmark_task2.png") -> str:
        """
        Generates comparison plots for the 4 search configurations.
        """
        if not self.single_move_results:
            print("[Warning] No single-move benchmark data available to plot.")
            return ""

        fig, axs = plt.subplots(1, 2, figsize=(14, 5))
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        agents_labels = list(dict.fromkeys(r["agent"] for r in self.single_move_results))
        depths = list(dict.fromkeys(r["depth"] for r in self.single_move_results))

        colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
        markers = ["o", "s", "^", "D"]

        # Subplot 1: Explored nodes vs Depth
        for idx, agent_label in enumerate(agents_labels):
            data = [r for r in self.single_move_results if r["agent"] == agent_label]
            axs[0].plot(
                [r["depth"] for r in data],
                [r["avg_nodes"] for r in data],
                marker=markers[idx],
                color=colors[idx],
                linewidth=2,
                label=agent_label
            )
        axs[0].set_title("Explored States (Nodes) vs Search Depth", fontsize=12, fontweight="bold")
        axs[0].set_xlabel("Search Depth")
        axs[0].set_ylabel("Explored States (Nodes)")
        axs[0].set_yscale("log")
        axs[0].grid(True, linestyle="--", alpha=0.6)
        axs[0].legend()

        # Subplot 2: Execution time vs Depth
        for idx, agent_label in enumerate(agents_labels):
            data = [r for r in self.single_move_results if r["agent"] == agent_label]
            axs[1].plot(
                [r["depth"] for r in data],
                [r["avg_time"] for r in data],
                marker=markers[idx],
                color=colors[idx],
                linewidth=2,
                label=agent_label
            )
        axs[1].set_title("Average Execution Time (Seconds) vs Depth", fontsize=12, fontweight="bold")
        axs[1].set_xlabel("Search Depth")
        axs[1].set_ylabel("Execution Time (s)")
        axs[1].grid(True, linestyle="--", alpha=0.6)
        axs[1].legend()

        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"\n[Visual] Benchmark comparison plot saved to: {os.path.abspath(save_path)}")
        return os.path.abspath(save_path)

    def export_tables(self) -> str:
        """
        Exports Markdown / LaTeX tables for the IEEE report.
        """
        md = []
        md.append("### Table 1: Search Performance Comparison Across 4 Configurations (Task 2 - Req 2)\n")
        md.append("| Depth | Algorithm Configuration | Explored Nodes | Prune Count | Execution Time (s) | Chosen Action |")
        md.append("|:---:|:---|:---:|:---:|:---:|:---:|")
        for r in self.single_move_results:
            md.append(f"| {r['depth']} | {r['agent']} | {r['avg_nodes']:.0f} | {r['avg_prunes']:.0f} | {r['avg_time']:.5f} | `{r['action']}` |")

        md.append("\n### Table 2: Head-to-Head Tournament Results\n")
        md.append("| Match Scenario | Player 0 (MAX) | Player 1 (MIN) | Winner | Game Cycles |")
        md.append("|:---|:---|:---|:---|:---:|")
        for r in self.match_results:
            md.append(f"| {r['match']} | {r['p0']} | {r['p1']} | **{r['winner']}** | {r['cycles']} |")

        return "\n".join(md)


if __name__ == "__main__":
    benchmark = TankTournament(max_cycles_per_game=25)
    benchmark.run_single_move_benchmark(depths=[1, 2, 3])
    benchmark.run_tournament()
    benchmark.plot_comparisons("benchmark_task2.png")
    print("\n" + benchmark.export_tables())

