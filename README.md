# city-digital-twin

A city-agnostic **digital twin of how a real city moves** — MATSim end to end.
Twelve modes, each physically simulated on the real roads and timetables and
scored against its real-life ridership, driven by a synthetic population drawn
from the published census, survey and licence data. The first city is
**Newcastle (NSW)**. The goal, its hard requirements and the loop every session
runs are in [`docs/GOAL.md`](docs/GOAL.md); where the twin stands against it is
the one-page board, [`docs/STATUS.md`](docs/STATUS.md).

Once the twin reproduces every mode at its real share it can be pointed at
questions observation cannot settle — Australia's low light rail usage
(Newcastle's 2019 line is the first application; the frozen origin design is
[`newcastle-lr-proposal.md`](cities/newcastle/docs/archived/design/newcastle-lr-proposal.md)),
the modes that could relieve a corridor, the demands of an event the size of
Brisbane 2032. One standard holds throughout: **every value that was not observed
is derived where it can be, and otherwise declared, given a sweep range and
recorded with the reason it was chosen.** Nothing is a result until a run's
`_run.json` says `ran_to_last_iteration`.

---

## What it models

Every person-transport mode is physically simulated or explicitly priced — none
is a share assumed at the outset — and every corridor mechanism a light rail
imposes on the street is represented rather than netted out.

| Modes | How |
|---|---|
| Car, motorbike | Physical on the road network, with parking charged on arrival |
| Vehicle passenger (`ride`) | A passenger physically in a driver's car, paired to a real household or escort trip; unpaired demand re-modes rather than teleporting |
| Freight (`truck`) | Physical, at declared PCE, seeded from each cordon station's own observed heavy-vehicle share |
| Bus, heavy rail, light rail, ferry | Scheduled transit on the mapped GTFS, scored as distinct submodes |
| Bike, walk | Physical on the footpath-and-road network — every harvested footway, path, cycleway, steps, track and shared path is a link, with gradient and directional walk-speed factors; a pt access, egress or transfer walk is a network leg the simulation executes, never a teleport |
| Taxi / rideshare | Physical on the road with a finite fleet — a request the fleet cannot serve is refused; priced on the published 2025 fares; scored against a target derived from the IPART trips-per-day band |

| Corridor mechanisms | How |
|---|---|
| Traffic signals | SCATS, implemented as its published algorithm at the 14 corridor intersections on MATSim's signals contrib: degree of saturation at every stop line, cycle and splits adapted toward a target DS. The operated phase plans and the offset library are not released, so offsets are not adapted ([below](#what-is-derived-rather-than-observed)) |
| Transit priority | Green extension with a declared priority budget and repayment — the tram in the light-rail scenarios, the bus in the bus-priority counterfactual |
| Level crossings | Every scheduled passenger train and the published survey's freight movements close two named crossings, as time-varying link capacity |
| Light rail charging dwell | Native, concurrent with boarding — the wire-free design's cost in run time |
| Lane, kerbside and turn changes | Per scenario, patched onto the network by OSM way id |

Ten scenarios (S0–S6, including three S2 variants) × three day types give the
**30 assembled run-input sets**. The light rail's road-space externality is
present in the same run as the tram.

---

## Set it up

```bash
pip install requests pandas numpy shapely pyproj lxml geopandas pyogrio rasterio openpyxl
python src/setup/install_paths.py                   # the import roots, once per interpreter (a .pth)
python src/setup/bootstrap_toolchain.py             # JDK 25, pt2matsim 26.6, Maven -> .tools/
python src/setup/bootstrap_toolchain.py --run-stack # + the MATSim signals run stack
python tests/check_manifest.py                      # the committed subset is intact
```

Python 3.11+ (CI and the workstation run 3.14). The toolchain is ~1.4 GiB,
gitignored and pinned by sha256; `--verify` re-checks the digests and compiles
the Java without downloading. Signal runs need the `--run-stack` half: the
signals contrib is not in the shaded jar and must never share a classpath with
it. A toolchain change is a model change.

## Run a scenario

```bash
python run.py --list                            # what is runnable: scenarios, day types, run overlays
python run.py --dry-run                         # resolve every input, print it, execute nothing
python run.py --run-config smoke                # a plumbing test: 1% sample, 2 iterations
python run.py --detach --run-config <overlay>   # an arm: S2, weekday, the overlay's sample and horizon
python run.py --stop <name> --cause "..."       # stop a running arm through the harness
```

An arm is a multi-hour run. Price it, never quote it:
`python src/analyse/arm_cost.py --run-config <overlay>` reads the newest runs'
own stopwatches at the same sample fraction and prints the band; the launcher
prints the same line before every launch. Four rules stand before any launch:

1. **A stated-cost approval from the user**, spent on use.
2. **25 % sample only** (user directive, 1 September 2026); the overlay declares
   the horizon, and `GOAL.md` asks for convergence within 250 iterations.
