"""
ui - Graphical and Notebook Visualizers for N-Queens
Course: Introduction to Artificial Intelligence (503043)
"""

from task1_nqueens.ui.pygame_nqueens import NQueensGUI, PYGAME_AVAILABLE
from task1_nqueens.ui.notebook_visualizer import visualize_board, plot_solution_gallery

__all__ = [
    "NQueensGUI",
    "PYGAME_AVAILABLE",
    "visualize_board",
    "plot_solution_gallery",
]
