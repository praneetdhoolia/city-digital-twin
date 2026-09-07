#!/usr/bin/env python
"""Keep the living documents the SHAPE they were designed to be.

    python tests/check_doc_shape.py            report
    python tests/check_doc_shape.py --strict   exit 1 if anything is out of shape

`check_doc_currency.py` pins the numbers a document states to the artefacts.
This is its companion for the thing no number can catch: a board that grows
back into a diary, a brief patched across five family boundaries instead of
rewritten, a record whose sections arrive out of order, a position page with a
figure nobody can trace, a frozen document read as current. Each rule here was
breached at least once; the board reached 801 lines under a line-9 rule that
said "not a diary", and one brief named F15, F16, F17, F18 and F20 as the
running family in different sections.

The rules are CITY-OWNED (`cities/<city>/tests/doc_shape.json`); this harness
names no city, no document and no number. A document that is absent is
skipped, so the check runs in CI over the committed subset.

Checks:

  board      hand-written lines (outside the generated blocks) under a cap;
             only the allowed `## ` headings; every required generated block
             present; no line longer than the cap (a 3,000-character header
             cell is a paragraph, not a cell).
  brief      under a line cap; the required section headings present; the
             family stamp equals the newest family in the ledger.
  record     every `## 9.x` section numbered above `frozen_through` is in
             ascending order after the frozen ones, under a line cap, and
             referenced from the topical index.
  positions  each page under a cap with the required headings; every line
             carrying a decimal, a percentage or a thousands separator also
             carries a reference (`§`, `#NN` or a backticked path); every
             family key in the ledger appears on the families page.
  archives   every file under the archive directories that is not on the
             live list carries a frozen/archive banner in its first lines.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

NUMBER = re.compile(r"(?<![\w/.-])\d{1,3}(,\d{3})+(?![\w-])|\d+\.\d+|\d+(\.\d+)?\s?%")
GENERATED = re.compile(r"<!-- generated:(\w+) start -->.*?<!-- generated:\1 end -->", re.S)


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def check_board(city: Path, spec: dict) -> list[str]:
    path = city / spec["path"]
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    problems = []
    present = set(GENERATED.findall(text))
    for name in spec.get("required_blocks", []):
        if name not in present:
            problems.append(f"{spec['path']}: generated block '{name}' is missing "
                            f"(add the <!-- generated:{name} start/end --> markers)")
    hand = GENERATED.sub("", text).splitlines()
    n_hand = sum(1 for l in hand if l.strip())
    cap = spec["max_hand_lines"]
    if n_hand > cap:
        problems.append(f"{spec['path']}: {n_hand} hand-written lines against a cap of "
                        f"{cap} - the board is becoming a diary; move narrative to "
                        f"DECISIONS.md or SESSION_LOG.md")
    allowed = set(spec.get("allowed_h2", []))
    # a scoreboard row whose gate says the number is not a fit must not
    # carry one (#114): `level only` and `representation` rows show `-`
    no_dev = tuple(spec.get("no_deviation_flags", []))
    in_block = False
    block = None
    for i, l in enumerate(text.splitlines(), 1):
        if l.startswith("<!-- generated:") and l.endswith("start -->"):
            in_block = True
            block = l[len("<!-- generated:"):-len(" start -->")].strip()
        elif l.startswith("<!-- generated:") and l.endswith("end -->"):
            in_block = False
            block = None
            continue
        if in_block and block == "scoreboard" and no_dev and l.startswith("| "):
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cells) >= 6 and cells[5].startswith(no_dev) and cells[4] != "-":
                problems.append(f"{spec['path']}:{i}: scoreboard row '{cells[1]}' is "
                                f"'{cells[5]}' yet carries a deviation '{cells[4]}' - "
                                f"a percentage against a non-target basis (#114)")
        if l.startswith("## "):
            title = l[3:].strip()
            if allowed and title not in allowed:
                problems.append(f"{spec['path']}:{i}: heading '## {title}' is not one the "
                                f"board allows ({', '.join(sorted(allowed))})")
        if not in_block and len(l) > spec.get("max_line_chars", 10 ** 9):
            problems.append(f"{spec['path']}:{i}: a {len(l)}-character line - a "
                            f"paragraph in a table cell")
    return problems


def check_brief(city: Path, spec: dict, latest_family: str | None) -> list[str]:
    path = city / spec["path"]
    if not path.exists():
        return []
    lines = _lines(path)
    problems = []
    if len(lines) > spec["max_lines"]:
        problems.append(f"{spec['path']}: {len(lines)} lines against a cap of "
                        f"{spec['max_lines']} - rewrite from the template, do not patch")
    text = "\n".join(lines)
    for h in spec.get("required_headings", []):
        if not re.search(r"^#+\s*" + re.escape(h), text, re.M):
            problems.append(f"{spec['path']}: required heading '{h}' is missing")
    m = re.search(spec["family_stamp"], text)
    if not m:
        problems.append(f"{spec['path']}: no family stamp matching {spec['family_stamp']!r}")
    elif latest_family and m.group(1) != latest_family:
        problems.append(f"{spec['path']}: stamped for family '{m.group(1)}' but the "
                        f"ledger's newest family is '{latest_family}' - the brief was "
                        f"not rewritten for the family it describes")
    return problems


def check_record(city: Path, spec: dict) -> list[str]:
    path = city / spec["path"]
    if not path.exists():
        return []
    lines = _lines(path)
    pat = re.compile(spec["section_pattern"])
    frozen = int(spec["frozen_through"])
    heads = [(i, int(pat.match(l).group(1))) for i, l in enumerate(lines) if pat.match(l)]
    problems = []
    if not heads:
        return problems
    last_frozen_line = max((i for i, n in heads if n <= frozen), default=-1)
    new = [(i, n) for i, n in heads if n > frozen]
    prev = frozen
    for k, (i, n) in enumerate(new):
        if i < last_frozen_line:
            problems.append(f"{spec['path']}:{i + 1}: §9.{n} sits before a frozen section "
                            f"- new sections are appended after §9.{frozen}")
        if n <= prev:
            problems.append(f"{spec['path']}:{i + 1}: §9.{n} follows §9.{prev} - sections "
                            f"above §9.{frozen} must be in ascending order")
        prev = n
        end = new[k + 1][0] if k + 1 < len(new) else next(
            (j for j in range(i + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
        length = end - i
        if length > spec["max_new_section_lines"]:
            problems.append(f"{spec['path']}:{i + 1}: §9.{n} is {length} lines against a "
                            f"cap of {spec['max_new_section_lines']} - what changed, what "
                            f"was measured, what is deliberately not done, consequences; "
                            f"narrative goes to SESSION_LOG.md")
        ref = re.compile(spec["index_reference"].replace("{n}", str(n)))
        index_end = heads[0][0]
        if not any(ref.search(l) for l in lines[:index_end]):
            problems.append(f"{spec['path']}: §9.{n} has no row in the topical index")
    return problems


def check_positions(city: Path, spec: dict, family_keys: list[str]) -> list[str]:
    d = city / spec["dir"]
    if not d.is_dir():
        return []
    problems = []
    ref = re.compile(spec.get("reference_pattern", "§"))
    for page in sorted(d.glob("*.md")):
        rel = page.relative_to(city).as_posix()
        lines = _lines(page)
        if len(lines) > spec["max_lines"]:
            problems.append(f"{rel}: {len(lines)} lines against a cap of {spec['max_lines']}")
        text = "\n".join(lines)
        for h in spec.get("required_headings", []):
            if h not in text:
                problems.append(f"{rel}: required heading '{h}' is missing")
        if spec.get("numbers_need_reference"):
            for i, l in enumerate(lines, 1):
                if l.startswith("#") or l.startswith("*A position page"):
                    continue
                if NUMBER.search(l) and not ref.search(l):
                    problems.append(f"{rel}:{i}: a figure with no source on its line - "
                                    f"add the §, the issue or the path it comes from")
        # THE STAMP NAMES THE FAMILY THE PAGE WAS WRITTEN AGAINST, and the
        # ledger has to know it. The stamp used to read "Open family", a LIVE
        # fact with its home on the board; seven of thirteen pages were two or
        # three boundaries out of date before anything looked, because the
        # brief was the only document whose stamp was checked.
        stamp_re = spec.get("family_stamp")
        if stamp_re:
            m = re.search(stamp_re, text)
            if not m:
                problems.append(f"{rel}: no family stamp matching {stamp_re!r} - a "
                                f"position page states the family it was written against")
            else:
                stamp = m.group(1)
                if not any(stamp == k or k.startswith(stamp + "-") for k in family_keys):
                    problems.append(f"{rel}: family stamp '{stamp}' names no family in "
                                    f"the ledger")
        if page.name == spec.get("families_page"):
            for key in family_keys:
                if key not in text:
                    problems.append(f"{rel}: family '{key}' from the ledger is not on the "
                                    f"families page")
    return problems


def check_archives(city: Path, spec: dict) -> list[str]:
    problems = []
    live = set(spec.get("live", []))
    banner = re.compile(spec["banner_pattern"])
    for d in spec.get("dirs", []):
        base = city / d
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in (".md", ".html"):
                continue
            rel = f.relative_to(city).as_posix()
            if rel in live or rel.startswith("docs/positions/"):
                continue
            head = "\n".join(_lines(f)[: spec.get("within_lines", 12)])
            if not banner.search(head):
                problems.append(f"{rel}: no ARCHIVE/FROZEN banner in its first "
                                f"{spec.get('within_lines', 12)} lines - a dated document "
                                f"either says it is frozen or is on the live list")
    return problems


def run() -> tuple[list[str], int]:
    import city as city_module  # noqa: PLC0415
    city = Path(city_module.CITY_DIR)
    spec_path = city / "tests" / "doc_shape.json"
    if not spec_path.exists():
        raise SystemExit(f"{spec_path.relative_to(REPO)} is missing.")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    family_keys: list[str] = []
    latest = None
    fam_path = city / spec.get("families", {}).get("path", "docs/run_families.json")
    if fam_path.exists():
        doc = json.loads(fam_path.read_text(encoding="utf-8"))
        fams = sorted(doc["families"].items(), key=lambda kv: kv[1]["from_launch"])
        family_keys = [k for k, _ in fams]
        latest = family_keys[-1] if family_keys else None

    problems: list[str] = []
    checks = 0
    for name, fn, args in (
        ("board", check_board, (city, spec["board"])),
        ("brief", check_brief, (city, spec["brief"], latest)),
        ("record", check_record, (city, spec["record"])),
        ("positions", check_positions, (city, spec["positions"], family_keys)),
        ("archives", check_archives, (city, spec["archives"])),
    ):
        if name in spec:
            checks += 1
            problems += fn(*args)
    return problems, checks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 on any problem")
    ap.add_argument("--city", default=None)
    args = ap.parse_args()
    import os
    if args.city:
        os.environ["CITYSIM_CITY"] = args.city
    problems, checks = run()
    print(f"DOCUMENT SHAPE - {checks} document class(es) checked")
    for p in problems:
        print("  " + p)
    print(f"TOTAL {len(problems)} shape problem(s).")
    return 1 if (problems and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
