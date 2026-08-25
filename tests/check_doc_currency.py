#!/usr/bin/env python
"""Find live-state numbers in the documentation that the artefacts no longer support.

    python tests/check_doc_currency.py            report
    python tests/check_doc_currency.py --strict   exit 1 if anything drifted
    python tests/check_doc_currency.py --json OUT machine-readable ledger

This repository already refuses a number decided in a script
(`src/registry/check_hardcoding.py`). This is the same refusal pointed at prose:
a number WRITTEN INTO A DOCUMENT is a claim about an artefact, and nothing was
checking that the claim still held.

It did not hold. On 25 August 2026 the front-door `README.md` advertised a 376-row
manifest against 489 on disk, a 210-field registry against 356, a road network of
43,112 edges against 50,182, and a warning that `networks/osm/` was empty and
`check_package` could not pass - nine days and three phases after the re-harvest
that filled it. `STATUS.md` carried the same 376 and a population that disagreed
with its own phase table by seven agents. Every one of those numbers was correct
when written. None was wrong in a way any reader could see.

**The distinction this check is built on: a DATED RECORD is frozen, a LIVE-STATE
CELL must track its artefact.** `DECISIONS.md` §14 saying "manifest 436" on
24 August is history and must never be rewritten. `README.md` saying "Files in the
manifest | 489" is a live claim and must equal the manifest. Only live claims are
declared here; the record is deliberately out of scope.

**The city owns its claims; this harness owns none.** Every path, pattern and
expected artefact lives in `cities/<city>/tests/doc_currency.json` - the same split
as `check_package.py` and its `package_expectations.json` (issue #62 B4). Nothing
in this file names a city, a document or a number.

Two claim kinds:

  number   a regex with ONE capture group, matched against a value DERIVED FROM
           AN ARTEFACT. The claim is the number in the document; the truth is
           measured, never declared twice. Integers by default; a claim that
           sets `decimals` compares to that many places, so a fit statistic
           written as "10.65 pp" is checkable rather than exempt.
  text     a regex with ONE capture group, matched against a STRING derived
           from an artefact. The number claims cannot see a stale NAME, and a
           figure captioned with the run it no longer draws is exactly as wrong
           as a stale count.

  absent   a regex that must NOT appear - for a statement that was true once and
           is now false in a way no number would catch ("the re-harvest has not
           been re-run"). Carries the reason it is banned.

A claim whose document or artefact is missing is SKIPPED, not failed, so this
runs in CI over the committed subset exactly as `check_manifest.py` does.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


# ---------------------------------------------------------------- truth resolvers
#
# Each resolver answers ONE question about the artefacts and returns an int, or
# raises Skip when the artefact it needs is not in this checkout. Resolvers never
# read a document: the whole point is that the truth comes from the artefact and
# the document is only ever compared against it.


class Skip(Exception):
    """The artefact this claim measures is not present in this checkout."""


def _manifest_rows(city_root: Path) -> list[dict]:
    path = city_root / "data" / "MANIFEST.csv"
    if not path.exists():
        raise Skip(f"{path.relative_to(REPO)} absent")
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def truth_manifest_files(city_root: Path, spec: dict) -> int:
    """How many files the manifest lists, optionally under one city-relative prefix.

    The prefix form exists so a phase's own delivery can be claimed without
    borrowing the whole-package total: P1 acquired the raw downloads, and saying
    so with a package-wide number is what made that line drift three phases later.
    """
    rows = _manifest_rows(city_root)
    prefix = spec.get("path_prefix")
    if prefix:
        rows = [r for r in rows if r["path"].startswith(prefix)]
    return len(rows)


def truth_manifest_artefact_rows(city_root: Path, spec: dict) -> int:
    """The row count the manifest records for ONE city-relative artefact path.

    Read from the manifest rather than from the artefact so the check works in CI,
    where the bulk data is gitignored but the manifest is committed. The manifest's
    own integrity is `check_manifest.py`'s job, not this one's.
    """
    want = spec["path"]
    for row in _manifest_rows(city_root):
        if row["path"] == want:
            if not row.get("rows"):
                raise Skip(f"manifest records no row count for {want}")
            return int(row["rows"])
    raise Skip(f"{want} not in the manifest")


def truth_registry_fields(city_root: Path, spec: dict) -> int:
    """How many fields the city declares across its registry files."""
    reg = city_root / "registry"
    if not reg.is_dir():
        raise Skip("registry/ absent")
    total = 0
    for path in sorted(reg.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        total += len(doc.get("fields", doc))
    return total


def truth_json_number(city_root: Path, spec: dict) -> float:
    """A number under a dotted key path in a committed JSON report.

    Returned unrounded: how many places the DOCUMENT states is the claim's
    business (`decimals`), not the artefact's.
    """
    path = city_root / spec["file"]
    if not path.exists():
        raise Skip(f"{spec['file']} absent")
    node = json.loads(path.read_text(encoding="utf-8"))
    for part in spec["key"].split("."):
        if not isinstance(node, dict) or part not in node:
            raise Skip(f"{spec['file']} has no key {spec['key']}")
        node = node[part]
    if not isinstance(node, (int, float)) or isinstance(node, bool):
        raise Skip(f"{spec['file']} key {spec['key']} is not a number")
    return node


def truth_csv_value_count(city_root: Path, spec: dict) -> int:
    """How many rows of a committed CSV carry one value in one column.

    The zone tiers are the motivating case: "1,500 core SA1" is a claim about
    `zone_tier == core`, and it should fail loudly if a boundary is ever redrawn.
    """
    path = city_root / spec["file"]
    if not path.exists():
        raise Skip(f"{spec['file']} absent")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or spec["column"] not in rows[0]:
        raise Skip(f"{spec['file']} has no column {spec['column']}")
    return sum(1 for r in rows if r[spec["column"]] == spec["value"])


def truth_json_text(city_root: Path, spec: dict) -> str:
    """A string under a dotted key path in a committed JSON report."""
    path = city_root / spec["file"]
    if not path.exists():
        raise Skip(f"{spec['file']} absent")
    node = json.loads(path.read_text(encoding="utf-8"))
    for part in spec["key"].split("."):
        if not isinstance(node, dict) or part not in node:
            raise Skip(f"{spec['file']} has no key {spec['key']}")
        node = node[part]
    if not isinstance(node, str):
        raise Skip(f"{spec['file']} key {spec['key']} is not a string")
    return node


def truth_path_count(city_root: Path, spec: dict) -> int:
    """How many paths match a city-relative glob (directories or files)."""
    matches = sorted(city_root.glob(spec["glob"]))
    if spec.get("dirs_only"):
        matches = [m for m in matches if m.is_dir()]
    if not matches and spec.get("skip_if_empty", True):
        raise Skip(f"nothing matches {spec['glob']}")
    return len(matches)


RESOLVERS = {
    "manifest_files": truth_manifest_files,
    "manifest_artefact_rows": truth_manifest_artefact_rows,
    "registry_fields": truth_registry_fields,
    "json_number": truth_json_number,
    "csv_value_count": truth_csv_value_count,
    "path_count": truth_path_count,
}

TEXT_RESOLVERS = {
    "json_text": truth_json_text,
}


# ------------------------------------------------------------------------ checking


def _as_number(raw: str) -> Decimal | None:
    """Parse a number as a document writes it: 489, 1,500, **50,182**, -91.8.

    The typographic minus (U+2212) is accepted alongside the hyphen: prose uses
    it, and a claim that silently failed to parse a negative would report
    UNPARSEABLE forever rather than checking anything.
    """
    cleaned = (raw.replace(",", "").replace("*", "")
               .replace("−", "-").strip())
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _expected(truth: float | int, claim: dict) -> Decimal:
    """The artefact's value at the precision the document states it to."""
    places = claim.get("decimals")
    value = Decimal(str(truth))
    if places is None:
        return value
    return value.quantize(Decimal(1).scaleb(-int(places)),
                          rounding=ROUND_HALF_UP)


