from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action

@dataclass
class SearchStats:
    explored_nodes: int = 0
    prune_count: int = 0
    search_depth: int = 0
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {'explored_nodes': self.explored_nodes, 'prune_count': self.prune_count, 'search_depth': self.search_depth, 'execution_time': round(self.execution_time, 6)}

class BaseAgent(ABC):

    def __init__(self, name: str):
        self.name = name
        self.stats = SearchStats()

    @abstractmethod
    def choose_action(self, state: GameState, player_id: int) -> Action:
        pass

    def reset_stats(self) -> None:
        self.stats = SearchStats()
