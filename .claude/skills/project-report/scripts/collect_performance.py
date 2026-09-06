"""The mechanical half of the simulator performance pass.

Reads what every run already left behind - never launches, never recompiles,
never writes into results/ - and writes OUT_DIR/performance.json: where an
iteration's wall time goes, how the pace scales with the sample fraction and
the thread count, what the JVM used, what each run wrote to disk, and what all
of it cost in machine hours. The report's performance section quotes this file
and nothing typed.

    python .claude/skills/project-report/scripts/collect_performance.py OUT_DIR
    python .claude/skills/project-report/scripts/collect_performance.py OUT_DIR --no-sizes   # skip the disk walk

Per run (results/raw/<run>/ and results/processed/<run>/ where present)
  record       _run.json / _meta.json: status, completion, family (from
               results/INDEX.csv), fraction, iterations reached, threads, Xmx,
               wall seconds, median iteration seconds, persons kept
  stopwatch    output/stopwatch.csv: median seconds per controller phase over
               the run's iterations (replanning, beforeMobsimListeners, dump
               all plans, prepareForMobsim, mobsim, afterMobsimListeners,
               scoring, iterationEndsListeners) and each phase's share of the
               iteration; the same again for the innovation-off tail if any
  memory       matsim.log MemoryObserver lines: peak used RAM and the JVM's
               max heap - read from the HEAD and TAIL of the log only
               (LOG_HEAD_BYTES / LOG_TAIL_BYTES), because a 25 % arm's log
               runs to tens of GiB and reading it whole is the kind of cost
               this pass exists to find
  throughput   output/telemetry.jsonl: departures per iteration and per wall
               second, stuck agents
  outputs      which iterations dumped events / plans / linkstats, the bytes
               each dump costs, the run directory's size
  config       every RUN.* value in _config.json (write intervals, threads,
               qsim settings, gate and monitor cadence)

Aggregates
  pace by (fraction, threads); pace over time by family at each fraction;
  phase shares for the longest run at each fraction; machine hours by family
  and by status (the hours spent on runs that died); bytes on disk by status.
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
from pathlib import Path

LOG_HEAD_BYTES = 4 * 1024 * 1024
LOG_TAIL_BYTES = 16 * 1024 * 1024
MEM_LINE = re.compile(r"MemoryObserver:\d+ used RAM: (\d+) MB\s+free: (\d+) MB\s+total: (\d+) MB\s+max: (\d+) MB")
MAX_MEM = re.compile(r"max\. Memory: ([\d.]+)MB")
INNOV_OFF = re.compile(r"fractionOfIterationsToDisableInnovation")
PHASES = ("iterationStartsListeners", "replanning", "dump all plans", "beforeMobsimListeners", "prepareForMobsim",
          "mobsim", "afterMobsimListeners", "scoring", "iterationEndsListeners", "iteration")


def sh(args: list[str]) -> str:
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def _hms(s: str) -> float | None:
    if not s:
        return None
    try:
        h, m, sec = s.split(":")
        return int(h) * 3600 + int(m) * 60 + int(sec)
    except ValueError:
        return None


def _json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stopwatch(p: Path, innovation_off_at: int | None) -> dict | None:
    """Median seconds per phase and its share of the iteration, iteration 0 excluded."""
    try:
        rows = [l.rstrip("\n").split(";") for l in p.open(encoding="utf-8", errors="ignore") if l.strip()]
    except OSError:
        return None
    if len(rows) < 3:
        return None
    header = rows[0]
    # the duration columns follow the empty column that separates timestamps from durations
    try:
        sep = len(header) - 1 - header[::-1].index("")
    except ValueError:
        return None
    cols = {name: i for i, name in enumerate(header) if i > sep}
    per_phase = collections.defaultdict(list)
    tail = collections.defaultdict(list)
    n_iter = 0
    for r in rows[1:]:
        try:
            it = int(r[0])
        except ValueError:
            continue
        if it == 0 or len(r) <= sep:
            continue
        n_iter += 1
        for name, i in cols.items():
            v = _hms(r[i]) if i < len(r) else None
            if v is None:
                continue
            per_phase[name].append(v)
            if innovation_off_at is not None and it >= innovation_off_at:
                tail[name].append(v)

    def summarise(d):
        it = statistics.median(d["iteration"]) if d.get("iteration") else None
        out = {}
        for name in PHASES:
            if d.get(name):
                med = statistics.median(d[name])
                out[name] = dict(median_s=med, max_s=max(d[name]), share=round(med / it, 3) if it else None)
        return out

    return dict(iterations_timed=n_iter, phases=summarise(per_phase),
                innovation_off_tail=summarise(tail) if tail else None,
                slowest_iterations=sorted(((v, k + 1) for k, v in enumerate(per_phase.get("iteration", []))), reverse=True)[:5])


def memory(log: Path) -> dict | None:
    try:
        size = log.stat().st_size
    except OSError:
        return None
    peak = 0
    max_heap = None
    samples = 0
    with log.open("rb") as f:
        chunks = [f.read(LOG_HEAD_BYTES)]
        if size > LOG_HEAD_BYTES + LOG_TAIL_BYTES:
            f.seek(size - LOG_TAIL_BYTES)
            chunks.append(f.read())
        elif size > LOG_HEAD_BYTES:
            chunks.append(f.read())
    for c in chunks:
        text = c.decode("utf-8", errors="ignore")
        for m in MEM_LINE.finditer(text):
            samples += 1
            peak = max(peak, int(m.group(1)))
        mm = MAX_MEM.search(text)
        if mm and max_heap is None:
            max_heap = float(mm.group(1))
    return dict(log_bytes=size, log_bytes_scanned=min(size, LOG_HEAD_BYTES + LOG_TAIL_BYTES), memory_samples=samples,
                peak_used_mb=peak or None, max_heap_mb=max_heap,
                note="peak is over the scanned head and tail of the log only" if size > LOG_HEAD_BYTES + LOG_TAIL_BYTES else None)


def telemetry(p: Path) -> dict | None:
    if not p.exists():
        return None
    walls, deps, stuck = [], [], []
    try:
        with p.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if "wall_s" in d and "departures" in d:
                    walls.append(d["wall_s"])
                    deps.append(d["departures"].get("total", 0))
                    stuck.append(d.get("stuck", {}).get("total", 0))
    except OSError:
        return None
    if not walls:
        return None
    rate = [dp / w for dp, w in zip(deps, walls) if w]
    return dict(iterations=len(walls), departures_median=statistics.median(deps), stuck_median=statistics.median(stuck),
                departures_per_wall_second_median=round(statistics.median(rate), 1) if rate else None)


def outputs(run: Path, with_sizes: bool) -> dict:
    iters = run / "output" / "ITERS"
    dumps = collections.defaultdict(list)
    dump_bytes = collections.Counter()
    if iters.is_dir():
        for d in sorted(iters.iterdir()):
            m = re.match(r"it\.(\d+)$", d.name)
            if not m:
                continue
            it = int(m.group(1))
            try:
                for f in d.iterdir():
                    kind = re.sub(r"^\d+\.", "", f.name)
                    dumps[kind].append(it)
                    if with_sizes:
                        dump_bytes[kind] += f.stat().st_size
            except OSError:
                pass
    total = None
    if with_sizes:
        total = 0
        for dirpath, _, files in os.walk(run):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass
    return dict(dumped_iterations={k: (len(v), v[:3] + (["..."] if len(v) > 3 else [])) for k, v in sorted(dumps.items())},
                dump_bytes_by_kind={k: v for k, v in dump_bytes.most_common()} if with_sizes else None,
                run_dir_bytes=total)


def run_config(p: Path) -> dict:
    d = _json(p) or {}
    vals = d.get("values", {})
    return {k: v for k, v in vals.items() if k.startswith("RUN.")}


def one_run(run: Path, index_row: dict | None, with_sizes: bool) -> dict:
    rec = _json(run / "_run.json") or {}
    meta = _json(run / "_meta.json") or {}
    cfg = run_config(run / "_config.json")
    innovation_off = None
    for k, v in cfg.items():
        if k.endswith("disable_innovation_fraction") or k.endswith("fractionOfIterationsToDisableInnovation"):
            try:
                innovation_off = int(float(v) * int(rec.get("iterations") or meta.get("iterations") or 0))
            except (TypeError, ValueError):
                pass
    prog = _json(run / "_progress.json") or {}
    if prog.get("innovation_off_at"):
        innovation_off = prog["innovation_off_at"]
    return dict(
        name=run.name, family=(index_row or {}).get("family"), cls=(index_row or {}).get("class"),
        status=meta.get("status") or (index_row or {}).get("status"), completion=rec.get("completion"),
        fraction=rec.get("fraction", meta.get("fraction")), iterations_declared=rec.get("iterations", meta.get("iterations")),
        reached_iteration=rec.get("reached_iteration"), threads=rec.get("threads", meta.get("threads")),
        xmx=rec.get("xmx", meta.get("xmx")), wall_s=rec.get("wall_s", meta.get("wall_s")),
        median_iteration_s=rec.get("median_iteration_s"), persons_kept=rec.get("persons_kept"),
        started=meta.get("started"), ended=meta.get("ended"), cause=(meta.get("cause") or "")[:160] or None,
        stopwatch=stopwatch(run / "output" / "stopwatch.csv", innovation_off), memory=memory(run / "matsim.log"),
        telemetry=telemetry(run / "output" / "telemetry.jsonl"), outputs=outputs(run, with_sizes), config=cfg,
    )


def aggregates(runs: list[dict]) -> dict:
    timed = [r for r in runs if r.get("median_iteration_s") and (r.get("reached_iteration") or r.get("iterations_declared") or 0) >= 5]
    by_ft = collections.defaultdict(list)
    for r in timed:
        by_ft[(r["fraction"], r["threads"])].append(r["median_iteration_s"])
    pace = [dict(fraction=f, threads=t, runs=len(v), median_iteration_s=statistics.median(v), min_s=min(v), max_s=max(v))
            for (f, t), v in sorted(by_ft.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1] or 0))]
    by_family = collections.defaultdict(list)
    for r in timed:
        by_family[(r["family"], r["fraction"])].append((r["started"], r["median_iteration_s"], r["name"]))
    pace_over_time = [dict(family=f, fraction=fr, runs=sorted(v)) for (f, fr), v in by_family.items()]
    pace_over_time.sort(key=lambda d: (d["fraction"] or 0, d["runs"][0][0] or ""))
    hours = collections.defaultdict(float)
    hours_status = collections.defaultdict(float)
    bytes_status = collections.Counter()
    for r in runs:
        h = (r.get("wall_s") or 0) / 3600
        hours[r.get("family") or "?"] += h
        hours_status[r.get("status") or "?"] += h
        if r["outputs"].get("run_dir_bytes"):
            bytes_status[r.get("status") or "?"] += r["outputs"]["run_dir_bytes"]
    longest = {}
    for r in runs:
        if r.get("stopwatch") and r["stopwatch"]["iterations_timed"] >= 5:
            fr = r["fraction"]
            if fr not in longest or r["stopwatch"]["iterations_timed"] > longest[fr]["stopwatch"]["iterations_timed"]:
                longest[fr] = r
    phase_shares = {str(fr): dict(run=r["name"], iterations=r["stopwatch"]["iterations_timed"], phases=r["stopwatch"]["phases"],
                                  innovation_off_tail=r["stopwatch"]["innovation_off_tail"]) for fr, r in longest.items()}
    peak = [dict(peak_used_mb=r["memory"]["peak_used_mb"], max_heap_mb=r["memory"]["max_heap_mb"], run=r["name"])
            for r in runs if r.get("memory") and r["memory"].get("peak_used_mb")]
    peak.sort(key=lambda d: -d["peak_used_mb"])
    return dict(runs_total=len(runs), runs_timed=len(timed), pace_by_fraction_and_threads=pace, pace_over_time_by_family=pace_over_time,
                phase_shares_longest_run_per_fraction=phase_shares,
                machine_hours_by_family={k: round(v, 1) for k, v in sorted(hours.items())},
                machine_hours_by_status={k: round(v, 1) for k, v in hours_status.items()},
                machine_hours_total=round(sum(hours.values()), 1),
                bytes_on_disk_by_status=dict(bytes_status), bytes_on_disk_total=sum(bytes_status.values()) or None,
                peak_memory_top=peak[:5], host_cpu_count=os.cpu_count())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    out_dir = Path(argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    root = Path(sh(["git", "rev-parse", "--show-toplevel"]).strip() or ".")
    os.chdir(root)
    with_sizes = "--no-sizes" not in argv
    index = {}
    ip = root / "results" / "INDEX.csv"
    if ip.exists():
        index = {r["name"]: r for r in csv.DictReader(ip.open(encoding="utf-8"))}
    runs, seen = [], {}
    # raw/ holds the bulk (stopwatch, log, telemetry); processed/ holds the same run's permanent findings.
    # A run present in both is read once, from raw/, so no hour is counted twice.
    for store in ("raw", "processed"):
        base = root / "results" / store
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and (d / "_meta.json").exists():
                key = re.sub(r"^(aborted|failed)_", "", d.name)
                if key in seen:
                    seen[key]["also_in"] = store
                    continue
                print(f"{store}/{d.name}", flush=True)
                r = one_run(d, index.get(d.name) or index.get(key), with_sizes)
                r["store"] = store
                r["family"] = r["family"] or "not in INDEX.csv"
                seen[key] = r
                runs.append(r)
    m = dict(head=sh(["git", "rev-parse", "--short", "HEAD"]).strip(), results_present=bool(runs),
             aggregates=aggregates(runs) if runs else None, runs=runs,
             build_timing="none recorded: no producing script writes its wall time into a report or the manifest")
    (out_dir / "performance.json").write_text(json.dumps(m, indent=1, default=str), encoding="utf-8")
    print(f"wrote {out_dir / 'performance.json'}: {len(runs)} runs")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
