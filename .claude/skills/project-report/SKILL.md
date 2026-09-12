---
name: project-report
description: Documents the entire city-digital-twin project in one call and places it in its field - every tracked file read by area with file:line findings and ratings, a code redundancy / quality / efficiency / simplification pass, a simulator performance pass over every run's own timing, the twelve modes one row each with what each is simulated by, what data it has and lacks and what would move it, the dated timeline of every stage and milestone from day 0, every PR, issue (past, present and the risks that are not yet issues), CI run and run on disk, an audit of whether the previous reports were followed and were worth their cost, plus two research passes that start from a standing reference library under cities/<city>/docs/reports/reference/ and search only what it cannot already answer - every comparable city twin and platform with what each does best, and every factor a real-world decision simulator must contain scored against this model - lodged as one dated, self-contained HTML report under cities/<city>/docs/reports/. Use when the user runs /project-report, asks for "a full project assessment", "a code-quality review of everything", "a milestone report across all PRs", "how do we compare to other city twins", "what are we missing", "could this be simpler", "is more data needed", or "where does the whole project stand". Not /onboard and not /handoff - it reads and changes nothing in the model, the data or the living documents.
---

# /project-report — the whole project, assessed, placed in its field, and lodged

Produce **one dated HTML report** at `REPORT_DIR/<yyyymmddThhmmss>_project_report.html`,
where `REPORT_DIR` is `cities/<city>/docs/reports/` (named here once; every
other mention in this file means this directory - a report assesses ONE
city's study, so it lives under that city's documents; the six reports before
11 September 2026 sat under the framework's `docs/` and were moved). In it every number is drawn from an artefact,
every code finding cites `file:line`, every milestone cites its pull request
or record section, every research claim cites the source it was read from
this time, and a reader who has never opened the repository can say what the
project is, how well it is built, how fast it runs, what it has achieved and
when, how it compares with every comparable effort in the world, what the
research says it still lacks, and what it should do next. `/onboard` answers
"where are we" in 600 lines; this answers "how good is all of it, and against
what" in as many lines as the evidence needs.

The report is an assessment, not a change: **it edits nothing under `src/`,
`cities/<city>/` or the living documents**, launches no run, recompiles
nothing, opens no issue. Findings go in the report; fixing them is scoped work
the user decides on. The report file lands through the session's one pull
request at `/handoff`, like any other change. The only files it writes are
the dated report, the `REPORT_DIR/README.md` index and the reference library
at `REPORT_DIR/reference/` that Phases 6 and 7 keep.

**When a report runs: once per READING, not once per session.** The eighth
report's audit of its own series found nine reports in eight days, three of
them on 7 September 4.5 h and 5.7 h apart with one PR and no reading between
them, 125 findings repeated across consecutive reports and 76 of 105
recommendations taken without the goal count moving — because between two
readings a report can add instruments and nothing else. A pass is warranted
after an arm reaches a gate or its horizon, after a family opens on a rebuild,
or when the user asks and says why; the index row names the reading the
report followed. A second report on the same reading is a cost, not an
instrument.

**Pace: a thorough inspection, not a document produced quickly.** A pass may
take hours; every phase reads what it says it reads, and a phase that cannot
finish declares the blind spot rather than closing the gap with a guess.
**When a pass needs the user's decision** - whether the cadence rule is met
and a report is warranted, which optional phase to cut when a budget is gone,
whether to lodge a report the gate has turned red under - ask with
`AskUserQuestion` and clickable choices, the recommended option first; never
a free-text question the user has to compose an answer to.

```
Project report:
- [ ] Phase 0  Ground: gate, tree, digest, the previous report
- [ ] Phase 1  Collect the mechanical half (three scripts)
- [ ] Phase 2  Code: every area read, plus the redundancy / quality / efficiency / simplification pass
- [ ] Phase 3  Simulator: the performance pass
- [ ] Phase 4  History: every PR, the commit log, the timeline from day 0, the report series
- [ ] Phase 5  Documents (placement, currency), controls, the issue ledger
- [ ] Phase 6  The field: the reference library refreshed, only its gaps searched
- [ ] Phase 7  The factors: the library's literature half, this repository's status half
- [ ] Phase 8  Synthesise: findings ranked, ratings evidenced, deltas since last time
- [ ] Phase 9  Write the HTML, lodge it, index it, verify
```

**Parallelism — one agent per phase, six in all.** Phase 1 runs first because
Phases 2–4 read its files. Phases 2–7 are independent of one another: launch
their **six** agents together, in one message, and synthesise when all have
returned — one code reviewer for all six areas, one performance analyst, one
historian, one document reviewer, one field researcher, one factor researcher.

**Never a second agent on the same phase.** Two agents given one phase re-read
the files the other read and re-run the searches the other ran, and the
duplicated research is what made earlier passes chaotic and expensive: the
7 September pass ran three field lanes and three factor lanes, exhausted its
web-search budget, and delivered no platform table and not one literature cell
across 72 factor rows. A phase too large for one agent **narrows its scope and
says so** — Phase 2's depth-of-read line, Phase 6 and 7's named gaps — rather
than growing a second agent. A recorded gap is worth more than a round of
searches nobody reads.

Reviewers and researchers **modify nothing** except `REFERENCE_DIR` (Phases 6
and 7 only) and **never recompile `.tools/classes`** (an arm may be running).

## Phase 0 — Ground

1. `python src/run/session_gate.py --digest`, then `python src/run/session_gate.py`.
   A red gate is reported in the assessment; it is not fixed here.
2. `git status --short` and `git branch --show-current`. **Uncommitted work in
   the tree is somebody's in-flight change**: read its `git diff --stat`, describe
   it in the report's "in-flight work" section, and never commit, revert or
   build on it.
3. Note `HEAD`, the branch and the date. The report is a reading of one commit.
4. Open the **previous report** (newest row of `REPORT_DIR/README.md`) and pull
   the JSON block it embeds at its end (`<script type="application/json" id="report-data">`).
   Its findings, its survey rows, its factor rows and its recommendations are
   what Phase 8's "since the last report" section is measured against. An older
   report without the block is diffed by hand on its findings table
   only. The dated reports are prunable files a user may delete: if none is in
   the tree, recover the newest from `git log -- REPORT_DIR/` if it is there,
   and otherwise take the reference library below as the whole of the prior
   state and say so in "since the last report".
5. Open the **reference library**, `REPORT_DIR/reference/` (`REFERENCE_DIR`
   from here on): its `README.md`, `field-survey.json` and `factors.json`.
   This is the project's standing record of what has already been researched
   and it is the durable half — it survives the deletion of every report.
   Phases 6 and 7 start from it and search only what it does not answer. Read
   its `gaps` array first: that is where this pass's search budget goes.

## Phase 1 — Collect the mechanical half

Three scripts, so the numbers are reproducible and never typed:

```bash
python .claude/skills/project-report/scripts/collect_metrics.py      <scratch>/metrics
python .claude/skills/project-report/scripts/collect_code_metrics.py <scratch>/metrics
python .claude/skills/project-report/scripts/collect_performance.py  <scratch>/metrics
```

- `metrics.json` — file inventory, commit log, direct-to-main commits, churn
  hotspots, the per-merge growth series of registry fields, manifest rows and
  code lines, every PR with its checks and review count, every issue with labels
  and ages, the CI history, the run index — plus `timeline.json` (every dated
  event from the root commit to today) and `prs_full.md` / `issues_full.md`
  for the readers of Phases 4 and 5. `--no-growth` skips the series;
  `--no-github` runs offline.
- `code_metrics.json` — the redundancy / quality / efficiency inventory for
  Phase 2: per-file metrics, long and complex functions, duplicated blocks,
  same-named helpers across files, definitions nothing references, modules
  nothing imports, nested loops, pandas row iteration, wall-clock and unseeded
  randomness in the regenerable layers, unused imports, swallowed exceptions,
  literal mode lists, the Java listener and thread-safety markers, and which
  `src/` modules a unit test imports. Thresholds are named constants at the
  top of the script; quote them.
- `performance.json` — the performance inventory for Phase 3: per run, where
  each iteration's wall time went (from the run's own `stopwatch.csv`), peak
  JVM memory, departures per wall second, which iterations dumped what and how
  many bytes, every `RUN.*` value it ran with; aggregated as pace by sample
  fraction and thread count, pace over time by family, phase shares of the
  longest run at each fraction, machine hours by family and by status, bytes
  on disk. `--no-sizes` skips the disk walk. It reads the head and tail of a
  `matsim.log`, never the whole file.

