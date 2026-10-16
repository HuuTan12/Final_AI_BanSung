"""
Module: rules.py
Mô tả: Định nghĩa hàm chuyển trạng thái (Transition Function) và cơ chế xử lý va chạm đạn từng ô (cell-by-cell).
Thực hiện chính xác quy định:
- Đạn bay tối đa 3 ô / cycle theo hướng tank đang đối mặt.
- Kiểm tra va chạm sau TỪNG ô di chuyển (cell-by-cell check).
- Đạn dừng ngay lập tức khi trúng vật thể (Wall, Base, Tank).
"""

from typing import List, Tuple
from task2_tank.engine.game_state import GameState
from task2_tank.engine.actions import Action, Direction
from task2_tank.engine.entities import Bullet


class GameRules:
    """
    Quy tắc trò chơi điều phối chuyển trạng thái và va chạm vật lý theo turn-based.
    """

    @staticmethod
    def apply_action(state: GameState, action: Action) -> GameState:
        """
        Hàm chuyển trạng thái (Transition Function):
        Nhận vào GameState hiện tại và hành động của current_player,
        sinh ra GameState kế tiếp (successor).
        """
        pass

    @staticmethod
    def step_bullets(state: GameState) -> None:
        """
        Cơ chế xử lý đạn:
        Mỗi viên đạn di chuyển tối đa 3 ô. Sau mỗi ô (step 1, 2, 3):
        - Kiểm tra va chạm với Wall, Tank hoặc Base.
        - Trừ 1 HP của thực thể trúng đạn.
        - Xóa đạn ngay khi xảy ra va chạm hoặc bay ra ngoài map.
        """
        pass

    @staticmethod
    def _move_tank(state: GameState, player_id: int, direction: Direction) -> None:
        """
        Di chuyển tank 1 ô nếu không bị chặn bởi tường, base hoặc tank đối thủ.
        Cập nhật hướng mặt của tank theo hướng di chuyển.
        """
        pass

    @staticmethod
    def _fire_bullet(state: GameState, player_id: int) -> None:
        """
        Tank bắn đạn theo hướng đang đối mặt.
        """
        pass
