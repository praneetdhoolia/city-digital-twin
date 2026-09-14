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

Last pass **14 September 2026**, at `b8f89ff` (the forty-seventh session: the
documents moved to `docs/`, the run viewer rebuilt, arm 0 of F35 landed as the
second result) — the **tenth** pass of the library, the same day as the ninth
(which ran at `780c4c2` and is lodged as
[`20260914T014107_project_report.html`](../20260914T014107_project_report.html))
and the first after a reading rule fired: arm 0 of F35 is a result with 2 of 12
modes inside 10 %. Field lane 40 of 40 calls over 12 rounds; every stored row was
inside its horizon and none was re-searched.

| | rows | this pass |
|---|---:|---|
| `field-survey.json` projects | **55** | 47 carried unchanged, **6 updated with verified material** (Lausitz from Meinhardt, Lu & Nagel 2026 — its calibration method, 10 % scale and teleported walk, in print for the first time; Kelheim from its published v3.0 25 % stopwatch — 388 iterations in ~15.5 h; Berlin from its own `calibrate.py`; Seoul's citation; MWCOG's memo still unlocated and the subcommittee dates; Brussels from the VUB portal), **2 added** (Rotterdam–The Hague, the ActivitySim + MATSim co-simulation read from TU Delft's copy; Barcelona-MATSim from mobile phone records, Bassolas et al. 2019, a holdout count validation with its misses named) |
| `field-survey.json` platforms | 12 | 10 reused unchanged, **2 updated** (OpenPaths' automated-calibration cell filled from the Utah MUG page after three passes; MATSim's `calibration_tooling` from Rakow & Nagel 2024 read in full — the three-page CC BY note behind the ASC fixed point, formula and damping advice verbatim) |
| excluded · not re-verified · gaps | 70 · 42 · **24 (12 open)** | **5 gaps closed** (the four VSP 2026 working papers titled — none is the downsampling study; the TNO candidate — now a row; joint trip-length calibration — the ecosystem hand-sets a marginal utility of travelling per mode and states no tolerance; the wall-time half of run cost — Kelheim's stopwatch; the OpenPaths cell), 8 narrowed, **3 opened** (Okanagan ASIM + MATSim, unpriced behind SSRN's 403; the Kelheim heap; the Berlin MATSim→SUMO hybrid behind MDPI); 2 excluded (Meinhardt et al. 2026 as a DRT application on Lausitz; Rakow & Nagel 2024 as a method note); 2 recorded unpriced |
| `calibration_methods` | **20** | 20 reused, 0 added, 1 dated addendum (the fixed-point family's source note read in full; two applications name it — Lausitz and Rotterdam) |
| `factors.json` rows | **96** | **94 reused unchanged, 0 re-searched** (all inside the 365-day horizon, `needs_research` 0), **2 added** (H12 habit, inertia and satisficing - three meta-analyses via Javaid et al. 2020, habit-mode r 0.42-0.50; F6 route-choice reliability and the indifference band - Carrion & Levinson), 11 dated addenda; gaps: I7 closed (the Berlin v6.3 EWGT paper read in full: undamped log-ratio ASC update, MAE < 0.5 pp), H6, I8, G5, A2 narrowed, BO4Mob ruled out; factor lane 35 of 40 calls over 9 rounds. Every status re-read at `b8f89ff`: IN 46 / PARTIAL 36 / INERT 3 / ASC 1 / OUT 10 over 96 (no class changed on the 94 carried rows) |
| `needs_research` | **0** | unchanged |

Budgets: field lane **40 of 40** calls over 12 rounds (the 14 September 2026
pass at `b8f89ff`); the factor lane's budget for this pass is written back by
that lane. The validation ladder over 55 rows is **7 / 12 / 26 / 10 / 0** (none
/ survey shares / road link counts / transit ridership / per-mode every mode);
no carried row moved rung, the top rung is still empty across every agent-based
project, and this repository is still the only attempt — in calibration, **2 of
12 modes inside 10 %** at the newest result (arm 0 of F35,
`20260912T202242_300it_25pct`: car +9.6 %, motorbike −5.6 %; six past the 20 %
bar). Three findings this pass bear on this project directly: Kelheim v3.0 at
25 % publishes ~139 s a recurring iteration and ~15.5 h for 388 iterations
against this project's 346 s and 30.35 h for 300 (five times the population);
the Rakow & Nagel note's "adjust the update step by a fraction" is the value
`CAL.asc.damping` declares and the ecosystem's only stated damping rule; and
Barcelona-MATSim attributes its two count misses by link to the port freight and
through traffic a resident model excludes — the first published bearing with
numbers on why a mode-share-calibrated model under-counts specific links.

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
[`20260910T134723_project_report.html`](../20260910T134723_project_report.html)
— the seventh pass: field 49 of 50 rows reused, 1 added (Tallinn/SimMobility),
6 calibration methods added; factors 83 reused, 7 added; field lane 38 of 40
calls, factor lane 18 of 40; statuses IN 46 · PARTIAL 32 · INERT 2 · ASC 1 · OUT 9.


Lodged as
[`20260909T003402_project_report.html`](../20260909T003402_project_report.html)
— the sixth pass of the library. The previous refresh of both lanes was the pass
at `6cf0ffd`, lodged as
[`20260908T192638_project_report.html`](../20260908T192638_project_report.html),
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
