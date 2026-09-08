# Brief for the next agent

**Written:** 8 September 2026, thirty-sixth session · **Open family:** `F31-the-car-router-reads-only-cars` · **Commit:** see `git log -1 origin/main` after this session's PR merges; the branch is `praneetdhoolia/the-tuner-can-run-and-the-score-matches-the-goal`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

**NO ARM RAN THIS SESSION. The scoreboard is unchanged.** What changed is the
INSTRUMENT. The calibration loop had never once executed — its objective was a
MEAN over five FOLDED survey categories in percentage points while GOAL
requirement 7 is a MAXIMUM over twelve UNFOLDED modes in relative per cent, it
handed registry keys to a raw MATSim `--set`, and its movable set was **5**
fields. It is now the goal's own maximum, computed by calling the board's own
reader, with **21** movable fields reaching ride, taxi and bike. **And then it
refused to start**: iteration 100 cannot resolve the goal band, measured within
six separate runs. That refusal is the session's most important finding.

## §0 Verify first - facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **The machine is IDLE.** No arm is running; nothing was launched this session. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The newest citable reading is F31's iteration-100 gate**, citable there and nowhere past it. **No arm has passed 100 since F4.** | `python src/analyse/report_mode_ridership.py --run aborted_20260908T100009_300it_25pct --it 100` |
| **NO APPROVAL STANDS.** None was sought or spent this session. | `python src/analyse/arm_cost.py --run-config f29_gate_25pct` for the next quote |
| **The issue gate is RED on FIVE issues** in its UNSCOPED view - #49, #50, #155 (standing directives, an operator decision) and #164, #165 (this session's own non-run defects). None of the five is a run question. A run whose overlay declares a lane is gated only on that lane. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **This session's PR** carries the whole close-out; #159 is closed. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| Registry **489** fields, **512** manifest files (**264 CC-BY / 233 ODbL** + 15 bespoke, undetermined 0). | `python src/registry/render_docs.py --check` · `python tests/check_manifest.py` |
| **`.tools/classes` IS COMPILED AND GREEN** (86 class files, newest 21:12:04, sources 20:47:40). | `python src/run/session_gate.py` (toolchain line) |
| **The package on disk is unchanged** - no data artefact was rebuilt. | `python tests/check_package.py` (~10 min) |

Then: `python src/run/session_gate.py`.

## §1 The lane

**Recompiling is DONE. The lane is the ASC contraction test — and it is blocked
by the reading point, which must be settled first.**

1. **THE READING POINT, and nothing tunes until it moves** (§9.158). Between
   iteration 80 and 100 of the SAME run, nothing changed, the objective drifts
   **0.272–0.418 pp** on all SIX 25 % arms that ever reached 100 — **upward on
   every one**, so systematic movement toward relaxation, not seed scatter — and
   the worst scored mode moves **15.72–24.88 points**, with heavy rail (6/6),
   bike (4/6) and taxi (3/6) each clearing the WHOLE 10 % acceptance band inside
   that twenty-iteration window. `CAL.search.reading_drift_pct` = 24.88
   (`measured`), `CAL.search.convergence_delta` is derived from it, and
   `calibrate.py --execute` REFUSES rather than search on noise. **The remedy is
   to change the READING — read deeper than 100, or average a window of
   iterations — not the rule.** Re-measure with
   `python src/analyse/measure_reading_stability.py --all --from 80 --to 100`.
   **This is the honest first move.**
2. **THE ASC CONTRACTION TEST, built and NOT run** (~15 h for two rounds; it
   opens NO family of its own, because a `C.asc.*` change is a run-inputs rebuild
   off the already-mapped schedule). `src/calibrate/asc_fixed_point.py` PROPOSES
   a damped log-ratio step per mode against reference car — the contraction a
   logit's share equation implies, the same object as the Berry (1994) inversion.
   Round 1, already proposed off the F31 gate: bike **−0.5121**, bus **−0.2301**,
   ferry **+0.6713**, light rail **+0.4143**, all inside their declared sweeps
   and under the `CAL.asc.max_step_utils` 1.5 refusal bound. **The observable is
   whether |Δasc| SHRINKS between round 1 and round 2, not whether the shares
   move**: contraction means the residual is a TASTE and constants will close it;
   no contraction means it is a MECHANISM and no constant ever will. Either
   answer ends a question eleven families have not answered. **Blocked by item 1
   unless the reading point changes.**
