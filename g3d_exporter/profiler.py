# <pep8 compliant>
import logging
import time
from typing import Dict, Callable, List


class FunctionMetric(object):
    def __init__(self, name: str):
        self.name = name
        self.duration = 0
        self.calls = 0


metrics: Dict[Callable, FunctionMetric] = dict()


def profile(func):
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
            metric.duration += duration
            metric.calls += 1

    if logging.root.level == logging.DEBUG:
        return timed
    return func

