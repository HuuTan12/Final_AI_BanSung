"""
human_agent.py - Interactive Human Controller for Tank Battle
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Enables human players to control tanks via keyboard (WASD / Arrow keys)
    or clickable GUI buttons. Supports Human vs AI, Human vs Human (Local PVP),
    and AI vs Human match configurations.
"""

from typing import Optional
from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class HumanAgent(BaseAgent):
    """
    Agent controlled by a human user through keyboard or UI mouse clicks.
    """

    def __init__(self, name: str = "Human (Player)"):
        super().__init__(name=name)
        self.is_human: bool = True
        self.pending_action: Optional[Action] = None

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Returns the action queued by human input.
        If no action was queued yet, returns Action.STAY.
        """
        if self.pending_action is not None:
            action = self.pending_action
            self.pending_action = None
            return action
        return Action.STAY

    def set_action(self, action: Action) -> None:
        """Queues an action from keyboard event or UI button click."""
        self.pending_action = action
