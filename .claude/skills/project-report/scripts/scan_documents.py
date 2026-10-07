#!/usr/bin/env python3
"""The document scans Phase 5 of /project-report used to re-derive in scratch.

    python .claude/skills/project-report/scripts/scan_documents.py <scratch>/reviews

Writes `<out>/scan_documents.json` and prints a summary. Five scans, the same
every pass, each of which the sixteenth pass (and the three before it) wrote
again as a scratch script the repository did not hold:

  banners        every tracked *.md under an archived/ directory carries a
                 frozen/archive banner in its first 1,500 bytes; living files
                 that behave as archives (over `LONG_LIVING_LINES`, no banner,
                 not a position page) are listed
  record         DECISIONS.md section numbering (monotonic, non-monotonic pairs
                 inside the frozen block named), every section in the topical
                 index, the §14 change log newest-first, sections over the cap
                 since `RECORD_WATCH_FROM`
  links          an own relative-link pass over EVERY tracked *.md (archived
                 included; tests/check_doc_links.py covers the living set)
  shared_figures the figures the board's generated blocks own (the result run,
                 N of 12, registry and manifest counts, the licence split, the
                 wall hours) restated in any living document, file:line each
  budgets        the reading budget of docs/HANDOVER_CONTRACT.md against wc -l
                 of each layer, and the divergence of .agents/ from .claude/

Reads the repository only; writes nothing inside it. Every threshold is a
named constant at the top; quote it in the report.
"""
from __future__ import annotations

import filecmp
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SRC = REPO / "src" / "analyse"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(REPO / "src"))

BANNER = re.compile(r"frozen|archived|superseded|historical", re.I)
BANNER_BYTES = 1500
LONG_LIVING_LINES = 400          # a living document this long with no banner behaves as an archive
RECORD_WATCH_FROM = 200          # sections numbered from here are checked against the cap
RECORD_SECTION_CAP = 140
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BUDGET_ROW = re.compile(r"^\| (\w[\w ]*) \| `([^`]+)` \| ([^|]+) \|", re.M)


def tracked(suffix: str = ".md") -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=REPO).stdout.splitlines()
    return [p for p in out if p.lower().endswith(suffix)]


def read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8", errors="replace")


def scan_banners(md: list[str]) -> dict:
    archived = [p for p in md if "/archived/" in p]
    unbannered = [p for p in archived if not BANNER.search(read(p)[:BANNER_BYTES])]
    long_living = []
    for p in md:
        if "/archived/" in p or p.startswith("docs/positions/") or p == "docs/DECISIONS.md":
            continue
        text = read(p)
        if text.count("\n") > LONG_LIVING_LINES and not BANNER.search(text[:BANNER_BYTES]):
            long_living.append({"file": p, "lines": text.count("\n")})
    return {"archived": len(archived), "unbannered": unbannered,
            "living_over_%d_lines_without_banner" % LONG_LIVING_LINES: long_living}


def scan_record(path: str = "docs/DECISIONS.md") -> dict:
    lines = read(path).splitlines()
    heads = [(i + 1, int(m.group(1))) for i, l in enumerate(lines)
             if (m := re.match(r"^## 9\.(\d+) ", l))]
    nums = [n for _, n in heads]
    non_mono = [{"before": "9.%d:%d" % (heads[i][1], heads[i][0]), "after": "9.%d:%d" % (heads[i + 1][1], heads[i + 1][0])}
                for i in range(len(nums) - 1) if nums[i + 1] <= nums[i]]
    idx_start = next((i for i, l in enumerate(lines) if l.startswith("## How to find")), 0)
    idx_end = next((i for i, l in enumerate(lines) if l.startswith("## 0.")), len(lines))
    idx_text = "\n".join(lines[idx_start:idx_end])
    missing_idx = ["9.%d" % n for _, n in heads if not re.search(r"§9\.%d\b" % n, idx_text)]
    s14 = next((i for i, l in enumerate(lines) if l.startswith("## 14.")), len(lines))
    dates = [m.group(1) for l in lines[s14:] if (m := re.match(r"^\| (\d{4}-\d{2}-\d{2}) \|", l))]
    out_of_order = [{"row": dates[i], "then": dates[i + 1]} for i in range(len(dates) - 1) if dates[i + 1] > dates[i]]
    over = []
    for k, (ln, n) in enumerate(heads):
        if n >= RECORD_WATCH_FROM:
            nxt = heads[k + 1][0] if k + 1 < len(heads) else s14 + 1
            if nxt - ln > RECORD_SECTION_CAP:
                over.append({"section": "9.%d" % n, "lines": nxt - ln})
    return {"lines": len(lines), "sections": len(heads),
            "first": "9.%d" % heads[0][1] if heads else None, "last": "9.%d" % heads[-1][1] if heads else None,
            "monotonic": not non_mono, "non_monotonic_pairs": non_mono, "missing_index_rows": missing_idx,
            "s14_rows": len(dates), "s14_newest_first": not out_of_order, "s14_out_of_order": out_of_order,
            "over_cap_since_9_%d" % RECORD_WATCH_FROM: over}


