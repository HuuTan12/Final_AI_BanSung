try:
    from task1_nqueens.experiments.benchmark import BenchmarkRunner
except ImportError:
    from experiments.benchmark import BenchmarkRunner
__all__ = ['BenchmarkRunner']
