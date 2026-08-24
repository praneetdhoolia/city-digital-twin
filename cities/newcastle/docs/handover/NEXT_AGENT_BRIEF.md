# Brief for the next agent — THE RIDE COLLAPSE IS DIAGNOSED AND REPAIRED IN THE BUILD; THE NEXT ARM MEASURES WHAT IT BOUGHT

*Updated 24 August 2026, second session (the owner's `/goal`: every mode's
ridership as close to real life as possible, ride first, all traffic forms
at observed values, everything fixable fixed before the next run).
**§9.68** the ride collapse decomposed on the completed arms and repaired
in the demand build (round-trip serve bindings, coherent seeds, direct
bound tours) · **§9.69** the missing short-trip mass gets its observed
distribution (HTS Sydney 2012/13 Table 4.4.7) · **§9.70** the coal chain
deliberately NOT simulated (dedicated grade-separated track); the two real
level-crossing interactions are #68 · **§9.71** the pre-LR cross-section
measured from OSM history (2 → 1 lanes/direction — B3's counterfactual
onto evidence) and the VoT set checked against EPV Jan 2025. The demand
package is REGENERATED and probe-verified: **a NEW comparability family —
the §9.58–§9.63 family closed with its two completed arms as the
pre-repair record.** This is a HANDOVER, not a source of truth: where it
disagrees with [`STATUS.md`](../STATUS.md), [`DECISIONS.md`](../DECISIONS.md)
or [`.claude/CLAUDE.md`](../../../../.claude/CLAUDE.md), those win.*

---

═══════════════════════════════════════════════════════════════════════════════
§0  DO THIS FIRST
═══════════════════════════════════════════════════════════════════════════════

