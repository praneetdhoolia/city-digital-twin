#!/usr/bin/env python3
"""Render the dated /project-report HTML from the lanes' JSON deliverables.

    python .claude/skills/project-report/scripts/render_report.py <scratch> <out.html>

`<scratch>` is the pass's scratch directory holding:

    metrics/metrics.json, metrics/code_metrics.json, metrics/performance.json
    reviews/phase2_code.json  reviews/phase3_perf.json
    reviews/phase4_history.json  reviews/phase5_docs.json
    research/field.json  research/factors.json
    modes_table.json          (Phase 8.4b, the twelve modes and the supply table)
    synthesis.json            (Phase 8: verdict, merged findings, ledger, ratings,
                               goal table, since-last, process verdict, recommendations)

Every section is rendered from the JSON it names; a key that is absent renders
as a stated gap, never as an empty box. Unknown shapes fall back to a generic
renderer so a lane can add a field without this script changing. The report-data
block embedded at the end is what the next pass diffs against.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

MAX_EMBED_LIST = 400          # per-list cap inside the embedded report-data block
STATUS_GOOD, STATUS_SERIOUS, STATUS_CRITICAL = "#0ca30c", "#ec835a", "#d03b3b"


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def load(scratch: Path, rel: str):
    p = scratch / rel
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def md_inline(s: str) -> str:
    """Escape, then allow **bold**, `code` and [text](url) only."""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def para(s: str) -> str:
    return "".join(f"<p>{md_inline(p.strip())}</p>" for p in str(s).split("\n\n") if p.strip())


def render_any(v, depth=0) -> str:
    """Generic renderer for a lane's JSON when the shape is not known here."""
    if v is None:
        return "<span class=muted>—</span>"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int, float)):
        return f"<span class=num>{v:,}</span>" if isinstance(v, int) else f"<span class=num>{v}</span>"
    if isinstance(v, str):
        return md_inline(v)
    if isinstance(v, list):
        if not v:
            return "<span class=muted>none</span>"
        if all(isinstance(x, dict) for x in v):
            cols: list[str] = []
            for x in v:
                for k in x:
                    if k not in cols:
                        cols.append(k)
            if len(cols) <= 12:
                return table(v, cols)
        return "<ul>" + "".join(f"<li>{render_any(x, depth + 1)}</li>" for x in v) + "</ul>"
    if isinstance(v, dict):
        return "<dl class=kv>" + "".join(
            f"<dt>{esc(k)}</dt><dd>{render_any(x, depth + 1)}</dd>" for k, x in v.items()) + "</dl>"
    return esc(v)


