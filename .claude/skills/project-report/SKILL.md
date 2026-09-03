---
name: project-report
description: Assesses the whole city-digital-twin repository to its full depth - every tracked file read by area, the code quality of each layer with file:line findings and ratings, the milestones delivered by every pull request and commit, the issue ledger, the CI history, the run index, the data package and the document system - and lodges one dated, self-contained HTML report under docs/reports/. Use when the user runs /project-report, asks for "a full project assessment", "a code-quality review of everything", "a milestone report across all PRs", or "where does the whole project stand, in depth". Not a session opener (/onboard) and not a close-out (/handoff): it reads, it does not change the model, the data or the living documents.
---

# /project-report — the whole repository, assessed and lodged

Produce **one dated HTML report** at
`docs/reports/<yyyymmddThhmmss>_project_report.html` in which every number is
drawn from an artefact, every code finding cites `file:line`, every milestone
cites its pull request, and a reader who has never opened the repository can
say what it is, how well it is built, what it has achieved and what it should
do next. `/onboard` answers "where are we" in 600 lines; this answers "how
good is all of it" in as many lines as the evidence needs.

The report is an assessment, not a change: **it edits nothing under `src/`,
`cities/<city>/` or the living documents**, launches no run, opens no issue.
Findings go in the report; fixing them is scoped work the user decides on.
The report file lands through the session's one pull request at `/handoff`,
like any other change.

```
Project report:
- [ ] Phase 0  Ground: gate, tree, digest
- [ ] Phase 1  Collect the mechanical half (one script)
- [ ] Phase 2  Read every area, in parallel, to file:line
- [ ] Phase 3  Read every PR and the commit log to a milestone ledger
- [ ] Phase 4  Read the documents and the process layer
- [ ] Phase 5  Synthesise: findings ranked, ratings evidenced
- [ ] Phase 6  Write the HTML, lodge it, index it, verify
```

## Phase 0 — Ground

1. `python src/run/session_gate.py --digest`, then `python src/run/session_gate.py`.
   A red gate is reported in the assessment; it is not fixed here.
2. `git status --short` and `git branch --show-current`. **Uncommitted work in
   the tree is somebody's in-flight change**: read its `git diff --stat`, describe
   it in the report's "in-flight work" section, and never commit, revert or
   build on it.
3. Note `HEAD`, the branch and the date. The report is a reading of one commit.

## Phase 1 — Collect the mechanical half

One script, so the numbers are reproducible and never typed:

```bash
python .claude/skills/project-report/scripts/collect_metrics.py <scratch>/metrics
```

It writes `metrics.json` (file inventory, commit log, direct-to-main commits,
churn hotspots, the per-merge growth series of registry fields, manifest rows
and code lines, every PR with its checks and review count, every issue with
labels and ages, the CI history, the run index) plus `prs_full.md` and
`issues_full.md` for the readers in Phases 3 and 4. `--no-growth` skips the
slow series; `--no-github` runs offline. Every figure in the report's tiles and
tables comes from this file or from a check you ran; **a number you cannot
point at does not go in**.

## Phase 2 — Read every area, in parallel

Spawn one reviewer per area, each told to **read every file completely** (Read
with offsets, never a skim) and to report in a fixed shape: inventory (one line
per file), architecture, findings ranked defect / risk / smell **with
`file:line` and a failure scenario**, testability, metrics (lines, functions,
longest function, docstring coverage, TODO count) and five ratings 1–5 each
with its two strongest pieces of evidence. The areas, and what each is told to
look for on top of the project's hard constraints in `.claude/CLAUDE.md`:

| Area | Files | Look for |
|---|---|---|
| Build layer | `src/build/`, `cities/<city>/build/` | unseeded or order-dependent randomness, wall-clock use, silent fallbacks, constants that belong in the registry, city names in the framework, O(n²) over the population, functions over 150 lines |
| Run harness | `run.py`, `src/city.py`, `src/run/`, `src/setup/`, `cities/<city>/overlays/` | Windows-only assumptions, subprocess and lock handling, log readers that scale with a 50 GiB log, races between runner, observer and gate watcher, anything that could delete or rename results wrongly |
| Analysis and calibration | `src/analyse/`, `src/calibrate/` | any path that presents a run without `_run.json` as a result, any deviation against an unscorable target, folding and ×1/fraction errors, hardcoded mode lists, duplicated event parsing |
| Contract and checks | `src/registry/`, `tests/`, `config/schema/`, `cities/<city>/tests/`, `cities/<city>/registry/`, `.github/workflows/` | what each check cannot see, vacuous passes, one-city enums in the portable schemas, registry fields with no consumer, values outside their own sweep, the absence of unit tests |
| Acquisition and data | `cities/<city>/extract/`, `data/MANIFEST.*`, every `provenance_*.json`, the build reports, the validation targets, the data dictionary | typed-in extents, blank licence or source cells, observed labels on derived values, hosts outside the sandbox allowlist, the holdout's enforcement |
| MATSim extensions | `src/java/`, `src/java_signals/` | thread safety under parallel events and replanning, per-iteration memory growth, plan mutation outside sanctioned boundaries, unseeded Random, id-suffix parsing, anything that could silently teleport a leg |

