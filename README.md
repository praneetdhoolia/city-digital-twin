# city-digital-twin

A city-agnostic transport digital-twin framework, applied first as a counterfactual
microsimulation of the **Newcastle (NSW) light rail** — MATSim end to end, for the
five-LGA regional demand model and the corridor alike.

The NSW Auditor-General found that the light rail's benefits were never estimated
against the alternatives that were available in 2013. This repository builds the
model that would answer that question, and holds itself to a stricter standard of
disclosure than the business case it examines: **every value that was not observed
is declared, given a sweep range, and recorded with the reason it was chosen.**

> **No counterfactual has been run, and nothing here is a finding about the light
> rail.** The base model *has* run and been measured — that measurement is
> [below](#does-it-reproduce-the-city-not-yet), and it is a calibration diagnostic,
> not a result. See [`STATUS.md`](cities/newcastle/docs/STATUS.md) for the board and
> the next action.

---

## What it models

Every person-transport mode is **physically simulated or explicitly priced** — none
is a share assumed at the outset — and every corridor mechanism that a light rail
imposes on the street is represented rather than netted out.

| Modes | How |
|---|---|
| Car, motorbike | Physical on the road network, with parking charged on arrival |
| Vehicle passenger (`ride`) | A passenger **physically in a driver's car**, paired to a real household or escort trip; unpaired demand re-modes rather than teleporting |
| Freight (`truck`) | Physical, at declared PCE, seeded from each cordon station's own observed heavy-vehicle share |
| Bus, heavy rail, light rail, ferry | Scheduled transit on the mapped GTFS, **scored as distinct submodes** so a bus and a tram are not interchangeable in route choice |
| Bike, walk | Physical on the active network, with gradient and directional walk-speed factors |
| Taxi / rideshare | One blended priced mode on the published 2025 fares, checked against an inferred trips-per-day band as a **constraint, never a target** |

| Corridor mechanisms | How |
|---|---|
| Traffic signals | **Explicit signal control at the 14 corridor intersections** — generated phase plans, declared minimum greens and saturation flows, run on MATSim's signals contrib. The real SCATS phasing was refused (see [below](#what-could-not-be-obtained)), so the plans are declared and swept, never presented as observed |
| Transit priority | Green extension with a declared priority budget and repayment, keyed to the **tram** in the light-rail scenarios and to the **bus** in the bus-priority counterfactual |
| Level crossings | Freight-train closures at two named crossings, as time-varying link capacity |
| Light rail charging dwell | Native, concurrent with boarding — the wire-free design's cost in run time |
| Lane, kerbside and turn changes | Per scenario, patched onto the network by OSM way id |

Ten scenarios (S0–S6, including three S2 variants) × three day types give the **30
assembled run-input sets**. The light rail's road-space externality is present in
the same run as the tram: a model that simulated the tram without the lane loss
would report a gain that the street never saw.

---

## Set it up

```bash
pip install requests pandas numpy shapely pyproj lxml geopandas pyogrio rasterio openpyxl
python src/setup/bootstrap_toolchain.py             # JDK 25, pt2matsim 26.6, Maven -> .tools/
python src/setup/bootstrap_toolchain.py --run-stack # + the MATSim signals run stack
python tests/check_manifest.py                      # the committed subset is intact
```

Python 3.11+. The toolchain is ~1.4 GiB, gitignored, and **pinned by sha256** —
`--verify` re-checks the digests and compiles the Java without downloading. Signal
runs need the `--run-stack` half: the signals contrib is not in the shaded jar and
must never share a classpath with it. **A toolchain change is a model change.**

## Run a scenario

```bash
python run.py --list        # what is runnable: scenarios, day types, run overlays
python run.py --dry-run     # resolve every input, print it, execute nothing
python run.py --run-config smoke   # a plumbing test: 1% sample, 2 iterations
python run.py --detach      # the DEFAULT arm: S2, weekday, 25% sample, 1000 iterations
```

**The default arm is a multi-hour run** — tens of hours, and how many depends on the
model it runs. [`STATUS.md`](cities/newcastle/docs/STATUS.md) carries the measured
seconds-per-iteration for each stack under *Measured run costs*; read it before
launching, and launch with `--detach`.

```bash
python run.py --run-config ride_fix_10pct
python run.py --scenario S3 --day SAT --fraction 0.10 --iterations 1000
```

**The runner names the run directory** —
`results/<launch yyyymmddThhmmss>_<iterations>it_<sample pct>pct` — so every run is
dated, sortable and self-describing. Re-invoking with the same parameters resumes
the completed run (identity is the parameter set in `_run.json`, not the name);
`--force` starts a fresh directory and overwrites nothing.

| Flag | What it does |
|---|---|
| `--scenario` | `S0`–`S6` and the S2 variants (default `S2`). `--list` shows which have assembled inputs |
| `--day` | `WEEKDAY`, `SAT` or `SUN` |
| `--run-config TAG` | a committed run overlay — **the reproducible way to vary a run** |
| `--fraction` `--iterations` `--threads` `--xmx` `--seed` | registry overrides, checked against each field's declared sweep |
| `--set KEY=VALUE` | a raw MATSim config override, e.g. `ride.constant=-3.4` |
| `--detach` | launch past `PersonPrepareForSim` and return; the run outlives the shell |
| `--dry-run` `--list` `--no-metrics` `--force` | resolve-only, list, skip metric extraction, ignore an existing run record |

**`run.py` does not invent an iteration count in code.**
`RUN.controler.last_iteration` is declared in the registry, so a bare `python run.py`
falls back to the committed `default_25pct` overlay — a named sweep member with its
provenance in the overlay file, not a number in a script.

After a run:

```bash
python src/analyse/extract_metrics.py --run results/<name>
python src/calibrate/fit.py           --run results/<name>   # calibration half only
python src/analyse/run_view.py        --run results/<name>   # live + replay, congestion map
python src/analyse/build_run_index.py                        # results/INDEX.md
python src/run/prune_run.py           --run results/<name>   # reclaim per-iteration output
```

A run without `_run.json` is not a result, and a run under 250 iterations is a
plumbing probe, never evidence.

---

## Does it reproduce the city? Not yet

The figures below are drawn by
[`src/analyse/build_fit_figures.py`](src/analyse/build_fit_figures.py) from the run
the calibrated base was written from — `20260821T175907_1000it_25pct`, S2 × WEEKDAY,
25% sample, 1,000 iterations, comparability family `F4-walk-wedge`. They are a
**pre-calibration diagnostic of the base arm**, they predate the ride and walk
repairs now in the model, and they compare no scenario against any other.

**Mode share** — the only block that carries the fit statistic. Of 67 calibration
targets, **35 are scored** and 32 could not be, each with a stated reason; mean
absolute error over the five scored mode shares is **10.65 percentage points**.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="cities/newcastle/docs/reference/figures/fit_mode_share.dark.svg">
  <img alt="Modelled against observed mode share: vehicle driver +14.19 pp, vehicle passenger -20.51 pp, walk -6.12 pp, public transport +4.42 pp, bike +8.01 pp" src="cities/newcastle/docs/reference/figures/fit_mode_share.light.svg">
</picture>

The errors come in two near-mirror pairs, which is what makes them structural
rather than a matter of tuning: passengers become drivers (−20.51 against
+14.19), and walking trips become cycling trips (−6.12 against +8.01). Both
pairs have since been repaired in the inputs — round-trip passenger bindings and
an observed short-trip distance distribution — and **neither repair has been
measured**. That is what the next arm is for.

**Trip length** — a constraint, checked and reported, never fitted to. **1 of 5**
modes falls inside its observed range.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="cities/newcastle/docs/reference/figures/fit_trip_length.dark.svg">
  <img alt="Modelled mean trip length against the observed range, by mode: only ride falls inside its range" src="cities/newcastle/docs/reference/figures/fit_trip_length.light.svg">
</picture>

**Traffic counts** — scored and reported, deliberately **not** optimised against:
tuning the network to these would compensate for whatever the model is still
missing rather than diagnose it. Across **30** count stations the mean error is
**-91.8%**, and **6** stations model to zero. The residual is unexplained — the
explanation the record used to give was retired when the boundary through-traffic
tier was built and measured as making no difference — and it is tracked as
[issue #82](https://github.com/praneetdhoolia/city-digital-twin/issues/82).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="cities/newcastle/docs/reference/figures/fit_counts.dark.svg">
  <img alt="Modelled against observed weekday traffic counts on log axes: every station falls below the line of perfect agreement" src="cities/newcastle/docs/reference/figures/fit_counts.light.svg">
</picture>

**On light rail patronage.** The arm puts the light rail at **1,260** weekday
boardings. The nearest published observation — 3,417 boardings/day — is the
March 2019 to February 2020 market, and `fit.py` **refuses to score it**: PT mode
share roughly halved between that vintage and the 2024/25 base the model calibrates
to, so the difference between the two numbers is not an error statistic. It is
recorded as unscored, with the reason, in
[`FIGURES.json`](cities/newcastle/docs/reference/figures/FIGURES.json).

Full rows, every unscorable target and the parameter provenance:
[`CALIBRATION_REPORT.md`](cities/newcastle/docs/audit/CALIBRATION_REPORT.md).
Regenerate the figures and the report together after a new arm:

```bash
python src/analyse/build_fit_figures.py          # --check verifies they are current
python src/calibrate/report.py --run <run dir>
```

---

## What is here

| | |
|---|---|
| Files in the manifest | **494** ([`data/MANIFEST.csv`](cities/newcastle/data/MANIFEST.csv): hash, rows, producing script, source, licence, retrieval date) |
| Package on disk | ~4.7 GB across `data/`, `networks/`, `schedules/`, `demand/`, `scenarios/` — mostly gitignored and regenerable |
| Study area | Newcastle, Lake Macquarie, Maitland, Cessnock, Port Stephens — 4,086 km² |
| Zones | 1,500 core SA1 + 201 external SA1, 222 core DZN |
| Population | 611,915 (2021 Census) → 612,687 synthetic agents |
| Road network | 50,182 edges, 11,434 km, gradient-attached |
| Active network | 40,195 edges, 7,920 km, directional walk-speed factors |
| PT | 5 GTFS eras + 10 scenario variants, 15 feeds mapped, 0 unmapped stops |
| Input registry | 407 controllable fields, each with units, provenance and a sweep or a held-fixed rule |
| Validation | 210 targets, pre-registered 67 calibration / 143 holdout |
| Base year | 2026 · CRS EPSG:28356 (GDA94 / MGA Zone 56) |

Every derived file above is regenerable from the immutable raw downloads by a
committed script, and every one is listed in the manifest with its hash, row count,
producing script, source, licence and retrieval date. Three checks stand behind that
claim: `tests/check_manifest.py` verifies the committed subset in CI,
`tests/check_package.py` verifies the full package locally where the bulk data
actually is, and `tests/check_doc_currency.py` verifies that the numbers written into
this page still equal the artefacts they describe.

---

## Documentation

| | |
|---|---|
| [`cities/newcastle/docs/STATUS.md`](cities/newcastle/docs/STATUS.md) | **The board** — phase state, deliverables, next action. Read first |
| [`cities/newcastle/docs/DECISIONS.md`](cities/newcastle/docs/DECISIONS.md) | **Every value that is not observed**, with its rationale and sweep range. Start at its own index |
| [`cities/newcastle/docs/design/newcastle-lr-proposal.md`](cities/newcastle/docs/design/newcastle-lr-proposal.md) | The research design: hypotheses, identification strategy, deliverables |
| [`docs/README.md`](docs/README.md) | The **framework's** documentation and the portable input contract |
| [`.claude/CLAUDE.md`](.claude/CLAUDE.md) | Conventions and hard constraints for anyone — human or agent — changing this repo |

**Read [`DECISIONS.md`](cities/newcastle/docs/DECISIONS.md) before using any of
this.** It records every assumed value, its sweep range, and five corrections to
premises stated in the research proposal.

---

## Layout

**The framework is city-agnostic; everything Newcastle-specific lives under
`cities/newcastle/`.** That split is the point: `config/schema/` states what *any*
city must supply, and a city directory is one instance of it.

```
run.py                       run a scenario
config/schema/               PORTABLE: what any city must supply, and in what shape
src/city.py                  resolves which city's inputs a run reads
src/build/                   layer construction (the reproduction pipeline)
src/run/                     the run harness
src/calibrate/               fit and calibration
src/analyse/                 metrics, figures, run view, replay
src/registry/                the registry resolver, validators and docs generator
src/java/citysim/            MATSim entry point: parking, fares, ride pairing, telemetry
src/java_signals/citysim/    the signals entry point and its tram/bus priority controller
tests/                       check_manifest.py, check_doc_currency.py,
                             check_city_agnostic.py (CI); check_package.py (local)
results/                     run outputs (gitignored)

cities/newcastle/            ONE CITY - every Newcastle/NSW/Australia-specific input
  registry/                  the 407 declared values, with units, provenance, sweeps
  overlays/scenarios|day|runs  per-scenario, per-day-type and per-run value overlays
  extract/                   acquisition adapters: ABS, TfNSW Open Data, Overpass
  build/                     builders that encode THIS city's intervention,
                             corridor, history and statistical geography
  docs/                      THIS city's study: STATUS, DECISIONS, design,
                             audit, handover and the generated reference
  geometry/                  declared extents that were once typed into scripts
  data/raw/                  immutable downloads + provenance_*.json
  data/processed/            zones, census, hts, observed, network, corridor, landuse
  data/MANIFEST.csv          every file: hash, rows, producing script, source, licence
  networks/                  OSM extracts, the MATSim network and variants
  schedules/                 GTFS era feeds + scenarios/S0..S6 variants
  demand/                    synthetic population (B1) and plans (B2 tours, MATSim plans)
  params/                    C1 behavioural parameters + the sensitivity sweep grid
  scenarios/                 E1 scenario configs + matsim/ assembled run inputs
```

Paths inside a city are recorded city-relative — `data/processed/network/...`, not
`cities/newcastle/data/processed/network/...` — so the same manifest row means the
same thing in every city. `src/city.py` is the only module that knows where a city
lives; the city is selected by `CITYSIM_CITY` (default `newcastle`).

---

## Reproducing the data package

Every derived file is regenerable by a committed script from the immutable raw
downloads, seeded (`20260810`) and deterministic — with one measured exception:
**pt2matsim's schedule mapping is not reproducible run to run**. About 18% of transit
route link sequences differ between identical builds while 100% of stop-to-link
assignments hold, so **any scenario comparison must use a single build of the network**
([`DECISIONS.md`](cities/newcastle/docs/DECISIONS.md) §3.5).

```bash
# --- acquisition (network-bound, ~2 GiB) ---
python cities/newcastle/extract/overpass.py                  # OSM, 10 themed extracts over 8 tiles
python cities/newcastle/extract/fetch_gtfs.py                # era GTFS from the TfNSW S3 archive
python cities/newcastle/extract/fetch_open_data.py           # Opal, traffic counts, HTS
python cities/newcastle/extract/fetch_abs_dem.py             # ABS boundaries, census, DEM

# --- clipping ---
python cities/newcastle/extract/extract_zones.py
python cities/newcastle/extract/extract_census.py
python cities/newcastle/extract/extract_hts.py
python cities/newcastle/extract/slice_newcastle.py

# --- layer construction ---
python cities/newcastle/build/build_era_feeds.py             # A3 era variants
python src/build/build_network_layers.py        # A1, A2, A5, A6
python src/build/attach_gradient.py             # gradient onto A1 and A6
python src/build/attach_speed_zones.py          # TfNSW regulated speed zones
python cities/newcastle/build/build_corridor_layers.py       # A4 + corridor A2
python cities/newcastle/build/build_landuse_parking.py   # D1 + A5 completion
python src/build/build_zone_attractions.py      # jobs to SA1, attraction terms
python src/build/build_params.py                # C1
python src/build/build_population.py            # B1 persons + households (~30 s)
python src/build/build_gtfs_extras.py           # A3 extras
python cities/newcastle/build/build_scenario_schedules.py    # S0..S6 feeds
python cities/newcastle/build/build_era1_reconstruction.py   # pre-2014 reconstruction
python cities/newcastle/build/build_scenario_configs.py      # E1
python cities/newcastle/build/build_validation_targets.py

# --- P2 network build (needs the toolchain) ---
python cities/newcastle/build/build_corridor_road_attributes.py
python src/build/build_matsim_network.py        # MATSim network + 15 mapped schedules
python cities/newcastle/build/build_matsim_signals.py    # explicit corridor signal data
python cities/newcastle/build/build_level_crossings.py   # level-crossing closure events

# --- P3 demand synthesis (needs the P2 build above) ---
python src/build/measure_network_factors.py     # C2: detour factor, day-type split
python src/build/build_activity_chains.py       # B2 tours, 3 day types (~90 s, 790 MB)
python src/build/build_matsim_plans.py          # MATSim population per day type
python src/build/build_matsim_run_inputs.py     # 30 runnable scenario x day-type sets

python src/build/build_data_dictionary.py
python src/build/build_manifest.py              # regenerate the manifest LAST
```

---

## Sources and licensing

| Source | Licence |
|---|---|
| TfNSW Open Data Hub — GTFS, Opal, traffic counts, HTS, speed zones | CC-BY 4.0 |
| ABS — Census DataPacks, ASGS boundaries | CC-BY 4.0 |
| OpenStreetMap (via Overpass) | **ODbL 1.0 (share-alike)** |
| Copernicus GLO-30 DEM | ESA, free and open |

OSM-derived layers are **ODbL**, which is share-alike; derived network files inherit
that obligation and the rest of the package is CC-BY 4.0. Keep the distinction visible
in anything published. Per-file provenance is in
[`data/MANIFEST.csv`](cities/newcastle/data/MANIFEST.csv).

---

## What could not be obtained

Three inputs the research design named as critical are not available from open
sources. **Each is handled by parameter sweep and never pinned to a point value** —
the model runs the mechanism, and the headline is reported as a band across the
range rather than as a single number:

- **SCATS signal phasing** — **refused by TfNSW policy**, documented and citable.
  The published inventory gives each signal's identity, location and install date;
  no phase plan, cycle time or split. The corridor's signals are therefore modelled
  explicitly from *declared* plans, and corridor run time swings 38% between no
  priority and full priority — the largest single uncertainty in the model.
- **Journey-linked Opal** — not published. Estimating the transfer penalty needs
  tap-on/tap-off *timing*; every Opal source held is a monthly aggregate and the
  stop-level tap data is holdout. Swept across 3–15 minutes.
- **Measured charging dwell** — no published figure. Swept, never pinned.

Also absent: pedestrian counts (none published for Newcastle — hypothesis B1 has no
observable without them), frontage-level retail floorspace and vacancy, parking meter
transactions, and a 2014 timetable to validate the era-1 reconstruction. The full list
and priority order is in
[`DECISIONS.md`](cities/newcastle/docs/DECISIONS.md) §13.
