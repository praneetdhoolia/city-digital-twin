# Brief for the next agent

**Written:** 7 September 2026, thirtieth session (interim — `/handoff` rewrites this) · **Open family:** `F28-the-car-waits-only-for-a-car` · **Branch:** `praneetdhoolia/history-check-and-pre-run-fixes`

**Trap, newest:** `RUN.qsim.vehicle_behavior` is GLOBAL — `wait` strands walk and taxi, which are network modes with per-person vehicles and not chain-based (§9.148); the household car constraint is car-only in `HouseholdCarDepartureHandler`. And the agent source must insert vehicles BEFORE creating the agent — MATSim 26 copies the plan elements into the agent.

**§0 at a glance, thirtieth session:** the F26 arm ran to its iteration-100 gate and was stopped by the watcher (8 modes out, §9.146); **the package on disk is F27's** (plans + 30 sets rebuilt 21:14 6 Sep, manifest 512, `check_package.py` see the board); #145 opened `awaiting-run`, every open issue carries the label; **no arm runs, no approval stands** — F27's first arm costs ~32 h at 25 % × 300 on F26's measured 384 s/it and is the first measurement of `wait` itself.
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

No arm ran. **#142 is fixed and closed, so nothing blocks a launch**: the escort
binder and the §9.60 lift pass chose a ride driver on a LICENCE alone, where the
joint and shared passes also require a household vehicle. 9,319 WEEKDAY bindings
named a driver with no car, and the seed then walked, bussed or taxied **85,993
legs the same person was declared to drive — now 0** (§9.144). The demand was
rebuilt on it, so **family F26 is open and no arm has run in it**. The ride lane
§9.143 opened is untouched and still owes the user a decision.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **Machine idle; no arm runs.** The newest reading is still F25's, at the watcher's iteration-100 gate. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F26 build** (§9.144): chains, plans and the 30 run-input sets rebuilt 6 Sep. `check_package.py` ALL CHECKS PASSED at handoff; manifest 512 files. | `python tests/check_package.py` (~10 min) |
| **This session's PR** — check whether it merged and whether the branch is gone. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| **Nothing blocks a launch.** #142 is closed; all 14 remaining open issues carry `awaiting-run`. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| Registry 466 fields, 30 run-input sets, `F26-a-driver-owns-a-car` newest in the ledger. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT. **25 % runs only.** | assume none; ask |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too. Every line should be green.

## §1 The lane

**Ride is lost downstream of the choice set, and the decision between its two
halves is still owed to the user.** F25 falsified the demand cause (§9.143): the
seeded ride share rose 31 % and the realised share did not move. F26 changed who
may be a driver but not that finding — it removed 9,319 bindings that could
never have become a ride and re-let the volume to drivers who can drive, so the
binder volume is essentially unchanged (375,007 → 375,307 WEEKDAY rows, seeded
ride share 0.0444 → 0.0448). What splits the remaining gap is unchanged from
last session, measured on `aborted_20260905T125612_300it_25pct`:

1. **Execution.** The pair rate fell **0.9817 → 0.8256 → 0.7827** across
   iterations 0 / 50 / 100, so **21.7 % of selected ride legs never pair** and
   execute as a drive or a walk, which the trips table counts as car or walk.
   The dominant miss is the TIME window and it grows monotonically —
   `miss_window` **1 → 5,339 → 7,921** — while `miss_endpoints` (5,237) and
   `miss_capacity` (2,012) stay smaller. `occupancy_from_pairings` reads
   **0.1642** against a measured 0.3503.
2. **Selection.** Selected ride legs rose 25,362 → 77,214, so the alternative IS
   offered and mostly not chosen. Indicatively — crossing two bases, so an
   indication only — ~3 pp of the 8.9 pp gap is execution and ~6 pp is
   selection, which is a scoring question.

**SUPERSEDED BY THE F26 GATE (§9.146) — read the board and the ride page; this
section is the state before the arm ran.** The gate found the declared pairs
holding (`miss_declared_absent` 719) and the loss in 12,461 ride legs with no
driver, 29,827 bound trips self-driven, and 12,317 car legs with every household
car already out. Three fixes are built with controls; F27 is open; the arm needs
your cost approval (~32 h). The paragraph below is kept for the trap it records.

