# Brief for the next agent — RIDE WAS OFFERED TO PEOPLE NOBODY DRIVES, THE SEED WAS DOING THE SEARCHING, AND THE F14 ARM DIED OF A CONSOLE STOP NOBODY CAN NAME

*Updated 30 August 2026, SIXTEENTH session (§9.120). **A twelve-mode reading now
exists at every iteration the run writes** (the reader derives the linked-trip table
from experienced plans, validated exactly against the trips table). **The F14 arm
died mid-iteration 38** — `0xC000013A STATUS_CONTROL_C_EXIT` recorded by Task
Scheduler, no exception, trigger not established. Its own iterations measured the
defect the gate would have found: **residents PLAN ride on 22.5% of trips and realise
9.1%**, a third of planned ride legs had no declared driver, the declared pairs
decayed under independent time mutation, **65% of cyclists held no bike-free plan in
memory**, and 6.7% of planned trips were never experienced. Three repairs that invent
nothing open **family F15**, and **the first F15 arm is running at 10% × 300
iterations.***

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
| **AN F16 ARM IS RUNNING — THE MACHINE IS NOT FREE.** `results/20260830T132843_300it_10pct` (overlay `f16_gate_10pct`: S2, WEEKDAY, 10%, 300 it, cutoff 240), launched 30 Aug 13:28 as Task Scheduler task `citysim_run_20260830T132842`. The F15 arm `aborted_20260830T124711_300it_10pct` was **stopped on the gate at iteration 13** (§9.121). Measured pace at 10%: 120–150 s/it, so a gate every ~3.5 h | `python src/run/run_failure.py --check` (now reports a `running` record whose pid is dead); `_meta.json`; a MATSim `java.exe` at tens of GB — **the ~0.5–1 GB one is VS Code's language server** |
| Which iterations it has written, and its per-mode reading at each | `python src/analyse/report_mode_ridership.py --run results/20260830T124711_300it_10pct --trend` (every readable iteration, every mode, direction) · `--it <n>` for one table · `--watch 300` to keep printing — every 10th iteration is readable now, not only the trips-table ones |
| **This session's PR is OPEN at handoff** (or merged overnight — check) | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues — **none closed this session; #48, #86, #91, #30, #93, #96 carry new measured comments** | `gh issue list --state open` |
| Issue / PR totals | `gh issue list --state all` · `gh pr list --state all` |
| Run directories, and every dead one stating its cause | `ls -1d results/*/` · `results/INDEX.md` · `python src/run/run_failure.py --check` |
| Registry field count | `python src/registry/check_hardcoding.py --strict` |
| **NO run approval stands beyond the running arm.** Approvals are spent on use | assume none; ask |

Then the environment gate — **all of it must pass, and a failure is your first work item**:

```bash
python src/setup/bootstrap_toolchain.py --verify   # compiles BOTH class trees - NOT while an arm runs off .tools/classes (see trap 1)
python tests/check_manifest.py
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
python src/run/run_failure.py --check              # every dead run says WHY; a dead pid under `running` now fails it
python src/analyse/build_fit_figures.py --check
python tests/check_city_agnostic.py                # 13/13
python tests/check_package.py                      # LOCAL ONLY - RUN IT (ALL PASSED at handoff, verified)
```

**⚠ STANDING DIRECTIVES**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL.** Measured: ~290–305 s/it at 25%,
   ~100 s/it at 10%, ~30 s/it at 1%. The running arm is ~8–9 h.
2. **THE `/goal` DIRECTIVE** (the user's, in force since 24 Aug and re-issued this
   session): twelve modes present, physically simulated, monitored and scored; <10%
   deviation per mode; gate every 100 iterations, stop on >20% **or heading there**,
   fix from the root; print all twelve individually with a timestamp; converge in
   ≤250 iterations; unobtained data DERIVED, never assumed.
3. **READ THE TREND, NOT THE LEVEL** (§9.108) — and now read it against a scored
   choice set (§9.120): under `full_choice_set` every mode is scored within the first
   iterations, so a level at 100 means more than it ever did.
4. **A CAUSE MUST CARRY ITS MEASUREMENT.** Seven mechanisms have been argued from
   plausibility and refuted across three sessions.
