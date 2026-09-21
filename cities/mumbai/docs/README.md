# Mumbai — the second city

This directory is one city: its acquisitions, parameters, adapters, overlays
and the documents specific to it. The simulator and its results are at
[`docs/`](../../../docs/README.md); the board is
[`docs/STATUS.md`](../../../docs/STATUS.md).

**Where it stands (21 September 2026, fifty-seventh session).** A broad
acquisition and an executable development case, not a digital twin. The city
runs through the framework's own harness (`run.py --scenario BASE --day WEEKDAY`,
§9.204) on **citywide plans**: the core extent (D13: the notified Mumbai
Metropolitan Region, tiered leaf by leaf in [`mmr_extent.csv`](../data/processed/zones/mmr_extent.csv))
is populated from the census controls (27.06 M persons for 2026), its plans are
written at a 5 % household build fraction (1.35 M persons) and the first
per-mode targets are derived from the published CTS and CMP splits, so the
twelve-mode reporter prints every mode against a target. The first citywide
case ran 0.1 % of the core through the harness (§9.205): a structural check
that measured the memory and flow-granularity constraints on the fraction
([`scaling.md`](scaling.md)) - on this host the city executes at about 1 %
and reads at none (decision D14). No sample fraction has been shown to
preserve behaviour and nothing about its ridership is a result. The [requirements ledger](requirements.json) holds **33 of 33
requirements `incomplete`**. The city passes the framework's city contract
(`python src/registry/check_city.py`), which says its declarations are complete
and well-formed, not that they are right.

## The study area

