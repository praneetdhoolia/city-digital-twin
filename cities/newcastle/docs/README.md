# Newcastle (NSW) — the first city

This directory is one city: its data, parameters, adapters, overlays and the documents specific
to it. The simulator and its results are at [`docs/`](../../../docs/README.md); the board is [`docs/STATUS.md`](../../../docs/STATUS.md).

## The study area

| | From [`city.json`](../city.json) and [`DECISIONS.md`](../../../docs/DECISIONS.md) §1 |
|---|---|
| Core | Five LGAs — Newcastle, Lake Macquarie, Maitland, Cessnock, Port Stephens — 4,086 km²; the agencies are the Australian Bureau of Statistics (ABS) and Transport for NSW (TfNSW) (`city.json`, §1) |
| External tier | The remaining SA2s of SA4 *Hunter Valley exc Newcastle* (Singleton, Muswellbrook, Upper Hunter, Dungog): a boundary treatment for Hunter Line through-demand only, not modelled at SA1, the line cut at Maitland (`city.json`, §1) |
| Zones | 1,500 core SA1 + 201 external SA1, 222 core DZN — residence SA1, external SA2, workplace DZN (`city.json`) |
| CRS | EPSG:28356, GDA94 / MGA Zone 56, metres — not GDA2020, which is EPSG:7856 (`city.json`) |
| Years · days · seed · currency | Base year 2026 on 2021 Census marginals with HTS 2024/25 behaviour; day types WEEKDAY, SAT, SUN, a full weekend in every feed (§1); seed 20260810; AUD (`city.json`) |
| Modes | Mode choice over car, ride, pt, bike, walk, taxi (`city.json`); scored as the twelve — car, ride, walk, taxi, bike, motorbike, bus, heavy_rail, light_rail, ferry, truck, freight_train ([`targets.md`](targets.md)) |

## Scenarios

| id | one line each, from the overlay's own `description` under [`overlays/scenarios/`](../overlays/scenarios/) |
|---|---|
| S0 | Heavy rail retained to Newcastle station — the primary counterfactual, no light rail ([`S0.json`](../overlays/scenarios/S0.json)) |
| S1 | Bus shuttle from Wickham, no light rail — the December 2012 policy as announced ([`S1.json`](../overlays/scenarios/S1.json)) |
| S2 | Light rail as built, wire-free, current signals — the reference case ([`S2.json`](../overlays/scenarios/S2.json)) |
| S2a | Light rail with the charging dwell removed — isolates the wire-free decision ([`S2a.json`](../overlays/scenarios/S2a.json)) |
| S2b | Light rail with full transit signal priority — isolates signal priority ([`S2b.json`](../overlays/scenarios/S2b.json)) |
| S2c | Light rail on the Option A harbour-side alignment — the route not selected ([`S2c.json`](../overlays/scenarios/S2c.json)) |
| S3 | Bus rapid transit on the same alignment — the value-for-money test is S2 vs S3 ([`S3.json`](../overlays/scenarios/S3.json)) |
| S4 | Light rail extended to Broadmeadow — the trunk-length hypothesis ([`S4.json`](../overlays/scenarios/S4.json)) |
| S5 | Light rail extended to Broadmeadow and John Hunter Hospital — the upper bound ([`S5.json`](../overlays/scenarios/S5.json)) |
| S6 | No trunk mode; walk, cycle and local bus only — the lower bound ([`S6.json`](../overlays/scenarios/S6.json)) |

## What is here

| | |
|---|---|
| Files in the manifest | **959** ([`data/MANIFEST.csv`](../data/MANIFEST.csv): hash, rows, producing script, source, licence, retrieval date) |
| Package on disk | 6.64 GiB across `data/`, `networks/`, `schedules/`, `demand/`, `scenarios/` — mostly gitignored and regenerable |
| Study area | Newcastle, Lake Macquarie, Maitland, Cessnock, Port Stephens — 4,086 km² |
| Zones | 1,500 core SA1 + 201 external SA1, 222 core DZN |
| Population | 611,915 (2021 Census) → 612,634 synthetic agents |
| Road network | 50,182 edges, 11,434 km, gradient-attached |
| Active network | 40,195 edges, 7,920 km, directional walk-speed factors — and walk- and bike-capable links of the MATSim network itself (368,230 links with the roads and railways) |
| PT | 5 GTFS eras + 10 scenario variants, 15 feeds mapped, 0 unmapped stops |
| Input registry | 559 controllable fields, each with units, provenance and a sweep or a held-fixed rule |
| Validation | 210 targets, pre-registered 67 calibration / 143 holdout |
| Base year | 2026 · CRS EPSG:28356 (GDA94 / MGA Zone 56) |

Every derived file is regenerable from the immutable raw downloads by a committed
script and listed in the manifest. `tests/check_manifest.py` verifies the
committed subset in CI, `tests/check_package.py` the full package locally, and
`tests/check_doc_currency.py` that the numbers on this page still equal the
artefacts they describe.

## Sources and licensing

| Source | Licence |
|---|---|
| TfNSW Open Data Hub — GTFS, Opal, traffic counts, HTS, speed zones | CC-BY 4.0 |
| ABS — Census DataPacks, ASGS boundaries | CC-BY 4.0 |
| OpenStreetMap (via Overpass) | **ODbL 1.0 (share-alike)** |
| Copernicus GLO-30 DEM | ESA, free and open |

