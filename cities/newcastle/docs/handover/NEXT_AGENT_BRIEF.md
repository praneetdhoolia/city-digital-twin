# Brief for the next agent — THE BASE ARMS ARE RUN; THE MODEL HAS ITS REPORT CARD; THE NEXT LEVER IS THE OWNER'S

*Updated 24 August 2026 (the two-arm campaign session, 21–24 Aug). The
session: **§9.62** the owner-approved two-arm launch (arm A base, arm B
seed replication) · **§9.63** both arms crashed at replanning 1 (the M1
lift-overlap defect, #65), repaired and relaunched the same afternoon ·
**§9.64** both arms COMPLETED (rc=0, relaxed, accounting closes) — C5
exists, the fit is measured, ride's collapse is diagnosed as choice not
physics, and the seed noise floor is ≤0.11 pp/mode. This is a HANDOVER,
not a source of truth: where it disagrees with [`STATUS.md`](../STATUS.md),
[`DECISIONS.md`](../DECISIONS.md) or
[`.claude/CLAUDE.md`](../../../../.claude/CLAUDE.md), those win.*

---

═══════════════════════════════════════════════════════════════════════════════
§0  DO THIS FIRST
═══════════════════════════════════════════════════════════════════════════════

**Run `/onboard`**; at session end, `/handoff`. The checks:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~1 min, compiles 14 Java sources
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
```

**⚠ OWNER DIRECTIVES, standing:**

1. **NO MULTI-HOUR RUNS WITHOUT EXPLICIT APPROVAL — none is standing.**
   The two-arm §9.62 approval was CONSUMED by the completed campaign.
   Measured cost on this family: **~240 s/iteration median per arm under
   the two-arm pattern → ~67.4 h/arm** (§9.64); single-arm ~233 s (§9.59).
2. **DO ONE THING RIGHT rather than bloating the repo.**
3. **Every mode individually in every numbers table** — never a "public
   transport" umbrella row (Tier R makes this mechanical).
4. **Never commit directly to `main`; the session's ONE PR opens at
   `/handoff`**, is watched to merge, and the branch deleted both sides.
5. **The prime goal (owner, 21 Aug): all forms of ridership as close to
   real life as possible ON THEIR OWN; no hardcoding or Newcastle bias;
   every issue spotted logged on GitHub.**

**Start from `main`. No run is in progress; the machine is free.**

**⚠ TWO DECISIONS WAIT ON THE OWNER (§9.64) — bring them before building:**
- **Which demand-side scoring lever answers ride's collapse.** M2 (driver
  detours) is a NO-GO on the evidence; the §8.5-held constants stay held;
  the candidate space is the declared-and-swept scoring priors.
- **`E.replication.n_replications`** — the seed floor is measured
  (≤0.11 pp/mode at n=2); 3–5 is supportable; the value is the owner's.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> **A digital twin of any city, traffic-wise ... whether that scaling
> actually predicts the correct ridership per mode must be CHECKED, not
> assumed. Every form of transport should be IN ACTION physically.**

**"In action physically" is DONE and survived a 1000-iteration campaign**
(§2). **"Checked" now has its first answer, and the answer is honest: the
uncalibrated base does NOT yet predict ridership per mode** — MAE 10.65 pp
over the five held mode shares, and the light rail realises 1,260 of its
observed 3,417 weekday boardings (§9.64). Note the direction: the standing
risk is rail OVER-forecast (9 of 10), and this base UNDER-realises the LR —
every flattering error stays reported, never absorbed (§9.50).

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — the base arm's measured state (fit, Newcastle LGA, §9.64)
═══════════════════════════════════════════════════════════════════════════════

| mode | modelled | observed | error | state |
|---|---|---|---|---|
| Vehicle driver | 73.19 | 59.0 | +14.19 | overshoot carries displaced ride |
| Vehicle passenger | **0.09** | 20.6 | **−20.51** | physical machinery works (100% of survivors board, 0 refusals); the CHOICE collapses — the central open problem |
| Walk only | 7.28 | 13.4 | −6.12 | wedge repaired (was 0.71); the deficit is #30's short-trip generation (mean 5.56 km vs 0.70 observed, 7.9×) |
| Bike | 11.21 | 3.2 | +8.01 | likely carries displaced child/carless ride demand |
| PT aggregate | 8.22 | 3.8 | +4.42 | split: bus 6.13 · rail 0.77 · **tram 0.02** · ferry 0.02 — composition wrong on the corridor |
| Motorbike | 0.21 | (locked carve, §9.52) | — | not a choice mode |
| Truck | — | swept, never pinned | — | freight physical (§9.49) |

Occupancy realises 0.0013 vs 0.3503 (stated violation in C5). Counts:
−91.8% mean with 6 modelled-zero stations — statistically identical to the
previous family (−91.05%), the recorded no-through-demand structure.

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE — in order (§9.64's derivation)
═══════════════════════════════════════════════════════════════════════════════

1. **Bring the owner the two §0 decisions** (ride lever; n_replications).
2. **Ride-choice decomposition** — measure where ride plans die:
   never-proposed vs proposed-and-scored-out vs unpairable-re-moded. Cheap
   (reads the completed arms' events/plans; no new run). This one gap
   plausibly explains most of driver's +14 and bike's +8.
3. **#30's generation mechanism** — the walk short-trip mass, now with a
   valid baseline (7.28 vs 13.4; noise floor 0.03 pp at this metric).
4. **PT composition on the corridor** — why demand rides buses past the
   tram (frequency? transfer sweep point? access stubs?): the diagnostic
   that matters most to the study's own question.
5. **A real calibration search** within declared sweeps against the C5
   baseline (the 4.2.4 machinery, now unblocked) — AFTER the structural
   lanes above, or it calibrates the wrong model.
6. Then by recorded order: #49 Tier C + taxi (4.4, owner-sequenced), #50's
   modelled table (now derivable from arm A), #62, #63.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — do not redo any of it
═══════════════════════════════════════════════════════════════════════════════

- **§9.49–§9.57** (20–21 Aug, PRs #56/#58/#59): freight physical ·
  constrain-and-report decision · motorbike · physical boarding · walk/bike
  physical · emergent ride · events accounting · events threads.
- **§9.58–§9.61** (21 Aug, PR #64): the walk wedge repaired four ways
  (refusals → 0) · every wall-time knob measured · non-household lifts
  (M0 waiting + M1 re-target) · 0b: four assumptions became measurements ·
  #49 Tier R · #62/#63 filed.
- **§9.62–§9.64** (21–24 Aug, this session's PR): the two-arm campaign —
  overlays `phys1000_arm_a/b_25pct` · the #65 lift-overlap repair (busy
  check reads re-targeted sibling times + a contiguity assertion in
  `bind_nonhousehold_lifts`; weekday bindings 55,249/55,614) · **both arms
  complete and valid** · fit + C5 + calibration report · seed floor
  measured · M2 no-go · #14/#9/#28/#31 closed on evidence.

**Phases:** P0–P3 ✅ · P4 🟡 (**8 of 9** — deliverable 0/0b open, #63) ·
P5–P7 ⬜.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES YOUR WORK
═══════════════════════════════════════════════════════════════════════════════

- **No multi-hour run without owner approval. None standing.**
- **The comparability family is §9.58–§9.63** (the §9.63 demand repair is
  part of it — the completed arms ran ON the repaired demand). Nothing in
  it compares to `phys50_25pct`, the aborted `phys1000_25pct`, or
  anything older. NEVER compare across families or fractions;
  `target_lga_pct`, never `all_residents_pct`.
- **THE 67/143 SPLIT IS PRE-REGISTERED** — `fit.py` enforces; need a
  holdout? SAY SO AND STOP.
- **One build of the network per comparison** (§3.5); `RUN.machine.threads`
  (qsim, now 8 on this family's arms) and `replanning_threads` are run
  identity; `event_handler_threads` is not (§9.56).
- **No invented data**: who-drives-whom stays unobserved; the lift split is
  REPORTED (§9.60); the fit's 32 unscorable targets are named, never
  padded.
- **A run without `_run.json` is not a result**; the two valid arms carry
  theirs, the three quarantine directories under
  `results/_aborted_20260821/` do not.
- **The §8.5-held mode constants are unreachable by calibration BY
  CONSTRUCTION** — do not "fix" ride by touching them without the owner.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE — 24 August 2026, session close
═══════════════════════════════════════════════════════════════════════════════

| | |
|---|---|
| PRs | This session's PR (`praneetdhoolia/two-arm-relaunch-watch`) opens at this handoff; 22 prior merged, 2 closed unmerged (#39, #57) |
| Toolchain | 3 pinned, unchanged; 14 Java sources compile |
| Registry | **334 fields**; ledger **0** `--strict`; G2 13/13 |
| Package | **429 manifest files** + `params/C5_calibration.json` (committed); `check_manifest` OK |
| Machine | **free**; no run in progress |
| Run cost | ~240 s/it/arm two-arm (measured §9.64), ~233 s single (§9.59) → ~65–67 h per 1000-iteration arm |
| Runs | **`20260821T175907_1000it_25pct` (arm A, ex `phys1000a_25pct`) + `20260821T180310_1000it_25pct` (arm B, ex `phys1000b_25pct`): the family's two VALID runs** (rc=0, relaxed 0.031 pp, accounting closes, `_run.json`/`_fit.json`/`SUMMARY.md`) · **every run directory renamed 24 Aug to the runner scheme — map in DECISIONS.md §9.65; the runner names new runs itself, `--tag` is gone** · quarantined (renamed in place): `_aborted_20260821/20260821T010821_1000it_25pct`, `_aborted_20260821/20260821T172050_1000it_25pct`, `_aborted_20260821/20260821T172453_1000it_25pct` · probes as recorded on the board |
| Open issues | **8**: #48 (ride choice — THE lane) · #30 (walk generation) · #49 (Tier C + taxi) · #50 (modelled table now derivable) · #62 (city-agnostic contract) · #63 (0b backlog) · #65 (repaired in-tree, closes with this PR) · #66 (machine stall, monitoring) |
| **Results** | **The base model's report card exists (MAE 10.65 pp, C5 feasible=False, violations stated). No counterfactual has run. Nothing is a finding about the light rail.** |

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════
• Iteration horizon = 1000 (§9.43, §9.57). • §8.5 = CONSTRAIN-AND-REPORT
(§9.50); ASCs stay priors; **C5 exists, feasible=False with five stated
violations (§9.64)**. • RIDE IS EMERGENT (§9.55); M0+M1 built (§9.60);
**M2 NO-GO on the §9.64 evidence; M3 rejected**. • The §9.58 network/model
family stands (motorway-only exclusion, reverse complements, activity
pinning, person-only SubtourModeChoice). • PassingQ; replanning 20; events
4; oneThreadPerHandler NEVER (§9.59). • The §9.61 measured day-type
factors stay measured. • **The seed floor is ≤0.11 pp/mode (n=2, §9.64)**
— n_replications value awaits the owner. • Freight swept never pinned;
SCATS refused; Opal swept 3–15 min; dwell swept. • Two concurrent arms are
a PROVEN pattern (§9.62/§9.64) but each campaign still needs its own
stated-cost approval.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — new ones first, each paid for
═══════════════════════════════════════════════════════════════════════════════
1. **A slow mobsim is not a dead run.** During the #66 stall the log went
   quiet 36 min while the qsim crawled through the pre-dawn sim-hours —
   check the `SIMULATION (NEW QSim) AT <time>` markers' sim-time progress
   before declaring a stall or killing anything (cost: one false alarm,
   correctly walked back).
2. **The machine-level stall (#66) hits BOTH arms at the same wall-clock
   time** (~35 min, self-recovered, lost=0, once in 2×67 h). It is not a
   model event; correlate with Task Scheduler/Defender if it recurs.
3. **Verified-at-1% is not verified.** The #65 crash class touched ~0.1%
   of persons; a 1%-sample probe had ~6 of them and passed twice. A
   structural invariant needs an ASSERTION in the builder (the contiguity
   check now in `bind_nonhousehold_lifts`), not a probe (cost: two
   crashed 25% launches).
4. **`bind_nonhousehold_lifts` must consult re-targeted sibling times** —
   the stale-rows class behind #65; the assertion guards it now, but any
   new pass that rewrites tours must preserve trip_seq contiguity per
   person (cost: one afternoon).
5. **The driver pins -Xms to -Xmx** — size per-arm heaps for concurrency
   (two 40g arms would commit 80 GiB on 63.5; 30g each is the proven
   §9.62 stack).
6. Carried: `build_matsim_run_inputs.py` subset OVERWRITES the report —
   regenerate ALL scenarios in one invocation. Timing probes never share
   the machine. PowerShell here-strings mangle — use `-F`/`--body-file`.
   `decideOnLink` silently accepts out-of-subnetwork activity links —
   re-verify `ActivityLinkAssigner` coverage on any mode/exclusion change.
   "Fix #NN" in a PR body closes the issue — write "the #NN fix" unless
   closure is intended. The G2 test asserts the `numberOfThreads`
   MULTISET. A `tail -f` monitor holds a Windows lock on the run
   directory. 1% timing says NOTHING about 25%. Car vehicles carry the
   BARE person id. CLEAR a re-moded leg's route. `render_docs`/
   `render_schema` after registry edits. `pkill` fails — `Stop-Process`
   then VERIFY. Branch `<git-handle>/<kebab>`, no attribution, STATUS in
   the same commit.

---

═══════════════════════════════════════════════════════════════════════════════
§9  STATE OF THE PROJECT — THE SIX QUESTIONS (24 August 2026, close)
═══════════════════════════════════════════════════════════════════════════════

### 1. Goals & achievement
Research goal (proposal §1/§3): hypotheses A1–A6, B1–B4 — **none tested**
(no counterfactual has run). Operational goal: physical half **COMPLETE
and campaign-proven**; checked half **has its first honest answer** — the
uncalibrated base misses per-mode ridership by MAE 10.65 pp and realises
37% of LR patronage (§9.64). Proposal §8 deliverables: model 🟡 · data 🟡
(429 files) · calibration report 🟡 (**C5 + report exist**, feasible=False
stated) · paper ⬜ · explorer 🟡 · method note 🟡.

### 2. Phases — 4 of 8, P4 nearly closed
P0 ✅ · P1 ✅ · P2 ✅ · P3 ✅ (regenerated 21 Aug, §9.63 repair) ·
**P4 🟡 (8 of 9 — deliverable 0/0b open, #63)** · P5–P7 ⬜. Home:
[`STATUS.md`](../STATUS.md) phase table.

### 3. Tasks
4.1: 9/9 ✅. 4.2: **all eight done-and-evaluated** (4.2.4 delivered 24 Aug
— C5 from the completed base arm). 4.3 (0b) started; backlog is #63. 4.4
owner-sequenced. Batch 4.5: 4.5.0 ✅ (the campaign, §9.62–§9.64); 4.5.1
build ✅ + measured (ride collapse → the #48 choice lane); 4.5.2 Tier R ✅
(Tier C open); 4.5.3 measured on the new family (mechanism open); 4.5.4
inventory done (modelled table now derivable). P5 0/5 · P6 0/5 · P7 0/4;
the four deletion/rework proposals (5.2/5.3/6.1/6.2) still await the owner.

### 4. Simulator vs real life
The §2 table above IS the latest valid fit (arm A, pre-calibration
constrained base, 35 of 67 targets scorable, MAE 10.65 pp; LR 1,260 vs
3,417 boardings; occupancy 0.0013 vs 0.3503; counts −91.8% structural).
Seed replication (arm B): every mode within 0.11 pp — the gaps are signal.
Full rows: `results/20260821T175907_1000it_25pct/_fit.json` (arm A; ex
`phys1000a_25pct`, renamed §9.65) and
[`docs/audit/CALIBRATION_REPORT.md`](../audit/CALIBRATION_REPORT.md).

### 5. Issue ledger — 42 filed (numbers shared with PRs), 34 closed, 8 open
#48 (ride choice — the lane, evidence 24 Aug) · #30 (walk generation,
re-baselined 24 Aug) · #49 (Tier C + taxi, owner-sequenced) · #50
(modelled table derivable, 24 Aug) · #62/#63 (framework/0b backlogs,
21 Aug) · #65 (repaired in-tree, closes with this PR) · #66 (stall,
monitoring, 24 Aug). Closed this session with evidence + REOPEN IF:
#14, #9, #28, #31.

### 6. PR history, and the next PR
22 merged PRs tell the build story (#1–#3 foundations · #38 audit+rebuild ·
#40 ride pairing · #43 escort+age · #44 first repaired-demand run · #46
freight · #47 calibration decision · #52 motorbike · #53 all-physical ·
#56 stack landing · #58 accounting · #59 events threads · #61 PR-only
convention · #64 walk wedge + lifts + knobs). **This session's PR carries
§9.62–§9.64: the two-arm campaign, the #65 repair, C5 and the close-out.**
The next PR after it: the ride-choice decomposition + whichever scoring
lever the owner picks (`P4: Diagnose and answer the ride choice collapse
(#48)`).

---

### Bootstrap reading, in this order

```
cities/newcastle/docs/STATUS.md                 the board; §3 above is the lane
cities/newcastle/docs/DECISIONS.md §9.62–§9.64  this session, cross-linked
results/20260821T175907_1000it_25pct/_fit.json  the report card, full rows (arm A, renamed §9.65)
cities/newcastle/docs/audit/CALIBRATION_REPORT.md   the generated report
issues #48 #30 #63                              the open lanes
.claude/CLAUDE.md                               conventions + hard constraints
```
