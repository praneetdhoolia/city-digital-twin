# Brief for the next agent — TWO REPRODUCIBILITY FAILURES NO GATE COULD SEE, AND A FIVE-ARM CRASH THAT WAS MATSIM REFUSING ITS OWN CREATION

*Updated 30 August 2026, FIFTEENTH session (§9.93 reconstructed, §9.116–§9.119).
**The committed builder had stopped reproducing the committed demand** — a filter was
committed without its rebuild and all eight arrival gates passed over it. **The
local-only suite was FAILING while three documents said it passed.** And the
`IllegalStateException` that had killed five arms across two sessions turned out to be
**MATSim's own mode choice manufacturing a state MATSim's own mode choice refuses** —
found only after three mechanisms were argued from the code and all three refuted.
Both queued fixes (#92, #93) are applied, the demand is rebuilt (**family F14**), and
**an arm is running that has passed the point where five arms died.***

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
| **AN ARM IS RUNNING — THE MACHINE IS NOT FREE.** `results/20260830T083019_1000it_25pct`, pid 27864, was at iteration 32 of 1000 | `tail results/20260830T083019_1000it_25pct/matsim.log`; its `_meta.json`; look for a MATSim `java` process |
| Whether that arm is alive, dead, or past its iteration-100 gate | `ls results/20260830T083019_1000it_25pct/output/ITERS/` |
| **This session's PR is OPEN at handoff** and is the first item of unfinished business | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues — **#92 CLOSED, #96 OPENED this session** | `gh issue list --state open` |
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
python tests/check_package.py                      # LOCAL ONLY - RUN IT
```

**⚠ RUN `check_package.py` YOURSELF.** It is the one gate CI never runs, which makes
its status the likeliest to be stale — and it *was* stale, red for at least a session
while three documents called it green (§9.117).

**⚠ STANDING DIRECTIVES**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL.** Measured on the current arm:
   **~290–305 s/it at 25%**, so 1000 iterations is **~84 h**. ~100 s/it at 10%,
   ~30 s/it at 1%.
2. **READ THE TREND, NOT THE LEVEL** (§9.108). A level read while innovation runs is
   not the model's answer.
3. **A CAUSE MUST CARRY ITS MEASUREMENT.** Six mechanisms across two sessions have now
   been argued from plausibility and refuted — three of them this session (§9.119).
   **If a crash names no agent, make it name one before theorising.**
4. **Every mode individually in every numbers table** — never an umbrella row.
5. **ONE ARM AT A TIME** (#66). Breached briefly this session — two arms overlapped for
   ~1 min during startup; caught, stopped, and recorded.
6. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**

**⚠ DECISIONS REQUIRED**
- **Whether to let the arm run to its innovation cutoff (~84 h total).** No arm in
  F10–F14 has ever reached one, so **no post-cutoff twelve-mode level has ever been
  read by this project.**
- **Whether the next family boundary is #30 / #96 (destination placement).** §9.119
  shows destination placement manufacturing degenerate one-trip subtours; §9.103 puts
  the light rail's whole market at 1.06% of trips; §9.107 names it for walk. It cannot
  be done while an arm is up.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> Twelve modes present, **physically simulated**, monitored and scored — no teleportation.
> **<10% deviation from real life for every mode.** Unavailable data must be DERIVED.
> Gate every 100 iterations; stop on any mode past 20%; fix the cause from the root.

**Physical simulation: 12 of 12.**

**<10% per mode: not met, and still not legitimately measurable** — no arm has ever run
past its innovation cutoff, so every level ever read has been a point on a moving curve.
**Taxi reads +0.9% and truck +5.4% on its own basis**, both at shallow depth.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode trips, target-LGA residents, from the iteration's own trips
table. **THIS IS ITERATION 1 — effectively the uniform seed (§9.92), NOT the model's
answer.** It is **25%**, so it is NOT comparable with any 10% arm (§9.10, §9.12).

Arm `20260830T083019_1000it_25pct`, iteration 1 of 1000, innovation cutoff 800.
Reproduce with
`python src/analyse/report_mode_ridership.py --run results/20260830T083019_1000it_25pct --it 1`.

| # | mode | modelled % | target % | deviation | count | mean km |
|---|---|---:|---:|---:|---:|---:|
| 1 | car | 40.6211 | 58.1631 | −30.2% | 60,917 | 9.79 |
| 2 | ride | 10.6932 | 20.6000 | −48.1% | 16,036 | 8.92 |
| 3 | walk | 30.2093 | 13.4000 | +125.4% | 45,303 | 7.92 |
| 4 | bike | 7.7659 | 2.2084 | +251.7% | 11,646 | 9.81 |
| 5 | motorbike | 0.1054 | 0.2406 | −56.2% | 158 | 9.63 |
| 6 | **taxi** | **1.0009** | **0.9916** | **+0.9%** | 1,501 | 11.39 |
| 7 | bus | 7.7239 | 2.3819 | +224.3% | 11,583 | 12.02 |
| 8 | light_rail | 0.0834 | 0.6444 | −87.1% | 125 | 12.02 |
| 9 | heavy_rail | 1.7938 | 0.7737 | +131.8% | 2,690 | 12.02 |
| 10 | ferry | 0.0033 | 0.1013 | −96.7% | 5 | 12.02 |
| 11 | truck | 9.1524 | — | **+5.4% on its own ground** (§9.101) | 22,370 | — |
| 12 | freight_train | 314 | 314 | representation, not a fit | 256 | — |

The four PT submodes share one folded HTS observation, so their geometry deviations are
**not independent**. Motorbike's share will fall further: §9.115's carve correction
lowers generation by design, and that is a consistency repair, never a fit repair.

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

**Read the arm's iteration-100 gate, then 200 and 300.** §9.108 measured car, walk and
pt arriving between iterations 200 and 350 on the previous family; this is the first
chance to see whether that holds on the repaired demand, and whether **ride still
diverges now that joint binding is supply-limited rather than thinned** (§9.116).

**Do NOT repair car, walk or pt off a gate reading before the trend says they are not
converging.** Four repairs in the fourteenth session went into a transient.

After the arm, the candidate next boundary is **#30 / #96, destination placement**.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.116 — the committed builder had stopped reproducing the committed demand.** The
§9.111 filter landed in `b65d280` via PR #95 without its rebuild. Caught from the
committed build report: `candidates` 201,931 with `candidates_unservable` absent is a
report the committed builder cannot write. **All eight arrival gates passed over it** —
none compares a builder with the artefact it produced. Both fixes applied together,
all three day types rebuilt. WEEKDAY:

| | before | after |
|---|---:|---:|
| candidates | 201,931 | 146,260 |
| `candidates_unservable` | — | 55,671 |
| **bound** | **74,663** | **82,384** |
| `skipped_infeasible` | 73,258 | 35,937 |
| `thin_p` | 0.8565 | **1.0000** |
| `driver_is_the_companion` | 51,215 | 8,150 |

**§9.111's "roughly 110,000" is superseded: the measurement is 82,384.** Thinning
stopped applying, so binding is **supply-limited by servable candidates** — WEEKDAY only
(SAT 0.6216, SUN 0.5955). **#93 applied:** `B.motorbike.trip_share` 0.0036 →
**0.0024064**, `assumed` → `derived`; two observations declared and
`build_mode_targets.py` **asserts them against the acquired sources every build**.
`mode_targets_by_mode.csv` unchanged but for line endings — the carve moves generation,
not the yardstick.

**§9.117 — the local suite was red while three documents said green.** A `decisions_ref`
named **§9.93**, which had never been written, and three `consumers` claims were
semantically true but textually false. **§9.93 is reconstructed** from evidence already
committed inside the field descriptions, labelled as a reconstruction, introducing no
new number. **0 false claims remain across 193 claims over 179 fields.** The check
reports only its FIRST failure — enumerate the whole set.

**§9.119 — the five-arm crash.** Three mechanisms argued from code, all refuted: the
§9.106 refusal path (the throw is inside MATSim's strategy, the bounds are 0.0);
§9.105's `car` fallback (every restore succeeded — 48101/48101, 50705/50705,
53890/53890); §9.118's nested-subtour conversion (a rebuilt arm died identically, 918 s
against 928 s). **Measured instead: 8 plans arrived mixed, 20 went clean→mixed in one
round.** A degenerate one-trip child subtour gets a non-chain mode from
`probaForRandomSingleTripMode`; the PARENT then holds `car`+`pt`, sleeps in memory, and
kills the run when mode choice later SELECTS it. Repaired by two refusals that invent
nothing. **§9.118's nested-subtour repair is real and kept, and is AMENDED in place to
say it is not this crash's cause.**

**Offline, the committed WEEKDAY demand holds 99 mixed subtours of 1,138,887 and 0 of
the fatal single-excursion shape** — all span excursions, all `closed=false` (**#96**).

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

- **FAMILY F14 IS OPEN.** Nothing run before 30 Aug compares with anything after,
  including the two F4 arms `README.md` draws its fit figures from.
- **Never compare across sample fractions.** This arm is 25%; the previous family was 10%.
- **One arm at a time** (#66).
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No arm in F10–F14 has one.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no session links.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**.

- **Phase:** P4 calibration. Yardstick sound; demand repaired; the replanner no longer
  manufactures states it refuses; first surviving F14 arm running.
- **Machine:** BUSY.
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6, Maven 3.9.9, run-stack 201 jars.
- **Registry:** 402 fields, ledger 0.
- **`check_package.py`: ALL CHECKS PASSED** with its 2 standing warnings — verified this
  session, not asserted.
- **Two new diagnostic tools**, both under `src/java/citysim/`:
  `SubtourChainScan` (scan a plans file for mixed subtours; **takes coordDistance**, and
  exits INCONCLUSIVE rather than reporting a clean it never tested) and
  `NestedSubtourProbe` (settles `getSubtours` ordering without a run).
- A Guice `LineNumbers` warning at startup (`Unsupported class file major version 69`)
  is **cosmetic** — its bundled ASM predates the pinned JDK 25.

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **`B.ride.pairing_rule` stays `both_links`** (§9.92, confirmed §9.102).
- **The walk/bike feasibility bounds stay 0.0** (§9.106) — measured, worse.
- **`B.ride.max_passengers_per_vehicle` does not bind** — 2 refusals of 73,258, and
  still 2 after the rebuild (§9.111, §9.116).
- **The seed stays uniform** (§9.92).
- **The coherence rates stay 0.4** (§9.93) — search completeness, not fit.
- **A proposal that would leave a subtour mixed is refused, not repaired** (§9.119).
- **SCATS offsets are not adapted** (§9.88); **freight trains are not mobsim vehicles**
  (§9.70, §9.90); **the taxi fare is not a lever** (§9.91).

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

1. **AN INTERMITTENT CRASH IS A STOCHASTIC SELECTION OVER A DETERMINISTIC DEFECT**
   (§9.119). The bad state was manufactured every round and lay dormant until the
   strategy drew the subtour holding it. Five arms, two sessions, three refuted
   mechanisms. **When a crash names no subject, make it name one first.**
2. **A GATE THAT NEVER COMPARES A PRODUCER WITH ITS PRODUCT CANNOT SEE A PRODUCER THAT
   HAS STOPPED PRODUCING IT** (§9.116). Eight checks passed over a repository that could
   not rebuild its own demand.
3. **RUN THE LOCAL SUITE BEFORE BELIEVING THE BOARD ABOUT THE LOCAL SUITE** (§9.117).
4. **A CHECK THAT REPORTS ONLY ITS FIRST FAILURE HIDES THE REST** (§9.117).
5. **A TOOL CAN REPORT A GREEN IT NEVER TESTED** (§9.119). `SubtourChainScan` printed
   CLEAN off **0 subtours decomposed** — it had the wrong `getSubtours` overload for
   unrouted plans. Caught only because the summary counts were read, not the verdict.
6. **AN ESTIMATE IS NOT A MEASUREMENT** (§9.116). "Roughly 110,000" became 82,384.
7. **A RECURRING EXCEPTION IS NOT A RECURRING BUG** (§9.118). The same message had one
   cause in August 26's repair and a different one underneath it.
8. **`run_failure.py --check` DOES NOT SEE A RUN STUCK IN `running`.** It inspects
   terminal records only, and `reconcile_stale()` fires only when another run launches —
   so a killed run can sit with a dead pid, no cause, and a green check. Found this
   session and closed out by hand; **not yet fixed in the harness.**
9. **A LEVEL READ WHILE INNOVATION RUNS IS NOT THE MODEL'S ANSWER** (§9.108).
10. **SPLIT A COMPOUND CONDITION BEFORE ATTRIBUTING ANYTHING TO IT** (§9.111).
11. **NEVER READ SERVICE FROM A `transitRoute` ID** (§9.113) — count departures.
12. **A `main_mode` IS NEVER A PT SUBMODE** (§9.112).
13. **CHECK THE YARDSTICK BEFORE THE MODEL** (§9.91, §9.100, §9.101).
14. Carried: `modestats.csv` is PLANNED and the trips table is REALISED; **git-bash
    heredocs eat backslashes and break on long documents** — write Java/Markdown with a
    file tool, not a heredoc; compiling is not installing; stopping a run needs BOTH
    `Stop-ScheduledTask` and `taskkill /PID <pid> /T /F`; a `java.exe` at ~1 GB is VS
    Code's language server; **a run directory's timestamp can differ from its scheduled
    task name by a second** — glob on the run directory, not the task.

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's claims by
counterfactual microsimulation. Operational goal: a twin whose per-mode ridership is
*checked*. **Physical simulation 12 of 12.** **<10% per mode not met** and not yet
legitimately measurable — no arm has passed its innovation cutoff. **No hypothesis
tested; no scenario comparison exists.** Deliverables: 1 🟡 · 2 🟡 · 3 🟡 · 4 ⬜ · 5 🟡 · 6 🟡.

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs · P2 ✅ · P3 ✅ · **P4 🟡** · P5–P7 ⬜.

**3 · Tasks.** This session: two reproducibility failures found and repaired, both
queued fixes applied and measured, a missing record reconstructed, three false registry
claims corrected, the five-arm crash diagnosed and fixed, the local suite returned to
green, one issue closed on evidence, one opened with measurements, and the first
surviving F14 arm launched. Open: #93 (needs an arm's realised share), #96, #86, #30.

**4 · Simulator versus real life.** See **§2** — that is iteration 1, the seed. **No
valid post-cutoff arm exists.** The standing calibrated base is still the pre-repair
**F4** arm `20260821T175907_1000it_25pct` (MAE 10.65 pp), now **two families back**.
Never quote an error against a target `_fit.json` marks unscorable — the light rail's
3,417 and all six HTS mode-share rows are on that list.

**5 · Issue ledger.** Totals in §0. **#92 closed** on its measurement. **#96 opened**:
the demand's 99 mixed subtours. Commented with measured evidence: **#30** (destination
placement manufactures degenerate one-trip subtours), **#86** (binding is now
supply-limited, not thinned). #93 deliberately left open — its close condition needs an
arm's realised share. Untouched: #94, #91, #84, #82, #73, #68, #66, #63, #62, #50, #49,
#48, #21.

**6 · PR history and the next PR.** Totals in §0. This session's PR carries §9.93,
§9.116, §9.117, §9.118 (with its amendment) and §9.119 — the rebuild, the gate repairs,
the crash fix and the arm. The next PR should carry the arm's gate readings, and then
whichever root cause those readings actually name.