Every figure in the report's tiles and tables comes from these files or from a
check you ran; **a number you cannot point at does not go in**.

## Phase 2 — Code: every area read, plus the redundancy / quality / efficiency pass

**One reviewer for all six areas**, working them in the order of the table
below and reporting each area separately. Its reading list is
`code_metrics.json` — the long, complex, duplicated, dead and unreferenced
rows are where it starts, not an afterthought — and it reads the files those
rows name, plus every file an area's "look for" column bears on, completely
(Read with offsets, never a skim).

**Depth of read is declared, not assumed.** Where an area is too large to read
whole, the reviewer reads the ranked subset and states one line for that area:
how many files of how many, how many lines of how many, which files went
unread and whether any of them carried a `code_metrics.json` row. An honest
partial read that names its blind spot is the deliverable; a second agent on
the same area is not, and a silent partial read is a defect in the report.

It reports, per area, in a fixed shape: inventory (one line per file),
architecture, findings ranked defect / risk / smell **with `file:line` and a
failure scenario**, the optimisation ledger below, testability, metrics (lines,
functions, longest function, docstring coverage, TODO count) and five ratings
1–5 each with its two strongest pieces of evidence. The areas, and what each
is examined for on top of the project's hard constraints in
`.claude/CLAUDE.md`:

| Area | Files | Look for |
|---|---|---|
| Build layer | `src/build/`, `cities/<city>/build/` | unseeded or order-dependent randomness, wall-clock use, silent fallbacks, constants that belong in the registry, city names in the framework, O(n²) over the population, functions over 150 lines, the same CSV parsed twice |
| Run harness | `run.py`, `src/city.py`, `src/run/`, `src/setup/`, `cities/<city>/overlays/` | Windows-only assumptions, subprocess and lock handling, log readers that scale with a 50 GiB log, races between runner, observer and gate watcher, anything that could delete or rename results wrongly |
| Analysis and calibration | `src/analyse/`, `src/calibrate/` | any path that presents a run whose record does not say `ran_to_last_iteration` as a result, any figure quoted from a stopped arm past its `reached_iteration`, any deviation against an unscorable target, folding and ×1/fraction errors, hardcoded mode lists, duplicated event parsing, the events file read more than once per question |
| Contract and checks | `src/registry/`, `tests/`, `config/schema/`, `cities/<city>/tests/`, `cities/<city>/registry/`, `.github/workflows/` | what each check cannot see, vacuous passes, one-city enums in the portable schemas, registry fields with no consumer, values outside their own sweep, `src/` modules no unit test imports |
| Acquisition and data | `cities/<city>/extract/`, `data/MANIFEST.*`, every `provenance_*.json`, the build reports, the validation targets, the data dictionary | typed-in extents, blank licence or source cells, observed labels on derived values, hosts outside the sandbox allowlist, the holdout's enforcement |
| MATSim extensions | `src/java/`, `src/java_signals/` | thread safety under parallel events and replanning, per-iteration memory growth, plan mutation outside sanctioned boundaries, unseeded Random, id-suffix parsing, string work inside event handlers, anything that could silently teleport a leg |

**The simplification lens.** For every module in its area the reviewer also
asks the question the optimisation ledger does not: *could this be greatly
simpler?* One line per module — what it does in a sentence, what the simplest
correct implementation of that would need (lines, dependencies, a library that
already does it, a MATSim feature that already does it), and the gap between
that and what is there. A module whose gap is large gets a ledger row of kind
*simplification*. The lens is aimed at structure, not style: a layer that
exists only to feed another layer, an abstraction with one consumer, a script
that re-derives what an artefact already holds, three readers of one file
where one pass would do, a bootstrap every script repeats (a `sys.path` edit
in every file is one such), a bespoke mechanism where the engine ships one.
**Retaining every function the module has is the constraint**; a
simplification that drops a behaviour is a defect proposal and is filed as
such.

**The optimisation ledger.** Every reviewer returns, for its area, one row per
candidate change under these headings, and nothing vaguer than a row:

| Column | Meaning |
|---|---|
| kind | *redundancy* (duplicated code, same helper in N files, dead definition, dead module, unused import, unwired registry field) · *quality* (long / complex / deeply nested function, swallowed exception, silent fallback, missing test, unclear ownership) · *efficiency* (repeated parse, nested loop over the population, row-wise pandas, subprocess in a loop, regex compiled per call, whole-file read of a growing log) · *simplification* (a component that could be a fraction of its size with every function kept, a bespoke mechanism the engine or a library already provides, a layer with one consumer) |
| where | `file:line` (both sites for a duplicate) |
| what it costs today | measured where an artefact holds it (a build report's wall time, a log's read size, a line count), reasoned otherwise, and marked which |
| the change | one sentence, concrete enough to file |
| expected saving | a range, never a point; lines removed, seconds saved, reads avoided |
| touches a result? | **none** (output byte-identical) · **opens a family** (the demand, the network or the Java changes, so `DECISIONS.md` §3.5 makes the next arm incomparable) · **unknown until run** |
| guard | the check that would catch a regression after the change (an existing one by name, or the test that would have to be written) |

The "touches a result" column is the one that matters: a change that opens a
family is not cheaper than the arm it invalidates, and the report must say so.
Reviewers **do not modify anything**.

## Phase 3 — Simulator: the performance pass

One analyst, reading `performance.json`, the position page
`cities/<city>/docs/positions/runs-and-economics.md`, the record section that
profiled the iteration (find it with `grep -n "stopwatch" cities/<city>/docs/DECISIONS.md`),
the Java under `src/java/` and `src/java_signals/`, the run overlays under
`cities/<city>/overlays/runs/` and the `RUN.*` fields of the registry. It
answers, each from the artefact that holds it:

1. **Where an iteration goes.** Phase shares at each sample fraction, and how
   they moved between families. Our own listeners are named: which class runs
   in `beforeMobsimListeners`, what it does per iteration, what in it is
   hoistable (computed once per run, not once per iteration), what allocates.
2. **What the mobsim itself costs.** Thread count against the host's cores,
   the qsim settings in force, PT vehicles and stuck agents per iteration,
   departures per wall second — and whether the pace scales with the sample
   fraction the way the sampling position page says it should.
3. **What replanning costs.** Strategy weights, innovation-off fraction, plan
   memory size, router calls per iteration; the innovation-off tail's pace
   against the innovating pace.
