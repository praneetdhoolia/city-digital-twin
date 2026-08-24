# Brief for the next agent — BATCH 4.7 IS BUILT (INERT); THE TWO §0 DECISIONS NOW DECIDE EVERYTHING

*Updated 25 August 2026, fifth session — the OVERNIGHT BUILD session (§9.76):
the whole 25 Aug batch was implemented. The harness safety set is LIVE (warm
restart #75, the `_progress.json` digest #76, the cross-run index #77, and the
detached launch `run.py --detach` — VERIFIED past `PersonPrepareForSim` with
the launching shell gone, closing #70). The SUMO descope is EXECUTED (#72)
with Maven + the MATSim signals run stack pinned (§14). The model-changing
set is BUILT INERT for ONE family boundary: crossings (#68), native charging
dwell (#74, concurrent-with-boarding decided), explicit signals + the
tram-priority controller with BOTH toy probes passing (#73), taxi as a
blended priced mode on the archived Fares Order 2025 (#49). Six 0b fields
moved onto measurement; PPSHCC-137 archived under the decided free-TIA route
(#78). **The assembled 4.6.9 run inputs are BYTE-IDENTICAL; no scenario ran;
nothing is a result.** This is a HANDOVER, not a source of truth: where it
disagrees with [`STATUS.md`](../STATUS.md), [`DECISIONS.md`](../DECISIONS.md)
or [`.claude/CLAUDE.md`](../../../../.claude/CLAUDE.md), those win.*

---

═══════════════════════════════════════════════════════════════════════════════
§0  DO THIS FIRST
═══════════════════════════════════════════════════════════════════════════════

**Run `/onboard`**; at session end, `/handoff`. The checks:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~2 min, compiles BOTH stacks
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
python src/run/run_signal_probes.py                # both signal toy probes PASS
```

**⚠ STANDING DIRECTIVES:**

1. **NO MULTI-HOUR RUNS WITHOUT EXPLICIT APPROVAL — none is standing.**
   ~65–67 h per 25%×1000 arm. (1% × 2-iteration plumbing probes are normal
   practice and need none.)
1a. **LAUNCH with `python run.py --detach ...`** — the Task Scheduler path
   whose lifetime is independent of the launching shell, VERIFIED (§9.76;
   #70 closed). A launch still counts only once `matsim.log` is past
   `PersonPrepareForSim` into iterations; watch the first arm-scale detached
   launch anyway — the §9.72 deaths were never attributed.
1b. **CONDITIONAL REPLICATION (standing): arm B launches ONLY if arm A's
   solo iterations 2–5 pace inside the declared band** — now mechanised:
   read `pace.solo_in_band` in the run's own `_progress.json`.
2. **The prime goal: all forms of ridership as close to real life as
   possible ON THEIR OWN; no hardcoding or Newcastle bias; every issue
   logged on GitHub.** All modes covered first — DONE in build (§9.76);
   what remains is measurement.
3. **Every mode individually in every numbers table** — never an umbrella.
4. **Never commit directly to `main`; the session's ONE PR opens at
   `/handoff`**, is watched to merge, branch deleted both sides.
5. **Never hand-name a run**; `_run.json` stays the only result gate.

**Start from `main`. If this session's PR is still open, merging it and
deleting the branch both sides is the first item of unfinished business.**

**⚠ DECISIONS REQUIRED (unchanged in substance, sharpened by the build):**
- **Re-approve the 4.6.9 arm** (~65–67 h; §9.72's approval is SPENT) **and
  pick the order**: run the repairs arm FIRST on the byte-identical inputs
  (clean §9.68/§9.69 attribution, then ONE activation boundary) vs activate
  the built batch first (saves one arm, confounds the repair measurement).
  §9.76's closing block is the ACTIVATION CHECKLIST either way.
- **`E.replication.n_replications`** — seed floor ≤0.11 pp/mode at n=2
  (§9.64); 3–5 supportable; awaits a decision.
- **Warm-restart validity** — is a warm-completed arm a valid arm or a
  diagnostic? The caveat is recorded (§9.76); the ruling is not.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> **A digital twin of any city, traffic-wise ... whether that scaling
> actually predicts the correct ridership per mode must be CHECKED, not
> assumed. Every form of transport should be IN ACTION physically.**

"In action physically" is DONE and campaign-proven (§9.64). "Checked" still
has only the pre-repair answer (MAE 10.65 pp, passenger −99.6%); the
§9.68/§9.69 repairs AND now the §9.76 batch (signals, crossings, dwell,
taxi) are all BUILT and UNMEASURED. Every next number is a run away.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — the CLOSED family's record (arm A fit, Newcastle LGA, §9.64)
═══════════════════════════════════════════════════════════════════════════════

Unchanged from the fourth brief — the pre-repair baseline every next-arm
comparison is made against (vs its own observed value, not pp):

| mode | modelled | observed | vs observed | what changed since |
|---|---|---|---|---|
| Vehicle driver | 73.19 | 59.0 | +24% | §9.68 repairs built, unmeasured |
| Vehicle passenger | 0.09 | 20.6 | **−99.6%** | §9.68 repairs built, unmeasured |
| Walk only | 7.28 | 13.4 | −46% | §9.69 mixture built, unmeasured |
| Bike | 11.21 | 3.2 | +250% | displaced child ride demand (#50) |
| PT aggregate | 8.22 | 3.8 | +116% | corridor composition lane open |
| Light rail | 1,260 | 3,417 boardings | −63% | §9.76: signals/dwell/priority now MECHANICAL when activated |
| Motorbike | 0.21 | locked carve | — | not a choice mode (§9.52) |
| Truck | swept | never pinned | — | freight physical (§9.49) |
| Taxi/rideshare | **BUILT, inert** | 15–25k trips/day band | — | §9.76: priced mode ready; band is a CONSTRAINT, never a target |

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

1. **Surface the §0 decisions.** Nothing else moves the project like them.
2. **On a yes**: launch with `run.py --detach` per the chosen order; watch
   `_progress.json` (`pace.solo_in_band` gates arm B). If activation is
   chosen first, execute §9.76's activation checklist as ONE boundary with
   its own DECISIONS entry, regenerate the run-input sets, and probe at 1%
   before any arm.
3. **Cheap and open meanwhile**: the PT corridor-composition diagnostic on
   the CLOSED arms (why demand rides buses past the tram); #63's attended
   acquisitions (TableBuilder JTW; the CWANZ bike-ownership domain
   decision); #62's remaining strata (A2/A5/B1/B4/B5); #73's movement-level
   lanes if turn-lane data ever justifies them.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — do not redo any of it
═══════════════════════════════════════════════════════════════════════════════

- **§9.49–§9.75** (20–25 Aug): everything the fourth brief listed — the
  physical model, the walk wedge, the two-arm campaign, the ride-lever
  answer, the §9.68/§9.69 repairs, the framework survey, the descope
  decision, the signalling dossier.
- **§9.76 (25 Aug, overnight): THE WHOLE 25 AUG BATCH IS BUILT — do not
  rebuild any of it.** Per-task state is the STATUS batch-4.7 table.
  Everything model-changing is INERT: `A.signals.representation` =
  `implicit_delay`, taxi absent from the two vocabularies, the assembled
  sets byte-identical. The activation checklist is §9.76's closing block.
- **Issues closed by §9.76**: #70, #72, #74, #75, #76, #77, #78.
- **Registry 352 fields, ledger 0 strict; manifest 489, `check_package`
  1,430 ALL PASSED; both signal toy probes PASS; agnostic gate 13/13.**

**Phases:** P0–P3 ✅ · P4 🟡 (deliverable 0/0b open #63) · P5–P7 ⬜.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES YOUR WORK
═══════════════════════════════════════════════════════════════════════════════

- **No multi-hour run without explicit approval. None standing.**
- **The comparability family is §9.68/§9.69 onward**; the CLOSED family's two
  arms are before-vs-after only. NEVER compare across families or fractions;
  the cross-run index (`results/INDEX.md`) labels both — regenerate it, never
  hand-edit it, and a NEW family is declared in
  `docs/audit/run_families.json` in the same change as its DECISIONS entry.
- **The built batch activates as ONE boundary** (§9.75/§9.76): flip
  `A.signals.representation`, add `taxi` to `RUN.mode_choice.modes` AND
  `RUN.routing.network_modes`, `bin_size_s` ≤300,
  `usingFastCapacityUpdate=false` for signal runs, regenerate the run-input
  sets from the derived artefacts, author the boundary's DECISIONS entry.
  Activating pieces separately creates uncomparable fragments.
- **One representation per effect is now ENFORCED in code**:
  `build_scenario_schedules.py` refuses to run under `explicit_signals`; the
  signal generator removes each variant's OWN embedded delay. Do not bypass
  either refusal.
- **THE 67/143 SPLIT IS PRE-REGISTERED** — need a holdout? SAY SO AND STOP.
- **One build of the network per comparison** (§3.5); every derived schedule
  (dwell, signals) comes from the mapped schedule, never the mapper.
- **No invented data**: taxi's band and the TIA numbers are constraints and
  evidence; crossing closures stay swept; `scats_phasing` stays `unobtained`.
- **A run without `_run.json` is not a result**; warm-started runs carry
  `warm_started_from` and are NOT bit-identical continuations (§9.76).
- **The §8.5-held mode constants stay held.**

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE — 25 August 2026, fifth session close
═══════════════════════════════════════════════════════════════════════════════

| | |
|---|---|
| PRs | **THIS session's PR (the §9.76 build) OPEN at handoff** — merge + delete both sides is the first item of unfinished business; 26 prior merged, 2 closed unmerged |
| Toolchain | JDK 25.0.4+7 · pt2matsim 26.6 · Maven 3.9.9 · signals run stack 2027.0-2026w25 (201 jars, all sha256-recorded); SUMO REMOVED (§14); both class trees compile |
| Registry | **352 fields**; ledger **0** `--strict`; G2 13/13 |
| Package | **489 manifest files**; `check_manifest` OK; `check_package` **1,430 ALL PASSED** (2 standing warnings) |
| Machine | free; no run in progress |
| Run cost | ~240 s/it/arm two-arm, ~233 s single → ~65–67 h per 25%×1000 arm |
| Runs | the two CLOSED-family arms (valid) · probes incl. the §9.76 detached-launch probe `20260825T033850_2it_1pct` · twelve `aborted_*` (incl. the unmaterialised-module probe, cause recorded) |
| Open issues | **9**: #73 #68 #49 (built inert; activation/measurement/lanes) · #48 #30 (await the converged arm) · #50 · #62 · #63 · #66 |
| **Results** | **Nothing new is a result.** No arm ran; the pre-repair report card stands; no counterfactual has run; nothing is a finding about the light rail. |

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════
• All of the fourth brief's list (MATSim stands §9.73; SUMO descoped §9.74;
taxi resequenced §9.75; signal ladder rungs 2+4 not 3; horizon 1000; §8.5;
ride emergent; PassingQ; coal not simulated; freight/Opal/dwell swept).
• **§9.76 adds**: charging dwell CONCURRENT with boarding (not additive);
signals at LINK level while turn-lane coverage is 16% (movement lanes open,
not silently faked); each signal variant's schedule loses ITS OWN embedded
delay, not the generic 26 s; taxi is ONE blended mode (measured taxi fares +
literature rideshare at the IPART split), ASC swept, band a constraint; the
free-TIA route (no LX purchase) per the session directive; crossings closures
uniform-per-site and phase-offset between sites.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — new ones first, each paid for
═══════════════════════════════════════════════════════════════════════════════
1. **This MATSim REFUSES an unmaterialised config module** ("Unmaterialized
   config group: tramPriority") — a module emitted into the config MUST have
   its ConfigGroup registered on EVERY stack that loads it. Cost: one dead
   detached probe. `TramPriorityConfigGroup` therefore lives in `src/java/`.
2. **The A2 cluster ids are stop-line OSM nodes, mostly NOT network nodes**
   (12 of 14 intersections keep none) — junction matching is a radius over
   car-carrying nodes, never an id lookup.
3. **Removing the GENERIC per-intersection delay over-subtracts on variants
   whose schedules already carry partial removal** (S2b went negative) — the
   amount to remove is the variant's OWN `mean_delay_to_tram_s`.
4. **The signals contrib refuses `qsim.usingFastCapacityUpdate=true`** — an
   activation config requirement, checked by the contrib at install time.
5. **A detached launch is verified only by the run's own progress** — the
   first §9.76 probe died in 10 s for a REAL reason and only the run
   directory said why. `results/_launch/<task>.log` holds the launcher side.
6. **OSM names differ from official ones** ("Saint James Road" vs "St James
   Road") — declared names must be the NETWORK's spelling, and the fare
   dossier's $5.17/$2.61 were not in the instrument: verify against the
   archived document, not the note that cites it.
7. Carried, all still live: `os.kill(pid,0)` on Windows TERMINATES; a slow
   mobsim is not a dead run; verified-at-1% is not verified; -Xms pins to
   -Xmx; subset run-input builds OVERWRITE the report; PowerShell
   here-strings mangle (use `--body-file`); "Fix #NN" closes issues; `tail
   -f` holds a Windows directory lock; car vehicles carry the bare person
   id; CLEAR a re-moded leg's route; `render_docs` after registry edits;
   `git status` after every move; branch `<git-handle>/<kebab>`, no
   attribution.

---

═══════════════════════════════════════════════════════════════════════════════
§9  STATE OF THE PROJECT — THE SIX QUESTIONS (25 August 2026, fifth close)
═══════════════════════════════════════════════════════════════════════════════

### 1. Goals & achievement
Research goal (proposal §1/§3): A1–A6, B1–B4 — **none tested** (no
counterfactual has run). The B1 fallback now has its INSTRUMENT
(`frontage_volumes.py`, 4.7.10). Operational goal: physical half COMPLETE;
checked half awaits the 4.6.9 arm; the all-modes-first corollary is BUILT
(§9.76). Proposal §8 deliverables: model 🟡 · data 🟡 (489 files) ·
calibration report 🟡 (C5, feasible=False) · paper ⬜ · explorer 🟡 ·
method note 🟡.

### 2. Phases — 4 of 8, P4 nearly closed
P0 ✅ · P1 ✅ · P2 ✅ · P3 ✅ · **P4 🟡 (deliverable 0/0b open #63)** ·
P5–P7 ⬜. Home: [`STATUS.md`](../STATUS.md) phase table.

### 3. Tasks
4.1/4.2/4.5/4.6 as the fourth brief recorded; **4.6.9 ⬜ AWAITING
RE-APPROVAL + the ordering call**. **Batch 4.7: 4.7.1–4.7.10 ALL BUILT
(§9.76)** — harness set LIVE, model set INERT awaiting the ONE activation
boundary. P5 0/2 remaining (5.4, 5.5) · P6 0/5 · P7 0/4; 6.1/6.2 REWORK
proposals still await a decision (4.7.10's instrument informs 6.1).

### 4. Simulator vs real life
The §2 table is the latest CONVERGED fit (arm A, closed family,
pre-calibration, pre-repair). Nothing measured since — by design: the next
number comes from the 4.6.9 arm. Full rows:
`results/20260821T175907_1000it_25pct/_fit.json` ·
[`docs/audit/CALIBRATION_REPORT.md`](../audit/CALIBRATION_REPORT.md).

### 5. Issue ledger — 51 filed, 42 closed, 9 open
**§9.76 closed #70 #72 #74 #75 #76 #77 #78.** Open: #73/#68/#49 (built
inert — activation, lanes, Tier C, measurement) · #48/#30 (need the
converged arm) · #50 (acquisition) · #62 (A1 half landed) · #63 (attended
acquisitions + remainder) · #66 (stall watch).

### 6. PR history, and the next PR
26 merged PRs tell the build story (#1–#79 as the fourth brief lists, plus
#79's merge). **This session's PR (open at this handoff): the §9.76 batch
build.** The next PR after it merges: whatever the §0 decisions dictate —
either the 4.6.9 arm's close-out or the activation boundary
(`P4: Activate the all-modes batch as one comparability family`).

---

### Bootstrap reading, in this order

```
cities/newcastle/docs/STATUS.md                    the board; the batch table is 4.7
cities/newcastle/docs/DECISIONS.md §9.76           the overnight build record + activation checklist
cities/newcastle/docs/DECISIONS.md §9.73–§9.75     the decisions the build executed
results/INDEX.md                                   every run, labelled (regenerate: build_run_index.py)
results/20260821T175907_1000it_25pct/_fit.json     the pre-repair report card
issues #73 #68 #49 #48 #30                         the open lanes
.claude/CLAUDE.md                                  conventions + hard constraints
```
