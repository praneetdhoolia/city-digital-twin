# The reference library

**What has already been researched, so that no later pass researches it again.**

The dated reports in the parent directory are prunable files — a reader may
delete one, and two were deleted on 7 September 2026. This directory is the
durable half. `/project-report`'s two research phases
([`.claude/skills/project-report/SKILL.md`](../../../.claude/skills/project-report/SKILL.md),
Phases 6 and 7) **read these files before running a single search** and spend
their budget only on what the files do not already answer.

It holds the **external** half of the research — what the world outside this
repository is and what the literature says. It deliberately holds **no fact
about this model**: a comparable project's engine does not change week to week,
but this model's coverage of a factor does, so every status is re-read at `HEAD`
on every pass.

| File | Holds | Freshness horizon |
|---|---|---|
| [`field-survey.json`](field-survey.json) | One row per comparable city twin and per platform: engine, city, sample fraction, modes, validation rung, best published fit, what it does best, source URLs. Plus `excluded` (candidates checked and rejected, with the reason), `not_reverified` and `gaps`. | **180 days** for facts (engine, city, modes, rung, fit) · **90 days** for liveness (active / dormant, last release) |
| [`factors.json`](factors.json) | One row per factor a real-world decision simulator must contain: what the research says, its magnitude, its source, how the leading simulators implement it. **No status column** — see below. | **365 days** — a meta-analysis says the same thing this week as last |

## The rules the library runs on

1. **A stored row inside its horizon is reused, not re-searched.** It is
   rendered in the report marked `reused` with its `last_verified` date, so a
   reader can see what was checked this pass and what was inherited. Reuse is
   not a shortcut to apologise for; it is the point.
2. **Search is spent on gaps.** In order: the `gaps` array, then candidates with
   no row, then cells recorded `unknown` or empty, then rows past their horizon.
   Each research phase gets **at most 40 searches or fetches**.
3. **What the budget does not reach becomes a named gap**, carrying the query
   that would close it — never another round of searches nobody reads.
4. **An excluded candidate stays excluded.** The `excluded` list exists so that
   no later pass pays again to rule out the same non-qualifying project.
5. **A row that cannot be re-found is not deleted.** It keeps its stored
   attributes and gains `not_reverified_on`.
6. **No status in this model is ever stored here.** A factor's IN / PARTIAL /
   INERT / ASC / OUT is re-read at `HEAD` every pass by `grep` of the registry
   and the Java. The model moves weekly and a status carried forward is a status
   that is wrong.
7. **A research phase writes its file before it returns**, so an interrupted
   pass still leaves the library better than it found it.

## State

Last pass **16 September 2026**, at `d6f9cdf` (the fifty-third session: the
routers pair closed out and read as the third result, the handoff's by-hand
steps made tools) — the **twelfth** pass of the library, two days after the
tenth (which ran at `b8f89ff` and is lodged as
[`20260914T152907_project_report.html`](../20260914T152907_project_report.html)).
Field lane 37 of 40 calls over 12 rounds, stopped by the two-barren-rounds rule;
every stored row was inside its horizon and none was re-searched. Nothing new
qualified: five candidate sweeps produced six exclusions and no row.

