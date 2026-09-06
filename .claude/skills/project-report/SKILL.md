---
name: project-report
description: Documents the entire city-digital-twin project in one call and places it in its field - every tracked file read by area with file:line findings and ratings, a code redundancy / quality / efficiency pass, a simulator performance pass over every run's own timing, the dated timeline of every stage and milestone from day 0, every PR, issue, CI run and run on disk, plus two research passes done from scratch each time - every comparable city twin and platform with what each does best, and every factor a real-world decision simulator must contain scored against this model - lodged as one dated, self-contained HTML report under docs/reports/. Use when the user runs /project-report, asks for "a full project assessment", "a code-quality review of everything", "a milestone report across all PRs", "how do we compare to other city twins", "what are we missing", or "where does the whole project stand". Not /onboard and not /handoff - it reads and changes nothing in the model, the data or the living documents.
---

# /project-report — the whole project, assessed, placed in its field, and lodged

Produce **one dated HTML report** at `REPORT_DIR/<yyyymmddThhmmss>_project_report.html`,
where `REPORT_DIR` is `docs/reports/` (named here once; every other mention in
this file means this directory). In it every number is drawn from an artefact,
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
request at `/handoff`, like any other change.

```
Project report:
- [ ] Phase 0  Ground: gate, tree, digest, the previous report
- [ ] Phase 1  Collect the mechanical half (three scripts)
- [ ] Phase 2  Code: every area read, plus the redundancy / quality / efficiency pass
- [ ] Phase 3  Simulator: the performance pass
- [ ] Phase 4  History: every PR, the commit log, the timeline from day 0
- [ ] Phase 5  Documents, process and controls
- [ ] Phase 6  The field: every comparable project and platform, researched from scratch
- [ ] Phase 7  The factors: what a real-world decision simulator contains, researched from scratch
- [ ] Phase 8  Synthesise: findings ranked, ratings evidenced, deltas since last time
- [ ] Phase 9  Write the HTML, lodge it, index it, verify
```

**Parallelism.** Phase 1 runs first because Phases 2–4 read its files. Phases
2–7 are independent of one another: launch every reviewer and researcher of
those phases **together, in one message**, and synthesise when all have
returned. The working number is fourteen agents — six code reviewers, one
performance analyst, one historian, one document reviewer, two or three field
researchers, two or three factor researchers. Add one wherever an area passes
~6,000 lines or a research lane passes ~25 candidates. Reviewers and
researchers **modify nothing** and **never recompile `.tools/classes`** (an
arm may be running).

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
   report without the block is diffed by hand on its findings table only.

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

Spawn one reviewer per area, each told to **read every file completely** (Read
with offsets, never a skim), to start from its area's rows in
`code_metrics.json`, and to report in a fixed shape: inventory (one line per
file), architecture, findings ranked defect / risk / smell **with `file:line`
and a failure scenario**, the optimisation ledger below, testability, metrics
(lines, functions, longest function, docstring coverage, TODO count) and five
ratings 1–5 each with its two strongest pieces of evidence. The areas, and what
each is told to look for on top of the project's hard constraints in
`.claude/CLAUDE.md`:

