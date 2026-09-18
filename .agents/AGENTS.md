# city-digital-twin — conventions

Codex project instructions. Loaded through `project_doc_fallback_filenames`
from `.agents/AGENTS.md`. All Codex support files in this repository live in
`.agents/`; keep the root free of extra documents.

Use native skills `$onboard`, `$handoff` and `$project-report`. Treat the
corresponding slash spellings in existing project documents as requests for
these skills. Read their `SKILL.md` files under `.agents/skills/` when applicable.
For a concrete task already authorised by the user, proceed within that scope.
Do not start unrelated lane work or ask again for existing authorisation.
Ask only for missing decisions that block the task, with the best recommendation
first. Use Codex's available question tool and its actual schema.

At session start, read the goal, inspect `git status`, and run
`python src/run/session_gate.py --digest`. Verify `core.hooksPath` points to
`.githooks` before committing. Use the active git identity; do not replace it
with a hardcoded identity. The full onboarding procedure applies to onboarding
or substantive model work; a tooling task does not authorise the model lane.

## What this is

An agent-based microsimulation (MATSim end to end) that reproduces how a real
city moves: twelve modes, each physically simulated on the real roads and
timetables and scored against its real-life ridership. Newcastle (NSW) is the
first city. The goal, its requirements and the loop every session runs are in
[`docs/GOAL.md`](../docs/GOAL.md) — read it first.

The simulator's documents are under [`docs/`](../docs/README.md); what describes
one city is under [`cities/<city>/docs/`](../cities/newcastle/docs/README.md) —
its front page, its targets, the reference generated from its registry and its
tables, its data requests and its frozen dossiers. The split rule (user decision,
14 September 2026, §9.171): `docs/` holds nothing whose structure is one city's.

- **[`STATUS.md`](../docs/STATUS.md)** — the board, one page: the twelve-mode
  scoreboard, where the build is, what runs, what is next. Its blocks are
  generated (`python src/analyse/build_status_board.py`); the hand-written rest
  is capped by `tests/check_doc_shape.py`. Keep it current in the same commit as
  the work it describes; never append narrative to it.
- **[`lane.json`](../docs/lane.json)** — the single next task and the decisions
  it waits on, rendered into the board's *Next* and the brief's §1
  (`src/analyse/lane.py`). A decision the user has not taken is asked once, as
  clickable options, at the end of `$onboard`; its answer is recorded, never
  re-asked.
- **[`positions/`](../docs/positions)** — the current truth per topic, one page
  each, every figure with its source. Read the page for your lane instead of the
  record; `$handoff` rewrites the pages a session touched.
- **[`DECISIONS.md`](../docs/DECISIONS.md)** — the dated, append-only record of
  every value that is not observed and every decision, with rationale and sweep.
  Frozen: never rewritten, only pointed past. Over 16,000 lines — enter through
  its topical index or a position page, never read it whole. Do not re-litigate a
  settled decision without new evidence.
- **[`reports/`](../docs/reports/README.md)** — the dated `$project-report`
  assessments and their standing reference library.
- [`README.md`](../README.md) at the repo root is the usage guide and the only
  document there. [`newcastle-lr-proposal.md`](../cities/newcastle/docs/archived/design/newcastle-lr-proposal.md)
  is the frozen origin design; read it for scenario vocabulary only.

Nothing is a result until a run's `_run.json` says `ran_to_last_iteration`. A
run stopped at a gate or by the operator is closed out with a record too, and its
reading is citable at that record's `reached_iteration` and nowhere past it; only
`ran_to_last_iteration` satisfies resume or anchors a calibrated base.

## Working style

1. **Inventory first.** Read the relevant files; state your understanding; flag
   contradictions, gaps and decisions.
2. **State the plan.** The user's concrete request authorises work within that
   scope. Get a decision only when scope or a required choice remains unresolved.
3. **Implement** the authorised task. Prefer a clear TODO to an unsupported
   assumption. Explicit approval is still required for a new multi-hour run.

## Hard constraints