| | rows | this pass |
|---|---:|---|
| `field-survey.json` projects | **55** | 51 carried unchanged, **1 updated with verified material** (BEAM — two PDFs saved and read in full: 7.75 M residents, a 30 % validated baseline and a 10 % calibration sample, the validation data named verbatim (Google Maps speeds, HPMS VMT, MTC agency boardings), route-level ridership CHANGES as the only published fit, ~12 h on 50 cores / 512 GB, and the field's only sample-size sweep for an on-demand mode — ride-hail dynamics converge at 40 %), 3 narrowed without a cell change (SimMobility's calibration method behind a third dead DSpace path; MWCOG's status from the November 2025 subcommittee highlights; Kelheim's heap by elimination), **0 added** |
| `field-survey.json` platforms | 12 | 12 reused unchanged |
| excluded · not re-verified · gaps | 76 · 42 · **26 (11 open)** | **3 gaps closed by elimination** (the Brussels and DC fits — every route dead, `unknown (paywalled)` is permanent; the Seoul fit — no open copy exists; the Kelheim heap — the 1 % log exceeds 10 MB, so no MATSim log is readable from here), 8 narrowed (ARC's 2015 report also over 10 MB; the MUM 2026 page live but without a programme 12 days out; gap 9's literature side exhausted), **2 opened** (the BEAM CORE calibration and validation report, Spurlock et al. 2024 — the one document that would give BEAM a level fit; Greater Jakarta 2026 — a 10 % MATSim scenario with a motorcycle mode, unreadable on three hosts); **6 excluded** (Ústí nad Labem eqasim, no validation claim; COMPASS, an LLM guidance method; a SUMO motorway EV twin; a Sensors 2026 signal-control demo; the two BEAM application papers, written into the BEAM row); 3 unpriced candidates narrowed (Okanagan, Jakarta, the Berlin→SUMO hybrid) |
| `calibration_methods` | **20** | 20 reused, 0 added |
| `factors.json` rows | **101** | **96 reused unchanged, 0 re-searched** (all inside the 365-day horizon, `needs_research` 0), **5 added**, each from a source read this pass (B7 immobility — the 8-12 % one-day diary benchmark, Madre, Axhausen & Brög; E27 heavy-rail station access mode — Meng, Taylor & Scrafton ATRF 2017 read in full: walk 37-43 %, park-and-ride 11-36 %, kiss-and-ride 7-17 % at outer stations, Sydney walk access ~50 %; E28 walk-access distance to public transport — Daniels & Mulley JTLU 2013 read in full: Sydney HTS mean 573 m, train 805 m, bus 461 m, upper quartile 1,018 m; I16 travel-time and speed validation — the FHWA Toolbox III / Wisconsin table: times within 15 % in > 85 % of cases, GEH < 5; J8 mobile-phone records as a demand observation — Nommon, Bassolas 2019, Matet et al. 2024), 7 dated addenda; gaps: F6's indifference band closed (Zhu & Levinson 2015 read in full: 34 % on the shortest-time path, half within 30 s, 90 % within 5 min), A2 and H12 narrowed, three new residuals named; factor lane **20 of 40** calls over 6 rounds, two PDFs read locally at no cost. Every status re-read at `d6f9cdf`: IN 47 / PARTIAL 39 / INERT 3 / ASC 1 / OUT 11 over 101 — **no class changed on the 96 carried rows** (46 / 36 / 3 / 1 / 10); the routers pair moved router-scorer consistency (F5) and the router-expressed rail bonus (E25) from the top of the would-move ranking to measured-and-negative, and ride's choice-set ceiling (H10), walk's placement (E15) and the scoring pair (H9) now lead |
| `needs_research` | **0** | unchanged |

