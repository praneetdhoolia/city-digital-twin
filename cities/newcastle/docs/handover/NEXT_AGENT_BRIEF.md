# Brief for the next agent — THE PAIR WAS DECLARED, THEN RE-FOUND BY A CLOCK THE MODEL ITSELF MOVES

*Updated 28 August 2026, TWELFTH session (§9.85) — a diagnosis-and-build session.
The F9 gate-2 arm was found RUNNING at session start, reached the iteration-100
gate, failed all five scored categories and was stopped. The cause is located and
repaired as family **F10**; the repair's effect on mode share is **NOT YET
MEASURED** — its validation probe was stopped on instruction at iteration 2 of 8.*

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
lives HERE and nowhere else** — later sections point at this table.

| Fact as of this handoff | Re-derive with |
|---|---|
| **This session's PR was OPEN at handoff.** If still open, merging it and deleting the branch both sides is the first item of unfinished business | `gh pr list --state open` |
| It carries **five** commits — the ELEVENTH session's four (F9) and this session's one (F10). The eleventh session never opened a PR | `git log main..HEAD --oneline` |
| 14 open issues: #88 #86 #84 #82 #73 #68 #66 #63 #62 #50 #49 #48 #30 #21 | `gh issue list --state open` |
| 55 filed · 41 closed · 14 open; 31 PRs merged, 2 closed unmerged, 0 open | `gh issue list --state all` · `gh pr list --state all` |
| **Machine FREE — no run in progress.** Everything was stopped on instruction 28 Aug ~21:0x | look for a MATSim `java` process (VS Code's `redhat.java` language server is NOT one); check `results/` mtimes |
| 66 run directories, 26 of them `aborted_*`, every one stating its cause | `ls -1d results/*/` · `results/INDEX.md` · `python src/run/run_failure.py --check` |
| Registry **372** fields | `python src/registry/check_hardcoding.py --strict` |
| **NO run approval stands. None.** Approvals are spent on use | assume none; ask |

Then the environment gate — **all of it must pass, and a failure is your first work
item, not a footnote**:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~3 s, compiles BOTH class trees
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
python src/run/run_failure.py --check              # every dead run says WHY
python src/analyse/build_fit_figures.py --check    # the front door draws the current base
python tests/check_city_agnostic.py                # 13/13
```

**⚠ STANDING DIRECTIVES:**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL — none is standing.** The F9 arm
   paced **273.82 s/it** median at 25%, so iteration 100 is ~7.6 h and iteration 200
   ~15.2 h. State the cost, get a yes.
1a. **LAUNCH with `python run.py --detach ...`**; a launch counts only once
   `matsim.log` is past `PersonPrepareForSim` (#70).
1b. **NEVER run two arms concurrently** (#66). No probe while an arm is up.
2. **The prime goal: every mode's ridership as close to real life as possible ON ITS
   OWN; no hardcoding, no biasing, no workarounds; every issue logged.**
3. **Every mode individually in every numbers table** — never an umbrella row.
4. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**
5. **Never hand-name a run**; `_run.json` stays the only result gate.
6. **A number in `README.md` or `STATUS.md` is a claim about an artefact** — fix it in
   the same commit and prove it with `check_doc_currency.py --strict`.
7. **NEVER STATE AN ERROR AGAINST AN UNSCORABLE TARGET** (#84). Read `_fit.json`'s
   `unscorable` list first. The light rail's boardings are a **level**, not an error.
8. **READ THE GATE ON `<n>.trips.csv.gz`, NEVER ON `modestats.csv`** (§9.83).
   `python src/analyse/measure_iteration_modes.py --run <dir> --it <n>`.

**⚠ DECISIONS REQUIRED:**
- **Approve the F10 arm**, and at what iteration count. ~7.6 h buys iteration 100.
  **Nothing is standing.**
- **Whether to complete the F10 validation probe first** (~35 min, 8 iterations). It
  was stopped at iteration 2; what it showed is in §4, and it is NOT a completed
  validation.
- **#88: make taxi physical?** It is a network-loading boundary and would make the
  F10 arm's effect unattributable if folded in. Sequence it, do not merge it.
- `E.replication.n_replications` — seed floor ≤0.11 pp/mode at n=2 (§9.64); open.
- **Warm-restart validity** — a warm-completed arm: valid arm, or diagnostic? (§9.76)
- **#84: what is the intervention's patronage legitimately checked against?**

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> **A digital twin of any city, traffic-wise ... whether that scaling actually
> predicts the correct ridership per mode must be CHECKED, not assumed. Every
> form of transport should be IN ACTION physically.**

Plus the standing gate-loop directive: *run → gate every 100 iterations → stop on
any mode past 20% deviation → fix the cause from the root → relaunch*, with **<10%
deviation per mode** as the bar and no workarounds, hardcoding or biasing.

"In action" is **nearly complete** — with one measured exception now filed as
**#88**: `taxi` is routed on the network but teleported in the mobsim, 39,892 of
39,923 legs per iteration. "Checked" has a measured answer and it is **5 of 5
scored categories failing the 10% bar**. The loop has now fired five times; each
firing has found a real cause and repaired it, and **none of the repairs has yet
been measured to move the fit** — F10's included.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually, on the basis that scores
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode TRIPS, Newcastle LGA residents, from the arm's own
`<n>.trips.csv.gz` — events-derived, so realised. **Family F9, arm
`aborted_20260828T111708_1000it_25pct`, iteration 100.** Reproduce with
`python src/analyse/measure_iteration_modes.py --run results/aborted_20260828T111708_1000it_25pct --it 100`.

### Scored against observation (`fit.py`'s own folds applied)

| survey category | modelled | observed | deviation | trend across it. 1 → 50 → 100 |
|---|---:|---:|---:|---|
| Other (`bike+taxi`) | 18.28 | 3.20 | **+471.2%** | 9.23 → 16.76 → 18.28 — **diverging** |
| Public transport (`pt`) | 8.49 | 3.80 | **+123.4%** | 9.85 → 9.14 → 8.49 — converging slowly |
| Vehicle driver (`car+motorbike`) | 47.57 | 59.00 | **−19.4%** | 35.25 → 40.65 → 47.57 — converging |
| Vehicle passenger (`ride`) | 4.87 | 20.60 | **−76.3%** | 9.10 → 6.03 → 4.87 — **decaying** |
| Walk only (`walk`) | 20.79 | 13.40 | **+55.2%** | 36.57 → 27.43 → 20.79 — converging |
| **mean abs error, pp** | | | **10.864** | 14.100 → 13.170 → 10.864 |

### Per mode individually (F9, iteration 100, target LGA)

| mode | share % | LGA trips |
|---|---:|---:|
| car | 47.41 | 75,414 |
| walk | 20.79 | 33,079 |
| bike | 9.79 | 15,575 |
| taxi | 8.49 | 13,500 |
| pt | 8.49 | 13,503 |
| ride | 4.87 | 7,750 |
| motorbike | 0.16 | 259 |
| truck | 0.00 | 0 (freight is not an LGA resident) |

**Three things to carry forward:**

1. **The excesses and the deficits balance exactly.** Over-chosen +27.16 pp (Other
   +15.08, walk +7.39, pt +4.69); under-chosen −27.16 pp (ride −15.73, driver
   −11.43). Bike, taxi and walk are absorbing the passenger demand `ride` is not
   realising — which is why the ride repair is the lever on all five categories and
   not just one.
2. **`fit.py` folds bike and taxi into ONE target** and car with motorbike into
   another. Quoting a folded mode alone halves the apparent defect.
3. **Car is UNDER, not over** (§9.83's inversion still holds).

**Unscorable — never quote an error against these:** V206 (Walk linked, 0.0 by
construction), V196–V201 (2018/19 vintage), V001/V002 (pre-pandemic patronage),
V003 (monthly total needing WEEKDAY+SAT+SUN composed).

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE — the single next task
═══════════════════════════════════════════════════════════════════════════════

**Run the F10 arm and gate it at iteration 100 on the per-mode basis.**

- **Why this and nothing else first:** F10 is built, gated and committed, and its
  effect is **unmeasured**. Every lever below it is a guess until the arm says what
  the identity repair actually realised.
- **Cost:** ~7.6 h to iteration 100 at the measured 273.82 s/it, 25% sample, ~40 GiB
  heap. **Needs a fresh stated-cost approval.**
- **Optionally first:** finish the 8-iteration `probe_replanning_25pct` validation
  (~35 min) that was stopped at iteration 2.
- **What decides success:** `paired_by_identity` grows with depth (it is 7 at
  iteration 0 and 1,745 at iteration 1 — it should keep climbing as drift
  accumulates); `pair_rate` and `occupancy_from_pairings` **stop decaying**; and
  `ride` rises while `Other` and `walk` fall.
- **What would falsify it:** `paired_by_identity` flat or `pair_rate` still decaying
  on the F9 curve. That would mean the identity is being found and the pairing still
  refused for a reason this session has not measured — go to `miss_endpoints` and
  `miss_capacity` in `ride_pairing.csv`, not to a parameter.

**If F10 proves insufficient**, the queue in measured order of size:

| # | lever | size | state |
|---|---|---|---|
| 2 | Bike's own excess | bike alone is 9.79% against a bike+taxi target of 3.20% | measure AFTER the F10 arm — bike may fall as ride is realised |
| 3 | Taxi physical in the mobsim (#88) | ~40,000 vehicle-trips/iteration missing from the network | **built nowhere**; a network-loading boundary, sequence it separately |
| 4 | Walk trip geometry (#30) | 24.3% of walk trips over 5 km | open |
| 5 | Counts −91.8% (#82) | 30 stations, 6 modelled-zero | awaiting a run |

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.85 — the translation loss. DIAGNOSED and REPAIRED; effect NOT YET MEASURED.**

The diagnosis, all measured on `aborted_20260828T111708` at iteration 100:

- **The seeded demand is right.** `modestats` ride is **0.1903 at iteration 0**
  against an observed 0.206. §9.84's binder closed the ceiling #86 was filed for.
- **The realisation fails.** `pair_rate` 0.556 → 0.362; `occupancy_from_pairings`
  0.3097 → **0.0956** against a measured 0.3503.
- **Why:** all three B2 binding tables NAME the driver (joint 70,964 rows, escort
  109,971, lift 45,602), and `build_matsim_plans.py` read that identity to decide
  **seeding** and then **discarded** it. Nothing in the population recorded that two
  people were a pair, so `RidePairingEngine` re-discovered each from geometry plus a
  15-minute window — while MATSim's own `TimeAllocationMutator` moved the two
  members apart independently at a **±1800 s default no registry field declared**.

| binding | ride legs | declared driver same OD **by car** | gap median | inside the 15-min window |
|---|---:|---:|---:|---:|
| joint | 28,709 | 73.8% | 10.3 min | **60.6%** |
| escort | 26,410 | 67.4% | 23.1 min | **42.6%** |
| lift | 7,746 | 80.5% | 7.1 min | **64.5%** |

**This is why §9.82's and §9.84's repairs were both inert** — each re-identifies
through the same window the drift has already exceeded. §9.84's driver-side pass
measured **10.920 → 10.864** mean abs error and ride **4.91 → 4.87** against the
previous arm at equal depth.

**Built as family F10** (committed, gates green):
1. `boundDriver` carries the identity from **all three tables** — 158,898 persons.
   Joint alone would have covered 46% of affected legs.
2. `RUN.replanning.time_mutation_range_s` **declared and swept** (group name
   `timeAllocationMutator` verified against `pt2matsim-26.6-shaded.jar` — it is NOT
   the capitalised form).
3. `B.ride.bound_pairing_window_min` **DERIVED** from it by identity; relaxes
   IDENTIFICATION only. The inferred window stays 15 min; endpoints, capacity and
   physical boarding still decide; the gap is waiting time paid for in score; a
   bound window narrower than the inferred one is **refused**.
4. `Booking` carries the tolerance it was made under — without this the pair rate
   rises while nobody boards.

**Partial validation only** (probe stopped at iteration 2 of 8, on instruction):

| | it. 0 (no drift) | it. 1 |
|---|---:|---:|
| `paired_by_identity` | 7 | 1,745 |
| pair_rate vs F9 at equal depth | 0.5560 = 0.5560 | 0.4936 → **0.5095** |
| occupancy vs F9 | 0.3097 = 0.3097 | 0.2770 → **0.2860** |
| physical wait-boardings / timeouts vs F9 | 453 → **637** / 3,964 → **3,784** | |

**Already ruled out by measurement — do not re-propose:**
- **Widening `B.ride.pairing_window_min`.** It is the INFERENCE window and stays 15
  min; widening it would loosen identification for strangers, which is the opposite
  of what the measurement supports.
- **Moving a mode constant to close `Other`.** The measured occupancy constraint
  would catch it, and it is a workaround.
- **Blaming the taxi teleport for the `Other` excess.** The fare IS scored — the
  teleported leg carries its route distance (median 13,343 m) and the flagfall fires
  on departure (46,914 × −$2.99 measured in the events). #88 is a physical-fidelity
  defect, not a scoring hole.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

- **F10 regenerates the population, so nothing run on it compares to F9** — and F9
  already broke comparability with F6/F7/F8. Never compare across families, sample
  fractions or network builds.
- **One arm at a time** (#66). No probe while an arm is up.
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No arm exists in F10 at all.
- **The calibrated base is still the pre-repair F4 arm** `20260821T175907_1000it_25pct`
  (MAE 10.65 pp, 35 of 67 targets scored) — a **different family**. Do not compare it
  with any F9 or F10 number.
- Raw data immutable; every assumed value declared in the registry with a sweep.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no session
  links; never commit directly to `main`.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**, with their commands. This section describes shape.

- **Phase:** P4 calibration, 8 of 9 deliverables; deliverable 0 (0b backlog, #63) open.
- **Machine:** free. Everything stopped on instruction 28 Aug.
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6 (embedding MATSim 2027.0-2026w25),
  Maven 3.9.9, run-stack 201 jars — sha256-pinned in `.tools/toolchain.json`.
  **Recompile with `bootstrap_toolchain.py --verify` after ANY Java change** — it
  installs into `.tools/classes`, which is what the JVM loads. Compiling to a scratch
  directory (trap 9) does NOT install, and a run will load the stale classes.
- **Package:** `check_manifest.py` passes; `check_package.py` needs the full local
  package and runs on a workstation only. **It was NOT run this session.**
- **Results:** the calibrated base did not move, so the front door's figures are
  current.
- **Families:** F6, F7, F8, F9, **F10 (current)** — declared in
  [`audit/run_families.json`](../audit/run_families.json). No arm in F7–F10 is a result.

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **SUMO descoped** (§9.74) — MATSim is the single simulator.
- **Constrain-and-report calibration** (§9.50, §9.64).
- **The pre-LR corridor keeps all 14 signalised intersections** (§9.24).
- **The coal chain is deliberately not simulated** (§9.70).
- **SCATS phasing stays `unobtained` and swept** (§9.21).
- **`B.ride.pairing_window_min` NOT moved** (§9.81, and re-affirmed §9.85 — it is the
  inference window and stays 15 min).
- **The §9.60 non-household scope stays `same_zone`** (§9.84) — measured 98% consumed.
- **§9.81, §9.82 and §9.84's repairs all KEPT** — none regressed anything, and §9.85
  explains why the last two could not have worked on their own.
- **#88 deliberately excluded from F10** (§9.85) — a separate boundary.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

1. **A repair can be found INERT and still be right about its cause.** §9.84's
   driver-side pass correctly identified that drivers drift off car, and moved the
   fit 0.056 pp — because it re-identified the drifted driver through the same
   15-minute window the drift had already exceeded. **When a well-evidenced repair
   does nothing, suspect the thing it depends on, not the diagnosis.**
2. **A MATSim config-group name is not what you would guess.** It is
   `timeAllocationMutator`, lowercase. Verify against the pinned jar with
   `javap -cp .tools/jars/pt2matsim-26.6-shaded.jar -constants <class>` before
   declaring a `matsim_param`.
3. **A framework DEFAULT is an undeclared modelling choice, and the ledger cannot
   see it.** `check_hardcoding.py` reads literals in scripts; `mutationRange` reached
   the mobsim through no declaration at all and was the single mechanism decohering
   every declared pair. **When a mechanism misbehaves, ask what MATSim is supplying
   that nobody declared.**
4. **Two engines can disagree about the same tolerance.** `RidePairingEngine` booked
   on the wide window while `JointRideEngine` timed the physical wait out on the
   narrow one — the pair rate would have risen while nobody boarded. Caught before it
   ran. **When you widen a tolerance, grep every consumer of it.**
5. **Compiling is not installing.** `javac -d <scratch>` (trap 9's advice, correct
   mid-run) leaves `.tools/classes` stale, and the next run dies on the config it
   cannot parse. Cost: one dead run. Run `bootstrap_toolchain.py --verify` once the
   machine is free.
6. **A parse bug in an analysis script will hand you a confident wrong number.** A
   flush-on-wrong-boundary bug reported taxi plans as scoring −137 utils worse than
   their alternatives; corrected, it is −4.43 median. **Re-derive a surprising number
   a second way before building on it.**
7. Carried: `modestats.csv` is PLANNED modes and the events stream is legs across
   five LGAs — **`fit.py` scores linked main-mode TRIPS for target-LGA residents**
   (§9.83); `fit.py` folds bike+taxi and car+motorbike; a short probe cannot see
   convergence; a probe too small or too short will pass blind; a subtour has ONE
   mode class; a `Leg` reference does not survive the mobsim; **log lines measure
   intent, not effect**; measure before moving a parameter.
8. **Stopping a run needs BOTH steps** — `Stop-ScheduledTask` leaves the JVM
   orphaned. Task names carry the launch stamp **minus one second**. Then
   `taskkill /PID <java pid> /T /F`. The harness renames the directory itself. **A
   `java.exe` at ~0.5 GB is VS Code's `redhat.java` language server, not an arm** —
   check the command line before killing it.
9. Carried and still live: `os.kill(pid,0)` on Windows TERMINATES; git-bash heredocs
   eat backslashes (write JSON and patches via Python); PowerShell 5.1 `-Encoding
   utf8` writes a BOM; `run.py --run-config smoke` resume-matches an earlier identical
   probe unless `--force`; a slow mobsim is not a dead run.

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's untested
claims by counterfactual microsimulation — hypotheses A1–A6 and B1–B4 (B3, net
arrivals across all modes, is the decisive test). Operational goal: a twin whose
per-mode ridership is *checked*. **Build nearly complete — one measured exception,
#88, where taxi is routed physically and simulated as a ghost. Checked half failing
5 of 5 scored categories** (§2). **No hypothesis has been tested; no scenario
comparison exists.** Deliverables (proposal §8): 1 reproducible model 🟡 (not
containerised) · 2 open data package 🟡 (492 files, unpublished) · 3 calibration
report 🟡 (C5, `feasible=False`, five stated violations) · 4 findings paper ⬜ ·
5 explorer 🟡 · 6 method note 🟡.

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs (SCATS refused, journey-linked Opal
unpublished, dwell unmeasured — all swept) · P2 ✅ (181,892-link MATSim base + 4
variants, 15 mapped feeds, 0 unmapped stops) · P3 ✅ (612,687 agents; 620,553
WEEKDAY plan persons on the F9/F10 demand) · **P4 🟡 8 of 9** · P5 ⬜ (mechanisms
built inert) · P6 ⬜ · P7 ⬜.

**3 · Tasks per phase.** Batch 4.12 closed except 4.12.6–4.12.8, which §9.84
superseded or built. Batch 4.13 (eleventh session) is closed: 4.13.7 superseded by
the two arms, 4.13.8 **done — the gate fired twice**. Batch 4.14 (this session):
4.14.1–4.14.7 **done and evaluated**, 4.14.8 **partial** (probe stopped at iteration
2 of 8), 4.14.9 **open and the active lane**, 4.14.10 open (#88).
Done-but-not-evaluated: **4.14.5–4.14.7 — the F10 build itself.** Its effect on mode
share is unmeasured and that is exactly what 4.14.9 exists to settle.

**4 · Simulator versus real life.** See **§2** for the full per-mode table. **No
valid post-repair run exists** — no `_run.json` in F7, F8, F9 or F10; every arm was
stopped or died. The standing calibrated base is the pre-repair **F4** arm
`20260821T175907_1000it_25pct` (MAE 10.65 pp, 35 of 67 scored), a **different
family** — do not compare it with F9's 10.864. **Light rail patronage carries NO
error figure**: V001/V002 are pre-pandemic and V003 is a monthly total no
single-day-type arm produces. Boardings are a level (#84).

**5 · Issue ledger.** Totals and the open set are in **§0**. Per open issue: **#88**
(NEW) taxi routed but teleported, 39,892 of 39,923 legs, ~40k vehicle-trips/iteration
missing from the network; **#86** the demand ceiling — **answered in the demand** by
§9.84 (ride 0.1903 seeded against an observed 0.206) and re-scoped by §9.85 to the
realisation question; **#48** ride as physical passenger — cause found and repaired,
effect unmeasured; **#21** gradient — built in §9.84, bike 12.02 → 9.79 across
families (not a like-for-like comparison); **#49** taxi modes; **#50** demographics;
**#30** walk geometry — 24.3% of walk trips over 5 km; **#84** patronage has no
legitimate target; **#82** counts −91.8%; **#73 #68 #66** awaiting a run; **#63** 0b
backlog; **#62** city-free input contract.

**6 · PR history and the next PR.** Totals in **§0**. The merged sequence runs from
the P1 data package (#1) through network (#2), demand (#3), the ride/mode work (#52,
#53, #69), the rename and two-arm campaign (#67), the all-modes batch (#80, #81), the
doc-currency gate (#83), the front-door figures (#85) and F6's first arm (#87).
**This session's PR** carries the eleventh session's four F9 commits plus this
session's F10 commit — the eleventh session closed without opening one. **The next
PR** should carry the F10 arm's gate reading and whatever cause it locates.
