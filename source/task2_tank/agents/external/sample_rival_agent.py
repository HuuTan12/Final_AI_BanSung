"""
sample_rival_agent.py - Sample External Agent from Another Student Group
Course: Introduction to Artificial Intelligence (503043)
Author: Rival Student Group (External Integration Example)
Description:
    Demonstrates that external agents written by other student groups
    can seamlessly integrate with our game framework by inheriting from BaseAgent.
"""

from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class RivalGroupAgent(BaseAgent):
    """
    Sample rival agent implementing a greedy rule-based combat policy:
    1. Fires if opponent tank or base is in direct line of sight.
    2. Moves towards the enemy base using Manhattan distance heuristic.
    3. Dodges if an incoming bullet is detected.
    """

    def __init__(self):
        super().__init__(name="RivalGroup-HeuristicBot")

    def choose_action(self, state: GameState, player_id: int) -> Action:
        legal_actions = state.get_legal_actions(player_id)
        if not legal_actions:
            return Action.STAY

        my_tank = state.tanks.get(player_id)
        opp_base = state.bases.get(1 - player_id)

        if not my_tank or not my_tank.is_alive:
            return Action.STAY

        # 1. Fire if aligned
        if Action.FIRE in legal_actions and opp_base:
            # Check alignment with enemy base
            dx, dy = my_tank.direction.value
            if (dx != 0 and my_tank.y == opp_base.y) or (dy != 0 and my_tank.x == opp_base.x):
                return Action.FIRE

        # 2. Greedily advance towards enemy base
        if opp_base:
            best_action = legal_actions[0]
            best_dist = float("inf")
            for action in legal_actions:
                direction = Action.get_move_direction(action)
                if direction:
                    dx, dy = direction.value
                    new_dist = abs(my_tank.x + dx - opp_base.x) + abs(my_tank.y + dy - opp_base.y)
                    if new_dist < best_dist:
                        best_dist = new_dist
                        best_action = action
            return best_action

        return Action.FIRE if Action.FIRE in legal_actions else legal_actions[0]
