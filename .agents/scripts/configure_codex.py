"""Enable nested project instructions without adding a root-level AGENTS.md.

Run from any directory. Skills themselves use Codex's native .agents/skills
discovery. This changes only the additional project instruction filename.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tomllib
from datetime import datetime, timezone


FALLBACK = ".agents/AGENTS.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing")
    parser.add_argument("--config", type=Path, help="Override the user config path")
    args = parser.parse_args()
    codex_dir = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    path = args.config or codex_dir / "config.toml"
    original = path.read_bytes() if path.exists() else b""
    text = original.decode("utf-8-sig")
    before = tomllib.loads(text)
    names = before.get("project_doc_fallback_filenames", [])
    if FALLBACK in names:
        print("PASS: Codex loads .agents/AGENTS.md through its native fallback setting")
        return 0
    if args.check:
        print("NOT CONFIGURED: run python .agents/scripts/configure_codex.py")
        return 1
    assignment = "project_doc_fallback_filenames = " + json.dumps([*names, FALLBACK])
    if "project_doc_fallback_filenames" in before:
        pattern = r"(?m)^project_doc_fallback_filenames\s*=\s*\[[\s\S]*?\]"
        updated, count = re.subn(pattern, lambda _: assignment, text, count=1)
        if count != 1:
            raise SystemExit("Cannot safely locate the existing fallback setting")
    else:
        updated = assignment + "\n\n" + text
    expected = dict(before, project_doc_fallback_filenames=[*names, FALLBACK])
    if tomllib.loads(updated) != expected:
        raise SystemExit("Refusing to change unrelated Codex configuration")
    path.parent.mkdir(parents=True, exist_ok=True)
    if original:
        backups = path.parent / "backups"
        backups.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        (backups / f"{path.name}.{stamp}.bak").write_bytes(original)
    path.write_text(updated, encoding="utf-8", newline="\n")
    print("Configured native instruction discovery; existing settings preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
