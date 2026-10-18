"""
problem.py - N-Queens Problem Representation
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Represents the N-Queens problem formulation. Handles coordinate
    conversions for SAT solvers, checks validity of solutions,
    and displays the chessboard in ASCII format.
"""

from typing import List, Tuple, Optional


class NQueensProblem:
    """
    Representation of an N x N chessboard for the N-Queens puzzle.
    """

    def __init__(self, n: int):
        if n < 4:
            raise ValueError(f"N must be greater than or equal to 4 (given n = {n}).")
        self.n = n

    def to_var(self, r: int, c: int) -> int:
        """
        Maps a 0-indexed coordinate (r, c) on the board to a 1-based variable ID for SAT solvers.
        Formula: var_id = r * n + c + 1
        Range: [1, n * n]
        """
        if not (0 <= r < self.n and 0 <= c < self.n):
            raise ValueError(f"Coordinate ({r}, {c}) is out of board bounds for N = {self.n}.")
        return r * self.n + c + 1

    def to_coords(self, var_id: int) -> Tuple[int, int]:
        """
        Converts a 1-based variable ID back to 0-indexed coordinate (r, c).
        """
        if not (1 <= var_id <= self.n * self.n):
            raise ValueError(f"Variable ID {var_id} is out of valid range [1, {self.n * self.n}].")
        idx = var_id - 1
        return idx // self.n, idx % self.n

    def is_valid_solution(self, queen_positions: List[int]) -> bool:
        """
        Checks whether a given assignment is a valid N-Queens solution.
        queen_positions is a list of size N where queen_positions[col] = row.
        """
        if queen_positions is None or len(queen_positions) != self.n:
            return False

        # Check bounds
        for row in queen_positions:
            if not (0 <= row < self.n):
                return False

        # Check row uniqueness (no two queens in the same row)
        if len(set(queen_positions)) != self.n:
            return False

        # Check diagonal conflicts
        for c1 in range(self.n):
            for c2 in range(c1 + 1, self.n):
                r1, r2 = queen_positions[c1], queen_positions[c2]
                if abs(r1 - r2) == abs(c1 - c2):
                    return False

        return True

    def count_attacking_pairs(self, queen_positions: List[int]) -> int:
        """
        Calculates the total number of attacking pairs of queens.
        Returns 0 if and only if the assignment is a valid solution.
        """
        if queen_positions is None or len(queen_positions) != self.n:
            return -1

        attacks = 0
        for c1 in range(self.n):
            for c2 in range(c1 + 1, self.n):
                r1, r2 = queen_positions[c1], queen_positions[c2]
                if r1 == r2 or abs(r1 - r2) == abs(c1 - c2):
                    attacks += 1
        return attacks

    def display(self, queen_positions: List[int]) -> None:
        """
        Prints an ASCII visualization of the chessboard.
        """
        if queen_positions is None or len(queen_positions) != self.n:
            print("No valid board to display.")
            return

        print(f"\n--- N-Queens Board (N = {self.n}) ---")
        for r in range(self.n):
            row_cells = []
            for c in range(self.n):
                if queen_positions[c] == r:
                    row_cells.append(" Q ")
                else:
                    row_cells.append(" . ")
            print(f"Row {r:2d} |" + "".join(row_cells) + "|")
        print("       " + "---" * self.n)
        print(" Col   " + "".join([f"{c:3d}" for c in range(self.n)]))
        print()
