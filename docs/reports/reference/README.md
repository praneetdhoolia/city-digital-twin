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

Last pass **8 September 2026**, at `6cf0ffd` (the PR #161 merge), lodged as
[`20260908T192638_project_report.html`](../20260908T192638_project_report.html)
— the fifth pass of the library and the first at this commit. The previous
refresh of both lanes was the pass at `f40d332`, lodged as
[`20260907T231739_project_report.html`](../20260907T231739_project_report.html),
six hours earlier.

That six-hour gap is the clearest demonstration yet of what the library is for.
Every stored row was **one day old and inside its horizon**, so across both lanes
**not one stored fact was re-searched**: 58 field rows and 67 factor literature
halves were carried in as they stand, and all 71 calls the two lanes spent went
to gaps and to this session's new question. A pass that had to re-establish the
field from scratch could not have afforded the calibration research at all.

### `field-survey.json` — 38 of 40 searches spent, 7 rounds (8 September 2026, at `6cf0ffd`)

| | count | this pass |
|---|---:|---|
| projects surveyed | **48** | **46 reused unchanged, 0 re-searched**, **2 added** — the ARC ABM (Atlanta CT-RAMP), promoted out of `not_reverified` because the *specification* report was the smaller route the last pass named and it worked; and Barcelona's SUMO traffic twin |
| platforms surveyed | 12 | all 12 reused; 5 gained a new cell |
| candidates excluded | **56** | 3 added — the Bloomington GP-emulator paper, the Las Palmas smart-cities architecture, the Rzeszów roundabout study |
| rows not re-verified | 37 | unchanged in count; ARC's note rewritten as it left the list |
| open gaps | **6** | SUMO's named-city cell **CLOSED** (Barcelona, plus Cologne, Nuremberg, Berlin, Rome, Ingolstadt); TRANSIMS partly closed (SourceForge evidences **7.1, 2018-07-12** — the stored "7.5" is *not* evidenced and is now marked so) |
| **`calibration_methods`** | **10 — NEW** | added for the session's directive: how the field actually calibrates, one row per method with its published objective-evaluation count |

The validation ladder over 48 rows is **7 / 9 / 25 / 7 / 0** (none / survey shares
/ road link counts / transit ridership / per-mode every mode). **The top rung is
still empty.** Our own row is counted separately, is the only attempt at that rung
anywhere, and reads 1 of 12 inside 10 % — recorded as a new reading rather than an
improvement, because three family boundaries and a different iteration separate it
from the previous pass's 0 of 12.

**The new `calibration_methods` array is the most reusable thing this pass
produced.** Two findings in it are worth more than the table: **no project or
framework anywhere in the survey publishes an objective-evaluation count** — the
cost of calibration is the field's unreported number; and the leading open
implementation of the standard answer, `matsim-vsp/matsim-python-tools`, computes
the ASC update verbatim as
`math.log(z_i) - math.log(m_i) - (math.log(z_0) - math.log(m_0))` under Optuna
while its `TerminationCondition.check_termination` carries `# TODO: not used yet`
and no default learning-rate scheduler. The standard answer is standard, widely
used, and unfinished.

### `factors.json` — 33 of 40 searches spent, 5 rounds (8 September 2026, at `6cf0ffd`)

| | count | this pass |
|---|---:|---|
| factors listed | **79** | **7 added**, all in Layers H and I, for the session's directive |
| literature half filled | **79** | 67 of 72 reused unchanged inside the 365-day horizon; 5 rewritten |
| still `needs_research` | **0** | **both remaining rows CLOSED** — workplace location (the finding is that *no* OD-flow tolerance exists anywhere; AToM validates work travel as a mode share to ±1 pp against the 2016 census) and external/through traffic (the M1 Raymond Terrace EIS puts the divertible share at the Hexham cordon at **25–45 %**, and `B.external.through_share = 0.35` sits inside it) |
| statuses stored | **0** | by design. All 79 were re-read at `6cf0ffd` by grep of the registry, `src/`, the city build layer and both Java trees, plus a read-only `check_hardcoding.py`. This pass: **IN 39 · PARTIAL 29 · INERT 2 · ASC 1 · OUT 8** (previous pass: 37 / 27 / 2 / 1 / 5) |

**Not one of the 72 carried-over factors changed status class.** The entire delta
is the seven rows added. Between two reports a day apart, spanning a full
comparability family and a gate firing, the model's *behavioural surface* did not
move — which is itself the result.

The seven new rows carry the evaluation counts that price every candidate method:
SPSA (2 evaluations per gradient step, but 120 % → 117 % in fifteen iterations on
a 30,000-dimension problem); Osorio's analytical metamodel (**120 % → 32 % within
one simulation iteration**, an improved plan at n=10 over 51 variables);
random-forest surrogate under Bayesian optimisation (**477 parameters fitted from
aggregate mode shares alone**, best point at ~150 evaluations); cross-entropy
(**98,304 evaluations** for a three-intersection SUMO model); and in-loop CMA-ES
(zero extra runs, but it needs unit-record survey plans, which the NSW HTS does
not have).

## Where the next pass's budget goes

1. **The residue of the platform gap** — the base OpenPaths 2025 (v25.00.00)
   announcement date is all that is left of it.
2. **Unreached fits** — Brussels (five routes have now failed) and the MDPI
   on-demand study; and the Washington DC study's full text, gold open access
   under CC BY yet Springer 303s to its identity provider.
3. **After 28 September 2026, the MUM 2026 programme**, where a new calibrated
   city scenario or a Wellington validation would surface first. Nothing was
   spent on it this pass because the date is in the future.
4. **Monty (NZ)** now has *five* failed routes including `web.archive.org`, which
   this repository's own network sandbox blocks and which therefore can never
   work from here. Treat it as closed unless a new lead appears.

**Routes that work, and should be reused.** The **Semantic Scholar graph API**
recovered three sources this pass and is the recommended way past MDPI and
Springer. A PDF that `WebFetch` returns as binary can be **saved locally and read
with page ranges at no search-budget cost** — that recovered five of this pass's
best sources, including the Osorio n=10 figure, which was read directly from the
PDF rather than from an abstract.

**Dead routes, recorded so no later pass pays for them again:** `web.archive.org`
(sandbox-blocked), MDPI article HTML (403 on three DOIs), ScienceDirect (403),
ResearchGate (403 to the agent), `arxiv.org/pdf/2112.12071` (over the 10 MB fetch
limit), CMAP's PDF (an image-only scan), `matsim-org/matsim-python-tools` (404 —
it lives under `matsim-vsp`), the eqasim docs path (404), the Open Berlin paper
(403) and opdyts' page (404). The last two are why those methods' outer-run counts
are marked `unknown` rather than guessed.
