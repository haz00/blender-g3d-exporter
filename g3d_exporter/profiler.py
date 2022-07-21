# <pep8 compliant>
import logging
import time
from typing import Dict, Callable, List


class FunctionMetric(object):
    def __init__(self, name: str):
        self.name = name # function name
        self.total = 0 # ms
        self.calls = 0 # function calls count


metrics: Dict[Callable, FunctionMetric] = dict()


def profile(func):
    """delegate - measures the duration of a function call"""
    def timed(*args, **kwargs):
        start = time.process_time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.process_time() - start
            metric = metrics.get(func, None)
            if not metric:
                metric = FunctionMetric(f"{func.__module__}.{func.__qualname__}")
                metrics[func] = metric
            metric.total += duration
            metric.calls += 1

    if logging.root.level == logging.DEBUG:
        return timed
    return func

