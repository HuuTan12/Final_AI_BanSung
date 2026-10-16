"""
Module: evaluator.py
Mô tả: Hàm đánh giá trạng thái heuristic (State Evaluation Function)
cho Heuristic Minimax và Heuristic Alpha-Beta.
"""

from task2_tank.engine.game_state import GameState


class TankEvaluator:
    """
    Tính điểm đánh giá trạng thái bất kỳ dưới góc nhìn của player_id:
    Score = w1*(my_tank_hp - opp_tank_hp) 
          + w2*(my_base_hp - opp_base_hp) 
          - w3*dist_to_opp_base 
          + w4*in_firing_line 
          - w5*in_bullet_danger
    """

    def __init__(self, w_tank_hp: float = 50.0, w_base_hp: float = 100.0,
                 w_dist_base: float = 5.0, w_line_of_fire: float = 30.0,
                 w_bullet_danger: float = 80.0):
        self.w_tank_hp = w_tank_hp
        self.w_base_hp = w_base_hp
        self.w_dist_base = w_dist_base
        self.w_line_of_fire = w_line_of_fire
        self.w_bullet_danger = w_bullet_danger

    def evaluate(self, state: GameState, player_id: int) -> float:
        """
        Tính toán và trả về điểm số lượng hóa độ lợi thế của trạng thái hiện tại.
        """
        pass
