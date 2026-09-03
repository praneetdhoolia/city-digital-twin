"""Collect the mechanical half of a project report into one JSON file.

Everything here is derived from the repository and GitHub, never typed in:
the file inventory, the commit log, the per-merge growth series, the pull
requests with their commits and files, the issues with their labels and
comments, the CI history, and the run index if one exists on disk. The
report writer reads the JSON; nothing in the report's numbers should come
from anywhere else.

    python .claude/skills/project-report/scripts/collect_metrics.py OUT_DIR
    python .claude/skills/project-report/scripts/collect_metrics.py OUT_DIR --no-github
    python .claude/skills/project-report/scripts/collect_metrics.py OUT_DIR --no-growth

Writes OUT_DIR/metrics.json, OUT_DIR/prs_full.md (one block per PR with its
commits, files and full body, for the milestone reviewer) and
OUT_DIR/issues_full.md. Needs `git`; the GitHub half needs `gh` logged in.
The growth series calls `git show` for every source file at every merge
commit and takes a few minutes on a repository of this size.
"""
from __future__ import annotations

import collections
import csv
import json
import os
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".git", ".tools", "__pycache__", "results", "node_modules"}
TEXT_EXT = {".py", ".java", ".md", ".json", ".sh", ".yml", ".yaml", ".html", ".tsv", ".csv", ".txt"}
CODE_EXT = {".py", ".java"}


def sh(args: list[str], **kw) -> str:
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} -> rc={r.returncode}: {r.stderr[:400]}")
    return r.stdout


def repo_root() -> Path:
    return Path(sh(["git", "rev-parse", "--show-toplevel"]).strip())


def inventory(root: Path) -> dict:
    ext = collections.Counter()
    lines = collections.Counter()
    largest = []
    n = 0
    todo = 0
    py = dict(files=0, defs=0, classes=0, documented=0)
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            p = Path(dirpath, f)
            rel = p.relative_to(root).as_posix()
            e = p.suffix or f
            n += 1
            ext[e] += 1
            if e not in TEXT_EXT:
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            L = txt.count("\n")
            lines[e] += L
            if e in CODE_EXT or e == ".md":
                largest.append((L, rel))
            if e in CODE_EXT:
                todo += len(re.findall(r"\b(TODO|FIXME|XXX|HACK)\b", txt))
            if e == ".py":
                py["files"] += 1
                py["defs"] += len(re.findall(r"^\s*def ", txt, re.M))
                py["classes"] += len(re.findall(r"^\s*class ", txt, re.M))
                py["documented"] += len(re.findall(r"^\s*(?:def|class) [^\n]*\n\s*(?:r?\"\"\"|r?''')", txt, re.M))
    tracked = [t for t in sh(["git", "ls-files"]).split("\n") if t]
    by_top = collections.Counter(t.split("/")[0] for t in tracked)
    by_city = collections.Counter("/".join(t.split("/")[:3]) for t in tracked if t.startswith("cities/"))
    return dict(
        files_on_disk=n,
        by_extension=ext.most_common(25),
        lines_by_extension=dict(lines),
        largest=sorted(largest, reverse=True)[:40],
        todo_markers=todo,
        python=py,
        tracked_files=len(tracked),
        tracked_by_top_dir=by_top.most_common(),
        tracked_under_cities=by_city.most_common(20),
    )


