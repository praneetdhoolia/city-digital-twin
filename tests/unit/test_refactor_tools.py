"""The two mechanical refactoring tools keep a module's behaviour.

src/setup/extract_loop_body.py moves a loop body (or a statement range) into a
module-level function behind a context object; src/setup/split_stages.py cuts
a long function into stages along line ranges. Both were written for the
twelfth report's maintainability findings (16 September 2026) and proved on
the plans and chains builders by rebuilding them byte-identically. This is
the cheap proof: a fixture module run before and after each tool gives the
same answer, and the transformed source still says what it said.
"""
import os
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TOOLS = os.path.join(REPO, 'src', 'setup')

FIXTURE = '''\
import collections

TOTAL = 0


def summarise(items, scale):
    counts = collections.Counter()
    biggest = None
    n_seen = 0
    # a comment about the loop
    for name, value in items:
        if value < 0:
            continue
        n_seen += 1
        counts[name] += value * scale
        label = 'big' if value > 5 else 'small'
        counts[label] += 1
        if biggest is None or value > biggest:
            biggest = value
    tail = dict(counts)
    tail['seen'] = n_seen
    tail['biggest'] = biggest
    return tail


def main():
    a = 3
    b = a * 2
    rows = [('x', 1), ('y', 7), ('z', -1), ('x', 9)]
    out = summarise(rows, b)
    out['a'] = a
    label = 'done'
    return out, label
'''

RUN = 'import json, fixture_mod; o, l = fixture_mod.main(); print(json.dumps([o, l], sort_keys=True))'


def _run(tmp_path):
    r = subprocess.run([sys.executable, '-c', RUN], cwd=tmp_path, capture_output=True,
                       text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture
def fixture_module(tmp_path):
    p = tmp_path / 'fixture_mod.py'
    p.write_text(FIXTURE, encoding='utf-8')
    return p


def test_extract_loop_body_keeps_the_answer(tmp_path, fixture_module):
    before = _run(tmp_path)
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'extract_loop_body.py'),
                        str(fixture_module), 'summarise', '11', 'summarise_one'],
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    src = fixture_module.read_text(encoding='utf-8')
    assert 'def summarise_one(name, value, ctx):' in src
    assert '# a comment about the loop' in src, 'comments travel with the body'
    assert "'big' if value > 5 else 'small'" in src, 'string literals are untouched'
    assert 'ctx.counts[' in src and 'ctx.n_seen += 1' in src
    assert 'return' in src.split('def summarise_one')[1].split('def summarise')[0], \
        'the loop\'s continue became a return'
    assert _run(tmp_path) == before


def test_extract_range_returns_what_it_produces(tmp_path, fixture_module):
    before = _run(tmp_path)
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'extract_loop_body.py'),
                        str(fixture_module), 'main', '27:28', 'prepare', '--ctx', 'pc'],
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    src = fixture_module.read_text(encoding='utf-8')
    assert 'def prepare(pc):' in src
    assert 'a, b = prepare(pc)' in src, src
    assert _run(tmp_path) == before


def test_split_stages_keeps_the_answer(tmp_path, fixture_module):
    before = _run(tmp_path)
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'split_stages.py'),
                        str(fixture_module), 'main', 'load_rows=29:29', 'finish=30:32'],
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    src = fixture_module.read_text(encoding='utf-8')
    assert 'def load_rows(' in src and 'def finish(' in src
    assert _run(tmp_path) == before


# The three defects met splitting the Mumbai builders (8 October 2026), each
# a NameError or UnboundLocalError in the split output: (a) `persons =
# sorted(persons, ...)` and `total += ...` read the name they bind; (b) the
# preamble's `from collections import OrderedDict` binds a name a stage
# reads; (c) the preamble's loop variable `r` and comprehension variable `c`
# re-appear as a lambda's argument and a comprehension's target in the
# stages, where they are the nested scope's and never the function's.
SCOPED = '''\
import collections


def main():
    from collections import OrderedDict
    rows = [('x', 1), ('y', 7), ('z', -1), ('x', 9)]
    total = 0
    for r in rows:
        total += r[1]
    labels = [c for c, _ in rows]
    persons = list(rows)
    # keep: the names worth keeping
    persons = sorted(persons, key=lambda r: -r[1])
    kept = OrderedDict()
    for s, v in persons:
        kept.setdefault(s, []).append(v)
    total += len(kept)
    # finish: the answer
    out = {c: sum(v) for c, v in kept.items()}
    out['order'] = sorted(kept, key=lambda s: s)
    out['first'] = persons[0]
    out['n'] = len(labels)
    out['total'] = total
    return out
'''

RUN_SCOPED = 'import json, scoped_mod; print(json.dumps(scoped_mod.main(), sort_keys=True))'


def test_split_stages_reads_names_in_evaluation_order_and_scope(tmp_path):
    p = tmp_path / 'scoped_mod.py'
    p.write_text(SCOPED, encoding='utf-8')

    def run():
        r = subprocess.run([sys.executable, '-c', RUN_SCOPED], cwd=tmp_path,
                           capture_output=True, text=True, encoding='utf-8')
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    before = run()
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'split_stages.py'),
                        str(p), 'main', 'keep=12:17', 'finish=18:23'],
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    src = p.read_text(encoding='utf-8')
    # (a) a name re-bound on the line that reads it is passed in and, read
    #     by the next stage, handed back; (b) the imported name is passed in;
    # (c) neither `r` nor `s` (lambda arguments) nor `c`, `v` (comprehension
    #     targets) is a parameter or a return
    assert 'def keep(OrderedDict, persons, total):' in src, src
    assert 'kept, persons, total = keep(OrderedDict, persons, total)' in src, src
    assert 'def finish(kept, labels, persons, total):' in src, src
    assert 'out = finish(kept, labels, persons, total)' in src, src
    assert run() == before
