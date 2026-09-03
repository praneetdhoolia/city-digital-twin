# Brief for the next agent

**Written:** 3 September 2026, twenty-fourth session · **Open family:** `F23-behaviour-channels` (the package on disk opens `F24` at its first launch) · **Commit:** the PR that carries §9.140
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session took the user's directive — every GitHub issue fixed to closed
or `awaiting-run` before the simulator is touched again — and made it
`GOAL.md` requirement 10 with a gate the launcher enforces (§9.140). Six
issues closed on evidence (#21, #62, #63, #84, #91, #99), seven are labelled
`awaiting-run` with the measurement each needs, and none is open without the
label. Along the way: seven dead registry fields retired, the S0 detour
measured, the external interaction rate derived from the 2011 journey-to-work
flow, the input contract made city-free (census readers behind the city
adapter, byte-identical), the motorbike carve conserved per LGA, the leaf
subtour mix repaired at the seed, and the ferry's market and the choice-set
decay measured on the F23 gate outputs. Chains, plans and run inputs are
rebuilt: **the next arm opens family F24.**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The last arm is `aborted_20260901T165115_300it_25pct`, F23's gate arm (§9.139). | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F24 build**: chains, plans and the 30 run-input sets rebuilt 3 Sep; manifest 511 files; `check_package.py` passes with §9.140 in the record. | `python tests/check_package.py` (~10 min) |
| **Every open issue is labelled `awaiting-run`** (13 on 3 Sep) and the launcher refuses otherwise. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/close-open-issues`. | `gh pr list --state open` · `gh pr checks <n>` |
| Registry 457 fields, manifest 511 files, 30 run-input sets, family `F23-behaviour-channels` in the ledger (F24 is declared at launch) — the board's *State* block. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT; **25% runs only** (1 Sep directive) governs any launch. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too.

## §1 The lane

**The first F24 arm, under a fresh stated-cost approval** (~45–50 h at 25% ×
300, §9.136; 25%-only stands). Launch `python run.py --detach` with the
standing gate overlay; the runner's own watcher stops it at a gate
(§9.137/§9.139, first live firing still unobserved). Read at iteration 100:
all twelve modes (`report_mode_ridership.py --trend`), and the readings the
awaiting-run issues name — motorbike at its identity (#93), the §9.119
stand-aside log empty (#96), the ferry's near-wharf split and whether its
plan survives in memory (#94, §9.140), rail under the income channel (#98,
#108), bike's fall (#107), ride's plateau (#86).

**Decisions the user must take** (the board's *Next*): the root-cause pick
for the family after F24 — the corridor's missing CBD end (#30: floorspace-
weighted attraction vs a declared agglomeration term), the income channel's
disposition (#108), a fifth binder pass for the unbindable ride classes or a
stated limitation (#86); the Task Scheduler operational log (#66); the S2
tram signal priority ([positions/signals-and-crossings](positions/signals-and-crossings.md)).

Nothing is open without a run. A new issue opened without `awaiting-run`
blocks the launcher until it is fixed or labelled — that is the requirement,
not a nuisance.

## §2 Traps — newest first, at most ten

1. **The launcher refuses behind an unlabelled open issue** (GOAL.md
   requirement 10, §9.140): `run.py` exits before `--detach`; fix or label,
   and never pass `--allow-open-issues` without writing why in the run record.
   Where `gh` is not authenticated the gate cannot see the tracker and says so.
2. **The target LGA's carve conserves to the DECLARED identity, not to its
   summed SA1 cells** (§9.140): the cells read +1.2% (ABS perturbation); the
   builder refuses only beyond 5%. Do not "fix" the declared value to the sum.
3. **`F24` is not in `run_families.json` yet** — it is declared at the first
   launch with `decisions_ref` 9.140, in the same change as the launch. A run
   launched before that entry inherits F23 in the index and is mis-attributed.
4. **The seeded choice set is a seed** (§9.140): at iteration 100 only 22.7%
   of residents still hold a pt plan and 8.7% a bike plan. A mode absent from
   memory is not a mode the person refused — read a gate with that in mind.
5. **The fixed gate watcher has never fired live** (§9.139): at the next
   arm's iteration-100 milestone verify `_gate_stop.json` appears; if not, the
   session owns the stop (`python run.py --stop NAME --cause "..."`).
6. **A 25% arm's log is ~51 GiB by its gate** (§9.139): never grep the whole
   `matsim.log`; read `_progress.json` or a bounded byte window from EOF.
7. **Read `cause`, never `cause_detail`, for why a run died** — the reader
   quotes the first exception-looking line, benign warnings included
   ([positions/runs-and-economics](positions/runs-and-economics.md)).
8. **The board's scoreboard reads the newest ARM's newest reading** — still
   the aborted F23 arm at iteration 100 until F24 writes one; not a result.
9. **The three behaviour channels are gated, not global** (§9.138):
   `A.bike_stress.representation`, `A.parking.search_time_representation`,
   `C.income.representation` — a sweep arm toggles the field, never code.
10. **Heredocs with mixed quotes break the shell** — write a script to the
    scratchpad and run the file; two long edits were silently lost that way.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to
  date is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25% runs only** (user directive, 1 Sep) — the 10% pace tables are history.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py` in the session gate and `run.py`.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10% each; gate every 100 iterations; stop on >20% or
  heading there; fix from the root; converge in ≤250; derive, never assume.
- **Read the trend, not the level** (§9.108); every mode individually in
  every table; **one arm at a time** (#66); launch detached; never commit
  to `main`; the session's one PR opens at `/handoff`.
