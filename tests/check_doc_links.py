#!/usr/bin/env python
"""Every relative link in a living document resolves to a file in the tree.

    python tests/check_doc_links.py            report
    python tests/check_doc_links.py --strict   exit 1 on any broken link

Why this exists: on 14 September 2026 the documents moved twice in one day
(into the city and back out, then the city-specific half back under the city,
DECISIONS.md 9.170-9.171). Each move retargeted links by hand, and the tenth
project report found four position-page lines still naming the old tree. A
frozen document may carry a dead link (its banner says so); a living one may
not. The living set is the simulator's documents at `docs/` (the record
included: its links are retargeted mechanically when a file moves, never its
text), the root README, the conventions and the active city's own pages.
Anchors (`#...`), absolute URLs and links inside fenced code are not checked.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMG = re.compile(r"(?:src|srcset)=\"([^\"]+)\"")


def living(city_root: Path) -> list[Path]:
    out = [REPO / "README.md", REPO / ".claude" / "CLAUDE.md"]
    docs = REPO / "docs"
    out += sorted(docs.glob("*.md"))
    out += sorted((docs / "positions").glob("*.md"))
    out += [docs / "reports" / "README.md", docs / "reports" / "reference" / "README.md"]
    out += sorted((city_root / "docs").glob("*.md"))
    return [p for p in out if p.exists()]


def broken(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems = []
    fenced = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        targets = [m.group(1) for m in LINK.finditer(line)]
        targets += [m.group(1) for m in IMG.finditer(line)]
        for t in targets:
            if re.match(r"^[a-z][a-z0-9+.-]*:", t) or t.startswith("#") or t.startswith("<"):
                continue
            t = t.split("#", 1)[0]
            if not t:
                continue
            target = (path.parent / t).resolve()
            if not target.exists():
                problems.append(f"{path.relative_to(REPO).as_posix()}:{i}: {t} does not exist")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    import city as city_module  # noqa: PLC0415
    files = living(Path(city_module.CITY_DIR))
    problems = []
    for f in files:
        problems += broken(f)
    print(f"DOCUMENT LINKS - {len(files)} living document(s) checked")
    for p in problems:
        print("  " + p)
    print(f"TOTAL {len(problems)} broken link(s).")
    return 1 if (problems and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
