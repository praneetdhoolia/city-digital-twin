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

Seeded 7 September 2026 from the `report-data` block of
`20260907T013735_project_report.html`, read at `9cd8b4f` before that report was
deleted in `03b5220`.

| | count | note |
|---|---:|---|
| projects surveyed | 40 | each with source URLs, verified 7 Sep 2026 |
| platforms surveyed | 0 | **open gap** — the lane never delivered |
| candidates excluded | 37 | with the reason each failed to qualify |
| rows not re-verified | 27 | source unreachable on the 7 Sep pass |
| factors listed | 72 | across layers A–K |
| factors with their literature half filled | **0** | **open gap** — see below |
| open gaps | 2 | platforms and agency programmes; lane 3's unmet stopping rule |

**Where the next pass's budget goes.** The 7 September pass ran three field
lanes and three factor lanes in parallel, exhausted its web-search budget, and
delivered no platform table and not one literature cell across its 72 factor
rows — every one reads *"not researched this pass (search budget exhausted
before the factor lanes wrote)"*. That is the duplicated-search problem this
library and the one-agent-per-phase rule exist to end. The 40 project rows it
did produce are now reusable rather than lost, and the next pass should spend
Phase 6 on the platform gap and Phase 7 on the 72 `needs_research` rows,
highest `relevance` first, instead of re-surveying what is already here.