def commit_log(root: Path) -> dict:
    raw = sh(["git", "log", "--format=%H|%ad|%an|%s", "--date=short"]).strip().split("\n")
    rows = [l.split("|", 3) for l in raw if l]
    by_day = collections.Counter(r[1] for r in rows)
    authors = collections.Counter(r[2] for r in rows)
    prefixes = collections.Counter()
    for _, _, _, s in rows:
        m = re.match(r"^(P\d|Merge)", s)
        prefixes[m.group(1) if m else "other"] += 1
    lengths = sorted(len(r[3]) for r in rows)
    direct = [l for l in sh(["git", "log", "--first-parent", "--no-merges", "--format=%h|%ad|%s", "--date=short"]).strip().split("\n") if l]
    churn = collections.Counter(f for f in sh(["git", "log", "--format=", "--name-only"]).split("\n") if f)
    return dict(
        total=len(rows),
        merges=sum(1 for r in rows if r[3].startswith("Merge")),
        first_date=rows[-1][1] if rows else None,
        last_date=rows[0][1] if rows else None,
        by_day=sorted(by_day.items()),
        authors=authors.most_common(),
        message_prefixes=prefixes.most_common(),
        subject_length=dict(min=lengths[0], median=lengths[len(lengths) // 2], max=lengths[-1]) if lengths else {},
        direct_to_default_branch=[dict(sha=d.split("|")[0], date=d.split("|")[1], subject=d.split("|", 2)[2]) for d in direct],
        churn_hotspots=churn.most_common(40),
    )


def _show(sha: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{sha}:{path}"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return r.stdout if r.returncode == 0 else None


def growth_series(root: Path) -> list[dict]:
    """Registry fields, manifest rows and code lines at every first-parent commit."""
    merges = [l for l in sh(["git", "log", "--first-parent", "--format=%h|%ad|%s", "--date=short"]).strip().split("\n") if l]
    out = []
    for m in reversed(merges):
        sha, date, msg = m.split("|", 2)
        tree = sh(["git", "ls-tree", "-r", "--name-only", sha]).split("\n")
        py = java = 0
        fields = None
        manifest = None
        registry_files = []
        for f in tree:
            if f.endswith(".py"):
                t = _show(sha, f)
                py += t.count("\n") if t else 0
            elif f.endswith(".java"):
                t = _show(sha, f)
                java += t.count("\n") if t else 0
            elif f.endswith("required_fields.json"):
                t = _show(sha, f)
                try:
                    j = json.loads(t)
                    fields = len(j.get("fields", j))
                except Exception:
                    pass
            elif f.endswith("MANIFEST.csv"):
                t = _show(sha, f)
                manifest = t.count("\n") - 1 if t else None
            elif "/registry/" in f and f.endswith(".json"):
                registry_files.append(f)
        if fields is None and registry_files:
            fields = 0
            for f in registry_files:
                t = _show(sha, f)
                try:
                    j = json.loads(t)
                    fields += len(j.get("fields", j))
                except Exception:
                    pass
        out.append(dict(date=date, sha=sha, registry_fields=fields, manifest_rows=manifest, python_lines=py, java_lines=java, subject=msg[:80]))
    return out


def github(root: Path, out_dir: Path) -> dict:
    prs = json.loads(sh(["gh", "pr", "list", "--state", "all", "--limit", "500", "--json",
                         "number,title,state,createdAt,mergedAt,additions,deletions,changedFiles,reviews,statusCheckRollup"]))
    full = []
    for p in sorted(prs, key=lambda x: x["number"]):
        d = json.loads(sh(["gh", "pr", "view", str(p["number"]), "--json", "commits,files,body,title,mergedAt,state"]))
        full.append(dict(number=p["number"], title=d["title"], state=d["state"], mergedAt=d["mergedAt"],
                         additions=p["additions"], deletions=p["deletions"], changedFiles=p["changedFiles"],
                         reviews=len(p["reviews"]), checks=collections.Counter((c.get("conclusion") or c.get("state")) for c in (p["statusCheckRollup"] or [])),
                         commits=[dict(oid=c["oid"][:8], date=c["committedDate"][:10], msg=c["messageHeadline"]) for c in d["commits"]],
                         files=[f["path"] for f in d["files"]], body=d["body"] or ""))
    with open(out_dir / "prs_full.md", "w", encoding="utf-8") as fh:
        for p in full:
            fh.write(f"\n\n# PR #{p['number']} [{p['state']}] merged {p['mergedAt']} +{p['additions']}/-{p['deletions']} files={len(p['files'])}\n## {p['title']}\n")
            fh.write("### commits\n" + "\n".join(f"- {c['date']} {c['oid']} {c['msg']}" for c in p["commits"]) + "\n")
            fh.write("### files (first 40)\n" + "\n".join("- " + f for f in p["files"][:40]) + "\n### body\n" + p["body"] + "\n")
    issues = json.loads(sh(["gh", "issue", "list", "--state", "all", "--limit", "1000", "--json",
                            "number,title,state,createdAt,closedAt,labels,comments,body"]))
    with open(out_dir / "issues_full.md", "w", encoding="utf-8") as fh:
        for i in sorted(issues, key=lambda x: x["number"]):
            fh.write(f"\n\n# #{i['number']} [{i['state']}] {i['createdAt'][:10]} -> {(i['closedAt'] or '')[:10]} labels={','.join(l['name'] for l in i['labels'])}\n## {i['title']}\n{i['body'] or ''}\n")
            for c in i["comments"]:
                fh.write(f"\n--- comment {c['createdAt'][:10]}\n{c['body']}\n")
    P = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    closed = [i for i in issues if i["state"] == "CLOSED"]
    opened = [i for i in issues if i["state"] == "OPEN"]
    ttc = [(P(i["closedAt"]) - P(i["createdAt"])).days for i in closed]
    runs = json.loads(sh(["gh", "run", "list", "--limit", "200", "--json", "conclusion,createdAt,workflowName,headBranch,event"]))
    return dict(
        prs=[{k: v for k, v in p.items() if k not in ("body", "files", "commits")} | dict(n_commits=len(p["commits"]), n_files=len(p["files"]), body_chars=len(p["body"]), checks=dict(p["checks"])) for p in full],
        pr_stats=dict(total=len(full), merged=sum(1 for p in full if p["state"] == "MERGED"), closed_unmerged=sum(1 for p in full if p["state"] == "CLOSED"),
                      reviews_total=sum(p["reviews"] for p in full),
                      median_additions=statistics.median(p["additions"] for p in full), median_files=statistics.median(len(p["files"]) for p in full),
                      commits_per_pr=dict(min=min(len(p["commits"]) for p in full), median=statistics.median(len(p["commits"]) for p in full), max=max(len(p["commits"]) for p in full))),
        issues=[dict(number=i["number"], title=i["title"], state=i["state"], created=i["createdAt"][:10], closed=(i["closedAt"] or "")[:10],
                     labels=[l["name"] for l in i["labels"]], comments=len(i["comments"])) for i in sorted(issues, key=lambda x: x["number"])],
        issue_stats=dict(total=len(issues), open=len(opened), closed=len(closed),
                         labels=collections.Counter(l["name"] for i in issues for l in i["labels"]).most_common(),
                         time_to_close_days=dict(median=statistics.median(ttc) if ttc else None, mean=round(statistics.mean(ttc), 1) if ttc else None, max=max(ttc) if ttc else None, same_day=sum(1 for t in ttc if t == 0)),
                         open_age_days=sorted((now - P(i["createdAt"])).days for i in opened),
                         open_unlabelled=[i["number"] for i in opened if not i["labels"]],
                         comments_total=sum(len(i["comments"]) for i in issues)),
        ci=dict(runs=len(runs), by_workflow_and_conclusion=collections.Counter(f"{r['workflowName']}:{r['conclusion']}" for r in runs).most_common(),
                failures_by_branch=collections.Counter(r["headBranch"] for r in runs if r["conclusion"] == "failure").most_common(10),
                first=runs[-1]["createdAt"][:10] if runs else None, last=runs[0]["createdAt"][:10] if runs else None),
    )


def run_index(root: Path) -> dict | None:
    p = root / "results" / "INDEX.csv"
    if not p.exists():
        return None
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    return dict(rows=len(rows),
                by_class_status=collections.Counter(f"{r.get('class')}:{r.get('status')}" for r in rows).most_common(),
                by_family=collections.Counter(r.get("family") for r in rows).most_common(),
                with_run_record=sum(1 for r in rows if r.get("run_record") == "yes"))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    out_dir = Path(argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    root = repo_root()
    os.chdir(root)
    m = dict(collected_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
             head=sh(["git", "rev-parse", "--short", "HEAD"]).strip(),
             branch=sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip(),
             dirty=[l for l in sh(["git", "status", "--short"]).split("\n") if l])
    print("inventory ...", flush=True)
    m["inventory"] = inventory(root)
    print("commit log ...", flush=True)
    m["commits"] = commit_log(root)
    if "--no-growth" not in argv:
        print("growth series (slow) ...", flush=True)
        m["growth"] = growth_series(root)
    if "--no-github" not in argv:
        print("github ...", flush=True)
        m["github"] = github(root, out_dir)
    m["run_index"] = run_index(root)
    (out_dir / "metrics.json").write_text(json.dumps(m, indent=1, default=str), encoding="utf-8")
    print(f"wrote {out_dir / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
