# Brief for the next agent

**Written:** 8 September 2026, thirty-seventh session · **Open family:** `F31-the-car-router-reads-only-cars` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/the-gate-clears-and-the-reading-averages-a-window`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**NO ARM RAN. The scoreboard is unchanged.** Two 1 % smoke probes ran and are
readings of nothing. The session's largest finding is a NEGATIVE one: the
windowed reading that §9.158 proposed as the repair for the reading point was
built, declared and measured, and it is **WORSE** than the point reading it
replaces — because the movement it was meant to average away is a monotone
TREND, not noise. **The reading point is a convergence problem.** Alongside
that, the two issues blocking the gate were closed by doing the work, and #167's
fix was built to the point where the one thing still missing is named exactly.

## §0 Verify first - facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **The machine is IDLE.** No arm ran; two 1 % probes did, and neither is a reading. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The newest READING is still F31's iteration-100 gate**, citable there and nowhere past it. The two newer directories are smoke probes. **No arm has passed 100 since F4.** | `python src/analyse/report_mode_ridership.py --run aborted_20260908T100009_300it_25pct --it 100` |
| **AN ARM IS APPROVED AND UNSPENT**: 300 iterations at 25 %, ceiling **32 h**, overlay `depth_convergence_25pct`, held at the operator's direction until this record existed. Confirm before spending it - an approval that crosses a session should be re-stated, not assumed. | `python src/analyse/arm_cost.py --run-config depth_convergence_25pct` |
| **The issue gate is GREEN UNSCOPED** - 20 open, every one awaiting a STATED measurement, 0 blocking. First time in its existence. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **#164 and #165 are CLOSED; #167 is open and awaits a mechanism, not a run.** | `gh issue view 167` |
| Registry **494** fields, **512** manifest files (**279 CC-BY / 218 ODbL** + 15 bespoke, undetermined 0). | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| **The store is at 130.7 GiB of 500 (26.1 %)**, down from 93.4 %. | `python src/run/results_store.py --report` |
| **The package on disk: only the run-input sets were reassembled**, off the already-mapped schedule (§3.5 not engaged). | `python tests/check_package.py` (~10 min) |

Then: `python src/run/session_gate.py`.

## §1 The lane

**Depth. Everything else waits on one arm that is read past iteration 100.**

1. **THE DEPTH ARM, approved and not launched** (§9.159, #163).
   `depth_convergence_25pct`: 300 iterations at 25 %, innovation off at 240 so
   the post-cutoff window straddles 250. `arm_cost.py` quotes **22.2 h** against
   a measured spread of **22.0–31.7 h**; the approved ceiling is **32 h**. It
   carries a SCOPED DEPARTURE — `RUN.gate.interval_iterations = 0` — because the
   gate watcher killing every arm at its first gate is precisely why nothing has
   been read past iteration **104** in eleven families, and an arm that exists to
   find where the reading settles cannot be stopped at the point under test. The
   departure is justified on the overlay and recorded at §9.159; the loop stays
   in force everywhere else and **no parameter may be tuned on anything this arm
   reads**. It answers two questions at once: where each mode's series flattens,
   and requirement 8, unmeasured since F4.
2. **WHY THE WINDOW IS NOT THE ANSWER, so nobody rebuilds it** (§9.159). Over
   the same six arms: heavy rail **41.46** points against the point reading's
   24.88, bike 4/6 arms → **6/6**, four modes past the whole 10 % band instead of
   three. Every scored mode's series over it.40–it.100 is monotone without a
   reversal (car 59.78 → 66.94, walk 14.55 → 9.76, heavy rail 27,948 → 19,140),
   and a mean over a monotone series is its centre. The field
   (`CAL.gate.reading_window_iterations`) stays declared and says so itself.
3. **#167: the last hop onto a platform** (§9.159). The routing half is SOLVED —
   the raptor's intermodal branch coexists with the mode mapping and teleports
   fall **520,385 → 6** — and the mobsim then refuses the landing link, because
   **675 of 4,123 stop facilities (16.4 %)** sit on a link walk cannot use (382
   pt/rail/train, 199 artificial `stopFacilityLink`s, 62 road links omitting
   walk, 36 rail). `accessEgressModeToLink` dies at `PersonPrepareForSim` on 40
   agents — a DIFFERENT failure from the `ClassCastException` §9.54 recorded. It
   ships at `beeline`; the parameter set and its four derived fields stay ready.
4. **The ASC contraction test, still built and not run** (§9.158, ~15 h, opens no
   family). Round 1 proposed off the F31 gate: bike **−0.5121**, bus **−0.2301**,
   ferry **+0.6713**, light rail **+0.4143**. Blocked by the reading point, which
   the depth arm is what unblocks.

**Decisions the user must take:** whether the approved depth arm launches; how
the last hop onto a platform is made (#167 — neither stock MATSim mechanism does
it in this scenario); whether the **real Newcastle corridor operates transit
signal priority** (`A.lightrail.tsp_enabled` is `source: assumed`, requirement 6
says derive it, and it is settled on evidence about the corridor, never on light
rail's −47.2 %); #66's Task Scheduler log.

## §2 Traps - newest first, each with what it cost

1. **AVERAGING REMOVES NOISE, NOT TREND — and this model's movement is trend.**
   The windowed reading was built on the assumption that iteration-100 drift was
   scatter. It is not: every mode's series runs one way without a reversal, and
   the window made the worst mode's drift nearly double. Check the SHAPE of a
   series before proposing a statistic for it (§9.159).
2. **A CONTENT PASS WRITTEN AS A REGEX WILL BE WRONG, PROBABLY TWICE.** An
   attribute-name pattern missed `linkIdRef="45339"`; a bare token match then
   flagged seat counts as link ids; and `signal_groups.xml` hides a link id
   INSIDE a composite (`NLR_SIG_01.45339`). Three false readings before the right
   test — an identifier in a slot that NAMES the network (§9.159, #165).
3. **A PROBE THAT "STARTS" HAS NOT PASSED.** The intermodal probe started, the
   raptor accepted both switches, and the teleport count collapsed — and then the
   mobsim threw four seconds later. Read the run to its end, and read the
   teleport table, not the exit code (§9.159, #167).
4. **BUILDING ONE SCENARIO REWRITES THE WHOLE RUN-INPUTS REPORT.**
   `build_matsim_run_inputs.py --scenarios S2 --day-types WEEKDAY` left
   `_run_inputs_report.json` holding one scenario of thirty. Rebuild all of them
   before the manifest (§9.159).
5. **`.tools/classes` NO LONGER MATCHES ANY ARM BEFORE 8 SEPTEMBER.** A hand
   comparison against an old run's outputs is a cross-boundary comparison
   whatever the file names suggest (§3.5, §9.158).
6. **Do not compare across a family boundary, however tempting the story.** F28
   and F31 are separated by three (§9.157, §3.5).
7. **`bootstrap_toolchain.py --verify` RECOMPILES.** It reads as a read-only word
   and is not (§9.156).
8. **Quote the band, never the point** (§9.156, §9.157).
9. **A run is a result only if `_run.json` says `ran_to_last_iteration`.** F31's
   arm says `stopped_at_gate`: citable at iteration 100 and nowhere past it
   (§9.143).

## §3 Standing directives and approvals

- **ONE APPROVAL STANDS AND IS UNSPENT**: the depth arm, 300 iterations at 25 %,
  ceiling **32 h** (user, 8 September 2026, on `arm_cost.py`'s quoted range). It
  was held for this record. **An approval that crosses a session should be
  re-stated before it is spent, not assumed.**
- **25 % runs only** (user directive, 1 September 2026) — for ARMS. A structural
  smoke probe whose whole output is a yes or a no may run at 1 %, states that it
  may in its overlay, and may not be read for any share, count or fit (§9.159).
- **One arm at a time**; never recompile `.tools/classes` under one.
- **No launch while an open issue in the RUN'S LANE is not awaiting a STATED
  measurement** (GOAL requirement 10). The unscoped gate is GREEN — keep it that
  way by fixing a new defect or stating its measurement, not by labelling it.
- **§8.5 binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`.** Three
  constants were opened at §9.158 with the departure logged; these three stay
  FROZEN. Do not open one without logging its own departure first.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
