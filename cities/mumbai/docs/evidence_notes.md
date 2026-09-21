# Evidence interpretation and unresolved conflicts

The [catalogue](../extract/sources.json) identifies each source below. The
[inventory](../data/processed/acquisition/source_inventory.json) records its
immutable path and hash. These notes describe limitations discovered during
acquisition; they do not establish a calibrated Mumbai model.

## Geography and population

`mmr_boundary_2019`, PDF page 3, defines the region through named administrative
limits, Tansa River and specified villages in Karjat. A rectangle or the union
of whole modern districts is not the notified region. Scheduled-area exclusions
also require reconciliation with the applicable notification and mapped extent.

The four acquired PCA workbooks describe Mumbai City, Mumbai Suburban, Thane
and Raigarh as recorded in 2011. That Thane geography includes later Palghar.
The [census audit](../data/processed/observed/_census_evidence_audit.json) verifies
that non-overlapping leaf geographies sum to their published district controls.
These totals are not MMR totals and have not been projected to the model year.
The leaf table retains work status jointly by sex, annual duration and the
published cultivator/agricultural-labourer/household-industry/other-worker
categories. Each partition reconciles within its source row and to the district
total. The [age/work audit](../data/processed/observed/_age_work_controls_audit.json)
also checks leaf aggregates against the separate B01 table for each district,
residence class, sex and main/marginal/non-worker category. These are resident
worker counts; they do not locate jobs or establish weekly working hours.

The IIT Bombay boundary downloads distinguish administrative wards from census
wards. Their identifiers require a crosswalk. The Mumbai City census-linked
shapefile has no features. Other acquired shapes include invalid geometries;
see the [geometry audit](../data/processed/acquisition/boundary_source_audit.json).
The original data is retained. No silent geometry repair is applied.

The acquisition descriptor uses WGS 84 / UTM zone 43N (EPSG:32643) for metric
processing. This is an engineering coordinate-system choice, not an observed
transport parameter. Source geometries retain their declared CRS until a
documented transformation is applied. The provisional model year follows the
project's 2026 requirement; current-year population remains to be derived.

The [municipal population estimates](../data/processed/observed/bmc_population_estimates.csv)
retain BMC's printed reference years: 2023 in the 2025 Civic Diary, 2025 in the
2026 diary, and 2024/2025 in the Environment Status Report. Their
[audit](../data/processed/acquisition/bmc_population_estimates_audit.json) retains
subtotal discrepancies and the conflicting 2025 ward estimates. PDF pages 87
of the 2026 diary and 19 of the environment report were also checked visually.
These administrative wards need a Census geography crosswalk. An apparent
reuse of older values is not sufficient evidence to relabel a year or choose
a preferred estimate. Neither publication covers all of MMR.

The National Health Mission copy of the population projection report is
acquired as `nhm_population_projection_2019`; its title page dates it November
2019. The state/age/sex tables still require extraction and comparison with
the later edition. A state projection cannot by itself determine Mumbai's
migration or current ward population.

## Demand definitions

`census_b28_maharashtra` counts travel to work by the census's *other workers*.
It is not an all-purpose travel survey. Tempo, autorickshaw and taxi appear in
one combined category, so their separate shares cannot be read from this table.
Total/Rural/Urban and total/distance-band rows are overlapping aggregations.

`cts_2021_mirror` is a third-party-hosted copy labelled *Final Report, Executive
Summary*, October 2021. Its cover and content are consistent with the official
study description; a byte-identical official copy is not yet acquired. PDF
pages 43–44 explain the household-survey vintages and main-mode classification.
Access/egress legs are not equivalent to main-mode journeys. PDF pages 50–51
distinguish bus journeys from boardings including feeders. PDF page 101 describes
the survey programme and demand model. The underlying microdata, zonal matrices
and machine-readable model package remain unobtained.

`jica_metro11_2026`, PDF pages 56–57, reproduces CTS horizon-year demand.
Future-year assignments are forecasts, not observed 2026 ridership. They must
not become calibration targets because the calendar year now matches.

`vehicle_stock_2025` and `vehicle_registrations_2024_25` downloaded identical
bytes from different official URLs. They are one combined source, not two
independent observations. Registered vehicles do not establish active fleet,
road trips, occupancy, daily utilisation or MMR residence.

## Public transport

Central Railway's current Mumbai Suburban index links older main-line tables,
May 2026 Harbour tables, a January 2024 Trans-Harbour table and December 2025
Port Line table. AC and August 2026 15-car supplements overlap those services;
they cannot be concatenated into a feed as additional trains. The acquired
abbreviation sheet defines `X` and `XX` operating exceptions and reserved
coaches. The main AC supplement states that `AC#` services use non-AC rakes on
Saturdays, Sundays and nominated holidays; the Harbour AC supplement states
Sunday/holiday substitution. The holiday sheet names movable festivals without
their dates. Its acquisition identifier is not proof of a year-specific calendar.
`extract_cr_timetable.py` retains printed glyph positions and separates stacked
table headers. It also reads station-name prefixes when PDF text lines merge
names with the first time or passing marker. Unassigned cells remain in its
audit. Printed row alignment, clock time and a train number are not yet a
validated stop, operating calendar or service-day offset.
The 15-car supplement's first page also contains white `00:00` text on a white
background. PDF text extraction exposes it although the rendered table does
not print those times. The extractor quarantines white glyph cells with their
coordinates and colours; they cannot silently become midnight departures.

## Road access and dated orders

The Mumbai Traffic Police public-notice index initially lists only its most
recent entries. A date-filter POST requesting January-September 2026 returns
an archive extending to February 2009; the filter was not honoured. The archive
is therefore preserved as an unfiltered listing. An order can have multiple
PDF or JPEG attachments, and repeated identical links count once per order.
The registrar validates the displayed notice count separately from attachment
counts. Attachment acquisition prioritises permanent orders, then retains dated
temporary arrangements for supersession and event-calendar checks.

Different notice IDs can return identical PDF bytes. For example, acquired
`mtp_notice_823391` and `mtp_notice_823390` are identical despite their different
subjects. An index title cannot establish a document's identity. Some linked
attachments return 404, and many acquired PDFs contain scanned images only.
Neither a missing file nor the index's generic *Till Next Order* label can set
an access rule or establish that an old order remains in force.

`mtp_notice_823227` contains the August 2026 Coastal Road and Sea Link order.
Its ramps, exclusions and speed rules require transcription, checks against the
source image and road-segment joins. `atal_setu_faq_20240315`, page 3, describes
cycle, two-wheel and three-wheel exclusions. Its historic toll wording must be
read with later orders, including the acquired August 2025 EV exemption. Toll
exemption and permission to enter are separate attributes, and current tolls
still require the applicable 2026 notification.

## Bus and other public transport evidence

The community bus GTFS contains routes with no trips and uses one seven-day
calendar. See the [structural audit](../data/processed/acquisition/bus_gtfs_audit.json).
It requires checks against operator schedules, cancellations, fares and fleet
capacity. A feed's advertised validity range does not prove operational accuracy.

The NMMT public route directory includes depot movements and a labelled test
route. Route membership alone does not prove an active passenger service.
The pilot schedule query for a route listed in that directory returned
`NO DATA FOUND`; this is not evidence of zero passenger demand.

The newer `nmmt_current_*` public portal uses a different API. Its directory
and route queries return departures, while a separate query supplies each
trip's timed stop names. The [NMMT audit](../data/processed/acquisition/nmmt_schedule_audit.json)
reports acquisition coverage and unresolved stop matches. No queried response
supplies a service calendar. Stop-name matches, midnight wraps, short turns and
depot movements require checks before conversion to a runnable schedule.

`metro1_faq` and `metro1_schedule` give different headway/day-type descriptions.
The dedicated schedule is more specific, but its full time-band timetable and
effective date still need confirmation. Do not combine the two into a synthetic
observed schedule.

`metro_timetable_april2026`, PDF pages 1–3, announces independent Line 2A,
integrated Lines 7/9 and the first Line 2B section from 8 April 2026. A current
model cannot inherit the operating-line list from older planning reports.
Subsequent changes, Aqua Line, Navi Mumbai Metro and monorail status still need
their own dated operator evidence.

## Water transport

The obsolete MMB PDF URL returns HTML. The new official website exposes public
statistics and service-directory APIs; their responses are acquired separately.
The [water audit](../data/processed/observed/_water_evidence_audit.json) records
conflicts that prevent automatic target generation.

The annual-series IDs and directory IDs do not identify the same routes.
Separately named routes sometimes have identical annual series. Those rows
must not be silently deduplicated or summed. `NIL`, a blank and numeric zero
remain distinct. Statewide routes require geographical filtering.

Capacity fields contain ranges, seasonal values and possible fleet totals.
They cannot all be interpreted as passengers per vessel. First and last
departure times do not establish frequency, and annual totals do not establish
weekday or peak-hour boardings. Vehicle-carrying ferries require separate
passenger and vehicle capacities and counts.

## Current rail and metro evidence

`wr_timetable_20260901_index` links a September 2026 main-line timetable,
AC subsets, Dahanu services and a separately dated Harbour attachment. The
documents must retain their own effective dates. AC supplements overlap the
main timetable and cannot be added as extra services.

The [WR extraction audit](../data/processed/observed/_wr_timetable_audit.json)
accounts for printed time cells by page. The table preserves row alignment
and PDF coordinates, not a validated station-stop association. Passing times,
through-service annotations, calendar restrictions and midnight continuation
must be resolved before creating a simulation schedule.

`mmrcl_all_stations` and the station-detail responses describe the complete
Aqua Line directory. The [station audit](../data/processed/observed/_metro3_station_audit.json)
finds that its neighbour graph still breaks into earlier project sections.
The public FAQ describes end-to-end operations, so those breaks are source
inconsistencies, not evidence of disconnected passenger services. Missing
links are present in the operator's separate public journey planner. The
[journey audit](../data/processed/observed/_metro3_journey_audit.json) checks
the complete forward path against the reverse path and the station directory.
It records the two connections missing from the station-detail responses.
The adjacent-segment distances differ from the end-to-end distance by one metre.
Both values remain as published. Every adjacent journey returns zero duration;
no running time is derived from those unusable values. The planner's internal
`line_no` is not the public metro line number. Adjacent fares are not additive.

Some gate fields labelled latitude and longitude contain values outside degree
ranges. Preserve those raw values; their CRS is unresolved. Empty gate geometry
and empty first/last-train arrays remain missing. Schematic diagram coordinates
are excluded from geographic tables. One station's type also conflicts with
its textual description. Operator publication does not remove the need to audit.

`mmrcl_passenger_faqs` supplies different weekday, Saturday and Sunday headways.
`mmrcl_faq_trains` gives regular terminal operating hours, an approximate journey
duration and maximum crush capacity at a stated standing density. That maximum
is not a measured comfortable capacity, seating count or observed train load.

`mmrcl_public_notices`, notice 47, extends terminal service during Ganeshotsav
from 14 to 25 September 2026. Notices 49 and 40 change tourist-pass prices and
trip-pass validity in September. Ordinary and festival service must remain
separate calendars; neither an undated FAQ nor today's exceptional service
defines every model day.

`metro1_metro_train_schedule_20260918` gives regular weekday headways and
terminal hours. The operator's FAQ retains different headways and a different
definition of weekdays. Prefer the dedicated schedule page for the published
current summary, while retaining the conflict; exact departures and weekend
service are still missing. Neither summary alone establishes a full timetable.

`monorail_status_official_20260918` retains suspension until further notice,
alongside older operating text. `monorail_safety_20260221` describes certification
and pending final clearance, not a reopening. A base-date status and a future
restoration scenario require separate evidence.

## Metered fares

`mmr_tariff_index_20260918` links revised taxi and autorickshaw tariff cards
dated 1 September 2026. Their scanned pages were visually checked; selected
values and page anchors are in [fare transcriptions](../extract/fare_transcriptions.json).
The cards distinguish minimum fares, distance rates, night surcharges, waiting
and qualifying luggage charges. Taxi air-conditioning has a separate uplift.
Use the published rounding sequence. These are published tariffs, not measured
transaction prices, shared-auto fares or app-aggregator products.

## District reviews and project reports

The World Bank's 2019 survey, described in `worldbank_mumbai_gender_transport_2021`
PDF pages 6-8, covers Greater Mumbai households with at least one man and one
woman aged 18-45, with stated institutional exclusions. It does not cover all
MMR households or all ages. The publication supplies summary evidence; the
underlying survey records have not been acquired. `suri_cropper_mumbai_2024`
uses this survey for commute-choice estimation and approximates work locations
within postal areas. Its coefficients and locations cannot be treated as
direct observations for every Mumbai resident or for the 2026 network.

[Published observation transcriptions](../extract/published_observations.json)
retain source hashes, periods and counting definitions. They are candidate
validation evidence. Metro One's monthly ridership label must be reconciled
with simulated boardings; JNPA's TEU throughput and reported rake counts have
different units. No daily schedule is inferred from an annual total.

The public `wri_mmr_*` GIS service supplies complete feature responses when
checked against its object-ID lists. The [GIS audit](../data/processed/acquisition/arcgis_boundary_audit.json)
finds valid source geometries but incomplete current regional coverage: the
taluka layer omits Palghar. Its publication date does not establish the age of
its boundaries. Repeated census codes occur with different names or talukas,
and a census ward has multiple source polygons. Candidate code matches are
retained; no population has been assigned and no polygon silently dissolved.
Source `Shape__Area` values are in Web Mercator. Local metric areas must be
computed in the city's projected CRS.

