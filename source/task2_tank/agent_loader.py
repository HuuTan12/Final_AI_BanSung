"""
Module: agent_loader.py
Mô tả: Cơ chế nạp động (Dynamic Loading) thuật toán của các nhóm sinh viên khác từ file Python bên ngoài.
Thực hiện yêu cầu 3 (0.5 điểm) của Task 2:
- Tự động quét và nạp file .py trong thư mục agents/external/.
- Kiểm tra kế thừa BaseAgent và xác thực giao diện choose_action(state, player_id).
- Bọc xử lý ngoại lệ (Exception Handling) và bảo vệ an toàn để agent lỗi không làm sập game.
"""

import os
import importlib.util
import inspect
from typing import List, Type, Optional
from task2_tank.agents.base_agent import BaseAgent


class AgentLoader:
    """
    Quản lý việc nạp và đăng ký các thuật toán tham gia thi đấu đối kháng.
    """

    @staticmethod
    def load_agent_from_file(file_path: str) -> Optional[BaseAgent]:
        """
        Nạp động một lớp Agent từ đường dẫn file .py chỉ định.
        """
        pass

    @staticmethod
    def discover_external_agents(folder_path: str = "agents/external") -> List[BaseAgent]:
        """
        Tự động quét thư mục và khởi tạo danh sách tất cả các Agent hợp lệ của các nhóm khác.
        """
        pass
