"""No tracked source holds a NUL byte (9.219).

`ServiceQualityScoring.java` was committed with two NUL characters where a
character literal should have held a space: javac accepted them, git showed
every diff of the file as binary, and the call they sat in never matched.
Nothing looked at the bytes. This does, for every tracked source and
document git would diff as text.
"""
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEXT = ('.py', '.java', '.json', '.md', '.sh', '.yml', '.yaml', '.xml', '.csv',
        '.txt', '.html', '.toml', '.cfg', '.ini')


def test_no_tracked_source_holds_a_nul_byte():
    files = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True,
                           capture_output=True).stdout.decode('utf-8').split('\0')
    bad = []
    for rel in files:
        if not rel.endswith(TEXT):
            continue
        path = os.path.join(ROOT, rel)
        if os.path.isfile(path):
            with open(path, 'rb') as fh:
                if b'\0' in fh.read():
                    bad.append(rel)
    assert not bad, 'NUL bytes in tracked text files: %s' % bad