The five `district_review_2025_*` publications are acquired from the Konkan
Divisional Commissioner's official annual-report index. Their tables can have
different reference years, including Census 2011. Marathi text extraction is
partly usable and partly affected by legacy fonts. Table values require a
page-level check before they become demographic or employment controls.

The `mmr_metro_dpr_*` reports contain design assumptions, historical surveys
and demand forecasts. An uploaded file's date does not establish survey year.
Proposed lines, modelled ridership and design capacities must retain those
classifications; they are not observations of current service or crowding.

## Current timetable and fare conflicts

The current NMMT passenger portal supplies a route directory, departures and
trip stop sequences through public information queries. The complete route
response collection identifies 9,522 trip queries across 619 routes. All those
trip-detail responses are acquired. The audit retains clock reversals: route 5582, trip
10513, for example, lists 07:05 at Thane, 08:33 at intermediate stops, then
07:34 and 07:35 near Airoli. These are source inconsistencies, not valid
negative travel times. Neither this API nor an exact stop-name match supplies
a service calendar or proves that a trip operates. The older NMMT service's
empty timetable response is not evidence of absent demand.

The Metro 3 fare-image extractor retains all published cells and template
classification diagnostics. The chart's Marol Naka to Science Centre cell
shows INR 50; the reverse cell shows INR 60. Separate calculator queries return
INR 60 in both directions. This visually checked conflict remains in the
audit. The extractor does not select or correct a model tariff.

`mmr_metro_april_2026_timetable`, PDF pages 1-3, confirms separate Line 2A
operation, integrated Lines 7/9 and Line 2B phase 1 from 8 April 2026. The PDF
repeats its ten-page block three times; these are not independent observations.
`mmr_line9_sept_2026_block`, page 1, moves the start of Lines 2A, 7 and 9 phase 1
to 06:30 during 15-25 September 2026. It describes phase 2 commissioning trials,
not passenger opening. A representative regular day and these exceptions must
not share an undifferentiated calendar.

## Household and demographic controls

The four `census_hl14_*` workbooks report household percentages. Their assets
describe possession, not vehicle counts; a household can possess several types.
The household-size bins sum to approximately 100 because the source rounds
percentages. The extractor retains those differences and all geographical
levels. Nested levels and rural, urban and total rows must not be added together.

`census_c14_maharashtra` age bands reconcile to each selected district's total
and to its PCA population. `census_c12_maharashtra` school-attendance and
economic-activity categories reconcile within each age and to the 5-19 total.
Neither school attendance nor worker status establishes daily trip frequency.
The two `census_hh1_*` files reconcile household-size counts. Their normal
household universe excludes institutional and houseless households; it differs
from the PCA population universe. These sources cannot be joined as if their
denominators and geographical levels were interchangeable.

`census_c13_maharashtra` supplies single-year ages through 99, a 100+ group
and unstated ages. Its counts reconcile to every selected C14 age/sex/residence
control. `census_b01_maharashtra` work-status populations also reconcile to C13.
Main and marginal work describe annual work duration, not full-time and
part-time employment. Seeking/available-for-work counts overlap their parent
categories. B01's 15-59 and 60+ rows overlap detailed age bands; its population
total includes children under five although no separate 0-4 row is published.
The extraction retains these distinctions and does not invent a conversion to
the framework's existing Australian labour categories.

## Activity and travel surveys

The public TUS 2024 documentation is acquired. Its unit-record download requires
a signed-in application and acceptance of the displayed data-use agreement.
The application has been prepared; acceptance remains with the user. No unit
records are acquired at this checkpoint. The README specifies household and
person/activity files, household/person linkage keys and final weights of
MLT/100. Activity rows are not distinct people. The user note explicitly limits
estimation to time-use indicators: auxiliary demographic fields must not be
used to estimate population totals, sex ratios or employment distributions.
The survey's age-six threshold and 30-minute recording intervals also limit
its use for young children's travel and short trips.

`nhts_2025_26_schedule` is an acquired questionnaire, not survey observations.
PDF pages 25-36 distinguish household and commercial vehicle counts, work and
education travel, non-fixed workplaces, other trips and overnight travel.
School-trip reporting uses a different reference period from daily work travel;
the non-fixed-workplace block records only three trips. Annexure 1 separates
shared and exclusive auto-rickshaws, app taxis, private buses, metro and suburban
rail. These distinctions are relevant to the city adapter. Released microdata,
sample design and sufficient local coverage still need to be established before
any of these questions can supply calibrated trip rates or mode shares.
The acquired companion `nhts_2025_26_instructions`, PDF page 123 (section 4.6.0),
explicitly excludes trips shorter than one kilometre. Its page 139 limits
non-fixed-workplace reporting to three trips per person. Using those records
alone for all-purpose demand would omit short walking trips and truncate some
mobile workers' travel. Their absence must not be interpreted as zero demand.

## Employment and activity controls

The Maharashtra final Sixth Economic Census report supplies historical district
establishment and employment controls. Tables 2.8 and 2.9 reconcile across all
35 historical districts and to the public dashboard's state totals. The blank,
shaded rural cells for Mumbai and Mumbai Suburban in table 2.8 are preserved as
derived differences between combined and urban counts, not printed observations.
The census excludes crop production, plantation, public administration, defence
and compulsory social security. Persons engaged at establishments are not
unique resident commuters. Thane uses its historical boundary before Palghar's
creation; the totals cannot be joined directly to current districts.
The dashboard's first detail page is only a partial establishment listing. Its
`totalRecord` and `totalWorkers` fields describe all India even after filtering
the state; `counter` and `wcounter` reconcile to the selected state's report.
The final and provisional reports are separate acquisitions, not two independent
measurements of employment.

The TUS 2024 report's state statements 3.1-7.1 supply Maharashtra activity
participation and duration benchmarks by residence and sex for ages six and
above. The extractor checks participation against per-participant and per-person
durations using the rounding precision of the printed tables. Nine activity
durations sum to 24 hours within rounding. Major-only and all-activity estimates
retain separate labels. These are state averages, not Mumbai diaries, observed
trip rates, workforce totals or travel times. Unit diaries remain subject to
the data-use agreement; public summary extraction does not resolve that gap.

## Education controls

Public MoSPI education queries currently provide state controls for UDISE
2024-25 and AISHE 2021-22. The extracted counts reconcile within each reported
gender breakdown. State codes differ across those APIs; query selection uses
the returned state label and validates the state and year in every data row.
All-management, combined education levels and gender totals overlap their
components. AISHE labels student enrolment as estimated. Neither dataset
establishes metropolitan totals, individual facility capacities or attendance.
The public API specifications are archived at their source commit. They are
read as documentation; their client code, which disables TLS verification, is
not executed. Acquisitions retain certificate verification through Windows TLS.

## Spatial support layers

The extended-area planning notices are distinct from the metropolitan boundary.
The English Schedule IV in `mmr_ena_spa_notification_20240709` lists consecutive
serials 1-446: 223 villages in each district. The later
`mmr_ena_raigad_plan_notice_20250918`, PDF page 3, instead states 224 in Palghar
and 223 in Raigad. Visual inspection of the earlier PDF's page 34 confirms the
district changes between serials 223 and 224. The extractor preserves this
conflict. Neither list is a complete list of all settlements in MMR.
The 1985 Scheduled Areas order is also acquired because the 2019 extension
notification refers to exclusions. Its historical place names, subsequent
changes and relationship to the later planning notices remain to be reconciled.
No legal exclusion has been converted to a modelling exclusion: connecting
travel must remain represented even where planning jurisdictions differ.

Raster acquisition uses an envelope derived from the five acquired district
boundary datasets. It deliberately covers more than the provisional model
region. The GHSL grid is intersected in its native projected CRS: projecting
the entire global tile grid can produce invalid polygons at the projection rim.
The selected tile and source hashes are recorded by the registration script.

