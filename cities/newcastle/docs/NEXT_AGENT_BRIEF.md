# Brief for the next agent

**Written:** 3 September 2026, twenty-sixth session · **Open family:** `F23-behaviour-channels` (the package on disk opens `F24` at its first launch) · **Commit:** the PR that carries the 3 Sep defect close-out (§9.141)
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session verified the 3 Sep assessment's sixteen defect issues at HEAD,
corrected seven of the proposed fixes before making them, and closed the
fourteen defects and nine of the twelve risks without a run (§9.141). No
model value moved, no target changed, no arm ran, no approval was spent.
Three issues are decisions for the user and hold the launcher.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The last arm is `aborted_20260901T165115_300it_25pct`, F23's gate arm (§9.139), now listed once. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F24 build** (§9.140) with the corridor flag repaired and the manifest at 512; `check_package.py` passed at handoff with one warn (the bike beeline factor outside its IQR sweep, §9.141). | `python tests/check_package.py` (~10 min) |
| **Three open issues carry no `awaiting-run`** — #129, #133, #134 are decisions — so the launcher and the gate refuse until the user takes them. #131 and 13 older issues carry the label. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/assessment-defects`. | `gh pr list --state open` · `gh pr checks <n>` |
| Registry 459 fields, manifest 512 files, 30 run-input sets, family `F23-behaviour-channels` in the ledger (F24 is declared at launch) — the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT; **25% runs only** (1 Sep directive) governs any launch. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too. `issues gated` is red by design until the
three decisions are taken.

## §1 The lane

**The user takes four decisions, then the first F24 arm.**

1. **#129** — the validation-target builder still EXCLUDES censored Opal
   cells from its station means (pre-registered holdout rows); the mode-target
   builder now reads `CAL.pt.censored_cell_value` (0, swept 0–25). Unify, or
   record the exclusion as the pre-registered treatment.
2. **#133** — a unit-test layer. Four stdlib checks exist and run in CI
   (`tests/check_gate_watcher.py`, `check_launch_refusal.py`,
   `check_registry_rules.py`, and the four Java probes under
   `run_signal_probes.py`); the question is whether a pytest layer follows.
3. **#134** — 238 of 254 declared sweeps have never been set by an overlay:
   run them after the gate at a stated cost, or reclassify as `held_fixed`.
4. **C2** (`params/C2_network_factors.json`, §9.141) is measured on the
   pre-16-August network; re-measuring moves detour 1.3376 → 1.3276 and the
   beeline factors, which feed the chains. Re-measure and rebuild, or keep.

Then **the first F24 arm under a fresh stated-cost approval** (~45–50 h at
25% × 300, §9.136; 25%-only stands), read at iteration 100 for all twelve
modes and for what the `awaiting-run` issues name (#93, #96, #94, #98, #108,
#107, #86, #131; §9.140, §9.141). It is the first live test of the
verdict-keyed gate watcher and of the taxi restore: taxi should read HIGHER
than F23's +76.6 % because the refused alternative now survives.

**Decisions the user must also take** (the board's *Next*): the root-cause
pick for the family after F24 — the corridor's missing CBD end (#30), the
income channel's disposition (#108), the fifth binder pass or a stated
limitation (#86); the Task Scheduler operational log (#66); the S2 tram
signal priority ([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## §2 Traps — newest first, at most ten

1. **Regenerating C2 changes the model** (§9.141): `measure_network_factors.py`
   on the current network moves the values, not just the sweeps. Do not run
   it into the package without the user's decision; the package check warns
   on the bike factor until then.
2. **The gate watcher's first live test is the F24 arm** (§9.141): read
   `_gate_stop.json`'s `breaches`, and `_gate_verdict.json` at each milestone;
   a passing milestone is logged, not stopped.
3. **The taxi level is not comparable to F23's** (#113, §9.141): every
   earlier reading was taken with refused trips amputated from plan memory.
4. **The next launch trims ~170 GiB on a daemon thread** beside the arm
   (#132): `results/raw` is at 671 GiB against the 500 GB cap; the launch no
   longer waits, but the disk is busy for the first hours.
5. **The launcher refuses behind #129, #133, #134** (requirement 10): they
   are decisions; never label them `awaiting-run` to pass the gate, and never
   pass `--allow-open-issues` without writing why in the run record.
6. **A named run overlay that is absent now raises** (#124, §9.141) — a
   mistyped `--run-config` no longer runs the base under the tag's name.
7. **`F24` is not in `run_families.json` yet** — declared at the first
   launch with `decisions_ref` 9.140, in the same change as the launch.
8. **A 25% arm's log is ~51 GiB by its gate** (§9.139): never grep
   `matsim.log`; the digest and the watcher read it incrementally now
   (§9.141), a one-off full pass on first read.
9. **Read `cause`, never `cause_detail`, for why a run died**
   ([positions/runs-and-economics](positions/runs-and-economics.md)).
10. **Heredocs with mixed quotes and backslashes break the shell**: write
    the script to the scratchpad and run the file. One explicit `gh` write
    per issue.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to
  date is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25% runs only** (user directive, 1 Sep) — the 10% pace tables are history.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py` in the session gate and `run.py`.
- **"Proceed" on a verified plan authorises the lane and its PR, never an
  arm** (user directive, 3 Sep, twenty-sixth session).
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10% each; gate every 100 iterations; stop on >20% or
  heading there; fix from the root; converge in ≤250; derive, never assume.
- **A whole-repository assessment is `/project-report`** (user directive,
  3 Sep): it reads, it changes nothing, it lodges a dated file under
  `docs/reports/` and files a finding as an issue, never as a fix.
- **Read the trend, not the level** (§9.108); every mode individually in
  every table; **one arm at a time** (#66); launch detached; never commit
  to `main`; the session's one PR opens at `/handoff`.