def _show(value: Decimal) -> str:
    return f"{value:,}"


def check_number(doc_text: str, doc_name: str, claim: dict,
                 truth: float | int) -> list[dict]:
    """Every occurrence of the claim's pattern must carry the measured value."""
    expected = _expected(truth, claim)
    pattern = re.compile(claim["pattern"])
    found = list(pattern.finditer(doc_text))
    if not found:
        return [{
            "claim": claim["id"], "doc": doc_name, "kind": "PATTERN NOT FOUND",
            "detail": "the claim's pattern matches nothing - the document was "
                      "reworded and this claim needs re-aiming or retiring",
            "expected": _show(expected),
        }]
    problems = []
    for match in found:
        stated = _as_number(match.group(1))
        line = doc_text[: match.start()].count("\n") + 1
        if stated is None:
            problems.append({
                "claim": claim["id"], "doc": doc_name, "line": line,
                "kind": "UNPARSEABLE", "detail": repr(match.group(1)),
                "expected": _show(expected),
            })
        elif stated != expected:
            problems.append({
                "claim": claim["id"], "doc": doc_name, "line": line,
                "kind": "DRIFTED", "stated": _show(stated),
                "expected": _show(expected), "detail": claim.get("note", ""),
            })
    return problems


def check_text(doc_text: str, doc_name: str, claim: dict,
               truth: str) -> list[dict]:
    """Every occurrence of the claim's pattern must name the measured string."""
    pattern = re.compile(claim["pattern"])
    found = list(pattern.finditer(doc_text))
    if not found:
        return [{
            "claim": claim["id"], "doc": doc_name, "kind": "PATTERN NOT FOUND",
            "detail": "the claim's pattern matches nothing - the document was "
                      "reworded and this claim needs re-aiming or retiring",
            "expected": truth,
        }]
    problems = []
    for match in found:
        stated = match.group(1).strip()
        if stated != truth:
            problems.append({
                "claim": claim["id"], "doc": doc_name,
                "line": doc_text[: match.start()].count("\n") + 1,
                "kind": "DRIFTED", "stated": stated, "expected": truth,
                "detail": claim.get("note", ""),
            })
    return problems


