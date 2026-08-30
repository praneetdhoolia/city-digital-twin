# Brief for the next agent — A SEVENTH OF THE WORKFORCE HAD NO LICENCE, THE RAIL AND TRAM TARGETS WERE A SURVEY'S SCALE, AND THE PACKAGE ON DISK IS HALF-REBUILT

*Updated 30 August 2026, SIXTEENTH session, at handoff (§9.127–§9.131). Five root causes
were measured and fixed from the root in one day — the harness resume key (§9.127), a
declared ride pair served by the **driver's detour** (§9.128, family F19), the sampling
rule that biased every sub-sample and the carve pool that was not drawn (§9.129, family
F20 — the carve fix read motorbike at **−0.1%**), heavy rail and light rail held to
their **disclosed boardings** (§9.130), and the licence rate replaced by the **TfNSW
count over the ABS population, per LGA** (§9.131, family F21). **Nothing is a result.**
The F20 arm was stopped at iteration 11 at the user's direction at handoff; **the
machine is idle and the data package is INCONSISTENT** — the population is rebuilt, the
chains, plans and run inputs are not. That rebuild is your first build.*

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
| **NO ARM IS RUNNING — the machine is idle.** The F20 arm `aborted_20260830T184955_300it_10pct` was stopped at iteration 11 at the user's direction (cause in its `_meta.json`). The only `java.exe` should be VS Code's (~0.4 GB). | `tasklist \| findstr java` · `Get-ScheduledTask \| ? TaskName -like 'citysim_run_*' \| ? State -eq Running` · `ls -t results/ \| head` |
| **THE PACKAGE ON DISK IS INCONSISTENT.** `demand/population/B1_synthetic_population.csv` was rebuilt 30 Aug 19:31 with the measured licence rates (612,634 persons); the demand chain was then stopped mid-way through the WEEKDAY chains and its partial `B2_activity_trips_WEEKDAY.csv` / `B2_escort_bindings_WEEKDAY.csv` were deleted. **WEEKDAY chains are ABSENT; SAT/SUN chains, all plans and the 30 run-input sets are the F20 build on the OLD population.** `tests/check_package.py` will say so. | `ls -la cities/newcastle/demand/plans/B2_activity_trips_*.csv` (WEEKDAY missing) · `python tests/check_package.py` |
| **This session's PR is OPEN at handoff** (or merged — check) | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues — **none closed; #98 and #99 opened; #49 #93 #86 #48 #91 #30 #84 #50 #94 carry new measured comments** | `gh issue list --state open` |
| Issue / PR totals | `gh issue list --state all` · `gh pr list --state all` |
| Run directories, and every dead one stating its cause (four arms died this session, all with causes) | `ls -1d results/*/` · `results/INDEX.md` · `python src/run/run_failure.py --check` |
| Registry field count (414 at handoff) | `python src/registry/check_hardcoding.py --strict` · `python tests/check_doc_currency.py --strict` |
| **NO run approval stands.** Approvals are spent on use | assume none; ask |

Then the environment gate — **all of it must pass, and a failure is your first work item**:

```bash
python src/setup/bootstrap_toolchain.py --verify   # compiles BOTH class trees - never while an arm runs (trap 3)
python tests/check_manifest.py
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
python src/run/run_failure.py --check              # every dead run says WHY
python src/analyse/build_fit_figures.py --check
python tests/check_city_agnostic.py                # 13/13
python tests/check_package.py                      # LOCAL ONLY - EXPECTED TO FAIL until the chain below is rerun
```

**Then the first build — the chain the handoff interrupted (~1 h, CPU only, not a run):**

```bash
python src/build/build_activity_chains.py          # four binder passes incl. shared rides under the bucket rule
python src/build/build_matsim_plans.py             # choice-set seed, carves on the drawn pool
python src/build/build_matsim_run_inputs.py        # 30 sets
python src/build/normalise_eol.py && python src/build/build_manifest.py && python src/build/normalise_eol.py
python tests/check_package.py                      # must be ALL PASSED before any launch
```

Read the chains report for the shared pass (`_activity_chains_report.json` →
`by_day.WEEKDAY.shared_binding`: servable / bound / shortfall — last value 73,509 /
59,701 / 0 on the OLD population) and the plans report's `motorbike_carve` /
`truck_carve`, then pin the counts `check_doc_currency.py` names.

