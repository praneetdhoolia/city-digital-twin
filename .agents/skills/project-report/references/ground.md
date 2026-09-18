## Phase 0 — Ground

1. `python src/run/session_gate.py --digest`, then
   `python src/run/session_gate.py --quick`. The report never recompiles the
   toolchain. State that this gate skips compilation; do not claim a full gate.
   A red gate is reported in the assessment; it is not fixed here.
2. `git status --short` and `git branch --show-current`. **Uncommitted work in
   the tree is somebody's in-flight change**: read its `git diff --stat`, describe
   it in the report's "in-flight work" section, and never commit, revert or
   build on it.
3. Note `HEAD`, the branch and the date. The report is a reading of one commit.
4. Open the **recommendation ledger** `REPORT_DIR/recommendations.json`
   (`python src/analyse/report_recs.py`): every recommendation since the tenth
   report with its status and evidence, kept by `$handoff`. The audit of the
   previous report's recommendations reads it first and re-derives only what
   it does not hold. Then open the **previous report** (newest row of `REPORT_DIR/README.md`) and pull
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
python .agents/skills/project-report/scripts/collect_metrics.py      <scratch>/metrics
python .agents/skills/project-report/scripts/collect_code_metrics.py <scratch>/metrics
python .agents/skills/project-report/scripts/collect_performance.py  <scratch>/metrics
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
