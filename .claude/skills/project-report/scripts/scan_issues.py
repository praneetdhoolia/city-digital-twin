#!/usr/bin/env python3
"""The issue and churn scans Phase 5 of /project-report used to re-derive in scratch.

    python .claude/skills/project-report/scripts/scan_issues.py <scratch>/metrics <scratch>/reviews [--prs N]

Reads `<metrics>/metrics.json` (collect_metrics.py: every issue with its
labels and dates) and `<metrics>/issues_full.md` (every open issue's body and
comments), asks GitHub through `gh` for the state of each issue a lane task or
a run overlay binds, and reads the last `--prs` merged pull requests' position
page diffs. Writes `<out>/scan_issues.json` and prints a summary. Four scans:

  past           closed-issue statistics: median, mean and maximum days open,
                 same-day closures, the oldest closures, those closed since
                 the previous report's date
  present        every open issue's labels, the AWAITING-RUN / AWAITING-DECISION
                 lines verified in its body and comments (the newest last), the
                 run names and families it names, two-state-label issues, open
                 issues without the phase label
  bindings       every issue number in docs/lane.json's open tasks and
                 decisions and in cities/<city>/overlays/runs/*.json
                 `answers_issues`, with its GitHub state - a CLOSED one is the
                 defect the sixteenth report found (#175 bound by the lane's
                 recommended arm, seventeen days after it closed)
  churn          per merged PR, which position pages changed and whether their
                 "What is built" changed or only the stamp and History

`gh` absent or offline: bindings carry state "unknown" and the summary says so.
"""
from __future__ import annotations

import json
import re
import statistics
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

DEFAULT_PRS = 5
PHASE_LABEL = re.compile(r"^P\d$")
STATE_LABELS = ("awaiting-run", "awaiting-implementation", "decision-needed")
AWAITING = re.compile(r"^\s*\**AWAITING-(RUN|DECISION|IMPLEMENTATION):?\**:?\s*(.*)$", re.M)
RUN_NAME = re.compile(r"\d{8}T\d{6}_\d+it_\d+(?:\.\d+)?pct")
FAMILY = re.compile(r"\bF\d{1,3}\b")


def _run(args, cwd=REPO, timeout=120):
    try:
        p = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=timeout, encoding="utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def scan_past(issues: list[dict], since: str | None) -> dict:
    closed = [i for i in issues if i.get("state") == "CLOSED" and i.get("closed")]
    def d(s):
        return date.fromisoformat(str(s)[:10])
    days = [(d(i["closed"]) - d(i["created"])).days for i in closed]
    out = {"closed": len(closed), "open": sum(1 for i in issues if i.get("state") == "OPEN")}
    if days:
        out.update({"median_days_open": statistics.median(days), "mean_days_open": round(sum(days) / len(days), 2),
                    "max_days_open": max(days), "same_day_closures": sum(1 for x in days if x == 0),
                    "oldest_closures": sorted([[x, i["number"], i["title"]] for x, i in zip(days, closed)], reverse=True)[:3]})
    if since:
        out["closed_since_%s" % since] = [{"number": i["number"], "opened": i["created"][:10], "closed": i["closed"][:10],
                                           "days": (d(i["closed"]) - d(i["created"])).days}
                                          for i in closed if i["closed"][:10] >= since]
    return out


def scan_present(issues_full: str, issues: list[dict], today: date) -> dict:
    blocks = re.split(r"^# #(\d+) ", issues_full, flags=re.M)
    present = {}
    for k in range(1, len(blocks), 2):
        n, body = int(blocks[k]), blocks[k + 1]
        head = body.split("\n", 1)[0]
        if "[OPEN]" not in head:
            continue
        meta = next((i for i in issues if i.get("number") == n), {})
        labels = meta.get("labels") or []
        labels = [l if isinstance(l, str) else l.get("name", "") for l in labels]
        lines = {"RUN": [], "DECISION": [], "IMPLEMENTATION": []}
        for m in AWAITING.finditer(body):
            lines[m.group(1)].append(m.group(2).strip()[:240])
        present[n] = {
            "labels": labels,
            "age_days": (today - date.fromisoformat(meta["created"][:10])).days if meta.get("created") else None,
            "awaiting_run_lines": lines["RUN"], "awaiting_decision_lines": lines["DECISION"],
            "awaiting_implementation_lines": lines["IMPLEMENTATION"],
            "runs_named": sorted(set(RUN_NAME.findall(body))), "families_named": sorted(set(FAMILY.findall(body))),
            "state_labels": [l for l in labels if l in STATE_LABELS],
            "has_phase_label": any(PHASE_LABEL.match(l) for l in labels),
        }
    return {"open": len(present),
            "two_state_labels": [n for n, p in present.items() if len(p["state_labels"]) > 1],
            "without_phase_label": [n for n, p in present.items() if not p["has_phase_label"]],
            "awaiting_run_without_line": [n for n, p in present.items()
                                          if "awaiting-run" in p["labels"] and not p["awaiting_run_lines"]],
            "issues": present}


def issue_states(numbers: list[int]) -> dict[int, str]:
    states = {}
    for n in sorted(set(numbers)):
        out = _run(["gh", "issue", "view", str(n), "--json", "state", "--jq", ".state"], timeout=60)
        states[n] = out.strip() if out else "unknown"
    return states