**⚠ STANDING DIRECTIVES**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL.** Measured: ~100–200 s/it at 10%
   (3–4 min/it with the driver detour and 25,000 ride legs), ~30 s/it at 1%. A 300
   iteration 10% arm is 9–15 h.
2. **THE `/goal` DIRECTIVE** (the user's, in force since 24 Aug): twelve modes present,
   physically simulated, monitored and scored; <10% deviation per mode; gate every 100
   iterations, stop on >20% **or heading there**, fix from the root; print all twelve
   individually with a timestamp; converge in ≤250 iterations; unobtained data
   DERIVED, never assumed — **and where a value is DISCLOSED, use the exact official
   value** (that is what §9.130 and §9.131 did).
3. **READ THE TREND, NOT THE LEVEL** (§9.108), and read it against a scored choice set
   (§9.120): iterations 0–6 execute the unscored seeds, 10–30 are exploration.
4. **A CAUSE MUST CARRY ITS MEASUREMENT.** Every cause this session was measured
   before it was fixed (§9.127–§9.131); a walking meeting point that was built first
   was measured out on its smoke before it reached an arm (§9.128).
5. **Every mode individually in every numbers table** — never an umbrella row.
6. **ONE ARM AT A TIME** (#66); launch **detached** (`run.py ... --detach`); **never
   recompile into `.tools/classes` while an arm runs.**
7. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**

**⚠ DECISIONS REQUIRED**
- **Enable the Task Scheduler operational log** (`wevtutil sl
  Microsoft-Windows-TaskScheduler/Operational /e:true`, needs elevation) — still
  pending since the F14 arm's unexplained death.
- **A confirmation arm's fraction.** The bucket coupling rule (§9.129) keeps pairs
  inside any nested sample whose fraction is a multiple of 0.05 — 10%, 25% and 50%
  all qualify. The stated cost of a 25% × 300 arm is ~25 h.
- **Whether bus should move to a boardings basis** (#99) once an official regional
  bus count is acquired — the HTS level and the operator counts differ by 3–10×.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> Twelve modes present, **physically simulated**, monitored and scored — no teleportation.
> **<10% deviation from real life for every mode.** Unavailable data must be DERIVED;
> disclosed values are used exactly. Gate every 100 iterations; stop on any mode past
> 20% or heading there; fix the cause from the root. Converge in ≤250 iterations.

**Physical simulation: 12 of 12** (a declared ride pair is now served physically by
the driver's detour, §9.128). **Monitoring: met** — the twelve-mode table at every
10th iteration, on the disclosed-boardings basis for the two rail modes. **<10% per
mode: not met; no gate has been reached since F4** — every arm since F15 was stopped
early because it measured its own root cause before iteration 100. **Motorbike read
−0.1% at F20 iteration 10** on the corrected carve pool. The structural cause behind
heavy rail (+475%), walk, bike and bus on work trips — a seventh of the workforce
unlicensed — is fixed in the population and awaits the F21 arm.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode trips of target-LGA residents at 10%, except heavy rail and
light rail, which are **boardings per weekday, all travellers, × 1/fraction, against
their disclosed counts (§9.130)**. **These are the F20 arm at ITERATION 10 — the
exploration phase, NOT a result and NOT a gate**; they are the last twelve-mode
reading taken. Reproduce with `python src/analyse/report_mode_ridership.py --run
results/aborted_20260830T184955_300it_10pct --it 10`. F19 at iteration 20 (`--run
results/aborted_20260830T170743_300it_10pct --it 20`) is the deepest reading of this
day; F17 at iteration 50 (§9.126) remains the deepest reading of any family.

| # | mode | F20 it.10 | target | deviation | F19 it.20 | what decides it next |
|---|---|---:|---:|---:|---:|---|
| 1 | car | 48.01% | 58.32% | −17.7% | 56.76% | the licence fix (§9.131): workers get their cars |
| 2 | ride | 9.22% | 20.60% | −55.2% | 10.86% | exploration; 41,194 bound ride trips in the 10% plans, above the target's share |
| 3 | walk | 25.60% | 13.40% | +91.0% | 18.05% | exploration (walk plans of 8 km tours) + the licence fix |
| 4 | bike | 7.77% | 2.21% | +251.7% | 6.90% | the licence fix (census JTW bicycle 0.06–1.4%) |
| 5 | motorbike | **0.378%** | 0.3785% | **−0.1%** | 0.115% | the carve delivers what it solves for (§9.129) |
| 6 | taxi | 1.64% | 0.99% | +64.9% | 1.63% | fleet (§9.99), untouched |
| 7 | bus | 5.49% | 2.38% | +130.5% | 4.30% | the licence fix; target basis questioned (#99) |
| 8 | heavy_rail | 37,520 bdg | 6,529 bdg | +474.7% | 30,800 bdg | suburban stations 3–13× over (#98); the licence fix |
| 9 | light_rail | 1,650 bdg | 2,954 bdg | −44.1% | 1,440 bdg | Interchange transfer works; corridor market present; open (§9.130) |
| 10 | ferry | 0.035% | 0.143% | −75.3% | 0.039% | derived target; untouched since §9.121 (#94) |
| 11 | truck | 7.98% network share | — | n/a | 6.53% | `--truck-stations` scores it |
| 12 | freight_train | 314 closures | 314 | representation | 314 | — |

Pairing at F20 iteration 0: 8,068 of 8,256 ride legs paired (0.977), 2,864 passengers
on 2,683 detours, none unroutable, 175 motorbike-locked persons (F19: 52), 23,040 named
drivers (F19: 28,244) — the sample's composition verified (§9.129).

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

**1. Rerun the demand chain on the rebuilt population (§0), pass the package suite,
write `cities/newcastle/overlays/runs/f21_gate_10pct.json` as a copy of
`f20_gate_10pct.json` with its own description (§9.131), declare family F21 in
`docs/audit/run_families.json` (`from_launch` = the launch stamp), smoke
(`run.py --run-config smoke --force`, 1% × 2 it, ~4 min; read the `ridePairing` and
`jointRide` log lines), launch detached, verify iteration 0** — persons ≈ 61,300 (10% of
612,634), `boardings` and `detour` lines present — then gate at 100 / 200 / 300.

**2. At the first gate, what must be answered, in order:**
- **Heavy rail on the disclosed basis, station by station** (#98):
  `python src/analyse/report_mode_ridership.py --run <arm> --it 100` gives the total;
  the per-station comparison script is not in the repo — rebuild it from §9.130's
  method (rail boardings by access-stop name against
  `data/processed/validation/pt_boardings_targets.json`'s `heavy_rail.stations`).
  If the suburban stations are still over after the licence fix, read the rail plan's
  score against the car plan for outer-LGA workers before touching a constant.
- **Work-trip mode split by HOME LGA against census G62** — the yardstick §9.131
  found; script it (experienced plans + `extract_metrics.home_lga()` +
  `census2021_G62_SA1.csv` via `zones/sa1_to_lga.csv`). Car 86–91%, train 0.1–0.3%,
  walked 1.4–4.4%, bicycle 0.06–1.4%.
- **Light rail** (§9.130): the corridor market and the Interchange transfer are
  measured present; where the missing ~1,300 boardings a weekday are — longer corridor
  trips, rail transferees, visitors — is open. Bus and ferry against their derived
  targets.

If a mode is past 20% AND not moving toward its target across 100/200, stop the arm
per the directive and fix the cause it names. **Do not repair a mode off one gate.**

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.127 — the harness resume key.** `find_completed` matched on scenario, day,
fraction, iterations, seed, overrides, the controler hash and the resolved values — not
on the population — so a smoke "passed" by resuming a probe on old plans. The day's
population sha256 (`inputs_sha256`) is part of the run key and of `_meta.json` /
`_run.json` (declared in their schemas). And the sampler: a shared ride binds only to
drivers the sampler keeps whenever it keeps the passenger (superseded by §9.129).

**§9.128 — the driver's detour (family F19, arm `aborted_20260830T170743`, 27 it).**
The valid F18 arm's iteration 0 refused 2,053 of 6,966 ride legs on endpoints (the
same-SA2 shared rides). A walking meeting point was built and measured on a 1% smoke at
8–11 km walked per passenger — replaced. `RidePairingEngine` now accepts a declared pair
on identity, defers it, and routes the driver's car leg (run's own car router, at
BeforeMobsim) through each carried passenger's origin links in departure order, then
their destination links; the passenger boards and alights at their own link; booked at
the routed pass time; re-timed to it; the driver's score pays. `B.ride.declared_pair_
meeting` = `driver_detour` | `passenger_links` (`ridePairing.declaredMeeting`). F19
iteration 0: 6,850 of 6,966 paired, 2,005 passengers on 1,888 detours, mean 596 s, none
unroutable; iteration 20 was ahead of F17 on every mode.

**§9.129 — the sample's composition, and the carve pool (family F20, arm
`aborted_20260830T184955`, 10 it).** The 9.127 at-or-below rule named low-hash
households as drivers, and a 10% sample is the low-hash households: named drivers kept
at 12.4%, everyone else at 7.95%, the motorbike carve at 5.5% of its persons. Replaced
by a same-bucket rule, `B.ride.shared_lift_hash_bucket` 0.05, measured on the binder
(at-or-below 98,549 / 59,718 / 0; bucket 0.10 86,848 / 59,806 / 0; **bucket 0.05 73,509
/ 59,701 / 0**; unconstrained 105,515 / 59,648 / 17). And the carves were solved before
the named-driver refusal (42.1% of the pool's trips): the pool now excludes named
drivers, and the rebuilt carve delivered 0.2666% against 0.2654% solved (was 0.153%).
F20 iteration 0 verified 175 motorbike-locked persons and 23,040 named drivers at 10%;
iteration 10 read motorbike 0.378% (−0.1%).

**§9.130 — the disclosed boardings basis.** Light rail: the line's own Opal series,
1,005,033 boardings over 2025-07..2026-06 = 2,754 a day; heavy rail: 24 stations'
entries, 6,086 a day; both × `CAL.pt.weekday_factor` 1.0727 (new) → 2,954 and 6,529 per
weekday. `build_mode_targets.py` writes them (`pt_boardings_targets.json` carries the
per-station counts); `report_mode_ridership.py` scores modelled boardings of every
subpopulation × 1/fraction (`iteration_trips.boardings`, `extract_metrics.
transit_stop_names`). Measured on F19 iteration 20: light rail 1,440 (−51%; was −96% on
the derived basis), heavy rail 30,800 (+372%; Interchange 1,430 vs 1,569 right; Hamilton
7,050 vs 534, Adamstown 1,670 vs 83). Also measured and NOT the tram's cause: the
corridor's destination market (work ends 5.8% vs jobs 4.4% within 400 m), the Interchange
transfer (44 of 74 CBD-bound rail alighters take the tram; rail→tram walk 54–58 m; 16
tram vs 8 bus departures to the CBD in 07–09), the corridor-internal market (1,127 trips,
mean beeline 500 m, car 59% walk 27%).

**§9.131 — the licence rate (family F21 at the next launch).** Work-trip mode split by
home LGA vs census G62 (car 86–91% / model 55–59%; train 0.1–0.3% / model 2.4–5.4%);
17.5–21% of employed persons had no car available, 14.2–14.8% no licence (a literature
vector). Acquired `data/raw/tfnsw/driver_licences_snapshot_2026.zip` and
`data/raw/abs/32350DS0003_2024.xlsx` (`fetch_licences.py`, `provenance_licences.json`);
`build_licence_rates.py` → `licence_rates_by_age_lga.csv` (per LGA) and the pooled
vector in `B.population.licence_rate_by_age_band` (measured: 18-24 0.78, 25-34 0.94,
35-44 1.00 capped, 45-54 0.98, 55-64 0.97, 65-74 0.98, 75-84 0.92, 85+ 0.51, 12-17
0.08); `build_population.py` draws at the LGA's rate. **Population rebuilt** (612,634
persons; employed with a car 90.8–91.7% outside Newcastle LGA, 80.8% inside). **Chains,
plans, run inputs NOT rebuilt** (§0).

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

- **FAMILY F21 OPENS AT THE NEXT LAUNCH (§9.131).** Nothing run before compares with
  anything after — not F20 (10 it), F19 (27 it), F18 (1 it), F17 (60 it), F16, F15,
  nor the F4 arms `README.md` draws from.
- **Heavy rail and light rail changed BASIS on 30 Aug 19:20 (§9.130)** — a reading on
  the trip-share basis does not compare with one on the boardings basis.
- **Never compare across sample fractions.** All arms since F15 are 10%.
- **One arm at a time** (#66). **No recompile into `.tools/classes` while it runs.**
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No arm in F10–F20 has one.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no session links.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**.

- **Phase:** P4 calibration. No arm running; no gate reached since F4.
- **Machine:** IDLE (verify, §0).
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6, Maven 3.9.9, run-stack 201 jars
  (MATSim 2027.0-2026w25); both class trees compiled at 18:47 with the §9.128 engine
  (the one later commit touched a comment only); `bootstrap_toolchain.py --verify`
  recompiles them.
- **Registry:** 414 fields, ledger 0 (this session added `B.ride.declared_pair_meeting`,
  `B.ride.shared_lift_hash_bucket`, `CAL.pt.weekday_factor`; `B.population.
  licence_rate_by_age_band` became `measured`).
- **Package:** 501 manifest rows; **INCONSISTENT on disk** (§0) — `check_package.py`
  last ALL PASSED on the F20 package at 18:42.
- **Session branch:** `praneetdhoolia/f15-choice-set-seed-bound-ride` (the whole
  sixteenth session, 48+ commits); the PR opens at `/handoff`.
- `GOAL.md` at the repo root is the user's `/goal` text (untracked, not committed —
  the root holds one document by convention).

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **A declared pair whose links differ is served by the driver's detour** (§9.128) —
  not by the passenger walking to the driver (measured 8–11 km) and not by refusing
  the pair on geometry.
- **A shared pair shares a sampling-hash bucket of 0.05** (§9.129) — at-or-below kept
  pairs together and biased the sample; a bucket prefers no hash.
- **The carves solve on the pool that is drawn** (§9.129) — escorters AND named
  drivers excluded before the solve.
- **A disclosed count is the target** (§9.130) — heavy rail and light rail on
  boardings; a survey level split by a composition is used only where nothing is
  disclosed (bus, ferry).
- **The licence rate is the published count over the published population, per
  LGA** (§9.131) — `literature` gave way to `measured`; the 35–44 rate is capped at 1.
- **The population a run sampled from is part of its identity** (§9.127).
- Carried: the seed is the full choice set (§9.120); the first-executed plan is drawn
  (§9.121); the direct walk is the network walk (§9.121); `ride` is a trip somebody
  drives (§9.120); plan memory 8; `both_links` for inferred pairs (§9.92, §9.102);
  coherence rates 0.4 (§9.93); mixed subtours refused (§9.119); SCATS offsets not
  adapted (§9.88); freight trains not mobsim vehicles (§9.70, §9.90); the taxi fare
  is not a lever (§9.91).

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

0. **STOPPING A BUILD CHAIN MID-STEP LEAVES A HALF-WRITTEN ARTEFACT.** The chains
   builder overwrites `B2_activity_trips_WEEKDAY.csv` incrementally; the interrupted
   F21 chain left a 317 MB partial where a 323 MB file had been. Deleted, and the
   package is inconsistent until the chain reruns (§0). Never hash a partial file into
   the manifest; never launch on it.
1. **A COUPLING RULE THAT USES THE SAMPLING HASH BIASES THE SAMPLE** (§9.129). The
   count was 10.01%; the composition was not — named drivers 12.4%, the motorbike carve
   5.5%. After any change to who is bound to whom, read the sample's composition
   (locked persons, named drivers) against 10% of the population, not just its size.
2. **A DERIVED TARGET CAN STAND WHERE A DISCLOSED COUNT EXISTS** (§9.130). The light
   rail's "−96%" was the survey's scale; the published series read −51%. Before naming
   a mode's cause, check whether its target is observed or derived.
3. **THE ENVIRONMENT GATE RECOMPILES `.tools/classes`, AND AN ARM LOADS FROM IT.**
   Run `bootstrap_toolchain.py --verify` before an arm is up, never during. A detached
   arm is a Task Scheduler task named ONE SECOND BEFORE its run directory's stamp;
   stopping it needs `Stop-ScheduledTask` AND killing the `java.exe`/`python.exe`.
4. **A MONITOR THAT WATCHES A RUN DIRECTORY BY PATH GOES BLIND WHEN `mark_dead`
   RENAMES IT `aborted_…`** — it never sees the status change. Watch by stamp glob.
5. **THE HARNESS RESUMED A COMPLETED PROBE WHEN ONLY THE POPULATION HAD CHANGED**
   (§9.127) — fixed (`inputs_sha256`), kept as the pattern: a run's identity is its
   inputs, not its parameters.
6. **A 1% SMOKE'S REALISED TIMES ARE THE FLOW-CAPACITY ARTEFACT** — a 40-minute car leg
   took 2–10 hours at 1% and made the detour's timeouts look like a defect (§9.128).
   Read a smoke for exceptions and counters, never for times or shares.
7. **A LAUNCH WITHOUT `--detach` IS A CHILD OF THE SESSION** — six minutes lost
   relaunching F19. Always `run.py --run-config <overlay> --detach`.
8. **`git-bash` HEREDOCS EAT BACKSLASHES AND BREAK ON `%`** — three scripts failed on
   `'\\'` and `'%'` before being written with the file tool. Write any script longer
   than a line, or containing a backslash or a percent sign, with a file tool.
9. Carried: a mode's excess is often another mode's deficit — split the population
   before touching a constant (§9.123); a beeline crosses water (§9.121); a choice set
   is scored under whatever traffic its iteration carried (§9.121); a `running` record
   with a dead pid is now caught by `--check`; the trips table is not the only source
   of a trip (§9.120); a planned share can be above target while the realised one is
   half of it; the ~0.4 GB `java.exe` is VS CODE; an intermittent crash is a
   deterministic defect under stochastic selection (§9.119); check the yardstick
   before the model (§9.91, §9.100, §9.101, §9.130).

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's claims by
counterfactual microsimulation (proposal §3, A1–A6, B1–B4). Operational goal: the
`/goal` twin whose per-mode ridership is *checked*. **Physical simulation 12 of 12;
per-iteration twelve-mode monitoring met (on the disclosed basis for the rail modes);
<10% per mode not met — motorbike read −0.1% at F20 iteration 10, no gate reached.**
No hypothesis tested; no scenario comparison exists. Deliverables: 1 🟡 · 2 🟡 · 3 🟡 ·
4 ⬜ · 5 🟡 · 6 🟡.

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs (raw downloads 58 with the licence
acquisition) · P2 ✅ · P3 🟡 **regressed to inconsistent on disk** (population rebuilt
19:31, chains/plans/run inputs not — §0) · **P4 🟡** · P5–P7 ⬜.

**3 · Tasks.** Batch 4.15 (§9.120–§9.131): 4.15.1–4.15.10, 4.15.13–4.15.14,
4.15.16–4.15.17, 4.15.19–4.15.24, 4.15.26, 4.15.28, 4.15.30–4.15.31, 4.15.33–4.15.35
done and measured; 4.15.11, 4.15.15, 4.15.18, 4.15.25, 4.15.27, 4.15.29, 4.15.32 are
arms stopped with their causes measured; **4.15.36 (rerun the chain, launch and gate
the F21 arm) is the active lane**; 4.15.12 (the ride ceiling) open.

**4 · Simulator versus real life.** See **§2** — F20 iteration 10, exploration phase,
superseded by F21. **No valid post-cutoff arm exists in any family since F4.** The
standing calibrated base is still the F4 arm `20260821T175907_1000it_25pct` (MAE 10.65
pp), now many families back. Never quote an error against a target `_fit.json` marks
unscorable — the light rail's pre-pandemic patronage row and all six HTS mode-share rows
are on that list; the report's disclosed-boardings rows (§9.130) are the honest light
rail comparison now.

**5 · Issue ledger.** Totals in §0. No issue closed this session. Opened: **#98**
(heavy rail five times the disclosed entries at suburban stations) and **#99** (the
HTS pt level and the operator boardings differ by a factor the targets cannot see).
Measured comments added: #49, #93, #86, #48, #91, #30, #84, #50, #94. Untouched: #96,
#82, #73, #68, #66, #63, #62, #21.

**6 · PR history and the next PR.** Totals in §0. Merged this month, newest first: #97
(F15–F18 demand rebuild and the replanner), #95 (PT and truck yardsticks, ride
ceiling), #89 (joint travel, gradient and age gates), #87 (ride ratchet, escort
decoherence), earlier PRs in `gh pr list --state merged`. **This session's PR** carries
§9.127–§9.131: the resume key, the driver detour, the bucket rule and carve pool, the
disclosed boardings basis, the licence acquisition and rates, four closed-out arms,
families F19 and F20, the F20 overlay, and the rebuilt population's reports. **The next
PR should carry the rerun chain, the F21 arm's gate readings, and whichever root cause
they name.**