- **`config/schema/` is portable; `cities/<city>/` is one city's data,
  parameters, adapters and overlays.** The framework (`src/`, `config/schema/`,
  `tests/`, `run.py`) must read identically for a city it has never seen.
  `src/city.py` is the only module that knows where a city lives; everything
  else asks it, and paths inside a city are recorded city-relative
  (`data/processed/...`). Never put a place name, a coordinate or a hand-drawn
  extent in a script — derive it from a boundary or a tag any city has, or
  declare it under `cities/<city>/registry/` or `geometry/`. (A typed-in harvest
  box once clipped 87 of 1,500 core SA1s out of the road network unnoticed for
  three phases.) The city is selected by `CITYSIM_CITY` (default `newcastle`).
- **The simulator's documents live at `docs/`, a city's under
  `cities/<city>/docs/`** (user decision, 14 September 2026, §9.171): the goal,
  the board, the brief, the lane, the positions, the record, the family ledger
  and the reports are the simulator's (`city.docs()`); the city's front page,
  its targets, its generated reference, its requests and its archives are the
  city's (`city.city_docs()`).
- **Every controllable value is declared in `cities/<city>/registry/`, never
  typed into a script.** A value whose `source` is `assumed`, `literature`,
  `measured` or `derived` carries a sweep, a `held_fixed` rule or a
  `derived_from` identity — the schema rejects anything else. Regenerate
  [`cities/<city>/docs/reference/CONFIG_REFERENCE.md`](../cities/newcastle/docs/reference/CONFIG_REFERENCE.md)
  (`python src/registry/render_docs.py`) in the same change. The build layer is
  pinned to the registry by `src/registry/check_legacy_drift.py`.
- **No invented data.** Never fabricate an observation, a count, a patronage
  figure or a coefficient. An unmeasured value is assumed or modelled, labelled
  as such in its artefact's `source` field and recorded in `DECISIONS.md` with a
  rationale and a sweep range.
- **No result before a run.** Nothing is an output of the model until a scenario
  has executed; never infer scenario results from the input package.
- **Reproducibility is a gate.** Every derived file is regenerable by a committed
  script from the immutable raw downloads and listed in
  `cities/<city>/data/MANIFEST.csv` with hash, row count, producing script,
  source, licence and retrieval date. Regenerate the manifest
  (`python src/build/build_manifest.py`) whenever a data artefact changes.
- **A number in a living document is part of the change that moved it.** If a
  change alters a count a document states — manifest rows, registry fields,
  network edges, agents — fix the document in the same commit and run
  `python tests/check_doc_currency.py --strict`. A dated record is frozen and is
  never rewritten to keep a check green; a live-state cell must equal its
  artefact today.
- **Determinism.** Everything synthetic is seeded (`20260810`). No unseeded
  randomness, wall-clock dependence or dict/set-ordering dependence in a build
  script.
- **Provenance for every acquisition.** A download lands under `data/raw/` with
  a `provenance_*.json` (source URL, retrieval timestamp, licence). Raw downloads
  are immutable; corrections happen in `cities/<city>/extract` or `src/build`.
- **Licence boundary.** OSM-derived layers are ODbL 1.0 (share-alike); the rest
  of the package is CC-BY 4.0. Keep the distinction visible in the manifest and
  in anything published.
- **Unobtained data is derived, never assumed and never marked impossible**
  (`GOAL.md` requirement 6). A sweep is the fallback only where derivation is
  genuinely impossible (today: the transfer penalty, the charging dwell, the
  SCATS offset library), with the reason stated. Never describe a derivable input
  as "handled by sweep".
- **The toolchain is pinned, and a toolchain change is a model change.**
  [`src/setup/bootstrap_toolchain.py`](../src/setup/bootstrap_toolchain.py)
  fetches the JDK, pt2matsim, Maven and the signals run stack into `.tools/`,
  pinned by sha256 in `.tools/toolchain.json`. A version change is re-run,
  re-hashed and logged in `DECISIONS.md` §14.
- **One build of the network per comparison.** pt2matsim's schedule mapping is
  not reproducible run to run (`DECISIONS.md` §3.5). Never compare scenarios
  mapped in different builds; derive per-day-type or per-variant schedules from
  the already-mapped schedule (as `build_matsim_run_inputs.py` does), never by
  re-running the mapper.
- **A scenario runs on its own mapped network** (`schedules/<S>/network.xml.gz`
  with the E1 patch re-applied by `osm:way:id`, §9.3), not on
  `networks/matsim/variants/`, which carry no mapped transit links.
