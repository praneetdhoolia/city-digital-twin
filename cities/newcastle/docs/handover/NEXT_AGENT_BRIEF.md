# Brief for the next agent — THE MODEL IS BUILT AND ACTIVATED; ONE DECISION REMAINS: APPROVE THE FIRST F6 ARM

*Updated 25 August 2026, SEVENTH session — a runless documentation-and-tooling
session (§9.79). No model or data value changed, no run was launched, and the
active lane is exactly where the sixth session left it: **the first F6 arm,
awaiting a stated-cost approval.** What this session added is a gate — the
living documents are now pinned to the artefacts that decide them, because an
`/onboard` scan found the front-door `README.md` three phases out of date.*

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
command; believe the output, not the brief. (The sixth-session brief opened by
telling its reader to merge a PR that had already merged, and the reader spent
its first moves disproving its own briefing. That is why this block exists.)

| Fact as of this handoff | Re-derive with |
|---|---|
| **This session's PR was OPEN at handoff.** If still open, merging it and deleting the branch both sides is the first item of unfinished business | `gh pr list --state open` |
| 10 open issues: #82 #73 #68 #66 #63 #62 #50 #49 #48 #30 | `gh issue list --state open` |
| 52 filed · 42 closed · 10 open; 28 PRs merged, 2 closed unmerged, 0 open | `gh issue list --state all` · `gh pr list --state all` |
| **Machine free; no run in progress** | look for a MATSim `java` process; check `results/` mtimes |
| 45 run directories, 14 of them `aborted_*` | `ls -1d results/*/` · `results/INDEX.md` |
| **NO run approval stands. None.** Approvals are spent on use | assume none; ask |

Then the environment gate — **all four must pass, and a failure is your first
work item, not a footnote**:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~2 min, compiles BOTH class trees
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0  (NEW, §9.79)
python src/run/run_signal_probes.py                # all THREE probe cases PASS
```

**⚠ STANDING DIRECTIVES:**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL — none is standing.**
   ~65–67 h per 25%×1000 arm on the PRE-F6 stack; **the F6 stack's pace is
   UNMEASURED at arm scale** (signals + time-variant network + submode routing
   are all new) — watch the first hours. 1%×2 plumbing probes are normal practice.
1a. **LAUNCH with `python run.py --detach ...`** (VERIFIED, #70 closed). A launch
   counts only once `matsim.log` is past `PersonPrepareForSim`.
1b. **CONDITIONAL REPLICATION: arm B launches ONLY if arm A's `_progress.json`
   shows `pace.solo_in_band`.** The declared [217, 253] s/it band was measured on
   the PRE-F6 stack; if F6 paces outside it, that is a measurement to record and
   a band to re-declare, not a failure.
2. **The prime goal: all forms of ridership as close to real life as possible ON
   THEIR OWN; no hardcoding or Newcastle bias; every issue logged on GitHub.**
   The BUILD half is complete. What remains is MEASUREMENT.
3. **Every mode individually in every numbers table** — never an umbrella row.
4. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`**,
   is watched to merge, branch deleted both sides.
5. **Never hand-name a run**; `_run.json` stays the only result gate.
6. **A number you write into `README.md` or `STATUS.md` is a claim about an
   artefact** (§9.79). If your change moves a count, fix the document in the same
   commit and prove it with `check_doc_currency.py --strict`.

**⚠ DECISIONS REQUIRED (unchanged — none was taken this session):**
- **Approve the first F6 arm** (~65–67 h at 25%×1000×WEEKDAY, S2). It re-measures
  EVERYTHING at once — the §9.68/§9.69 ride/walk repairs, the signals, crossings,
  dwell, taxi, submodes, the CWANZ bike rate — jointly. The separate
  repairs-only measurement was forfeited when F5 closed unmeasured (§9.77).
- **`E.replication.n_replications`** — seed floor ≤0.11 pp/mode at n=2 (§9.64);
  3–5 supportable; still awaits a decision.
- **Warm-restart validity** — is a warm-completed arm a valid arm or a
  diagnostic? Caveat recorded (§9.76); ruling still open.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> **A digital twin of any city, traffic-wise ... whether that scaling actually
> predicts the correct ridership per mode must be CHECKED, not assumed. Every
> form of transport should be IN ACTION physically.**

"In action" is **COMPLETE**: every person-transport mode is physical or priced,
and every corridor mechanism (signal timing, tram/bus priority, crossing
closures, charging dwell, submode-distinct PT costs) is explicit, declared,
swept and live in the 30 assembled run-input sets.

