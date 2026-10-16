"""
Module: benchmark_tanks.py
Mô tả: Thiết lập thí nghiệm so sánh toàn diện 4 cấu hình theo yêu cầu 2 (1.5 điểm) của Task 2:
1. Minimax Search
2. Alpha-Beta Search
3. Heuristic Minimax Search
4. Heuristic Minimax Search with Alpha-Beta Pruning
Ghi nhận các chỉ số: Thời gian tính toán (Execution Time), Số trạng thái đã khám phá (Explored States),
Độ sâu tìm kiếm (Search Depth), và Tỷ lệ thắng/thua khi đấu chéo.
"""

from typing import List, Dict, Any
from task2_tank.agents.minimax_agent import MinimaxAgent
from task2_tank.agents.alphabeta_agent import AlphaBetaAgent
from task2_tank.agents.heuristic_minimax_agent import HeuristicMinimaxAgent
from task2_tank.agents.heuristic_alphabeta_agent import HeuristicAlphaBetaAgent


class TankTournament:
    """
    Bộ điều phối giải đấu vòng tròn và đo đạc số liệu giữa 4 cấu hình AI.
    """

    def __init__(self, rounds_per_pair: int = 10):
        self.rounds_per_pair = rounds_per_pair
        self.results: List[Dict[str, Any]] = []

    def run_benchmark(self) -> None:
        """
        Cho 4 cấu hình đấu chéo (đổi bên P0/P1 để đảm bảo công bằng).
        Ghi nhận:
        - Thời gian trung bình mỗi nước đi
        - Số node trung bình mở rộng mỗi nước
        - Tỉ lệ thắng / hòa / thua
        """
        pass

    def export_latex_table(self) -> str:
        """
        Xuất bảng kết quả chuẩn LaTeX chèn trực tiếp vào báo cáo IEEE Task 4.
        """
        pass


if __name__ == "__main__":
    tournament = TankTournament()
    print("TankTournament skeleton initialized.")
