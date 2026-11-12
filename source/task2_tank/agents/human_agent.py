"""
human_agent.py - Interactive Human Controller for Tank Battle
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Enables human players to control tanks via keyboard (WASD / Arrow keys)
    or clickable GUI buttons. Supports Human vs AI, Human vs Human (Local PVP),
    and AI vs Human match configurations.
"""

import time
from typing import Optional
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class HumanAgent(BaseAgent):
    """
    Interactive Human Controller with reaction time telemetry and input management.
    Supports keyboard controls (WASD / Arrows), mouse clicks on the battlefield,
    continuous key-hold driving, and on-screen HUD buttons.
    """

    def __init__(self, name: str = "Human (Player)"):
        super().__init__(name=name)
        self.is_human: bool = True
        self.pending_action: Optional[Action] = None
        self.turn_start_time: float = 0.0
        self.last_reaction_time: float = 0.0
        self.total_moves: int = 0
        self.total_shots: int = 0

    def start_turn(self) -> None:
        """Records timestamp when human turn begins to measure reaction time."""
        self.turn_start_time = time.perf_counter()

    def record_decision(self, action: Action) -> None:
        """Records decision statistics and reaction latency."""
        if self.turn_start_time > 0.0:
            self.last_reaction_time = time.perf_counter() - self.turn_start_time
            self.stats.execution_time = self.last_reaction_time
        else:
            self.last_reaction_time = 0.0
            self.stats.execution_time = 0.0
        self.stats.explored_nodes = 1

        if action == Action.FIRE:
            self.total_shots += 1
        elif action != Action.STAY:
            self.total_moves += 1

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Returns the action queued by human input.
        If no action was queued yet, returns Action.STAY.
        """
        if self.pending_action is not None:
            action = self.pending_action
            self.pending_action = None
            self.record_decision(action)
            return action
        return Action.STAY

    def set_action(self, action: Action) -> None:
        """Queues an action from keyboard event or UI button click."""
        self.pending_action = action
