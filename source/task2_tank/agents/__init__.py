"""
Module: agents
Adversarial search and game-playing agent implementations:
1. MinimaxAgent (Pure Minimax Search - Req 2)
2. AlphaBetaAgent (Alpha-Beta Pruning - Req 2)
3. HeuristicMinimaxAgent (Heuristic Minimax with Evaluation Function - Req 2)
4. HeuristicAlphaBetaAgent (Optimal Heuristic Alpha-Beta with Move Ordering - Req 2)
5. IterativeDeepeningAgent (Proposed: Iterative Deepening with Transposition Table)
6. GreedyTacticalAgent (Proposed: 1-Ply Greedy Tactical Baseline)
7. HumanAgent (Interactive Human Controller via Keyboard & GUI D-Pad)
"""

from task2_tank.agents.base_agent import BaseAgent, SearchStats
from task2_tank.agents.minimax_agent import MinimaxAgent
from task2_tank.agents.alphabeta_agent import AlphaBetaAgent
from task2_tank.agents.heuristic_minimax_agent import HeuristicMinimaxAgent
from task2_tank.agents.heuristic_alphabeta_agent import HeuristicAlphaBetaAgent
from task2_tank.agents.iterative_deepening_agent import IterativeDeepeningAgent
from task2_tank.agents.greedy_agent import GreedyTacticalAgent
from task2_tank.agents.human_agent import HumanAgent
from task2_tank.agents.evaluator import TankEvaluator

__all__ = [
    "BaseAgent",
    "SearchStats",
    "MinimaxAgent",
    "AlphaBetaAgent",
    "HeuristicMinimaxAgent",
    "HeuristicAlphaBetaAgent",
    "IterativeDeepeningAgent",
    "GreedyTacticalAgent",
    "HumanAgent",
    "TankEvaluator",
]