3. **No open issue in the run's lane without a stated measurement**
   (`python src/run/issue_gate.py`; `GOAL.md` requirement 10). An issue claiming
   `awaiting-run` carries a line `AWAITING-RUN: <the measurement>`; the run's
   lane is the set of issues its overlay declares it answers.
   `--allow-open-issues` needs `--override-reason` and is counted.
4. **One arm at a time**, launched with `--detach`, stopped with `--stop`, never
   by hand. The launcher refuses a concurrent arm, a launch with no automatic
   stop, a heap below the registry's rule, and an overlay that changes nothing
   the run reads.

| Flag | What it does |
|---|---|
| `--scenario` | `S0`–`S6` and the S2 variants (default `S2`); `--list` shows which have assembled inputs |
| `--day` | `WEEKDAY`, `SAT` or `SUN` |
| `--run-config TAG` | a committed run overlay — the reproducible way to vary a run |
| `--fraction` `--iterations` `--threads` `--xmx` `--seed` | registry overrides, checked against each field's declared sweep |
| `--set KEY=VALUE` | a raw MATSim config override |
| `--detach` | launch past `PersonPrepareForSim` and return; the run outlives the shell |
| `--stop NAME --cause TEXT` | stop a running arm and record why — the one sanctioned way |
| `--dry-run` `--list` `--no-metrics` `--force` | resolve-only, list, skip metric extraction, ignore an existing run record |

The runner names the run directory
`results/raw/<launch yyyymmddThhmmss>_<iterations>it_<sample pct>pct`; re-invoking
with the same parameters resumes a completed run (identity is the parameter set
in `_run.json`). `results/` manages itself (§9.137): `raw/` is a budgeted cache
whose oldest runs are deleted once their findings are extracted, `processed/`
keeps every run's records permanently. Never rename, delete or edit anything
under it by hand. A bare `python run.py` falls back to the committed
`default_25pct` overlay: `run.py` invents no iteration count in code.

After a run:

```bash
python src/analyse/extract_metrics.py --run <name>           # a bare name resolves via results/raw
python src/calibrate/fit.py           --run <name>           # calibration half only
python src/analyse/report_mode_ridership.py --run <name> --trend   # the twelve modes against their targets
python src/analyse/run_view.py        --run <name>           # the run viewer: progress, the twelve modes, the map
python src/analyse/build_run_index.py                        # results/INDEX.md
python src/run/prune_run.py           <name>                 # reclaim per-iteration output
```

A run is a result only if its `_run.json` says `ran_to_last_iteration`. A run
stopped by the gate watcher or by `--stop` is closed out with a record saying
`stopped_at_gate` or `stopped_by_operator`: its reading is real at that record's
`reached_iteration` and says nothing about any iteration after it. A run that
crashed gets no record; its `_meta.json` states the cause.

---

## Does it reproduce the city? Not yet

The figures below are drawn by
[`src/analyse/build_fit_figures.py`](src/analyse/build_fit_figures.py) from the run
the calibrated base was written from — `20260909T015217_300it_25pct`, S2 × WEEKDAY,
25% sample, 300 iterations, comparability family `F32-crowding-reaches-scoring`.
The base is written from it as constrain-and-report (`DECISIONS.md` §9.50): no
parameter was fitted, and the run is reported as it came out. The figures compare
no scenario against any other. The newer result, F35's arm 0, is read on the
board.

**Mode share** — the only block that carries the fit statistic. Of 67 calibration
targets, **36 are scored** and 31 could not be, each with a stated reason; mean
absolute error over the five scored mode shares is **4.73 percentage points**.
The objective the twin is held to is the twelve-mode one on the board: at this
result **0 of 12** modes are inside 10 % and the largest deviation is heavy rail
at +225 %.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="cities/newcastle/docs/reference/figures/fit_mode_share.dark.svg">
  <img alt="Modelled against observed mode share: vehicle driver +6.34 pp, vehicle passenger -8.44 pp, walk -3.55 pp, public transport +0.84 pp, other (bike and taxi) +4.50 pp" src="cities/newcastle/docs/reference/figures/fit_mode_share.light.svg">
</picture>

The five folded shares hide what the twelve unfolded modes show: the passenger
deficit (−8.44 pp) is a driver surplus (+6.34 pp), and the "Other" surplus
(+4.50 pp) is bike at +113 % and taxi at +202 % sharing one survey cell.

