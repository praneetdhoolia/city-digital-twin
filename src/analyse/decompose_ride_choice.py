"""Decompose where ride plans die in a completed run.

Reads a finished run directory (its output_persons.csv.gz and
output_plans.xml.gz) and classifies every choice-eligible person by what
happened to ride in their final plan memory:

  excluded    rideAvail=never - ride is structurally unavailable to them
  selected    the selected plan contains at least one ride leg
  scored_out  a plan in memory contains ride, but a non-ride plan won -
              the score gap to the best ride plan is measured
  absent      ride is available but no plan in memory contains it (either
              never proposed, or proposed and evicted from the 5-plan
              memory before the innovation cutoff)

After the innovation cutoff MATSim creates and evicts no plans, so the
final memory is the standing choice set of the converged run; the gap
distribution over `scored_out` is the direct measurement of how far the
ride alternative sits below the winner, and the flip curve states what a
uniform per-leg utility shift would first-order re-select. It is a
diagnostic, not a prediction: re-selection moves the equilibrium, so any
chosen shift must be validated by a run.

Usage:
    python src/analyse/decompose_ride_choice.py results/<run-dir>

Writes `_ride_choice.json` into the run directory and prints the report.
No city value is read; everything comes from the run's own records.
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

# Reporting grid for the flip curve (a presentation choice, not a model
# input: the JSON carries the full gap list so any other grid can be read
# off it without re-running).
FLIP_GRID = [round(0.25 * i, 2) for i in range(0, 33)]  # 0.00 .. 8.00 utils


def load_persons(out_dir: Path) -> dict[str, dict]:
    persons = {}
    with gzip.open(out_dir / "output_persons.csv.gz", "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            persons[row["person"]] = {
                "sub": row.get("subpopulation", ""),
                "ride_avail": row.get("rideAvail", ""),
                "car_avail": row.get("carAvail", ""),
                "licensed": row.get("hasLicense", ""),
                "locked": row.get("lockedMode", "") or "",
            }
    return persons


def stream_plans(plans_path: Path):
    """Yield (person_id, plans) where plans is a list of
    (selected, score, n_ride_legs, selected_modes)."""
    with gzip.open(plans_path, "rb") as fh:
        context = ET.iterparse(fh, events=("start", "end"))
        _, root = next(context)
        pid = None
        plans = []
        cur = None
        for event, elem in context:
            tag = elem.tag
            if event == "start":
                if tag == "person":
                    pid = elem.get("id")
                    plans = []
                elif tag == "plan":
                    score = elem.get("score")
                    cur = {
                        "selected": elem.get("selected") == "yes",
                        "score": float(score) if score not in (None, "") else None,
                        "ride_legs": 0,
                        "modes": set(),
                    }
                elif tag == "leg" and cur is not None:
                    mode = elem.get("mode")
                    cur["modes"].add(mode)
                    if mode == "ride":
                        cur["ride_legs"] += 1
            else:  # end
                if tag == "plan" and cur is not None:
                    plans.append(cur)
                    cur = None
                elif tag == "person":
                    yield pid, plans
                    root.clear()  # free the finished subtree


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    run_dir = Path(sys.argv[1])
    out_dir = run_dir / "output"
    persons = load_persons(out_dir)

    counts = Counter()
    gaps = []  # (gap, gap_per_leg, licensed_with_car: bool)
    absent_by_group = Counter()
    scored_out_by_group = Counter()
    selected_mode_of_nonriders = Counter()
    n_eligible = 0

    for pid, plans in stream_plans(out_dir / "output_plans.xml.gz"):
        attrs = persons.get(pid)
        if attrs is None or attrs["sub"] != "person" or attrs["locked"]:
            continue
        if attrs["ride_avail"] == "never":
            counts["excluded"] += 1
            continue
        n_eligible += 1
        sel = next((p for p in plans if p["selected"]), None)
        if sel is None or sel["score"] is None:
            counts["unscored"] += 1
            continue
        group = (
            "licensed_car"
            if (attrs["licensed"] == "yes" and attrs["car_avail"] == "always")
            else "carless"
        )
        if sel["ride_legs"] > 0:
            counts["selected"] += 1
            continue
        ride_plans = [
            p for p in plans if p["ride_legs"] > 0 and p["score"] is not None
        ]
        if ride_plans:
            counts["scored_out"] += 1
            scored_out_by_group[group] += 1
            best = max(ride_plans, key=lambda p: p["score"])
            gap = sel["score"] - best["score"]
            gaps.append((gap, gap / best["ride_legs"], group))
        else:
            counts["absent"] += 1
            absent_by_group[group] += 1
        for m in sorted(sel["modes"] - {"non_network_walk"}):
            selected_mode_of_nonriders[m] += 1

    gaps.sort(key=lambda t: t[0])

    def pctile(values, q):
        if not values:
            return None
        i = min(len(values) - 1, max(0, int(q * (len(values) - 1))))
        return round(values[i], 3)

    gap_values = [g for g, _, _ in gaps]
    gap_per_leg = sorted(g for _, g, _ in gaps)

    flip_curve = {}
    for delta in FLIP_GRID:
        flipped = sum(1 for _, gpl, _ in gaps if gpl < delta)
        flip_curve[f"{delta:.2f}"] = {
            "flipped": flipped,
            "share_of_scored_out": round(flipped / len(gaps), 4) if gaps else None,
            "share_of_eligible": round(flipped / n_eligible, 4) if n_eligible else None,
        }

    report = {
        "run": run_dir.name,
        "choice_persons": sum(counts.values()) + counts["excluded"] * 0,
        "counts": dict(counts),
        "eligible_ride_avail": n_eligible,
        "scored_out_by_group": dict(scored_out_by_group),
        "absent_by_group": dict(absent_by_group),
        "gap_utils": {
            "n": len(gap_values),
            "p10": pctile(gap_values, 0.10),
            "p25": pctile(gap_values, 0.25),
            "p50": pctile(gap_values, 0.50),
            "p75": pctile(gap_values, 0.75),
            "p90": pctile(gap_values, 0.90),
        },
        "gap_per_ride_leg_utils": {
            "n": len(gap_per_leg),
            "p10": pctile(gap_per_leg, 0.10),
            "p25": pctile(gap_per_leg, 0.25),
            "p50": pctile(gap_per_leg, 0.50),
            "p75": pctile(gap_per_leg, 0.75),
            "p90": pctile(gap_per_leg, 0.90),
        },
        "flip_curve_per_leg_delta": flip_curve,
        "selected_modes_of_non_ride_selectors": dict(
            selected_mode_of_nonriders.most_common()
        ),
        "note": (
            "flip curve is first-order: it re-selects standing plans under a "
            "uniform per-ride-leg utility shift and ignores equilibrium "
            "feedback; validate any chosen shift with a run"
        ),
    }

    out_path = run_dir / "_ride_choice.json"
    out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")

    print(f"run {run_dir.name}: {n_eligible} ride-available choice persons")
    for k in ("selected", "scored_out", "absent", "unscored", "excluded"):
        if counts.get(k):
            print(f"  {k:11} {counts[k]:>8}")
    print(f"  scored_out by group: {dict(scored_out_by_group)}")
    print(f"  absent by group:     {dict(absent_by_group)}")
    print(f"  gap p25/p50/p75 (utils): {report['gap_utils']['p25']} / "
          f"{report['gap_utils']['p50']} / {report['gap_utils']['p75']}")
    print(f"  per-leg p25/p50/p75:     {report['gap_per_ride_leg_utils']['p25']} / "
          f"{report['gap_per_ride_leg_utils']['p50']} / "
          f"{report['gap_per_ride_leg_utils']['p75']}")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
