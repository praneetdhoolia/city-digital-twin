"""The Bash PreToolUse hook refuses a heredoc and a bare `python -`, and only those.

`.claude/hooks/block-stdin-trap.sh` reads the harness's JSON payload on stdin
and exits 2 to refuse. It is fed synthetic payloads here, in the JSON encoding
the harness uses (a newline is `\\n`, a double quote `\\"`).
"""
import json
import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, '..', '..', '.claude', 'hooks', 'block-stdin-trap.sh')
SETTINGS = os.path.join(HERE, '..', '..', '.claude', 'settings.json')
BASH = shutil.which('bash')


def _rc(command):
    payload = json.dumps(dict(tool_name='Bash', tool_input=dict(command=command)))
    return subprocess.run([BASH, HOOK], input=payload, capture_output=True,
                          text=True).returncode


@pytest.mark.skipif(BASH is None, reason='bash not on PATH')
@pytest.mark.parametrize('command', [
    'cat <<EOF\nhi\nEOF',
    "cat <<'EOF'\nhi\nEOF",
    'cat <<"EOF"\nhi\nEOF',
    'cat <<-EOF\n\thi\nEOF',
    'python - < script.py',
    'echo "print(1)" | python3 -',
    'python -',
])
def test_the_stdin_shapes_are_refused(command):
    assert _rc(command) == 2


@pytest.mark.skipif(BASH is None, reason='bash not on PATH')
@pytest.mark.parametrize('command', [
    'python -m pytest -q tests/unit',
    'python -c "print(1 << 20)"',
    'python run.py --stop x',
    'python tests/check_manifest.py --all-cities < /dev/null',
    'git log --oneline -3',
])
def test_everything_else_passes(command):
    assert _rc(command) == 0


def test_the_hook_is_registered_on_the_bash_tool():
    with open(SETTINGS, encoding='utf-8') as fh:
        pre = json.load(fh)['hooks']['PreToolUse']
    bash = [h['command'] for m in pre if m.get('matcher') == 'Bash' for h in m['hooks']]
    assert any('block-stdin-trap.sh' in c for c in bash)