**Trip length** — a constraint, checked and reported, never fitted to. **0 of 5**
modes falls inside its observed range; walk is modelled at 3.28 km against an
observed 0.70, a supply ceiling set at build time ([issue #30](https://github.com/praneetdhoolia/city-digital-twin/issues/30)).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="cities/newcastle/docs/reference/figures/fit_trip_length.dark.svg">
  <img alt="Modelled mean trip length against the observed range, by mode: no mode falls inside its range" src="cities/newcastle/docs/reference/figures/fit_trip_length.light.svg">
</picture>

**Traffic counts** — scored and reported, deliberately not optimised against.
Across **31** count stations the mean error is
**16.3%** (median −1.1 %), and **0** stations model to zero.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="cities/newcastle/docs/reference/figures/fit_counts.dark.svg">
  <img alt="Modelled against observed weekday traffic counts on log axes" src="cities/newcastle/docs/reference/figures/fit_counts.light.svg">
</picture>

**Light rail patronage.** The arm puts the light rail at **1,224** weekday
boardings against a derived target of 2,954 (−58.6 %). The nearest published
observation — 3,417 boardings/day — is the March 2019 to February 2020 market,
and `fit.py` refuses to score it: PT mode share roughly halved between that
vintage and the base year, so the difference is not an error statistic. It is
recorded as unscored, with the reason, in
[`FIGURES.json`](cities/newcastle/docs/reference/figures/FIGURES.json).

Full rows, every unscorable target and the parameter provenance:
[`CALIBRATION_REPORT.md`](cities/newcastle/docs/reference/CALIBRATION_REPORT.md). The figures
and the report derive from the synthetic plans, which carry the OSM network's
share-alike ancestry, so they are published under **ODbL 1.0**, not CC-BY 4.0.
Regenerate them together after a new calibrated base:

```bash
python src/analyse/build_fit_figures.py          # --check verifies they are current
python src/calibrate/report.py --run <run dir>
```

---

## Five words

- **Arm** — one scenario run, launched detached, gated every 100 iterations; a result only when its `_run.json` says `ran_to_last_iteration`.
- **Family** — a comparability class: every run since a change to the plans or the network; nothing compares across families ([`docs/run_families.json`](docs/run_families.json)).
- **Gate** — the reading of all twelve modes against their targets every 100 iterations; a mode at or past 20 % stops the run.
- **Holdout** — the 143 of 210 validation targets that stay unread until the end; the 67 others are the calibration half.
- **`awaiting-run`** — the label an open issue carries when the only thing left to do on it is a measurement that needs the run.

## The first city: Newcastle (NSW)

The package counts, its sources and licences, what is derived rather than
observed and the reproduction steps are on the city's page
[`cities/newcastle/docs/README.md`](cities/newcastle/docs/README.md); its twelve
targets and their bases on [`targets.md`](cities/newcastle/docs/targets.md).
The licence boundary stays visible: OSM-derived layers are ODbL 1.0
(share-alike), the rest of the package CC-BY 4.0, per file in `data/MANIFEST.csv`.

---

## Documentation

[`docs/`](docs/README.md) is the simulator and its results: the goal, the board,
the brief, the position pages, the record, the family ledger and the reports.
[`cities/<city>/docs/`](cities/newcastle/docs/README.md) is that city's documents:
its front page, targets, generated reference, requests and archives. Conventions
and hard constraints for anyone changing this repository are in
[`.claude/CLAUDE.md`](.claude/CLAUDE.md).

---

## Layout

The framework is city-agnostic; everything Newcastle-specific lives under
`cities/newcastle/`. `config/schema/` states what any city must supply, and a
city directory is one instance of it.

```
README.md                    this page
docs/                        the simulator's documents: GOAL, STATUS, the brief, positions, DECISIONS, run_families.json, reports
run.py                       run a scenario
config/schema/               PORTABLE: what any city must supply, and in what shape
src/city.py                  resolves which city's inputs a run reads, and where the documents are
src/build/                   layer construction (the reproduction pipeline)
src/run/                     the run harness, the gates, the session gate
src/calibrate/               fit and calibration
src/analyse/                 metrics, the twelve-mode reader, figures, the board, the run viewer
src/registry/                the registry resolver, validators and docs generator
src/java/citysim/            MATSim entry point: parking, fares, ride pairing, telemetry
src/java_signals/citysim/    the signals entry point and its tram/bus priority controller
tests/                       the CI checks and tests/unit/; check_package.py (local)
results/                     run outputs (gitignored): raw/ the budgeted cache, processed/ the findings

cities/newcastle/            ONE CITY - every Newcastle/NSW/Australia-specific input
  registry/                  the 558 declared values, with units, provenance, sweeps
  overlays/scenarios|day|runs  per-scenario, per-day-type and per-run value overlays
  extract/                   acquisition adapters: ABS, TfNSW Open Data, Overpass
  build/                     builders that encode THIS city's intervention, corridor and geography
  geometry/                  declared extents that were once typed into scripts
  docs/                      THIS city's documents: front page, targets, generated reference, requests, archives
  tests/                     the city's live-state claims (doc_currency.json) and package expectations
  data/raw/                  immutable downloads + provenance_*.json
  data/processed/            zones, census, hts, observed, network, corridor, landuse
  data/MANIFEST.csv          every file: hash, rows, producing script, source, licence
  networks/                  OSM extracts, the MATSim network and variants
  schedules/                 GTFS era feeds + scenarios/S0..S6 variants
  demand/                    synthetic population (B1) and plans (B2 tours, MATSim plans)
  params/                    C1 behavioural parameters + the sensitivity sweep grid
  scenarios/                 E1 scenario configs + matsim/ assembled run inputs
```

Paths inside a city are recorded city-relative — `data/processed/network/...` —
so the same manifest row means the same thing in every city. The city is
selected by `CITYSIM_CITY` (default `newcastle`).