4. **What writing costs.** Which iterations dump plans, events, linkstats and
   experienced plans, the bytes each dump costs, the `dump all plans` share,
   the write intervals in force, the bulk per run against the results store's
   budget, and what the observers (progress digest, gate watcher, telemetry)
   read and write per cycle.
5. **What the JVM was given.** Heap against peak use, GC and flags in the
   launcher, whether the heap was ever the binding constraint.
6. **What the Python side costs.** The post-run pipeline (`summarise_run`,
   `extract_metrics`, `fit`, the readers) — what reads the events file, how
   many times, and whether one pass could serve every question.
7. **What the build costs.** No producing script records its wall time
   (`performance.json` says so): the report states that as a finding, and the
   pass recommends where the timing would be written.

Output: one ranked table — change · measured basis (`file` or run name and
figure) · expected saving as a range · touches a result? (as in Phase 2) ·
effort — and a one-paragraph verdict on whether the 250-iteration horizon in
`GOAL.md` is reachable at the measured pace and what would halve it. **A
measurement that needs a run is written as "unmeasured — needs a probe arm"**,
never estimated as though it had been made. The pass launches nothing and
recompiles nothing.

## Phase 4 — History: every PR, the commit log, the timeline from day 0, the report series

One historian reads `prs_full.md` end to end and returns a **ledger with one
block per PR**: delivered (model, data, harness, documents), measured (numbers
quoted exactly), issues closed or opened, record sections added, and an honesty
line — does the body say "nothing is a result" where it should, does it correct
an earlier conclusion, and did a **later** PR correct it. Then statistics (size,
commits per PR, days between, documentation-only count) and a PR-body-quality
tally against the convention in `.claude/CLAUDE.md`.

From `metrics.json`, the commit log gives: totals, merges, **direct commits to
the default branch and their dates** (the rule bans them from 21 Aug 2026),
message-prefix compliance, subject lengths, the busiest day, and the churn
hotspots (which files change most, and whether they are generated).

**The timeline from day 0.** From `timeline.json`, which holds every dated
event the artefacts carry — the root commit, every PR merge, every direct
commit, every row of the record's §14 change log with its section references,
every comparability family at its launch stamp, every run that reached fifty
iterations or stopped at a gate, the board's phase table and the first and last
commit of each `P<n>` stage — the historian builds:

1. **The stage strip**: day 0 to the report date, one lane per stage P0–P7
   with its span, one lane each for families, runs and gates, PR merges, and
   record sections; drawn in Phase 9 as inline SVG from the same JSON.
2. **The milestone table**: one row per milestone with its date, the artefact
   that dates it (PR number, `§9.x`, run name) and what it unlocked. The set
   always includes: first commit; each stage's first and last commit; the
   network rebuild; the first completed arm; the first arm past 100 iterations;
   the first gate that fired; each mode's first reading inside 10 % if any; the
   document restructure; the results store; the issue gate; each family
   boundary; every report lodged. A milestone without an artefact date is
   **not on the timeline** — it is listed under "undated" with what would date it.
3. **The cadence**: days per stage, sessions per week from the record's row
   dates, machine hours per family from `performance.json`, PRs per week; and
   a narrative of at most twelve lines saying what happened when.

**The report process itself.** Every previous report in `REPORT_DIR/README.md`
is a recommendation set with a date; this section reads the whole series and
answers, with counts: how many reports, how many days apart, how many
recommendations each made; for every recommendation of every previous report,
whether it was **taken** (name the PR or commit), **overtaken** (the model moved
so it no longer applies), **repeated** (issued again by a later report without
being taken — count how many times) or **open**; how many findings were
re-reported in two, three or more consecutive reports; what a report costs
(agents, search calls, the size of the file lodged); and what the project
measurably did between reports (PRs merged, arms launched, arms that reached
their horizon, modes that entered or left the 10 % band). The verdict says
whether the reports are being followed, whether following them has moved the
scoreboard or the gate count, and whether the cadence is right — a report a
day that repeats itself is a cost, not an instrument. The verdict is written
against this report too: it names the recommendations below that are repeats.


## Phase 5 — Documents, process and controls

One reviewer reads every living and archived document (never `DECISIONS.md`
whole: its first 210 lines, its headings, its topical index and its §14 change
log), every hook, workflow, skill and settings file, and runs a relative-link
check over every Markdown file. It reports: the layering and whether the
reading-budget line counts in `docs/HANDOVER_CONTRACT.md` hold; every archived
file bannered frozen; the record's numbering monotonic and every section
indexed; **numbers that disagree between two living documents, with both
`file:line`s**; stale family stamps on position pages; every rule stated as
advice that no hook or check enforces; and three control questions — what a
hook or workflow could do with the permissions it holds and whether it needs
them, which dependencies and toolchain versions are pinned by hash and which
by name, and whether the ODbL / CC-BY boundary is visible in every artefact
that crosses it.

