"""The report's collectors read what the repository holds, not the branch they run on.

- `collect_metrics.py` lists commits that landed on main directly. It walked
  the CURRENT branch's first-parent chain, so a session branch's own unmerged
  commits were reported as direct commits to main (the fifteenth report). It
  now walks `origin/main` from the local ref. The fixture is a throwaway git
  repository: a direct commit and a merged PR on main, then a session branch
  with two commits of its own.
- `collect_performance.py` typed "none recorded" for the build's cost while
  each city's `_build_timing.json` held it; it now reads the roll-up.
- The Codex copies under `.agents/skills/project-report/scripts/` are thin
  shims onto the `.claude/` scripts, so the two cannot diverge again.

No data package and no network: the fixtures are built here.
"""
import importlib.util
import json
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SCRIPTS = os.path.join(REPO, '.claude', 'skills', 'project-report', 'scripts')
AGENTS_SCRIPTS = os.path.join(REPO, '.agents', 'skills', 'project-report', 'scripts')


def _load(name):
    spec = importlib.util.spec_from_file_location(
        'report_' + name, os.path.join(SCRIPTS, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.org',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.org',
               GIT_CONFIG_NOSYSTEM='1')
    return subprocess.run(['git', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
                           *args], cwd=cwd, env=env, check=True,
                          capture_output=True, text=True).stdout


def _commit(cwd, name):
    with open(os.path.join(cwd, name), 'w', encoding='utf-8') as f:
        f.write(name)
    _git(cwd, 'add', name)
    _git(cwd, 'commit', '-q', '-m', 'P1: ' + name)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """main: root, a direct commit, a merged PR. Then a session branch with
    two unmerged commits, checked out, and origin/main at main's tip."""
    r = str(tmp_path)
    _git(r, 'init', '-q', '-b', 'main')
    _commit(r, 'root.txt')
    _commit(r, 'direct_on_main.txt')
    _git(r, 'checkout', '-q', '-b', 'feature')
    _commit(r, 'feature.txt')
    _git(r, 'checkout', '-q', 'main')
    _git(r, 'merge', '-q', '--no-ff', 'feature', '-m', 'Merge pull request #1 from x/feature')
    _git(r, 'update-ref', 'refs/remotes/origin/main', 'main')
    _git(r, 'checkout', '-q', '-b', 'session')
    _commit(r, 'session_one.txt')
    _commit(r, 'session_two.txt')
    monkeypatch.chdir(r)
    return r


def test_direct_commits_are_main_s_not_the_session_branch_s(repo):
    cm = _load('collect_metrics')
    log = cm.commit_log(None)
    subjects = [d['subject'] for d in log['direct_to_default_branch']]
    assert log['default_branch_ref'] == 'origin/main'
    assert 'P1: direct_on_main.txt' in subjects
    assert not any('session' in s for s in subjects)
    assert not any(s.startswith('Merge') for s in subjects)


def test_the_timeline_does_not_carry_the_session_branch(repo):
    cm = _load('collect_metrics')
    events = cm.timeline(__import__('pathlib').Path(repo), {})['events']
    titles = [e['title'] for e in events]
    assert any(e['kind'] == 'pr' for e in events)
    assert not any('session' in t for t in titles)


def test_without_origin_main_the_local_main_is_walked(repo):
    _git(repo, 'update-ref', '-d', 'refs/remotes/origin/main')
    cm = _load('collect_metrics')
    assert cm.default_ref() == 'main'


def test_build_timing_is_read_from_each_city_s_rollup(tmp_path):
    cp = _load('collect_performance')
    data = tmp_path / 'cities' / 'somecity' / 'data'
    data.mkdir(parents=True)
    (data / '_build_timing.json').write_text(json.dumps(dict(
        builders={'src/build/a.py': dict(seconds=10.5, status='ok', recorded='2026-09-01T00:00:00'),
                  'src/build/b.py': dict(seconds=2.0, status='failed', recorded='2026-09-02T00:00:00')},
        total_seconds=12.5)), encoding='utf-8')
    (data / 'MANIFEST.csv').write_text(
        'path,produced_by\nx.csv,src/build/a.py\ny.csv,src/build/c.py\nz.csv,manual\n',
        encoding='utf-8')
    out = cp.build_timing(tmp_path)['somecity']
    assert out['total_seconds'] == 12.5
    assert out['builders_timed'] == 2
    assert out['slowest'][0]['builder'] == 'src/build/a.py'
    assert out['failed'] == ['src/build/b.py']
    assert out['manifest_producers_untimed'] == ['src/build/c.py']


def test_no_rollup_says_so_rather_than_inventing_a_figure(tmp_path):
    cp = _load('collect_performance')
    assert 'none' in cp.build_timing(tmp_path)


def test_the_codex_copies_are_shims_onto_the_claude_scripts():
    """One source of truth: every .claude report script has a .agents twin,
    and the twin runs the .claude script rather than carrying a copy."""
    if not os.path.isdir(AGENTS_SCRIPTS):
        pytest.skip('no .agents copy in this checkout')
    ours = sorted(f for f in os.listdir(SCRIPTS) if f.endswith('.py'))
    theirs = sorted(f for f in os.listdir(AGENTS_SCRIPTS) if f.endswith('.py'))
    assert theirs == ours
    for name in ours:
        with open(os.path.join(AGENTS_SCRIPTS, name), encoding='utf-8') as f:
            text = f.read()
        assert "'.claude', 'skills', 'project-report', 'scripts'" in text, name
        assert 'runpy.run_path' in text, name
        assert len(text.splitlines()) < 40, name + ' carries more than a shim'