| Area | Files | Look for |
|---|---|---|
| Build layer | `src/build/`, `cities/<city>/build/` | unseeded or order-dependent randomness, wall-clock use, silent fallbacks, constants that belong in the registry, city names in the framework, O(n²) over the population, functions over 150 lines, the same CSV parsed twice |
| Run harness | `run.py`, `src/city.py`, `src/run/`, `src/setup/`, `cities/<city>/overlays/` | Windows-only assumptions, subprocess and lock handling, log readers that scale with a 50 GiB log, races between runner, observer and gate watcher, anything that could delete or rename results wrongly |
| Analysis and calibration | `src/analyse/`, `src/calibrate/` | any path that presents a run whose record does not say `ran_to_last_iteration` as a result, any figure quoted from a stopped arm past its `reached_iteration`, any deviation against an unscorable target, folding and ×1/fraction errors, hardcoded mode lists, duplicated event parsing, the events file read more than once per question |
| Contract and checks | `src/registry/`, `tests/`, `config/schema/`, `cities/<city>/tests/`, `cities/<city>/registry/`, `.github/workflows/` | what each check cannot see, vacuous passes, one-city enums in the portable schemas, registry fields with no consumer, values outside their own sweep, `src/` modules no unit test imports |
| Acquisition and data | `cities/<city>/extract/`, `data/MANIFEST.*`, every `provenance_*.json`, the build reports, the validation targets, the data dictionary | typed-in extents, blank licence or source cells, observed labels on derived values, hosts outside the sandbox allowlist, the holdout's enforcement |
| MATSim extensions | `src/java/`, `src/java_signals/` | thread safety under parallel events and replanning, per-iteration memory growth, plan mutation outside sanctioned boundaries, unseeded Random, id-suffix parsing, string work inside event handlers, anything that could silently teleport a leg |

**The optimisation ledger.** Every reviewer returns, for its area, one row per
candidate change under these headings, and nothing vaguer than a row:

| Column | Meaning |
|---|---|
| kind | *redundancy* (duplicated code, same helper in N files, dead definition, dead module, unused import, unwired registry field) · *quality* (long / complex / deeply nested function, swallowed exception, silent fallback, missing test, unclear ownership) · *efficiency* (repeated parse, nested loop over the population, row-wise pandas, subprocess in a loop, regex compiled per call, whole-file read of a growing log) |
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

## Phase 4 — History: every PR, the commit log, the timeline from day 0

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

## Phase 6 — The field: every comparable project and platform, from scratch

Two or three researchers, `WebSearch` and `WebFetch` only (the shell's
network is sandboxed to data sources; `curl` will not reach a paper). The
deliverable is a table where **every cell was read from a source found in this
pass**. The previous report's survey, the artefact *Twenty City Twins* and any
memory of the field are **candidate lists only**: a project they name is a
query to run, never a row to copy. A row that cannot be re-found is listed as
"not re-verified this pass" and carries no attributes.

**Who qualifies.** A project that models a real city or region with agents
(activity-based or agent-based, any engine) and publishes a validation claim of
any kind; and a platform (open or commercial) on which such projects are built.
A candidate checked and excluded is listed with the reason (no validation
claim, not a real city, a demo). Do not stop at the well-known: the sweep
covers, at least, every public MATSim scenario and every eqasim derivative,
the SUMO / Aimsun / PTV / POLARIS / BEAM / ActivitySim / SimMobility / mobiTopp /
TRANSIMS / Cube / EMME worlds, the commercial and national "digital twin"
platforms and city programmes, the LLM-agent and generative-agent mobility
simulators of the last three years, and anything a transport agency, a
university lab or a GitHub search turns up under the terms *city digital twin*,
*agent-based transport model*, *activity-based model validation*, *multimodal
microsimulation calibration*. **Stopping rule**: a lane stops when three
successive rounds of differently phrased searches across different venues
(indexed papers, agency pages, GitHub, conference proceedings, user-meeting
programmes) add no new qualifying entry. Record the round count.

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

Output: a JSON file (`<scratch>/research/field.json`) the writer renders as the
table, the validation-ladder chart, a "what the comparison says" list of at
most eight bullets, a "what each does best that we lack" list that feeds
Phase 8's recommendations, and the delta since the previous report (projects
that appeared, went dormant, moved a rung, or were not re-verified).

## Phase 7 — The factors: what a real-world decision simulator contains, from scratch

Two or three researchers, the same tools and the same rule: **from scratch**,
the previous ledger and the artefact *The Mode-Choice Ledger* being candidate
checklists whose every row is re-researched and whose every status is re-read
from the repository as it stands at `HEAD` — the model moves weekly and a
status carried forward is a status that is wrong. The question is wider than
mode choice: **every factor that the research says bears on how people and
goods decide to move, and every mechanism a simulator needs to reproduce those
decisions**, organised by decision horizon and layer:

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