def table(rows, cols, labels=None, cls="") -> str:
    labels = labels or {}
    head = "".join(f"<th>{esc(labels.get(c, c))}</th>" for c in cols)
    body = []
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c) if isinstance(r, dict) else None
            cells.append(f"<td>{render_any(v)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def section(sid: str, title: str, body: str, lead: str = "") -> str:
    lead_html = f"<p class=lead>{md_inline(lead)}</p>" if lead else ""
    return f'<section id="{sid}"><h2>{esc(title)}</h2>{lead_html}{body}</section>'


def _count(v):
    return len(v) if isinstance(v, (list, dict)) else v


def gap(what: str) -> str:
    return f'<p class="gap">Not produced this pass: {esc(what)}.</p>'


def dev_class(dev) -> str:
    try:
        d = abs(float(dev))
    except (TypeError, ValueError):
        return "na"
    return "ok" if d < 10 else ("warn" if d < 20 else "stop")


# ----------------------------------------------------------------- charts

def deviation_chart(modes: list[dict]) -> str:
    """Horizontal bars of per-mode deviation at the newest RESULT, clipped at ±120 %,
    status-coloured with the label carrying the state so colour is never alone."""
    rows = [m for m in modes if isinstance(m.get("result", {}).get("dev"), (int, float))]
    if not rows:
        return ""
    w, rh, left, right = 720, 26, 110, 70
    h = rh * len(rows) + 40
    clip = 120.0
    scale = (w - left - right) / (2 * clip)
    x0 = left + clip * scale
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Deviation from target by mode at the newest result" class="chart">']
    for pct, lab in ((-20, "−20 %"), (-10, "−10 %"), (10, "+10 %"), (20, "+20 %")):
        x = x0 + pct * scale
        out.append(f'<line x1="{x:.1f}" y1="18" x2="{x:.1f}" y2="{h-18}" class="grid"/>')
        out.append(f'<text x="{x:.1f}" y="12" class="tick" text-anchor="middle">{lab}</text>')
    out.append(f'<line x1="{x0:.1f}" y1="18" x2="{x0:.1f}" y2="{h-18}" class="axis"/>')
    for i, m in enumerate(rows):
        d = float(m["result"]["dev"])
        y = 24 + i * rh
        dc = max(-clip, min(clip, d))
        x1, x2 = sorted((x0, x0 + dc * scale))
        col = {"ok": STATUS_GOOD, "warn": STATUS_SERIOUS, "stop": STATUS_CRITICAL}[dev_class(d)]
        out.append(f'<text x="{left-8}" y="{y+13}" class="lab" text-anchor="end">{esc(m["mode"])}</text>')
        out.append(f'<rect x="{x1:.1f}" y="{y+5}" width="{max(2, x2-x1):.1f}" height="{rh-10}" rx="3" fill="{col}"/>')
        lx = (x2 + 6) if d >= 0 else (x1 - 6)
        anc = "start" if d >= 0 else "end"
        clipped = " ▸" if abs(d) > clip else ""
        out.append(f'<text x="{lx:.1f}" y="{y+13}" class="val" text-anchor="{anc}">{d:+.1f} %{clipped}</text>')
    out.append("</svg>")
    return "".join(out)


def series_chart(points: list[dict], xkey: str, ykeys: list[str], title: str, colours: list[str]) -> str:
    """Small multiple-series line chart; one scale, direct-labelled ends."""
    pts = [p for p in points if all(isinstance(p.get(k), (int, float)) for k in ykeys)]
    if len(pts) < 2:
        return ""
    w, h, l, r, t, b = 640, 220, 44, 120, 24, 36
    ymax = max(max(float(p[k]) for k in ykeys) for p in pts) or 1
    n = len(pts)
    sx = lambda i: l + i * (w - l - r) / (n - 1)
    sy = lambda v: t + (h - t - b) * (1 - float(v) / ymax)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}" class="chart">']
    for g in range(0, 5):
        yv = ymax * g / 4
        out.append(f'<line x1="{l}" y1="{sy(yv):.1f}" x2="{w-r}" y2="{sy(yv):.1f}" class="grid"/>')
        out.append(f'<text x="{l-6}" y="{sy(yv)+4:.1f}" class="tick" text-anchor="end">{yv:.0f}</text>')
    for i, p in enumerate(pts):
        out.append(f'<text x="{sx(i):.1f}" y="{h-12}" class="tick" text-anchor="middle">{esc(str(p.get(xkey))[:10])}</text>')
    for k, col in zip(ykeys, colours):
        d = " ".join(f"{'M' if i == 0 else 'L'}{sx(i):.1f},{sy(p[k]):.1f}" for i, p in enumerate(pts))
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2"/>')
        for i, p in enumerate(pts):
            out.append(f'<circle cx="{sx(i):.1f}" cy="{sy(p[k]):.1f}" r="4" fill="{col}"><title>{esc(k)} {p[k]} ({esc(p.get(xkey))})</title></circle>')
        out.append(f'<text x="{w-r+8}" y="{sy(pts[-1][k])+4:.1f}" class="lab" fill="{col}">{esc(k)}</text>')
    out.append("</svg>")
    return "".join(out)