- **Bulk data is not committed** (see `.gitignore`): raw downloads, GTFS,
  synthetic population and plans, large derived geometry, run outputs. The
  manifest is committed; the bytes are not.
- **Units and CRS.** EPSG:28356 (GDA94 / MGA Zone 56 — not GDA2020, which is
  EPSG:7856), metres, base year 2026. State units in every new column name.
- **Language:** Australian / Indian English spellings.

## Runs

- **No multi-hour run without a stated-cost approval from the user**, spent on
  use. **25 % sample only** for arms (user directive, 1 September 2026).
- **One arm at a time**; never recompile `.tools/classes` while one runs. The
  launcher refuses a concurrent arm, a launch with no automatic stop, a heap
  below the registry's rule, and an overlay that changes nothing the run reads.
- **No launch while an open issue in the run's lane lacks a stated measurement**
  (`GOAL.md` requirement 10; `python src/run/issue_gate.py`).
- **Never compare across a family boundary, a sample fraction or a network
  build** (`docs/run_families.json`). MATSim runs are not bit-reproducible: a
  difference is read as a band, never as a diff.
- **The 67/143 validation holdout stays shut until the end.**
- **A dead run says why it died.** `_meta.json` requires a `cause` on a `failed`
  or `aborted` run, read out of its own `matsim.log` by `src/run/run_failure.py`.
- `results/` is self-managing (§9.137): never touched by hand; stop a run with
  `run.py --stop`.

## Git

- **Naming.** The project is Newcastle, not Wickham. Wickham is one suburb and
  is legitimate in exactly three places: its own zones and stops, Newcastle
  Interchange at Wickham, and S1, the bus-shuttle scenario. Two codename
  identifiers survive and are tracked for rename — the `CITYSIM_*` environment
  prefix and the `src/java/citysim/` package. Do not add more.
- **Branches** are `<git-handle>/<short-kebab-description>`, the handle from the
  active git identity. Never `claude/*` — if the harness assigns one, rename it
  before committing.
- **Never commit to `main`.** Every change lands through a pull request that
  targets `main` only — never a stacked branch. The session's one PR opens at
  `$handoff`, which then watches it to merge and deletes the local branch.
- **Titles** follow `P<phase>: <concise plain-English summary>` (≤ ~72 chars),
  issue refs in parentheses at the end, no internal idiom and no DECISIONS
  §-refs. PR bodies: Summary / Changes / Testing / Breaking changes, neutral
  voice.
- **No attribution.** No co-author trailer, no `claude.ai/code` session link in a
  commit or PR body. Inspect both before publishing. The commit hook strips
  Claude session links but does not check co-author trailers; full enforcement
  remains tracked in #210. The PR-body scrubber is
  [`.github/workflows/strip-session-ref.yml`](../.github/workflows/strip-session-ref.yml).
- **Commit messages** state what changed in the model or the data, not which
  script ran. **Path references in prose** are written in full — never
  abbreviated with `…`, which renderers auto-link into a broken URL.
- **Data sources** follow the allowlist in
  [`.claude/settings.json`](../.claude/settings.json). A new acquisition source
  means adding its domain there and a provenance record. Codex permissions are
  enforced by the active Codex client; Claude sandbox settings do not enforce
  Codex network access.

## Checks

`python src/run/session_gate.py` runs every gate below on one line each
(`--digest` prints the session opener; the toolchain compile is skipped while an
arm runs). Run it at `$onboard` and `$handoff`, and before every commit.

| Check | Where | Needs |
|---|---|---|
| `python tests/check_manifest.py` | CI + local | committed files |
| `python -m compileall -q src tests` | CI | nothing |
| JSON validity of provenance, scenario and params files | CI | nothing |
| `python src/registry/check_hardcoding.py --strict` | CI + local | committed files |
| `python tests/check_doc_currency.py --strict` | CI + local | committed files |
| `python tests/check_doc_shape.py --strict` · `python tests/check_doc_links.py --strict` · `python src/analyse/build_status_board.py --check` | CI + local | committed files |
| `python src/analyse/lane.py --check` · `python src/analyse/report_recs.py --check` | local | committed files |
| `python src/registry/check_city.py --all` · `render_schema.py --check` | CI | nothing |
| `python tests/check_city_agnostic.py` | CI | nothing |
| `python -m pytest -q tests/unit` | CI + local | nothing |
| `python tests/check_package.py` | local only | the full package |
| `python src/analyse/build_fit_figures.py --check` | `check_package.py` + local | a run with a `_fit.json` |
| `python src/run/run_failure.py --check` | local only | `results/` |

