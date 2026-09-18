## Phase 2 — Code: every area read, plus the redundancy / quality / efficiency pass

**One reviewer for all six areas**, working them in the order of the table
below and reporting each area separately. Its reading list is
`code_metrics.json` — the long, complex, duplicated, dead and unreferenced
rows are where it starts, not an afterthought — and it reads the files those
rows name, plus every file an area's "look for" column bears on, completely
(use bounded file reads until the selected files are covered).

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
`.agents/AGENTS.md`:

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
`docs/positions/runs-and-economics.md`, the record section that
profiled the iteration (find it with `rg -n "stopwatch" docs/DECISIONS.md`),
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
7. **What the build costs.** Inspect current build timing artefacts and their
   producing scripts. If timing is absent, report that gap and recommend where
   to record it. Do not inherit a previous report's claim that timing is absent.

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
tally against the convention in `.agents/AGENTS.md`.

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
the board / a position page / the record / the reports / `docs/README.md` or
the contract / a skill) and names each one that is not, with where it belongs; and
for every living document, the newest artefact it describes and whether the
description still holds. A document is *misplaced* when a reader looking for
its content would open a different file first, and *stale* when an artefact it
describes has moved since its stamp.

**The session process: what every session pays, and what it pays for.** The
same reviewer audits the procedures the sessions run — `$onboard`, `$handoff`,
and this skill — as work, from evidence, not from memory. The evidence is the
last five sessions' record sections (each §9.x's *What changed* and the §14
row), their pull requests (`gh pr view <n> --json files,additions,deletions`)
and the skills' own text. It reports:

- **Document churn per session**: for each of the last five PRs, the lines
  changed in `docs/positions/`, `docs/STATUS.md`, `docs/NEXT_AGENT_BRIEF.md`
  and `docs/DECISIONS.md`, and how many position pages were rewritten. A page
  rewritten on every handoff whose *What is built* did not change is a page
  the handoff re-keys, not consolidates.
- **Facts with more than one home**: every number or run name that appears
  verbatim in two or more living documents (the board, the brief, the
  position pages, the contract), each with both `file:line`s — whether or not
  they still agree. The disagreeing ones are the defect; the agreeing ones are
  the next session's re-keying cost.
- **Steps the skills prescribe by hand**: each step in the three skills that is
  prose ("edit", "find", "place", "rewrite") rather than a command, with the
  record section where a session last did it by hand and what it cost there
  (a mis-numbered section, a cap breached three times, a mis-ordered index row
  — §9.176 holds one of each); and each command a session ran ad hoc (a scratch
  script named in a record) that the repository does not hold.
- **Steps that yield nothing**: each phase or step of the three skills — this
  one included — whose output in the last three passes produced no finding,
  no recommendation taken, and no change to a decision (this skill's Phases 6
  and 7 are measured by rows changed in `REFERENCE_DIR`, not by rows
  re-verified); and each check that has never gone red since it was added
  (`git log -S` on its name) beside each check that went red at a handoff and
  was fixed in the same PR. A step that costs and yields nothing is a
  recommendation to drop or fold it; a check that never fires is not proof it
  is useless — say which of the two it is, and why.
- **What a session waited on**: from the records, every wait a session spent on
  a computation it could have cached or run once — a reader re-deriving every
  iteration, a gate run four times for one claim, a monitor polling on a clock —
  and the seconds and the arm-CPU it cost where a record states them.

Each finding here becomes a recommendation in Phase 8 with the category
`process`, ranked like the others by what it prevents or saves × how cheap; a
process recommendation names the skill section or the script it changes and the
check that would catch the regression, exactly as a model one names a registry
key. This skill's own steps are in scope: a recommendation to shorten or drop a
phase of the report is made here, and the next report's audit records whether
it was taken.

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
