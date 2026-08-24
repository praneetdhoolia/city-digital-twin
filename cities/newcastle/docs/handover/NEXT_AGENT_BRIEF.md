# Brief for the next agent — BATCH 4.7 IS SET (ALL MODES FIRST); TWO OPEN DECISIONS DECIDE THE ORDER

*Updated 25 August 2026, fourth session — a research-and-decisions session:
**no model, data or registry value changed, no run was made.** MATSim was
re-affirmed against the 2026 field and the embedded MATSim version recorded
(§9.73); **SUMO was descoped by recorded decision — MATSim is the single
simulator** (§9.74; execution is #72); the ten-file signalling dossier landed
at [`design/signalling/`](../design/signalling/README.md) with operated SCATS
history for two non-modelled Newcastle sites discovered public (#78); and
**batch 4.7 was ticked** — corridor signals + tram priority + lanes
(#73), taxi (#49, resequenced), level crossings (#68), native charging dwell
(#74), descope execution (#72), warm restart (#75), progress digest (#76),
cross-run index (#77), sweep-basis sharpening (4.7.9) — to be implemented
next session, activating as **ONE family boundary**. The §9.72 record stands:
the 4.6.9 arm is launch-blocked, not model-blocked, and its approval is
SPENT. This is a HANDOVER, not a source of truth: where it disagrees with
[`STATUS.md`](../STATUS.md), [`DECISIONS.md`](../DECISIONS.md) or
[`.claude/CLAUDE.md`](../../../../.claude/CLAUDE.md), those win.*

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

**⚠ STANDING DIRECTIVES:**

1. **NO MULTI-HOUR RUNS WITHOUT EXPLICIT APPROVAL — none is standing.**
   Measured cost: ~240 s/it/arm two-arm, ~233 s single → **~65–67 h per
   25%×1000 arm**.
1a. **LAUNCH CONSTRAINT (§9.72, #70): launch arms from a user-controlled
   shell** — session-spawned launches died silently by BOTH detachment
   routes tried. A launch is verified only when `matsim.log` progresses PAST
   `PersonPrepareForSim` into iterations with the launching context gone.
1b. **CONDITIONAL REPLICATION (standing): arm B launches ONLY if arm A's
   solo iterations 2–5 pace at the closed family's 217–253 s/it band.**
2. **The prime goal: all forms of ridership as close to real life as
   possible ON THEIR OWN; no hardcoding or Newcastle bias; every issue
   logged on GitHub; all traffic forms at observed or academically studied
   values.** The 25 Aug corollary: **all modes covered first** — batch 4.7.
3. **Every mode individually in every numbers table** — never a "public
   transport" umbrella row.
4. **Never commit directly to `main`; the session's ONE PR opens at
   `/handoff`**, is watched to merge, branch deleted both sides.
5. **Never hand-name a run.** `<launch>_<iterations>it_<pct>pct`, status in
   `_meta.json`; `_run.json` stays the only result gate.

**Start from `main`. No run is in progress; the machine is free. If this
session's PR is still open, merging it and deleting the branch both sides is
the first item of unfinished business.**

**⚠ DECISIONS REQUIRED:**
- **Re-approve the 4.6.9 arm** (~65–67 h at 25%×1000; §9.72's approval is
  spent; #70's launch-shell constraint applies) **and pick the order against
  batch 4.7**: run the repairs arm FIRST (clean attribution of §9.68/§9.69,
  then one batch boundary) vs fold the batch in first (saves one arm,
  confounds the repair measurement). §9.75 states the tension; either way
  the batch activates as ONE boundary.
- **`E.replication.n_replications`** — seed floor ≤0.11 pp/mode at n=2
  (§9.64); 3–5 supportable; the value awaits a decision.
- **Operated SCATS data (#78)**: the ~AU$200 LX purchase (licence vs the
  reproducibility gate — quarantine as validation-only or don't buy) and
  the free TIA-harvest lane. Recommended now regardless: archive TIA
  PPSHCC-137 against link rot.
- Flagged, not changed (§9.71): `C.vot.by_purpose.HE` 9.3 and
  `C.vot.concession_factor` 0.75 sit outside their sweeps vs EPV Jan 2025.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> **A digital twin of any city, traffic-wise ... whether that scaling
> actually predicts the correct ridership per mode must be CHECKED, not
> assumed. Every form of transport should be IN ACTION physically.**

"In action physically" is DONE and campaign-proven (§9.64). "Checked" has the
pre-repair answer (MAE 10.65 pp, passenger −99.6%) and a built,
probe-verified counter-move (§9.68/§9.69) whose converged effect is
UNMEASURED — the 4.6.9 arm's job. **New since 24 Aug: MATSim is the single
simulator (§9.74)** — every corridor supply effect (signals, priority, dwell,
crossings, lane loss) now lands natively, which is what batch 4.7 builds.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — the CLOSED family's record (arm A fit, Newcastle LGA, §9.64)
═══════════════════════════════════════════════════════════════════════════════

The last converged measurement — the PRE-repair baseline every next-arm
comparison is made against (vs its own observed value, not pp):

| mode | modelled | observed | vs observed | diagnosis, and what changed since |
|---|---|---|---|---|
| Vehicle driver | 73.19 | 59.0 | +24% | carries displaced ride; §9.68 repairs the supply side |
| Vehicle passenger | 0.09 | 20.6 | **−99.6%** | §9.68 repairs BUILT in the demand, unmeasured at convergence |
| Walk only | 7.28 | 13.4 | −46% | §9.69 short-trip mixture BUILT, unmeasured at convergence |
| Bike | 11.21 | 3.2 | +250% | displaced child ride demand (#50 table); §9.68 covers that population first |
| PT aggregate | 8.22 | 3.8 | +116% | bus 6.13 / rail 0.77 / tram 0.02 / ferry 0.02 — corridor composition lane open |
| Light rail | 1,260 | 3,417 boardings | −63% | corridor composition; EPV bus–LR transfer 3.8 equiv-min anchors inside the 3–15 sweep; #73 makes the signal side mechanical |
| Motorbike | 0.21 | locked carve | — | not a choice mode (§9.52) |
| Truck | swept | never pinned | — | freight physical (§9.49); Mayfield cap 1,268/day a constraint (§9.70) |
| Taxi/rideshare | not modelled | 15–25k trips/day band | — | becomes a priced mode in 4.7.8 (#49, §9.75); band is a constraint, never a target |

Occupancy 0.0013 vs 0.3503 (repair probe's pairing-implied 0.12 at seed
state). Counts −91.8% structural. Seed noise floor ≤0.11 pp/mode (n=2).

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE — batch 4.7, in build order
═══════════════════════════════════════════════════════════════════════════════

1. **Surface the §0 decisions** — chiefly the 4.6.9 re-approval AND
   the ordering call (repairs-arm-first vs fold-in).
2. **Build the harness safety set first: 4.7.1 warm restart (#75), 4.7.2
   progress digest (#76), 4.7.3 run index (#77)** — no model change, no
   boundary, and 4.7.1 must exist before ANY 65 h arm runs.
3. **4.7.4 descope execution (#72)** — registry/toolchain/checks/manifest;
   a logged §14 toolchain change; invalidates nothing.
4. **Build the model-changing set INERT: 4.7.5 crossings (#68), 4.7.6 dwell
   (#74), 4.7.7 signals+priority+lanes (#73), 4.7.8 taxi (#49)** — code,
   registry fields, derivations and toy probes, WITHOUT touching the
   assembled 4.6.9 run inputs; activation happens at the single batch
   boundary per the project's ordering call. 4.7.7 is the big one: Maven run
   stack (§14 entry), saturation-flow re-capacitation (double-count rule),
   per-green discharge check, `QSignalsNetworkFactory` toy probe.
5. **4.7.9 sweep-basis sharpening + 4.7.10 frontage analyser** — cheap,
   docs/registry/analysis only.
6. Still cheap and open on the CLOSED arms while anything runs: the PT
   corridor composition diagnostic (why demand rides buses past the tram).

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — do not redo any of it
═══════════════════════════════════════════════════════════════════════════════

- **§9.49–§9.72** (20–24 Aug, PRs #56/#58/#59/#64/#67/#69/#71): everything
  physical; the walk wedge; lifts; the two-arm campaign; C5; runner-named
  runs; the rename; the ride-lever decomposition + repairs (§9.68/§9.69);
  coal chain scoped out (§9.70); pre-LR lanes 2→1 + EPV check (§9.71); the
  §9.72 launch-death record.
- **§9.73 (25 Aug): the framework survey is DONE — do not re-run it.**
  MATSim re-affirmed; POLARIS/BEAM/GPU/commercial verdicts recorded; the
  pinned jar verified to embed MATSim **2027.0-2026w25**; DSim watch-only.
- **§9.74 (25 Aug): the SUMO descope is DECIDED** — do not re-litigate;
  #72 executes it. Deliverable 7/§9.16 retired; P5 5.1/5.2 deleted; 5.3
  resolved to stays-swept.
- **§9.75 (25 Aug): the signalling dossier is COMPLETE** at
  [`design/signalling/`](../design/signalling/README.md) — SCATS mechanics
  head-to-toe (file 09's closure checklist), the MATSim signals contrib
  mapped (file 04), algorithms in pseudo-code (file 05), data-availability
  map (files 03/07/08). Do not re-research SCATS; read the dossier.
  `scats_phasing` STAYS `unobtained` for the 14 modelled sites.
- **Issues #72–#78 filed 25 Aug** carrying the batch's scope; #49 and #68
  updated with the resequencing and the Stewart-Ave/boom-gate evidence.
- **Regeneration + verification (24 Aug)**: B2/plans/30 run-input sets on
  §9.68/§9.69; manifest 436; `check_package` ALL PASSED; probe
  `20260824T210040_2it_1pct` rc=0, returns pair 347/347.

**Phases:** P0–P3 ✅ · P4 🟡 (deliverable 0/0b open #63; deliverable 7
retired §9.74) · P5–P7 ⬜.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES YOUR WORK
═══════════════════════════════════════════════════════════════════════════════

- **No multi-hour run without explicit approval. None standing.**
- **The comparability family is §9.68/§9.69 onward**; the two completed
  arms (`20260821T175907_1000it_25pct`, `20260821T180310_1000it_25pct`) are
  the CLOSED family's record — before-vs-after only. NEVER compare across
  families or fractions; `target_lga_pct`, never `all_residents_pct`.
- **Batch 4.7's model changes activate as ONE family boundary** (§9.75) —
  building them inert is fine; activating them piecemeal creates
  uncomparable fragments. The boundary's DECISIONS entry is authored at
  activation.
- **The signals build has four recorded traps (§9.75)**: the double-count
  rule (explicit signals meter saturation-flow approaches; the implicit
  `A.signals` delay comes OUT of the same movements — one representation
  per effect); the sample-discretisation check (0–2 vehicles per short
  green at 25% — verify per-green discharge before trusting any effect);
  the `QSignalsNetworkFactory` single-binding toy probe before any
  scenario; Stewart Avenue is a T-aspect signal site, never a boom-gate
  closure (#68 and #73 must not double-treat it).
- **THE 67/143 SPLIT IS PRE-REGISTERED** — `fit.py` enforces; need a
  holdout? SAY SO AND STOP.
- **One build of the network per comparison** (§3.5); threads are run
  identity (§9.56/§9.59). Per-day-type/variant schedules derive from the
  mapped schedule — the dwell work (4.7.6) uses exactly this rule.
- **No invented data**: the TIA numbers are cited evidence, not inputs,
  until acquired with provenance (#78); who-drives-whom stays unobserved;
  crossing closure logs are unpublished — swept, never pinned.
- **A run without `_run.json` is not a result**; `aborted_*` means
  disregard.
- **The §8.5-held mode constants stay held** (§9.68 measured the ASC is not
  ride's lever).

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE — 25 August 2026, fourth session close
═══════════════════════════════════════════════════════════════════════════════

| | |
|---|---|
| PRs | **THIS session's PR (docs + issues: §9.73–§9.75, the dossier landing, batch 4.7) OPEN at handoff** — merging it and deleting the branch both sides is the first item of unfinished business; 25 prior merged, 2 closed unmerged |
| Toolchain | 3 pinned, unchanged this session (SUMO's removal is #72, next session); 13 Java sources compile; the jar embeds MATSim 2027.0-2026w25 (§9.73) |
| Registry | **341 fields**, unchanged; ledger **0** `--strict`; G2 13/13 |
| Package | **436 manifest files**, unchanged; `check_manifest` OK; `check_package` ALL PASSED (24 Aug, 2 standing warnings) |
| Machine | **free**; no run in progress |
| Run cost | ~240 s/it/arm two-arm, ~233 s single → ~65–67 h per 25%×1000 arm |
| Runs | unchanged from §9.72's record: two CLOSED-family arms (valid) · the §9.68 probe · prior probes · eleven `aborted_*` |
| Open issues | **16**: #72–#78 (NEW, §9.75) · #70 · #48 · #30 · #49 · #50 · #62 · #63 · #66 · #68 |
| **Results** | **Nothing new is a result.** No run this session; the pre-repair report card stands as the closed family's record; no counterfactual has run; nothing is a finding about the light rail. |

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════
• **MATSim stands; migration rejected on a documented survey (§9.73).**
• **SUMO descoped; MATSim the single simulator (§9.74)** — S-b native via
#73 (a band regardless), reliability variance a stated limitation,
deliverable 7 retired. • **Taxi resequenced into 4.7 (§9.75)** — supersedes
§9.42's after-deliverable-5 gate; still a priced mode, never a fleet sim.
• **Signal ladder: rungs 2+4 ticked, rung 3 (SCATS emulator) NOT ticked.**
• Iteration horizon 1000 (§9.43). • §8.5 constrain-and-report; C5
feasible=False; the ASC is not ride's lever (§9.68). • RIDE IS EMERGENT;
M2 un-built; M3 rejected. • PassingQ; replanning 20; events 4. • Seed floor
≤0.11 pp/mode; n_replications awaits a decision. • Coal trains NOT simulated
(§9.70). • `pre_lr_lanes_per_dir` = 1 (§9.71). • Freight swept never
pinned; SCATS refused (§9.21) and `scats_phasing` unobtained; Opal swept
3–15 min; dwell swept 10–35 s. • Two concurrent arms proven; every campaign
needs its own stated-cost approval.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — new ones first, each paid for
═══════════════════════════════════════════════════════════════════════════════
1. **A directory move can silently delete a tracked framework file.** The
   dossier's move out of `docs/` deleted `docs/README.md` in the working
   tree; caught and restored at handoff. `git status` after every move.
2. **A detached launch from the agent session is not a launch** (§9.72,
   #70): both routes tried died silently within minutes. Launch from an
   interactive shell outside the agent session; verify past `PersonPrepareForSim`. Cost: two dead
   launches and a campaign evening.
3. **Survivorship bias in converged-run diagnostics** — decompose over the
   SEARCH-phase population, never the survivors (cost: the §9.64 wrong
   lever).
4. **A seed probability can BE a converged ceiling** (0.2 car seed = the
   0.196 pairing ceiling) — check coherence-critical seeds explicitly.
5. **Per-person budgets break paired allocations** — pending-ledger pattern
   (cost: one killed regen).
6. **The Bash tool's 10-min cap kills backgrounded builds silently** —
   detach long builds; for RUNS superseded by trap 2.
7. **`git add -A` in the repo root can commit a stray task artefact** —
   check `git status` before wide adds.
8. Carried, all still live: `os.kill(pid,0)` on Windows TERMINATES; a slow
   mobsim is not a dead run; the #66 stall hits both arms at one
   wall-clock; verified-at-1% is not verified; `bind_nonhousehold_lifts`
   busy checks read re-targeted sibling times; -Xms pins to -Xmx; subset
   run-input builds OVERWRITE the report; PowerShell here-strings mangle
   (use `--body-file`); "Fix #NN" closes issues; `tail -f` holds a Windows
   directory lock; car vehicles carry the bare person id; CLEAR a re-moded
   leg's route; `render_docs` after registry edits; branch
   `<git-handle>/<kebab>`, no attribution.

---

═══════════════════════════════════════════════════════════════════════════════
§9  STATE OF THE PROJECT — THE SIX QUESTIONS (25 August 2026, fourth close)
═══════════════════════════════════════════════════════════════════════════════

### 1. Goals & achievement
Research goal (proposal §1/§3): A1–A6, B1–B4 — **none tested** (no
counterfactual has run). B3's counterfactual input is on evidence (§9.71);
S-b's home moved from SUMO to the native #73 build (§9.74/§9.75).
Operational goal: physical half COMPLETE; checked half awaits the 4.6.9
arm on the built §9.68/§9.69 repairs. Proposal §8 deliverables: model 🟡 ·
data 🟡 (436 files) · calibration report 🟡 (C5, feasible=False) · paper ⬜
· explorer 🟡 · method note 🟡 (gains the reliability-variance limitation,
§9.74).

### 2. Phases — 4 of 8, P4 nearly closed
P0 ✅ · P1 ✅ · P2 ✅ · P3 ✅ (regenerated 24 Aug on §9.68/§9.69) · **P4 🟡
(8 of 9 — deliverable 0/0b open #63; deliverable 7 RETIRED §9.74)** ·
P5–P7 ⬜ (P5's SUMO tasks deleted/reworked §9.74). Home:
[`STATUS.md`](../STATUS.md) phase table.

### 3. Tasks
4.1/4.2/4.5 ✅. 4.3 (0b): §9.61+§9.71 done; backlog #63 (4.7.9 takes the
sweep-basis items). 4.6: 4.6.1–4.6.6, 4.6.10, 4.6.11 ✅ · 4.6.7 → 4.7.5 ·
4.6.8 → 4.7.8 (resequenced §9.75) · **4.6.9 ⬜ AWAITING RE-APPROVAL +
the ordering call**. **Batch 4.7 (NEW, §9.75): 4.7.1–4.7.10 all ⬜ — the
next session's work, harness set first, model set built inert.** P5 0/2
remaining (5.4, 5.5) · P6 0/5 · P7 0/4; deletion/rework proposals: 5.2/5.3
RESOLVED by §9.74; 6.1/6.2 still await a decision (4.7.10 informs 6.1).

### 4. Simulator vs real life
The §2 table is the latest CONVERGED fit (arm A, closed family,
pre-calibration, pre-repair). Nothing measured since. Full rows:
`results/20260821T175907_1000it_25pct/_fit.json` ·
[`docs/audit/CALIBRATION_REPORT.md`](../audit/CALIBRATION_REPORT.md) ·
`_ride_choice.json` · `_mode_by_demographics.json`.

### 5. Issue ledger — 51 filed (numbers shared with PRs), 35 closed, 16 open
**#72–#78 NEW 25 Aug** (descope execution · signals+priority+lanes · dwell ·
warm restart · digest · index · SCATS data acquisition — decision required) · #70 (launch
constraint) · #48/#30 (repairs built, converged measurement open) · #49
(taxi → 4.7.8) · #50 (mode × age acquisition) · #62 · #63 · #66 (stall
watch) · #68 (crossings → 4.7.5; boom gates verified in OSM).

### 6. PR history, and the next PR
25 merged PRs tell the build story (#1–#3 foundations · #38 audit+rebuild ·
#40 ride pairing · #43 escort+age · #44 first repaired-demand run · #46
freight · #47 calibration decision · #52 motorbike · #53 all-physical · #56
stack landing · #58 accounting · #59 events threads · #61 PR-only
convention · #64 walk wedge + lifts + knobs · #67 two-arm campaign + C5 +
rename · #69 the ride-lever answer · #71 the launch-death record). **This
session's PR (open at this handoff): §9.73–§9.75, the signalling dossier,
issues #72–#78, batch 4.7 on the board.** The next PR after it merges:
batch 4.7's build (`P4: Build the all-modes batch — signals, taxi,
crossings, dwell, harness safety (#73 #49 #68 #74 #72 #75 #76 #77)`) — with
the 4.6.9 ordering per an open decision.

---

### Bootstrap reading, in this order

```
cities/newcastle/docs/STATUS.md                    the board; batch 4.7 is the lane
cities/newcastle/docs/DECISIONS.md §9.73–§9.75     this session's record
cities/newcastle/docs/design/signalling/README.md  the dossier (read 06 then 04 before #73)
results/20260821T175907_1000it_25pct/_fit.json     the pre-repair report card
issues #72–#78, #48, #30, #68                      the open lanes
.claude/CLAUDE.md                                  conventions + hard constraints
```
