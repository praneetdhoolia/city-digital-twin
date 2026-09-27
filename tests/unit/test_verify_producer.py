"""`build_manifest.py --verify-producer`: a builder re-run after a refactor
must leave its manifest outputs byte-identical; a difference is reported and
the package restored. `--against-committed` compares HEAD's copy of the
builder with the working copy under one environment and restores both the
package and the script. Proved on a tiny fake producer in a temp repo."""
import os
import shutil
import subprocess

import pytest

import build_manifest as bm

SCRIPT = 'build/fake.py'
PRODUCER = '''import os
city = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'city', 'data')
os.makedirs(city, exist_ok=True)
tag = os.environ.get('FAKE_TAG', 'a')
open(os.path.join(city, 'one.csv'), 'w').write('x\\n1\\n')
open(os.path.join(city, 'two.csv'), 'w').write('y\\n%s\\n' % tag)
'''
ROWS = [dict(path='data/one.csv', produced_by=SCRIPT),
        dict(path='data/two.csv', produced_by='src/other.py + ' + SCRIPT),
        dict(path='data/three.csv', produced_by='src/other.py')]


def _repo(tmp_path, body=PRODUCER):
    repo = tmp_path / 'repo'
    (repo / 'build').mkdir(parents=True)
    (repo / 'build' / 'fake.py').write_text(body, encoding='utf-8')
    city = repo / 'city'
    (city / 'data').mkdir(parents=True)
    (city / 'data' / 'one.csv').write_text('x\n1\n', encoding='utf-8')
    (city / 'data' / 'two.csv').write_text('y\na\n', encoding='utf-8')
    return str(repo), str(city)


def _run(tmp_path, repo, city, **kw):
    return bm.verify_producer(SCRIPT, ROWS, city_root=city, repo_root=repo,
                              backup_dir=str(tmp_path / 'bk'), **kw)


def test_producer_rows_match_a_joined_entry_and_nothing_else():
    assert [r['path'] for r in bm.producer_rows(SCRIPT, ROWS)] == ['data/one.csv', 'data/two.csv']
    assert bm.producer_rows('src/build/build_matsim_network.py', [
        dict(path='n', produced_by='src/build/build_matsim_network.py (pt2matsim 26.6)')])


def test_an_identical_rebuild_passes(tmp_path):
    repo, city = _repo(tmp_path)
    res = _run(tmp_path, repo, city)
    assert res['identical'] and res['differing'] == [] and res['rc'] == 0


def test_a_differing_rebuild_is_reported_and_restored(tmp_path):
    repo, city = _repo(tmp_path)
    res = _run(tmp_path, repo, city, env={'FAKE_TAG': 'b'})
    assert not res['identical'] and res['differing'] == ['data/two.csv']
    with open(os.path.join(city, 'data', 'two.csv'), encoding='utf-8') as fh:
        assert fh.read() == 'y\na\n'                    # the package is back
    assert os.path.exists(os.path.join(str(tmp_path / 'bk'), 'new', 'data', 'two.csv'))


def test_a_failing_builder_restores(tmp_path):
    repo, city = _repo(tmp_path, body=PRODUCER + 'raise SystemExit(3)\n')
    os.remove(os.path.join(city, 'data', 'one.csv'))    # absent before: removed after
    res = _run(tmp_path, repo, city, env={'FAKE_TAG': 'b'})
    assert res['rc'] == 3 and not res['identical']
    assert not os.path.exists(os.path.join(city, 'data', 'one.csv'))
    with open(os.path.join(city, 'data', 'two.csv'), encoding='utf-8') as fh:
        assert fh.read() == 'y\na\n'


@pytest.mark.skipif(shutil.which('git') is None, reason='git not on PATH')
@pytest.mark.parametrize('working_tag_line, same', [
    ("tag = os.environ.get('FAKE_TAG', 'a')", True),
    ("tag = os.environ.get('FAKE_TAG', 'a') + '!'", False)])
def test_against_committed_compares_head_with_the_working_copy(tmp_path, working_tag_line, same):
    repo, city = _repo(tmp_path)
    git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false',
           '-c', 'core.hooksPath=' + str(tmp_path / 'no-hooks')]
    subprocess.check_call(['git', 'init', '-q'], cwd=repo)
    subprocess.check_call(git + ['add', 'build/fake.py'], cwd=repo)
    subprocess.check_call(git + ['commit', '-q', '-m', 'fake'], cwd=repo)
    working = PRODUCER.replace("tag = os.environ.get('FAKE_TAG', 'a')", working_tag_line)
    script = os.path.join(repo, 'build', 'fake.py')
    with open(script, 'w', encoding='utf-8') as fh:
        fh.write(working)
    res = _run(tmp_path, repo, city, env={'FAKE_TAG': 'z'}, against_committed=True)
    assert res['identical'] is same
    assert res['differing'] == ([] if same else ['data/two.csv'])
    with open(script, encoding='utf-8') as fh:
        assert fh.read() == working                      # the working copy is back
    with open(os.path.join(city, 'data', 'two.csv'), encoding='utf-8') as fh:
        assert fh.read() == 'y\na\n'                     # and so is the package
