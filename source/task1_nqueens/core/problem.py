"""
problem.py - N-Queens Problem Representation
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Represents the N-Queens problem formulation. Handles coordinate
    conversions for SAT solvers, checks validity of solutions,
    and displays the chessboard in ASCII format.
"""

import os
from typing import List, Tuple, Optional, Any


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

    def plot_board(
        self,
        queen_positions: List[int],
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        show: bool = False
    ) -> Optional[Any]:
        """
        Renders a publication-ready matplotlib graphical visualization of the N-Queens chessboard.
        Draws alternating wood/cream square colors, coordinates, and high-visibility Queen symbols (♛).
        """
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        if queen_positions is None or len(queen_positions) != self.n:
            print("No valid board to display.")
            return None

        fig_size = max(4.0, min(self.n * 0.6, 9.0))
        fig, ax = plt.subplots(figsize=(fig_size, fig_size))

        # Color scheme for chessboard squares
        color_light = "#F0D9B5"
        color_dark = "#B58863"
        queen_color = "#1A1A2E"
        font_size = max(9, int(180 / self.n))

        for r in range(self.n):
            for c in range(self.n):
                square_color = color_light if (r + c) % 2 == 0 else color_dark
                rect = patches.Rectangle(
                    (c, self.n - 1 - r), 1, 1,
                    facecolor=square_color,
                    edgecolor="#4A3728",
                    linewidth=0.5
                )
                ax.add_patch(rect)

        # Draw queen symbols
        for c in range(self.n):
            r = queen_positions[c]
            if 0 <= r < self.n:
                ax.text(
                    c + 0.5,
                    self.n - 1 - r + 0.5,
                    "♛",
                    fontsize=font_size,
                    ha="center",
                    va="center",
                    color=queen_color,
                    fontweight="bold"
                )

        ax.set_xlim(0, self.n)
        ax.set_ylim(0, self.n)
        ax.set_aspect("equal")

        # Board axis labels
        ax.set_xticks([c + 0.5 for c in range(self.n)])
        ax.set_xticklabels([str(c) for c in range(self.n)], fontsize=max(7, min(11, int(90 / self.n))))
        ax.set_yticks([self.n - 1 - r + 0.5 for r in range(self.n)])
        ax.set_yticklabels([str(r) for r in range(self.n)], fontsize=max(7, min(11, int(90 / self.n))))

        ax.set_xlabel("Column (Variable)", fontsize=10, fontweight="bold", labelpad=6)
        ax.set_ylabel("Row (Assigned Value)", fontsize=10, fontweight="bold", labelpad=6)

        board_title = title if title is not None else f"N-Queens Solution (N = {self.n})"
        ax.set_title(board_title, fontsize=11, fontweight="bold", pad=10)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"[Visual] Chessboard plot saved to: {os.path.abspath(save_path)}")

        if show:
            plt.show()

        return fig