def scan_bindings() -> dict:
    import city
    lane = json.loads((Path(city.docs()) / "lane.json").read_text(encoding="utf-8"))
    bound: dict[int, list[str]] = {}
    for t in lane.get("tasks", []):
        if t.get("status") in ("open", "held"):
            for n in t.get("answers_issues", []) or []:
                bound.setdefault(int(n), []).append("lane task %s" % t.get("id"))
    for dcs in lane.get("decisions", []):
        if dcs.get("answer") is None:
            for n in dcs.get("issues", []) or []:
                bound.setdefault(int(n), []).append("lane decision %s" % dcs.get("id"))
    overlays = Path(city.path("overlays", "runs"))
    if overlays.is_dir():
        for f in sorted(overlays.glob("*.json")):
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            for n in doc.get("answers_issues", []) or []:
                bound.setdefault(int(n), []).append("overlay %s" % f.stem)
    states = issue_states(list(bound))
    rows = [{"issue": n, "state": states.get(n, "unknown"), "bound_by": by} for n, by in sorted(bound.items())]
    return {"bound": rows, "closed": [r for r in rows if r["state"] == "CLOSED"],
            "unknown": [r["issue"] for r in rows if r["state"] == "unknown"]}


def scan_churn(n_prs: int) -> list[dict]:
    out = _run(["gh", "pr", "list", "--state", "merged", "--limit", str(n_prs), "--json",
                "number,title,mergedAt,mergeCommit,baseRefOid"], timeout=120)
    if not out:
        return []
    rows = []
    for pr in json.loads(out):
        merge, base = (pr.get("mergeCommit") or {}).get("oid"), pr.get("baseRefOid")
        if not merge or not base:
            continue
        files = (_run(["git", "diff", "--name-only", base, merge, "--", "docs/positions"]) or "").split()
        pages = {}
        for f in files:
            diff = _run(["git", "diff", "-U0", base, merge, "--", f]) or ""
            new = (_run(["git", "show", "%s:%s" % (merge, f)]) or "").splitlines()
            sec_of_line, cur = {}, "intro/stamp"
            for i, l in enumerate(new, 1):
                if l.startswith("## "):
                    cur = l[3:].strip()
                sec_of_line[i] = cur
            counts: dict[str, int] = {}
            for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, flags=re.M):
                s = sec_of_line.get(int(m.group(1)), "intro/stamp")
                counts[s] = counts.get(s, 0) + max(int(m.group(2) or 1), 1)
            pages[f.rsplit("/", 1)[-1]] = {"add": diff.count("\n+") - diff.count("\n+++"),
                                           "del": diff.count("\n-") - diff.count("\n---"),
                                           "new_lines_by_section": counts}
        rows.append({"pr": pr["number"], "title": pr["title"], "merged": str(pr.get("mergedAt", ""))[:10],
                     "pages_touched": len(files),
                     "pages_with_what_is_built_change": sum(1 for p in pages.values() if p["new_lines_by_section"].get("What is built", 0) > 0),
                     "pages_stamp_or_history_only": [k for k, p in pages.items()
                                                     if set(p["new_lines_by_section"]) <= {"intro/stamp", "History"}],
                     "pages": pages})
    return rows


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # a Windows console is cp1252
    n_prs = DEFAULT_PRS
    if "--prs" in argv:
        i = argv.index("--prs")
        n_prs = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 2:
        print(__doc__)
        return 2
    metrics_dir, out_dir = Path(argv[0]), Path(argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = json.loads((metrics_dir / "metrics.json").read_text(encoding="utf-8")) if (metrics_dir / "metrics.json").exists() else {}
    issues = (metrics.get("github") or {}).get("issues") or []
    full = (metrics_dir / "issues_full.md").read_text(encoding="utf-8") if (metrics_dir / "issues_full.md").exists() else ""
    today = date.fromisoformat(str(metrics.get("collected_at", date.today().isoformat()))[:10])
    import city
    reports = Path(city.docs()) / "reports"
    stamps = sorted(p.name[:8] for p in reports.glob("*_project_report.html")) if reports.is_dir() else []
    since = ("%s-%s-%s" % (stamps[-2][:4], stamps[-2][4:6], stamps[-2][6:8])) if len(stamps) >= 2 else None
    result = {
        "collected_at": today.isoformat(),
        "past": scan_past(issues, since),
        "present": scan_present(full, issues, today),
        "bindings": scan_bindings(),
        "churn": scan_churn(n_prs),
    }
    out = out_dir / "scan_issues.json"
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    p, pr = result["past"], result["present"]
    print("scan_issues: %d closed (median %s d, max %s d), %d open" % (p["closed"], p.get("median_days_open"), p.get("max_days_open"), pr["open"]))
    print("  present: %d with two state labels %s; %d without a phase label %s; %d awaiting-run without a line %s"
          % (len(pr["two_state_labels"]), pr["two_state_labels"], len(pr["without_phase_label"]), pr["without_phase_label"],
             len(pr["awaiting_run_without_line"]), pr["awaiting_run_without_line"]))
    b = result["bindings"]
    print("  bindings: %d issue(s) bound by the lane or an overlay; CLOSED: %s; unknown (gh offline): %s"
          % (len(b["bound"]), [r["issue"] for r in b["closed"]] or "none", b["unknown"] or "none"))
    for c in result["churn"]:
        print("  PR #%d (%s): %d page(s), %d with a What-is-built change, stamp/history only: %s"
              % (c["pr"], c["merged"], c["pages_touched"], c["pages_with_what_is_built_change"], c["pages_stamp_or_history_only"] or "none"))
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
