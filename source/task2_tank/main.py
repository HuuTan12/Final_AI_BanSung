"""
Module: main.py
Mô tả: Điểm khởi chạy chính (Entry Point) của Task 2 - Tank Battle Game.
Cho phép chạy với PyGame GUI hoặc chạy chế độ headless benchmark.
"""

import argparse
from task2_tank.engine.maps import MapBuilder
from task2_tank.agents.heuristic_alphabeta_agent import HeuristicAlphaBetaAgent
from task2_tank.agents.minimax_agent import MinimaxAgent
from task2_tank.ui.pygame_ui import TankGameGUI
from task2_tank.agent_loader import AgentLoader


def main():
    parser = argparse.ArgumentParser(description="AI Tank Battle Game - Adversarial Search")
    parser.add_argument("--mode", choices=["gui", "benchmark"], default="gui", help="Chế độ chạy")
    parser.add_argument("--p0", default="heuristic_alphabeta", help="Agent cho Player 0")
    parser.add_argument("--p1", default="alphabeta", help="Agent cho Player 1")
    parser.add_argument("--load_external", type=str, default=None, help="Đường dẫn nạp Agent của nhóm khác")
    args = parser.parse_args()

    print(f"=== KHỞI CHẠY TANK BATTLE (Mode: {args.mode}) ===")
    # Khởi tạo bản đồ và các Agent tương ứng


if __name__ == "__main__":
    main()
