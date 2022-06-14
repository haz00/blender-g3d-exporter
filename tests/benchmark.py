import datetime

from g3d_exporter import builder, profiler
from g3d_exporter.builder import *
from tests.base import BaseTest
from tests.common import *


class Benchmark(BaseTest):
    def setUp(self):
        super().setUp()
        profiler.metrics.clear()

    def test_mesh(self):
        obj1 = add_triangle("obj1")

        subsurf = obj1.modifiers.new('SUBSURF', 'SUBSURF')
        subsurf.levels = 7

        opt = ModelOptions()
        opt.selected_only = True

        try:
            mod = builder.build(opt)
            json = encoder.encode_json(mod)
        finally:
            dump_metrics()


def dump_metrics():
    out_dir = Path(__file__).parent / f"build/{bpy.app.version_string}/benchmark"
    out_dir.mkdir(exist_ok=True, parents=True)

    filename = out_dir / f"{datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.txt"

    with open(filename, 'w') as f:
        metrics = sorted(profiler.metrics.values(), key=lambda m: m.total, reverse=True)
        max_metric = max(metrics, key=lambda m: m.total)

        f.write("{:<80} {:>10} {:>10} {:>10} {:>10}\n"
                .format("FUNCTION", "CALLS", "TOTAL(ms)", "AVG(ms)", "TOTAL %"))

        for m in metrics:
            avg = m.total / float(m.calls) * 1000
            prc = m.total / max_metric.total * 100
            f.write("{:<80} {:>10} {:>10.3f} {:>10.3f} {:>10.3f}\n"
                    .format(m.name, m.calls, m.total * 1000, avg, prc))
        log.debug("dump benchmark to %s", filename)