**Run `/onboard`**; at session end, `/handoff`. The checks:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~1 min, compiles the Java
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
```

**⚠ OWNER DIRECTIVES, standing:**

1. **NO MULTI-HOUR RUNS WITHOUT EXPLICIT APPROVAL — none is standing.**
   The §9.62 two-arm approval was consumed by the completed campaign; the
   24 Aug `/goal` authorised BUILD work, not a run. Measured cost:
   ~240 s/it/arm two-arm, ~233 s single → **~65–67 h per 25%×1000 arm**.
2. **The prime goal (owner, 21 + 24 Aug): all forms of ridership as close
   to real life as possible ON THEIR OWN; no hardcoding or Newcastle bias;
   every issue spotted logged on GitHub; all traffic forms at observed or
   academically studied values.**
3. **Every mode individually in every numbers table** — never a "public
   transport" umbrella row.
4. **Never commit directly to `main`; the session's ONE PR opens at
   `/handoff`**, is watched to merge, branch deleted both sides.
5. **Never hand-name a run.** The harness names runs
   `<launch>_<iterations>it_<pct>pct` and status-tracks them in
   `_meta.json`; `_run.json` stays the only result gate.

**Start from `main`. No run is in progress; the machine is free.**

**⚠ DECISIONS WAITING ON THE OWNER:**
- **Approve the next base arm** on the repaired demand (task 4.6.9,
  ~65–67 h at 25%×1000; the §9.68/§9.69 repairs are built and
  probe-verified but UNMEASURED at convergence).
- **`E.replication.n_replications`** — seed floor measured ≤0.11 pp/mode
  at n=2 (§9.64); 3–5 supportable; the value is the owner's.
- Flagged, not changed (§9.71): `C.vot.by_purpose.HE` 9.3 and
  `C.vot.concession_factor` 0.75 sit outside their sweeps against EPV
  Jan 2025's only comparators.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> **A digital twin of any city, traffic-wise ... whether that scaling
> actually predicts the correct ridership per mode must be CHECKED, not
> assumed. Every form of transport should be IN ACTION physically.**

"In action physically" is DONE and campaign-proven (§9.64). "Checked" has
its first honest answer — the pre-repair base missed by MAE 10.65 pp with
passenger at −99.6% of its observed value — **and now, for the first time,
a mechanically complete counter-move**: the decomposition (§9.68) showed
the collapse was one-directional lift supply + seed decoherence, both
repaired in the build and verified in a probe (return legs pair 347/347
vs 2/2,818 before). **What the repairs BUY at convergence is unmeasured**
— that is the next arm's job, and the honest expectation is a large but
partial recovery (round-trip coverage is bounded by the observed serve
rate: ~51k of ~150k weekday passenger tours).

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — the CLOSED family's record (arm A fit, Newcastle LGA, §9.64)
═══════════════════════════════════════════════════════════════════════════════

The last converged measurement — the PRE-repair baseline every next-arm
comparison is made against (vs its own observed value, not pp):

| mode | modelled | observed | vs observed | diagnosis, and what changed since |
|---|---|---|---|---|
| Vehicle driver | 73.19 | 59.0 | +24% | carries displaced ride; §9.68 repairs the supply side |
| Vehicle passenger | 0.09 | 20.6 | **−99.6%** | §9.68: returns unserved (0.0079 pairing) + seed p(car)=0.2 was the 0.196 ceiling — REPAIRED in build, unmeasured at convergence |
| Walk only | 7.28 | 13.4 | −46% | §9.69: the ≤1 km trip mass was never generated (4.45% vs 18.8% observed) — REPAIRED in build |
| Bike | 11.21 | 3.2 | +250% | #50 table: children ride 46–50% bike / 0% ride — displaced child ride demand; §9.68 covers exactly that population first |
| PT aggregate | 8.22 | 3.8 | +116% | bus 6.13 / rail 0.77 / tram 0.02 / ferry 0.02 — composition wrong on the corridor; UNTOUCHED this session (lane open) |
| Light rail | 1,260 | 3,417 boardings | −63% | the corridor composition lane; EPV bus–LR transfer 3.8 equiv-min (§9.71) is an official anchor inside the 3–15 sweep |
| Motorbike | 0.21 | locked carve | — | not a choice mode (§9.52) |
| Truck | swept | never pinned | — | freight physical (§9.49); Mayfield cap 1,268/day recorded as an upper-bound constraint (§9.70) |

Occupancy 0.0013 vs 0.3503 (the §9.68 probe's pairing-implied occupancy
is 0.12 at seed state). Counts −91.8% structural (no-through-demand,
recorded). Seed noise floor ≤0.11 pp/mode (n=2).

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE — in order
═══════════════════════════════════════════════════════════════════════════════

1. **Bring the owner the §0 decisions** — chiefly the next-arm approval:
   without it nothing else can be measured.
2. **Launch the next base arm** (4.6.9) on the regenerated demand —
   25% × 1000 × WEEKDAY (+ replication per the owner's n_replications
   choice). It re-baselines EVERY mode at once: ride vs 20.6, walk vs
   13.4, bike vs 3.2, driver vs 59.0, the LR boardings, occupancy.
3. **PT composition on the corridor** — why demand rides buses past the
   tram (frequency? the transfer point? access stubs?): the diagnostic
   closest to the study's own question, cheap to start on the CLOSED
   arms' events while the new arm runs.
4. **#68 level crossings** (designed §9.70) — build it BEFORE the arm
   after next, or accept another family boundary.
5. Then by recorded order: #49 Tier C + taxi 4.4 (evidence complete on
   the issue), #63 remainder, #62.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — do not redo any of it
═══════════════════════════════════════════════════════════════════════════════

- **§9.49–§9.67** (20–24 Aug, PRs #56/#58/#59/#64/#67): everything
  physical; the walk wedge; lifts M0/M1; the two-arm campaign; C5;
  runner-named, status-carded runs; the city-digital-twin rename.
- **§9.68** (24 Aug, this PR): `src/analyse/decompose_ride_choice.py` +
  `_ride_choice.json` on arm A (absent 76,986 / scored-out 109 /
  selected 531); round-trip binding in BOTH binder passes
  (`B.activity.escort_binding_directions`, household pending-pickup
  ledger, non-household all-or-nothing two-driver pairs, same driver
  preferred); `escort_binding_direct_tour`; `B.mode.serve_tour_seed=car`
  (guarded: carless escorts keep the uninformed draw) and
  `bound_passenger_seed=ride`; `liftHousehold` comma-list through
  `RidePairingEngine` and `sample_population`; `B2_escort_bindings_<day>.csv`
  new, `B2_lift_bindings_<day>.csv` gains `direction`.
- **§9.69** (24 Aug, this PR): the two-component gravity mixture —
  `short_trip_band_share` (literature, Table 4.4.7), `short_trip_band_km`
  (held fixed), `short_trip_mean_km` (derived from the held walk mean);
  weights solved per purpose, long kernels re-solved; build report shows
  every band target hit EXACTLY with every mean preserved.
- **§9.70** (24 Aug, this PR): coal chain scoped OUT on observed
  infrastructure (ARTC/PWCS/NCIG, ~110 movements/day on dedicated track);
  #68 filed for the two level crossings; Mayfield truck cap a constraint.
- **§9.71** (24 Aug, this PR): `pre_lr_lanes_per_dir` 2 → 1 from the
  Overpass attic record (raw responses + provenance landed under
  `data/raw/osm_attic/`, ODbL); EPV Jan 2025 check recorded.
- **#50's modelled table** (`src/analyse/mode_by_demographics.py`,
  `_mode_by_demographics.json` on arm A).
- **Regeneration + verification**: B2/plans/30 run-input sets; manifest
  436; `check_package` ALL PASSED; G2 13/13; probe
  `20260824T210040_2it_1pct` rc=0, accounting closes, pair rate 0.9988
  at it-2 with returns 347/347.

**Phases:** P0–P3 ✅ · P4 🟡 (8 of 9 — deliverable 0/0b open, #63) ·
P5–P7 ⬜.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES YOUR WORK
═══════════════════════════════════════════════════════════════════════════════

- **No multi-hour run without owner approval. None standing.**
- **The comparability family is §9.68/§9.69 onward** — the regenerated
  demand. The two completed arms (`20260821T175907_1000it_25pct`,
  `20260821T180310_1000it_25pct`) are the CLOSED §9.58–§9.63 family's
  record: compare the next arm's fit against their table as
  before-vs-after, never as same-family runs. NEVER compare across
  families or fractions; `target_lga_pct`, never `all_residents_pct`.
- **THE 67/143 SPLIT IS PRE-REGISTERED** — `fit.py` enforces; need a
  holdout? SAY SO AND STOP.
- **One build of the network per comparison** (§3.5); threads are run
  identity (§9.56/§9.59).
- **No invented data**: who-drives-whom stays unobserved (the round-trip
  allocation re-aims the observed rate, adds no tour); closure logs for
  #68 are unpublished — swept, never pinned.
- **A run without `_run.json` is not a result**; `aborted_*` means
  disregard.
- **The §8.5-held mode constants stay held** — §9.68 measured that the
  ASC was never the lever (109 flippable persons); do not re-open it
  without the post-repair arm's evidence.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE — 24 August 2026, second session close
═══════════════════════════════════════════════════════════════════════════════

| | |
|---|---|
| PRs | **the session PR merged as #69** (§9.68–§9.71) and the branch is deleted both sides — the handoff is complete; **24 merged**, 2 closed unmerged, none open |
| Toolchain | 3 pinned, unchanged; 13 Java sources compile (RidePairingEngine touched: comma-list liftHousehold) |
| Registry | **341 fields**; ledger **0** `--strict`; G2 13/13 |
| Package | **436 manifest files**; `check_manifest` OK; `check_package` ALL PASSED (2 standing warnings) |
| Machine | **free**; no run in progress |
| Run cost | ~240 s/it/arm two-arm, ~233 s single → ~65–67 h per 25%×1000 arm |
| Runs | the two CLOSED-family arms (valid, pre-repair record) · the §9.68 verification probe `20260824T210040_2it_1pct` (probe, not a result) · prior probes and nine `aborted_*` as recorded on the board |
| Open issues | **8**: #48 (repair built, converged measurement open) · #30 (mechanism built, re-measure open) · #49 (Tier C + taxi; evidence complete) · #50 (mode × age acquisition) · #62 · #63 (0b remainder) · #66 (stall watch) · #68 (NEW: level crossings) |
| **Results** | **Nothing new is a result.** The pre-repair report card (MAE 10.65 pp) stands as the closed family's record; the repairs are probe-verified builds; no counterfactual has run; nothing is a finding about the light rail. |

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════
• Iteration horizon = 1000 (§9.43); the innovation-cutoff residual is
declared uncertainty — the measured search creep at cutoff on the closed
arms was ~0.26 pp/100 it decaying, and an evidence-triggered cutoff is the
eventual instrument, deferred until the structure settles. • §8.5 =
constrain-and-report; C5 exists feasible=False; **the ASC is measured NOT
to be ride's lever (§9.68)**. • RIDE IS EMERGENT; M0+M1+round-trip built;
M2 stays un-built (round-trip answers returns within the observed rate);
M3 rejected. • The §9.58 network family stands; PassingQ; replanning 20;
events 4. • Seed floor ≤0.11 pp/mode; n_replications awaits the owner.
• Coal trains deliberately NOT simulated (§9.70 — dedicated track; adding
them would fabricate an interaction). • `pre_lr_lanes_per_dir` = 1
(measured §9.71; sweep keeps 2). • Freight swept never pinned; SCATS
refused; Opal swept 3–15 min (EPV's bus–LR 3.8 equiv-min is an anchor
INSIDE it); dwell swept. • Two concurrent arms are proven; each campaign
needs its own stated-cost approval.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — new ones first, each paid for
═══════════════════════════════════════════════════════════════════════════════
1. **Survivorship bias in converged-run diagnostics.** "100% of surviving
   ride requests pair" read as "supply is fine" cost the §9.64 session
   the correct lever: selection had already killed every plan whose
   requests could NOT pair. Decompose over the SEARCH-phase population
   (plan memories, per-iteration counters), never the survivors.
2. **A seed probability can BE a converged ceiling.** The uniform seed
   gave serve tours car with p=0.2; outbound pairing converged at 0.196.
   When a two-sided coordination needs both agents' selected plans to
   align, MATSim's independent selection cannot climb past the seed —
   check coherence-critical seeds explicitly.
3. **Per-person budgets break paired allocations.** Requiring drop+pickup
   from one escorter's drawn budget would have collapsed household
   binding (most draw exactly one HX tour) — the pending-ledger pattern
   (household scope, like `claimed`) is the fix. Cost: one killed regen.
4. **The Bash tool's 10-min cap kills backgrounded builds silently** —
   launch long builds detached (`Start-Process` + log) and chain
   downstream steps on pid exit + output freshness, not on hope. Cost:
   one B2 build killed mid-lift-pass and restarted.
5. **`git add -A` in the repo root can commit a stray task artefact** —
   check `git status` before wide adds (cost: one revert commit).
6. Carried, all still live: `os.kill(pid,0)` on Windows TERMINATES;
   a slow mobsim is not a dead run; the #66 stall hits both arms at one
   wall-clock; verified-at-1% is not verified (assertions, not probes);
   `bind_nonhousehold_lifts` busy checks read re-targeted sibling times;
   -Xms pins to -Xmx; subset run-input builds OVERWRITE the report;
   PowerShell here-strings mangle (use `--body-file`); "Fix #NN" closes
   issues; `tail -f` holds a Windows directory lock; car vehicles carry
   the bare person id; CLEAR a re-moded leg's route; `render_docs` after
   registry edits; branch `<git-handle>/<kebab>`, no attribution.

---

═══════════════════════════════════════════════════════════════════════════════
§9  STATE OF THE PROJECT — THE SIX QUESTIONS (24 August 2026, second close)
═══════════════════════════════════════════════════════════════════════════════

### 1. Goals & achievement
Research goal (proposal §1/§3): A1–A6, B1–B4 — **none tested** (no
counterfactual has run); B3's counterfactual input moved onto evidence
(§9.71). Operational goal: physical half COMPLETE; checked half has the
pre-repair report card (MAE 10.65 pp) AND a built, probe-verified repair
awaiting its converged measurement. Proposal §8 deliverables: model 🟡 ·
data 🟡 (436 files) · calibration report 🟡 (C5, feasible=False) ·
paper ⬜ · explorer 🟡 · method note 🟡.

### 2. Phases — 4 of 8, P4 nearly closed
P0 ✅ · P1 ✅ · P2 ✅ · P3 ✅ (regenerated 24 Aug on §9.68/§9.69) ·
**P4 🟡 (8 of 9 — deliverable 0/0b open, #63)** · P5–P7 ⬜. Home:
[`STATUS.md`](../STATUS.md) phase table.

### 3. Tasks
4.1: 9/9 ✅. 4.2: all eight ✅. 4.3 (0b): §9.61 + §9.71 done; backlog #63.
4.4: evidence complete, build owner-sequenced. 4.5: campaign ✅. **4.6
(the owner's 24 Aug goal): 4.6.1–4.6.6, 4.6.10, 4.6.11 ✅ · 4.6.7 (#68)
designed ⬜ · 4.6.8 (taxi) evidence-complete ⬜ · 4.6.9 (the next arm)
⬜ AWAITING OWNER APPROVAL.** P5 0/5 · P6 0/5 · P7 0/4; the four
deletion/rework proposals (5.2/5.3/6.1/6.2) still await the owner.

### 4. Simulator vs real life
The §2 table above is the latest CONVERGED fit (arm A, closed family,
pre-calibration, pre-repair). The §9.68 probe is a 2-iteration
verification, not a fit. Full rows:
`results/20260821T175907_1000it_25pct/_fit.json` ·
[`docs/audit/CALIBRATION_REPORT.md`](../audit/CALIBRATION_REPORT.md) ·
`_ride_choice.json` and `_mode_by_demographics.json` beside it.

### 5. Issue ledger — 43 filed (numbers shared with PRs), 35 closed, 8 open
#48 (evidence 24 Aug, converged measurement open) · #30 (evidence 24 Aug,
re-measure open) · #49 (evidence 24 Aug) · #50 (modelled half DONE 24 Aug)
· #62 (21 Aug) · #63 (two items measured 24 Aug) · #66 (monitoring) ·
#68 (NEW 24 Aug). #65 closed with PR #67's merge.

### 6. PR history, and the next PR
23 merged PRs tell the build story (#1–#3 foundations · #38 audit+rebuild
· #40 ride pairing · #43 escort+age · #44 first repaired-demand run · #46
freight · #47 calibration decision · #52 motorbike · #53 all-physical ·
#56 stack landing · #58 accounting · #59 events threads · #61 PR-only
convention · #64 walk wedge + lifts + knobs · #67 two-arm campaign + C5 +
runner-named runs + rename). **The session PR (open at this handoff)
carries §9.68–§9.71.** The next PR after it merges: the post-repair base
arm's launch-watch-close-out (`P4: Run the repaired-demand base arm and
re-measure every mode (#48, #30)`) — gated on the owner's approval.

---

### Bootstrap reading, in this order

```
cities/newcastle/docs/STATUS.md                    the board; batch 4.6 is the lane
cities/newcastle/docs/DECISIONS.md §9.68–§9.71     this session, cross-linked
results/20260821T175907_1000it_25pct/_fit.json     the pre-repair report card
results/20260821T175907_1000it_25pct/_ride_choice.json   the decomposition
cities/newcastle/demand/plans/_activity_chains_report.json  band + coverage diagnostics
issues #48 #30 #68 #63                             the open lanes
.claude/CLAUDE.md                                  conventions + hard constraints
```
