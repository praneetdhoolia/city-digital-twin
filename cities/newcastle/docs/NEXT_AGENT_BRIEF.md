# Brief for the next agent

**Written:** 5 September 2026, twenty-eighth session · **Open family:** `F25-ride-reaches-plan-memory` · **Commit:** `23f195d` on `praneetdhoolia/stopped-runs-carry-their-record`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

Two arms ran and both were read. **F25 falsified the demand cause for ride**:
three repairs put 60,273 + 33,832 more bound trips into plan memory and removed
17,740 impossible bookings, the seeded ride share rose 31 %, and the realised
share did not move. The ride ceiling is downstream of the choice set. Also
built: a run that ends at a defined boundary now closes itself out, so a gate
stop is citable instead of an orphan.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The last is `aborted_20260905T125612_300it_25pct`, F25's gate arm, stopped by the watcher at iteration 100. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F25 build** (§9.143): chains, plans and the 30 run-input sets rebuilt 5 Sep. `check_package.py` ALL CHECKS PASSED at handoff. | `python tests/check_package.py` (~10 min) |
| **This session's PR** — check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| **#142 BLOCKS THE NEXT LAUNCH** and is meant to: it is fixable without a run, so requirement 10 refuses an arm until it is done. Every other open issue is `awaiting-run`. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry 466 fields, 30 run-input sets, `F25-ride-reaches-plan-memory` newest in the ledger. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT. **25 % runs only.** | assume none; ask |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too. Every line should be green.

## §1 The lane

**First, #142 — it blocks every launch and needs no run.** An escort binding is
created for **5,426 licence holders whose household owns no vehicle** (4.9 % of
escort drivers); the joint and shared passes bind none, because they test
`cav` and the escort pass tests only a licence. Those escorts are real travel
but not car-passenger travel, so they should not generate a `ride` binding at
all — which also explains the 85,993 non-car legs seeded onto serving trips and
part of the mirror class of 4,460. The repair is in the escort pass in
`src/build/build_activity_chains.py`; it changes the demand, so it opens a
family boundary and needs a rebuild. Settle the `car_available` vs
`household_vehicles > 0` question for all four passes while there.

**Then: ride is lost downstream of the choice set. Find out which half.** F25 settles
that it is not the demand and not plan memory. The arm's own
`output/ride_pairing.csv` splits what remains:

1. **Execution.** The pair rate fell **0.9817 → 0.8256 → 0.7827** across
   iterations 0 / 50 / 100, so at the gate **21.7 % of selected ride legs never
   pair** and execute as a drive or a walk, which the trips table counts as car
   or walk. The dominant miss is the TIME window and it grows monotonically —
   `miss_window` **1 → 5,339 → 7,921** — while `miss_endpoints` (5,237) and
   `miss_capacity` (2,012) stay smaller. `occupancy_from_pairings` reads
   **0.1642** against a measured 0.3503.
2. **Selection.** Selected ride legs rose 25,362 → 77,214, so the alternative IS
   being offered and mostly not chosen. Indicatively — crossing two bases, so an
   indication only — ~3 pp of the 8.9 pp gap is execution and ~6 pp is
   selection, which is a scoring question.

**The root cause under both is that MATSim has no joint replanning**:
`TimeAllocationMutator` moves the two members of a declared pair independently
at `RUN.replanning.time_mutation_range_s` = 1800 s, which is why the gap opens
and why `B.ride.bound_pairing_window_min` was derived as 2× it. Widening a
window treats the symptom; `EscortCoherenceListener` already re-proposes the
coherent state at 0.4. **This is the decision the next session owes the user.**

**Decisions the user must take** (the board's *Next*): the pick between
execution and selection; whether §9.98's window refusal is superseded by the new
gap median; whether a car-less server may serve; whether a fifth binder pass is
needed now the reachable volume is ~18.7 % rather than 20.13 %; a stated-cost
approval for any arm (~26–27 h at 25 % × 300, MEASURED); the Task Scheduler log
(#66); the S2 tram signal priority.

## §2 Traps — newest first, at most ten

1. **A milestone is readable only when its experienced plans decompress to the
   END** (§9.143). Three weaker signals were tried this session and every one
   means STARTED: the progress digest's iteration counter, the `it.N`
   directory, and the file's existence. Cost: the F24 gate reading, taken at
   milestone 90 because the arm was stopped mid-iteration-100. The runner's own
   watcher already had this right — it retries the reporter until it succeeds.
2. **`reached_iteration` is the last ENDED iteration**, from the log's markers,
   never the digest's in-flight figure — a record that says otherwise sends a
   reader to a milestone holding nothing.
3. **`completion`, not the record's presence, is the result gate** (§9.143).
   Only `ran_to_last_iteration` is a result, satisfies resume or anchors a
   calibrated base. A record written before the field reads as that value.
4. **Never write a registry field or a document through an unquoted shell
   heredoc.** Backticked mode names are executed and silently deleted; it
   happened this session and was caught only by reading the field back. Write
   the script to the scratchpad and run the file.
5. **Do not regex-edit the build layer in bulk.** A `, 'w')` substitution broke
   21 scripts this session. Compile each file before writing it.
6. **A build writer must pin `newline='\\n'`** (§9.143). Windows text mode makes
   the same script emit different bytes, and the manifest then disagrees with
   the blob git commits — invisible locally, fatal in CI. Verify against
   `git show HEAD:<path>`, not the working tree.
7. **The chains build takes about an hour** and never pipe its output through a
   buffering filter.
8. **Reading pairing or ride share off a 1 % smoke is refused** (§9.128,
   §9.129): the flow-capacity artefact and broken pairs.
9. **The taxi level is not comparable across #113** (§9.141), and no level is
   comparable across a family boundary.
10. **Read `cause`, never `cause_detail`,** for why a run died.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to date
  is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25 % runs only** (user directive, 1 Sep).
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py`.
- **"Proceed" on a verified plan authorises the lane and its PR, never an arm**
  (user directive, 3 Sep).
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10 % each; gate every 100 iterations; stop on ≥20 %; fix
  from the root; converge in ≤250; derive, never assume.
- **A whole-repository assessment is `/project-report`** (user directive, 3 Sep).
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