**Documents: placed right, and current.** For every document the reviewer
states whether it is in the layer its content belongs to (`GOAL.md` /
the board / a position page / the record / the framework's `docs/` / a city's
`docs/` / a skill) and names each one that is not, with where it belongs; and
for every living document, the newest artefact it describes and whether the
description still holds. A document is *misplaced* when a reader looking for
its content would open a different file first, and *stale* when an artefact it
describes has moved since its stamp.

**The issue ledger: past, present, upcoming.** From `issues_full.md` and the
GitHub API output in `metrics.json`: (a) **past** — every closed issue with its
open and close dates, days open, and whether it closed on evidence (a PR, a
run, a measurement it cites) or by decision; the median days open and the
oldest ever; (b) **present** — every open issue with its state under
`GOAL.md` requirement 10 (`awaiting-run` + measurement / `decision-needed` /
`awaiting-implementation`), the run or decision it waits on, and **whether the
record has overtaken it** (a position page or a merged PR says the thing it
asks for is built or measured); (c) **upcoming** — every risk the reviewers of
Phases 2, 3 and 5 raised that is not an issue yet, ranked by what it would cost
if it fired, each with the one-line issue title it would be filed under. The
upcoming list is the raw material for the issue-filing step that follows a
report; it is written so a user can file it without re-deriving it.

## Phase 6 — The field: the library first, only its gaps searched

**One researcher**, `WebSearch` and `WebFetch` only (the shell's network is
sandboxed to data sources; `curl` will not reach a paper). It opens
`REFERENCE_DIR/field-survey.json` **before it runs a single search**, and
treats it as the answer, not as a hint.

**The reuse rule.** A stored row inside its freshness horizon is carried into
the report as it stands and **is not searched for again**. Search is spent
only on the left-hand column:

| Search this | Leave this alone |
|---|---|
| a project or platform the library has no row for | any row inside its horizon |
| a cell the row records as `unknown`, `ambiguous` or empty | a cell the row already answers with a source URL |
| a row whose facts are past **180 days** (engine, city, modes, validation rung, published fit) | a fact that cannot move: what a 2019 paper measured is what it measured |
| a liveness cell past **90 days** (active / dormant, last release or paper date) | a row's liveness inside 90 days |
| anything the library lists in `gaps` | a candidate already in `excluded`, unless its reason is `not re-verified` |

A reused row is rendered with `reused` and its `last_verified` date in the
sources column, so a reader sees exactly what was checked this pass and what
was inherited. **Reuse is not a shortcut to apologise for: it is how the
library pays for itself.** A row searched for and not re-found keeps its
stored attributes and gains `not_reverified_on: <date>`; it is never emptied.

**The search budget: at most 40 searches or fetches for this phase**, spent in
the order of the table above — the library's own `gaps` first, then
never-seen candidates, then `unknown` cells, then expiries. When the budget is
gone, everything still unsearched is written back into `field-survey.json` as
a named `gap` carrying the query that would close it, and the report says which
gaps it inherited and which it added. A search whose result reaches no row and
no gap was a wasted search; do not run its variants again.

**Who qualifies.** A project that models a real city or region with agents
(activity-based or agent-based, any engine) and publishes a validation claim of
any kind; and a platform (open or commercial) on which such projects are built.
A candidate checked and excluded is written to the library's `excluded` list
with its reason (no validation claim, not a real city, a demo) **so that no
later pass pays for it again**. The territory — every public MATSim scenario
and eqasim derivative, the SUMO / Aimsun / PTV / POLARIS / BEAM / ActivitySim /
SimMobility / mobiTopp / TRANSIMS / Cube / EMME worlds, the commercial and
national "digital twin" platforms and city programmes, the LLM-agent and
generative-agent mobility simulators of the last three years, and what a
transport agency, a university lab or a GitHub search turns up under *city
digital twin*, *agent-based transport model*, *activity-based model
validation*, *multimodal microsimulation calibration* — is the territory the
**library** is meant to cover, not the territory each pass re-walks. Sweep only
the parts of it the library is blank or stale on.

**Stopping rule**: stop when the budget is spent, or when two successive rounds
of differently phrased searches add no qualifying entry the library does not
already hold. Record the round count and the searches spent.

**One row per project**, these columns, an `unknown` where the source does not
say (never a guess, never a figure remembered from training):

engine · city and population · sample fraction · modes simulated · active
modes physical or teleported · public transport physical · signals · freight ·
fares and pricing · **validation rung** (none / survey shares / road link counts /
transit ridership counts / per-mode ridership, every simulated mode) · best
published fit with its metric and what it was measured on · open source ·
reproducible pipeline · city-agnostic · **status** (active / dormant, last
release or paper date) · **what it does best** (one line; the thing this
project could learn from it) · sources (at least one URL per row; a paywalled
source gives `unknown`, and says so).

**One row per platform**: engine, licence, last release, city-agnostic by
design, what it does best, who runs on it. **Our row** is filled from the
artefacts only — the board's scoreboard for the reading, the registry for what
is priced and signalled, the run record for the sample — and says "in
calibration, no mode inside 10 %" if that is what the board says.

