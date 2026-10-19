"""
base_agent.py - Standard Agent Interface and Performance Statistics
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Defines the abstract base class BaseAgent and SearchStats dataclass.
    Acts as the standard public interface for all tank algorithms,
    including internal search algorithms and external agents from other groups.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


@dataclass
class SearchStats:
    """
    Search performance metrics recorded per decision move.
    """
    explored_nodes: int = 0
    prune_count: int = 0
    search_depth: int = 0
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "explored_nodes": self.explored_nodes,
            "prune_count": self.prune_count,
            "search_depth": self.search_depth,
            "execution_time": round(self.execution_time, 6),
        }


class BaseAgent(ABC):
    """
    Abstract Base Class for all tank-controlling AI agents.
    Every agent (Minimax, AlphaBeta, Heuristic, or Rival group agent)
    must inherit from this class and implement choose_action.
    """

    def __init__(self, name: str):
        self.name = name
        self.stats = SearchStats()

    @abstractmethod
    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Core decision method: Receives current GameState and player_id (0 or 1),
        returns one of the 6 legal Action enums.
        """
        pass

    def reset_stats(self) -> None:
        """Resets search metrics before planning a new move."""
        self.stats = SearchStats()
