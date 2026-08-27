# Brief for the next agent — THE GATE WAS READ ON THE WRONG QUANTITY; THE RIDE GAP IS A DEMAND CEILING

*Updated 27 August 2026, TENTH session (§9.83) — a measurement session. **No run was
launched, no model or data value changed, no parameter moved.** What it produced is
the quantity the gate should have been read on all along, the first clean
same-basis comparison of the three gate-loop arms, and the located cause of the
residual: the synthetic demand cannot supply the vehicle-passenger share the model
is scored against.*

*This is a **HANDOVER, not a source of truth.** Where it disagrees with
[`STATUS.md`](../STATUS.md), [`DECISIONS.md`](../DECISIONS.md) or
[`.claude/CLAUDE.md`](../../../../.claude/CLAUDE.md), those win. The shared
definitions — trust order, the six questions, the environment gate — live in
[`docs/HANDOVER_CONTRACT.md`](../../../../docs/HANDOVER_CONTRACT.md).*

---

═══════════════════════════════════════════════════════════════════════════════
§0  VERIFY FIRST — these facts expire; re-derive them before trusting a word below
═══════════════════════════════════════════════════════════════════════════════

**Every line in this block was true when written and may be false now.** Run the
command; believe the output. **Every count derived from GitHub or from `results/`
lives HERE and nowhere else** — later sections point at this table rather than
restating a number.

| Fact as of this handoff | Re-derive with |
|---|---|
| **This session's PR was OPEN at handoff.** If still open, merging it and deleting the branch both sides is the first item of unfinished business | `gh pr list --state open` |
| 13 open issues: #86 #84 #82 #73 #68 #66 #63 #62 #50 #49 #48 #30 #21 | `gh issue list --state open` |
| 54 filed · 41 closed · 13 open; 30 PRs merged, 2 closed unmerged, 0 open | `gh issue list --state all` · `gh pr list --state all` |
| **Machine FREE — no run in progress.** The F8 arm was stopped 27 Aug 13:02 | look for a MATSim `java` process; check `results/` mtimes |
| 58 run directories, 20 of them `aborted_*`, every one stating its cause | `ls -1d results/*/` · the *Why the dead runs died* table in `results/INDEX.md` |
| Registry **357** fields | `python src/registry/check_hardcoding.py --strict` |
| **NO run approval stands. None.** Approvals are spent on use | assume none; ask |

