# city-digital-twin — project conventions

Repo-level guidance for any Claude Code session working in this repository.
This file lives in `.claude/`, which Claude Code loads automatically. The repo
root holds exactly one document: [`README.md`](../README.md), the usage guide.

## What this is

A **city digital twin**: an agent-based microsimulation (MATSim end to end) that
reproduces how a real city moves — twelve modes, each physically simulated on the
real roads and timetables and scored against its real-life ridership — so that
questions nobody can answer by observation alone can be put to it. Newcastle (NSW)
is the first city. The goal, its hard requirements and the loop that drives every
session are in **[`GOAL.md`](../cities/newcastle/docs/GOAL.md)** — read it first.

- **[`STATUS.md`](../cities/newcastle/docs/STATUS.md) is the board — ONE page**: the
  twelve-mode scoreboard, where the build is, what runs, what is next. Its state
  blocks are generated (`python src/analyse/build_status_board.py`); the
  hand-written rest is capped by `tests/check_doc_shape.py`. **Keep it current in
  the same commit/PR as the work it describes**, and never append narrative to it.
- **[`positions/`](../cities/newcastle/docs/positions) hold the current truth per
  topic** (ride, signals, sampling, seed, taxi, walk/bike, PT yardsticks, …), one
  page each, every figure with its source. Read the position page for your lane
  instead of the record. `/handoff` rewrites the pages a session touched.
- **[`DECISIONS.md`](../cities/newcastle/docs/DECISIONS.md) is the dated record** of
  every value that is not observed and every decision, with its rationale and
  sweep. It is append-only and frozen: never rewritten, only pointed past. **Consult
  it through its topical index or a position page, never by reading it whole** — it
  is over 13,000 lines. Do not re-litigate a settled decision without new evidence.
- [`README.md`](../README.md) is the **usage guide**: install, run a scenario with
  `run.py`, reproduce the data package. It is the only document at the repo root;
  every other one is under [`docs/`](../docs/README.md).
- [`docs/archived/design/newcastle-lr-proposal.md`](../cities/newcastle/docs/archived/design/newcastle-lr-proposal.md)
  is the **frozen origin design** — the light-rail counterfactual that started the
  study and is now its first application; read it for scenario vocabulary only.
- Stage: the board's phase table says where the build is. Nothing is a result until
  a run completes with `_run.json`, and no run since family F4 has reached its gate.

## Working style (apply to every change)

1. **Inventory first.** Read the relevant files; state your understanding; flag
   contradictions, gaps and decisions.
2. **Plan, then get sign-off.** Propose the change and **wait for approval** before
   writing files.
3. **Implement.** Only after approval. Prefer clear TODOs over speculative
   implementation.

## Hard constraints (do not violate)

- **`config/schema/` is portable; `cities/<city>/` is one city's everything.**
  **Nothing city-specific belongs outside `cities/<city>/`** - not a value, not an
  acquisition adapter, not a coordinate, not a data file. The framework
  (`src/`, `config/schema/`, `tests/`, `run.py`) must read identically for a city it
  has never seen. `src/city.py` is the ONLY module that knows where a city lives;
  everything else asks it. Paths inside a city are recorded CITY-RELATIVE
  (`data/processed/...`), so one manifest row means the same thing in every city.
  That split is the point of the naming: a field key like `A.road.speed_default` is
  generic, but 50 km/h residential, 16.96 AUD/h and a 0.50 bicycle ownership rate are
  Newcastle's. The city is selected by `CITYSIM_CITY` (default `newcastle`) — an env prefix that is itself a suburb name awaiting rename; see *Naming* under Conventions. **Never
  put a place name, a coordinate or a hand-drawn extent in a script** — derive it from
  a boundary or a tag that any city also has, and if it genuinely must be declared, it
  belongs under `cities/<city>/registry/`. A typed-in rectangle cannot be wrong in a
  way anyone notices: the OSM harvest box in `cities/<city>/extract/overpass.py` clipped **87 of
  1,500 core SA1s** out of the road network and nobody saw it for three phases.