def check_absent(doc_text: str, doc_name: str, claim: dict) -> list[dict]:
    """A statement banned because the artefacts made it false."""
    pattern = re.compile(claim["pattern"])
    problems = []
    for match in pattern.finditer(doc_text):
        line = doc_text[: match.start()].count("\n") + 1
        problems.append({
            "claim": claim["id"], "doc": doc_name, "line": line,
            "kind": "STALE STATEMENT", "detail": claim.get("reason", ""),
            "matched": match.group(0)[:120],
        })
    return problems


def run() -> tuple[list[dict], list[dict], int]:
    # `city` reads CITYSIM_CITY at import and exposes CITY_DIR - the framework's
    # one module that knows where a city lives. `--city` sets the variable before
    # this import, which is why the import is here rather than at module scope.
    import city as city_module  # noqa: PLC0415

    city_root = Path(city_module.CITY_DIR)
    spec_path = city_root / "tests" / "doc_currency.json"
    if not spec_path.exists():
        raise SystemExit(
            f"{spec_path.relative_to(REPO)} is missing.\n"
            "Every city declares its own live-state claims; this harness holds none."
        )
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    problems: list[dict] = []
    skipped: list[dict] = []
    checked = 0

    for claim in spec["claims"]:
        doc_path = REPO / claim["doc"]
        if not doc_path.exists():
            skipped.append({"claim": claim["id"], "why": f"{claim['doc']} absent"})
            continue
        doc_text = doc_path.read_text(encoding="utf-8")

        if claim["kind"] == "absent":
            checked += 1
            problems += check_absent(doc_text, claim["doc"], claim)
            continue

        if claim["kind"] == "text":
            resolver = TEXT_RESOLVERS.get(claim["truth"]["kind"])
            if resolver is None:
                raise SystemExit(
                    f"claim {claim['id']}: unknown text truth kind "
                    f"{claim['truth']['kind']!r}. Known: "
                    f"{', '.join(sorted(TEXT_RESOLVERS))}")
            try:
                truth_text = resolver(city_root, claim["truth"])
            except Skip as exc:
                skipped.append({"claim": claim["id"], "why": str(exc)})
                continue
            checked += 1
            problems += check_text(doc_text, claim["doc"], claim, truth_text)
            continue

        resolver = RESOLVERS.get(claim["truth"]["kind"])
        if resolver is None:
            raise SystemExit(
                f"claim {claim['id']}: unknown truth kind "
                f"{claim['truth']['kind']!r}. Known: {', '.join(sorted(RESOLVERS))}"
            )
        try:
            truth = resolver(city_root, claim["truth"])
        except Skip as exc:
            skipped.append({"claim": claim["id"], "why": str(exc)})
            continue
        checked += 1
        problems += check_number(doc_text, claim["doc"], claim, truth)

    return problems, skipped, checked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any claim drifted")
    ap.add_argument("--json", metavar="OUT", help="write the ledger as JSON")
    ap.add_argument("--city", default=None,
                    help="city key (default: CITYSIM_CITY, else the framework default)")
    args = ap.parse_args()

    import os
    if args.city:
        os.environ["CITYSIM_CITY"] = args.city

    problems, skipped, checked = run()

    print(f"DOCUMENT CURRENCY - {checked} live claim(s) checked against the artefacts")
    print()
    if problems:
        by_doc: dict[str, list[dict]] = {}
        for p in problems:
            by_doc.setdefault(p["doc"], []).append(p)
        for doc in sorted(by_doc):
            print(f"  {doc}")
            for p in by_doc[doc]:
                where = f":{p['line']}" if "line" in p else ""
                if p["kind"] == "DRIFTED":
                    print(f"    {doc}{where}  {p['claim']}")
                    print(f"        states {p['stated']}  artefact says "
                          f"{p['expected']}")
                else:
                    print(f"    {doc}{where}  {p['claim']}  [{p['kind']}]")
                if p.get("detail"):
                    print(f"        {p['detail']}")
            print()
    if skipped:
        print(f"  {len(skipped)} claim(s) SKIPPED - the artefact is not in this "
              f"checkout (expected in CI, not locally):")
        for s in skipped:
            print(f"    {s['claim']}: {s['why']}")
        print()

    print(f"TOTAL {len(problems)} drifted claim(s). "
          "A number in a document is a claim about an artefact.")

    if args.json:
        Path(args.json).write_text(
            json.dumps({"problems": problems, "skipped": skipped,
                        "checked": checked}, indent=2),
            encoding="utf-8",
        )

    return 1 if (problems and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
