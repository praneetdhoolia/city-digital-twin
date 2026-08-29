# Brief for the next agent — THE BUILDER HAD STOPPED REPRODUCING ITS OWN DEMAND, THE LOCAL SUITE WAS RED WHILE THREE DOCUMENTS SAID GREEN, AND THE FIRST F14 ARM IS UP

*Updated 30 August 2026, FIFTEENTH session (§9.93 reconstructed, §9.116, §9.117). Two
reproducibility failures were found on `main` within an hour of each other, both invisible
to every gate that CI runs. **The §9.111 candidate-pool filter had been committed without
its rebuild**, so the committed builder could not regenerate the committed demand. **And
`check_package.py` — the local-only gate the conventions name for declaring a data phase
complete — was FAILING**, against a board, a brief and a dated row all calling it green.
Both are repaired. Both queued fixes (#92, #93) are applied together, the demand, plans and
30 run-input sets are rebuilt, and **the first F14 arm is running at 25%.***

*This is a **HANDOVER, not a source of truth.** Where it disagrees with
[`STATUS.md`](../STATUS.md), [`DECISIONS.md`](../DECISIONS.md) or
[`.claude/CLAUDE.md`](../../../../.claude/CLAUDE.md), those win. The shared definitions —
trust order, the six questions, the environment gate — live in
[`docs/HANDOVER_CONTRACT.md`](../../../../docs/HANDOVER_CONTRACT.md).*

---

═══════════════════════════════════════════════════════════════════════════════
§0  VERIFY FIRST — these facts expire; re-derive them before trusting a word below
═══════════════════════════════════════════════════════════════════════════════

**Every count derived from GitHub or from `results/` lives HERE and nowhere else.**

| Fact as of this handoff | Re-derive with |
|---|---|
| **AN ARM IS RUNNING — the machine is NOT free.** `results/20260830T022430_1000it_25pct`, pid 27512 | look for a MATSim `java` process; `results/` mtimes; its `_meta.json` |
| Whether that arm is still alive, dead, or past its gate | `tail results/20260830T022430_1000it_25pct/matsim.log`; `ls .../output/ITERS/` |
| This session's PR — open or merged | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues (**#92 CLOSED this session**; #93 left open deliberately) | `gh issue list --state open` |
| Issue / PR totals | `gh issue list --state all` · `gh pr list --state all` |
| Run directories, and every dead one stating its cause | `ls -1d results/*/` · `results/INDEX.md` · `python src/run/run_failure.py --check` |
| Registry field count | `python src/registry/check_hardcoding.py --strict` |
| **NO run approval stands. None.** Approvals are spent on use | assume none; ask |

Then the environment gate — **all of it must pass, and a failure is your first work item**:

```bash
python src/setup/bootstrap_toolchain.py --verify   # compiles BOTH class trees
python tests/check_manifest.py
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
python src/run/run_failure.py --check
python src/analyse/build_fit_figures.py --check
python tests/check_city_agnostic.py                # 13/13
python tests/check_package.py                      # LOCAL ONLY - RUN IT, DO NOT TRUST THE BOARD
```

**⚠ RUN `check_package.py` YOURSELF.** It is the one gate CI never runs, which makes its
status the one most likely to be stale — and it *was* stale, for at least a session
(§9.117). It needs the full package and takes several minutes.

**⚠ STANDING DIRECTIVES**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL.** Measured: **240 s/it at 25%** on the
   F14 arm's iteration 0, ~100 s/it at 10%, ~30 s/it at 1%. A 1000-iteration arm at 25%
   is **~66 h**.
2. **READ THE TREND, NOT THE LEVEL** (§9.108). A level read while innovation runs is not
   the model's answer. Four repairs in the fourteenth session chased a transient.
3. **A CAUSE MUST CARRY ITS MEASUREMENT.** Five mechanisms were asserted and three
   committed before refutation in the fourteenth session.
4. **Every mode individually in every numbers table** — never an umbrella row.
5. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**
6. `python src/analyse/report_mode_ridership.py --run <dir> --it <n>` is the twelve-mode
   reader; `--truck-stations` scores truck on its own ground (§9.101).

**⚠ DECISIONS REQUIRED**
- **Whether to let the F14 arm run to its cutoff (~66 h total) or stop it at a gate.** No
  arm in F10–F14 has ever reached its innovation cutoff, so **no post-cutoff twelve-mode
  level has ever been read by this project.**
- **Whether the next family boundary is #30 (destination placement).** §9.103 localises
  the light rail's deficit to a corridor market of 1.06% of all trips, and names
  destination placement rather than mode choice. It is also walk's diagnosis (§9.107).
  It cannot be done while an arm is up (#66).

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> Twelve modes present, **physically simulated**, monitored and scored — no teleportation.
> **<10% deviation from real life for every mode.** Unavailable data must be DERIVED.
> Gate every 100 iterations; stop on any mode past 20%; fix the cause from the root.

**Physical simulation: 12 of 12.**

**<10% per mode: not met**, and **not yet legitimately measurable** — no arm has ever run
past its innovation cutoff, so every level ever read has been a point on a moving curve.
Truck is inside on its own correct basis (+5.4%).

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode trips, target-LGA residents, from the iteration's own trips
table. **THIS IS ITERATION 0 — THE UNIFORM SEED (§9.92), NOT THE MODEL'S ANSWER.** It is
also **25%**, so it is NOT comparable with any 10% arm (§9.10, §9.12).

Arm `20260830T022430_1000it_25pct`, iteration 0 of 1000, innovation cutoff 800.

| # | mode | modelled % | target % | deviation | count | mean km |
|---|---|---:|---:|---:|---:|---:|
| 1 | car | 41.8522 | 58.1631 | −28.0% | 62,646 | 9.54 |
| 2 | ride | 10.7092 | 20.6000 | −48.0% | 16,030 | 8.76 |
| 3 | walk | 29.9230 | 13.4000 | +123.3% | 44,790 | 7.87 |
| 4 | bike | 7.8539 | 2.2084 | +255.6% | 11,756 | 9.79 |
| 5 | motorbike | 0.1089 | 0.2406 | −54.7% | 163 | 9.01 |
| 6 | taxi | 0.0000 | 0.9916 | −100.0% | 0 | — |
| 7 | bus | 7.6775 | 2.3819 | +222.3% | 11,492 | 12.00 |
| 8 | light_rail | 0.0895 | 0.6444 | −86.1% | 134 | 12.00 |
| 9 | heavy_rail | 1.7824 | 0.7737 | +130.4% | 2,668 | 12.00 |
| 10 | ferry | 0.0033 | 0.1013 | −96.7% | 5 | 12.00 |
| 11 | truck | 9.1280 | — | **+5.4% on its own ground** | 22,370 | — |
| 12 | freight_train | 314 | 314 | representation, not a fit | 256 | — |

The four PT submodes share one folded HTS observation; their geometry deviations are not
independent. **Taxi at 0.0000 is expected at iteration 0** — it is not a seeded mode and
appeared by iteration 100 on the previous arm.

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

**Read the F14 arm's iteration-100 gate**, then its 200 and 300. §9.108 measured car, walk
and pt arriving between iterations 200 and 350 on the previous family; this arm is the
first chance to see whether that holds on the repaired demand, and whether **ride still
diverges now that joint binding is supply-limited rather than thinned**.

**Do NOT repair car, walk or pt off a gate reading before the trend says they are not
converging.**

After the arm, the candidate next boundary is **#30, destination placement** — named by
§9.103 for the light rail and by §9.107 for walk.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.116 — the committed builder had stopped reproducing the committed demand.** The
§9.111 filter was committed in `b65d280` via PR #95 without its rebuild. Caught from the
committed build report: `candidates` 201,931 with `candidates_unservable` absent is a
report the committed builder cannot write. **All eight arrival gates passed over it** —
none compares a builder with the artefact it produced.

Both queued fixes applied together, all three day types rebuilt. **Measured, WEEKDAY:**

| | before | after |
|---|---:|---:|
| candidates | 201,931 | 146,260 |
| `candidates_unservable` | — | 55,671 |
| **bound** | **74,663** | **82,384** |
| `skipped_infeasible` | 73,258 | 35,937 |
| `thin_p` | 0.8565 | **1.0000** |
| `driver_is_the_companion` | 51,215 | 8,150 |

**§9.111's "roughly 110,000" was wrong; the measurement is 82,384.** Thinning stopped
applying altogether, so **joint binding is now supply-limited by servable candidates** —
a different regime, and a WEEKDAY property only (SAT 0.6216, SUN 0.5955).

**#93 applied:** `B.motorbike.trip_share` 0.0036 → **0.0024064**, `assumed` → `derived`.
Two observations declared (`CAL.mode_split.vehicle_driver_level`,
`.motorbike_driver_journey_share`) and `build_mode_targets.py` now **asserts them against
the acquired sources on every build**. `mode_targets_by_mode.csv` unchanged but for line
endings — **the carve moves generation, not the yardstick, and motorbike's share goes
DOWN.** It is a consistency repair; do not sell it as a fit repair.

**§9.117 — the local suite was red while three documents said green.** Two failures:
a `decisions_ref` naming §9.93, which had never been written; and three `consumers` claims
that were semantically true and textually false. **§9.93 is reconstructed** from evidence
already committed inside the two field descriptions, labelled as such, introducing no new
number. Consumers repaired on both sides; **0 false claims across 193 claims over 179
fields.** The check reports only its FIRST failure — enumerate the whole set.

**The F14 arm is launched and verified past `PersonPrepareForSim`** per #70.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

- **FAMILY F14 IS OPEN.** Nothing run before 30 Aug compares with anything after,
  including the two F4 arms `README.md` draws its fit figures from.
- **Never compare across sample fractions.** This arm is 25%; the previous was 10%.
- **One arm at a time** (#66). No probe while an arm is up.
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No arm in F10–F14 has one.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no session links.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**.

- **Phase:** P4 calibration. Yardstick sound; demand repaired; first F14 arm running.
- **Machine:** BUSY.
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6, Maven 3.9.9, run-stack 201 jars. Two Java
  files gained comments this session and were recompiled clean.
- **Registry:** 402 fields, ledger 0.
- **`check_package.py`: ALL CHECKS PASSED** with its 2 standing warnings — verified this
  session, not asserted.
- A Guice `LineNumbers` warning at startup (`Unsupported class file major version 69`) is
  **cosmetic** — its bundled ASM predates the pinned JDK 25, it decorates stack traces
  only, and it is logged once.

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **`B.ride.pairing_rule` stays `both_links`** (§9.92, confirmed §9.102).
- **The walk/bike feasibility bounds stay 0.0** (§9.106) — measured, worse.
- **`B.ride.max_passengers_per_vehicle` does not bind** (§9.111) — 2 refusals of 73,258,
  and still 2 after the rebuild.
- **The seed stays uniform** (§9.92).
- **The coherence rates stay 0.4** (§9.93) — search completeness, not fit.
- **SCATS offsets are not adapted** (§9.88); **freight trains are not mobsim vehicles**
  (§9.70, §9.90); **the taxi fare is not a lever** (§9.91).

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

1. **A GATE THAT NEVER COMPARES A PRODUCER WITH ITS PRODUCT CANNOT SEE A PRODUCER THAT HAS
   STOPPED PRODUCING IT** (§9.116). Eight checks passed over a repository that could not
   rebuild its own demand.
2. **RUN THE LOCAL SUITE BEFORE BELIEVING THE BOARD ABOUT THE LOCAL SUITE** (§9.117). It
   is the one gate a session can skip silently, so its status is the likeliest to be stale.
3. **A CHECK THAT REPORTS ONLY ITS FIRST FAILURE HIDES THE REST** (§9.117). Fixing two
   revealed a third; enumerate the whole set in one pass.
4. **AN ESTIMATE IS NOT A MEASUREMENT** (§9.116). "Roughly 110,000" became 82,384, because
   the estimate assumed a thinning rate that the fix itself removed.
5. **AN EXPLANATION IS NOT EVIDENCE, HOWEVER WELL IT FITS.** Five times in the fourteenth
   session; three reached committed entries before refutation.
6. **A LEVEL READ WHILE INNOVATION RUNS IS NOT THE MODEL'S ANSWER** (§9.108).
7. **SPLIT A COMPOUND CONDITION BEFORE ATTRIBUTING ANYTHING TO IT** (§9.111).
8. **NEVER READ SERVICE FROM A `transitRoute` ID** (§9.113) — count departures.
9. **A `main_mode` IS NEVER A PT SUBMODE** (§9.112) — the submode comes from the legs table.
10. **CHECK THE YARDSTICK BEFORE THE MODEL** (§9.91, §9.100, §9.101).
11. Carried: `modestats.csv` is PLANNED and the trips table is REALISED; git-bash heredocs
    break on long documents (write them with a file tool); compiling is not installing;
    stopping a run needs BOTH `Stop-ScheduledTask` and `taskkill /PID <pid> /T /F`; a
    `java.exe` at ~0.5 GB is VS Code's language server.

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's claims by
counterfactual microsimulation. Operational goal: a twin whose per-mode ridership is
*checked*. **Physical simulation 12 of 12.** **<10% per mode not met**, and not yet
legitimately measurable — no arm has ever passed its innovation cutoff. **No hypothesis
tested; no scenario comparison exists.** Deliverables: 1 🟡 · 2 🟡 · 3 🟡 · 4 ⬜ · 5 🟡 · 6 🟡.

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs · P2 ✅ · P3 ✅ · **P4 🟡** · P5–P7 ⬜.

**3 · Tasks.** This session: two reproducibility failures found and repaired, both queued
fixes applied and measured, one missing record reconstructed, three false registry claims
corrected, the local suite returned to green, and the first F14 arm launched and verified.
Open: #93 (awaits an arm's realised share), #94, #86, and the arm itself.

**4 · Simulator versus real life.** See **§2** — but that is the SEED. **No valid
post-cutoff arm exists.** The standing calibrated base is still the pre-repair **F4** arm
`20260821T175907_1000it_25pct` (MAE 10.65 pp), now **two families back**. Never quote an
error against a target `_fit.json` marks unscorable — the light rail's 3,417 and all six
HTS mode-share rows are on that list.

**5 · Issue ledger.** Totals in §0. **#92 closed this session on its measurement.** #93
left open deliberately: its close condition needs an arm's realised share. Untouched:
#94, #91, #86, #84, #82, #73, #68, #66, #63, #62, #50, #49, #48, #30, #21.

**6 · PR history and the next PR.** Totals in §0. This session's PR carries §9.93, §9.116
and §9.117 — the rebuild, the gate repairs and the arm launch. The next PR should carry
the F14 arm's gate readings, and then whichever root cause those readings actually name.