OSM points, lines and multiline relations are extracted from the acquired PBF
within this research envelope. An exact geometry intersection checks the OGR
spatial filter. Intersecting features retain their complete geometry, including
long routes outside the envelope. The resulting GeoPackage preserves OSM IDs
and driver-exposed tags but does not retain complete native node references or
restriction relations. It is evidence for mapping and cross-checks, not a
routing network. No geometry repair or modal access inference is applied.
These derived layers retain ODbL attribution and source lineage.
The GeoPackage container timestamp comes from the immutable acquisition record,
using [GDAL's reproducibility option](https://gdal.org/en/stable/drivers/vector/gpkg.html#creation-issues).
It is not a feature observation date. A repeated build under the recorded GDAL
version produces the same file hash; cross-platform equivalence is not claimed.
The transport-point inventory preserves source names, all driver-exposed tags,
OSM node IDs and geographic/projected coordinates. It includes station nodes,
stops, entrances, ferry terminals, taxi ranks, crossings and signals, with
proposed and construction tags intact. Multiple selected tags can describe
one node, so tag counts are not additive. Polygon-only stations, unmapped
facilities and route-relation stops require further extraction and comparison.

GHSL's population and building products are estimates, with source years and
projection methods defined in `ghsl_methodology_2023`. A 2025 layer is not a
new census. Copernicus GLO30 is a surface model that includes vegetation and
buildings; it is not a surveyed road surface or a tunnel/bridge alignment.
These layers require local checks before spatial allocation or slope modelling.

### NMMT published map geometry and tracking queries

The public passenger map exposes route vertices in response order. The
[geometry audit](../data/processed/acquisition/nmmt_path_audit.json) records
coverage, empty responses, coordinate ranges, duplicate vertex identifiers and
ellipsoidal segment lengths. These paths still need road matching, direction
checks and comparison with physical stop locations. They are published
alignments, not measured vehicle trajectories.

The bus directory snapshot lists identifiers rather than an active fleet.
The first queried vehicle returned no locations. The route query for 5582
returned stop records with no vehicle indications. Its origin has zero distance
fields, while the terminal reports 10 km cumulative distance. Distance fields
must be interpreted by position and meaning, never as measured travel times.
Route tracking snapshots are sequential queries with individual retrieval
timestamps; they do not form a simultaneous fleet census. Timetable calendars,
capacity, observed dwell and running-time distributions remain unresolved.

### Native OSM topology and Coastal Road rules

The [PBF conversion audit](../data/processed/acquisition/osm_conversion_audit.json)
records the complete source extract converted to compressed OSM XML. It retains
node coordinates, way-node references, relation members and tags. Contributor
metadata and header bounds are omitted. This is a format conversion of the
whole source extent, not a clipped city network or proof of connectivity.
The converter uses the existing pinned Java stack. A synthetic round-trip
check covers conditional access tags, turn restrictions, nested relations,
large identifiers, Unicode and deterministic compression.

The [Coastal Road transcription](../extract/transcriptions/coastal_road_order_187_20260825.json)
records the English notification on PDF pages 3-4, with the raw source hash.
It preserves the heavy-vehicle exceptions for passenger buses and emergency
vehicles, the separate two-wheeler/three-wheeler/pedestrian bans, directional
access points and speed limits by road section. The press note on pages 7-8
abbreviates the exceptions. The notification states 24-hour access and repeals
previous temporary corridor notifications. It remains subject to further
orders: a single-pass transcription does not establish the absence of later
amendments. OSM links, junctions and modal classes are not yet assigned.

The [Western Express Highway amendment](../extract/transcriptions/western_express_order_155_20260626.json)
records notification 155 of 26 June 2026 from English PDF pages 3-4. It sets
heavy-vehicle restrictions in both directions between Bandra and Dahisar at
08:00-11:00 and 16:00-21:00, except Sundays. It also preserves all other terms
of notification 227 of 29 December 2025. That predecessor has not been located
in the acquired index. Its exceptions cannot be replaced by an empty list or
inferred from another corridor's order. The transcription remains incomplete
for model use until the predecessor, later amendments and road links are checked.
An installed Windows English OCR engine helped locate the clauses; the source
images were read separately. English OCR does not validate Marathi pages.

### Vehicle registration controls and conflicting office labels

The [vehicle audit](../data/processed/acquisition/rto_2025_audit.json) extracts
stock at March 2025 separately from new registrations during 2024-25. Category
sums within each printed column reconcile. Office-to-region and office-to-state
checks retain discrepancies in the provisional stock table. Mumbai East and Borivali totals are
reversed between the summary and category-table labels for both measures.
The extraction preserves the printed column order and marks those columns as
conflicted. Their apparent exchange is not a verified correction. Regional
and category subtotals are flagged to prevent double counting. Registration
offices still need a jurisdiction crosswalk; registered vehicles are not an
active fleet, household ownership distribution or observed traffic volume.

The 2025 bike-taxi rules, bike-taxi resolution and EV policy are acquired from
the [Transport and Ports Department](https://transports.maharashtra.gov.in/en/documents/).
Their policy conditions do not establish which operators have valid licences
or which services operate on the simulation date. The 2016-17 transport
statistics provide historical context, not current fleet targets.

### NMMT reported vehicle times require status-aware interpretation

The [vehicle detail audit](../data/processed/acquisition/nmmt_vehicle_detail_audit.json)
separates covered, skipped and upcoming stop records. The public client displays
arrival/departure fields as actual times only for covered stops. Some skipped
records carry schedule values in an actual-named field; those cannot become
observed dwell or running times. Source clock strings and refresh flags are
retained without assigning an unverified timezone or freshness threshold.
Tracking trip IDs remain separate from timetable trip IDs. Snapshot vehicles
are a selected set indicated by public route queries, not a complete active
fleet census. Covered records still require timestamp and operational checks
before any calibration use.

The completed route-query pass has a raw response for each directory entry;
explicit no-data replies remain empty coverage. The
[stop snapshot audit](../data/processed/acquisition/nmmt_route_stop_audit.json)
compares stop points with operator polylines. Some offsets exceed ten kilometres,
so exact route identifiers alone do not validate spatial alignment. These
records remain evidence for reconciliation, not snapped network stops.

### OSM reference closure

The [reference audit](../data/processed/acquisition/osm_reference_audit.json)
checks each entity ID and every way-node and relation-member reference in the
whole acquired source. IDs are unique and all way-node references resolve.
Some relation members are absent, including route and administrative-boundary
members. The [complete missing-reference table](../data/processed/acquisition/osm_missing_references.csv)
preserves parent IDs, relation types, member order and roles. No missing member
belongs to a restriction relation. This does not prove that all real-world
restrictions are mapped, or that a city network is connected and legally
routable. Cross-boundary relations require reconciliation before use.

### Port rail movements

The [JNPA daily rake audit](../data/processed/acquisition/jnpa_rake_audit.json)
reconciles each handled-rake cargo subtotal and all printed column totals.
Arrival, completion and departure dates are separate; a handled-date table
contains arrivals from earlier days and departures on later days. Blank
departure cells remain missing. Calculated elapsed times use the printed local
clocks without a timezone assumption and must not be confused with the port's
handling-time measure, which can exclude delays. Multiline destination and
train-label cells are not yet resolved. These selected daily reports are not
a complete timetable, path assignment or representative operating calendar.

The [Mumbai Port monthly audit](../data/processed/acquisition/mumbai_port_monthly_rakes_audit.json)
keeps inward/outward and loaded/empty rakes separate. Commodity and wagon-class
subtotals reconcile with monthly and annual totals. One blank commodity cell
is derived from its printed subtotal, with the identity recorded; it is not
labelled observed. Subtotal flags prevent double counting. These are port-rail
movements, not all metropolitan freight trains, wagons or road vehicles.

JNPA's [August departure notice](https://www.jnport.gov.in/uploads/media_center/1/1798/JNPA_PR_-_Long_Haul_DFC_Operations.pdf)
records a long-haul double-stack DFC movement. That event must not be expanded
into an assumed daily frequency or used alone to establish every corridor's
commissioning date. Current line occupation and conflicts with passenger
services still require route and operating evidence.

### Navi Mumbai Metro annual observations

The [annual control audit](../data/processed/acquisition/navi_metro_controls_audit.json)
extracts Navi Mumbai's operating paragraphs from Maha Metro's current public
annual-report directory. The corporate reports also cover other cities; their
ridership and train specifications are not transferred to this line. The older
report's utilisation, headway and operating window describe its initial
financial year. The newer report describes a later headway change and a
special-event service. These periods and the event remain separate.

The published percentage growth disagrees with the two reported daily averages.
Both the source claim and the arithmetic check remain visible. Repetition in
the same report's highlights is not independent corroboration. Ridership stated
in decimal millions retains that precision, and punctuality/availability
statistics still need their measurement definitions. Current full departures,
peak clock boundaries, fares and seated/standing capacities remain unresolved.

### BEST fares, depots and operating records

The [BEST control audit](../data/processed/acquisition/best_controls_audit.json)
preserves the operator's published fare and pass tables. The Marathi PDF prints
8 May 2025 as its effective date. This is the printed date, not independent
proof of implementation or the absence of later amendments. Fare-stage distance
differs from the distance between boarding and alighting stops. AC tax,
concessions, luggage and toll additions require their own rules. The undated
facilities page conflicts with the dated fare table on AC concessions.
The [transcription](../extract/transcriptions/best_fares_passes_20250508.json)
records the reading and unresolved eligibility; it has not had an independent
language review.

Depot-route listings establish published associations, not a current timetable.
Two missing HTML delimiters are repaired in memory with exact matches recorded
in the audit. Raw bytes are unchanged. Route labels retain leading zeros and
variant text. In this bus directory, a `FORT FERRY` label is a bus service.
The linked route-network host timed out through both the downloader and Chrome.

BEST's public departmental manuals identify existing schedule, fleet-capacity,
loading-survey and operational-statistics records. Their descriptions are
evidence of records held, not acquisition of those datasets. The
[data specification](requests/best_operations.md) identifies the relevant
manual pages and missing fields. No request has been sent.

### Bus fleet snapshots and historical operator controls

The acquired OpenCity copy of BMC's 2025–26 climate budget retains BMC authorship;
byte identity with the unavailable original is unverified. PDF page 53 gives a
ridership forecast, not observed trips. Page 63 labels another figure as an
annual average without establishing its temporal denominator. Pages 113–115
mix fleet snapshots, procurement plans and infrastructure. A repeated charging
paragraph is one claim. These cannot become current daily ridership or fleet
controls without resolving definitions and dates. The environment report also
contains fleet snapshots; its publication year does not date each observation.

The [MoRTH historical audit](../data/processed/acquisition/srtu_controls_audit.json)
extracts Annexure I for BEST, NMMT, Thane, Kalyan-Dombivali and Maharashtra SRTC.
The years include pandemic restrictions. Maharashtra SRTC covers a statewide
network. Printed lakh units and `NR` are retained; missing is distinct from
zero. Fleet-utilisation and passenger-kilometre occupancy ratios are checked
at printed precision. This arithmetic agreement does not resolve NMMT's
unusually small 2021–22 passenger count or validate the passenger-kilometre
units. NMMT fleet age is `NR` in Annexure I but zero in Annexure VI; the latter
must not fill the missing observation.

The [manufacturer capacity evidence](../data/processed/acquisition/bus_capacity_evidence_audit.json)
keeps Tata's historical BEST order configurations separate from Olectra's
product range. Switch's brochure technical table and descriptive text disagree
on seating capacity; both claims remain visible. None of these publications
establishes current vehicle availability, licensed standing places or departure
assignments. Range and charging claims are product conditions, not measured
operating dwell. A procurement count must not become an active fleet count.

### Mira-Bhayandar route data and fleet claims

The [MBMT route audit](../data/processed/acquisition/mbmt_route_audit.json)
covers every entry of the acquired public route directory. Stop-detail queries
give cumulative distance and minutes, not dated departures. Some minute series
equal the zero-based stop index throughout. This pattern is preserved as a
warning against interpreting a mechanical sequence as measured running time.
Empty responses remain empty coverage. Stops and details reconcile by response
position and exact name; this does not establish an operating calendar.

Every comparable map response lies closer to its published stops when the
latitude/longitude field meanings are exchanged. Both interpretations and
their nearest-vertex distances are reported. Some large remaining separations
still need reconciliation. Raw fields remain unmodified; a preferred axis
interpretation does not prove legal road matching, direction or stop placement.

The [municipal control audit](../data/processed/acquisition/mbmt_controls_audit.json)
retains the undated fleet and day-type allocation tables. Weekday and Saturday
row sums disagree with their printed totals; neither is silently corrected.
The page also describes an electric fleet absent from its detailed fleet table.
Its additive capacity components are not explicitly labelled seated/standing
in that table. API route IDs and printed route numbers still need a crosswalk.

The acquired electric-bus contract specifies minimum passenger seats for its
standard-bus variants and a stated seating requirement for its midi variant,
each excluding the driver. Standing numbers are referred to a calculation
under AIS 052, not supplied. The visually checked
[transcription](../extract/transcriptions/mbmt_electric_bus_contract_capacities.json)
preserves this distinction. Contract specifications do not establish delivered
configurations, current availability or the vehicles assigned to each trip.

## Historical Scheduled Areas and the planning boundary

The [1985 gazette](https://tribal.gov.in/downloads/CLM/CLM_Declare/1.pdf), PDF
page 8, names 144 Palghar and 45 Vasai villages under the then Thane district.
The [transcription](../extract/transcriptions/scheduled_areas_1985_palghar_vasai.json)
retains the English spellings, printed counts and four uncertain scan readings.
It covers these two lists only. The other language version has not been
independently checked.

The [name audit](../data/processed/acquisition/scheduled_area_name_audit.json)
compares case/punctuation-normalised names within the same named taluka, with
no fuzzy matching. It finds one census settlement candidate for 96 Palghar
and 20 Vasai entries; the remaining 48 and 25 have none. It also finds one
2024 extended planning-area candidate for 88 Palghar and 10 Vasai entries.
These are name candidates, not an accepted historical geography crosswalk.
Absorption into towns, renaming, splits, uncertain transcription and boundary
changes remain to be checked. No model polygon is included or excluded.

The [2019 MMR extension notification](https://mmrda.maharashtra.gov.in/sites/default/files/2021-09/MMR_Extension_Notification_0.pdf)
refers to Scheduled Areas in its recitals and supplies a perimeter in Schedule I.
The overlapping names in the later planning list mean that simply subtracting
the historical village list is not an established boundary construction.
The [state administration report for 2017–18](https://tribal.maharashtra.gov.in/Site/Upload/GR/Administration%20Report%202017-2018.pdf),
PDF page 7, distinguishes the main and additional Tribal Sub Plan areas and
MADA categories. Those labels are not interchangeable filters.

The [Palghar Zilla Parishad setup page](https://www.zppalghar.gov.in/about-department/administrative-setup/)
was also acquired. It has a 2018 publication label and aggregate PESA village
counts, but no dated village-code crosswalk. Its totals therefore do not resolve
the extent or justify applying today's administrative counts to the 1985 list.

## State and district population projections

The acquired [National Commission on Population report](https://www.nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf)
is the **November 2019** edition named on its cover. The extraction retains
Maharashtra totals and urban populations at three distinct reference dates
(1 March, 1 July and 1 October), five-year age groups, published age percentages
and the single-age school/young-adult table. Counts remain in the published
thousands. Table 20 omits the unit in its title; its unit is explicitly derived
by reconciling complete five-year groups with Table 18, rather than silently
treated as persons. The supplementary `0-1` row overlaps `0-4` and is excluded
from partition sums. The 2011 age profile is a smoothed baseline.

The [state audit](../data/processed/acquisition/state_population_projection_audit.json)
records 822 arithmetic comparisons, all exact or compatible with independently
rounded cells. This checks extraction and arithmetic, not projection accuracy.
No state growth rate has been applied to Mumbai's wards or households.

The [IIPS district projection report](https://www.iipsindia.ac.in/sites/default/files/FULL_REPORT_WITH_FINAL_TABLES.pdf)
(suggested citation: Dhar, 2022; project listed by IIPS for 2022–23) supplies
annual age/sex projections through 2031 on **2011 district boundaries**. The
extractor retains all 35 Maharashtra districts, allowing their totals to be
checked against the state projection. Its 21,000 detailed rows include totals,
single ages 0–14 and five-year/open groups above 14. Its summary table supplies
175 district/year rows, including the 2011 census baseline.

The [district audit](../data/processed/acquisition/district_population_projection_audit.json)
records 1,720 exact or rounding-compatible comparisons. The four acquired
census district baselines match by district name and both sex totals. Report
row numbers and within-state numbers are not Census or current LGD identifiers.
The old Thane district includes the area subsequently separated as Palghar;
the projection cannot be applied independently to both today's districts.

For Maharashtra, the publisher selects Ratio Method 1: district-share changes
from 2001–2011 are extended to 2021, then held constant. Age shares are projected
analogously; childhood single ages use Sprague multipliers (PDF pages 17–18
and 38). This is a published model, not observed migration or age composition.

The 2025 sum for Mumbai and Mumbai Suburban differs from the BMC civic diary's
Greater Mumbai estimate by 504,770 persons. The audit preserves comparisons
with both diaries and the environmental report. Their dates, methods and
geographies still require reconciliation; none is averaged or overwritten.
Small-area growth, household composition and current employment/education
distributions still need evidence before a 2026 synthetic population is built.

The full English [Economic Survey of Maharashtra 2025–26](https://mahaces.maharashtra.gov.in/files/EconomicSurvey/esm_2526_e.pdf)
has also been acquired from the statistics commissioner's own publication
index. It provides another dated source for population and transport controls;
acquisition alone does not validate or incorporate every table into the model.
Its population chapter cites the same NCP and IIPS projections (PDF pages 37–38),
so these repeated figures are not independent validation observations.

The [transport audit](../data/processed/acquisition/economic_survey_transport_audit.json)
retains Table 9.27's daily operating vehicles, passenger averages and effective
kilometres for 17 bus providers, at the printed 31 March 2024 and 2025 dates.
The averaging period is not specified beyond that heading. The three missing
2024 Ulhasnagar cells remain missing. An average vehicle count is not a fleet
inventory or route assignment. Other-state-region operators and the statewide
MSRTC city-operation row cannot be assigned wholly to MMR.

Section 9.29 gives a 2024–25 Mumbai suburban aggregate: fleet, AC fleet subset,
services, AC service subset and average daily passengers. These are retained
separately from timetable departures and current stock formations. The report
does not resolve whether the passenger count represents unique people,
journeys or boardings, so it is not yet a directly scorable simulation target.

## Historical census geography joined to population controls

`extract/build_census_geographies.py` produces a spatial population input with
every source census leaf retained once. The `census_leaves` layer in
`data/processed/geospatial/census_2011_geographies.gpkg` carries the original
79 count columns, source identifiers and explicit geometry status. It uses the
city's declared projected CRS. This layer does not select the metropolitan
extent or estimate a current population.

All 3,630 rural records match the IIT Bombay files by administrative codes and
normalised village names. The 49 untruncated common count fields provide
171,157 exact cell comparisons. The 6,713 blank GIS cells remain missing, while
the joined count columns come from the Census workbooks. Of these village
records, 137 have no polygon in the IIT Bombay source. One polygon has a ring self-intersection. GEOS
linework repair preserves its calculated projected area; the audit records
both geometry hashes, the reason, method and software versions.

The WRI ward source has 98 polygons for 97 census keys. Two polygons claim the
same Nahur ward key but cover different areas. Both remain in the separate
`ward_source_candidates` layer. The census leaf retains its population once
and has null geometry until the duplicate is resolved. The other 96 ward
polygons join by the complete census identifier and name.

The WRI village/town layer supplies another 125 polygons: 92 missing village
geometries and 33 towns represented by one census ward each. Each match requires
exact state, district, subdistrict and place codes, plus a normalised place name.
Name normalisation removes case, punctuation and printed census type markers.
It does not correct spelling or substitute another place. The audit retains
nine name conflicts and one duplicate-code rejection. A town with multiple
census leaves cannot supply a polygon for any individual ward through this join.

The [geography audit](../data/processed/acquisition/census_geography_audit.json)
checks that all 4,813 leaves and every district count total survive the join.
It reports 3,714 records with polygons and 1,099 with unresolved geometry.
Of the latter, 1,053 urban wards have no polygon in these selected sources.
The remaining gaps are 45 villages and the ambiguous Nahur ward.
The crosswalk CSV identifies every unresolved record; none receives a guessed
centroid, a zero population or an allocation across duplicate polygons.

This is an intermediate input for population construction. Polygon accuracy,
cross-polygon topology, remaining urban geometry and current MMR inclusion
still require resolution before home locations can be generated.

## Native network input and portable source selection

The [rail geometry audit](../data/processed/network/rail_geometry/audit.json)
records 48,273 native nodes, 5,643 railway-tagged ways and 49,625 adjacent-node
segments. Its [way table](../data/processed/network/rail_geometry/ways.csv)
preserves complete node order and tags, including 4,124 rail, 438 subway and
37 monorail ways. These are mapped objects in the research extent, not counts
of operating routes. Platform outlines, station areas, inactive infrastructure
and construction remain labelled evidence; 452 ways explicitly carry area tags.

The portable reader computes both WGS84 ellipsoidal and city-projected lengths,
with units in the column names. It does not snap coincident nodes, simplify
curves, infer junctions at crossings, reverse source order or insert a minimum
link length. All selected references resolve, and no zero-length segments occur
in this extraction. Source node identity preserves grade-separated crossings.
The lengths are horizontal; gradients still require separate evidence.

Two complete builds produce identical bytes. Tests cover coincident crossings,
duplicate/conflicting inputs, missing references, inactive/area geometry,
zero-length retention, metre-unit checks and another projected CRS. Source tags
retain direction, speed, gauge, signal and switch evidence without inventing
operating defaults. The package still needs route allocation, dated operating
status, rail permissions and a physical train-control/capacity representation.

The [MRVC CBTC consulting reference](https://mrvc.indianrailways.gov.in/mrvc/notice/1565425828445_CBTCTOR090918.pdf)
is catalogued for historical signalling/headway evidence, but remains unobtained
after both verified download transports failed. Search-index figures are not
adopted as current headways or model capacities.

`extract/build_osm_network_source.py` selects native OSM entities from the
immutable PBF, using the previously derived administrative research envelope.
It reads line ways and closed area ways, plus tagged point features. Whole ways
retain their original node sequences even where they cross the envelope.
Touching turn restrictions retain every member, role and tag. Missing selected
members or duplicate identifiers prevent publication of the derived file.

The [native network audit](../data/processed/acquisition/osm_network_source_audit.json)
records 5,441,839 nodes, 687,975 ways and 333 restriction relations. These counts
describe the OSM input, not MATSim links or operational services. The source
contains buildings and other mapped features as well as transport ways. The
extractor does not assign permissions, capacities, speeds or service calendars.

Two native builds have the same SHA-256. The independent reference audit checks
6,279,094 way-to-node references and all 998 selected relation members, with no
missing references or duplicate IDs. The spatial parser reports four invalid
selected area geometries and source-wide ring warnings. Native way sequences
remain unchanged; these warnings do not justify geometric repair or legal
boundary claims.

The city's `osm_network_inputs` declaration supplies this combined compressed
source to the shared network builder. The portable contract accepts ordered
`.osm` and `.osm.gz` files under `networks/osm/`. Cities without the declaration
retain the existing four-file input order. The city readiness inventory reads
the declared paths, and the manifest traces the network source to its inputs.
The manifest classifies this native source as derived, despite its location
under `networks/osm/`. Its ancestry follows the declared producing script.
The shared builder's lineage resolves the exact city-selected input list,
excluding unrelated files in the same directory.
The shared `--stage osm` command has prepared the Mumbai source successfully.
Newcastle's existing merged XML remains byte-identical under the new reader.

The native source retains ODbL attribution and remains uncommitted bulk data.
The full source still holds route, public-transport and boundary relations
which this network extract does not copy unless a selected restriction requires
them. These remain separate inputs for service and boundary construction.
Native reference closure does not verify conditional restrictions, current
legal access, signal behaviour, all-mode connectivity or simulation accuracy.

Further capacity research identifies the 2016 Gajjar and Mohandas Mumbai field
study and a 2026 JVLR corridor study. The first full paper remains unobtained;
the JVLR paper and its earlier conference poster are now acquired through the
public Chrome session after ordinary delivery failures. The acquired CRRI manual
index points to the already acquired Indo-HCM excerpts and a procurement
procedure. Excerpts, design service volumes and observed traffic counts cannot
be substituted for a validated per-link flow capacity.

### Native transport attributes

The [transport tag audit](../data/processed/acquisition/network_source/transport_tag_audit.json)
describes 238,072 linear transport ways in the research envelope. It excludes
512 area ways from linear statistics and retains their geometry in the native
source. Its [value table](../data/processed/acquisition/network_source/transport_tag_values.csv)
keeps raw values, units, parse status and way counts. It preserves directional,
mode-specific and conditional tags separately; it does not assign access or
network capacity. Duplicate ways across ordered sources use the first source,
matching the network merger.

Coverage is sparse and uneven. Of 122,350 residential ways, 299 carry a speed
tag and 829 carry a lane count. Primary roads have 298 speed tags among 4,806
ways. There are 37 ways marked `oneway=reversible` and 17 marked `oneway=-1`.
No conditional way tags occur in this extract's audited transport keys; that
absence does not cancel restrictions in police orders or relations.

The parser converts recognised speed and width units without truncating ranges
or symbolic values. Lane totals remain totals; no equal directional split is
inferred. The class quantiles weight mapped ways equally, so mapping splits and
selective tagging affect them. They are descriptive evidence, not calibrated
defaults. OSM speed limits do not measure free-flow speed, and carriageway
width does not identify usable lane width. Missing values need further evidence.

The public author-hosted copy of the historical road-capacity paper is also
catalogued. Its PDF delivery returned HTTP 403, so it remains unobtained.

### JVLR classified counts and version differences

The final [JVLR proceedings paper](https://doi.org/10.3390/eesp2026045010) is
acquired as a PDF with its CC BY 4.0 notice. The earlier conference poster is
preserved inside the publisher's public JSON download response. Its embedded
PDF hash anchors the manual table transcription; no poster text or figure is
silently replaced by the later version.

The paper reports a survey from 23 to 29 June 2025, selecting 24 June for detailed
analysis because it had the highest aggregate volume. Each of the 18 stretches
has its own one-hour peak window. The
[classified counts](../data/processed/observed/jvlr_journal_classified_counts.csv)
retain cars, two-wheelers, autos, trucks, tempos, buses, cycles and pedestrians
separately. Pedestrians are excluded from PCU conversion. All 18 published PCU
flows reproduce exactly from the classified counts and the paper's stated
factors; all 18 match its physical-control table. These factors reproduce the
publication and are not measured dynamic vehicle equivalents for the simulator.

The [road controls](../data/processed/observed/jvlr_journal_road_controls.csv)
retain lane counts and official reference speed limits reported by the authors.
The paper explicitly uses those limits to calculate indicative density, rather
than observing traffic speeds. Those density estimates cannot validate simulated
speed or density. The [audit](../data/processed/acquisition/jvlr_journal_audit.json)
also retains the changes from the poster, including four revised flow values.
The earlier poster has table/map discrepancies and inconsistent narrative LOS
counts; its separate audit preserves them. Three arithmetic differences in its
per-lane densities are compatible with rounding the intermediate total density.

The counts are dated corridor evidence, not a current full-day demand profile
or a road-capacity measurement. Different peak windows must not be summed as a
simultaneous corridor flow. Count-line georeferencing, raw video and the seven
daily classified tables remain outstanding.

The [road inventory](../data/processed/observed/jvlr_journal_road_inventory.csv)
preserves all 252 published cells for the 18 stretches, including parking,
footpaths, crossings, medians and street hardware. Numeric widths remain tied
to their reported feature: right-of-way width is not usable carriageway width.
An absent footpath does not establish a pedestrian access prohibition. The
table reports 1.5 m footpaths on two Saki Vihar stretches, which the abstract's
broad summary omits. These dated observations still need location matching and
a check of current conditions before network assignment.

The [temporal statistics](../data/processed/observed/jvlr_journal_temporal_variability.csv)
retain all 18 published mean, standard-deviation and coefficient-of-variation
rows. Each coefficient agrees with its mean and standard deviation within
printed rounding. These summaries cannot reconstruct the missing daily counts
or establish current demand. The [inventory audit](../data/processed/acquisition/jvlr_inventory_audit.json)
records the extraction and arithmetic checks.

### Arterial capacity literature

The acquired [Dhamaniya and Chandra paper](https://doi.org/10.1007/s40999-017-0206-7)
provides vehicle dimensions, traffic composition, dynamic PCU summaries and
capacity estimates for divided arterial midblocks in four other Indian cities.
The [extracted tables](../data/processed/literature/arterial_2017_capacity.csv)
retain their original values. They are supporting literature, not Mumbai
observations or adopted parameters. The study selected flat sections without
intersections, bus stops, parking or other side friction. Capacity was estimated
from fitted speed-density curves; most observed flows did not reach capacity.
Its operating speed is a measured free-flow percentile, not a speed limit.

The [arithmetic audit](../data/processed/acquisition/arterial_2017_audit.json)
finds five disagreements: one directional/per-lane capacity identity, a quadratic
coefficient printed as 0.496 in the equation and 0.497 in its coefficient table,
both reported validation percentages, and one narrative/table operating speed.
The printed validation capacities imply errors of approximately 0.476% and
0.323%, rather than the table's 0.10% and 0.05%. These differences remain
unresolved; no version is silently selected for the simulator.

The ordinary HTML download returned a challenge page with HTTP 200. Its bytes
are retained as failed-delivery evidence and marked `acquired_unusable` by a
hash-bound catalogue review. The successful public-browser PDF acquisition is
separate and includes the paper's CC BY 4.0 notice.

### Coastal Road access and the historical island-city boundary

The [Coastal Road candidate geometry](../data/processed/geospatial/coastal_access_candidates.geojson)
and [topology audit](../data/processed/acquisition/coastal_access_audit.json)
retain native OSM way IDs, node references, tags and coordinates for review
against traffic notification 187 of 25 August 2026. Exact corridor names select
57 ways; another seven are named approaches and 44 are search-only matches.
The audit also records 27 adjacent ways, including unnamed ramps. These counts
describe the extraction, not the extent of the legal restriction. One additional
name match in the research GeoPackage has no highway tag and is not a road
candidate. It is a bridge structure, not an omitted routable way.

Two corridor-name candidates carry `access=no`, including one construction way.
The audit retains them for review and does not open them. Shared-node components
do not prove directed connectivity or legal turns. Tagged toll booths help locate
the northern limit, but their OSM charge text is not adopted as the current toll.
The notified extent, unnamed ramps, superseding orders and each mode's exceptions
still require resolution before permissions or speed limits are assigned.

The acquired [V. M. Lal committee report](https://cat.org.in/wp-content/uploads/2017/03/V.-M.-Lal-Committee-Report.pdf)
describes an island-city boundary on PDF pages 30 and 96 (printed pages 31 and
97). The descriptions differ around Dharavi and Sion. The latter says that the
area broadly corresponds to the autorickshaw exclusion area. Both passages sit
within a proposed experimental vehicle-restraint scheme for 2000, not a current
autorickshaw notification. They are historical search anchors; neither defines
a validated 2026 restriction polygon. The committee's weekday registration-digit
proposal is not implemented as a current traffic rule. The government-hosted
taxi/auto committee Part 3 download timed out and remains unobtained.

### Pollution Control Board vehicle activity evidence

The [MPCB Mumbai report](https://mpcb.gov.in/sites/default/files/Establishment%20of%20MPCB/Seniority%20list/2014/Mumbai_Final_El_%26_SA_Report_July_2024.pdf)
is dated December 2023; its hosted filename says July 2024. Neither date is a
verified traffic-survey date. PDF pages 79–80 describe manual classified counts
at 60 major junctions and a two-kilometre grid. Four counting shifts cover the
day: 07:00–11:00, 11:00–17:00, 17:00–22:00 and 22:00–07:00. The nearby vehicle
registration table covers 2008–2018 and does not date the junction survey.

PDF page 84 states that junction/road counts were expanded and allocated to
adjacent grids. Its citywide activity totals are therefore derived movements,
not unique registered vehicles or independent citywide counts. PDF page 85
estimates vehicle kilometres from road length and allocated traffic. These
results require the underlying count lines, dates, directions and allocation
weights before comparison with simulated link flows. The ward/road directory
on PDF pages 82–83 can guide location matching but is not a georeferenced count
station table. No emission factor, activity total or traffic share from this
report has been adopted as a model parameter or validation target.

### Economic Survey metro groups and port units

The 2025-26 Economic Survey's Table 9.34 (PDF page 223) supplies the
[metro route entries](../data/processed/observed/economic_survey_metro_routes.csv)
and [passenger controls](../data/processed/observed/economic_survey_metro_controls.csv).
The printed braces combine Lines 2A and 7 under one daily passenger figure.
The extractor retains that group without duplicating or dividing it between
routes. Nagpur and Pune rows remain source evidence outside the Mumbai demand
scope. The table does not specify its averaging window or whether passengers
means boardings, journeys or unique people. Its commissioning month is a table
entry, not a complete history of each route's opening phases.

Table 9.36 (PDF page 225) supplies the
[port controls](../data/processed/observed/economic_survey_port_controls.csv)
for Mumbai Port and JNPA in 2023-24 and 2024-25. Cargo remains in the printed
lakh MT units, passengers in thousands and vessels in counts. JNPA's passenger
entry is not applicable, not zero. Port passengers have not been established
as local ferry boardings, and tonnes cannot become trucks or rakes without
commodity, load and movement evidence. The 2023-24 JNPA import/export sum differs
from the printed total by 0.01 lakh MT, within the 0.015 lakh MT envelope from
three independently rounded cells. Original values remain unchanged in the
[audit](../data/processed/acquisition/economic_survey_metro_ports_audit.json).

### Metro rolling stock publication scope

The acquired [Alstom opening release of 5 October 2024](https://www.alstom.com/sites/alstom.com/files/2024/10/04/20241005_PR_Mumbai_Metro_Line_3_EN.pdf)
describes a contract for 31 eight-car trains, with 24 delivered at that date.
Its stated capacity is at least 3,000 passengers per train. It does not provide
a seating split or standing density. Delivery, operational fleet and timetable
assignments remain distinct quantities. The release's daily-demand and traffic
reduction claims are prospective; neither is an observed calibration target.
The separately catalogued MMRC August 2022 trial document failed PDF delivery
and remains unobtained. Its search excerpt is not an acquired specification.

The [PIB order announcement of 22 November 2018](https://www.pib.gov.in/newsite/PrintRelease.aspx?lang=2&reg=48&relid=185919)
was acquired through the standard verified HTTPS client after the Windows
client timed out. It describes 63 six-car trains across Lines 2A, 2B and 7,
with a nominal capacity of 300 passengers per coach. It supplies neither a
seating split nor a standing density. The
[extracted fleet claims](../data/processed/observed/metro_fleet_publication_claims.csv)
preserve per-coach versus per-train units, contract versus delivered counts,
publication dates and the manufacturer's lower-bound qualifier. Missing seat
and standing counts remain blank, not zero. No capacity has been assigned to
an operational trip from these releases alone.

### Native road attributes for network assembly

The [way attribute table](../data/processed/network/osm_way_attributes.csv)
retains native way IDs and source hashes and separates mapper-reported lane
totals, explicit directional counts, shared lanes and resolved one-way counts.
The [coverage audit](../data/processed/acquisition/road_attribute_evidence_audit.json)
includes every linear highway class, including paths and construction. Inclusion
is not permission to route a vehicle. Missing directions stay unresolved except
for the motorway and roundabout implication defined by
[OSM oneway semantics](https://wiki.openstreetmap.org/wiki/Key:oneway).

The resolver does not divide two-way lane totals equally. Explicit asymmetric
counts remain distinct, and conflicting or invalid counts cannot produce
resolved lane values. One-way totals supply their direction only where the
counts and lane/direction qualifiers permit that identity. The general and
directional speed tags retain their precedence and units; an invalid
directional value cannot fall back silently to a general value. Conditional
and vehicle-specific qualifiers remain visible and unapplied. Width is a road
quantity, not an inferred lane width. The
[lanes](https://wiki.openstreetmap.org/wiki/Key:lanes) and
[speed](https://wiki.openstreetmap.org/wiki/Key:maxspeed) definitions guide
these transformations; they do not establish the tags' accuracy in Mumbai.

This table is an input to further network assembly, not an operating network.
Class-based imputation, current official access/speed orders, road capacities,
signal effects and connections remain unresolved. In particular, OSM legal
speed limits cannot stand in for measured free-flow speeds. The framework's
older defaults measurement would halve two-way lane totals and truncate units;
it has not been run to select Mumbai parameters.

### Coastal Road peer-review traffic evidence, 2016

The acquired [BMC-hosted November 2016 peer review](https://portal.mcgm.gov.in/irj/go/km/docs/documents/Coastal%20road/Peer%20Review%20Reports%20by%20M_s%20Frischmann%20Prabhu/5.%20Report%204A_B_Rev1.pdf)
contains historical surveys separately from VISUM forecasts and proposed works.
PDF page 39 dates the classified counts to January 2016: seven full days at
17 sites, with a separate one-day, twelve-hour OD survey. These are selected
Coastal Road influence-area sites, not a representative whole-MMR sample.
The source states restrictions on reproduction; public hosting does not grant
an unrestricted licence.

The [travel-time extraction](../data/processed/observed/coastal_2016_travel_times.csv)
preserves Table 4-10's evening northbound and Table 4-11's morning southbound
observations on PDF page 59 (printed page 42). The two triangles remain separate.
Blank cells are absent; diagonal zeroes are labelled structural, not measured
zero-duration journeys. Exact clock windows, survey dates for these matrices,
vehicle classes and study-zone georeferencing remain unresolved. The times
include delay and cannot establish free-flow speeds or capacities. They are
historical evidence, not current calibration targets. The
[extraction audit](../data/processed/acquisition/coastal_2016_travel_time_audit.json)
records cell coverage and the visual check against the original table.

The same report's [daily traffic counts](../data/processed/observed/coastal_2016_daily_counts.csv)
retain both directions and the separately printed total. These overlapping rows
must not be summed. At Fountain Hotel, the two directions sum to 71,333
vehicles/day while the printed total is 70,904. The
[audit](../data/processed/acquisition/coastal_2016_traffic_count_audit.json)
retains this disagreement; it exceeds the possible rounding of three integer
means. The other sites reconcile. Daily traffic here is a seven-day mean,
not annual average daily traffic.

The [peak counts](../data/processed/observed/coastal_2016_peak_counts.csv)
retain each site's printed morning and evening hour. The separate
[vehicle shares](../data/processed/observed/coastal_2016_peak_vehicle_shares.csv)
have no morning/evening or directional split. No modal counts are manufactured
by multiplying these shares by either daily or period-specific totals.
Whole-percent zeroes do not prove absence; unlisted categories remain unlisted.
The source's Goods Temp and Goods Vehicles labels remain distinct. Neither
vehicle passages nor these shares measure passenger mode share, and the sites
cannot be summed into a unique regional vehicle count.

### Thane-Borivali tunnel report: survey counts versus forecasts

The [MMRDA-hosted tunnel DPR](https://mmrda.maharashtra.gov.in/sites/default/files/2024-10/1_tbtt_detailed_project_report.pdf)
has October 2022 footers, but PDF page 36 dates its seven-day traffic count to
2018. The [site counts](../data/processed/observed/tbtt_2018_site_counts.csv)
on page 48 cover five published groups at four sites. The
[reported aggregates](../data/processed/observed/tbtt_2018_reported_aggregates.csv)
are an equal mean across those sites, followed by an AADT calculation using
seasonality one. That assumption has not been adopted. The printed base-case
date is not proof of the survey's exact dates. The 2023 and 2029 figures on
page 56 are projections, not new observations.

The [audit](../data/processed/acquisition/tbtt_2018_count_audit.json)
checks the means and aggregate sum. Location 1 is listed as Magathane Midblock
(WEH), while page 44 places CVC1 on Dattapada Road; mainline assignment requires
map resolution. Trucks and Others/MAV become Truck 2 Axle and Multi Axle Truck
in the aggregate table, without an independently established class crosswalk.
Missing motorcycle and three-wheeler categories do not mean zero traffic.
Neither a four-site mean nor proposed tunnel geometry defines a current
operating network or citywide target.

The [moving-observer travel times](../data/processed/observed/tbtt_travel_times.csv)
from PDF pages 54-55 preserve six observations on two reverse circuits through
Ghodbunder Road and JVLR. The merged distance cell covers the complete circuit,
not a single leg between Magathane and Tikujiniwadi. Clock labels describe survey
windows. The speed-delay section does not independently establish the survey
date, test vehicle class or number of repetitions. The
[arithmetic audit](../data/processed/acquisition/tbtt_travel_time_audit.json)
checks journey and running speeds against distance, elapsed time and delay,
allowing only the rounding implied by printed precision. These intervals do
not quantify measurement uncertainty. Running speeds exclude stopping delay
but remain traffic-condition measurements, not free-flow speeds or capacities.
Exact route geometry and day type still need resolution before comparison.

### Signal reference locations and evidence of control operation

The [BMC 2021 tender](https://portal.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000008779_311221.pdf)
provides a [junction inventory](../data/processed/observed/bmc_2021_signal_junctions.csv)
on PDF pages 63-65. All 70 serials and coordinate pairs are retained, including
15 Ped entries and three combined arm/pedestrian entries. The
[audit](../data/processed/acquisition/bmc_2021_signal_inventory_audit.json)
keeps the original junction classes. Decimal conversion changes the notation
of the reference coordinates; the source does not establish datum or accuracy.
No points have been snapped to OSM or assigned to stop lines or controllers.
This selected upgrade list is not a citywide signal census or evidence that
the upgrades were completed. Pages 55 and 62 identify timing-plan design,
existing drawings and ITACA access as project work or available resources;
the inventory itself supplies no cycles, splits, offsets or conflict phases.

The [IBI report for Shakti](https://shaktifoundation.in/wp-content/uploads/2021/12/Best-Practices-for-Traffic-Signal-Operations-in-India.pdf)
is dated April 2016, despite its 2021 hosting path. PDF pages 74-75 describe
Mumbai's historical ITACA installation and report limited use of its adaptive
functions. Controller capability therefore does not establish the operating
mode at any junction or time. The report's simulation experiments and general
recommendations remain separate from measured Mumbai conditions. Current
controller logs, physical phases, detector coverage and field measurements
are still needed; Newcastle's SCATS rules cannot establish Mumbai's control.

### Suburban train formations, capacity and conditional operation

The [CR supplement markers](../data/processed/observed/cr_service_markers.csv)
join the visible train headers to 80 main-line AC, 28 Harbour AC and 54 main-line
15-car entries. Every header matches the previously extracted timetable cells
and their source hash. These are overlays, not additional departures. The
[audit](../data/processed/acquisition/cr_service_marker_audit.json) retains
page coverage and the unresolved calendar work. X/XX cancellations take
precedence over AC# substitutions. Harbour services that operate on Sundays
and nominated holidays use non-AC rakes under the printed footnote. An absent
cancellation marker establishes no complete operating calendar. The main-line
AC date comes from its download filename, not an independently printed date.
An AC marker does not establish coach count; 15C does not establish coach design.

Visual comparison also exposes cells that need service-specific interpretation.
On the Harbour DOWN base table's first page, train 99003 prints TNA in the
Mumbai CSMT row and 05:12 in the next row, labelled Masjid. That layout does
not establish a Masjid stop for a Thane-origin service. For train 98009, the
AC supplement prints R/O and another service reference above a 04:56 cell in
the Reay Road row, whereas the base table leaves that row blank and first
prints 05:06 at Vadala Road. The original cells remain evidence, with stopping
semantics unresolved in the raw extraction; a nearest-row match must not create
extra passenger stops. The assembly below resolves the evidenced reference
layouts while retaining those original cells.

The [Harbour service assembly](../data/processed/transit/cr_harbour_service_candidates.csv)
now produces one candidate per train across the Harbour and Trans-Harbour
tables, with [stop sequences and source references](../data/processed/transit/cr_harbour_stop_candidates.csv).
These remain dated evidence, with schedule export disabled until calendar,
physical station, vehicle and amendment reconciliation is complete. The
[layout annotations](../data/processed/observed/cr_harbour_layout_annotations.csv)
are read from individual glyphs. An independent grid reconstruction reproduces
all original Harbour time cells before interpreting any references.

Across 74 overlapping Harbour/Trans-Harbour services, all 555 shared time cells
agree. The [semantic resolution ledger](../data/processed/observed/cr_harbour_semantic_resolutions.csv)
reassigns 37 apparent Masjid-row times to their explicit TNA origin reference,
corroborated by the same train and clock in the Trans-Harbour table. Train 91491's
21:50 Tilaknagar-row time belongs to its explicit BVI destination reference;
the unprinted intervening Western Railway stops are not invented. Its external
branch remains incomplete, and later WR times need reconciliation.

Eighteen Panvel-Goregaon services are split at Vadala Road across the UP and
DOWN publications. Each pair has the same train number and PLGN/GNPL service
code, disjoint route portions and a shared endpoint. The assembly joins each
pair once and keeps the approach time as a derived arrival and the onward time
as a derived departure. Their published differences span 180-540 seconds,
retained individually. Train 98901, for example, reaches Vadala at 06:58 in the
UP table and continues at 07:02 in the DOWN table. No default reversal dwell
replaces these values; track movements and rake working still need evidence.

The AC supplement supplies 605 matching cells for 28 existing trains. Its three
extra Reay Road cells, accompanied by R/O and other service references, are
quarantined instead of added as passenger stops. The
[assembly audit](../data/processed/acquisition/cr_harbour_service_evidence_audit.json)
accounts for every input time cell exactly once in retained references or
quarantine. It records 876 service candidates and 14,731 stop candidates; neither
is a validated daily service count. Clock offsets are relative to the first
printed time, not an adopted service-day boundary. Agreement on the shared
portion of a 2024 table does not establish current validity of its other stops.

The [transport-area extraction](../data/processed/geospatial/osm_transport_areas.geojson)
adds the PBF's multipolygon layer to the existing point/line evidence. It retains
complete OSM way or relation identities, geometry and tags within the same
source-derived research envelope. The
[area audit](../data/processed/acquisition/osm_transport_areas_audit.json)
records 939 features, including 61 railway-station areas and 510 railway-platform
areas. Tag classes overlap; these are not counts of distinct operating stations.
They also include bus, ferry, taxi, bicycle and aviation facilities. No polygons
are clipped, repaired or replaced by invented boarding coordinates.

The [Harbour geometry candidates](../data/processed/transit/cr_harbour_geometry_candidates.csv)
use exact station-code matches, case/space/punctuation-equivalent names and the
explicitly scoped identity proposals described below.
A code-matched station can supply its own published OSM name to find associated
stop positions. Platform-number refs are not treated as station alpha codes.
The [coverage table](../data/processed/transit/cr_harbour_station_geometry_coverage.csv)
finds candidates for all 46 source station keys. Explicit metro and monorail
tags exclude 19 same-name matches. One retained candidate lacks mode evidence;
the others have source tags supporting a railway network. These labels describe
the map's evidence, not independently verified service status.

The [matching audit](../data/processed/acquisition/cr_harbour_station_geometry_audit.json)
has no unmatched source keys. It records that the source vocabularies
JNJ/Juinagar, VSH/Vashi and SNPD/Sanpada point to shared features. Node and area representations
must not become additional stations. Train stop positions without a `railway`
tag remain eligible when `public_transport=stop_position` and `train=yes` are
explicit; this preserves the source tags at Govandi and Panvel.

The [native transport relations](../data/processed/observed/osm_transport_relations.csv)
retain 1,811 relation records with ordered, typed members and roles, including
307 stop areas. Their source is the full native OSM build; the reduced road
network retained turn restrictions only. Related parent/child membership is
closed within the selected relation categories, without claiming complete
member geometry or current service operation.

The [Harbour track audit](../data/processed/acquisition/cr_harbour_track_evidence_audit.json)
uses 45 stop areas to add 15 boarding candidates to 168 directly matched nodes.
A Thane bus stop with relation role `stop` is explicitly excluded: the role
alone does not establish a railway boarding point.
All 183 candidates occur in the native network and belong to rail ways; the
[membership table](../data/processed/network/cr_harbour_track_memberships.csv)
preserves 222 parent-way positions, adjacent node IDs, gauge and direction tags.
It supplies boarding candidates for 46 source station keys. Stop-area groups
are not expanded across interchange modes, and blank member roles stay blank.
Long-distance and suburban platforms in one stop area still need allocation.

Of 90 ordered timetable station pairs, the
[topology check](../data/processed/network/cr_harbour_adjacent_station_topology.csv)
finds all 90 sharing an undirected rail component. Connectedness includes
sidings and does not establish a train path,
distance, direction, platform assignment, signal/block capacity or accessibility.
Those validations remain required before any service can enter the simulator.

The [continuous path audit](../data/processed/acquisition/cr_harbour_path_audit.json)
groups the 876 service candidates into 31 ordered stopping patterns. A portable
router chooses boarding nodes jointly across a whole pattern: each intermediate
arrival and departure uses the same native node. It cannot stitch independently
chosen platforms together without a connecting train path. The
[pattern table](../data/processed/transit/cr_harbour_path_patterns.csv) finds
continuous geometry for all 31 patterns covering 876 services, using the scoped
SNPD identity proposal below for 120 services.

Two diagnostic variants retain complete
[segment sequences](../data/processed/network/cr_harbour_path_segments.csv).
The geometry-only variant ignores direction; 26 of its retained patterns cross
explicit one-way tags backwards. Screening static, unqualified one-way tags
removes those traversals while retaining continuous candidates for the same
services. Every retained pattern still includes unresolved direction evidence.
Seven screened patterns travel against a mapped preferred direction somewhere.
[Preferred direction](https://wiki.openstreetmap.org/wiki/Key:railway:preferred_direction)
describes usual operation and is not treated as an absolute prohibition;
conditional and qualified direction tags require separate interpretation.

The [time diagnostics](../data/processed/transit/cr_harbour_path_time_diagnostics.csv)
pair candidate leg lengths with printed intervals, subtracting only explicitly
resolved origin dwell. All intervals are positive, but minute precision and
arrival/departure roles prevent treating distance/time ratios as observed
speeds. Shortest geometry can use crossovers or sidings and does not validate
switch movements, reversal feasibility, gauge, block occupation or operating
platforms. Both variants remain ineligible for timetable export. Different
source vintages and incomplete external branches retain their existing status.

The [mapped-route audit](../data/processed/acquisition/cr_harbour_mapped_routes_audit.json)
compares these patterns with native PTv2 passenger routes. It retains 24 train
relations with at least two identified boarding stops, including other suburban
and intercity routes that share stations. Of these, 22 have complete, uniquely
oriented native way chains; two intercity relations extend beyond the available
rail geometry. Twenty have every listed stop on their chain in the listed order.
The [route inventory](../data/processed/transit/cr_harbour_mapped_routes.csv),
[stop positions](../data/processed/transit/cr_harbour_mapped_route_stops.csv) and
[segment traces](../data/processed/network/cr_harbour_mapped_route_segments.csv)
preserve member order, repeated ways, original tags and exact native node IDs.
The portable checker does not snap, reorder, substitute or join disconnected
members. Its interpretation follows the [OSM PTv2 member convention](https://wiki.openstreetmap.org/wiki/Public_transport#Service_routes).

The CSMT-to-Panvel relation lists Chembur before Tilak Nagar, whereas its track
chain and the timetable put Tilak Nagar first. Tilak Nagar is present on the
chain; this is a stop-order discrepancy, not a missing track connection.
The broader inventory also finds an out-of-order stop on the Kasara-to-CSMT
fast relation. Both source relations remain intact for review.

The [pattern comparison](../data/processed/transit/cr_harbour_pattern_route_evidence.csv)
finds 20 coherent contiguous route windows covering 19 patterns and 613 services.
One pattern has two mapped alternatives, which remain separate. Six additional
comparisons expose the CSMT-to-Panvel station-order conflict. Other patterns need
skipped-stop, composite, reversal or external-branch evidence; absence of a
contiguous match does not mean that the service cannot operate. Mapped windows
often choose different boarding nodes from the shortest-geometry candidates.
They strengthen route/platform evidence without establishing train-specific
assignments, current operating permissions, switch or signal capacity, calendars
or fleet compatibility. Every row remains ineligible for schedule export.

The [fixed-chain assignment audit](../data/processed/acquisition/cr_harbour_constrained_paths_audit.json)
then uses timetable stop order to locate identified boarding nodes on each
unchanged mapped track chain. The portable matcher counts every complete
strictly ordered assignment and prunes positions that cannot fit the whole
trip. It exports positions only when the assignment within that chain is unique.
[Coverage](../data/processed/transit/cr_harbour_chain_coverage.csv) retains all
682 pattern/chain checks, including missing nodes, order conflicts and ambiguity.
There are [28 path candidates](../data/processed/transit/cr_harbour_constrained_path_candidates.csv)
for 27 patterns and [820 services](../data/processed/transit/cr_harbour_constrained_service_candidates.csv).
One pattern retains two route alternatives. All boarding nodes are listed in
their source route relations, and no candidate runs against explicit static
one-way tags. Seven candidates retain mapped stop-order disagreements; one
contains a mapped stop without a timetable candidate. That omission does not
establish a non-stop service: quarantined source cells remain unresolved.

The [9,380 segment traversals](../data/processed/network/cr_harbour_constrained_path_segments.csv)
retain native identities, source way tags and one arrival/departure node at each
intermediate stop. These are mapped track candidates, not operational paths.
At this single-chain stage, 56 services lack candidates: 18 through services via Vadala, 37 Thane-to-
Panvel services and one incomplete Borivali branch. The mapped Thane-to-Panvel
chain ends before any resolved Panvel boarding node. At Vadala, the mapped
branch routes use different platform nodes, so joining their stop lists would
not prove a physically continuous reversal. Current permissions, signalling,
reversal movements, calendars and fleet assignments still require validation.

The [composite-path audit](../data/processed/acquisition/cr_harbour_composite_paths_audit.json)
tests the unresolved patterns using two original mapped chains joined at an
identical native boarding node. Both halves must satisfy timetable stop order;
nearby platforms and matching station names cannot substitute for node identity.
Five [shared-stop joins](../data/processed/transit/cr_harbour_composite_join_candidates.csv)
between the Thane-to-Panvel and CSMT-to-Panvel mapped chains yield the same
[physical path candidate](../data/processed/transit/cr_harbour_composite_path_candidates.csv).
The equivalent join points are Seawood Darave, Belapur, Kharghar, Mansarovar and
Khandeshwar, using the source station-code keys. They are alternative provenance
cuts, not five routes or five extra services. The
[388 segment traversals](../data/processed/network/cr_harbour_composite_path_segments.csv)
retain every contributing route/member reference, with no platform jump,
immediate reversal at the join or traversal against a static explicit one-way tag.

The [combined service evidence](../data/processed/transit/cr_harbour_composite_service_candidates.csv)
now has fixed-chain or composite track candidates for 857 of 876 services.
Composite paths are derived evidence, not observed route relations or current
operating assignments. The 18 Vadala through services and one incomplete Borivali
branch still lack this level of route evidence. Their existing shortest-geometry
candidates remain separate. The [path audit](../data/processed/acquisition/cr_harbour_path_audit.json)
records immediate reversals at the two through-pattern candidates' selected
Vadala nodes and links them to the 18 trains' source arrival/departure clocks.
Neither this geometry nor the printed dwell establishes platform permissions,
turnout movements, signal routes or train-length clearance.
All calendar, source-cell and fleet gaps remain, and no service is exported.

The [identity proposals](../data/processed/transit/cr_harbour_identity_proposals.csv)
preserve four source keys while linking them to published station-code or
mapped corridor evidence.
The [WR code reference](../data/processed/observed/wr_station_code_reference.csv)
extracts five name/code rows from the 2025 zonal reference, without telephone
numbers. The acquired [Mumbai division reference](https://wr.indianrailways.gov.in/cris/uploads/files/1739174922855-Disaster%20Management%20%20Plan%202025%20Part-I%20BCT%20Division.pdf)
supplies [three glossary entries](../data/processed/observed/wr_station_abbreviations.csv),
including `Jn.` = `Junction`, `MM` = Mahim Station and `JOS` = Jogeshwari Station.
Its identical glossary on PDF pages 15 and 158 is one source, not corroboration.

Jogeshwari maps to JOS, but the reference also uses JOS for Jogeshwari AT; that
code alone cannot choose Harbour or Western platforms. Mahim Jn has a scoped
crosswalk to MM using the published junction abbreviation. The Harbour source
actually prints Ramnagar: 112 service triplets place it between Jogeshwari and
Goregaon, while 56 WR timetable grids place Ram Mandir there. The RMAR link is
an inferred label-correction proposal. Repeated grids are not independent
sources, source labels stay intact, and no times or calendars cross vintages.

All 120 timetable occurrences of SNPD lie between TUH and VSH. Two native OSM
passenger-route relations identify Sanpada in that position, in opposite
directions; their stop-area memberships link both boarding nodes to the station
area tagged SNCR. This supports a scoped SNPD-to-SNCR passenger-station proposal.
The original timetable key remains intact, and no global car-shed alias is
created. Both mapped directions share one OSM source; they do not independently
verify current operation. The [archived named Trans-Harbour timetable](https://cr.indianrailways.gov.in/cris/uploads/files/1640069704271-5.%20Trans-Harbour.pdf)
is still catalogued but unobtained after both verified download transports and
a public browser fetch failed.

The acquired [WR 2025 disaster-management reference](https://wr.indianrailways.gov.in/cris/uploads/files/1747654690625-ZDMP_Part-II%202025.pdf)
contains station names/codes in PDF pages 39-40, including two Jogeshwari entries
with code JOS and Ram Mandir with RMAR. It helps distinguish source identities;
the telephone table is not a service or capacity inventory. The older CR system
map remains unobtained after two transport failures. The discovered Railway
Board [IRCA alpha-code directory](https://indianrailways.gov.in/railwayboard/uploads/directorate/IRCA/PDF/ALPHA%20CODES%20AS%20ON%2010-3-2023%20FINAL.pdf)
also remains unacquired. A combined source-list,
allowlist and acquisition command was rejected by automatic approval review as
blocked by policy; subsequent acquisitions used existing allowed domains.

The [Railways' December 2017 announcement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1514002&lang=2&reg=48)
supplies [capacities](../data/processed/observed/suburban_first_ac_capacity_2017.csv)
for the first BHEL 12-car AC rake: 1,028 seats and 4,936 standing places. The
three coach types and the complete rake have separate units. Component sums
reconcile, but the standing-density basis is unstated. These design capacities
cannot be assigned to later fleets without evidence of the same configuration.
Reserved seats and ladies' compartments require eligibility and crowding rules
beyond a train's aggregate capacity. The original weekday-only operation is
historical and does not define current service calendars.

The [April 2026 Railways statement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2248576&lang=1&reg=3)
reports [service counts](../data/processed/observed/suburban_service_counts_202604.csv):
WR 1,414 including 133 AC, and CR 1,820 including 94 AC. The combined 3,234
and AC subset 227 reconcile, but no individual reference operating day is
specified. The [stock claims](../data/processed/observed/suburban_stock_claims_202604.csv)
separate FY2025-26 receipts from sanctioned procurement. Two received AC rakes
for each railway and one received non-AC 15-car WR rake do not establish the
total active fleet. The 238 sanctioned rakes are not operating vehicles. The
[audit](../data/processed/acquisition/suburban_fleet_claims_audit.json) adopts
none of these quantities as model parameters or trip-specific assignments.

The acquired [25 March 2026 Railways statement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2245194&lang=2&reg=48)
adds [12 terminal-work rows](../data/processed/observed/rail_terminal_project_status_20260325.csv),
[13 corridor-project rows](../data/processed/observed/rail_corridor_project_status_20260325.csv)
and [six aggregate claims](../data/processed/observed/rail_capacity_claims_20260325.csv).
The terminal heading mixes completed, taken-up and planned work; row-specific
status is left unresolved unless explicitly stated. The sanctioned Goregaon-to-
Borivali Harbour extension does not prove commissioning or resolve the single
Borivali timetable candidate. Approximate March service totals are kept distinct
from the later April operator counts. Platform works and sanctioned rakes do
not enter current supply. The [project audit](../data/processed/acquisition/rail_project_status_audit.json)
also excludes the separate Pune tables and the page's duplicated article copy.

The acquired [MRVC/TISS report](https://mrvc.indianrailways.gov.in/works/uploads/File/Gender%20Study%20Report%20by%20TISS%281%29.pdf)
is dated 2016. Its [sample-strata extraction](../data/processed/observed/tiss_rail_survey_strata_2016.csv)
retains the 1,000 women rail-user sample across railway lines and travel classes.
The study's peak/off-peak strata also distinguish weekends and flow direction;
they cannot become clock-hour departure shares. The
[station-access table](../data/processed/observed/tiss_rail_access_modes_2016.csv)
contains 994 numeric respondent records: walking 494, auto/shared auto 365,
bus 75, taxi 33, own/private vehicle 26 and metro one. The printed train `N/A`
remains not applicable, not zero. The six-person difference from the full sample
is unexplained in these extracted sections and is not imputed as nonresponse.

PDF pages 19 and 27 were checked visually. The
[audit](../data/processed/acquisition/tiss_rail_access_audit.json) preserves one
printed percentage discrepancy in the sample-strata table; access percentages
agree with rounding against the derived 994-person denominator. These are
historical responses from women rail users, not citywide or current mode shares.
The grouped auto and private-vehicle categories remain grouped. Survey weights,
full fieldwork dates and comparability with current demand still need study.
The separate MRVC mid-section trespassing summary remains unobtained after both
verified download transports failed; it supplies no model observations yet.

The RDSO MRVC-III 2017 and EMU/MEMU 2022 specifications remain unobtained after
both verified Windows TLS and ordinary HTTPS acquisition attempts failed.
Search-index text is not a substitute for their immutable source documents.

### Festival dates and railway operating exceptions

The [December 2025 state notification](https://maharashtra.gov.in/site/Upload/pdf/Public-Holiday-2026.pdf)
provides [26 holiday rows](../data/processed/observed/maha_holidays_2026.csv):
24 public-holiday names on 22 dates, one bank-only closure and one addition for
specified state and local government bodies. The English tables on PDF pages
5, 6 and 12 were checked visually; all Gregorian dates match their printed
weekdays. Saka dates retain the English transcription without claiming agreement
with the Marathi table. Holidays with a shared date are separate names, not
two closed days. None establishes universal business or school closure.

The [CR date-evidence join](../data/processed/observed/cr_holiday_date_evidence_2026.csv)
matches twelve explicitly named rules in its undated Sunday-schedule sheet to
state publication dates. The remaining Diwali rule is unresolved: the state
lists Laxmi Pujan on 8 November and Bali Pratipada on 10 November, while CR says
first and second day without defining them. Neither consecutive-day arithmetic
nor all state holidays can fill that gap. The
[audit](../data/processed/acquisition/holiday_evidence_audit.json) retains the
need for dated operating notices and festival amendments before expanding a
train calendar. The acquisition identifier's year is not evidence that the
undated CR rule applies unchanged throughout that year.

The acquired [CR 2026 wall calendar hosted by CAG](https://saiindia.gov.in/uploads/media/CR-Wall-Calendar-2026-1-0699ee2aca61af2-81437787.pdf)
is an image-only poster. Its visually reviewed legend distinguishes General
and Restricted Holidays, with Diwali entries in the latter. It gives Bakri Id
as 27 May, while the state notification gives 28 May. This is a retained source
disagreement, not grounds for moving a train cancellation. The poster supplies
no suburban timetable exception rules and cannot replace the operating sheet.


### Railway control evidence and acquisition limits

The [MRVC control claims](../data/processed/observed/mrvc_rail_control_claims_2023_24.csv)
extract eight historical statements from the acquired annual report for 2023-24,
PDF page 134 (printed page 10), checked against the rendered page. The report
lists CBTC project extents of 130 route-km / 370 track-km for CR and
74 route-km / 268 track-km for WR. Its 2.5-minute headway is a project target;
the following paragraph describes indigenous development and further action
pending Railway Board directives. These are not commissioned control systems
or an operating headway. The [audit](../data/processed/acquisition/rail_control_evidence_audit.json)
retains the unit conversion to 150 seconds as a derived project quantity only.

The same page reports two existing Kalyan-Badlapur lines carrying mixed
Mail/Express, goods and suburban traffic, with about 136 trains against a
stated capacity of 120. The period, directional basis and capacity method are
not stated there. The extraction preserves that omission; it does not convert
these counts into daily demand, hourly link capacity or current track counts.

The acquired CR signalling-assets HTML was last reviewed on 14 May 2026,
but its asset table is an external image. The
[page dependency audit](../data/processed/acquisition/cr_signalling_page_dependencies.json)
records the exact image URL and zero extracted asset values. Page review date
is not an asset observation date. Both verified download transports failed for
the image, the Harbour EMU draft specification, the CSMT-Panvel fast-corridor
DPR, and carshed/suburban-operation pages. Line-capacity and Mumbai S&T pages
also refused their initial downloads. The targeted CBTC-reference retry after
the successful MRVC TISS acquisition failed again. These sources remain
catalogued and obtainable in principle; failed requests do not supply data.

Current block lengths, aspect logic, braking curves, interlocking conflicts,
platform occupation, reversal permissions and train-specific fleet assignments
still need evidence. None of these historical claims changes operating supply
or makes a Harbour path candidate eligible for schedule export.


### Road access by vehicle class

The [road access audit](../data/processed/acquisition/road_access_evidence_audit.json)
now joins all 232,856 linear highway records to 249 distinct explicit
[access profiles](../data/processed/network/osm_access_profiles.json).
The [way/profile table](../data/processed/network/osm_way_access_profiles.csv)
retains native way IDs. The
[class evidence](../data/processed/network/osm_access_class_evidence.csv)
contains 2,988 profile/class rows for foot, bicycle, motorcar, motorcycle,
moped, auto-rickshaw, bus, taxi, minibus, shared taxi, goods and HGV categories.
These are OSM tag categories, not automatic mappings to local legal classes or
the simulator's mode inventory. The downloaded OSM tag-documentation pages have
independent hashes and CC-BY-SA 2.0 notices; native map data remains ODbL 1.0.

The resolver retains broad-to-specific inheritance and each contributing tag.
A bus or pedestrian exception can override a general restriction without
opening the way to cars or motorcycles. Unknown child values do not fall back
to a permissive parent. Private, destination, customer and permit restrictions
remain dependent on the traveller and journey. Conditional, directional,
lane and nonstandard qualifiers are visible and unevaluated. Motorcar tags
have a documented scope ambiguity for other double-tracked vehicle classes;
those class interpretations are flagged rather than silently propagated.

There are 172,644 ways without an explicit access-family tag. That absence is
neither a grant nor a ban. The audit counts tagged prohibitions after inheritance
and before direction/physical checks: 1,392 for motorcars, 1,302 for motorcycles,
1,309 for bicycles, 842 for pedestrians and 859 for buses. Scope-review cases
are separate. These are way counts, not lengths, trips or model link counts.

Every original way has one profile; the source-tag joins and all class totals
were independently checked. Four derived outputs were byte-identical on
repeat. Unit checks exercise modal exceptions, malformed specific tags,
restricted purposes and qualifier preservation. The profiles do not establish
operating permissions or write a MATSim network. Class defaults, one-way
exceptions, physical barriers and suitability, legal notices and traveller
entitlements remain part of network construction.


### Complete native road/path geometry

The [native road geometry audit](../data/processed/network/road_geometry/audit.json)
covers 232,958 source ways, 2,043,886 referenced nodes and 2,139,676 adjacent-node
segments. It retains whole native way sequences without snapping, clipping,
simplification or a minimum segment length. Geographic coordinates, projected
EPSG:32643 metre coordinates, projected and WGS84 geodesic lengths, complete tags
and source hashes remain available in the geometry tables. Lengths are
horizontal; no unobserved vertical profile is supplied.

All 232,856 linear highway attribute and access-profile records match their
geometry and tags exactly. The other 102 geometry ways comprise 61 area
boundaries and 41 ways carrying only a lifecycle-prefixed highway tag. They are
not silently promoted to operating links. The
[join audit](../data/processed/acquisition/road_geometry_join_audit.json)
checks every segment against its parent way's adjacent nodes, count and length
totals, and verifies all referenced road nodes exist.

The road node tags include 34,422 barriers, 2,469 traffic-signal nodes and
897 railway level-crossing tags. These are mapped features in the research
envelope, not operating junction counts or verified control installations.
The [road/rail shared-node table](../data/processed/network/road_rail_shared_nodes.csv)
retains 1,512 common native node identities with exactly equal coordinates,
tags and provenance in both layers. Parent-way lists distinguish source
feature classes and area boundaries. Shared geometry creates neither a
passenger transfer nor permission to enter a track. Geometric intersections
without a common native node are not connected.

The portable geometry reader now serves roads and rail. Existing Mumbai rail
outputs remained byte-identical after the refactor. The full road build also
produced four byte-identical files on repeat. Tests cover coincident but
separate nodes, shared junctions, rail/road coordinate agreement, barriers,
areas, lifecycle features and reference failures. Large geometry CSVs and the
bulk road attribute/profile tables are gitignored; their scripts and manifest
remain the reproducibility record. This is native geometry evidence, not a
MATSim network or a simulation. Direction-specific permissions, local access
rules, signals, speeds, capacities and crossing operations remain to be built.


The join audit also retains railway-tagged road nodes without a matching rail
geometry node. Level-crossing node `6698536234` lies outside the source-derived
research envelope on a retained whole road way; that is overcoverage, not a
reason to snap an artificial railway connection. Switch-tagged node
`10927965890` lies inside the envelope on private service ways `856312672` and
`936736937`, without membership in the extracted rail geometry. Its tag and
parents remain available for investigation. The 27 unshared subway-entrance
nodes are retained as entrances rather than forced onto track. The envelope is
a research extent, not a confirmed legal simulation boundary. These checks
create no operating links or transfer permissions.


### Protected geometry chains and converter control loss

A native probe of pinned pt2matsim 26.6
(`tests/check_osm_control_nodes.py`, jar hash recorded by the probe) shows that
`keepPaths=false` removes intermediate gate, traffic-signal and level-crossing
nodes from a synthetic road. With `keepPaths=true`, their coordinates remain,
but node tags are absent from the converted network in both cases. Equal total
link length does not establish control preservation. No Mumbai network was
converted by this probe, and its passing assertions do not certify suitability.

The [protected-chain audit](../data/processed/network/road_chains/audit.json)
now partitions the native road geometry into 512,916 chains with 417,126 retained
nodes. All 49,677 tagged source nodes survive, along with way endpoints, native
shared/repeated identities, 1,512 road/rail shared nodes and the available
members of 333 turn-restriction relations. There are 1,626,760 internal shape
nodes, whose coordinates and order remain in the original node table and each
chain's ordered geometry. Every one of the 2,139,676 native adjacent segments
occurs exactly once in its parent way's chain sequence. No area or lifecycle
feature becomes operational through this partition.

The chain lengths are exact sums of the input segment table's decimal
representations, checked with inexact arithmetic trapped. This is an arithmetic
identity, not a claim of survey precision. Source-coordinate hashes, node tags,
parent way IDs, source segment intervals and access-profile references remain
available. Closed chains retain an existing interior anchor; the generated
package contains no self-loop or zero-length chains. The retained node and
chain CSVs are bulk, gitignored data with committed producers and manifest rows.

The source includes an incomplete restriction relation `16357332`, tagged
`no_right_turn` but containing only via node `10281845108`, without from/to way
members. That node is not in the road geometry. The audit retains the exact
member list; no turn prohibition can be derived from it yet. Other road
restriction member ways were found and their nodes retained. No missing turn
endpoint was guessed or manufactured.

This is a candidate geometry reduction, not an adopted MATSim network.
Control behaviour, direction and purpose-dependent access are still required.
Later stop/activity mapping can introduce additional anchors. Queue storage,
flow, discrete time steps and junction interactions need paired simulation
checks before this reduction can support an accuracy claim. Unit checks cover
control retention, repeated visits, closed geometry, native edge conservation
and input-order independence.


## Native turn restrictions and source-history defects

`extract/build_turn_restriction_evidence.py` retains all 333 selected native
restriction relations, their tags, member order and input hashes in
`data/processed/network/osm_turn_restrictions.json`. Of these, 140 have a
single junction node shared by the from/to road endpoints; 180 have a unique
ordered full-way chain through their via ways. Geometry checks do not establish
vehicle direction, legal scope or simulation enforcement. No model turns are
exported. The source values comprise 181 no-right-turn, 139 no-U-turn, eight
no-left-turn and five no-straight-on records within the research extraction.

Thirteen relations lack both from/to roads. Public OSM API histories were
acquired for all thirteen, and each latest member/tag set matches the native
snapshot. Eleven histories show later removal of both road members; two were
incomplete at creation. One also has an empty member role. The audit retains
all versions, timestamps and source hashes. Historical roads are not restored
as current rules. Relation 16357332, whose node also lies outside the road
geometry, lost both road members on 19 August 2024; it is one of these thirteen.

The reproducible audit is
`data/processed/acquisition/turn_restriction_audit.json`. The associated
`osm_relation_*_history_20260919` acquisitions are ODbL evidence; the acquired
`osm_wiki_restriction_20260919` documents tag semantics under CC-BY-SA 2.0.
Neither is an official current traffic-order inventory. These defects still
need reconciliation with dated traffic orders and current junction layouts.


## Broad baseline supply build after the priority change

The user prioritised a running behavioural baseline on 19 September 2026
(decision 9.187). `registry/A_baseline_supply.json` now declares the provisional
supply and mapper settings, and `docs/reference/CONFIG_REFERENCE.md` renders
them. They are not calibrated observations. The shared MATSim builder completed
the base network and mapped the acquired community bus feed. The build report
is `networks/matsim/_matsim_build_report.json`; raw geometry is retained.

`build/build_baseline_bus_feed.py` stages the unchanged source zip. It covers
BEST, KDMT, TMT and VVMT, with operational accuracy unverified. It is one input
to broad coverage, not the complete bus supply. Mapping may introduce artificial
links, and repeated equal stop departure times are a source/converter warning.
Neither a successfully mapped schedule nor a network build is a simulation.
`build/build_baseline_transit_feed.py` adds OSM-derived suburban rail, metro
and ferry services with explicit provisional frequencies. The representative
population builder draws historical census age, sex, worker and vehicle-access
marginals; incomes and destinations remain provisional, with no household
coupling or citywide expansion. The bounded `run.py --baseline-smoke` case has
completed its declared three iterations (0 to 2).

The runtime preparation preserves the mapped build, repairs a reversed stop
ordering with a connected detour, and derives feasible stop offsets from
mapped distance, speed and dwell. Mode-specific access retains endpoint stubs
where the walk network cannot reach a boarding link. Dedicated transit flow
is expressed in PCU/hour from vehicle PCU and a declared service headway;
it must not be confused with trains/hour. All corrections have per-run audits.

The baseline enables income-sensitive money scoring, travel and activity time,
waiting, transfers, crowding, frequency and measured prior-iteration reliability.
There are no ridership quotas. Fleet defaults, provisional truck/freight inputs,
incomplete operator coverage, passenger-driver coupling and finite hire fleets
remain material gaps. Precise corridor audits are deferred unless a defect
prevents execution or defeats the broad choice mechanism.


## Provisional background freight

`build/build_baseline_freight.py` adds fixed-mode goods movements to the small
resident case. The unambiguous LCV and Trucks groups in the acquired 2018 road
survey determine a historical goods/car ratio. A declared smoke intensity
converts that ratio to a background cohort; it is not a current regional count.
The two acquired JNPA handled-day rake reports supply the rail activity scale.
A declared stationary-operation multiplier represents inbound and outbound
movements; handled-day counts are not relabelled as observed train movements.

The acquired OSM port locality anchors access. Each mode uses mutually
reachable links and research-network extremities for provisional external
origins/destinations. These are not observed cargo destinations or legal port
gates. All freight is kept out of resident mode innovation and income scoring;
it still occupies shared road or rail links at its declared vehicle dimensions,
speed and PCU. Current OD, road time bans, empty return movements, depot
circulation, formation mix and regional intensity still require refinement.
The audit is `data/processed/acquisition/baseline_freight.json`.


## Regional buses in the broad baseline

`build/build_regional_bus_feed.py` extends the existing multimodal feed with
NMMT and MBMT. NMMT departure clocks come from the acquired passenger API.
Ordered operator route-stop snapshots define the sequence. Published trip
sequences sometimes insert foreign stops; matching route endpoints and the
operator sequence resolve these conflicts. Unmatched departures are retained
as explicit quarantines in the audit, not silently forced into the model.

Segment running times use median usable adjacent-stop clock differences with
a geographic feasibility floor. Extreme timing ratios, negative clock changes
and absent matching segments fall back to declared geographic derivation.
These are provisional pattern timetables, not observed operation. Every
replacement is counted. Acquired raw observations remain unchanged.

MBMT directed route stops supply geometry. The sum of published weekday route
bus allocations supplies a pooled fleet proxy; the printed subtotal disagrees
and is not substituted. Equal pattern frequency is derived from total one-way
cycle time and terminal allowances divided by that pool. Its envelope applies
to approximate input times, not mapped runtime or verified vehicle circulation.
Current route assignments, service calendars and actual operating fleet remain
unverified. Ridership is never used to choose departures or seed mode quotas.


## Boarding fares in the broad baseline

`build/build_baseline_fares.py` reads the acquired BEST fare transcription and
community route identifiers. Published distance bands supply the tariff amounts.
A declared route-label rule assigns provisional AC/non-AC profiles; it is not
proof of a departure's vehicle class. All travellers use the adult column until
concession eligibility and pass ownership are integrated. Both class choices
have explicit uncertainty alternatives in the registry.

The native boarding-fare handler charges actual modelled network distance at
alighting and sends a money event into income-sensitive scoring. The previous
PT monetary distance rate is zero to prevent double charging. For distances
beyond the published table, the last marginal rate is extrapolated and counted
separately. Other operators and suburban rail, metro and ferry retain the prior
provisional linear price. None of these proxies are labelled observed tariffs.

The analyser preserves per-iteration charged money, currency, completed rides,
unfinished rides and out-of-table extensions. The fare-routing gate applies the
same declared tariff and person-specific money utility before transit paths are
pruned. This closes the scoring-only mechanism gap for these boarding rules;
it does not validate provisional operator prices or ticket eligibility.
The tariff's publication date does not establish current validity or actual
fare-stage distances. See `data/processed/acquisition/baseline_fares.json`.

## Daily activities and mapped destinations

`build/build_baseline_activities.py` reads the existing demographic cohort and
adds purpose-specific locations and discretionary tours. Person identities,
ages, incomes, licences and available modes remain unchanged. Work and education
keep their primary roles; a declared mixture relocates them to acquired OSM
points and area representative points. Remaining primary locations retain the
historical zone proxy. Each mapped location is an equal opportunity proxy,
not an observed job, capacity or verified entrance.

Shopping, social and leisure tours use the acquired state time-use activity
participation and per-participant minutes, by sex and rural/urban residence.
These are broad activities for people aged six and above, including activity
at home. They are **not** observed adult trip rates. Explicit provisional
out-of-home fractions and time allocations translate these benchmarks into
adult outings. The cap on discretionary tours is also assumed. No trip survey
or observed diary is claimed, and no ridership share controls the draws.

Each tour returns home. The first departure has a declared time window; later
departures follow actual return travel and a home interval. Activity durations
are preserved after arrival instead of scheduling overlapping fixed end times.
The analyser reports trips by destination activity and departures after 24:00;
long travel can push a synthetic day past midnight and needs further validation.

The point and area inventories retain source IDs and coordinates.
`extract/extract_activity_areas.py` reads mapped activity areas from the acquired
OSM PBF. Invalid geometry is counted and excluded. Exact nonempty named nodes
inside same-purpose areas lose only duplicate purposes; other duplicates may
remain. Destinations within the
research envelope but outside the available census polygons stay available,
without an invented zone ID. Overlapping polygon matches choose the first
geography ID in stable sorted order and are counted. Uneven mapping,
age-specific school eligibility, attraction capacity, opening hours, household escorts, visitor
demand and observed daily attendance remain gaps. The new plans feed the
existing freight builder; the transport network and timetables are reused.

The reproducible audit is `data/processed/acquisition/baseline_activities.json`;
individual synthetic tours are in `demand/baseline/activities.csv`.

## Controlled road-capacity sensitivity

The bounded launcher applies the declared `RUN.smoke.road_capacity_factors`
to class-tagged links on the existing mapped network. The base is identity.
The `smoke_low_capacity_double` overlay tests a higher prior for the low-capacity
road classes without changing demand, geometry, lane counts, free speed or
timetables. Reverse active-mode links inherit their forward road capacity.
This is a test of model sensitivity, not measured capacity or sampling.

`src/analyse/compare_capacity_inputs.py` verifies the source hashes, resolved
configuration, prepared timetable and vehicle bytes, network metadata and
every node/link attribute. Only the declared capacities may differ.
`src/analyse/transit_supply_capacity.py` measures the flow-budget implications
of the schedule; it does not infer current road capacity from bus frequency.

## Initial mode-choice coverage

`build/build_baseline_choices.py` adds eligible, unscored whole-day mode
alternatives to each mobile resident's original plan. The original selection,
activities, timings, attributes and fixed freight movements are preserved;
before/after selected-demand hashes must match. No mode share sets these
alternatives. Existing subtour innovation can create further mixed-mode plans.

The `smoke_mode_coverage` overlay uses the separate plans and sufficient memory
to retain them. The launcher refuses a memory limit below the supplied maximum.
The analyser measures distinct first-trip modes actually recorded across the
completed iterations. That count excludes people without a recorded first trip,
including stay-home residents; it is not a convergence or calibration test.

The same report reads final native retained plans and counts missing or
non-finite scores, including selected plans without a finite score. Stored
scores can come from different iterations and describe evaluations under those
conditions. Their distribution is not a welfare or convergence comparison.
The reader rejects inconsistent person inventories and ambiguous selections.

## Hired-vehicle availability

`build/build_hired_fleet.py` derives a provisional supply pool from regional
registration stock and the explicit cohort size. The active fraction is assumed.
The source years and geographical coverage differ. The output records these
limitations, source hashes and integer-rounding errors. It is not observed
operating supply or a validated scaling rule.

The optional `smoke_hired_fleet` case queues requests during the simulation.
A unit remains occupied until actual arrival and a declared turnaround interval.
Waiting delays the journey and enters its experienced travel time. Taxi and
auto pools are separate. A timeout aborts the day through native stuck handling.
The behavioural report preserves each iteration's queue and waiting totals.

This pool has no spatial dispatch, vehicle shifts or empty road movements.
Per-person vehicle proxies carry served trips on the network. Pickup geography,
operator availability and a fallback after refusal remain implementation gaps.
The native probe is `python tests/check_hired_fleet.py`. It uses synthetic roads
and travellers, not Mumbai observations. See decision 9.199 for the first city
experiment and its provisional coefficients.
The [portable pool contract](../../../docs/hired_fleet.md) defines the mechanism
and its configuration independently of the Mumbai inputs.
