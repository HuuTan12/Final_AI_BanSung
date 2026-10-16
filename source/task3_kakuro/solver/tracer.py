"""
Module: tracer.py
Mô tả: Áp dụng Observer Pattern để ghi lại toàn bộ sự kiện diễn ra trong quá trình giải
(Gán giá trị, Tỉa nhánh miền giá trị, Quay lui, Hoàn tất).
Đóng vai trò cầu nối dữ liệu để Giao diện đồ họa (UI) phát lại và trực quan hóa từng bước.
"""

from enum import Enum
from typing import List, Any, Optional
from dataclasses import dataclass
from task3_kakuro.csp.variable import Cell


class EventType(Enum):
    INITIAL_DOMAINS = "INITIAL_DOMAINS"
    ASSIGN = "ASSIGN"
    PRUNE = "PRUNE"
    RESTORE = "RESTORE"
    BACKTRACK = "BACKTRACK"
    SOLVED = "SOLVED"
    NO_SOLUTION = "NO_SOLUTION"


@dataclass
class SolverEvent:
    event_type: EventType
    cell_pos: Optional[tuple] = None
    value: Optional[int] = None
    pruned_domain: Optional[set] = None
    message: str = ""


class SolverTracer:
    """
    Thu thập vết hoạt động của Backtracking và AC-3 để UI trình chiếu.
    """

    def __init__(self):
        self.events: List[SolverEvent] = []

    def emit(self, event_type: EventType, cell_pos=None, value=None, pruned_domain=None, message=""):
        event = SolverEvent(event_type, cell_pos, value, pruned_domain, message)
        self.events.append(event)

    def clear(self):
        self.events.clear()