5. **Every mode individually in every numbers table** — never an umbrella row.
6. **ONE ARM AT A TIME** (#66). **Never recompile into `.tools/classes` while an arm
   runs** — the gate's `bootstrap_toolchain.py --verify` does exactly that.
7. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**

**⚠ DECISIONS REQUIRED**
- **Enable the Task Scheduler operational log** (`wevtutil sl
  Microsoft-Windows-TaskScheduler/Operational /e:true`, needs elevation) so the next
  console-stop death of an arm names its trigger. The F14 arm's cannot be named.
- **Whether the demand's ride ceiling (#86) is the next family boundary** once the
  running arm shows bound ride realising — the binder supplies ~11% of trips against
  20.6% observed, and nothing in F15 changes that.
- **25% confirmation arm** after the 10% gate loop — stated cost ~25 h for 300
  iterations.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> Twelve modes present, **physically simulated**, monitored and scored — no teleportation.
> **<10% deviation from real life for every mode.** Unavailable data must be DERIVED.
> Gate every 100 iterations; stop on any mode past 20% or heading there; fix the cause
> from the root. Converge in ≤250 iterations. Print all twelve, individually, with a
> timestamp.

**Physical simulation: 12 of 12.** **Monitoring: met** — every 10th iteration yields the
twelve-mode table (§9.120). **<10% per mode: not met, and no honest level has been
read since F4** — F15's only gate (§2) was the seed-order artefact §9.121 names, and
the F16 arm is its correction. **Ride's mechanism is fixed** (88.8% of ride legs pair on
identity); its remaining gap is the demand's supply of drivers (#86).

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode trips, target-LGA residents, 10%. **THIS IS THE RUNNING
F16 ARM AT ITERATION 10 — every seed scored, selection still lagging scoring (car is
the best-scored plan for 61.1% of car-available residents and selected by 38.0%), NOT
the model's answer.** Reproduce with `python src/analyse/report_mode_ridership.py
--run results/20260830T132843_300it_10pct --it 10`; the F15 column is the same depth
with the car-first seed order (§9.121).

| # | mode | F16 it.10 % | F15 it.10 % | target % | deviation (F16) | what it is |
|---|---|---:|---:|---:|---:|---|
| 1 | car | 44.0758 | 36.9159 | 58.1631 | −24.2% | selection lag; best plan for 61% |
| 2 | ride | 7.4288 | 7.3597 | 20.6000 | −63.9% | **realises what is bound** (81–89% paired); ceiling is #86 |
| 3 | walk | 29.3956 | 33.0019 | 13.4000 | +119.4% | best plan for 6.4%; selected 16.9% |
| 4 | bike | 9.1107 | 11.2446 | 2.2084 | +312.5% | beats car for 14.1% (F15: 48.7%) |
| 5 | motorbike | 0.0591 | 0.0627 | 0.2406 | −75.4% | locked carve; 37 trips at 10% |
| 6 | taxi | 1.6100 | 1.6167 | 0.9916 | +62.4% | fleet refusing 37% of requests |
| 7 | bus | 6.5231 | 7.7055 | 2.3819 | +173.9% | pt best plan for 7.1% |
| 8 | heavy_rail | 1.7426 | 2.0318 | 0.7737 | +125.2% | as bus |
| 9 | light_rail | 0.0495 | 0.0579 | 0.6444 | −92.3% | corridor market (#30) |
| 10 | ferry | 0.0048 | 0.0032 | 0.1013 | −95.3% | 3 trips; the catchment exists (§9.120) |
| 11 | truck | 8.1391 | 9.3341 | — | n/a network-wide | `--truck-stations` scores it |
| 12 | freight_train | 314 closures | 314 | 314 | representation | — |

The four PT submodes share one folded HTS observation; their geometry deviations are
not independent. **The last valid trend reading remains the dead F14 arm's (25%,
iterations 1→30), recorded in §9.120.**

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

**Gate the running F16 arm at iterations 100, 200 and 300 — all twelve modes, trend
and level — with `report_mode_ridership.py --trend`.** Read the trend from iteration
10 on (iterations 0–6 execute the unscored seeds). What it must answer, in this order:

1. **Ride — answered on F15 (§9.121): it realises what the demand binds** (88.8% of
   ride legs paired on identity). Confirm on F16, then the ride gap is the demand
   ceiling (#86) and nothing in the run.
2. **With every mode scored under ONE traffic state, where do car, walk, bike and pt
   settle?** The F15 levels were the seed-order artefact; F16 is the first honest
   read. If bike still beats car in a resident's own memory, run
   `plan_scores`-style per-mode score comparison on the plans file before touching a
   constant — the scores, not the shares, say why.
3. **Does the model settle inside 250 iterations?** `_progress.json`'s relaxation block
   after the cutoff at 240.

If a mode is past 20% AND not moving toward its target across 100/200, stop the arm
per the directive and fix the cause it names. **Do not repair a mode off one gate.**

After the arm: the ride ceiling (#86/#91) is the likeliest next root cause; light rail
(#30, §9.103 — the corridor holds shopping/other ends at two-thirds of the observed
attraction rate, measured §9.120) and the ferry (#94) are untouched by F15.

**The ride ceiling, stated for the decision it needs.** The demand binds a driver to
~11% of resident trips against 20.6% observed. The joint binder re-aims a companion's
OWN drawn tour onto a household co-member's tour and adds no trip (§9.84), so its
supply is a SECOND licensed, car-available, travelling household member — and §9.111
measured that 41.7% of multi-person households have at most one, while 26.2% of
households are lone persons (#48). The passenger travel the HTS observes beyond what
households can serve is therefore travel with NON-household drivers, for which the
model holds a mechanism (the §9.60 lift binder, scoped `same_zone` to escort
re-targeting) and no observation of who drives whom. The derivable lane: anchor the
non-household volume on the identity (observed passenger share minus what household
binding serves), and match passengers to non-household drivers on OD and time within
the population — feasibility, not a rate, decides how much realises. That is a B2
change and a family boundary; it needs the user's decision and the F15 arm's ride
reading first.

**Queued for the same next family, measured and not built (§9.120):** residents who
drive trucks — census G62 one-method `Truck` 1,880 journeys to work, 1.058% of
car-as-driver journeys — transfer exactly as the motorbike carve does (≈0.62% of
resident trips, locked to `truck`); the directive's item 8. And #30's destination
solver, now quantified against the D1 layers (shopping/other ends in the tram
corridor at two-thirds of the observed attraction rate).

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.120 — the reader.** `src/analyse/iteration_trips.py` rebuilds the linked-trip
table from `<n>.experienced_plans.xml.gz` (stage activities by MATSim's rule, main mode
by `PtSubmodeMainModeIdentifier` over `DefaultAnalysisMainModeIdentifier`, distance as
the sum of route distances, pt submodes from boarded routes through the run's own
schedule). **Validated exactly** against the trips table at F14 it.0 (532,161 trips) and
F13 it.100 (221,144 trips, taxi included). `--validate <it>` re-checks any run holding
both. Both readers fall back to it and the basis line names the source.

**§9.120 — the F14 arm's death.** Closed out through `mark_dead` with the Task
Scheduler exit status; `run_failure.py --check` now also fails on a `running` record
whose pid is dead (trap 8 of the previous brief, fixed in the harness).

**§9.120 — the measurements** (all on `aborted_20260830T083019` iteration 30, residents):

| planned → experienced | trips | share |
|---|---:|---:|
| ride → ride | 13,994 | 9.14% |
| **ride → car (fallback drive)** | **12,098** | **7.90%** |
| **ride → walk (fallback walk)** | **5,833** | **3.81%** |
| ride → never experienced | 2,462 | 1.61% |
| walk → never experienced | 4,479 | 2.93% |
| taxi → walk (refused) | 1,194 | 0.78% |

Planned ride legs by declared-driver class, it.0 → it.30: no declared driver **26.6% →
36.0%**; same OD within 15 min **57.1% → 27.5%**; gap >45 min 1.8% → 7.5%; driver on
another mode 0.6% → 3.4%. Bike: **65.1% of 4,459 cycling agents hold no bike-free
plan** in memory. Stuck at 30:00: 18,412 agents (walk 9,327, ride 5,070, bus 3,202).

**§9.120 — the repairs, all built, probed (`20260830T124345_2it_1pct` rc 0) and running:**

| what | where | invents |
|---|---|---|
| `boundRideTrips` / `boundDriveTrips` per trip, from the three binding tables; ride refused off the first, non-car refused on the second | `build_matsim_plans.py`, `GatedSubtourModeChoice` | nothing |
| declared pair: no clock test; passenger's departing activity re-timed to the driver's departure minus the planned access walk | `RidePairingEngine` | nothing |
| `B.mode.seed_method` = `full_choice_set` — one plan per usable mode (2–6 per person); `RUN.replanning.max_agent_plan_memory` 5 → 8 | registry, `build_matsim_plans.py` | a method, swept against `uniform_draw` |
| motorbike carve q solved on eligible persons' own trip counts | `build_matsim_plans.py` | nothing |

Plans (3 day types), 30 run-input sets and the manifest (494 rows) rebuilt; F13, F14,
F15 declared in `run_families.json`; `check_package.py` adapted to the multi-plan seed
and ALL PASSED.

**§9.121 — the F15 arm's gate at iteration 10, and why it stopped at 13.** Ride pairs
at **88.8% on identity** (13,580 of 15,295; 0.41 on F14) — the ride repairs work. But
the per-mode plan scores of 14,753 car-available residents showed the **bike plan
+67.95 utils over the car plan on average (48.7% prefer it)**, pt +34.7 at p75, gaps of
±100 utils: activity utility lost, not travel time (parking −1.87 AUD/person-day).
Cause: the seed wrote car first and selected, so **iteration 0 ran car for 74.7% of
residents — 162,812 departures at 10%, 6,820 stuck, average score −77.8 — while every
other mode was scored on quarter-traffic roads in iterations 1–6**. Repair: the
first-executed seed plan is drawn uniformly per person by a hash. Plans, run inputs,
manifest rebuilt as **family F16**; the F15 arm is closed out with the reading in its
cause. Also measured and recorded in §9.120: the corridor holds shopping/other ends at
two-thirds of the observed attraction rate (`src/analyse/corridor_market.py`); the
ferry's catchment holds 59,458 trip ends within 1 km; the router's search/extension
radii were undeclared jar defaults and are now `RUN.transit_router.*`; 1,880 resident
truck commuters are observed in G62 and queued.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

- **FAMILY F16 IS OPEN (30 Aug 13:30, §9.121).** Nothing run before compares with
  anything after — not the 13-iteration F15 arm, not the dead F14 arm, not the two F4
  arms `README.md` draws from.
- **Never compare across sample fractions.** The running arm is 10%; F14 was 25%.
- **One arm at a time** (#66). **No recompile into `.tools/classes` while it runs.**
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No arm in F10–F15 has one.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no session links.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**.

- **Phase:** P4 calibration. First F15 arm running; no F15 level read yet.
- **Machine:** BUSY (the 10% arm, ~30 GB heap).
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6, Maven 3.9.9, run-stack 201 jars
  (MATSim 2027.0-2026w25); `.tools/classes` carries the §9.120 classes as compiled
  at 12:40 — **the source is one commit ahead of it** (`aba700f`, the bound-trip
  refusal counters logged), verified to compile in scratch; `bootstrap_toolchain.py
  --verify` installs it once no arm is running.
- **Registry:** 405 fields, ledger 0 (§9.120 added `B.mode.seed_method`,
  `RUN.transit_router.search_radius_m`, `RUN.transit_router.extension_radius_m`).
- **`check_package.py`: ALL CHECKS PASSED** with its 2 standing warnings — run this
  session on the F15 package, not asserted.
- **Session branch:** `praneetdhoolia/f15-choice-set-seed-bound-ride`, three commits
  at the time of writing; the PR opens at `/handoff`.
- `GOAL.md` at the repo root is the user's `/goal` text (untracked, not committed —
  the root holds one document by convention).

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **The seed is the full choice set** (§9.120) — supersedes §9.92's "the seed stays
  uniform"; `uniform_draw` is retained and swept against.
- **The first-executed seed plan is drawn uniformly per person** (§9.121) — never
  one mode for everyone: iteration 0 must be a mixed traffic state.
- **`ride` is a trip somebody drives**; a declared driver keeps `car` on the trips
  they serve (§9.120).
- **A declared pair is paired on identity and timed by the driver** (§9.120);
  `B.ride.bound_pairing_window_min` is a physical-wait tolerance only.
- **Plan memory 8** (§9.120), inside its 3–10 sweep, because MATSim removes an
  unscored plan first.
- Carried: `B.ride.pairing_rule` `both_links` (§9.92, §9.102); walk/bike feasibility
  bounds 0.0 (§9.106); coherence rates 0.4 (§9.93); a mixed-subtour proposal is
  refused (§9.119); SCATS offsets not adapted (§9.88); freight trains not mobsim
  vehicles (§9.70, §9.90); the taxi fare is not a lever (§9.91).

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

1. **A CHOICE SET IS SCORED UNDER WHATEVER TRAFFIC ITS ITERATION CARRIED** (§9.121).
   Car-first seeding gridlocked iteration 0 and handed every car plan a 60–100 util
   handicap ChangeExpBeta never re-tests. Read the per-mode plan SCORES in a resident's
   memory before believing a share; a share can be an ordering.
2. **THE ENVIRONMENT GATE RECOMPILES `.tools/classes`, AND AN ARM LOADS FROM IT.**
   `bootstrap_toolchain.py --verify` is in the gate; run it before an arm is up, never
   during. The F14 arm died within a minute of this session's start; the correlation
   is recorded, the cause is not established, and the scheduler log that would settle
   it is disabled.
2. **A `running` RECORD WITH A DEAD PID WAS INVISIBLE TO `--check`** (trap 8 of the
   last brief) — half an hour of a dead arm behind a green check. Fixed: the check
   fails on it now.
3. **THE TRIPS TABLE IS NOT THE ONLY SOURCE OF A TRIP** — the readers refused
   iterations the run had fully written. Derive from the experienced plans and
   VALIDATE against the table.
4. **A PLANNED SHARE CAN BE ABOVE TARGET WHILE THE REALISED ONE IS HALF OF IT** — a
   ride plan executed as a drive scores like a car plan. Read planned against
   experienced, trip by trip, before believing either.
5. **A LEVEL AT ITERATION 100 UNDER A UNIFORM SEED IS A STATEMENT ABOUT THE SEARCH.**
   65% of cycling agents had never been offered a bike-free plan.
6. **THE TASK NAME IS ONE SECOND BEFORE THE RUN DIRECTORY** — `Get-ScheduledTaskInfo`
   on the directory's stamp finds nothing.
7. **THE ~0.5–1 GB `java.exe` IS VS CODE**, not the arm; the arm is tens of GB.
8. Carried from earlier briefs: an intermittent crash is a deterministic defect under
   stochastic selection (§9.119); a gate that never compares a producer with its
   product cannot see a stopped producer (§9.116); run the local suite before
   believing the board about it (§9.117); an estimate is not a measurement; never read
   service from a `transitRoute` id (§9.113); a `main_mode` is never a pt submode
   (§9.112); check the yardstick before the model (§9.91, §9.100, §9.101);
   `modestats.csv` is PLANNED and the trips table is REALISED; git-bash heredocs eat
   backslashes — write Java/Markdown with a file tool.

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's claims by
counterfactual microsimulation (proposal §3, A1–A6, B1–B4). Operational goal: the
`/goal` twin whose per-mode ridership is *checked*. **Physical simulation 12 of 12;
per-iteration twelve-mode monitoring met; <10% per mode not met and no F15 level yet
read.** No hypothesis tested; no scenario comparison exists. Deliverables: 1 🟡 · 2 🟡
· 3 🟡 · 4 ⬜ · 5 🟡 · 6 🟡.

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs · P2 ✅ · P3 ✅ (plans regenerated 30 Aug
12:40 as the full choice set) · **P4 🟡** · P5–P7 ⬜.

**3 · Tasks.** Batch 4.15 (§9.120/§9.121): 4.15.1–4.15.10, 4.15.13 and 4.15.14 done;
4.15.11 (the F15 arm) stopped on the gate with its cause measured; **4.15.15 (run and
gate the F16 arm) running**; 4.15.12 (the ride ceiling) open as the next root cause.

**4 · Simulator versus real life.** See **§2** — F14 iteration 30, superseded. **No valid
post-cutoff arm exists in any family since F4.** The standing calibrated base is still
the F4 arm `20260821T175907_1000it_25pct` (MAE 10.65 pp), now three families back. Never
quote an error against a target `_fit.json` marks unscorable — the light rail's 3,417
and all six HTS mode-share rows are on that list.

**5 · Issue ledger.** Totals in §0. No issue closed this session. Measured comments
added: #48 (planned vs experienced; driver classes), #86 (the ~11% ceiling), #91 (26.6
→ 36.0% un-driven ride), #30 (walk's composition; 6.7% never experienced), #93 (carve
arithmetic repaired), #96 (F15 seeds no mixed subtour by construction; the scan is
pending). Untouched: #94, #84, #82, #73, #68, #66, #63, #62, #50, #49, #21.

**6 · PR history and the next PR.** Totals in §0. This session's PR carries §9.120 —
the reader, the F14 close-out, the measurements, the three repairs, the rebuild, the
F13/F14/F15 family declarations and the check widening. The next PR should carry the
F16 arm's gate readings and whichever root cause they name.
