# Mumbai — the second city

This directory is one city: its acquisitions, parameters, adapters, overlays
and the documents specific to it. The simulator and its results are at
[`docs/`](../../../docs/README.md); the board is
[`docs/STATUS.md`](../../../docs/STATUS.md).

**Where it stands (21 September 2026).** A broad acquisition and an executable
development case, not a digital twin. The framework loads the city, maps its
network and combined feed once, and runs an explicit **1,000-person synthetic
population** (labelled `synthetic_from_historical_marginals_and_provisional_assumptions`)
for a handful of iterations on one day type. No mode target has been derived,
no population has been synthesised from the census controls, no sample
fraction has been shown to preserve behaviour, and nothing about its ridership
is a result. The [requirements ledger](requirements.json) holds **33 of 33
requirements `incomplete`**. The city passes the framework's city contract
(`python src/registry/check_city.py`), which says its declarations are complete
and well-formed, not that they are right.

## The study area

| | From [`city.json`](../city.json) and the record |
|---|---|
| Core | The four Census of India 2011 districts **Mumbai, Mumbai Suburban, Thane and Raigad** (IIT Bombay MahaCensus shapefiles) — the research OVERCOVERAGE the acquisition used, not the notified Mumbai Metropolitan Region. The 2011 Thane district includes today's Palghar; the MMR takes only parts of Thane, Palghar and Raigad. **Decision D13 (awaiting the user):** the MMR notified extent is the intended core once its villages are reconciled ([`census_geography_audit.json`](../data/processed/acquisition/census_geography_audit.json): 1,053 of 4,813 census leaves without a source polygon) |
| External tier | None declared: through-demand from beyond the four districts (the Pune, Nashik and Gujarat corridors) is not represented |
| Zones | Census 2011 leaves — 1,183 urban wards and 3,630 villages (`geography_id`); residence and workplace at the leaf, external at the district |
| CRS | EPSG:32643, WGS 84 / UTM zone 43N, metres (`city.json`) |
| Years · days · seed · currency | Base year 2026 on 2011 Census controls; one day type, WEEKDAY; seed 20260810; INR (`city.json`) |
| Modes | Mode choice over car, ride, walk, bike, motorbike, taxi, auto_rickshaw, pt (`city.json`, `RUN.mode_choice.modes`); the transit router combines bus, suburban rail, metro and ferry |
| Observed mode series | Census 2011 table B-28, other workers by mode of travel to work, residence end — the ONLY observed mode series held; not an all-trip share, not a target |

## Scenarios

| id | one line, from the overlay's own `description` |
|---|---|
| BASE | The base year as acquired: the mapped network and combined feed as built, nothing overridden ([`BASE.json`](../overlays/scenarios/BASE.json)) |

Run overlays under [`overlays/runs/`](../overlays/runs/) declare the bounded
development cases: `smoke_mode_coverage`, `smoke_low_capacity_double`,
`smoke_hired_fleet` and `smoke_two_iterations` (the structural check after a
registry or launcher change).

## What is here

| | |
|---|---|
| Files in the manifest | **1,293** ([`data/MANIFEST.csv`](../data/MANIFEST.csv)) — 28,587 before the harvest rule of 21 September 2026 folded 13,500 per-response files into eleven archives (§9.201) |
| Catalogue | **567** sources in [`extract/sources.json`](../extract/sources.json), 514 acquired, 53 unobtained, one acquired-unusable; eleven of them harvests (one archive of many public queries each) |
| Package on disk | 9.2 GB under `data/raw/`, mostly gitignored: 3.6 GB of traffic-police road orders, 633 MB of transit responses, 582 MB of raster and geospatial layers |
| Network | 846,699 links, 101,306 km, from one native OSM extract (`networks/osm/network_source.osm.gz`, Geofabrik western zone 15 September 2026) |
| PT | Three feeds mapped once: community bus GTFS (1,120 bus routes, 99,080 departures); the multimodal feed adding 31 suburban rail, 14 metro and 4 ferry patterns; the regional feed adding NMMT and MBMT (1,802 bus routes, 114,670 departures, 18,105 stop facilities, 0 unmapped) |
| Population | 1,000 explicit persons with activities, freight movements and initial mode alternatives under `demand/baseline/`; no census synthesis, no households, no expansion weight |
| Input registry | **313** fields — the city's own supply, demand, fare and fleet declarations plus the framework's run-side keys, moved from a private namespace or adopted from the reference city and labelled so (§9.202) |
| Validation | No targets. `data/processed/validation/mode_targets_by_mode.csv` does not exist |

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
| heavy_rail (suburban) | WR and CR printed timetables extracted, harbour-line geometry evidence, MRVC and Economic Survey controls | a validated harbour-line path, station entries or ridership by line |
| light_rail (metro, monorail) | MMRCL stations, journeys and fares; metro fleet claims; Navi Mumbai metro controls | ridership by line; monorail service |
| ferry | MMB water-transport directory and annual passengers | a schedule with departures; a target |
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

The bounded development entry point (a few minutes; it prepares the network
and schedule at launch and records the case under the results store):

```powershell
$env:CITYSIM_CITY = 'mumbai'
python run.py --baseline-smoke --run-config smoke_hired_fleet
```

`python src/analyse/baseline_behaviour.py --run <name>` reads a case's execution
and choice diagnostics. The launch path is still the city's own
(`src/run/baseline_smoke.py`), not the framework's `run.py <scenario>`: folding
it in is the lane's next task (§9.202).

To rebuild the development demand and combined feed after changing their
registries:

```powershell
$env:PYTHONPATH = 'src'
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
