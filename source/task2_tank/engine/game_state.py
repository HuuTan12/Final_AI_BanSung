"""
Module: game_state.py
Mô tả: Đại diện cho trạng thái toàn cục của trò chơi Tank Battle (GameState).
Đáp ứng yêu cầu 1 (1.0 điểm) của Task 2: Mô hình hóa Zero-Sum Game.
"""

from typing import List, Dict, Tuple, Optional
from task2_tank.engine.actions import Action
from task2_tank.engine.entities import Tank, Base, Wall, Bullet


class GameState:
    """
    Biểu diễn trạng thái trò chơi tại một thời điểm trong cây tìm kiếm đối kháng.
    
    Bao gồm:
    - Kích thước bản đồ (width, height)
    - Thông tin 2 Tanks (vị trí, HP, hướng)
    - Thông tin 2 Bases (vị trí, HP)
    - Bản đồ các tường Walls (vị trí -> HP)
    - Danh sách các đạn Bullets đang bay
    - Lượt đi hiện tại (current_player: 0 hoặc 1)
    - Chu kỳ trò chơi (game_cycle)
    """

    def __init__(self, width: int = 13, height: int = 13):
        self.width = width
        self.height = height
        self.tanks: Dict[int, Tank] = {}
        self.bases: Dict[int, Base] = {}
        self.walls: Dict[Tuple[int, int], Wall] = {}
        self.bullets: List[Bullet] = []
        self.current_player: int = 0
        self.game_cycle: int = 0
        self.max_cycles: int = 200

    def clone(self) -> 'GameState':
        """
        Tạo bản sao sâu (deep copy độc lập) của GameState để phục vụ mở rộng cây tìm kiếm.
        """
        pass

    def get_legal_actions(self, player_id: int) -> List[Action]:
        """
        Lấy danh sách các hành động hợp lệ của Tank player_id trong trạng thái hiện tại.
        (Loại bỏ các bước di chuyển đâm vào tường, căn cứ, hoặc vượt ra ngoài biên).
        """
        pass

    def is_terminal(self) -> bool:
        """
        Kiểm tra trạng thái kết thúc (Terminal State):
        1. Một trong hai Căn cứ (Base) bị phá hủy (HP <= 0).
        2. Một trong hai Tank bị phá hủy (HP <= 0).
        3. Vượt quá số chu kỳ tối đa (Hòa).
        """
        pass

    def get_winner(self) -> Optional[int]:
        """
        Xác định người chiến thắng: 0, 1 hoặc None (nếu hòa hoặc chưa kết thúc).
        """
        pass

    def get_utility(self, player_id: int) -> float:
        """
        Hàm Utility (Zero-Sum):
        +10000.0 nếu player_id thắng.
        -10000.0 nếu player_id thua.
        0.0 nếu hòa.
        """
        pass
