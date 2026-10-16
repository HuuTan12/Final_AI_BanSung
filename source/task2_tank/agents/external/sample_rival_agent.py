"""
Module: sample_rival_agent.py
Mô tả: File mẫu đại diện cho thuật toán của một nhóm sinh viên khác gửi tới.
Minh họa việc kế thừa BaseAgent và tuân thủ giao diện choose_action(state, player_id).
"""

from task2_tank.agents.base_agent import BaseAgent
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action


class RivalGroupAgent(BaseAgent):
    """
    Agent mẫu của nhóm khác được tích hợp vào hệ thống thi đấu.
    """

    def __init__(self):
        super().__init__(name="RivalGroup-CustomAI")

    def choose_action(self, state: GameState, player_id: int) -> Action:
        """
        Chiến thuật riêng của nhóm đối thủ (ví dụ: né đạn và bắn về phía Base).
        """
        legal_actions = state.get_legal_actions(player_id)
        if Action.FIRE in legal_actions:
            return Action.FIRE
        return legal_actions[0] if legal_actions else Action.STAY
