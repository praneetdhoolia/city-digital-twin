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

Last pass **7 September 2026**, at `419b0da`, lodged as
[`20260907T130247_project_report.html`](../20260907T130247_project_report.html).
Seeded 7 September 2026 from the `report-data` block of
`20260907T013735_project_report.html`, read at `9cd8b4f` before that report was
deleted in `03b5220`.

### `field-survey.json` — 39 of 40 searches spent, 7 rounds

| | count | this pass |
|---|---:|---|
| projects surveyed | 41 | **40 reused unchanged, 0 re-searched, 1 added** (Dhaka BRT MATSim) |
| platforms surveyed | **12** | **12 added** — the lane that had never delivered a row |
| candidates excluded | 41 | 4 added, each with the reason it failed to qualify |
| rows not re-verified | 34 | 7 added; every one keeps its stored attributes |
| open gaps | 4 | 1 inherited and still open, 3 added |

The whole budget went to the two inherited gaps, because all 40 stored project
rows were inside both horizons. That is the library working as designed: reuse
paid for the platform table.

### `factors.json` — 38 of 40 searches spent, 9 rounds

| | count | this pass |
|---|---:|---|
| factors listed | 72 | unchanged |
| literature half filled | **58** | **58 added** — the previous pass filled none |
| still `needs_research` | 25 | 14 filled but without a transferable magnitude, 11 never reached |
| statuses stored | **0** | by design — every status is re-read at `HEAD` each pass |

**Where the next pass's budget goes.** The two dead lanes of the 7 September
pass are closed. What is left:

1. **25 factor rows still needing research**, eight of them `high` relevance —
   led by bicycle ownership, ride pairing/lifts/detour, and workplace location.
   Each keeps the query that would close it.
2. **Platform licence and release dates** — six cells the sources did not state
   (MATSim's own licence among them) are recorded `unknown`, not guessed.
3. **Agency programmes as programmes** — TfNSW, Virtual Singapore and the US
   MPO validation reports are still unsurveyed.
4. **Paywalled fits**, and **lane 3's stopping rule**, which has still not been
   met: only one round of no new qualifying entry, where two are required.
