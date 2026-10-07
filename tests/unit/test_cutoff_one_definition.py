"""One innovation cutoff, computed once (sixteenth report, 8 October 2026).

The jar truncates `first + f x (last - first)` to an int. The harness
(`run_matsim.jar_cutoff`), the viewer (`run_view.scan`) and the one-line
watcher (`watch_run.projection`) each computed it until the watcher was found
reading 83 where the jar read 200 on the F38 resume overlay (first 175, last
250, fraction 0.333334): `int(round(horizon x fraction))` ignores the first
iteration and rounds where the jar truncates. All three now call
`iteration_reading.innovation_off_after`.
"""
import iteration_reading
import run_matsim as rm
import watch_run


F38_RESUME = {'RUN.controler.first_iteration': 175,
              'RUN.controler.last_iteration': 250,
              'RUN.replanning.fraction_to_disable_innovation': 0.333334,
              'RUN.gate.wall_ceiling_h': 34}


def test_the_watcher_reads_the_jar_cutoff_on_a_resume():
    per = {i: 300.0 for i in range(176, 230)}
    out = watch_run.projection(per, F38_RESUME, {'started': '2026-09-28T04:21:07'},
                               now=1_800_000_000)
    assert out['cutoff'] == 200, 'the jar switches innovation off at 200, not 83'
    # the tail is the iterations PAST the cutoff, so its median rests on
    # 201-229 and not on everything after 83
    assert out['tail_median_s'] == 300.0


def test_the_watcher_on_a_cold_arm_reads_the_same_cutoff_as_the_jar():
    cfg = {'RUN.controler.last_iteration': 250,
           'RUN.replanning.fraction_to_disable_innovation': 0.8}
    out = watch_run.projection({}, cfg, {})
    assert out['cutoff'] == rm.jar_cutoff(0, 250, 0.8) == 200


def test_the_watcher_without_a_fraction_has_no_cutoff():
    out = watch_run.projection({}, {'RUN.controler.last_iteration': 250}, {})
    assert out['cutoff'] is None


def test_the_harness_delegates_to_the_one_definition():
    for first, last, f in ((175, 250, 0.333333), (175, 250, 0.333334),
                           (225, 250, 0.0), (0, 300, 0.8), (75, 250, 0.714286)):
        assert rm.jar_cutoff(first, last, f) == \
            iteration_reading.innovation_off_after(first, last, f)
    assert rm.jar_cutoff(175, 250, 0.333333) == 199
    assert rm.jar_cutoff(175, 250, 0.333334) == 200


def test_the_source_holds_no_second_cutoff_formula():
    """A grep, because the three copies were found by one: no reader may
    multiply a horizon by the innovation fraction on its own again."""
    import os
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, '..', '..'))
    own = re.compile(r'(horizon|last|target)\s*\*\s*(frac|fraction|f)\b')
    for rel in ('src/run/watch_run.py', 'src/run/run_matsim.py',
                'src/analyse/run_view.py'):
        with open(os.path.join(root, rel), encoding='utf-8') as fh:
            for n, line in enumerate(fh, 1):
                code = line.split('#', 1)[0]
                assert not own.search(code), '%s:%d computes its own cutoff' % (rel, n)
