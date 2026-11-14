from typing import Set, Optional

class Cell:

    def __init__(self, r: int, c: int):
        self.r = r
        self.c = c
        self.pos = (r, c)
        self.domain: Set[int] = set(range(1, 10))
        self.value: Optional[int] = None

    @property
    def is_assigned(self) -> bool:
        return self.value is not None

    def assign(self, val: int) -> None:
        self.value = val

    def unassign(self) -> None:
        self.value = None

    def __hash__(self) -> int:
        return hash(self.pos)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Cell):
            return self.pos == other.pos
        return False

    def __repr__(self) -> str:
        return f'Cell({self.r},{self.c}, val={self.value}, d_size={len(self.domain)})'