- **Every controllable value is declared in `cities/<city>/registry/`, not typed into a
  script.** A value whose `source` is `assumed`, `literature`, `measured` or `derived`
  must carry a sweep, a `held_fixed` rule or a `derived_from` identity — the schema
  rejects anything else, and `check_package.py` tests it. Regenerate
  [`docs/reference/CONFIG_REFERENCE.md`](../cities/newcastle/docs/reference/CONFIG_REFERENCE.md)
  (`python src/registry/render_docs.py`) in the same change. The build layer is not yet
  migrated and is pinned to the registry by `src/registry/check_legacy_drift.py`: if you
  change a constant there, change the registry field with it.
- **No invented data.** Never fabricate an observation, a count, a patronage figure or a
  coefficient. If a value is not measured it is **assumed or modelled**, and it must be
  labelled as such in the `source` field of its artefact **and** recorded in
  `DECISIONS.md` with a rationale and a sweep range. An unsupported number presented as
  observed is the one failure this project cannot absorb.
- **No result before a run.** Nothing in this repo is an output of the model until a
  scenario has actually been executed. Do not write, summarise or infer scenario results
  from the input package.
- **Reproducibility is a gate, not an aspiration.** Every derived file must be
  regenerable by a committed script from the immutable raw downloads, and must be listed
  in [`data/MANIFEST.csv`](../cities/newcastle/data/MANIFEST.csv) with its hash, row count, producing script,
  source, licence and retrieval date. Regenerate the manifest
  (`python src/build/build_manifest.py`) whenever a data artefact changes.
- **A number in a living document is part of the change that moved it.** If your
  change alters a count a document states — manifest rows, registry fields, network
  edges, agents, assembled sets — fix that document **in the same commit**, and run
  `python tests/check_doc_currency.py --strict`. It is not a courtesy: the front-door
  `README.md` spent nine days and three phases advertising a 376-row manifest against
  489 on disk, a 210-field registry against 356, a road network 7,070 edges short, and
  a warning that the OSM harvest still had to be run after it had been run. Every one
  of those was correct when written, and none was wrong in a way a reader could see.
  **The distinction the check is built on: a DATED RECORD is frozen and must never be
  rewritten to keep a check green; a LIVE-STATE CELL must equal its artefact today.**
- **Determinism.** Everything synthetic is seeded (`20260810`). Do not introduce
  unseeded randomness, wall-clock dependence or dict/set-ordering dependence into a build
  script.
- **Provenance for every acquisition.** A new download lands under `data/raw/` with a
  `provenance_*.json` recording source URL, retrieval timestamp and licence. Raw
  downloads are **immutable** — never edit one in place; corrections happen in
  `cities/<city>/extract` / `src/build`.
- **Licence boundary.** OSM-derived layers are **ODbL 1.0 (share-alike)**; the rest of
  the package is CC-BY 4.0. Keep the distinction visible in the manifest and in anything
  published; do not merge an OSM-derived column into a CC-BY artefact without noting it.
- **Unobtained data is derived, never assumed and never marked impossible**
  (`GOAL.md` requirement 6). Where a value is disclosed, the exact official value is
  used; where it is not, it is researched and derived — SCATS as its published
  algorithm (§9.88), rail and tram on disclosed boardings (§9.130), licence rates
  from the published count (§9.131). A sweep is the fallback only where derivation
  is genuinely impossible (today: the transfer penalty, the charging dwell, the
  SCATS offset library), and then the reason is stated and the value is never
  quietly pinned. Do not describe a derivable input as "handled by sweep".