**The window reading above is WRONG, and §9.145 settles it on the code.** A
declared pair faces no clock test at all (`if (!isDeclared && gap > window)`,
since §9.120), so it can never be recorded as a window miss: `miss_window` means
the declared driver was ABSENT and a substitute was found at the wrong hour. The
four buckets sum exactly to the 16,778 unpaired legs and **14,766 of them (88 %)
are that one class**. A declared driver leaves `car` only by SELECTING a seeded
plan that never held it — `GatedSubtourModeChoice` gates proposals, not memories
— and §9.144 took those from 85,993 to 0. **§9.98's window refusal stands; do not
widen either window.** `EscortCoherenceListener` is intra-household on both
passes, leaving 170,582 of 375,307 bindings (45.4 %) uncovered — measured, not
repaired, because the F26 gate's new `miss_declared_absent` decides whether it
still matters.

One measurement is now available that was not before: **F26's own
`ride_pairing.csv` at its first gate** tells you whether removing car-less
drivers moved `miss_no_candidate` (1,608 at the F25 gate) — the only part of the
pairing loss #142 could have touched. It costs nothing extra; it is a column of
the arm you were going to run anyway.

**Decisions the user must take** (the board's *Next*): the pick between execution
and selection; whether §9.98's window refusal is superseded by the new gap
median (344 min when refused, 50.0 min now); whether a fifth binder pass is
needed now the reachable volume is ~18.7 % rather than 20.13 %; a stated-cost
approval for any arm (~26–27 h at 25 % × 300, MEASURED); the Task Scheduler log
(#66); the S2 tram signal priority.

## §2 Traps — newest first, at most ten

1. **Count only what would otherwise have happened** (§9.144). A refusal counter
   added this session first read 51,436 where the honest figure was 9,555: it
   counted the Poisson HX draw of unlicensed persons, whose tours the builder
   discards anyway. It was caught only because `hx_tours_requested` fell by
   9,555 and the two figures would not reconcile. Reconcile every new counter
   against a total that already exists.
2. **`boundDriveTrips` and `boundRideTrips` are 1-BASED** (§9.144). A 0-based
   reading of them reports 386,217 violations where there are none, and the
   modes it invents look plausible.
3. **A milestone is readable only when its experienced plans decompress to the
   END** (§9.143). Three weaker signals all mean STARTED: the progress digest's
   iteration counter, the `it.N` directory, and the file's existence.
4. **`reached_iteration` is the last ENDED iteration**, from the log's markers,
   never the digest's in-flight figure.
5. **`completion`, not the record's presence, is the result gate** (§9.143).
   Only `ran_to_last_iteration` is a result, satisfies resume or anchors a
   calibrated base.
6. **Never write a registry field or a document through an unquoted shell
   heredoc**; and the Bash tool will break on a long quoted one. Write the
   script to the scratchpad with the file tool and run the file.
7. **Do not regex-edit the build layer in bulk.** A `, 'w')` substitution broke
   21 scripts. Compile each file before writing it.
8. **A build writer must pin `newline='\n'`** (§9.143). Verify against
   `git show HEAD:<path>`, not the working tree.
9. **The chains build takes about an hour** (three day types), the plans build
   about twenty minutes, and neither should be piped through a buffering filter.
10. **No level is comparable across a family boundary** — and F26 is one, on the
    demand. The board's scoreboard is F25's reading; do not difference an F26
    number against it.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to date
  is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25 % runs only** (user directive, 1 Sep).
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py`, and currently GREEN.
- **"Proceed" on a verified plan authorises the lane and its PR, never an arm**
  (user directive, 3 Sep).
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10 % each; gate every 100 iterations; stop on ≥20 %; fix
  from the root; converge in ≤250; derive, never assume.
- **A whole-repository assessment is `/project-report`** (user directive, 3 Sep).
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