- **The document checks take seconds; the gate takes minutes.** After each
  document edit run `python tests/check_doc_shape.py --strict`,
  `python tests/check_doc_currency.py --strict` and
  `python src/analyse/build_status_board.py --check`; run `session_gate.py`
  once, before the commit. The mechanical parts of a handoff are scripts
  (`positions.py --stamp`, `record.py --append`, `lane.py --add-*`,
  `compare_runs.py --modes`, `watch_run.py`; the table in
  [`docs/HANDOVER_CONTRACT.md`](../docs/HANDOVER_CONTRACT.md)) — a fact has
  one home, and a page never restates a number the board owns.
- **`check_hardcoding.py` is the ledger for the registry rule**: declared-but-
  unwired fields, config template literals, numeric constants in the build
  layer, coordinates in code. It is at 0 and stays at 0; an item is worked down,
  never silenced. If your change adds an item, the change is not finished.
- **`check_doc_shape.py`** keeps the living documents the shape they were
  designed to be; the rules are the framework's
  ([`tests/doc_shape.json`](../tests/doc_shape.json)): a position page is capped
  at 130 lines and 14,000 bytes, a record section a living document cites must
  exist, the board's *Last updated* is two lines. A PR cannot open while a
  document gate is red. Run the checks in `$handoff` before a PR create or edit;
  Claude `PreToolUse` hooks do not execute in Codex.
- **`check_doc_currency.py`** pins each live-state figure in `README.md`,
  `STATUS.md` and the framing documents to the artefact that decides it
  ([`cities/<city>/tests/doc_currency.json`](../cities/newcastle/tests/doc_currency.json)).
  Only live-state cells are pinned; the record is exempt. If a claim's pattern
  stops matching because you reworded a line, re-aim the claim, never delete it.
- **The front door's fit figures are drawn, not typed** —
  `src/analyse/build_fit_figures.py` from the calibrated base's run
  (`C5_calibration.json`'s `best_tag`). Regenerate them in the same change as a
  new calibrated base; never draw an error bar against a target `fit.py` marks
  unscorable.

CI runs nothing that downloads a source dataset or executes a scenario. Run
`tests/check_package.py` on a workstation before declaring a data phase complete.

## Repo map

| Path | What it holds |
|---|---|
| `README.md` | The usage guide: install, run a scenario, reproduce the package. The only document at the root. |
| `docs/` | The simulator's documents: `GOAL.md`, `STATUS.md`, `NEXT_AGENT_BRIEF.md`, `lane.json`, `positions/`, `DECISIONS.md`, `run_families.json` (the family ledger), `reports/` (with `recommendations.json`), and `HANDOVER_CONTRACT.md` (how a session opens and closes). Indexed by `docs/README.md`. |
| `config/schema/` | The portable half: what any city must supply and in what shape. No city's values live here. |
| `run.py` | The front door: run a scenario. |
| `src/city.py` | Resolves which city's inputs a run reads, and where the documents are. |
| `src/build/` · `src/run/` · `src/calibrate/` · `src/analyse/` · `src/registry/` | Layer construction, the run harness, fit and calibration, metrics / readers / the board / the run viewer, the registry resolver and its validators. |
| `src/java/citysim/` · `src/java_signals/citysim/` | The MATSim entry point (parking, fares, ride pairing, telemetry) and the signals entry point. |
| `cities/<city>/` | One city: `registry/`, `overlays/`, `extract/`, `build/`, `geometry/`, `data/` (raw + processed + `MANIFEST.csv`), `networks/`, `schedules/`, `demand/`, `params/`, `scenarios/`, `docs/` (its front page, `targets.md`, the generated `reference/`, `requests/`, `archived/`), `tests/` (its live-state claims `doc_currency.json` and package expectations). |
| `tests/` | The CI checks and `tests/unit/`; `check_package.py` for the full package. |
| `results/` | Run outputs, gitignored: `raw/` a budgeted cache, `processed/` the permanent findings. |