Output: `<scratch>/research/factors.json`, rendered as the ledger with its
status tiles, and a **ranked "would move the scoreboard" list** — strength of
evidence × relevance to a current deviation × how much of the data is already
in the package — that feeds Phase 8's recommendations; plus the delta since the
previous report (statuses that changed, factors added, factors retired).

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
5. **The project in its field**: where our row sits on the validation ladder,
   what no other project attempts, what several do that we do not, and the
   factor ledger's counts (IN / PARTIAL / INERT / ASC / OUT) with the top
   movers.
6. **Since the last report**: findings closed, still open, new; survey rows
   changed; factor statuses changed; recommendations taken up or not, with the
   PR that did so.
7. **Verify a sample**: re-read ten cited `file:line`s and re-fetch five
   research rows' sources yourself before they go in. A finding or a row that
   does not survive the re-read is dropped, not softened.
8. **Recommendations**, ranked by (what it would prevent or move) × (how
   cheap), each naming the file or registry key to change, whether it opens a
   family, and the check that would then catch a regression. At most twenty.

## Phase 9 — Write, lodge, index, verify

1. Load the `artifact-design` and `dataviz` skills before writing. The report
   is a **standalone** file: full `<!doctype html>`, `<html lang="en-AU">`,
   `<head>` with `<meta charset>` and viewport, all CSS and JS inline, fonts
   with real fallback stacks, no external resources except optionally Google
   Fonts, light and dark themes, no horizontal page scroll (tables inside
   `overflow-x:auto`). Charts are inline SVG built from the data in the file.
2. Sections, in order: masthead (date, HEAD, branch, gate result, one-paragraph
   verdict) · at-a-glance tiles · method (what was read, by whom, the rating
   rubric, the search rounds run) · **the timeline from day 0** (stage strip,
   milestone table, cadence) · repository anatomy (inventory, growth series,
   churn) · code quality by area · the ranked findings table · **the
   optimisation ledger** (redundancy / quality / efficiency, with the
   touches-a-result column) · **the simulator performance pass** (phase shares,
   pace scaling, memory, writing, the ranked changes, the 250-iteration
   verdict) · testing and CI · the PR ledger · the commit log · the issue
   ledger · runs on disk and their cost · milestones against the goal ·
   **the project in its field** (the survey table, the platform table, the
   validation ladder, what the comparison says) · **the factor ledger** (by
   layer, with the status tiles and the ranked movers) · the document and
   process layer · in-flight work seen in the tree · **since the last report** ·
   recommendations · appendix (rubric, sources, how this report was produced
   and how to reproduce it, search rounds per lane).
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
   headline that states the verdict, the count of findings, the top optimisation,
   where we sit on the validation ladder and the top missing factor.
6. `python src/run/session_gate.py` must still pass; the report and the index
   are the only files this skill changes. Publish the same file as an Artifact
   as well when the harness offers one, so the user has a link, but the file
   under `REPORT_DIR` is the deliverable.
7. Close with the ranked recommendations in the reply, at most twelve lines,
   the report's path, and the one-line placing in the field. Then stop: the
   change lands at `/handoff`.

## What this skill never does

- Never edits the model, the data, the registry, the board, the brief, a
  position page or the record. A finding about them goes in the report.
- Never launches or stops a run, never recompiles the toolchain, never reads a
  `matsim.log` whole.
- Never rates an area without citing the evidence, and never states a number
  it did not collect or read.
- Never carries a survey row or a factor status forward from an earlier pass:
  every row is re-found and every status re-read at `HEAD`.
- Never presents a literature value as observed, never fills an `unknown`
  from memory, never fetches with `curl`.
- Never reads `DECISIONS.md`, `SESSION_LOG.md` or `CONFIG_REFERENCE.md` whole.