Reviewers **do not modify anything and never recompile `.tools/classes`** (an
arm may be running). Six reviewers is the working number; add one when an
area passes ~6,000 lines.

## Phase 3 — Every PR and the commit log

One reviewer reads `prs_full.md` end to end and returns a **ledger with one
block per PR**: delivered (model, data, harness, documents), measured (numbers
quoted exactly), issues closed or opened, record sections added, and an
honesty line — does the body say "nothing is a result" where it should, does it
correct an earlier conclusion, and did a **later** PR correct it. Then a dated
milestone timeline (first load, first completed arm, model build complete,
first gate, first mode inside 10 %, the document restructure), statistics
(size, commits per PR, days between, documentation-only count) and a
PR-body-quality tally against the convention in `.claude/CLAUDE.md`.

From `metrics.json`, the commit log gives: totals, merges, **direct commits to
the default branch and their dates** (the rule bans them from 21 Aug 2026),
message-prefix compliance, subject lengths, the busiest day, and the churn
hotspots (which files change most, and whether they are generated).

## Phase 4 — The documents and the process layer

One reviewer reads every living and archived document (never `DECISIONS.md`
whole: its first 210 lines, its headings, its topical index and its §14 change
log), every hook, workflow, skill and settings file, and runs a relative-link
check over every Markdown file. It reports: the layering and whether the
reading-budget line counts hold; every archived file bannered frozen; the
record's numbering monotonic and every section indexed; **numbers that
disagree between two living documents, with both `file:line`s**; stale family
stamps on position pages; and every rule stated as advice that no hook or check
enforces.

## Phase 5 — Synthesise

1. **Merge the findings into one ranked table**: severity (defect / risk /
   smell), area, `file:line`, one sentence, failure scenario. Deduplicate
   across reviewers; keep the sharper citation.
2. **Ratings**: one row per area, the five dimensions, each cell carrying its
   evidence in a tooltip or footnote. Never average ratings across areas.
3. **Milestones against the goal**: for each hard requirement in
   `cities/<city>/docs/GOAL.md`, met / unmet / unmeasured, with the PR and the
   record section that decided it.
4. **Verify a sample**: re-read ten cited `file:line`s yourself before they go
   in. A reviewer's finding that does not survive the re-read is dropped, not
   softened.
5. **Recommendations**, ranked by (what it would prevent) × (how cheap), each
   naming the file to change and the check that would then catch a regression.

## Phase 6 — Write, lodge, index, verify

1. Load the `artifact-design` and `dataviz` skills before writing. The report
   is a **standalone** file: full `<!doctype html>`, `<html lang="en-AU">`,
   `<head>` with `<meta charset>` and viewport, all CSS and JS inline, fonts
   with real fallback stacks, no external resources except optionally Google
   Fonts, light and dark themes, no horizontal page scroll (tables inside
   `overflow-x:auto`). Charts are inline SVG built from the data in the file.
2. Sections, in order: masthead (date, HEAD, branch, gate result, one-paragraph
   verdict) · at-a-glance tiles · method (what was read, by whom, the rating
   rubric) · repository anatomy (inventory, growth series, churn) · code
   quality by area · the ranked findings table · testing and CI · the PR ledger
   and milestone timeline · the commit log · the issue ledger · milestones
   against the goal · the document and process layer · in-flight work seen in
   the tree · recommendations · appendix (rubric, sources, how this report was
   produced and how to reproduce it).
3. Name it `docs/reports/<yyyymmddThhmmss>_project_report.html` with the
   stamp from `date +%Y%m%dT%H%M%S` at the time of writing. Never overwrite an
   earlier report; the directory is a dated series.
4. Add a row for the new report to `docs/reports/README.md` (create it from the
   previous report's row if absent) — newest first, with the HEAD it read.
5. `python src/run/session_gate.py` must still pass; the report and the index
   are the only files this skill changes. Publish the same file as an Artifact
   as well when the harness offers one, so the user has a link, but the file
   under `docs/reports/` is the deliverable.
6. Close with the ranked recommendations in the reply, at most twelve lines,
   and the path of the report. Then stop: the change lands at `/handoff`.

## What this skill never does

- Never edits the model, the data, the registry, the board, the brief, a
  position page or the record. A finding about them goes in the report.
- Never launches or stops a run, never recompiles the toolchain.
- Never rates an area without citing the evidence, and never states a number
  it did not collect or read.
- Never reads `DECISIONS.md`, `SESSION_LOG.md` or `CONFIG_REFERENCE.md` whole.
