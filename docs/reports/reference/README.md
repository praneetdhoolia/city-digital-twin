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

Last pass **7 September 2026**, at `af7d718`, lodged as
[`20260907T173435_project_report.html`](../20260907T173435_project_report.html)
(the third pass of the day; the 13:02 pass at `419b0da` is the one before it).
Seeded 7 September 2026 from the `report-data` block of
`20260907T013735_project_report.html`, read at `9cd8b4f` before that report was
deleted in `03b5220`.

### `field-survey.json` — 40 of 40 searches spent, 4 rounds (7 September 2026, third pass, at `af7d718`)

| | count | this pass |
|---|---:|---|
| projects surveyed | **44** | **40 reused unchanged, 0 re-searched, 1 updated from a closed gap** (Dhaka, its paywalled fit read from the author's thesis), **3 added** (MWCOG Gen3 ActivitySim with the whole ladder and its acceptance standards; the UCLA Deep Activity Model; the Brussels cellphone-matrix MATSim) |
| platforms surveyed | 12 | 6 reused unchanged; **9 of 12 `unknown` cells filled** (SUMO 1.27.1 / EPL-2.0, BEAM GPL v3 / v1.0.0 2022, SimMobility no releases, mobiTopp 0.3.1, OpenPaths 2025 Update 1); MATSim's licence still `unknown` after four failed fetches |
| candidates excluded | 46 | 5 added (the NSW Spatial Digital Twin — visualisation and an AI predictor, no ABM — and four LLM-lane papers); the ETH Singapore entry re-written from the paper itself, which says its validation was planned, not done |
| rows not re-verified | 34 | 3 resolved into rows or read (MWCOG, Brussels, Dhaka full text), 3 added (Virtual Singapore 404, a Springer DC open-data study, arXiv 2501.10221), 4 notes updated |
| open gaps | 4 | 3 inherited and **narrowed**, 1 **closed** (the LLM lane's stopping rule — two further rounds added nothing), 1 added (the MUM 2026 programme, 28 September) |

Every stored row was inside both horizons, so the budget went to the gaps in
order and to one never-seen candidate; three PDFs the fetches left on disk
(MWCOG, the Dhaka thesis, ETH Singapore 2012) were read without spending a
call. The validation ladder now stands at 7 / 9 / 22 / 6 / 0 (none / survey
shares / road link counts / transit ridership / per-mode every mode); no
project publishes the top rung.

### `factors.json` — 34 of 40 searches spent, 6 rounds (7 September 2026, second pass, at `af7d718`)

| | count | this pass |
|---|---:|---|
| factors listed | 72 | unchanged |
| literature half filled | **72** | **11 added** (the rows the first pass never reached) and **14 completed** with a magnitude where the literature holds one; 47 reused unchanged |
| still `needs_research` | **5** | workplace location, ride pairing / matching, age and sex, route choice, external and through traffic — each wants a coefficient or a share the literature does not state, and each keeps the query that would close it |
| statuses stored | **0** | by design — every status is re-read at `HEAD` each pass |

**Where the next pass's budget goes.** The two dead lanes of the 7 September
pass are closed. What is left:

1. **5 factor rows still needing research**, two of them `high` relevance —
   workplace location (a transferable tolerance for own-LGA commute share) and
   ride pairing / matching (a household, not a platform, detour and wait
   tolerance). Each keeps the query that would close it. Two sources this
   pass were reachable only at abstract level (the Transport Reviews e-bike
   meta-analysis, the Melbourne bicycle-ownership study); their figures are
   labelled as such in the row.
2. **MATSim's own licence** (four fetch routes failed) and three lesser
   platform cells — each gap carries the exact URL to try next; do not retry
   the ones that returned 404.
3. **The agency programmes not reached** — Monty (New Zealand: one page empty,
   one 403), Virtual Singapore (both official pages 404), and any MTC / ARC /
   SEMCOG ActivitySim validation report. MWCOG is done and TfNSW resolved to a
   visualisation platform.
4. **Unreached fits** — Brussels (open access, yet the publisher blocks; a
   ResearchGate copy would close it), the MDPI on-demand study, the Springer
   Washington DC study — and, after **28 September 2026**, the **MUM 2026
   programme**, where a new calibrated city scenario or a Wellington
   validation would surface first. The LLM lane's stopping rule is met; do not
   spend budget there without a new lead.