| | From [`city.json`](../city.json) and the record |
|---|---|
| Core | The **notified Mumbai Metropolitan Region** (decision D13, 21 September 2026): **2,538 of the 4,813 Census 2011 leaves, 23,536,582 persons at the 2011 census**, derived leaf by leaf by [`build_mmr_extent.py`](../extract/build_mmr_extent.py) — every Greater Mumbai ward (97 leaves), the wards of the municipal corporations and councils the public MMR GIS names (874), the villages and census towns whose 2011 code the GIS villages layer carries (1,360) and the villages of the extended-notified-area SPA notification of 9 July 2024 matched by name within their taluka (207). Four notification villages match no census leaf and are listed with their candidates, not guessed; 1,053 leaves still lack a source polygon ([`mmr_extent_audit.json`](../data/processed/acquisition/mmr_extent_audit.json)) |
| External tier | The rest of the four 2011 census districts Mumbai, Mumbai Suburban, Thane (with today's Palghar) and Raigad — **2,275 leaves, 5,200,278 persons at the 2011 census**, rural Thane, Palghar and Raigad — represented at the district level. Through-demand from beyond the four districts (the Pune, Nashik and Gujarat corridors) is not represented |
| Zones | Census 2011 leaves — 1,183 urban wards and 3,630 villages (`geography_id`); residence and workplace at the leaf, external at the district |
| CRS | EPSG:32643, WGS 84 / UTM zone 43N, metres (`city.json`) |
| Years · days · seed · currency | Base year 2026 on 2011 Census controls; one day type, WEEKDAY; seed 20260810; INR (`city.json`) |
| Modes | Mode choice over car, ride, walk, bike, motorbike, taxi, auto_rickshaw, pt (`city.json`, `RUN.mode_choice.modes`); the transit router combines bus, suburban rail, metro and ferry |
| Observed mode series | Census 2011 table B-28 (other workers by mode of travel to work, residence end) — a commute series, not an all-trip share; and, since 21 September 2026, the **published daily mode splits** transcribed from the CTS Updation (MMR 2017: 18.78 M motorised main-mode trips a day, train 43.2 %, bus 20.0 %, two-wheeler 12.5 %, taxi 8.7 %, car 8.5 %, rickshaw 5.1 %, metro and mono 2.2 %; active modes about 47 % of all trips) and the CMP for Greater Mumbai (2005 and 2014) into [`published_mode_splits.csv`](../data/processed/observed/published_mode_splits.csv); the thirteen per-mode targets below are derived from them (§9.205) |

## Scenarios

| id | one line, from the overlay's own `description` |
|---|---|
| BASE | The base year as acquired: the mapped network and combined feed as built, nothing overridden ([`BASE.json`](../overlays/scenarios/BASE.json)) |

Run overlays under [`overlays/runs/`](../overlays/runs/) declare the bounded
development cases: `smoke_two_iterations` (the structural check after a
registry, harness or assembly change: two iterations, a fifteen-minute
ceiling) and `smoke_hired_fleet` (the pooled hired-fleet case, nine iterations,
a one-hour ceiling). The 19 September cases `smoke_mode_coverage` and
`smoke_low_capacity_double` were retired at the fold (§9.204): the one chose a
plans file the assembly now fixes, the other varied a build-time capacity
factor no run overlay can reach.

## What is here

| | |
|---|---|
| Files in the manifest | **1,319** ([`data/MANIFEST.csv`](../data/MANIFEST.csv)) — 28,587 before the harvest rule of 21 September 2026 folded 13,500 per-response files into eleven archives (§9.201) |
| Catalogue | **572** sources in [`extract/sources.json`](../extract/sources.json), 529 acquired, 42 unobtained, one acquired-unusable; eleven of them harvests (one archive of many public queries each) |
| Package on disk | 9.2 GB under `data/raw/`, mostly gitignored: 3.6 GB of traffic-police road orders, 633 MB of transit responses, 582 MB of raster and geospatial layers |
| Network | 846,699 links, 101,306 km, from one native OSM extract (`networks/osm/network_source.osm.gz`, Geofabrik western zone 15 September 2026) |
| PT | Three feeds mapped once: community bus GTFS (1,120 bus routes, 99,080 departures); the multimodal feed adding 31 suburban rail, 14 metro and 4 ferry patterns; the regional feed adding NMMT and MBMT (1,802 bus routes, 114,670 departures, 18,105 stop facilities, 0 unmapped). Every mapped vehicle carries an evidenced capacity profile since 21 September 2026 (§9.206, [`build_transit_fleet.py`](../build/build_transit_fleet.py)): a 12-car EMU 1,168 + 3,816, Line 1 200 + 1,300, the BEML 6-car 239 + 1,561, Line 3 399 + 2,601, Navi Mumbai 150 + 950, the two launches 80 and 100, every bus 36 + 30 (the standing room assumed, swept) |
| Plans | **1,352,144 persons in 303,384 households**, the core households the harness's nested hash keeps at `B.population.plans_build_fraction` 0.05, written by [`build_plans.py`](../build/build_plans.py): work tours at the Census B-28 distance bands, education and optional tours by the declared mechanisms, homes inside the leaf, municipality or taluka polygon; no freight ([`_plans_core_sample_report.json`](../demand/baseline/_plans_core_sample_report.json)). A run at `RUN.sample.fraction` at or below 0.05 keeps what a file of everyone would |
| Population | **27,057,132 persons in 6,068,786 households at the core extent for the 2026 base year**, synthesised by [`build_population.py`](../build/build_population.py) from the Census 2011 leaf controls (households, persons and workers by sex, ages 0-6), the ward/village HL-14 household sizes and vehicle possession, the district single-year ages, work status and school attendance, and the IIPS district projections to 2026 ([`_population_report.json`](../demand/population/_population_report.json)); licence holding and income are declared assumptions, tertiary attendance 20-24 unobtained |
| Input registry | **403** fields — the city's own supply, demand, fare and fleet declarations plus the framework's run-side keys, moved from a private namespace or adopted from the reference city and labelled so (§9.202) |
| Validation | **Thirteen per-mode targets** in [`mode_targets_by_mode.csv`](../data/processed/validation/mode_targets_by_mode.csv) ([`build_mode_targets.py`](../build/build_mode_targets.py), §9.205): every share derived from the CTS Updation 2017 MMR motorised split and its 47 % active share, the B-28 walk/bicycle split, the synthesised car-driver share, the MMB ferry passengers and the CMP goods share, each with its sweep; no projection to 2026, no holdout |

The regional extension's counts come from
[`baseline_regional_buses.json`](../data/processed/acquisition/baseline_regional_buses.json);
published operation and calendars remain unverified:

| Regional input | Count |
|---|---:|
| NMMT directed patterns | 566 |
| NMMT published departures included | 8,806 |
| MBMT directed patterns | 116 |
| MBMT derived departures | 1,972 |

## The twelve modes — what the package holds

| Mode | Held | Missing before it can be scored |
|---|---|---|
| car, motorbike | RTO registration tables, Economic Survey vehicle controls, JVLR and coastal-road counts and travel times | a synthesised population with car and two-wheeler access; a household roster; an all-trip mode share |
| ride | nothing beyond the population's `permittedModes` | households (no ride can name its driver: `B.ride.pairing_enabled` is off) |
| walk, bike | OSM footways and access evidence; the walking network reaches most boarding links | the short-trip band, gradient, stress classes (all gates `absent`) |
| taxi, auto_rickshaw | published meter tariffs (transcribed), RTO stock, a pooled-queue fleet with provisional counts | spatial dispatch, empty running, calibrated fleet sizes, an observed trip volume |
| bus | community GTFS, BEST depots, fares and passes, NMMT timetables (619 routes, 9,522 trips), MBMT routes (118), bus capacity evidence | BEST's own timetable and ridership (requested: [`requests/best_operations.md`](requests/best_operations.md)), a validated per-vehicle capacity file |
| heavy_rail (suburban) | WR and CR printed timetables extracted, harbour-line geometry evidence, MRVC and Economic Survey controls, rake capacities from Indian Railways' EMU primer (§9.206) | a validated harbour-line path, station entries or ridership by line, the AC/15-car/MEMU stock per departure |
| light_rail (metro, monorail) | MMRCL stations, journeys and fares; metro fleet claims and per-line train capacities (§9.206); Navi Mumbai metro controls | ridership by line; monorail service; the seated/standing split of the BEML and Alstom trains |
| ferry | MMB water-transport directory and annual passengers; the two mapped launches at the directory's vessel capacities (§9.206) | the commuter crossings the directory lists and the target counts (#245); a schedule with departures |
| truck | port and JNPA daily rake and cargo statistics; provisional port trucks in the baseline | a count basis on the network; an OD proxy that is validated |
| freight_train | Mumbai Port monthly rakes (loaded and empty by commodity), JNPA ICD rakes | the paths and times of the movements |

Every row above is `incomplete` in the requirements ledger; the ledger holds
the source, the representation and the unresolved evidence per mode.

## Harvests — one archive of many public queries

An operator API answers one route or one trip at a time. Kept one file per
response, the transit folder held 11,956 responses beside 11,956 provenance
records and the catalogue repeated every one. Since 21 September 2026
(§9.201) a family of queries is one **harvest**
([`extract/harvest.py`](../extract/harvest.py)): one zip under
`data/raw/<category>/`, its member listing (`_members.csv`: id, url, request,
sha256, retrieval time) inside, and ONE provenance record pinning the archive.
Members are written in id order with a fixed timestamp, so the archive's hash
depends only on its bytes; a member already archived is never fetched again.

| Harvest | Members | Reader |
|---|---:|---|
| `nmmt_route_schedules`, `nmmt_trip_timetables` | 619 · 9,522 | `audit_nmmt_schedules.py` |
| `nmmt_route_alignments` | 619 | `audit_nmmt_paths.py` |
| `nmmt_route_stop_snapshot_20260918`, `nmmt_vehicle_snapshot_20260918` | 619 · 36 | `audit_nmmt_route_stops.py`, `audit_nmmt_vehicle_details.py` |
| `mbmt_route_details`, `mbmt_route_stops`, `mbmt_route_alignments` | 118 each | `audit_mbmt_routes.py` |
| `mtp_traffic_notices_20260101_20260918` | 1,840 of 1,855 listed (15 return 404 at the publisher) | `audit_traffic_notices.py`, `audit_coastal_access.py` |
| `mumbai_port_rail_statistics` | 47 | `extract_port_rail_controls.py` |

Every processed table re-derived from the archives is byte-identical to the
one derived from the loose files, except route 9841's alignment, which had
been unobtained and was acquired on 21 September 2026.

## Rebuilding

The city runs through the framework's harness like any other (§9.204). Assemble
the run inputs once, then launch a declared case; the harness prices it, refuses
a case with no automatic stop, records it and extracts its metrics:

```powershell
$env:CITYSIM_CITY = 'mumbai'
$env:PYTHONPATH = 'src'
python cities/mumbai/build/build_baseline_run_inputs.py
python run.py --scenario BASE --day WEEKDAY --run-config smoke_two_iterations --foreground
python src/analyse/report_mode_ridership.py --run <name> --it 2
```

The assembly writes `scenarios/matsim/BASE/` (the mapped regional network with
the declared mode permissions, the repaired combined feed, the vehicle types,
the boarding-fare table, the hired-fleet derivation and a header-only parking
table: no parking price is observed) and `demand/plans/matsim/population_WEEKDAY.xml.gz`.
`python src/analyse/baseline_behaviour.py --run <name>` reads a case's execution
and choice diagnostics; `report_mode_ridership.py` reads every mode against
its target. The live view serves at `http://127.0.0.1:8731` on every run
(§9.206: the user's direction that the viewer always runs with a run), and
`python src/analyse/run_view.py --run <name>` opens any finished one: every
mode against its target, the loaded links, and every transit route of the
schedule the run drove by transport mode (bus, suburban rail, metro, ferry),
all read from the run directory.

To rebuild the development demand and combined feed after changing their
registries:

```powershell
$env:PYTHONPATH = 'src'
python cities/mumbai/extract/build_mmr_extent.py
python cities/mumbai/build/build_population.py
python cities/mumbai/build/build_plans.py
python cities/mumbai/build/build_mode_targets.py
python cities/mumbai/build/build_baseline_bus_feed.py
python cities/mumbai/build/build_baseline_transit_feed.py
python cities/mumbai/build/build_regional_bus_feed.py
python cities/mumbai/build/build_baseline_fares.py
python cities/mumbai/build/build_baseline_population.py
python cities/mumbai/extract/extract_activity_areas.py
python cities/mumbai/build/build_baseline_activities.py
python cities/mumbai/build/build_baseline_freight.py
python cities/mumbai/build/build_baseline_choices.py
python cities/mumbai/build/build_hired_fleet.py
python src/build/build_matsim_network.py --stage schedules --only baseline_regional --workers 1 --threads 2
python cities/mumbai/build/build_baseline_run_inputs.py
```

Map a changed feed once; reuse that mapped network for comparisons, never
remap separate arms. After a contract change (`config/schema/required_fields.json`),
`python cities/mumbai/build/adopt_framework_fields.py` re-derives the
framework-key declarations in `registry/*_framework.json`.

The acquisition and audit adapters run from the repository root with
`CITYSIM_CITY=mumbai` and `PYTHONPATH=src`; `extract/sources.json` is the
catalogue, `acquire_sources.py` lands loose single acquisitions, the
harvesters (`acquire_nmmt_*.py`, `acquire_mbmt_sources.py`,
`register_traffic_notices.py --acquire`, `register_port_rail_sources.py
--acquire`) land the archives, and `inventory_sources.py --sync-descriptor`
followed by `python src/build/build_manifest.py` closes the package. Every
adapter is listed in the manifest's `produced_by` for what it writes.

Acquisitions are immutable and carry provenance. An unsuccessful download
stays unobtained; an HTML error page is not a PDF; identical bytes at two URLs
are one observation. `extract/import_browser_acquisition.py` validates a
browser-captured HTTPS response against the catalogue before importing it.
`extract_port_rail_controls.py` needs poppler's `pdftotext` 24 or later: the
4.00 build on Git Bash's PATH mangles the table layout.

## Sources and licensing

Government publication does not establish an open reuse licence; 119 of the
567 catalogue entries carry `Government publication; reuse terms unverified`,
and the manifest's `licence` column states each row's. OSM-derived layers
retain their ODbL provenance and share-alike terms. Source rights remain
separate from the package's own records (CC-BY 4.0).

- [Requirements ledger](requirements.json) · [Evidence notes](evidence_notes.md)
  · [Scaling evidence required](scaling.md) · [Source catalogue](../extract/sources.json)
  · [Acquisition inventory](../data/processed/acquisition/source_inventory.json)
  · [Bus feed audit](../data/processed/acquisition/bus_gtfs_audit.json)
  · [Generated field reference](reference/CONFIG_REFERENCE.md)
