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

Last pass **7 September 2026**, at `f40d332`, lodged as
[`20260907T231739_project_report.html`](../20260907T231739_project_report.html)
— the fourth pass of that day, and the one that refreshed **both** lanes (the
previous refresh of each was the pass at `af7d718`, lodged as
[`20260907T173435_project_report.html`](../20260907T173435_project_report.html)).
Seeded 7 September 2026 from the `report-data` block of
`20260907T013735_project_report.html`, read at `9cd8b4f` before that report was
deleted in `03b5220`.

### `field-survey.json` — 35 of 40 searches spent, 5 rounds (7 September 2026, fourth pass, at `f40d332`)

| | count | this pass |
|---|---:|---|
| projects surveyed | **46** | **43 reused unchanged, 0 re-searched, 1 updated** (POLARIS Chicago, its rung now carried by a verbatim 2026 validation sentence), **2 added** (the SEMCOG ActivitySim model for Detroit; the Washington DC open-data MATSim COVID study) |
| platforms surveyed | 12 | 7 reused unchanged; **5 more `unknown` cells filled — the licence gap is CLOSED**: MATSim is the GNU GPL per the `<licenses>` block of `matsim/pom.xml` (GitHub's licence API 404s because there is no SPDX-detectable `LICENSE` at the root, which is why four earlier routes found nothing); mobiTopp 0.3.1 = 16 May 2024; eqasim v2.2.0 = 3 June 2026; OpenPaths 2025 Update 1 = 4 December 2025; SimMobility city-agnostic by design |
| candidates excluded | 53 | 7 added — Virtual Singapore (a 3D visualisation and experimentation platform, no ABM of its own), arXiv 2501.10221 (no city), the Takamatsu MATSim study (no validation claim), and four 2026 "digital twin" papers that are not city travel models |
| rows not re-verified | 37 | 3 added (ARC, the Brussels fit as its own entry, an eqasim French-cities 2026 lead), 2 notes updated (Monty's third and fourth failed routes; MTC/ARC/PSRC/SEMCOG split apart) |
| open gaps | 4 | 2 inherited and **narrowed**, 1 **closed** (the platform-licence gap), 1 carried unchanged (MUM 2026, 28 September — in the future, no budget spent), 1 added (the residue of the closed platform gap) |

Not one stored row was re-searched: all 44 project rows and 12 platform rows
carried `last_verified` 2026-09-07 from the same day's earlier pass, inside both
horizons. The budget went to the library's gaps in order, then to never-seen
candidates, then to `unknown` cells, and **the pass stopped on the stopping
rule, not the budget** — rounds 4 and 5 were two successive rounds of
differently phrased sweeps (agency ActivitySim programmes, Australian and
Victorian ABMs, Japanese/Korean/Chinese MATSim scenarios, African and South
American models, eqasim 2026, generic 2026 "digital twin validated per mode")
and neither added a qualifying entry. Five searches were left unspent and the
work they would have done is written back as gaps. The validation ladder now
stands at 7 / 9 / 24 / 6 / 0 (none / survey shares / road link counts / transit
ridership / per-mode every mode) over 46 rows; **no project publishes the top
rung**, and our own row moved the other way — from one mode of twelve inside
10 % to none.

### `factors.json` — 21 of 40 searches spent, 6 rounds (7 September 2026, fourth pass, at `f40d332`)

| | count | this pass |
|---|---:|---|
| factors listed | 72 | unchanged; none added, none retired |
| literature half filled | **72** | **69 reused unchanged** (all inside the 365-day horizon) and **3 completed** — route choice, ride pairing / matching, age and sex |
| still `needs_research` | **2** | workplace location and external and through traffic. Two rounds of differently phrased searches added nothing to either, so the stopping rule was applied rather than a further round; each keeps a **narrowed** query naming the exact route to try next |
| statuses stored | **0** | by design — every status was re-read at `f40d332` for all 72 rows by `grep` of `cities/newcastle/registry/`, `src/`, `cities/newcastle/build/`, `src/java/` and `src/java_signals/`, plus a read-only `check_hardcoding.py`. This pass: **IN 37 · PARTIAL 27 · INERT 2 · ASC 1 · OUT 5** (previous pass at `af7d718`: 35 / 28 / 1 / 2 / 6) |

**Where the next pass's budget goes.** The two dead lanes of the 7 September
pass are closed. What is left:

1. **2 factor rows still needing research**, one of them `high` relevance —
   **workplace location** (no published Australian journey-to-work flow
   tolerance; the FHWA validation manual chapter 3 was fetched this pass and
   states there are no criteria guidelines for trip-distribution checks, so try
   the AToM full text on ResearchGate `357268039` or the `matsim-melbourne`
   validation notebooks) and **external and through traffic** (the quantity is
   cordon-specific by construction; try the TfNSW Lower Hunter Freight Corridor
   and M1 Raymond Terrace EIS traffic chapters directly — a general search
   returns only the ~15 % heavy-vehicle share on the New England Highway, which
   is a vehicle-class share, not a through share). Dead fetches this pass, **do
   not retry**: the AToM arXiv PDF (over the 10 MB limit), the Taylor & Francis
   AToM full text (403), Springer `10.1007/s11116-021-10259-4` (auth redirect —
   the PMC copy `PMC7614415` works), `PMC9987251` (captcha), the alogit Sydney
   model PDF (unreadable). Two sources from the second pass remain
   abstract-level (the Transport Reviews e-bike meta-analysis, the Melbourne
   bicycle-ownership study) and stay labelled as such in their rows.
2. **The agency programmes still not reached** — Monty (four routes have now
   failed: both `transport.govt.nz` pages return blank bodies, Arup 403s, the
   MATSim showcase carries no validation claim), ARC's ABM calibration report
   (its PDF exceeds the 10 MB fetch limit; try the smaller specification
   report), and MTC's Travel Model Two (TM2.3, still in development, no report
   published). SEMCOG is now a row; Virtual Singapore and TfNSW are excluded.
3. **Unreached fits** — Brussels (four routes failed, including ResearchGate,
   which is now confirmed to 403 the agent) and the MDPI on-demand study; plus
   the Washington DC study's **full text**, which is gold open access under
   CC BY yet Springer 303s to its identity provider, so its SafeGraph
   R² = 0.99 is still only a search-index snippet. The DC abstract was
   recovered through the Semantic Scholar graph API — a route worth reusing.
4. **The residue of the closed platform gap** — the base OpenPaths 2025
   (v25.00.00) announcement date, the TRANSIMS 7.5 release date, and a named
   agency or city running on SUMO.
5. After **28 September 2026**, the **MUM 2026 programme**, where a new
   calibrated city scenario or a Wellington validation would surface first.
   The LLM lane's stopping rule has now been met three passes running; do not
   spend budget there without a new lead.
