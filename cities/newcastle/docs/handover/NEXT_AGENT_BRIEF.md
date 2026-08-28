# Brief for the next agent — THE SEED IS RECOVERABLE FOR THREE MODES, AND TAXI IS BLOCKED ON A DEPENDENCY

*Updated 29 August 2026, THIRTEENTH session (§9.86–§9.96) — a groundwork-and-diagnosis
session. The `/goal` directive was amended mid-session to forbid leaving an unavailable
input SWEPT where it can be DERIVED. Four inputs were derived or made physical, two arms
were run and stopped at their gates, and five paired 1% diagnostics separated the causes.
**The first evidence that the uniform seed is recoverable now exists.** Taxi's repair is
identified and **blocked on a dependency outside the sandbox** (#90).*

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
| **NO PR IS OPEN, and 16 commits sit unmerged on `praneetdhoolia/f11-taxi-physical`.** Opening that PR is the first item of unfinished business | `gh pr list --state open` · `git log main..HEAD --oneline` |
| 15 open issues: #91 #90 #86 #84 #82 #73 #68 #66 #63 #62 #50 #49 #48 #30 #21 | `gh issue list --state open` |
| 57 filed · 42 closed · 15 open; 32 PRs merged, 2 closed unmerged, 0 open | `gh issue list --state all` · `gh pr list --state all` |
| **#88 was CLOSED this session** on measured evidence (taxi physical); **#90 is NEW** and carries taxi's blocker | `gh issue view 88` · `gh issue view 90` |
| **Machine FREE — no run in progress.** Both arms stopped on the gate directive | look for a MATSim `java` process (VS Code's `redhat.java` is NOT one); `results/` mtimes |
| 82 run directories, 32 of them `aborted_*`, every one stating its cause | `ls -1d results/*/` · `results/INDEX.md` · `python src/run/run_failure.py --check` |
| Registry **389** fields | `python src/registry/check_hardcoding.py --strict` |
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
```

**⚠ STANDING DIRECTIVES:**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL.** Measured pace: **108 s/it at 10%**,
   **~300 s/it at 25%**. A 1000-iteration arm is ~30 h at 10%, ~83 h at 25%.
2. **READ THE GATE ON `<n>.trips.csv.gz`**, never on `modestats.csv` (§9.83), via
   `python src/analyse/report_mode_ridership.py --run <dir> --it <n>`. Trips are written
   at iterations **0, 1, 50, 100, 150 …** — every 50, not every iteration.
3. **A LEVEL READ WHILE INNOVATION IS RUNNING IS NOT A STATEMENT ABOUT THE MODEL**
   (§9.92, §9.94). Innovation is off after 80% of iterations. **Read the TREND, not the
   level**, until you have a post-cutoff arm.
4. **Every mode individually in every numbers table** — never an umbrella row.
5. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**
6. `python src/analyse/report_mode_ridership.py` is the twelve-mode reader.

**⚠ DECISIONS REQUIRED:**
- **#90 — unblock taxi**: Maven Central in `sandbox.network` (for DRT/DVRP), **or** a
  point-to-point usage/incidence source. Without one, taxi cannot reach the bar honestly.
- **Approve a converged arm.** ~30 h at 10% to iteration 1000, innovation off at 800.
- **Whether ride's ceiling is structural** — per-agent scoring cannot represent joint
  household utility, and that may cap `ride` below its target permanently.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> Twelve modes present, **physically simulated**, monitored and scored — no teleportation.
> **<10% deviation from real life for every mode.** Unavailable data must be DERIVED,
> not ignored and not left swept. Gate every 100 iterations; stop on any mode past 20%;
> fix the cause from the root — no workarounds, no biasing.

**Physical simulation: 11 of 12 complete.** Taxi stopped being teleported this session
(§9.86). The exception is not a teleport — it is **taxi's absent SUPPLY constraint**
(#90). Freight rail is represented by its road effect (timetable-derived crossings,
§9.90); the trains are deliberately not mobsim vehicles because the coal chain is
grade-separated.

**<10% per mode: not met.** At the last gate, one mode (heavy rail, −10.5%) was near the
bar and the rest were past it. **But the trend is the finding, not the level** — see §2.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually, and the TREND that matters
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode TRIPS, Newcastle LGA residents, from the arm's own
`<n>.trips.csv.gz`. Arm `aborted_20260829T054941_1000it_10pct`, **iteration 100**.
Reproduce with `python src/analyse/report_mode_ridership.py --run results/aborted_20260829T054941_1000it_10pct --it 100`.

| # | mode | modelled % | target % | deviation |
|---|---|---:|---:|---:|
| 1 | car | 45.5103 | 58.1631 | −21.8% |
| 2 | ride | 7.1512 | 20.6000 | −65.3% |
| 3 | walk | 20.6445 | 13.4000 | +54.1% |
| 4 | bike | 8.9434 | 2.2084 | +305.0% |
| 5 | motorbike | 0.1174 | 0.2406 | −51.2% |
| 6 | taxi | 9.2720 | 0.9916 | +835.1% |
| 7 | bus | 6.4360 | 1.3039 | +393.6% |
| 8 | heavy_rail | 1.8735 | 2.0922 | **−10.5%** |
| 9 | light_rail | 0.0407 | 0.4039 | −89.9% |
| 10 | ferry | 0.0110 | 0.1013 | −89.2% |
| 11 | truck | 6.7974 | 15.4698 | −56.1% |
| 12 | freight_train | 314 | 314 | representation, not a fit |

**The seed is deliberately uniform (§9.92), so read the direction:**

| CONVERGING | it. 0 | it. 100 | target |
|---|---:|---:|---:|
| car | 34.09 | **44.22** | 58.16 |
| walk | 28.88 | **15.22** | 13.40 |
| pt | 6.88 | **5.30** | 3.80 |

| DIVERGING | it. 0 | it. 100 | target |
|---|---:|---:|---:|
| taxi | 0.00 | **8.81** | 0.99 |
| bike | 7.08 | **8.24** | 2.21 |
| ride | 19.03 | **14.19** | 20.60 |

Motorbike is flat at 0.18 against 0.24.

**Walk travelled from +115% to +14% of target in 100 iterations. That is the first
evidence the co-evolution recovers from the seed at all**, and it is this session's most
important result.

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE — the single next task
═══════════════════════════════════════════════════════════════════════════════

**Open the PR. 16 commits are unmerged and no PR exists.** Nothing else should start first.

**Then: ride.** It is the largest fixable deviation (13.4 pp) with no external blocker,
and it is the one that indicts the model rather than the data. **Do NOT repeat the
claim that ride seeding at 19.03% vindicates the binder — §9.96 withdraws it.** That
number is the deliberately uniform seed showing through (p=0.20/0.25 predicts 21.2% on
its own); whether the binder is correctly sized is OPEN.

The mechanism, measured (§9.92, §9.94):

1. 52.1% of planned ride legs fail to pair (44,044 of 84,609 at the F12 25% arm)
2. `remodeUnpaired=true` converts every unpaired leg **before the mobsim** — the events
   carry 40,965 ride departures against 40,565 *paired* legs, so none of the unpaired
   ones departs as ride; they are realised as **walk**
3. the ride plan therefore scores badly, the agent abandons ride, and the thinner demand
   leaves fewer pairing candidates — a feedback loop

**What to measure first, before changing anything:** why DECLARED pairs fail on
endpoints. `miss_endpoints` is 27,807 against `miss_window` 4,981 and `miss_capacity`
1,432, while `paired_by_identity` is only 8,883 of 40,565 pairings. The demand names the
driver in all three B2 binding tables; find out what the driver's plan is actually doing
when the endpoint test refuses it. `ride_pairing.csv` carries only aggregates — this
needs a per-leg diagnostic that does not yet exist.

**Suspect the joint-utility ceiling.** MATSim scores agents individually, so a driver who
detours for a household member is scored only on their own loss. The coherent state may
be genuinely unreachable under per-agent scoring, which would cap `ride` permanently.
That is a finding worth establishing rather than fighting.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.86 — taxi stops being teleported (family F11).** It was network-routed,
link-permitted, congestion-bound and car-bodied but absent from `RUN.qsim.main_mode`, so
39,892 of 39,923 legs an iteration never touched the carriageway. One registry enum.
Measured: 197 of 197 taxi departures now enter traffic, 29,994 link traversals. #88 closed.

**§9.87 — twelve modes get twelve targets.** The HTS publishes SIX categories; bus, light
rail, heavy rail and ferry shared ONE 3.8% row. `build_mode_targets.py` writes
`mode_targets_by_mode.csv`, read by `report_mode_ridership.py`. Deliberately NOT added to
`validation_targets.csv` — a disaggregation scored beside its parents would double-count
and disturb the 67/143 split.

**§9.88 — SCATS becomes an implemented ALGORITHM (family F12).** Every prior arm ran 14
intersections on a fixed 110 s plan. `ScatsSignalController` measures degree of saturation
at every signalised stop line, adapts cycle length toward a target DS on the critical
movement, and equalises DS across stages. **Offsets deliberately NOT adapted** — that
library is the unreleased artefact and no algorithm replaces it. Transit priority lives
inside the same controller; its compensation ledger became unnecessary because SCATS
repays a starved stage through DS feedback. Two defects found and recorded: DS measured
against FULL-SCALE capacity read 0.000 at a 1% sample (`flowCapacityFactor` belongs in the
denominator), and modular cycle arithmetic cannot survive a variable cycle.

**§9.89 — the ferry gets a derived target**, 0.1013%, from the census one-method count
scaled by the HTS PT level. Mode 10 had no target at all before.

**§9.90 — level crossings derived from the mapped rail timetable.** Adamstown 110/weekday
and Islington 204, against an assumed flat 30 per site; 541 → 2,440 change events. The
SHAPE matters more than the count: uniform closures land where there is no traffic. A
boom already down stays down (spans merge), and a passenger train is not a coal train
(separate declared duration).

**§9.91 — the first defect the gate found was in the YARDSTICK.** §9.87 sized taxi from
the census journey-to-work share; taxi is overwhelmingly non-commute, so the target was
fivefold low. `B.taxi.daily_trips_band` (IPART 2025) gives **0.9916%**, and **bike takes
the residual 2.2084%** because the two share one survey category.

**§9.92 — the seed is a bad guess ON PURPOSE.** `B.mode.seed_split` is uniform so that
arriving at the observed point is evidence about the model. **Do not switch to
`seed_split_informed` to close the gap** — its own description says seeding at the answer
makes reaching the answer uninformative.

**§9.93 — coherence rates 0.1 → 0.4**, argued on search completeness, not fit: the
listener proposes and `ChangeExpBeta` disposes, so a higher rate cannot make a bad plan
win, only reduce the chance a good two-sided plan is never offered.

**§9.94 — the first F12 gate.** See §2.

**Reader fix:** a linked PT trip was counted once per submode boarded (only 14,785 of
29,761 board one submode). Now allocated to the submode with the greatest in-vehicle
distance. It flipped **ferry from +51.2% to −94.9%** — the bus over-count had been hiding
a light-rail and ferry deficit.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

- **F12 changed signal control, crossings and the coherence rate**, so nothing before it
  compares to anything after. F11 closed unmeasured; F10 closed unmeasured.
- **Never compare across sample fractions.** This session's arms are 25% and 10%, and the
  diagnostics are 1%. Judging ONE arm against fixed observed targets is fine; comparing
  two arms at different fractions is not.
- **One arm at a time** (#66). No probe while an arm is up.
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No arm in F10, F11 or F12 has one.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no session links.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**.

- **Phase:** P4 calibration. Groundwork now derived rather than assumed.
- **Machine:** free.
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6, Maven 3.9.9, run-stack **201 jars —
  matsim + signals ONLY, no DVRP/DRT** (this is #90's blocker). Recompile with
  `bootstrap_toolchain.py --verify` after ANY Java change.
- **Network sandbox:** ABS, TfNSW, Overpass, Copernicus, GitHub reachable (200).
  **`repo1.maven.org` returns 404 in 0.3 s — Maven Central is blocked**, verified.
- **Families:** F10, F11 closed unmeasured; **F12 current** (§9.88–§9.90, §9.93).
- **Diagnostic overlays committed:** `taxi_fare_stress_1pct`, `taxi_fare_control_1pct`,
  `subtour_chain_1pct`, `ride_coherence_1pct` — all 1%/40it, all with written
  justification, none a result.

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **The seed stays uniform** (§9.92). Seeding at the answer makes the answer uninformative.
- **`B.ride.pairing_rule` stays `both_links`** (§9.92). The engine's own measurement finds
  the missing pairs have no endpoint-matching driver at ANY hour, so relaxing it would
  pair passengers with drivers going elsewhere.
- **`proba_random_single_trip_mode` stays at its declared value** (§9.92). Measured worth
  ~4 pp of a 22 pp deficit — buying a small fit improvement with an exploration parameter.
- **SCATS offsets are not adapted** (§9.88).
- **The taxi fare is not a lever** (§9.91) — it binds elevenfold, and the held-fixed rule's
  excluded 12 km tail would make long taxi trips *cheaper*, not dearer.
- **Freight trains are not mobsim vehicles** (§9.70, §9.90) — grade-separated track.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

1. **A NUMBER THAT AGREES WITH YOUR EXPECTATION STILL HAS TO BE EXPLAINED.** Ride
   seeds at 19.03% against a 20.60% target, and §9.94 and §9.95 both read that as
   evidence the demand was right. It is the uniform seed's own p=0.20 showing through
   (§9.96), and the claim was repeated in two committed entries before anyone checked
   the arithmetic. **Ask what would produce the number if the model were WRONG.**
2. **A CURVE THAT IS STILL MOVING IS NOT A LEVEL.** This session made that error TWICE
   inside one investigation (§9.91): a stress arm read at iteration 20 said "price cannot
   discipline taxi" and by iteration 40 said the opposite; then a collapse was attributed
   to the innovation cutoff when the control showed the cutoff worth ~11% against the
   fare's elevenfold. **Wait for the arm to finish before concluding.**
3. **A LEVEL READ WHILE INNOVATION RUNS IS NOT THE MODEL'S ANSWER.** Car jumps
   31.96% → 35.90% across the cutoff. Read the trend, or read post-cutoff.
4. **The TARGET can be the defect.** §9.87's taxi target was fivefold low because it used a
   commute source for a non-commute mode. **Check the yardstick before blaming the model.**
5. **A sampled mobsim is not a small city.** It is a city whose capacities were scaled, so
   any measurement against a real-world rate must scale with `flowCapacityFactor` (§9.88).
6. **Submodes are not additive.** A linked PT trip boards several; counting it once per
   submode nearly doubled the PT total and hid two deficits.
7. **The registry refuses out-of-sweep values typed at a shell** — and it is right to.
   Deliberate stress tests need a COMMITTED overlay with a written justification.
8. Carried: `modestats.csv` is PLANNED modes and the trips table is REALISED — the two
   differ by exactly the remoded unpaired rides; git-bash heredocs eat backslashes (write
   patches via a Python file); compiling is not installing (`bootstrap_toolchain.py
   --verify`); stopping a run needs BOTH `Stop-ScheduledTask` and `taskkill /PID <pid> /T
   /F`; a `java.exe` at ~0.5 GB is VS Code's language server, not an arm.

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's claims by
counterfactual microsimulation. Operational goal: a twin whose per-mode ridership is
*checked*. **Physical simulation 11 of 12** (taxi lacks supply, #90). **<10% per mode not
met**, but the seed is now demonstrated recoverable for car, walk and pt. **No hypothesis
tested; no scenario comparison exists.** Deliverables: 1 🟡 · 2 🟡 · 3 🟡 · 4 ⬜ · 5 🟡 · 6 🟡.

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs · P2 ✅ · P3 ✅ · **P4 🟡** · P5–P7 ⬜.

**3 · Tasks.** This session: groundwork derived (§9.86–§9.90), two arms gated and stopped,
five diagnostics run, causes separated. Open: ride's pairing loop, taxi's supply (#90),
and a converged arm.

**4 · Simulator versus real life.** See **§2**. **No valid post-cutoff arm exists** — no
`_run.json` in F10, F11 or F12. The standing calibrated base is still the pre-repair **F4**
arm `20260821T175907_1000it_25pct` (MAE 10.65 pp, 35 of 67 scored), a **different family**.

**5 · Issue ledger.** Totals in §0. **#91** (NEW) three in ten ride legs carry no declared driver — reframed by §9.96; **#90** (NEW) taxi supply, blocked on a dependency;
**#86** demand ceiling — the seed is now measured RIGHT for ride (19.03 vs 20.60), so this
is a realisation question; **#48** ride as physical passenger — the loop is measured;
**#84** patronage has no legitimate target; **#82** counts; **#73** signals — SCATS landed;
**#68** crossings — derived, §9.90; **#66** concurrency; **#63** 0b backlog; **#62**
city-free contract; **#50** demographics; **#49** individualise modes — targets landed;
**#30** walk geometry; **#21** gradient.

**6 · PR history and the next PR.** Totals in §0. **NO PR IS OPEN and 16 commits are
unmerged** — that is the next PR, and it carries §9.86–§9.94.