3. **The PT routing failure is DIAGNOSED and its remedy is undecided** (§9.158).
   Of **2,553,357** pt routing requests on the F31 arm, **33.4 %** get no transit
   route at all and **40.6 %** of the answered take the network walk — **60.5 %
   of every request comes back as a walk** — because
   `(marginalUtilityOfTraveling − performing)/3600` makes **one second walking
   cost 1.0400 seconds riding**. Radius, search parameters and schedule integrity
   are each REFUTED with numbers. `RUN.transit_router.direct_walk_factor` is a
   declared field with a sweep to 2.0 (1.5 → 27.3 % walk-answered, 2.0 → 21.7 %,
   3.0 → 16.2 %), and moving it is a family boundary and a FIDELITY decision.
   **It must not be picked to land a mode share.**

**Decisions the user must take:** whether the reading point moves (item 1);
**which of #49, #50 and #155 is stated, split or closed** — the gate is RED on
them, none is a run question, and closing someone's standing product directives
is not a close-out's call (#164 and #165 are this session's own non-run defects
and block the unscoped gate the same way); whether the **real Newcastle corridor
operates transit signal priority** (`A.lightrail.tsp_enabled` is
`source: assumed`, requirement 6 says derive it, and it is settled on evidence
about the corridor, never on light rail's −47.2 %); whether the two 336.4 GiB
arms in the store are reclaimed; whether the pt-walk teleportation is filed; #66.

## §2 Traps - newest first, each with what it cost

1. **`.tools/classes` NO LONGER MATCHES ANY EARLIER ARM'S BYTECODE.** The
   controler was recompiled this session, so nothing on disk from an earlier arm
   was produced by it. A hand comparison against an old run's outputs is a
   cross-boundary comparison whatever the file names suggest (§3.5, §9.158).
2. **A search that stops on a delta smaller than its own reading's drift is
   reading noise.** The old `convergence_delta` was 0.25 pp against a measured
   within-run drift of 0.272–0.418 pp on every arm — it would have stopped, or
   failed to stop, on nothing (§9.158).
3. **A folded objective can improve while the goal gets worse.** Heavy rail and
   light rail sat in ONE folded survey cell with OPPOSITE signs. Never score a
   twelve-mode goal on a five-category instrument (§9.158).
4. **A field the loop cannot reach is not a field the loop should ignore.**
   `rebuild_stage` classified by a consumer's BASENAME and silently dropped every
   field carrying a `matsim_param` binding, which reaches the emitted config on
   every run. The movable set went 5 → 21 on that one correction (§9.158).
5. **Do not compare across a family boundary, however tempting the story.** F28
   and F31 are separated by three boundaries (§9.157, §3.5).
6. **`bootstrap_toolchain.py --verify` RECOMPILES.** It reads as a read-only word
   and is not; run under a live probe on 8 Sep it rewrote both class trees
   beneath the JVM and cost that probe its only purpose (§9.156).
7. **Quote the band, never the point.** The probe's recurring 216.0 s was 17 %
   optimistic while the long-arm top anchor of 259.6 s was right to 0.5 %
   (§9.156, §9.157).
8. **A counter on an unscoped Guice provider counts nothing** — "log the first 3"
   wrote 19,469 lines and `% 100000` never fired once (§9.156). The new
   teleport counters are singleton-scoped for exactly this reason (§9.158).
9. **Verify an assessment finding before fixing it.** Tram priority IS the S2b
   intervention; switching it on would have destroyed the comparison the study
   exists to make (§9.156).
10. **A run is a result only if `_run.json` says `ran_to_last_iteration`.** F31's
    arm says `stopped_at_gate`: citable at iteration 100 and nowhere past it
    (§9.143).

## §3 Standing directives and approvals

- **NO APPROVAL STANDS, and none was sought or spent this session.** The
  authorisation behind this work covered the lane and the pull request, not
  machine time. Quote the next arm as a RANGE from `arm_cost.py`.
- **25 % runs only** (user directive, 1 September 2026).
- **One arm at a time**; never recompile `.tools/classes` under one.
- **No launch while an open issue in the RUN'S LANE is not awaiting a STATED
  measurement** (GOAL requirement 10). A label is not evidence: an issue must
  carry `AWAITING-RUN: <the measurement>` with real content. **Five issues fail
  that today in the unscoped view — #49, #50, #155 and this session's own #164,
  #165 — and none of the five is a run question.**
  `--allow-open-issues` needs `--override-reason`, is ledgered and is counted.
- **§8.5 still binds on `C.asc.rail`, `C.asc.walk` and `C.asc.car_passenger`.**
  Three constants were opened this session with the departure logged at §9.158;
  these three stay FROZEN, each with a per-mode reason on its own `held_fixed`
  rule. Do not open one without logging its own departure first.
- **The 67/143 holdout stays shut until the end** (§12).
- **Never commit to `main`**; the session's PR opens at `/handoff`.
- The record is never rewritten; superseded text is corrected on the position
  page with a §14 row, never by editing the dated section.