- **The toolchain is pinned, and a toolchain change is a model change.** The JDK,
  pt2matsim, Maven and the MATSim signals run stack are fetched by [`src/setup/bootstrap_toolchain.py`](../src/setup/bootstrap_toolchain.py)
  into `.tools/` (gitignored) and pinned by sha256 in `.tools/toolchain.json`. Changing a
  version means re-running, re-hashing and logging it in `DECISIONS.md` §14 — a different
  jar can move a result.
- **One build of the network per comparison.** pt2matsim's schedule mapping is not
  reproducible run to run (`DECISIONS.md` §3.5): ~18% of route link sequences differ
  between identical builds, while stop-to-link assignment is stable. Never compare a
  scenario mapped in one build against a scenario mapped in another. **Anything that
  needs a per-day-type or per-variant schedule must derive it from the already-mapped
  schedule** (as `build_matsim_run_inputs.py` does, by filtering `transitRoute` ids),
  never by re-running the mapper.
- **A scenario runs on its own mapped network, not on `networks/matsim/variants/`.**
  The variant networks are patched over the *base* network, which carries no mapped
  transit links; they are a reference artefact showing the E1 deltas. The runnable
  network is the scenario's own `schedules/<S>/network.xml.gz` with the E1 patch
  re-applied by `osm:way:id` (`DECISIONS.md` §9.3).
- **Bulk data is not committed.** See [`.gitignore`](../.gitignore) — raw downloads, GTFS
  bundles, synthetic population/plans, large derived geometry and run outputs are
  regenerable and stay out of git. The manifest is committed; the bytes are not.
- **Units and CRS.** EPSG:28356 (**GDA94** / MGA Zone 56 — GDA2020 is EPSG:7856; the
  label was wrong repo-wide and is corrected in `DECISIONS.md` §2.6, the projection
  itself is unchanged), metres, base year 2026. State
  units in every new column name or data-dictionary entry.
- **Language:** Australian / Indian English spellings throughout.

## Conventions

- **Naming: the project is Newcastle, not Wickham.** The modelled city is the
  **Newcastle (NSW) region** — five LGAs, 1,500 core SA1s. **Wickham is one
  suburb of it**, and the name is legitimate in exactly three places: the
  suburb's own zones and stops, **Newcastle Interchange at Wickham** (the
  transfer `beta_transfer_penalty_min` prices), and **S1, the bus-shuttle
  scenario** that starts there. Anywhere else it is a stale project codename —
  the repo and the framework are `city-digital-twin` (renamed from
  the earlier Newcastle-specific repository name, 24 Aug 2026) and the city registry is `newcastle`.
  Naming the whole project after one suburb also contradicts the hard constraint
  directly below: **no place name belongs in the framework**, only in
  `cities/<city>/`. Two codename identifiers survive in code and are
  tracked for rename — the `CITYSIM_*` environment prefix and the
  `src/java/citysim/` package (see the open naming issue). Do not add more, and
  do not rename a genuine Wickham-the-suburb reference.
- **Branch naming.** `<git-handle>/<short-kebab-description>`, with `<git-handle>` derived
  from the active git identity (the `…+<handle>@users.noreply.github.com` email, else
  `git config user.name`). **Never `claude/*`** — if the harness assigns one, this rule
  wins: `git branch -m …` before committing. A SessionStart hook surfaces this each
  session.
- **NEVER commit directly to `main` — every change, including a docs-only
  close-out, lands via a pull request** (project rule, 21 Aug 2026; it
  supersedes the earlier "docs-only close-outs land directly on `main`"
  convention). Work on `<git-handle>/<kebab>` branches and merge through a
  PR, with no exception for size or urgency. The repository's root commit
  (`ba95e7a`) is the single structural exception — a root cannot arrive by
  PR. Direct commits made before this rule stay in history as they are
  (decision, 21 Aug 2026 — do not rewrite `main`).