Then the environment gate — **all of it must pass, and a failure is your first work
item, not a footnote**:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~2 min, compiles BOTH class trees
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
python src/run/run_failure.py --check              # every dead run says WHY
python src/analyse/build_fit_figures.py --check    # the front door draws the current base
python tests/check_city_agnostic.py                # 13/13
```

**⚠ STANDING DIRECTIVES:**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL — none is standing.** The F8 arm
   paced **257.89 s/it** median at 25%, outside the declared [217, 253] band; a
   1000-iteration arm is therefore ~71 h, and reaching iteration 200 alone is ~14 h.
1a. **LAUNCH with `python run.py --detach ...`**; a launch counts only once
   `matsim.log` is past `PersonPrepareForSim`.
1b. **NEVER run two arms concurrently** — #66 records that a machine-level stall hits
   both at the same wall-clock time. This also means **no probe while an arm is up.**
2. **The prime goal: all forms of ridership as close to real life as possible ON
   THEIR OWN; no hardcoding, no biasing, no workarounds; every issue logged.**
3. **Every mode individually in every numbers table** — never an umbrella row.
4. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**
5. **Never hand-name a run**; `_run.json` stays the only result gate.
6. **A number in `README.md` or `STATUS.md` is a claim about an artefact** — fix it in
   the same commit and prove it with `check_doc_currency.py --strict`.
7. **NEVER STATE AN ERROR AGAINST AN UNSCORABLE TARGET** (#84). Read `_fit.json`'s
   `unscorable` list first. The light rail's boardings are a **level**, not an error.
8. **READ THE GATE ON `<n>.trips.csv.gz`, NEVER ON `modestats.csv`** (§9.83, NEW —
   see §8 trap 1). Use `python src/analyse/measure_iteration_modes.py --run <dir> --it <n>`.

**⚠ DECISIONS REQUIRED:**
- **Approve the next arm**, and at what iteration count. ~14 h buys iteration 200;
  ~71 h buys 1000. **Nothing is standing.**
- **How far to widen `B.activity.escort_binding_nonhh_scope`** (§9.60) — the declared,
  swept lever on the demand ceiling (#86). Currently `same_zone`.
- **Whether non-escort companion travel should be generated at all** (#86). §9.55
  calls it "the unobserved non-household-lift share". **No rate may be invented.**
- `E.replication.n_replications` — seed floor ≤0.11 pp/mode at n=2 (§9.64); still open.
- **Warm-restart validity** — a warm-completed arm: valid arm, or diagnostic? (§9.76)
- **#84: what is the intervention's patronage legitimately checked against?**

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> **A digital twin of any city, traffic-wise ... whether that scaling actually
> predicts the correct ridership per mode must be CHECKED, not assumed. Every
> form of transport should be IN ACTION physically.**

Plus the standing gate-loop directive: *run → gate at iteration 200 → stop →
diagnose → fix the cause → relaunch*, with **<10% deviation per mode** as the bar,
and **no workarounds, no hardcoding, no biasing — real-life-derived factors only.**

"In action" is **COMPLETE**. "Checked" now has a *measured* answer, and it is
**5 of 5 scored categories failing the 10% bar**. The loop has fired three times;
cycles 1 and 2 each found a real cause and repaired it, and both repairs measurably
improved the model without moving a parameter. Cycle 3's arm was stopped before its
gate on instruction.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually, on the basis that scores
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode TRIPS, Newcastle LGA residents, from each arm's
per-iteration `<n>.trips.csv.gz` — events-derived, so realised. **Iteration 150**,
the deepest snapshot all three arms hold. Reproduce with
`python src/analyse/measure_iteration_modes.py --run results/<arm> --it 150`.

### Scored against observation (`fit.py`'s own folds applied)

| survey category | observed | F6 unfixed | F7 (§9.81) | **F8 (§9.82)** | F8 error |
|---|---:|---:|---:|---:|---:|
| Other (`bike+taxi`) | 3.20 | 21.95 | 21.30 | **21.31** | **+566%** |
| Public transport (`pt`) | 3.80 | 7.88 | 7.70 | **7.44** | **+96%** |
| Vehicle driver (`car+motorbike`) | 59.00 | 51.52 | 52.05 | **52.12** | **−11.7%** |
| Vehicle passenger (`ride`) | 20.60 | 0.61 | 1.39 | **1.61** | **−92%** |
| Walk only (`walk`) | 13.40 | 18.05 | 17.55 | **17.52** | **+31%** |
| **mean abs error, pp** | | **10.991** | **10.460** | **10.348** | |

### Per mode individually (F8, iteration 150, target LGA)

| mode | share % | LGA trips |
|---|---:|---:|
| car | 51.96 | 83,421 |
| walk | 17.52 | 28,133 |
| bike | 12.02 | 19,294 |
| taxi | 9.29 | 14,913 |
| pt | 7.44 | 11,950 |
| ride | 1.61 | 2,578 |
| motorbike | 0.17 | 265 |
| truck | 0.00 | 0 (freight is not an LGA resident) |

**Three things to carry forward:**

1. **CAR IS NOT OVER-CHOSEN.** It is **11.7% UNDER**. The record's "car bias"
   (54.33 planned / 47.90 realised legs) was whole-scenario legs across five LGAs
   including freight — the §12.1 geography error.
2. **`fit.py` folds bike and taxi into ONE target.** Quoting bike alone against 3.20
   understates the defect by half.
3. **`Other` +18.11 pp and `ride` −18.99 pp very nearly cancel.** They are one defect.

**Unscorable — never quote an error against these:** V206 (Walk linked, 0.0 by
construction), V196–V201 (2018/19 vintage), V001/V002 (pre-pandemic patronage),
V003 (monthly total needing WEEKDAY+SAT+SUN composed).

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE — the single next task
═══════════════════════════════════════════════════════════════════════════════

**Measure the declared, swept lever on the demand ceiling: widen
`B.activity.escort_binding_nonhh_scope` (§9.60) from `same_zone`, regenerate the
demand, and run an arm to iteration 200.**

- **Why this first:** it is the only lever on the +18.11/−18.99 pp defect that is
  already built, already declared, already swept, and needs no new number. The 5.4%
  ceiling in §4 is measured **with that mechanism live at `same_zone`**.
- **Cost:** demand regeneration (~1 h attended) + ~14 h to iteration 200 at the
  measured 257.89 s/it. **Needs a fresh stated-cost approval.**
- **Blocked on:** the scope decision in §0, and the run approval.
- **What decides success:** `Other` and `ride` move toward each other, and modelled
  occupancy moves off 1.0013 toward the **measured** 1.3503.

**If that is insufficient**, the queue in measured order of size:

| # | lever | size | state |
|---|---|---|---|
| 2 | Non-escort companion travel (#86) | the rest of the ~19 pp | **needs a decision — no rate may be invented** |
| 3 | Gradient into bike/walk link travel time (#21, reopened) | targets 28.5% of bike trips over 10 km | designed, **not built** |
| 4 | Taxi availability gate + age gate (#49, #50) | **19%** of the `Other` excess | needs a declared, swept, labelled-assumed field |

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.81 — the ride ratchet. FIXED and MEASURED.** `RidePairingEngine` re-moded an
unpaired ride leg by MUTATING THE PLAN; 95.7% of the 61,409 iteration-0 misses were
gone by iteration 1 and never returned. The forced walk is now an EXECUTION restored
at `AfterMobsim`. **Worth −0.531 pp of mean abs error.** No parameter moved.

**§9.82 — the empty escort tours. FIXED and MEASURED.** 84.53% of escort-arriving
trips were car while 11.45% of escort-bound members rode. `EscortCoherenceListener`
*proposes* the coherent plan back; `ChangeExpBeta` decides; the driver is never
touched. **Worth a further −0.112 pp.** `B.ride.escort_coherence_rate` is a SEARCH
rate whose zero recovers F7 exactly.

**§9.83 — this session. Measurement only.**
- `src/analyse/measure_iteration_modes.py` scores any single iteration through
  `fit.py`'s OWN `score_mode_share`, so folds and vintage filters cannot drift.
- The three-arm comparison in §2 — the first on a consistent basis.
- The car verdict **inverted**.
- **§9.82's probe evidence CORRECTED**: its pair-rate "reversal" at iterations 7–8
  is the innovation cutoff at 0.8 × 8 = 6.4, not convergence. §9.82 stays as written.
- The residual **located**: a demand ceiling (§5).
- The F8 arm stopped at iteration 163 and closed out with a measured cause.

**Already ruled out by measurement — do not re-propose:**
- Widening `B.ride.pairing_window_min` (§9.81): median gap to an endpoint-matching
  driver is **253.7 min**; 15→60 recovers 13 legs of 1,529.
- Moving a mode constant to close `Other`. The measured occupancy constraint would
  catch it, and it is a workaround.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

**THE DEMAND CEILING — read this before proposing any ride fix.**

**Every B2 trip carries `party_size = 1`** — all 2,343,321 rows. The only two-person
travel generated is the escort binding (`escorted` 125,409; `lift_pickup` and
`lift_serve` 49,030 each). **Escort-bound travel is 5.4% of trips against an observed
vehicle-passenger share of 20.6%.** Two **measured** observations agree:

| | modelled (F8 it.150) | observed | source |
|---|---:|---:|---|
| vehicle occupancy | 1.0013 | **1.3503** (sweep 1.2493–1.394) | `C.constraint.vehicle_occupancy`, measured |
| vehicle-passenger share | 1.61% | **20.60%** | V205 |

The seats exist — the arm's car trips carry ~330,000 free seat-trips against ~33,000
needed. **No repair inside the escort path can reach the target.**

Also standing:
- **Never compare across families, sample fractions or network builds.** F4 (the
  MAE 10.65 pp report card) is a **different family** from F6/F7/F8 — no taxi, no
  signals. Do not compare them.
- **One arm at a time** (#66).
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No converged arm exists in F7 or F8.
- Raw data immutable; every assumed value declared in the registry with a sweep.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no
  session links; never commit directly to `main`.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**, with their commands. This section describes shape.

- **Phase:** P4 calibration, 8 of 9 deliverables; deliverable 0 (0b backlog, #63) open.
- **Machine:** free. Last arm stopped 27 Aug 13:02.
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6 (embedding MATSim 2027.0-2026w25),
  Maven 3.9.9, run-stack 201 jars — all sha256-pinned in `.tools/toolchain.json`.
  **`LinkSpeedCalculator` is present in the run stack**, so the gradient lane needs
  no toolchain change.
- **Package:** `check_manifest.py` passes; `check_package.py` needs the full local
  package and runs on a workstation only.
- **Results:** the calibrated base is still C5 from `20260821T175907_1000it_25pct`
  (family F4, MAE 10.65 pp, 35 of 67 targets scored). **It did not move this
  session**, so the front door's figures are current.
- **Families:** F6 (activation boundary), F7 (§9.81), F8 (§9.82) — declared in
  [`audit/run_families.json`](../audit/run_families.json). No arm in any of them is
  a result.

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **SUMO descoped** (§9.74) — MATSim is the single simulator.
- **Constrain-and-report calibration** (§9.50, §9.64) — C5 states `feasible=False`
  with five violations rather than flattering the fit.
- **The pre-LR corridor keeps all 14 signalised intersections** (§9.24).
- **The coal chain is deliberately not simulated** (§9.70).
- **SCATS phasing stays `unobtained` and swept** (§9.21) — refused by policy.
- **Household-only ride pairing** (§9.55) — *superseded in part* by §9.60's
  non-household mechanism. §9.55 named the converged-run measurement as decisive;
  §9.83 delivers it, which is why #86 is a measurement-backed reopening of the
  question and **not** a re-litigation.
- **`B.ride.pairing_window_min` NOT moved** (§9.81) — refused on measurement.
- **Both §9.81 and §9.82 repairs KEPT** (§9.83) — measured to improve every scored
  category with no regression.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

1. **`modestats.csv` is not what `fit.py` scores, and neither is the events stream.**
   `modestats` counts **planned** modes (written at `IterationEnds`, after the §9.81
   restore); events give **legs** across five LGAs including freight. `fit.py` scores
   **linked main-mode TRIPS for target-LGA residents**, which MATSim writes per
   iteration as `<n>.trips.csv.gz`. **Cost: the entire gate loop chased a "car bias"
   that the scored quantity shows as 11.7% UNDER.** Use
   `src/analyse/measure_iteration_modes.py`.
2. **`fit.py` folds bike+taxi into one target and car+motorbike into another.**
   Quoting a folded mode alone halves the apparent defect.
3. **A short probe cannot see convergence, even the probe built to fix that.**
   `probe_replanning_25pct` keeps innovation on through 0.8 × 8 = 6.4 — which makes
   iterations 7 and 8 the **cutoff snap**, not evidence. §9.82 read that snap as the
   fix working. Cost: a 13.4 h arm launched on evidence that was an artefact.
4. **A validation probe too small or too short is blind, and it will pass.** 1%×2
   missed a multi-leg defect; 25%×2 passed code that killed an arm at iteration 2.
5. **A subtour has ONE mode class.** Re-moding one trip of a subtour while siblings
   stay `car` throws `Subtour contains a mix of chain- and non-chainbased modes`.
   Met twice (§9.63/#65, then §9.82's first build).
6. **A `Leg` reference does not survive the mobsim** — `PlanRouter` replaces the
   trip's elements; a restore through the old reference writes to an orphan and
   produces results byte-identical to the unfixed arm while logging success.
7. **Log lines measure intent, not effect.** Every failure above was caught by
   comparing arms, never by reading a success message.
8. **Measure before moving a parameter** (§9.81's window refusal).
9. **`bootstrap_toolchain.py --verify` mid-run can break a live JVM** — it recompiles
   into `.tools/classes`, which the JVM loads lazily. Compile to a scratch directory
   instead:
   `.tools/jdk/bin/javac.exe -cp .tools/jars/pt2matsim-26.6-shaded.jar -d <scratch> src/java/citysim/*.java`
10. **Stopping a run needs BOTH steps** — `Stop-ScheduledTask` leaves the JVM
    orphaned. Task names carry the launch stamp **minus one second**
    (`citysim_run_20260826T233657` for run `20260826T233658`). Then
    `taskkill /PID <java pid> /T /F`. The harness renames the directory itself.
11. Carried and still live: `os.kill(pid,0)` on Windows TERMINATES; git-bash
    heredocs eat backslashes; PowerShell 5.1 `-Encoding utf8` writes a BOM (write
    JSON via Python); `run.py --run-config smoke` resume-matches an earlier identical
    probe unless `--force`; a slow mobsim is not a dead run.

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's untested
claims via counterfactual microsimulation — hypotheses A1–A6 (LR share of regional
PT, trunk-vs-shuttle, door-to-door GJT, Hansen accessibility, genuine vs reshuffled
shift, network centrality) and B1–B4 (frontage exposure, retail catchment, **B3 net
arrivals across all modes — the decisive test**, generated vs displaced). Operational
goal: a twin whose per-mode ridership is *checked*. **Build half complete; checked
half failing 5 of 5 scored categories** (§2). **No hypothesis has been tested; no
scenario comparison exists.** Deliverables (proposal §8): 1 reproducible model 🟡
(not containerised) · 2 open data package 🟡 (489 files, unpublished) · 3 calibration
report 🟡 (C5, `feasible=False`, five stated violations) · 4 findings paper ⬜ ·
5 explorer 🟡 (replay + live view) · 6 method note 🟡 (SCATS refusal citable).

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs (55 raw downloads; SCATS refused,
journey-linked Opal unpublished, dwell unmeasured — all swept) · P2 ✅ (181,892-link
MATSim base + 4 variants, 15 mapped feeds, 0 unmapped stops) · P3 ✅ (612,687 agents,
621,722 WEEKDAY plan persons, 68.6% of escort tours bound) · **P4 🟡 8 of 9** ·
P5 ⬜ (mechanisms built inert) · P6 ⬜ (B1 has no observable without pedestrian
counts) · P7 ⬜.

**3 · Tasks per phase.** Batch 4.11 (ninth session) closed except 4.11.9, which was
**not reached** — the F8 arm was stopped at 163. Batch 4.12 (this session) is
measurement-only: 4.12.1–4.12.5 **done and evaluated**; 4.12.6 (non-household scope),
4.12.7 (taxi gate), 4.12.8 (gradient) **open**, and 4.12.6 is the active lane.
Done-but-not-evaluated: none — every item in 4.12 carries its measurement.

**4 · Simulator versus real life.** See **§2** for the full per-mode table. **No
valid post-repair run exists** — no `_run.json` in F6, F7 or F8; every arm was
stopped or died. The standing calibrated base is the **pre-repair F4** arm
`20260821T175907_1000it_25pct` (MAE 10.65 pp, 35 of 67 scored) and it is a
**different family** — do not compare it with F8's 10.348. **Light rail patronage
carries NO error figure**: V001/V002 are pre-pandemic, V003 is a monthly total no
single-day-type arm produces. Boardings are a level (#84).

**5 · Issue ledger.** Totals and the open set are in **§0**. Per open issue: **#86**
(NEW) the demand ceiling — 5.4% vs 20.6%, measured, the active lane's parent;
**#21** (REOPENED) gradient reaches mode choice through nothing, now measured as
material — 30.5% of 50,182 edges over 4% grade, bike trips 9.21 km vs a measured
5.2; **#48** ride as physical passenger — mechanism works, demand does not supply it;
**#49** taxi gated by nothing, folds into `Other` with bike; **#50** `age` reaches
nothing — measured table posted, bounds at 19% of the excess; **#30** walk geometry —
24.3% of walk trips over 5 km; **#84** patronage has no legitimate target; **#82**
counts −91.8%; **#73 #68 #66** awaiting a run; **#63** 0b backlog; **#62** city-free
input contract. Eight carry `awaiting-run`.

**6 · PR history and the next PR.** Totals in **§0**. The merged sequence runs from
the P1 data package (#1) through network (#2), demand (#3), the ride/mode work
(#52, #53, #69), the rename and two-arm campaign (#67), the all-modes batch
(#80, #81), the doc-currency gate (#83) and the front-door figures (#85). **This
session's PR** carries the ninth session's ten commits (the §9.81 and §9.82 repairs,
families F7/F8, registry 356→357) **plus** this session's §9.83 record and
`measure_iteration_modes.py`. **The next PR** should carry the widened non-household
scope and the arm that measures it — pending the §0 decisions.