OSM-derived layers are ODbL, which is share-alike; derived network files inherit
that obligation and the rest of the package is CC-BY 4.0. Per-file provenance is
in [`data/MANIFEST.csv`](../data/MANIFEST.csv).

## What is derived rather than observed

The rule ([`GOAL.md`](../../../docs/GOAL.md) requirement 6): a disclosed value is used
exactly; an undisclosed one is researched and derived; a sweep is the fallback
only where derivation is genuinely impossible, and then the reason is stated and
the value is never pinned.

- **SCATS signal operation** — TfNSW does not release the operated phase plans or
  the offset library. The published SCATS algorithm is implemented instead
  (degree of saturation, cycle and split adaptation, priority); offsets are not
  adapted because no algorithm replaces the unreleased library
  ([`positions/signals-and-crossings.md`](../../../docs/positions/signals-and-crossings.md)).
- **Rail and tram patronage** — held to the disclosed weekday boardings. **Ferry**
  patronage is not published; its target is derived from the harbour's market.
- **Licence holding** — the published TfNSW licence count over the ABS
  population, per age band and LGA.
- **Journey-linked Opal** — not published; the transfer penalty it would estimate
  is swept 3–15 minutes. **Measured charging dwell** — no published figure; swept.

Also absent: pedestrian counts, frontage-level retail floorspace and vacancy,
parking meter transactions, and a 2014 timetable to validate the era-1
reconstruction. The current position on every input is
[`positions/network-and-inputs.md`](../../../docs/positions/network-and-inputs.md).

## Reproducing the data package

Every derived file is regenerable by a committed script from the immutable raw
downloads, seeded (`20260810`) and deterministic — with one measured exception:
pt2matsim's schedule mapping is not reproducible run to run (about 18% of route
link sequences differ between identical builds while every stop-to-link
assignment holds), so any scenario comparison must use a single build of the
network ([`DECISIONS.md`](../../../docs/DECISIONS.md) §3.5).

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
python src/build/build_network_layers.py                     # A1, A2, A5, A6
python src/build/attach_gradient.py                          # gradient onto A1 and A6
python src/build/attach_speed_zones.py                       # TfNSW regulated speed zones
python cities/newcastle/build/build_corridor_layers.py       # A4 + corridor A2
python cities/newcastle/build/build_landuse_parking.py       # D1 + A5 completion
python src/build/build_zone_attractions.py                   # jobs to SA1, attraction terms
python src/build/build_params.py                             # C1
python src/build/build_population.py                         # B1 persons + households (~30 s)
python src/build/build_gtfs_extras.py                        # A3 extras
python cities/newcastle/build/build_scenario_schedules.py    # S0..S6 feeds
python cities/newcastle/build/build_era1_reconstruction.py   # pre-2014 reconstruction
python cities/newcastle/build/build_scenario_configs.py      # E1
python cities/newcastle/build/build_validation_targets.py

# --- P2 network build (needs the toolchain) ---
python cities/newcastle/build/build_corridor_road_attributes.py
python src/build/build_matsim_network.py                     # MATSim network + 15 mapped schedules
python cities/newcastle/build/build_charging_dwell_offsets.py  # the dwell-transformed schedules the signals read
python cities/newcastle/build/build_matsim_signals.py        # explicit corridor signal data
python cities/newcastle/build/build_level_crossings.py       # level-crossing closure events

# --- P3 demand synthesis (needs the P2 build above) ---
python src/build/measure_network_factors.py                  # C2: detour factor, day-type split
python src/build/build_activity_chains.py                    # B2 tours, 3 day types (~90 s, 790 MB)
python src/build/build_matsim_plans.py                       # MATSim population per day type
python src/build/build_matsim_run_inputs.py                  # 30 runnable scenario x day-type sets

python src/build/build_data_dictionary.py
python src/build/build_manifest.py                           # regenerate the manifest LAST
```

## Naming

The project is Newcastle, not Wickham: Wickham is one suburb, legitimate in exactly three
places — its own zones and stops, Newcastle Interchange at Wickham, and S1, the bus-shuttle
scenario. Two codename identifiers survive, tracked for rename: `CITYSIM_*` and `src/java/citysim/`.

## The city's documents

| Where | What |
|---|---|
| [`targets.md`](targets.md) | The twelve targets and their bases, read from `data/processed/validation/mode_targets_by_mode.csv` |
| [`reference/`](reference/) | Generated, never edited by hand: [`CONFIG_REFERENCE.md`](reference/CONFIG_REFERENCE.md) from the registry, [`DATA_DICTIONARY.md`](reference/DATA_DICTIONARY.md) from the CSVs, [`CALIBRATION_REPORT.md`](reference/CALIBRATION_REPORT.md) and [`figures/`](reference/figures/) from the calibrated base's run |
| [`requests/`](requests/) | Drafted data requests, e.g. the TfNSW HTS bespoke tables ([`tfnsw_hts_bespoke_tables.md`](requests/tfnsw_hts_bespoke_tables.md), #50) |
| [`archived/design/`](archived/design/) · [`archived/audit/`](archived/audit/) | The frozen origin design, [`newcastle-lr-proposal.md`](archived/design/newcastle-lr-proposal.md), and the evidence dossiers; frozen diagnostics of retired runs |
| [`../tests/doc_currency.json`](../tests/doc_currency.json) · [`../tests/package_expectations.json`](../tests/package_expectations.json) | The city's live-state claims the currency check pins; what `tests/check_package.py` expects of the full package |
