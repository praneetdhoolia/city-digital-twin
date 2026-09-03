# Brief for the next agent

**Written:** 3 September 2026, twenty-fifth session · **Open family:** `F23-behaviour-channels` (the package on disk opens `F24` at its first launch) · **Commit:** the PR that carries the 3 Sep assessment
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session assessed the whole repository at commit `9c99e54` — every
tracked file by area, all 45 pull requests and 376 commits, the 65 issues,
CI, the 126 run records, the data package and the document system — and
lodged the reading as `docs/reports/20260903T134517_project_report.html`,
reproducible with the new `/project-report` skill. Fourteen defects were
confirmed at HEAD and filed as #112–#127; nine risks and gaps and three
document drifts as #128–#137. No model, data or target value changed; no
family opened; no approval was spent. The twenty-fourth session's work
(§9.140: requirement 10, the F24 package) merged as PR #111 during this one.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The last arm is `aborted_20260901T165115_300it_25pct`, F23's gate arm (§9.139). | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F24 build** (§9.140): chains, plans and the 30 run-input sets rebuilt 3 Sep; `check_package.py` passed at PR #111. | `python tests/check_package.py` (~10 min) |
| **26 issues are open without `awaiting-run`** (#112–#137, filed 3 Sep), so the launcher and the session gate refuse a launch until they are fixed or labelled (GOAL.md requirement 10). 13 older issues carry the label. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/project-report`. | `gh pr list --state open` · `gh pr checks <n>` |
| Registry 457 fields, manifest 511 files, 30 run-input sets, family `F23-behaviour-channels` in the ledger (F24 is declared at launch) — the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT; **25% runs only** (1 Sep directive) governs any launch. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too.

## §1 The lane

**Fix the assessment's defects, then launch the first F24 arm.** None of
#112–#127 needs a run, and requirement 10 refuses a launch while they are
open. In order of what each prevents:

1. **#112, the gate watcher** (`src/run/run_matsim.py:800`): it stops on the
   text `GATE:`, which the reporter also prints on a pass. The first arm to
   pass its iteration-100 gate would be recorded aborted. Key the stop on a
   verdict and add the canned-reporter test. Fix this before anything runs.
2. **#113, the taxi restore** (`TaxiFleetEngine.java:263`): re-find refused
   legs by endpoints as the ride engine does; a restore round-trip test.
3. **#114, the board's truck deviation**: pass `None` for level-only rows.
4. **#115 and #116, the two producers that cannot rebuild their layer**
   (`extract_hts.py:81`, `slice_newcastle.py:36`), with a builder-versus-
   artefact assertion in `check_package.py`.
5. **#117 and #118, the manifest's provenance join and the OSM harvest
   record**; then #119–#127 (each a one-file fix with its line cited).
6. #128–#137 are risks, gaps and document drift: label `awaiting-run` only
   what genuinely needs an arm (none does); #133 (a unit-test layer) and
   #134 (238 sweeps never run) are decisions, not fixes.

Then **the first F24 arm under a fresh stated-cost approval** (~45–50 h at
25% × 300, §9.136; 25%-only stands), read at iteration 100 for all twelve
modes and for what the `awaiting-run` issues name (#93, #96, #94, #98, #108,
#107, #86; §9.140).

**Decisions the user must take** (the board's *Next*): the root-cause pick
for the family after F24 — the corridor's missing CBD end (#30), the income
channel's disposition (#108), the fifth binder pass or a stated limitation
(#86); the sweeps-never-run disposition (#134); the Task Scheduler
operational log (#66); the S2 tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## §2 Traps — newest first, at most ten

1. **The watcher would kill a passing arm** (#112): until it is fixed, a
   gate that passes is indistinguishable in the record from one that
   breached. Read `_gate_stop.json`'s gate lines, not its existence.
2. **`run.py --stop` and `--list` die on an invalid registry** (#126):
   while anyone is mid-edit of a registry layer, the one sanctioned way to
   stop an arm is unavailable. Finish registry edits before touching a run.
3. **The next launch trims about 170 GiB synchronously** (#132):
   `results/raw` is at 671 GiB against the 500 GB cap and `trim` runs the
   reporter on each directory before deleting it. Budget hours, or trim first.
4. **The launcher refuses behind an unlabelled open issue** (requirement
   10, §9.140): 26 are open today. Fix or label; never pass
   `--allow-open-issues` without writing why in the run record.
5. **A run-config typo runs the 1 % base under the tag's name** (#124):
   a missing run overlay is silently skipped. Check `_config.json`'s
   `resolved_from` after any launch.
6. **The board's scoreboard reads the newest ARM's newest reading** — still
   the aborted F23 arm at iteration 100 until F24 writes one; not a result.
7. **`F24` is not in `run_families.json` yet** — declared at the first
   launch with `decisions_ref` 9.140, in the same change as the launch.
8. **A 25% arm's log is ~51 GiB by its gate** (§9.139, #131): never grep
   `matsim.log`; read `_progress.json` or a bounded window from EOF.
9. **Read `cause`, never `cause_detail`, for why a run died**
   ([positions/runs-and-economics](positions/runs-and-economics.md)).
10. **Bulk `gh` writes from a script are refused by the harness**; one
    explicit `gh issue create` per issue is allowed. Twenty-six took one
    response. Heredocs with mixed quotes still break the shell: write the
    script to the scratchpad and run the file.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to
  date is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25% runs only** (user directive, 1 Sep) — the 10% pace tables are history.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py` in the session gate and `run.py`.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10% each; gate every 100 iterations; stop on >20% or
  heading there; fix from the root; converge in ≤250; derive, never assume.
- **A whole-repository assessment is `/project-report`** (user directive,
  3 Sep): it reads, it changes nothing, it lodges a dated file under
  `docs/reports/` and files a finding as an issue, never as a fix.
- **Read the trend, not the level** (§9.108); every mode individually in
  every table; **one arm at a time** (#66); launch detached; never commit
  to `main`; the session's one PR opens at `/handoff`.
