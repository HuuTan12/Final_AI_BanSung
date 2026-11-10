"""
core - Propositional Logic Formulation and N-Queens Problem Model
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Provides problem representation for N-Queens and automated generation
    of DIMACS CNF propositional logic constraints (Row ALO/AMO, Col ALO/AMO, Diagonal AMO).
"""

from task1_nqueens.core.problem import NQueensProblem
from task1_nqueens.core.constraints import ConstraintGenerator

__all__ = ["NQueensProblem", "ConstraintGenerator"]