Output, **written before the researcher returns** so the work survives an
interrupted pass: the refreshed `REFERENCE_DIR/field-survey.json` — every row
reused, updated or added, each with its `sources`, `last_verified` and
`verified_in`, plus the refreshed `excluded`, `not_reverified` and `gaps`
arrays. Then a copy at `<scratch>/research/field.json` for the writer, which
renders the table, the validation-ladder chart, a "what the comparison says"
list of at most eight bullets, a "what each does best that we lack" list that
feeds Phase 8's recommendations, and the delta since the previous pass
(projects that appeared, went dormant, moved a rung, were not re-verified, or
were carried unchanged from the library).

## Phase 7 — The factors: the library's literature, this repository's status

**One researcher**, the same tools, and one rule that splits the row in half:

- **The literature half is reused.** What the research says about a factor,
  its magnitude, its source and how the leading simulators of Phase 6
  implement it come from `REFERENCE_DIR/factors.json` under a **365-day**
  horizon — a 2021 meta-analysis says the same thing this week as last. Search
  only for a factor the library has no row for, a row whose
  `what_research_says` is empty or marked `needs_research`, or a row past the
  horizon. **The seeded library has 72 rows whose literature half is empty**
  (the 7 September pass ran out of budget before writing it); those rows are
  where this phase's budget goes, highest `relevance` first.
- **The status half is never reused.** Every factor's status in this model —
  IN / PARTIAL / INERT / ASC / OUT — is re-read at `HEAD` on every pass
  without exception, by `grep` of the registry and the Java, not by a search.
  The model moves weekly and a status carried forward is a status that is
  wrong, which is why the library deliberately does not store one.

**The search budget: at most 40 searches or fetches for this phase.** What it
does not reach is written back as a `needs_research: true` row with the query
that would close it, so the next pass resumes instead of restarting.

The question is wider than mode choice: **every factor that the research says
bears on how people and goods decide to move, and every mechanism a simulator
needs to reproduce those decisions**, organised by decision horizon and layer:

| Layer | Covers |
|---|---|
| A. Long-term choices | residential and workplace location, vehicle ownership and type (including EV and e-bike), licence holding, public-transport passes |
| B. Daily activity pattern | activity generation and scheduling, joint household decisions, escort, telework, day-type differences |
| C. Destination choice | attraction, distance decay, constraints at both ends, intra-zonal trips |
| D. Departure time | peak spreading, schedule delay, activity duration preferences |
| E. Mode choice | time and money; household resources; person attributes; the built form; the trip; comfort, safety, habit, weather, scenery; mode-specific factors for every one of the twelve modes |
| F. Route and within-day | route choice, re-routing and information, parking search, boarding and crowding, ride pairing, reliability |
| G. Supply and physics | network detail, signals, transit operations and dwell, capacity, freight and external traffic, incidents, weather |
| H. Behavioural machinery | utility form, heterogeneity and value-of-time segments, choice-set generation, learning and replanning, plan memory, habit, satisficing, LLM-driven agents |
| I. Calibration and validation | targets and the validation ladder, holdouts, convergence criteria, replication across seeds, sensitivity and sweeps |
| J. Data | population synthesis, travel surveys, smartcard, counts, GTFS, OSM, what is disclosed and what must be derived |
| K. Computation | sample fraction and scaling rules, iteration count, reproducibility, cost per iteration |

**One row per factor**: what the research says, with the source read this
pass (a benchmark synthesis or meta-analysis where one exists, named); how the
leading simulators of Phase 6 implement it; **status in this model** — IN /
PARTIAL / INERT (declared in the registry, read by nothing) / ASC (folded into
a mode constant) / OUT — **proven** by the registry key or the `file:line` that
holds it, checked this pass (`grep` the registry and the Java; the
declared-but-unwired list from `check_hardcoding.py` is the INERT source); and
what it would move on the current scoreboard, tied to a mode's present
deviation. Magnitudes are central tendencies from the literature, labelled
`literature` exactly as the registry's source classes would label them; **no
coefficient is invented, no literature value is presented as observed.**