- **The session's PR is opened at `/handoff`, not when a piece of work
  finishes** (project rule, 21 Aug 2026). During a session, work accumulates
  as commits on the session branch; `/handoff` closes the session out and
  opens ONE pull request carrying it. After opening the PR, the agent
  **arms a watch for the merge**: when the PR merges and the remote branch
  is deleted, the agent deletes the local branch — **only then is the
  handoff complete**. If the session ends before the merge, the open PR is
  the next session's first item of unfinished business (`/onboard` surfaces
  it).
- **Pull requests target `main` only — never another work branch.** A PR is
  opened when the work is ready to merge into `main`, not before, and never
  stacked on an unmerged branch: merging a stacked PR lands it on its *base
  branch*, not `main` (measured 20 Aug 2026 — five of six stacked PRs never
  reached `main` until PR #56 carried the union across). Sequentially
  dependent work stays as commits on one branch until the prior PR merges,
  or ships in the same PR. **Issue and PR titles follow one scheme**:
  `P<phase>: <concise plain-English summary>` (≤~72 chars), task numbers or
  issue cross-refs in parens at the end — never internal idiom ("Directive:", "Audit …:", "handover:", "board:", "Tooling:") and never
  DECISIONS §-refs in a title. PR bodies follow conventional large-project
  GitHub style (Summary / Changes / Testing / Breaking changes; neutral
  voice — the internal idiom of `DECISIONS.md` stays out of GitHub
  artefacts).
- **Attribution.** No Claude co-author trailer or PR attribution
  (`attribution.commit`/`pr` empty, `includeCoAuthoredBy: false` in
  [`.claude/settings.json`](settings.json)); a SessionStart hook pins the git
  identity. **No `claude.ai/code` session link** in commit messages or PR bodies either.
  `attribution.sessionUrl: false` is set, but it does **not** suppress the session-link
  footer the cloud platform injects into a PR body — so this is enforced
  deterministically across four layers, not by that setting alone:
  1. [`.githooks/commit-msg`](../.githooks/commit-msg) strips the session link /
     `Claude-Session:` trailer from every commit (activated each session via
     `core.hooksPath`, set in the SessionStart hook because an ephemeral container
     doesn't track `.git/hooks`);
  2. [`.claude/hooks/block-session-ref-in-pr.sh`](hooks/block-session-ref-in-pr.sh)
     (`PreToolUse`) denies `create`/`update_pull_request` MCP calls whose title/body carry
     the link;
  3. [`.claude/hooks/block-session-ref-in-gh-pr.sh`](hooks/block-session-ref-in-gh-pr.sh)
     (`PreToolUse`) denies `gh pr create`/`gh pr edit` commands carrying it (the `gh` CLI
     path);
  4. [`.github/workflows/strip-session-ref.yml`](../.github/workflows/strip-session-ref.yml)
     scrubs the link from a PR **body** server-side — the only layer that catches a body
     injected by the cloud **platform** (outside the agent's tool loop, and not in git
     history, so layers 1–3 structurally cannot see it). It is a scrub-after-creation.
- **Network access** is sandboxed to the data sources this project actually uses
  (ABS, TfNSW Open Data, Overpass, Copernicus, GitHub) — see `sandbox.network` in
  `.claude/settings.json`. Adding a source means adding its domain there **and** a
  provenance record.
- **Path references in prose.** Never abbreviate a file path with `…`/`...` (e.g.
  `data/.../A1_road_edges.csv`). Renderers auto-link it into a literal, broken URL. Write
  the full real path — `data/processed/network/A1_road_edges.csv`.
- **Commit messages** state what changed in the *model or the data*, not which script ran.

## Checks

| Check | Where | Needs |
|---|---|---|
| `python tests/check_manifest.py` | CI (`.github/workflows/test.yml`) + local | committed files only |
| `python -m compileall -q src tests` | CI | nothing |
| JSON validity of provenance / scenario / params files | CI | nothing |
| `python src/registry/check_hardcoding.py --strict` | **CI** + local, before every commit | committed files only |
| `python tests/check_doc_currency.py --strict` | **CI** + local, before every commit | committed files only |
| `python tests/check_doc_shape.py --strict` · `python src/analyse/build_status_board.py --check` | **CI** + local, before every commit | committed files only (the results-derived board blocks are skipped without `results/`) |
| `python src/run/session_gate.py` (every gate above, one line each; `--digest` for the session opener) | local, at `/onboard` and `/handoff` | skips the toolchain compile while an arm runs |
| `python src/registry/check_city.py --all` · `render_schema.py --check` | CI | nothing |
| `python tests/check_city_agnostic.py` | CI | nothing |
| `python tests/check_package.py` | **local only** | the full ~2.3 GiB package |
| `python src/analyse/build_fit_figures.py --check` | `check_package.py` + local | a run with a `_fit.json` |
| `python src/run/run_failure.py --check` | **local only** | `results/` |

**`check_hardcoding.py` is the ledger for the rule above it: every value declared,
nothing decided in a script.** It reports declared-but-unwired fields, config
template literals, numeric constants in the build layer, and coordinates typed
into code. **It is at 0, `--strict` gates CI, and it stays at 0** — an item is
worked down, never silenced. **If your change adds an item, the change is not
finished.**

**`check_doc_shape.py` keeps the living documents the shape they were designed
to be**: the board's hand-written lines are capped and its generated blocks
required, the brief is capped and stamped with the family it was written for,
new `DECISIONS.md` sections arrive in order and under a cap with an index row,
every figure on a position page carries its source, and a frozen document says
so in its first lines. The rules are city-owned
([`cities/<city>/tests/doc_shape.json`](../cities/newcastle/tests/doc_shape.json)).
A pull request cannot open while either document gate is red
([`.claude/hooks/gate-pr-on-docs.sh`](hooks/gate-pr-on-docs.sh)).

**`check_doc_currency.py` is the same refusal pointed at prose: a number written
into a living document is a claim about an artefact, and it must still be true.**
It pins each live-state figure in `README.md` and `STATUS.md` to the artefact that
decides it — the manifest, the registry, a zone layer, a build report — and fails
when the two disagree. The claims are city-owned
([`cities/<city>/tests/doc_currency.json`](../cities/newcastle/tests/doc_currency.json));
the harness names no city, document or number.

**A dead run must say why it died.** `_meta.json` requires a `cause` on any
`failed` or `aborted` run, and `src/run/run_failure.py` reads it out of that run's
own `matsim.log` — the terminating exception with its `Caused by` chain, quoted,
never composed. A record that says only `failed, rc=1` is a directory nobody can
rule out, and three of them reached a later session unable to explain themselves.
`build_run_index.py` prints every cause in `results/INDEX.md`.

**The front door's numbers are drawn, not typed.** `README.md` shows the base
model's fit against observation as figures generated by
`src/analyse/build_fit_figures.py` from the run the calibrated base was written
from (`C5_calibration.json`'s `best_tag`) — the same run the calibration report
covers. **Regenerate the figures in the same change as a new calibrated base**,
and never draw an error bar against a target `fit.py` marked unscorable: the
patronage observation is a pre-pandemic vintage against a 2026 base, and the
difference between the two is not a fit statistic.

**Only LIVE-STATE cells are pinned; the record is deliberately exempt.** A dated
`DECISIONS.md` §14 row saying *"manifest 436"* is history and must never be
rewritten to keep a check green — that would be the reproducibility rule running
backwards. If your change moves an artefact, the document that describes it moves
in the same commit; if a claim's pattern stops matching because you reworded the
line, re-aim the claim rather than deleting it.

CI deliberately runs nothing that downloads a source dataset or executes a scenario:
those depend on ABS/TfNSW/Overpass availability and on compute, not on the diff. Run
`tests/check_package.py` on a workstation before declaring a data phase complete.

## Repo map

| Path | What it holds |
|------|---------------|
| `README.md` | **The only document at the repo root.** Usage guide: install, run a scenario, reproduce the package. |
| `.claude/CLAUDE.md` | This file — conventions and hard constraints. Loaded automatically each session. |
| `cities/<city>/docs/GOAL.md` | **What the city's twin is for** — the hard requirements, the gate loop, the monitoring rule. Read first. |
| `cities/<city>/docs/STATUS.md` | **That city's board, one page** — scoreboard, phase state, runs, next action; generated blocks + a capped hand-written rest. Read at session start; keep current. |
| `cities/<city>/docs/positions/` | **The current truth per topic**, one page each, every figure sourced. Read the page for your lane; `/handoff` rewrites the pages a session touched. |
| `cities/<city>/docs/DECISIONS.md` | The frozen, append-only record: every assumed/modelled value + rationale + sweep, every decision (don't re-litigate). **Enter through its topical index or a position page** — never read it whole. |
| `docs/` | **The FRAMEWORK's documentation only**, indexed by [`docs/README.md`](../docs/README.md). A city's own study documents live under `cities/<city>/docs/`. |
| `config/schema/` | **The portable half.** What any city must supply and in what shape: the field and registry schemas, the overlay schema and the output schemas. **No city's values live here.** |
| `run.py` | The front door: run a scenario with defaults or custom arguments. |
| `src/city.py` | Resolves which city's inputs a run reads. The only module that knows. |
| `cities/<city>/` | **ONE CITY - everything specific to it.** Selected by `CITYSIM_CITY` (default `newcastle`). |
| `cities/<city>/docs/` | That city's study: `GOAL.md`, `STATUS.md` (board), `NEXT_AGENT_BRIEF.md`, `positions/` (current truth per topic), `DECISIONS.md` (the record), `run_families.json` (the ledger), the GENERATED `reference/`, and `archived/` — everything frozen, bannered as such. |
| `cities/<city>/build/` | Builders that encode that city's intervention, corridor, history and statistical geography. |
| `cities/<city>/geometry/` | Declared extents that were once typed into scripts. |
| `cities/<city>/registry/` | That city's declared values, with units, provenance and a sweep or held-fixed rule. |
| `cities/<city>/overlays/` | `scenarios/`, `day/` and `runs/` value overlays, in resolution order. |
| `cities/<city>/extract/` | That city's acquisition adapters — for Newcastle, ABS / TfNSW / Overpass. **Jurisdiction-specific by nature.** |
| `cities/<city>/data/raw/` | Immutable downloads + `provenance_*.json`. Never edited in place. |
| `cities/<city>/data/processed/` | Clipped and derived layers: zones, census, hts, observed, network, corridor, landuse, validation. |
| `cities/<city>/data/MANIFEST.csv` / `.json` | Per-file hash, rows, producing script, source, licence, retrieval date. **Paths are city-relative.** |
| `cities/<city>/networks/osm/` | Raw Overpass extracts (roads, footways, rail, parking, POI, buildings). |
| `cities/<city>/schedules/` | GTFS era feeds + `scenarios/S0..S6` variants. |
| `cities/<city>/demand/` | Synthetic `population/` (B1) and `plans/` (B2 tours per day type + `matsim/` plans). Seeded, deterministic. |
| `cities/<city>/params/` | C1 behavioural parameters + the sensitivity sweep grid. |
| `cities/<city>/scenarios/` | E1 scenario configs, one JSON per scenario, plus `matsim/` — the assembled run inputs, one directory per scenario x day type. |
| `src/build/` | Layer construction (the reproduction pipeline, in README order). |
| `src/registry/` | The registry resolver, its validators, the legacy-drift check and the docs generator. |
| `src/run/`, `src/calibrate/`, `src/analyse/` | P3+ execution, calibration and analysis. |
| `results/` | Run outputs. Gitignored — nothing here is committed. |
| `tests/` | `check_manifest.py` (CI, committed subset) and `check_package.py` (local, full package). |
