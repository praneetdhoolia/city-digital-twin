"""Codex entry point for the project report's `collect_performance.py`.

The script lives ONCE, at .claude/skills/project-report/scripts/collect_performance.py; this
shim runs it with the same arguments, so the Codex and Claude reports cannot
diverge (they did: four copies drifted by hand between 18 and 25 September
2026). tests/unit/test_report_collectors.py holds the two directories together.

    python .agents/skills/project-report/scripts/collect_performance.py ...
"""
import os
import runpy
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..',
                    '.claude', 'skills', 'project-report', 'scripts', 'collect_performance.py')
_SRC = os.path.normpath(_SRC)
sys.argv[0] = _SRC
sys.path.insert(0, os.path.dirname(_SRC))
runpy.run_path(_SRC, run_name='__main__')