Output, **written before the researcher returns**: the refreshed
`REFERENCE_DIR/factors.json` — the literature half of every row with its
`source_url`, `last_verified` and `needs_research` flag, and **no status
column** (Phase 8 joins this pass's freshly read statuses to it). Then
`<scratch>/research/factors.json` for the writer, carrying both halves,
rendered as the ledger with its status tiles and a **ranked "would move the
scoreboard" list** — strength of evidence × relevance to a current deviation ×
how much of the data is already in the package — that feeds Phase 8's
recommendations; plus the delta since the previous pass (statuses that changed,
factors added, factors retired, literature halves newly filled).

## Phase 8 — Synthesise

1. **Merge the findings into one ranked table**: severity (defect / risk /
   smell), area, `file:line`, one sentence, failure scenario. Deduplicate
   across reviewers; keep the sharper citation.
2. **Merge the optimisation ledgers** (Phases 2 and 3) into one table, sorted
   by expected saving within "touches a result = none" first, then the
   family-opening ones, then the unmeasured.
3. **Ratings**: one row per area, the five dimensions, each cell carrying its
   evidence in a tooltip or footnote. Never average ratings across areas.
4. **Milestones against the goal**: for each hard requirement in
   `cities/<city>/docs/GOAL.md`, met / unmet / unmeasured, with the PR and the
   record section that decided it, and the date from the timeline.
4b. **The twelve modes, one row each.** Built from the board's reader
   (`report_mode_ridership.py` on the newest RESULT and, separately, on the
   newest citable reading), the validation targets, the registry, the position
   pages and the reviewers' reports — never from memory. Columns: modelled ·
   target · deviation at the newest result · at the newest citable reading
   (labelled as not a result) · **target provenance** (disclosed / derived /
   vintage, with the file) · **how the mode is simulated** (which engine
   carries it, physical or teleported, which legs are not) · **data it has**
   (the observations in the package that bear on it) · **data it lacks** (the
   observation that would settle its deviation, whether it is obtainable, and
   from whom) · **the mechanism** the evidence names for its deviation · the
   **controls** that exist for it (built / run / unrun, by registry key) · the
   **next measurement**. Then a **supply-fidelity table** for the physical
   layer the modes share — roads and lanes, speeds, signals, level crossings,
   PT timetables and dwell, vehicles and capacity, parking, fares and
   pricing, freight and external traffic — each row: what is real (from which
   artefact), what is derived, what is assumed, what is absent. These two
   tables answer, from evidence, whether more data is needed for a mode and
   whether a more realistic implementation of the traffic system is needed.
5. **The project in its field**: where our row sits on the validation ladder,
   what no other project attempts, what several do that we do not, and the
   factor ledger's counts (IN / PARTIAL / INERT / ASC / OUT) with the top
   movers.
6. **Since the last report**: findings closed, still open, new; survey rows
   changed; factor statuses changed; recommendations taken up or not, with the
   PR that did so.
7. **Verify a sample**: re-read ten cited `file:line`s yourself, and re-fetch
   the sources of **five rows that were searched this pass**. Rows reused from
   the library are verified by inspection — each must carry at least one
   source URL and a `last_verified` inside its horizon — and are not
   re-fetched; re-fetching them is the duplicated work this design exists to
   stop. A finding or a row that does not survive the check is dropped, not
   softened, and a reused row that fails inspection is sent back to `gaps`.
8. **Recommendations**, ranked by (what it would prevent or move) × (how
   cheap), each naming the file or registry key to change, whether it opens a
   family, and the check that would then catch a regression. At most twenty.

## Phase 9 — Write, lodge, index, verify

1. **The report is rendered, not hand-written.** Every lane writes JSON
   (`<scratch>/reviews/phase{2,3,4,5}_*.json`, `<scratch>/research/{field,factors}.json`),
   Phase 8 writes `<scratch>/modes_table.json` and `<scratch>/synthesis.json`
   (verdict, method, the goal table, the merged findings and ledger, ratings,
   since-last-report, recommendations, own verifications), and

   ```bash
   python .claude/skills/project-report/scripts/render_report.py <scratch> REPORT_DIR/<stamp>_project_report.html
   ```

   renders the whole file: a standalone `<!doctype html>`, `<html lang="en-AU">`,
   inline CSS, Google Fonts with real fallback stacks, light and dark themes,
   every table inside `overflow-x:auto`, the charts as inline SVG from the same
   JSON (the per-mode deviation bars, the stage strip, the growth and
   report-series lines), and the `report-data` block at the end. A lane's key
   that is missing renders as a stated gap, never as an empty box, and an
   unknown shape falls back to a generic table or list, so a lane may add a
   field without the renderer changing. Load `artifact-design` and `dataviz`
   before changing the renderer's CSS or charts, not before every pass: the
   design is fixed in the script and the pass's craft goes into the JSON. The
   six reports before 11 September 2026 were written by hand at 0.8–1.8 MB
   each; the renderer is what makes the ninth pass cost what the eighth did.
2. Sections, in order: masthead (date, HEAD, branch, gate result, one-paragraph
   verdict) · at-a-glance tiles · method (what was read, by whom, the rating
   rubric, the search rounds run) · **the timeline from day 0** (stage strip,
   milestone table, cadence) · repository anatomy (inventory, growth series,
   churn) · code quality by area · the ranked findings table · **the
   optimisation ledger** (redundancy / quality / efficiency / simplification,
   with the touches-a-result column) · **the simulator performance pass**
   (phase shares, pace scaling, memory, writing, the ranked changes, the
   250-iteration verdict) · testing and CI · the PR ledger · the commit log ·
   **the issue ledger** (past, present, upcoming) · runs on disk and their
   cost · milestones against the goal · **the twelve modes, one row each, and
   the supply-fidelity table** · **the project in its field** (the survey
   table, the platform table, the validation ladder, what the comparison
   says) · **the factor ledger** (by layer, with the status tiles and the
   ranked movers) · the document and process layer (placement and currency
   included) · in-flight work seen in the tree · **since the last report, and
   the report process itself** · recommendations · appendix (rubric, sources,
   how this report was produced and how to reproduce it, search rounds per
   lane).
3. **Embed the data** the report was written from at the end of the file, in
   `<script type="application/json" id="report-data">`: the summaries from
   the three collectors, the findings table, the optimisation ledger,
   `field.json`, `factors.json`, the recommendations. The next report diffs
   against it (Phase 0.4). Keep the file under 4 MB; trim the embedded
   per-run detail before trimming anything a reader sees.
4. Name it `REPORT_DIR/<yyyymmddThhmmss>_project_report.html` with the stamp
   from `date +%Y%m%dT%H%M%S` at the time of writing. Never overwrite an
   earlier report; the directory is a dated series.
5. Add a row for the new report to `REPORT_DIR/README.md` (create it from the
   previous report's row if absent) — newest first, with the HEAD it read and a
   headline of **at most 80 words** that states the verdict, the count of
   findings, the top optimisation, where we sit on the validation ladder and
   the top missing factor. The headline is an index entry, not the report:
   every earlier row that ran to several hundred words made the index
   unreadable, and the detail it carried is in the report it points at.
6. **Confirm the reference library was written.** `REFERENCE_DIR/field-survey.json`
   and `factors.json` must carry this pass's stamp, and `REFERENCE_DIR/README.md`
   must state, for each file, its row count, how many rows were reused, refreshed
   and added this pass, and how many gaps remain open. If a research phase
   returned without writing its file, the report says the library is unchanged
   for that lane and why — it never silently keeps the old file and claims a
   fresh pass. The library is committed: the dated reports are prunable, it is
   not.
7. `python src/run/session_gate.py` must still pass; the report, the index and
   the reference library are the only files this skill changes. Publish the same file as an Artifact
   as well when the harness offers one, so the user has a link, but the file
   under `REPORT_DIR` is the deliverable.
8. Close with the ranked recommendations in the reply, at most twelve lines,
   the report's path, and the one-line placing in the field. Then stop: the
   change lands at `/handoff`.

## After the report - the follow-on the report feeds

The report changes nothing; what follows it does, and it is scoped work the
user authorises step by step (clickable choices at each). The order is fixed
because each step is the input of the next:

1. **The issue ledger becomes the tracker.** Every *upcoming* risk in Phase 5's
   ledger is filed as an issue under its one-line title, in the
   `P<phase>: <summary>` scheme; every *present* issue the record has
   overtaken is closed on the evidence the report cites (a PR, a run, a
   measurement), or moved to `awaiting-run` with its `AWAITING-RUN:` line or
   `decision-needed` with its `AWAITING-DECISION:` line (GOAL.md requirement
   10). A risk filed twice is one issue; check the open set first.
2. **Everything fixable without a run is fixed before the next run.** Work the
   ranked findings, the optimisation ledger's `touches a result = none` rows
   and every open issue that needs no arm, in the ranking the report gave,
   on the session branch; `check_hardcoding.py --strict` and the doc gates
   stay green after each. A row that opens a family is worked only if the
   next arm was going to open one anyway, and the record says so.
3. **The run is handed off when nothing else stands in front of it.** When the
   issue gate is green, every remaining issue names the measurement or
   decision it waits on and the brief's lane is the arm, `/handoff` closes the
   session; the next agent's first item is the stated-cost approval and the
   launch, and the next report runs after that arm's gate - one per reading.
   Ask before stopping short: whether anything is left that a run does not
   need is a judgement the user confirms, not one the session takes alone.

## What this skill never does

- Never edits the model, the data, the registry, the board, the brief, a
  position page or the record. A finding about them goes in the report.
- Never launches or stops a run, never recompiles the toolchain, never reads a
  `matsim.log` whole.
- Never rates an area without citing the evidence, and never states a number
  it did not collect or read.
- Never carries a **status in this model** forward: every factor's IN / PARTIAL
  / INERT / ASC / OUT is re-read at `HEAD` from the registry or a `file:line`,
  every pass, by `grep` and never by search. The external half — what the
  research says, what a comparable project is — is reused from `REFERENCE_DIR`
  under Phase 6's horizons.
- Never re-searches what the reference library already answers, never runs more
  than one agent on a phase, and never spends a research lane past its 40-call
  budget: what is left over is a named gap in the library, not another round.
- Never returns from a research phase without writing the library, and never
  deletes a stored row because this pass could not re-find it.
- Never presents a literature value as observed, never fills an `unknown`
  from memory, never fetches with `curl`.
- Never reads `DECISIONS.md`, `SESSION_LOG.md` or `CONFIG_REFERENCE.md` whole.
- Never proposes a simplification that drops a function the component has:
  that is a defect proposal, and is filed as one.
- Never judges its own series kindly: the process audit counts this report's
  repeats too.
