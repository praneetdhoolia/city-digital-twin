"""Every GitHub Action reference is pinned to a commit SHA.

A repository that hashes 201 jars individually in `.tools/toolchain.json` and
refuses a toolchain change without re-hashing it (`.claude/CLAUDE.md`, "the
toolchain is pinned, and a toolchain change is a model change") ran its own CI
on mutable major tags. `actions/checkout@v4` resolves to whatever the tag points
at on the day the workflow runs, and two of these workflows hold
`pages: write` and `id-token: write`.

The rule is the one the toolchain already lives under, applied to the other
half of the supply chain: a version that can move under the project without the
project re-hashing it is not pinned.

Local actions (`./.github/actions/...`) and reusable workflows in this
repository are exempt: they move only when this repository moves them.
"""

from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / '.github' / 'workflows'

# `uses: owner/repo@ref` or `uses: owner/repo/path@ref`, with the ref captured.
USES = re.compile(r'^\s*(?:-\s*)?uses:\s*(?P<ref>\S+)')
SHA40 = re.compile(r'^[0-9a-f]{40}$')


def _references():
    """Every third-party `uses:` in the workflow tree, as (file, line, ref)."""
    for path in sorted(WORKFLOWS.glob('*.yml')) + sorted(WORKFLOWS.glob('*.yaml')):
        for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            m = USES.match(line)
            if not m:
                continue
            ref = m.group('ref')
            if ref.startswith('./') or ref.startswith('.github/'):
                continue          # local to this repository
            yield path, n, ref


def test_there_are_workflows_to_check():
    """A test that silently checks nothing is the failure it exists to catch."""
    assert list(_references()), 'no `uses:` found under .github/workflows'


def test_every_action_is_pinned_to_a_sha():
    unpinned = []
    for path, n, ref in _references():
        if '@' not in ref:
            unpinned.append('%s:%d  %s (no ref at all)' % (path.name, n, ref))
            continue
        version = ref.rsplit('@', 1)[1]
        if not SHA40.match(version):
            unpinned.append('%s:%d  %s' % (path.name, n, ref))
    assert not unpinned, (
        'GitHub Actions must be pinned to a 40-character commit SHA, not a '
        'mutable tag or branch. Resolve one with\n'
        "    gh api repos/<owner>/<repo>/git/ref/tags/<tag> --jq .object.sha\n"
        'and keep the human-readable version in a trailing comment:\n'
        '    uses: actions/checkout@11d5960...  # v4\n\n' + '\n'.join(unpinned))


def test_each_pin_carries_a_version_comment():
    """A bare SHA says nothing about what it is; the comment is how a reader
    knows which version to compare against when it is time to bump."""
    bare = []
    for path, n, ref in _references():
        line = path.read_text(encoding='utf-8').splitlines()[n - 1]
        if '#' not in line.split('uses:', 1)[1]:
            bare.append('%s:%d  %s' % (path.name, n, ref))
    assert not bare, (
        'a pinned action carries its version in a trailing comment so the pin '
        'can be read and bumped:\n' + '\n'.join(bare))