Budgets: field lane **37 of 40** calls over 12 rounds (the 16 September 2026
pass at `d6f9cdf`); factor lane **20 of 40** calls over 6 rounds (the same pass,
the same `HEAD`). The validation ladder over 55 rows is **7 / 12 / 26 / 10 / 0** (none
/ survey shares / road link counts / transit ridership / per-mode every mode);
no carried row moved rung, the top rung is still empty across every agent-based
project, and this repository is still the only attempt — in calibration, **2 of
12 modes inside 10 %** at the newest result (the routers pair,
`20260915T000704_250it_25pct`, 250 of 250: car +9.0 %, motorbike −5.5 %; six past
the 20 % bar; nothing moved against arm 0 outside one build's noise). Three
findings this pass bear on this project directly: BEAM calibrates at 10 %,
validates at 30 % and states that an on-demand mode's dynamics settle only at a
40 % sample — this project's taxi and ride are read at 25 %, on the steep part
of that curve; BEAM CORE's 7.75 M-resident weekday takes ~12 h on 50 cores and
512 GB against this project's 27.39 h for 250 iterations of 622,318 residents on
16 threads, and neither the field nor this pass could read a MATSim heap at any
scale; and MWCOG's own record has its ABM and its four-step model agreeing
"except for transit ridership and VHD", the family this project's six STOP
modes belong to. Five dead routes were added to the ledger (climr.ok.ubc.ca,
cris.unibo.it, its-archive.mit.edu, a third DSpace path, the ScienceDirect
`/org/` mirror); two live ones (eta-publications.lbl.gov and escholarship.org
serve PDFs that read locally at no budget cost).

### The previous pass (11 September 2026, at `20ae4e9`)

Lodged as
[`20260911T210144_project_report.html`](../20260911T210144_project_report.html)
— the eighth pass: field 50 of 50 rows reused, 6 updated (MATSim-NYC, AToM,
POLARIS, Munich, SoundCast, Lausitz), 0 added, every row given
`data_acquired_per_mode` and `physical_fidelity` cells; factors 90 reused,
3 added (E25, J6, J7), a `per_mode_data` block; field lane 40 of 40 calls,
factor lane 37 of 40; statuses IN 44 · PARTIAL 34 · INERT 2 · ASC 1 · OUT 9
over the carried rows.

### The pass before (10 September 2026, at `4d1d1bc`)

Lodged as
`20260910T134723_project_report.html` (pruned; git history)
— the seventh pass: field 49 of 50 rows reused, 1 added (Tallinn/SimMobility),
6 calibration methods added; factors 83 reused, 7 added; field lane 38 of 40
calls, factor lane 18 of 40; statuses IN 46 · PARTIAL 32 · INERT 2 · ASC 1 · OUT 9.


Lodged as
`20260909T003402_project_report.html` (pruned; git history)
— the sixth pass of the library. The previous refresh of both lanes was the pass
at `6cf0ffd`, lodged as
`20260908T192638_project_report.html` (pruned; git history),
about five hours earlier.

Two passes a day apart is the second demonstration of what the library is for,
and a sharper one than the first. Every stored row was **one day old and inside
its horizon**, so across both lanes **not one stored fact was re-searched**: 48
of 49 project rows, all 12 platform rows, all 10 stored `calibration_methods`
and all 79 factor literature halves were carried in as they stand. The field
lane spent 39 calls and the factor lane 13 — **52 calls, every one of them on a
gap or on this pass's new question**, which was: *what architectures exist for
reaching equilibrium across many simultaneously-targeted variables?* A pass that
had to re-establish the field from scratch could not have asked it.

### `field-survey.json` — 39 of 40 searches spent, 8 rounds (9 September 2026, at `781cf41`)

| | count | this pass |
|---|---:|---|
| projects surveyed | **49** | **48 reused unchanged, 0 re-searched**, **1 added** — Munich (PNAS Nexus 3(11) pgae489): MATSim + MITO against a multicommodity-network-flow model and an inertial-random-walk model, on one network and one observed dataset (MVV stop-level boardings, 7 Oct – 20 Dec 2019), at **25 % and 5 %** — the two fractions this project sweeps between |
| platforms surveyed | 12 | all 12 reused unchanged |
| candidates excluded | **59** | 3 added — GATSim (a stylised Nguyen–Dupuis network with 70 GPT-4o agents and no empirical validation); **WFTDM** (four-step, not agent-based, but recorded in full for its per-mode table); the SPSA/PSO/ADAM destination-choice study (small synthetic network) |
| rows not re-verified | 37 | unchanged; no row was searched for and lost |
| open gaps | **8** | two closed by elimination (the Springer and Bentley routes are confirmed dead); two added — whether a four-step model's per-mode validation counts as the same rung, and an unsourced "myopic heuristics" claim about coupled choice-model calibration, **the single highest-value item for the next pass** |
| `calibration_methods` | **14** | **4 added** — the staged agency protocol; history matching / NROY; multi-objective formulations; and the Calibration Illusion counter-finding |

The validation ladder over 49 rows is **7 / 9 / 25 / 8 / 0** (none / survey
shares / road link counts / transit ridership / per-mode every mode). **The top
rung is still empty across every agent-based project**, and ours remains the
only attempt at it.

**This pass qualified that claim for the first time, and the qualification is
honest rather than flattering.** A trip-based **four-step** model — WFTDM,
Wasatch Front — *does* report the top rung: six transit modes separately, all
inside 10 %, most inside 5 %, verbatim *"All mode shares were calibrated to
within 5% of observed data"*. It is excluded for having no agents, which is
correct, but it means the empty rung is **partly a reporting convention among
agent-based models** rather than purely a difficulty. Written back as a gap.

**The most reusable thing this pass produced is the answer to its own question,
and it is a negative one.** Across 49 projects the mechanisms actually in use
are (a) a weighted sum of normalised deviations, (b) a log-ratio constant update
applied mode by mode, and (c) a human deciding when to stop. **There is no
published architecture in transport that treats "all N targets inside their
bands" as the object being solved.** Two architectures exist for it elsewhere
and neither is used here: **history matching**, whose implausibility statistic
is computed per output with model discrepancy as an explicit term and whose
empty NROY region is a formal verdict that a deficit is structural; and
**epsilon-constraint** multi-objective formulations, the textbook way to express
a feasibility goal as constraints rather than as a sum. NSGA-II has been coupled
to MATSim — for *network design*, not calibration.

Three further findings worth carrying: the profession publishes this project's
own §8.5 rule verbatim (*mode-constant adjustment "should be considered 'a last
resort'"*); **there is no published acceptance bar for mode choice at all**
(*"There are no applicable criteria guidelines for checks of mode choice"*), so
the 10 % band is self-imposed; and *The Calibration Illusion in Traffic
Microsimulation* (Hickert et al., 2026) explains why no one publishes an
evaluation count — automatic calibration hides *"a significant and unquantified
amount of bespoke manual work"*.

### `factors.json` — 13 of 40 searches spent, 3 rounds (9 September 2026, at `781cf41`)

| | count | this pass |
|---|---:|---|
| factors listed | **83** | **4 added**, all in Layer I, all on this pass's question: sequential versus simultaneous calibration; the damping and step-size *schedule*; diagnosing a residual as constant versus mechanism; multi-objective aggregation across many targets |
| literature half filled | **83** | **79 reused unchanged, 0 re-searched**; 4 written for the new rows |
| still `needs_research` | **0** | unchanged |
| statuses stored | **0** | by design. All 83 re-read at `781cf41` by grep of the registry, `src/`, the city build layer and both Java trees. This pass: **IN 45 · PARTIAL 27 · INERT 2 · ASC 1 · OUT 8** (previous pass: 39 / 29 / 2 / 1 / 8) |

**Five carried factors changed class — the first movement the library has ever
recorded.** The previous pass reported that not one did. Every one of the five
traces to a named commit in `6cf0ffd..781cf41`: crowding (E11) and boarding /
denied boarding (F3) went PARTIAL → IN when `PtCrowdingScoring.java` was bound
end to end; the ASC calibration method (I6) and aggregate-only estimation (I10)
went PARTIAL → IN when `asc_fixed_point.py` landed; and access/egress/wait/
transfer weights (E2) went **IN → PARTIAL**, a regression on evidence that did
not exist a day earlier — `RUN.transit_router.access_egress_basis` ships at
`beeline`, so the raptor draws those legs as straight lines.

The top mover is now **E12, reliability and headway, and it is INERT**:
`C.time_weights.beta_headway` = 0.5 and `beta_reliability` = 1.3 are declared
with literature sweeps and written into `params/C1_parameters.json`, and neither
carries a `matsim_param` or a consumer. Bus at +54.6 % against light rail at
−47.2 % is a service-quality inversion, and the two parameters that would price
service quality reach a JSON file and stop there.

## Where the next pass's budget goes

1. **The "myopic heuristics" claim** about coupled choice-model calibration —
   unsourced, and the highest-value single item in the gap list.
2. **Whether a four-step model's per-mode validation is the same rung.** It
   decides whether the top rung is empty because the problem is hard or because
   agent-based projects do not report that way, and the two have different
   consequences for this project's claim.
3. **After 28 September 2026, the MUM 2026 programme**, where a new calibrated
   city scenario or a Wellington validation would surface first. Nothing was
   spent on it this pass or the last because the date is still in the future.
4. **Unreached fits** — Brussels (five failed routes) and the MDPI on-demand
   study. The Washington DC study's full text is gold open access under CC BY
   and Springer still 303s to its identity provider.

**Routes that work, and should be reused.** `tfresource.org/topics/<Page>.html`
was the single best source of this pass. Also live:
`api.semanticscholar.org/graph/v1/paper/DOI:<doi>` (three successes),
`arxiv.org/html/<id>v<n>` where the abs page carries nothing,
`www.mdpi.com/<j>/<v>/<i>/<n>/pdf?version=...` even though MDPI article HTML
403s, and open-access articles on `academic.oup.com`. A PDF that `WebFetch`
returns as binary can be **saved locally and read with page ranges at no
search-budget cost**.

**Dead routes, recorded so no later pass pays for them again:**
`link.springer.com` (both `/content/pdf/` and `/article/` 303 to
`idp.springer.com` — never retry) · `www.tandfonline.com` (403) ·
`blog.bentley.com` → `www.bentley.com/blog/` (301, then a sign-in interstitial) ·
`pubmed.ncbi.nlm.nih.gov` (cookie-consent page only) ·
`api.semanticscholar.org/graph/v1/paper/search` (429 on both attempts) ·
`arxiv.org/pdf/2112.12071` (over the 10 MB fetch limit) · `web.archive.org`
(blocked by this repository's own network sandbox, so it can never work from
here) · ScienceDirect and ResearchGate (403) · CMAP's PDF (an image-only scan).