"Checked" still has only the **pre-repair** answer (MAE 10.65 pp, passenger
−99.6%, LR −63%). **Every next number is one F6 arm away.**

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — the record (arm A fit, Newcastle LGA, §9.64, PRE-REPAIR)
═══════════════════════════════════════════════════════════════════════════════

The baseline every F6 comparison is made against. Source:
`results/20260821T175907_1000it_25pct/_fit.json` (S2 WEEKDAY 25%×1000, **CLOSED
family F4**, pre-calibration). Each mode against **its own observed value**:

| mode | modelled | observed | vs observed | what changed since (ALL unmeasured) |
|---|---|---|---|---|
| Vehicle driver (car+motorbike) | 73.19 | 59.0 | **+24%** (+14.19 pp) | §9.68 repairs live in F6 |
| Vehicle passenger (ride) | 0.09 | 20.6 | **−99.6%** (−20.51 pp) | §9.68 round-trip bindings live in F6 |
| Walk only | 7.28 | 13.4 | **−46%** (−6.12 pp) | §9.69 short-trip mixture live in F6 |
| Bike ("Other") | 11.21 | 3.2 | **+250%** (+8.01 pp) | CWANZ availability 0.493 live (§9.78); child-ride displacement (#50) re-measures |
| PT aggregate | 8.22 | 3.8 | **+116%** (+4.42 pp) | submode constants now bite in route choice (§9.78) |
| — bus | 6.13 | — | — | Tier R reporting split (§9.58) |
| — rail | 0.77 | — | — | + combos |
| — tram | 0.02 | — | — | |
| — ferry | 0.02 | — | — | C1 declares no ferry constant |
| Light rail | 1,260 boardings | 3,417/day | **−63%** | signals/dwell/priority now MECHANICAL (§9.77); the composition answer is COVERAGE, not frequency (§9.78) |
| Motorbike | 0.21 | locked carve | — | unchanged (§9.52) |
| Truck | swept | never pinned | — | unchanged (§9.49) |
| Taxi/rideshare | **LIVE** (probe 1.4–2.1% at 1%) | 15–25k trips/day band | — | a CONSTRAINT, never a target |

**Fit MAE 10.65 pp across 5 scored mode-share targets. 35 of 67 targets scored;
32 unscorable, each with a stated reason.**

Constraints — checked, never fitted:

| constraint | modelled | observed | inside range? |
|---|---|---|---|
| Vehicle occupancy (pax/driver) | 0.0013 | 0.3503 [0.2493, 0.394] | **NO** |
| Walk trip length | 5.56 km | 0.70 km | **NO — 7.9×** |
| Bike trip length | 8.62 km | 5.20 km | NO — 1.66× |
| Car trip length | 10.94 km | 10.20 km | NO — 1.07× |
| PT trip length | 10.40 km | 23.40 km | NO — 0.44× |
| Ride trip length | 7.84 km | 9.80 km | **YES** |
| Traffic counts (30 stations) | — | — | **−91.8% mean; 6 modelled-zero → #82** |

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

1. **Get the F6 arm approved and launched** (`run.py --detach`, S2 WEEKDAY
   25%×1000; watch `_progress.json`; arm B only on `pace.solo_in_band`).
   **Nothing else moves the project — there is no implementable lane ahead of it.**
2. **On completion**: `_run.json` gates; metrics → fit → the F6 report card;
   re-measure onto #48 #30 #73 #68 #49 #50 **and #82**; the taxi band comparison;
   the corridor composition re-read; C5 regenerates.
3. **Attended-only, if the user is present**: the ABS TableBuilder SA2×SA2 JTW
   extract (#63's last item — needs interactive registration).
4. **Do not start**: movement-level signal lanes (data-gated at 16% turn-lane
   coverage), the census-reader adaptation (#62 follow-up — a pipeline rebuild),
   anything in the backlog.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — do not redo any of it
═══════════════════════════════════════════════════════════════════════════════

- **§9.49–§9.76** (20–25 Aug): the physical model, the two-arm campaign, the
  ride/walk repairs, the SUMO descope, the batch built inert, the harness safety set.
- **§9.77 (25 Aug): THE ACTIVATION.** The §9.76 checklist executed as ONE
  boundary; family F6 declared; 30 sets regenerated; S3 bus-keyed
  (`A.signals.tsp.priority_group`); three probe-caught defects fixed.
- **§9.78 (25 Aug): EVERY RUNLESS LANE.** Tier C submodes (bytecode-verified
  raptor mode mapping; `PtSubmodeMainModeIdentifier` pre-empts the interchange
  crash); seven 0b source upgrades (CWANZ bike 0.493, plans regenerated); the
  corridor-composition ANSWER (coverage, not frequency —
  [`CORRIDOR_PT_COMPOSITION.md`](../audit/CORRIDOR_PT_COMPOSITION.md)); the
  sex-invariance finding ([`DEMOGRAPHIC_MODES.md`](../audit/DEMOGRAPHIC_MODES.md));
  the TIA sweep (EMPTY); #66's stall capture armed; #62's six strata.
- **§9.79 (25 Aug, THIS session): DOCUMENT CURRENCY IS A GATE.** Nine stale
  figures and two false statements corrected across `README.md`, `STATUS.md` and
  `.claude/CLAUDE.md`; **`tests/check_doc_currency.py`** built (portable harness,
  `--strict` gates CI) over city-owned
  [`tests/doc_currency.json`](../../tests/doc_currency.json) (22 claims, two claim
  kinds); **`docs/HANDOVER_CONTRACT.md`** de-duplicates `/onboard` and `/handoff`;
  both skills rewritten; the superseded traffic-count attribution corrected in
  `src/calibrate/report.py` and the residual filed as **#82**.

**Registry 356 fields · hardcoding ledger 0 strict · reach 91/91 · manifest 489 ·
doc-currency 22/22 · agnostic 13/13 (at AUD_2031) · check_city 38/0 · all three
signal probes PASS.**

**Phases:** P0–P3 ✅ · P4 🟡 (deliverable 0/0b: one attended item) · P5–P7 ⬜.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES YOUR WORK
═══════════════════════════════════════════════════════════════════════════════

- **No multi-hour run without explicit approval. None standing.**
- **F6 is the current family** (from launch stamp 20260825T090000); the two CLOSED
  F4 arms are the pre-repair baseline only; **F5 closed with zero arms** — never
  claim a repairs-only measurement exists. NEVER compare across families or
  fractions; regenerate `results/INDEX.md` (`build_run_index.py`), never hand-edit it.
- **F6 is ONE boundary. Do not change the model again before its first arm** —
  every further fold-in was legitimate only while no arm existed. The moment an arm
  runs, the next model change is a NEW family.
- **One representation per effect is ENFORCED in code**:
  `build_scenario_schedules.py` refuses under `explicit_signals`; the builders
  refuse missing/foreign artefacts. Do not bypass a refusal.
- **THE 67/143 SPLIT IS PRE-REGISTERED** — need a holdout? SAY SO AND STOP.
- **One build of the network per comparison** (§3.5); every derived schedule comes
  from the mapped schedule, never the mapper.
- **No invented data**: taxi's band and the TIA numbers are constraints and
  evidence; crossings stay swept; `scats_phasing` stays `unobtained`; the
  ownership→availability step in the CWANZ move stays assumed.
- **A run without `_run.json` is not a result**; warm-started runs carry
  `warm_started_from` and are not bit-identical continuations.
- **Pre-§9.78 run records cannot be scored by the new fit**
  (`intervention_boardings` rename — accepted, recorded; do not "fix" old records).
- **The §8.5-held mode constants stay held.**
- **A dated record is FROZEN** (§9.79). Never rewrite a §14 row or a dated section
  to match today's artefacts to make a check green — that is the reproducibility
  rule running backwards. Only live-state cells are pinned.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE — 25 August 2026, seventh session close
═══════════════════════════════════════════════════════════════════════════════

| | |
|---|---|
| PRs | **THIS session's PR OPEN at handoff — see §0, re-derive it.** 28 merged, 2 closed unmerged |
| Toolchain | JDK 25.0.4+7 · pt2matsim 26.6 · Maven 3.9.9 · signals run stack 2027.0-2026w25 (201 jars, sha256-recorded); both class trees compile |
| Registry | **356 fields**; ledger **0** `--strict`; reach 91/91; G2 13/13 (at AUD_2031); check_city 38/0 |
| Package | **489 manifest files**; `check_manifest` OK; `check_package` **1,433 ALL PASSED** (2 standing warnings), a portable harness over [`package_expectations.json`](../../tests/package_expectations.json) |
| **Documents** | **22/22 doc-currency claims green** (§9.79) over [`doc_currency.json`](../../tests/doc_currency.json); `--strict` gates CI |
| Machine | free; no run in progress |
| Run cost | ~240 s/it/arm two-arm, ~233 s single on the PRE-F6 stack → ~65–67 h per 25%×1000 arm; **the F6 stack's pace is UNMEASURED at arm scale** |
| Runs | two CLOSED F4 arms (valid, pre-repair baseline) · F6 plumbing probes `20260825T094638` (S2 activated), `20260825T101929` (S2 + Tier C), `20260825T103013` (S3 bus priority) · fourteen `aborted_*` (each with a cause-stating `_meta.json`) — **45 directories**, all labelled in `results/INDEX.md` |
| Open issues | **10** (see §0). None implementable in-session: #82 #73 #68 #49 #48 #30 #50 await the F6 arm · #66 awaits the stall's recurrence (capture armed) · #63 attended TableBuilder only · #62 recorded design follow-ups |
| **Results** | **Nothing new is a result.** No F6 arm ran; the pre-repair report card stands; no counterfactual has run; nothing is a finding about the light rail. |

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

• All of the fifth brief's list (MATSim stands §9.73; SUMO descoped §9.74; signal
ladder rungs 2+4; horizon 1000; §8.5; ride emergent; PassingQ; coal not simulated;
freight/Opal/dwell swept; charging dwell concurrent; taxi one blended mode;
free-TIA route; crossings uniform-per-site phase-offset).
• **§9.77 adds**: activate-first (F5's separate measurement forfeited, recorded);
crossings gated by `A.crossings.representation`; bin size 300; S3's priority group
is `corridor`.
• **§9.78 adds**: submodes score-distinct via raptor mode mapping (plan-level choice
stays `pt` — what the jar supports); ferry keeps the aggregate constant; bike
availability 0.493 (CWANZ 2025); the activity-duration derived-identity candidate
REFUSED; `intervention_boardings` rename accepted as a schema break; mid-block
priority extension owes nobody.
• **§9.79 adds**: a live-state figure in a document is a checked claim, and the
check gates CI; **a dated record is exempt and frozen**; the brief is exempt because
`/handoff` rewrites it wholesale; the six state-of-the-project questions have ONE
home (`docs/HANDOVER_CONTRACT.md`), not one per skill; traffic counts stay a
reported constraint and are **not** to be fitted, even though their recorded
justification was superseded (#82).

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each paid for
═══════════════════════════════════════════════════════════════════════════════
1. **Git Bash `/tmp` and Python's `/tmp` are DIFFERENT directories on Windows.**
   `cp x /tmp/bak` in Bash writes the MSYS temp; `open('/tmp/bak')` in Python
   writes `C:\tmp\`. A backup-then-restore across the two silently loses the
   restore and leaves an edited file behind. Use the session scratchpad with an
   absolute path, and verify with `git status` — which is how this one was caught
   before it reached a commit.
2. **MATSim's change-events reader validates against the XSD and the element order
   matters** (flowCapacity BEFORE freespeed). Cost: one aborted probe.
3. **A priority system may have NO competing signal group** (S3's mid-block
   crossings under `priorityGroupId=corridor`) — booking borrowed time against
   `longestCompetingGreen` NPEs on the null key. **Verified-in-toy is not
   verified-in-scenario.**
4. **The stock `AnalysisMainModeIdentifier` THROWS on a trip with two unknown leg
   modes** (any bus+rail interchange under submode mapping) —
   `PtSubmodeMainModeIdentifier` folds submode legs to `pt`; do not remove it while
   `pt_submode_scoring=per_submode`.
5. **An unmapped route transportMode under raptor mode mapping yields a SILENT null
   passenger mode** — `split_schedule` refuses out-of-vocabulary modes at build
   time; keep that refusal.
6. **`run.py --run-config smoke` RESUME-MATCHES an earlier identical probe** and
   reports it complete without running — pass `--force` when the model changed
   underneath.
7. **PowerShell 5.1 `-Encoding utf8` writes a BOM** that breaks JSON readers
   (`city.json` failed check_city on it) — write files via Python.
8. Carried, all still live: a module emitted into the config MUST have its
   ConfigGroup registered on every stack that loads it; the A2 cluster ids are
   mostly not network nodes (radius match, never id lookup); removing the generic
   per-intersection delay over-subtracts on variants with partial removal; the
   signals contrib refuses `usingFastCapacityUpdate=true`; a detached launch is
   verified only by the run's own progress; OSM names differ from official ones;
   `os.kill(pid,0)` on Windows TERMINATES; a slow mobsim is not a dead run;
   verified-at-1% is not verified; `-Xms` pins to `-Xmx`; subset run-input builds
   OVERWRITE the report; PowerShell here-strings mangle (use `--body-file`); "Fix
   #NN" closes issues; `tail -f` holds a Windows directory lock; car vehicles carry
   the bare person id; CLEAR a re-moded leg's route; `render_docs` after registry
   edits; `git status` after every move; branch `<git-handle>/<kebab>`, no
   attribution.

---

═══════════════════════════════════════════════════════════════════════════════
§9  STATE OF THE PROJECT — THE SIX QUESTIONS (25 August 2026, seventh close)
═══════════════════════════════════════════════════════════════════════════════

### 1. Goals & achievement
**Research goal** (proposal §1/§3): hypotheses A1–A6, B1–B4 — **none tested**; no
counterfactual has run. **Operational goal**: the BUILD half is COMPLETE — every
mode physical or priced, every corridor mechanism explicit, declared, swept and
live in F6; the CHECKED half holds only the pre-repair answer (§2).
**Proposal §8 deliverables:** model 🟡 (built, unmeasured on F6) · data 🟡 (489
files) · calibration report 🟡 (C5 pre-repair, `feasible=False`, five stated
violations) · paper ⬜ · explorer 🟡 (replay + live view; no per-scenario explorer)
· method note 🟡 (the SCATS refusal is citable, §9.21).

### 2. Phases — 4 of 8; P4 is one attended item and one arm from closing
P0 ✅ · P1 ✅ · P2 ✅ · P3 ✅ · **P4 🟡 (8 of 9 deliverables; only deliverable 0/0b
open)** · P5 ⬜ · P6 ⬜ · P7 ⬜. Evidence: [`STATUS.md`](../STATUS.md) phase table.

### 3. Tasks
Batches 4.1–4.6 as recorded. **4.7: ALL TEN BUILT**, the model-changing four
ACTIVATED (§9.77). **4.8: ALL NINE DONE** (§9.77/§9.78). **4.9 (this session): ALL
SEVEN DONE** (§9.79) — the STATUS tables are the record. **4.6.9 is the F6 arm,
awaiting approval — the single open task in P4.** P5 0/2 (5.4, 5.5) · P6 0/5 · P7
0/4; the 6.1/6.2 REWORK proposals still await a decision.

### 4. Simulator vs real life
The §2 table (arm A, CLOSED F4 family, pre-calibration, pre-repair) is still the
latest converged fit — **by design: nothing was measured since, and the next number
comes from the F6 arm.** Full rows:
`results/20260821T175907_1000it_25pct/_fit.json` ·
[`CALIBRATION_REPORT.md`](../audit/CALIBRATION_REPORT.md). Two diagnostics sharpen
what that arm must explain:
[`CORRIDOR_PT_COMPOSITION.md`](../audit/CORRIDOR_PT_COMPOSITION.md) (the LR deficit
is a COVERAGE structure — 98.3% of corridor-band demand has an end the 6-stop
alignment cannot reach without an interchange) and
[`DEMOGRAPHIC_MODES.md`](../audit/DEMOGRAPHIC_MODES.md) (the choice model is
sex-invariant where G62 is not). **New this session:** the traffic-count residual
(−91.8%, 6 modelled-zero stations) is now a named open question, **#82**, rather
than an attribution to a cause §9.41 had already addressed.

### 5. Issue ledger — 52 filed, 42 closed, 10 open
All ten gated, none implementable in-session: **#82** (NEW, §9.79 — the count
residual; run-gated) · **#73 #68 #49 #48 #30 #50** await the converged F6 arm ·
**#66** awaits the stall's recurrence (capture armed) · **#63** awaits an attended
ABS TableBuilder session · **#62** holds recorded design follow-ups (census-family
readers, currency-bearing key names), with a comment recording that §9.79 applied
its harness/city-expectations split to a second check.

### 6. PR history, and the next PR
**28 merged PRs** tell the build story (#1–#81), 2 closed unmerged. **This
session's PR: the §9.79 document-currency gate** (see §0 — re-derive its state).
The next PR after it merges: **the F6 arm's close-out**
(`P4: First converged arm on the activated all-modes family`) — there is no other
candidate, and it is blocked only on the approval in §0.

---

### Bootstrap reading, in this order

```
docs/HANDOVER_CONTRACT.md                          the trust order + the six questions
cities/newcastle/docs/STATUS.md                    the board; batches 4.7/4.8/4.9
cities/newcastle/docs/DECISIONS.md §9.77–§9.79     activation, close-out, the doc gate
cities/newcastle/docs/audit/run_families.json      F1–F6, declared
results/INDEX.md                                   every run, labelled (regenerate: build_run_index.py)
results/20260821T175907_1000it_25pct/_fit.json     the pre-repair report card
cities/newcastle/docs/audit/CORRIDOR_PT_COMPOSITION.md   why demand rides buses past the tram
issues #82 #73 #68 #49 #48 #30 #50                 the measurement lanes the arm feeds
.claude/CLAUDE.md                                  conventions + hard constraints
```
