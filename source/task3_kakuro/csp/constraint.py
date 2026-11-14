import itertools
from functools import lru_cache
from typing import List, Set, Tuple
from task3_kakuro.csp.variable import Cell


class RunConstraint:

    def __init__(self, direction: str, target_sum: int, cells: List[Cell]):
        self.direction = direction
        self.target_sum = target_sum
        self.cells = cells
        self.length = len(cells)

    @staticmethod
    @lru_cache(maxsize=512)
    def get_valid_combinations(target_sum: int, length: int) -> List[Tuple[int, ...]]:
        if length < 1 or length > 9:
            return []

        valid_combos = []
        all_digits = range(1, 10)

        for combo in itertools.combinations(all_digits, length):
            total = sum(combo)

            if total == target_sum:
                valid_combos.append(combo)

        return valid_combos

    def get_possible_digits(self) -> Set[int]:
        digits = set()
        combos = self.get_valid_combinations(self.target_sum, self.length)

        for combo in combos:
            digits.update(combo)

        return digits

    def is_satisfied(self) -> bool:
        values = []

        for cell in self.cells:
            if not cell.is_assigned:
                return False

            values.append(cell.value)

        if len(values) != self.length:
            return False

        if len(set(values)) != self.length:
            return False

        if sum(values) != self.target_sum:
            return False

        return True

    def is_partially_valid(self) -> bool:
        assigned_values = []
        unassigned_count = 0

        for cell in self.cells:
            if cell.is_assigned:
                assigned_values.append(cell.value)
            else:
                unassigned_count = unassigned_count + 1

        if len(assigned_values) != len(set(assigned_values)):
            return False

        current_sum = sum(assigned_values)

        if current_sum > self.target_sum:
            return False

        if unassigned_count == 0:
            if current_sum == self.target_sum:
                return True
            else:
                return False

        remaining_sum = self.target_sum - current_sum
        used_digits = set(assigned_values)

        available_digits = []

        for digit in range(1, 10):
            if digit not in used_digits:
                available_digits.append(digit)

        if len(available_digits) < unassigned_count:
            return False

        min_possible = 0

        for i in range(unassigned_count):
            min_possible = min_possible + available_digits[i]

        max_possible = 0
        last_index = len(available_digits) - 1

        for i in range(unassigned_count):
            max_possible = max_possible + available_digits[last_index - i]

        if remaining_sum >= min_possible and remaining_sum <= max_possible:
            return True
        else:
            return False