def scan_links(md: list[str]) -> dict:
    broken = []
    for p in md:
        base = (REPO / p).parent
        for m in LINK.finditer(read(p)):
            tgt = m.group(1)
            if tgt.startswith(("http://", "https://", "mailto:", "#")):
                continue
            tgt = tgt.split("#")[0]
            if tgt and not (base / tgt).exists():
                broken.append({"file": p, "target": tgt})
    return {"files": len(md), "broken": broken}


def living_documents() -> list[str]:
    import city
    docs = Path(city.docs())
    cdocs = Path(city.city_docs())
    out = [REPO / "README.md", REPO / ".claude" / "CLAUDE.md"]
    out += sorted(docs.glob("*.md")) + sorted((docs / "positions").glob("*.md"))
    out += [docs / "reports" / "README.md", docs / "reports" / "reference" / "README.md"]
    out += sorted(cdocs.glob("*.md"))
    return [str(p.relative_to(REPO)).replace("\\", "/") for p in out if p.exists()]


def scan_shared_figures() -> dict:
    import city
    import positions
    board = (Path(city.docs()) / "STATUS.md").read_text(encoding="utf-8")
    figures = positions.board_figures(board)
    docs = [str(REPO / p) for p in living_documents() if not p.endswith("STATUS.md")]
    rows = positions.second_homes(figures, docs)
    by_figure: dict[str, list] = {}
    for label, fig, where, line in rows:
        by_figure.setdefault("%s = %s" % (label, fig), []).append({"where": where, "line": line})
    return {"board_figures": figures, "restatements": by_figure, "total": len(rows)}


def scan_budgets() -> dict:
    contract = read("docs/HANDOVER_CONTRACT.md")
    rows = []
    for m in BUDGET_ROW.finditer(contract):
        layer, path, budget = m.group(1).strip(), m.group(2), m.group(3).strip()
        target = path.replace("<city>", "newcastle").replace("<topic>", "")
        if target.endswith("/"):
            continue
        p = REPO / target
        actual = read(target).count("\n") if p.exists() and p.is_file() else None
        rows.append({"layer": layer, "path": path, "budget": budget, "lines": actual})
    pairs = {}
    agents = REPO / ".agents"
    if agents.is_dir():
        for sk in ("handoff", "onboard", "project-report"):
            a, b = agents / "skills" / sk / "SKILL.md", REPO / ".claude" / "skills" / sk / "SKILL.md"
            pairs[str(a.relative_to(REPO)).replace("\\", "/")] = (
                "missing" if not a.exists() else ("same" if b.exists() and filecmp.cmp(a, b, shallow=False) else "differs"))
        sdir = agents / "skills" / "project-report" / "scripts"
        if sdir.is_dir():
            for f in sorted(sdir.glob("*.py")):
                b = REPO / ".claude" / "skills" / "project-report" / "scripts" / f.name
                pairs[str(f.relative_to(REPO)).replace("\\", "/")] = (
                    "no .claude twin" if not b.exists() else ("same" if filecmp.cmp(f, b, shallow=False) else "differs"))
    return {"reading_budget": rows, "agents_divergence": pairs}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # a Windows console is cp1252
    if len(argv) != 1:
        print(__doc__)
        return 2
    out_dir = Path(argv[0])
    out_dir.mkdir(parents=True, exist_ok=True)
    md = tracked(".md")
    result = {
        "head": subprocess.run(["git", "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True, cwd=REPO).stdout.strip(),
        "tracked_md": len(md),
        "banners": scan_banners(md),
        "record": scan_record(),
        "links": scan_links(md),
        "shared_figures": scan_shared_figures(),
        "budgets": scan_budgets(),
    }
    out = out_dir / "scan_documents.json"
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    r = result
    print("scan_documents at %s: %d tracked .md" % (r["head"], r["tracked_md"]))
    print("  banners: %d archived, %d unbannered; %d long living without a banner"
          % (r["banners"]["archived"], len(r["banners"]["unbannered"]),
             len(r["banners"]["living_over_%d_lines_without_banner" % LONG_LIVING_LINES])))
    rec = r["record"]
    print("  record: %d sections %s..%s, monotonic %s, %d index rows missing, §14 %d rows newest-first %s, %d over the cap"
          % (rec["sections"], rec["first"], rec["last"], rec["monotonic"], len(rec["missing_index_rows"]),
             rec["s14_rows"], rec["s14_newest_first"], len(rec["over_cap_since_9_%d" % RECORD_WATCH_FROM])))
    print("  links: %d broken over %d files" % (len(r["links"]["broken"]), r["links"]["files"]))
    print("  shared figures: %d restatements of %d board figures" % (r["shared_figures"]["total"], len(r["shared_figures"]["board_figures"])))
    for row in r["budgets"]["reading_budget"]:
        print("  budget %-10s %-28s %-9s lines %s" % (row["layer"], row["path"], row["budget"], row["lines"]))
    div = [k for k, v in r["budgets"]["agents_divergence"].items() if v != "same"]
    print("  .agents divergence: %d of %d differ" % (len(div), len(r["budgets"]["agents_divergence"])))
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