def stage_strip(strip: dict | list) -> str:
    """Lanes of dated spans and events from the historian's stage_strip JSON."""
    lanes = strip.get("lanes") if isinstance(strip, dict) else strip
    if not lanes:
        return ""
    def d(s):
        try:
            return dt.date.fromisoformat(str(s)[:10])
        except Exception:
            return None
    dates = []
    for ln in lanes:
        for it in ln.get("items", ln.get("spans", [])) + ln.get("events", []):
            for k in ("start", "end", "date"):
                x = d(it.get(k)) if isinstance(it, dict) else None
                if x:
                    dates.append(x)
    if not dates:
        return ""
    d0, d1 = min(dates), max(dates)
    span = max(1, (d1 - d0).days)
    w, lh, left = 900, 22, 150
    h = lh * len(lanes) + 40
    sx = lambda x: left + (x - d0).days * (w - left - 20) / span
    out = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="Timeline from day 0">']
    cur = d0
    while cur <= d1:
        if cur.day in (1, 10, 20) or cur == d0:
            out.append(f'<line x1="{sx(cur):.1f}" y1="14" x2="{sx(cur):.1f}" y2="{h-16}" class="grid"/>')
            out.append(f'<text x="{sx(cur):.1f}" y="10" class="tick" text-anchor="middle">{cur.strftime("%d %b")}</text>')
        cur += dt.timedelta(days=1)
    for i, ln in enumerate(lanes):
        y = 20 + i * lh
        out.append(f'<text x="{left-8}" y="{y+14}" class="lab" text-anchor="end">{esc(ln.get("name", ln.get("lane", "")))}</text>')
        for it in ln.get("items", ln.get("spans", [])):
            a, b_ = d(it.get("start")), d(it.get("end"))
            if a and b_:
                out.append(f'<rect x="{sx(a):.1f}" y="{y+4}" width="{max(3, sx(b_)-sx(a)):.1f}" height="{lh-8}" rx="3" class="span"><title>{esc(it.get("label", ""))} {a}–{b_}</title></rect>')
        for ev in ln.get("events", []):
            x = d(ev.get("date"))
            if x:
                out.append(f'<circle cx="{sx(x):.1f}" cy="{y+lh/2}" r="3.5" class="ev"><title>{esc(ev.get("label", ""))} {x}</title></circle>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- sections

def tiles(items: list[tuple[str, str, str]]) -> str:
    return '<div class="tiles">' + "".join(
        f'<div class="tile"><div class="tile-v">{v}</div><div class="tile-k">{esc(k)}</div><div class="tile-s">{md_inline(s)}</div></div>'
        for k, v, s in items) + "</div>"


def modes_section(mt: dict) -> str:
    modes = mt.get("modes", [])
    cols = ["mode", "result", "reading", "target_provenance", "simulated", "data_has", "data_lacks", "obtainable_from", "mechanism", "controls"]
    rows = []
    for m in modes:
        r = dict(m)
        res, rd = m.get("result", {}), m.get("reading", {})
        r["result"] = f'<span class="dev {dev_class(res.get("dev"))}">{esc(res.get("modelled"))} vs {esc(res.get("target"))} → {esc(res.get("dev"))}{"" if isinstance(res.get("dev"), str) else " %"}</span>'
        r["reading"] = f'<span class="dev {dev_class(rd.get("dev"))}">{esc(rd.get("modelled"))} → {esc(rd.get("dev"))}{"" if isinstance(rd.get("dev"), str) else " %"}</span>'
        rows.append(r)
    labels = {"result": "newest RESULT (it.300)", "reading": "newest citable reading (not a result)", "target_provenance": "target provenance",
              "simulated": "how it is simulated", "data_has": "data it has", "data_lacks": "data it lacks", "obtainable_from": "obtainable from"}
    # result/reading cells are pre-rendered HTML: bypass render_any escaping
    head = "".join(f"<th>{esc(labels.get(c, c))}</th>" for c in cols)
    body = []
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c)
            cells.append(f"<td>{v if c in ('result', 'reading') else render_any(v)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    t = f'<div class="scroll"><table class="modes"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    lead = f'Result: `{mt.get("result_run")}`. Reading: `{mt.get("reading_run")}`.'
    sup = mt.get("supply_fidelity", [])
    sup_html = table(sup, ["element", "real", "derived", "assumed", "absent"]) if sup else gap("supply-fidelity table")
    return section("modes", "The twelve modes, one row each", deviation_chart(modes) + t + "<h3>Supply fidelity — the physical layer the modes share</h3>" + sup_html, lead)


def findings_section(syn: dict) -> str:
    f = syn.get("findings", [])
    if not f:
        return section("findings", "Findings, ranked", gap("merged findings"))
    order = {"defect": 0, "risk": 1, "smell": 2}
    f = sorted(f, key=lambda x: (order.get(str(x.get("severity", "")).lower(), 9), x.get("rank", 99)))
    counts = {k: sum(1 for x in f if str(x.get("severity", "")).lower() == k) for k in order}
    rows = [dict(x, severity=f'<span class="sev {str(x.get("severity","")).lower()}">{esc(x.get("severity"))}</span>') for x in f]
    head = "".join(f"<th>{esc(c)}</th>" for c in ["#", "severity", "area", "where", "finding", "failure scenario"])
    body = "".join(
        f'<tr><td>{i+1}</td><td>{r["severity"]}</td><td>{esc(r.get("area"))}</td><td><code>{esc(r.get("file"))}{(":" + str(r["line"])) if r.get("line") else ""}</code></td><td>{md_inline(r.get("summary", ""))}</td><td>{md_inline(r.get("failure_scenario", ""))}</td></tr>'
        for i, r in enumerate(rows))
    lead = f'**{counts["defect"]} defects · {counts["risk"]} risks · {counts["smell"]} smells** at HEAD, deduplicated across the lanes and verified by sample (§8.7).'
    return section("findings", "Findings, ranked", f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>', lead)


def ledger_section(syn: dict) -> str:
    L = syn.get("ledger", [])
    if not L:
        return section("ledger", "The optimisation ledger", gap("merged optimisation ledger"))
    cols = ["kind", "where", "costs_today", "change", "saving", "touches_result", "guard"]
    labels = {"costs_today": "what it costs today", "saving": "expected saving", "touches_result": "touches a result?"}
    order = {"none": 0, "no": 0, "opens a family": 1, "family": 1, "unknown until run": 2}
    L = sorted(L, key=lambda r: order.get(str(r.get("touches_result", "")).lower()[:16], 3))
    by_kind = {}
    for r in L:
        by_kind[r.get("kind", "?")] = by_kind.get(r.get("kind", "?"), 0) + 1
    lead = " · ".join(f"**{v} {k}**" for k, v in by_kind.items()) + ". Rows that touch no result first; a change that opens a family is not cheaper than the arm it invalidates."
    return section("ledger", "The optimisation ledger", table(L, cols, labels), lead)


def ratings_section(syn: dict, code: dict | None) -> str:
    R = syn.get("ratings") or (code or {}).get("areas")
    if not R:
        return section("ratings", "Code quality by area", gap("ratings"))
    dims: list[str] = []
    for a, v in R.items():
        for dname in (v.get("ratings") or {}):
            if dname not in dims:
                dims.append(dname)
    head = "<th>area</th>" + "".join(f"<th>{esc(d)}</th>" for d in dims) + "<th>depth of read</th>"
    body = []
    for a, v in R.items():
        cells = []
        for d in dims:
            x = (v.get("ratings") or {}).get(d) or {}
            score = x.get("score", "—")
            ev = " · ".join(str(e) for e in (x.get("evidence") or []))
            cells.append(f'<td><span class="score s{score}" title="{esc(ev)}">{esc(score)}</span></td>')
        dor = v.get("depth_of_read", "")
        if isinstance(dor, dict):
            dor = "; ".join(f"{k}: {x}" for k, x in dor.items())
        body.append(f"<tr><td>{esc(a)}</td>{''.join(cells)}<td class=small>{esc(dor)}</td></tr>")
    return section("ratings", "Code quality by area", f'<div class="scroll"><table class="ratings"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div><p class=small>Hover a score for its two pieces of evidence. Ratings are never averaged across areas.</p>')


def list_section(sid, title, items, lead=""):
    if not items:
        return section(sid, title, gap(title.lower()), lead)
    return section(sid, title, "<ol class=recs>" + "".join(f"<li>{render_any(x)}</li>" for x in items) + "</ol>", lead)


def recs_section(syn: dict) -> str:
    R = syn.get("recommendations", [])
    if not R:
        return section("recommendations", "Recommendations", gap("recommendations"))
    items = []
    for r in R:
        rep = f' <span class="tag repeat">repeat ×{r["repeat_of"]}</span>' if r.get("repeat_of") else ""
        fam = f' <span class="tag fam">{esc(r.get("opens_family"))}</span>' if r.get("opens_family") else ""
        items.append(
            f'<li><b>{md_inline(r.get("what", ""))}</b>{rep}{fam}<br>{md_inline(r.get("why", ""))}'
            f'<div class=small>change: {md_inline(r.get("change", ""))} · guard: {md_inline(r.get("guard", ""))}</div></li>')
    return section("recommendations", "Recommendations, ranked", "<ol class=recs>" + "".join(items) + "</ol>",
                   "Ranked by what each would prevent or move × how cheap it is. A `repeat` tag marks one an earlier report already issued; the process audit counts them against this report too.")


def build(scratch: Path, out: Path) -> None:
    M = load(scratch, "metrics/metrics.json") or {}
    C = load(scratch, "metrics/code_metrics.json") or {}
    P = load(scratch, "metrics/performance.json") or {}
    code = load(scratch, "reviews/phase2_code.json")
    perf = load(scratch, "reviews/phase3_perf.json")
    hist = load(scratch, "reviews/phase4_history.json")
    docs = load(scratch, "reviews/phase5_docs.json")
    field = load(scratch, "research/field.json")
    fac = load(scratch, "research/factors.json")
    mt = load(scratch, "modes_table.json") or {}
    syn = load(scratch, "synthesis.json") or {}
    stamp = syn.get("stamp") or dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    head_sha = syn.get("head") or M.get("head", "")
    branch = syn.get("branch") or M.get("branch", "")
    date = syn.get("date") or dt.date.today().isoformat()

    sb = mt.get("modes", [])
    inside = [m["mode"] for m in sb if dev_class(m.get("result", {}).get("dev")) == "ok"]
    past = [m["mode"] for m in sb if dev_class(m.get("result", {}).get("dev")) == "stop"]
    fcount = {k: sum(1 for x in syn.get("findings", []) if str(x.get("severity", "")).lower() == k) for k in ("defect", "risk", "smell")}

    parts = []
    # masthead
    gate = syn.get("gate", {})
    parts.append(f'''<header class="mast">
<p class="eyebrow">city-digital-twin · Newcastle study · project report</p>
<h1>{esc(syn.get("title", "Project report"))}</h1>
<p class="meta"><span>{esc(date)}</span><span>HEAD <code>{esc(head_sha[:7])}</code></span><span>branch <code>{esc(branch)}</code></span><span>gate <b class="{ 'ok' if str(gate.get('result','')).upper().startswith('PASS') else 'stop'}">{esc(gate.get("result", "unknown"))}</b></span></p>
{para(syn.get("verdict", ""))}
</header>''')
    # tiles
    parts.append(tiles([
        ("modes inside 10 % at the newest result", f"{len(inside)} / 12", ", ".join(inside) or "none"),
        ("past the 20 % stop bar", f"{len(past)}", ", ".join(past)),
        ("findings at HEAD", f'{fcount["defect"]} · {fcount["risk"]} · {fcount["smell"]}', "defects · risks · smells"),
        ("registry fields", f'{syn.get("registry_fields", "—")}', "each with provenance and a sweep or a held-fixed rule"),
        ("manifest files", f'{syn.get("manifest_files", "—")}', "hash, rows, producer, source, licence, date"),
        ("machine hours, all runs", f'{syn.get("machine_hours", "—")}', syn.get("machine_hours_note", "")),
        ("open issues", f'{syn.get("open_issues", "—")}', syn.get("open_issues_note", "")),
        ("reports before this one", f'{syn.get("reports_before", "—")}', syn.get("reports_note", "")),
    ]))
    # method
    parts.append(section("method", "Method", para(syn.get("method", "")) + (render_any(syn.get("method_table")) if syn.get("method_table") else "")))
    # goal table
    parts.append(section("goal", "Milestones against the goal", table(syn.get("goal_table", []), ["requirement", "state", "evidence", "decided_by"]) if syn.get("goal_table") else gap("goal table")))
    # modes
    parts.append(modes_section(mt))
    # timeline
    if hist:
        tl = stage_strip(hist.get("stage_strip", {}))
        ms = hist.get("milestones", [])
        ms_html = render_any(ms) if ms else gap("milestone table")
        und = hist.get("undated", [])
        cad = hist.get("cadence", {})
        parts.append(section("timeline", "The timeline from day 0",
                             tl + "<h3>Milestones</h3>" + ms_html + ("<h3>Undated</h3>" + render_any(und) if und else "") +
                             "<h3>Cadence</h3>" + render_any(cad) + "<h3>Narrative</h3>" + para(hist.get("narrative", "")) if isinstance(hist.get("narrative"), str) else render_any(hist.get("narrative"))))
    else:
        parts.append(section("timeline", "The timeline from day 0", gap("history lane")))
    # anatomy
    inv = M.get("inventory", {})
    anatomy = render_any({k: inv.get(k) for k in ("tracked_files", "files_on_disk", "tracked_by_top_dir", "lines_by_extension") if k in inv})
    growth = M.get("growth")
    if isinstance(growth, list) and growth:
        gk = [k for k in ("registry_fields", "manifest_rows", "code_lines") if all(isinstance(g.get(k), (int, float)) for g in growth[-12:])]
        if gk:
            anatomy += "<h3>Growth over the last merges</h3>" + series_chart(growth[-12:], "merge", gk, "Growth series", ["#0B5FA5", "#7a5c00", "#5b5b5b"])
    churn = (M.get("commits") or {}).get("churn_hotspots", [])[:15]
    if churn:
        anatomy += "<h3>Churn hotspots</h3>" + render_any(churn)
    parts.append(section("anatomy", "Repository anatomy", anatomy))
    # code quality
    parts.append(ratings_section(syn, code))
    if code:
        simp = code.get("simplification", [])
        ans = code.get("answers", {})
        body = ""
        if simp:
            body += "<h3>The simplification lens — could each component be greatly simpler?</h3>" + table(simp, [c for c in ("module", "does", "simplest", "gap", "lines_now", "lines_simplest_estimate") if any(c in s for s in simp)])
        if ans:
            body += "<h3>Three questions</h3>" + render_any(ans)
        per_area = code.get("areas", {})
        if per_area:
            body += "<h3>Per area</h3>"
            for a, v in per_area.items():
                body += f"<details><summary>{esc(a)}</summary>{render_any({k: x for k, x in v.items() if k not in ('ratings',)})}</details>"
        parts.append(section("code", "Code: every area read", body or gap("code lane detail")))
    parts.append(findings_section(syn))
    parts.append(ledger_section(syn))
    # performance
    if perf:
        body = ""
        for k in ("reference_runs", "iteration_phases", "mobsim", "replanning", "writing", "jvm", "python", "build", "warm_start"):
            if perf.get(k) is not None:
                body += f"<h3>{esc(k.replace('_', ' '))}</h3>" + render_any(perf[k])
        body += "<h3>Ranked changes</h3>" + render_any(perf.get("ranked_changes"))
        body += "<h3>Verdict on the 250-iteration horizon</h3>" + (para(perf["verdict"]) if isinstance(perf.get("verdict"), str) else render_any(perf.get("verdict")))
        body += "<h3>Since the previous pass</h3>" + render_any(perf.get("delta_since_previous"))
        parts.append(section("perf", "The simulator performance pass", body))
    else:
        parts.append(section("perf", "The simulator performance pass", gap("performance lane")))
    # testing and CI
    tests = C.get("tests", {})
    ci = (M.get("github") or {}).get("ci")
    parts.append(section("testing", "Testing and CI", render_any({
        "test files": tests.get("test_files"), "test functions": tests.get("test_functions"),
        "src modules": _count(tests.get("src_modules")), "imported by a unit test": _count(tests.get("src_modules_imported_by_a_test")),
        "uncovered src modules": tests.get("uncovered_src_modules"), "CI": ci if not isinstance(ci, list) else ci[:20]})))
    # history: PRs, commits
    if hist:
        parts.append(section("prs", "The pull-request ledger", render_any(hist.get("pr_stats")) + render_any(hist.get("pr_quality")) +
                             "<details><summary>One block per PR</summary>" + render_any(hist.get("pr_ledger")) + "</details>"))
        parts.append(section("commits", "The commit log", render_any(hist.get("commits")) + "<h3>Direct commits to the default branch</h3>" + render_any(hist.get("direct_to_main"))))
    # issues
    if docs and docs.get("issues"):
        I = docs["issues"]
        body = "<h3>Past</h3>" + render_any(I.get("past_stats")) + "<details><summary>Every closed issue</summary>" + render_any(I.get("past")) + "</details>"
        body += "<h3>Present</h3>" + render_any(I.get("present")) + "<h3>Overtaken by the record</h3>" + render_any(I.get("overtaken"))
        body += "<h3>Upcoming — risks that are not issues yet</h3>" + render_any(I.get("upcoming"))
        parts.append(section("issues", "The issue ledger: past, present, upcoming", body))
    # runs
    ag = P.get("aggregates", {})
    parts.append(section("runs", "Runs on disk and their cost", render_any({k: ag.get(k) for k in ag if k in ("machine_hours_by_family", "machine_hours_by_status", "pace_by_fraction", "bytes_on_disk", "runs_by_status", "totals")}) or render_any(ag)))
    # field
    if field:
        body = render_any(field.get("counts") or field.get("validation_ladder")) if (field.get("counts") or field.get("validation_ladder")) else ""
        for k in ("what_the_comparison_says", "what_each_does_best_that_we_lack", "data_acquired_answer", "physical_fidelity_answer", "warm_start_answer", "ours", "delta"):
            if field.get(k) is not None:
                body += f"<h3>{esc(k.replace('_', ' '))}</h3>" + render_any(field[k])
        projs = field.get("projects", [])
        if projs:
            cols = [c for c in ("name", "engine", "city", "validation_rung", "best_published_fit", "status", "what_it_does_best", "data_acquired_per_mode", "physical_fidelity", "last_verified") if any(c in p for p in projs)]
            body += "<details><summary>Every project row (" + str(len(projs)) + ")</summary>" + table(projs, cols) + "</details>"
        plats = field.get("platforms", [])
        if plats:
            body += "<details><summary>Platforms (" + str(len(plats)) + ")</summary>" + render_any(plats) + "</details>"
        parts.append(section("field", "The project in its field", body))
    else:
        parts.append(section("field", "The project in its field", gap("field lane")))
    # factors
    if fac:
        body = render_any(fac.get("counts_by_status")) + render_any(fac.get("counts_by_layer"))
        body += "<h3>Would move the scoreboard — ranked</h3>" + render_any(fac.get("ranked_would_move"))
        body += "<h3>Delta since the previous pass</h3>" + render_any(fac.get("delta_since_previous_pass"))
        rows = fac.get("rows", [])
        if rows:
            cols = [c for c in ("id", "layer", "factor", "status", "proof", "would_move", "what_research_says", "source_url", "last_verified") if any(c in r for r in rows)]
            body += "<details><summary>Every factor row (" + str(len(rows)) + ")</summary>" + table(rows, cols) + "</details>"
        parts.append(section("factors", "The factor ledger", body))
    else:
        parts.append(section("factors", "The factor ledger", gap("factor lane")))
    # documents
    if docs:
        body = ""
        for k in ("layering", "budget_check", "frozen_banners", "record_numbering", "stale_stamps", "controls", "doc_simplification", "link_check"):
            if docs.get(k) is not None:
                body += f"<h3>{esc(k.replace('_', ' '))}</h3>" + render_any(docs[k])
        body += "<h3>Placement and currency</h3>" + render_any(docs.get("placement"))
        body += f"<h3>Contradictions between living documents ({len(docs.get('contradictions', []))})</h3>" + render_any(docs.get("contradictions"))
        body += f"<h3>Rules stated as advice that nothing enforces ({len(docs.get('unenforced_rules', []))} examined)</h3>" + render_any(docs.get("unenforced_rules"))
        parts.append(section("docs", "The document and process layer", body))
    # in-flight
    parts.append(section("inflight", "In-flight work seen in the tree", para(syn.get("in_flight", "The tree was clean at the commit read."))))
    # since last + process audit
    since = syn.get("since_last_report", "")
    body = para(since) if isinstance(since, str) else render_any(since)
    if hist and hist.get("report_audit"):
        ra = hist["report_audit"]
        body += "<h3>The report process itself</h3>"
        reps = ra.get("reports", [])
        if reps:
            pts_ = [{"report": str(r.get("date", r.get("file", "")))[:10], "recommendations": r.get("n_recs"), "findings": r.get("n_findings")} for r in reps]
            body += series_chart(pts_, "report", ["recommendations", "findings"], "Per report", ["#0B5FA5", "#7a5c00"])
            body += table([{k: r.get(k) for k in ("file", "date", "head", "n_recs", "n_findings", "size_bytes", "taken", "overtaken", "repeated", "open")} for r in reps],
                          ["file", "date", "head", "n_recs", "n_findings", "size_bytes", "taken", "overtaken", "repeated", "open"])
        for k in ("findings_rereported", "between_reports", "verdict", "still_open_from_last"):
            if ra.get(k) is not None:
                body += f"<h3>{esc(k.replace('_', ' '))}</h3>" + (para(ra[k]) if isinstance(ra[k], str) else render_any(ra[k]))
        body += "<details><summary>Every recommendation of every previous report, classified</summary>" + render_any([{"report": r.get("date"), "recs": r.get("recs")} for r in reps]) + "</details>"
        if hist.get("goal_alignment") is not None:
            body += "<h3>Alignment with the goal</h3>" + render_any(hist["goal_alignment"])
    parts.append(section("since", "Since the last report, and the report process itself", body))
    parts.append(recs_section(syn))
    # appendix
    parts.append(section("appendix", "Appendix", para(syn.get("appendix", "")) + "<h3>Own verifications (§8.7)</h3>" + (render_any(syn.get("verifications")) if syn.get("verifications") else "") ))

    # embedded data
    def trim(v, depth=0):
        if isinstance(v, list):
            return [trim(x, depth + 1) for x in v[:MAX_EMBED_LIST]]
        if isinstance(v, dict):
            return {k: trim(x, depth + 1) for k, x in v.items()}
        return v
    data = {
        "head": head_sha, "branch": branch, "date": date, "stamp": stamp,
        "previous_report": syn.get("previous_report"), "gate": gate,
        "scoreboard": [{"mode": m["mode"], "result": m.get("result"), "reading": m.get("reading")} for m in sb],
        "metrics_summary": {"inventory": {k: inv.get(k) for k in ("tracked_files", "files_on_disk")}, "commits": {k: (M.get("commits") or {}).get(k) for k in ("total", "merges", "first_date", "last_date")},
                             "python": C.get("python", {}).get("summary"), "java": C.get("java", {}).get("summary"), "tests": {k: tests.get(k) for k in ("test_files", "test_functions")}},
        "findings": syn.get("findings", []), "ledger": syn.get("ledger", []), "ratings": syn.get("ratings") or (code or {}).get("areas"),
        "modes": mt, "perf": trim({k: perf.get(k) for k in ("ranked_changes", "verdict", "jvm", "warm_start")} if perf else None),
        "history_summary": trim({k: hist.get(k) for k in ("pr_stats", "cadence", "milestones", "report_audit", "goal_alignment")} if hist else None),
        "docs": trim({k: docs.get(k) for k in ("contradictions", "unenforced_counts", "placement", "issues")} if docs else None),
        "field": trim({k: field.get(k) for k in ("counts", "validation_ladder", "gaps", "ours", "delta")} if field else None),
        "factors": trim({k: fac.get(k) for k in ("counts_by_status", "counts_by_layer", "ranked_would_move", "per_mode_data", "delta_since_previous_pass")} if fac else None),
        "recommendations": syn.get("recommendations", []),
    }
    embed = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    toc = "".join(f'<a href="#{sid}">{esc(t)}</a>' for sid, t in re.findall(r'<section id="([^"]+)"><h2>([^<]+)</h2>', "".join(parts)))
    doc = f'''<!doctype html>
<html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(syn.get("title", "Project report"))}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>{CSS}</style></head>
<body><nav class="toc">{toc}</nav><main>{"".join(parts)}</main>
<script type="application/json" id="report-data">{embed}</script>
</body></html>'''
    out.write_text(doc, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB), {len(parts)} sections, findings {sum(fcount.values())}, recommendations {len(syn.get('recommendations', []))}")


CSS = """
:root{--bg:#f5f7f8;--surface:#fcfcfb;--ink:#1b2430;--ink2:#4a5561;--muted:#7a8590;--line:#d9dee3;--accent:#0b5fa5;--accent-ink:#0b5fa5;
--ok:#0ca30c;--warn:#ec835a;--stop:#d03b3b;--code-bg:#eef2f5;--span:#9ec5e8;--ev:#0b5fa5}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1519;--surface:#1a1a19;--ink:#e6eaee;--ink2:#b7c0c8;--muted:#8a949d;--line:#2c353d;--accent:#5aa4e6;--accent-ink:#8cc2f0;--code-bg:#1f272e;--span:#2f5f86;--ev:#8cc2f0}}
:root[data-theme="dark"]{--bg:#0f1519;--surface:#1a1a19;--ink:#e6eaee;--ink2:#b7c0c8;--muted:#8a949d;--line:#2c353d;--accent:#5aa4e6;--accent-ink:#8cc2f0;--code-bg:#1f272e;--span:#2f5f86;--ev:#8cc2f0}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Source Sans 3","Segoe UI",system-ui,sans-serif;font-size:16px;line-height:1.55;padding-block:0 4rem;padding-inline:clamp(16px,4vw,48px)}
main{max-width:1180px;margin:0 auto}
h1{font-family:"Source Serif 4",Georgia,serif;font-weight:600;font-size:clamp(1.7rem,3.2vw,2.4rem);line-height:1.15;text-wrap:balance;margin:.3rem 0 .8rem}
h2{font-family:"Source Serif 4",Georgia,serif;font-weight:600;font-size:1.45rem;margin:2.6rem 0 .6rem;padding-top:.6rem;border-top:2px solid var(--line);text-wrap:balance}
h3{font-family:"Source Sans 3",sans-serif;font-weight:600;font-size:1.05rem;margin:1.6rem 0 .4rem;color:var(--ink2);letter-spacing:.01em}
p{max-width:72ch}p.lead{color:var(--ink2);font-size:1.02rem}
.mast{padding-block:2.2rem 1rem}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;color:var(--muted);margin:0}
.meta{display:flex;flex-wrap:wrap;gap:1.2rem;color:var(--ink2);font-size:.92rem;margin:0 0 1rem}
.meta b.ok{color:var(--ok)}.meta b.stop{color:var(--stop)}
code{font-family:"JetBrains Mono",Consolas,monospace;font-size:.86em;background:var(--code-bg);padding:.05em .3em;border-radius:3px}
.num{font-variant-numeric:tabular-nums}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:1rem 0 .5rem}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:.8rem .9rem}
.tile-v{font-family:"JetBrains Mono",monospace;font-size:1.5rem;font-weight:500;font-variant-numeric:tabular-nums;color:var(--accent-ink)}
.tile-k{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-top:.2rem}.tile-s{font-size:.85rem;color:var(--ink2);margin-top:.3rem}
.toc{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:.2rem .9rem;padding:.5rem 0;font-size:.82rem}
.toc a{color:var(--ink2);text-decoration:none}.toc a:hover,.toc a:focus{color:var(--accent-ink);text-decoration:underline}
.scroll{overflow-x:auto;max-width:100%;margin:.6rem 0}
table{border-collapse:collapse;font-size:.9rem;min-width:100%}th,td{text-align:left;vertical-align:top;padding:.45rem .6rem;border-bottom:1px solid var(--line)}
th{font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;background:var(--surface);position:sticky;top:0}
td{max-width:46ch}td ul,td dl{margin:0;padding-left:1.1rem}td dl.kv{padding-left:0}
table.modes td{max-width:34ch;font-size:.85rem}
dl.kv{display:grid;grid-template-columns:max-content 1fr;gap:.25rem 1rem;margin:.4rem 0}dl.kv dt{color:var(--muted);font-size:.85rem}dl.kv dd{margin:0}
.dev{font-family:"JetBrains Mono",monospace;font-size:.85em;padding:.1em .35em;border-radius:3px;white-space:nowrap}
.dev.ok{background:color-mix(in srgb,var(--ok) 16%,transparent)}.dev.warn{background:color-mix(in srgb,var(--warn) 22%,transparent)}.dev.stop{background:color-mix(in srgb,var(--stop) 18%,transparent)}
.sev{font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;padding:.1em .4em;border-radius:3px;color:#fff}.sev.defect{background:var(--stop)}.sev.risk{background:#a35a00}.sev.smell{background:#5b6770}
.score{display:inline-block;min-width:1.8em;text-align:center;font-family:"JetBrains Mono",monospace;padding:.05em .3em;border-radius:3px;background:var(--code-bg);cursor:help}
.tag{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;padding:.05em .4em;border-radius:3px;margin-left:.3rem}.tag.repeat{background:color-mix(in srgb,var(--warn) 30%,transparent)}.tag.fam{background:color-mix(in srgb,var(--accent) 18%,transparent)}
ol.recs li{margin:.7rem 0;max-width:80ch}.small{font-size:.85rem;color:var(--ink2)}.muted{color:var(--muted)}
.gap{border-left:3px solid var(--warn);padding-left:.6rem;color:var(--ink2)}
details{border:1px solid var(--line);border-radius:6px;padding:.4rem .8rem;margin:.6rem 0;background:var(--surface)}summary{cursor:pointer;font-weight:600;color:var(--ink2)}
svg.chart{width:100%;height:auto;max-width:100%;display:block;margin:.6rem 0;background:var(--surface);border:1px solid var(--line);border-radius:6px}
svg .grid{stroke:var(--line);stroke-width:1}svg .axis{stroke:var(--ink2);stroke-width:1.2}svg .tick{fill:var(--muted);font-size:11px;font-family:"JetBrains Mono",monospace}
svg .lab{fill:var(--ink);font-size:12px;font-family:"Source Sans 3",sans-serif}svg .val{fill:var(--ink);font-size:11px;font-family:"JetBrains Mono",monospace}
svg .span{fill:var(--span)}svg .ev{fill:var(--ev)}
a{color:var(--accent-ink)}a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media (max-width:640px){td{max-width:60vw}.toc{font-size:.78rem}}
"""

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
