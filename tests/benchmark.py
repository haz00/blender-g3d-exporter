import datetime

from g3d_exporter import builder, profiler
from g3d_exporter.builder import *
from tests.base import BaseTest
from tests.common import *


class Benchmark(BaseTest):
    def test_mesh(self):
        obj1 = add_triangle("obj1")

        subsurf = obj1.modifiers.new('SUBSURF', 'SUBSURF')
        subsurf.levels = 7

        opt = ModelOptions()
        opt.selected_only = True

        try:
            builder.build(opt)
        finally:
            dump_metrics()


def dump_metrics():
    out_dir = Path(__file__).parent / f"build/{bpy.app.version_string}/benchmark"
    out_dir.mkdir(exist_ok=True, parents=True)

    filename = out_dir / f"{datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.txt"

    metrics = sorted(profiler.metrics.values(), key=lambda m: m.duration, reverse=True)

    with open(filename, 'w') as f:
        f.write("{:<100} {:>6} {:>7} {:>6}\n".format("FUNCTION", "CALLS", "SUM(ms)", "AV(ms)"))
        for m in metrics:
            f.write("{:<100} {:>6} {:>7.0f} {:>6.2f}\n".format(m.name,
                                                             m.calls,
                                                             m.duration * 1000, (m.duration / float(m.calls)) * 1000))
        log.debug("dump metrics to %s", filename)
