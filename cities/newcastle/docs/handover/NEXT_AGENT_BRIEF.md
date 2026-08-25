# Brief for the next agent — THE MODEL IS BUILT AND ACTIVATED; ONE DECISION REMAINS: APPROVE THE FIRST F6 ARM

*Updated 25 August 2026, EIGHTH session — a runless documentation-and-tooling
session (§9.80). No model or data value changed, no run was launched, and the
active lane is exactly where the sixth session left it: **the first F6 arm,
awaiting a stated-cost approval.** What this session added is a front door that
shows the model's fit instead of describing the package, a requirement that a
dead run state why it died — and **one correction that matters more than either**:
the light rail's boardings had been reported as a −63% error against a target the
model's own fit refuses to score.*

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
command; believe the output, not the brief. **Every count derived from GitHub or
from `results/` lives HERE and nowhere else** — the seventh-session brief also
stated its PR count in §6, and it was wrong before its reader finished the
environment gate.

| Fact as of this handoff | Re-derive with |
|---|---|
| **This session's PR was OPEN at handoff.** If still open, merging it and deleting the branch both sides is the first item of unfinished business | `gh pr list --state open` |
| 11 open issues: #84 #82 #73 #68 #66 #63 #62 #50 #49 #48 #30 | `gh issue list --state open` |
| 53 filed · 42 closed · 11 open; 29 PRs merged, 2 closed unmerged, 0 open | `gh issue list --state all` · `gh pr list --state all` |
| **Machine free; no run in progress** | look for a MATSim `java` process; check `results/` mtimes |
| 45 run directories, 14 of them `aborted_*`, **every one now stating its cause** | `ls -1d results/*/` · the *Why the dead runs died* table in `results/INDEX.md` |
| **NO run approval stands. None.** Approvals are spent on use | assume none; ask |

Then the environment gate — **all of it must pass, and a failure is your first
work item, not a footnote**:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~2 min, compiles BOTH class trees
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
python src/run/run_failure.py --check              # every dead run says WHY (NEW, §9.80)
python src/analyse/build_fit_figures.py --check    # the front door draws the current base (NEW, §9.80)
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
7. **NEVER STATE AN ERROR AGAINST AN UNSCORABLE TARGET** (§9.80, #84). Read
   `_fit.json`'s `unscorable` list before quoting any comparison. A modelled value
   beside an observation the fit declines to score is a **level**, not an error.
8. **If the calibrated base moves, regenerate the front door in the same change**:
   `build_fit_figures.py` then `report.py --run <dir>`. Both follow
   `C5_calibration.json`'s `best_tag`, so they never describe different arms.

**⚠ DECISIONS REQUIRED (unchanged — none was taken this session):**
- **Approve the first F6 arm** (~65–67 h at 25%×1000×WEEKDAY, S2). It re-measures
  EVERYTHING at once — the §9.68/§9.69 ride/walk repairs, the signals, crossings,
  dwell, taxi, submodes, the CWANZ bike rate — jointly. The separate
  repairs-only measurement was forfeited when F5 closed unmeasured (§9.77).
- **`E.replication.n_replications`** — seed floor ≤0.11 pp/mode at n=2 (§9.64);
  3–5 supportable; still awaits a decision.
- **Warm-restart validity** — is a warm-completed arm a valid arm or a
  diagnostic? Caveat recorded (§9.76); ruling still open.
- **NEW (#84): what is the intervention's patronage legitimately checked
  against?** Nothing currently scores it. V001/V002 are a pre-pandemic vintage;
  V003 is the only 2026-appropriate target and it is a MONTHLY total needing
  WEEKDAY + SAT + SUN composed over a calendar month, which no single-day-type
  arm produces. Until that is built, patronage fidelity is unmeasurable and every
  statement about it must say so.

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
−99.6%, walk −46%). **Every next number is one F6 arm away.** The answer is now
also *visible*: `README.md` opens on the three modelled-against-observed figures
rather than on the package's size.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — the record (arm A fit, Newcastle LGA, §9.64, PRE-REPAIR)
═══════════════════════════════════════════════════════════════════════════════

The baseline every F6 comparison is made against. Source:
`results/20260821T175907_1000it_25pct/_fit.json` (S2 WEEKDAY 25%×1000, **CLOSED
family F4**, pre-calibration), now also drawn in
[`docs/reference/figures/`](../reference/figures/) and summarised in
[`FIGURES.json`](../reference/figures/FIGURES.json). Each mode against **its own
observed value**:

| mode | modelled | observed | vs observed | what changed since (ALL unmeasured) |
|---|---|---|---|---|
| Vehicle driver (car+motorbike) | 73.19 | 59.0 | **+14.19 pp** | §9.68 repairs live in F6 |
| Vehicle passenger (ride) | 0.09 | 20.6 | **−20.51 pp** | §9.68 round-trip bindings live in F6 |
| Walk only | 7.28 | 13.4 | **−6.12 pp** | §9.69 short-trip mixture live in F6 |
| Bike ("Other") | 11.21 | 3.2 | **+8.01 pp** | CWANZ availability 0.493 live (§9.78); child-ride displacement (#50) re-measures |
| PT aggregate | 8.22 | 3.8 | **+4.42 pp** | submode constants now bite in route choice (§9.78) |
| — bus | 6.13 | no target | reported, unscored | Tier R reporting split (§9.58) |
| — rail | 0.77 | no target | reported, unscored | + combos |
| — tram | 0.02 | no target | reported, unscored | |
| — ferry | 0.02 | no target | reported, unscored | C1 declares no ferry constant |
| — bus+rail (linked) | 1.08 | no target | reported, unscored | |
| Light rail | **1,260 boardings — A LEVEL** | **nothing scores it** | **NOT an error** | see below; signals/dwell/priority now MECHANICAL (§9.77); the composition answer is COVERAGE, not frequency (§9.78) |
| Motorbike | 0.17 | locked carve | — | unchanged (§9.52) |
| Truck | 3.88 (all-residents basis) | never pinned | swept | unchanged (§9.49) |
| Taxi/rideshare | not in this arm (activated after it) | 15–25k trips/day band | a CONSTRAINT, never a target | probe 1.4–2.1% at 1% |

**Fit MAE 10.65 pp across 5 scored mode-share targets. 35 of 67 targets scored;
32 unscorable, each with a stated reason.** The two dominant errors are near-mirror
pairs — passengers become drivers, walking trips become cycling trips — which is
why they are structural rather than a matter of tuning.

> **THE LIGHT RAIL ROW CHANGED THIS SESSION AND THE OLD VERSION WAS WRONG.**
> Three consecutive briefs, this one's predecessor included, printed
> *"1,260 boardings | 3,417/day | −63%"*. `fit.py` marks V001/V002 **unscorable**:
> March 2019 – February 2020 is a pre-pandemic PT market, PT mode share roughly
> halved before the 2026 base year (§12.1), and V002 is V001 ÷ 30.4 rather than an
> independent datum. `patronage.targets` in `_fit.json` is EMPTY. The modelled
> 1,260 is a level; the −63% was a statistic the model's own fit declines to
> compute. Corrected in §9.80, filed as **#84**, and now banned in the figure
> generator and both session skills. **Do not reintroduce it.**

Constraints — checked, never fitted:

| constraint | modelled | observed | inside range? |
|---|---|---|---|
| Vehicle occupancy (pax/driver) | 0.0013 | 0.3503 [0.2493, 0.394] | **NO** |
| Walk trip length | 5.56 km | 0.70 km [0.7, 1.1] | **NO — 7.94×** |
| Bike trip length | 8.62 km | 5.20 km [3.1, 5.2] | NO — 1.66× |
| Car trip length | 10.94 km | 10.20 km [6.6, 10.8] | NO — 1.07× |
| PT trip length | 10.40 km | 23.40 km [15.9, 24.5] | NO — 0.44× |
| Ride trip length | 7.84 km | 9.80 km [5.6, 9.8] | **YES** (the only one) |
| Traffic counts (30 stations) | — | — | **−91.8% mean; 6 modelled-zero → #82** |

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

1. **Get the F6 arm approved and launched** (`run.py --detach`, S2 WEEKDAY
   25%×1000; watch `_progress.json`; arm B only on `pace.solo_in_band`).
   **Nothing else moves the project — there is no implementable lane ahead of it.**
2. **On completion**: `_run.json` gates; metrics → fit → **then regenerate the
   front door and the calibration report together** (`build_fit_figures.py`,
   `report.py --run <dir>`; both follow C5's `best_tag`) → the F6 report card;
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
- **§9.78 (25 Aug): EVERY RUNLESS LANE.** Tier C submodes; seven 0b source
  upgrades (CWANZ bike 0.493, plans regenerated); the corridor-composition ANSWER
  (coverage, not frequency); the sex-invariance finding; the TIA sweep (EMPTY);
  #66's stall capture armed; #62's six strata.
- **§9.79 (25 Aug): DOCUMENT CURRENCY IS A GATE.** Nine stale figures and two
  false statements corrected; `tests/check_doc_currency.py` built;
  `docs/HANDOVER_CONTRACT.md` de-duplicates the two skills; #82 filed.
- **§9.80 (25 Aug, THIS session): THE FRONT DOOR, THE DEAD-RUN CAUSE, AND ONE
  CORRECTION.**
  - **`src/analyse/build_fit_figures.py`** (NEW) draws mode share, the trip-length
    constraint and the 30 counts from the calibrated base's own run — selected via
    `C5_calibration.json`'s `best_tag`, never the newest directory (usually a
    probe) — as dependency-free light/dark SVG carrying **no wall-clock**, which is
    what lets `--check` gate them in `check_package.py`.
  - **`README.md` rewritten** as a front door: what the project is, **what it
    models** (every mode, and the corridor mechanisms including the explicit signal
    control that replaced the refused SCATS phasing — the old README described
    signals only as an input that could not be obtained, nine days after §9.77 made
    them mechanical), how to set it up, and the fit as figures.
  - **THE CORRECTION (#84)**: the light rail "−63%" — see §2.
  - **`src/run/run_failure.py`** (NEW): `_meta.json` now REQUIRES a `cause` on
    `failed`/`aborted`, read from the run's own `matsim.log`. All 14 dead runs
    backfilled from their logs; the three 25 Aug probe failures independently
    reproduce the §9.77 narrative; `results/INDEX.md` prints every cause.
  - **`check_doc_currency.py`** gains `decimals` and a `text` claim kind (a stale
    NAME was structurally exempt), 10 new README claims, and one stale-statement
    ban covering every phrasing of "the package is not built yet".
  - **`report.py`** gains a patronage section: the modelled level plus every
    patronage-family observation and why none scores.
  - **`P4_CHECKPOINT.md` RETIRED as a live document** and frozen as the 12 August
    record it was; `docs/README.md`, `.claude/CLAUDE.md` and the `DECISIONS.md`
    header corrected.

**Registry 356 fields · hardcoding ledger 0 strict · reach 91/91 · manifest 489 ·
doc-currency 32/32 · agnostic 13/13 · check_city 38/0 · `check_package` ALL PASSED
(2 standing warnings) · all three signal probes PASS.**

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
  every further fold-in was legitimate only while no arm existed.
- **NEVER quote an error against a target `fit.py` marked unscorable** (§9.80,
  #84). Read the `unscorable` list first.
- **One representation per effect is ENFORCED in code**:
  `build_scenario_schedules.py` refuses under `explicit_signals`; the builders
  refuse missing/foreign artefacts. Do not bypass a refusal.
- **THE 67/143 SPLIT IS PRE-REGISTERED** — need a holdout? SAY SO AND STOP.
- **One build of the network per comparison** (§3.5); every derived schedule comes
  from the mapped schedule, never the mapper.
- **No invented data**: taxi's band and the TIA numbers are constraints and
  evidence; crossings stay swept; `scats_phasing` stays `unobtained`.
- **A run without `_run.json` is not a result**; warm-started runs carry
  `warm_started_from` and are not bit-identical continuations.
- **Pre-§9.78 run records cannot be scored by the new fit**
  (`intervention_boardings` rename — accepted, recorded; do not "fix" old records).
- **The §8.5-held mode constants stay held.**
- **A dated record is FROZEN** (§9.79). Never rewrite a §14 row or a dated section
  to match today's artefacts. Where a dated claim actively misleads, **add a
  supersession note where the claim was made** — as §9.80 did to §2.1 — rather
  than editing the claim.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE — 25 August 2026, eighth session close
═══════════════════════════════════════════════════════════════════════════════

| | |
|---|---|
| PRs / issues / runs | **counts live in §0 with their commands** — do not restate them here |
| Toolchain | JDK 25.0.4+7 · pt2matsim 26.6 · Maven 3.9.9 · signals run stack 2027.0-2026w25 (201 jars, sha256-recorded); both class trees compile |
| Registry | **356 fields**; ledger **0** `--strict`; reach 91/91; G2 13/13; check_city 38/0 |
| Package | **489 manifest files**; `check_manifest` OK; `check_package` **ALL PASSED** (2 standing warnings) over [`package_expectations.json`](../../tests/package_expectations.json) |
| **Documents** | **32/32 doc-currency claims green** over [`doc_currency.json`](../../tests/doc_currency.json); `--strict` gates CI. The front door's fit figures are generated and `--check`-gated |
| Machine | free; no run in progress |
| Run cost | ~240 s/it/arm two-arm, ~233 s single on the PRE-F6 stack → ~65–67 h per 25%×1000 arm; **the F6 stack's pace is UNMEASURED at arm scale** |
| Runs | two CLOSED F4 arms (valid, pre-repair baseline) · F6 plumbing probes `20260825T094638` (S2 activated), `20260825T101929` (S2 + Tier C), `20260825T103013` (S3 bus priority) · the `aborted_*` set, **each now stating its cause** in `results/INDEX.md` |
| Open issues | all gated — none implementable in-session: #84 #82 #73 #68 #49 #48 #30 #50 await the F6 arm or a decision · #66 awaits the stall's recurrence · #63 attended TableBuilder only · #62 recorded design follow-ups |
| **Results** | **Nothing new is a result.** No F6 arm ran; the pre-repair report card stands (now drawn on the front page); no counterfactual has run; nothing is a finding about the light rail |

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
• **§9.78 adds**: submodes score-distinct via raptor mode mapping; ferry keeps the
aggregate constant; bike availability 0.493 (CWANZ 2025); the activity-duration
derived-identity candidate REFUSED; `intervention_boardings` accepted as a schema
break.
• **§9.79 adds**: a live-state figure in a document is a checked claim, and the
check gates CI; a dated record is exempt and frozen; the six questions have ONE
home; traffic counts stay a reported constraint, never fitted.
• **§9.80 adds**: the front door SHOWS the fit rather than describing the package;
the figures track the **calibrated base's** run via `C5_calibration.json` so they
and the calibration report can never describe different arms; **no wall-clock in a
generated artefact** (it churns the diff and defeats `--check`); hand-written SVG
rather than a plotting dependency (byte-stability is what makes `--check` a gate);
**a dead run must state a cause, and the cause is read from its own log, never
composed**; a number with no artefact to be pinned to becomes a **pointer to the
thing that always knows** rather than a restated figure; and a living document
that duplicates another's job is **frozen, not refreshed**.

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each paid for
═══════════════════════════════════════════════════════════════════════════════
1. **A modelled value beside an observation is not an error.** Check
   `_fit.json`'s `unscorable` list first. The light rail's "−63%" survived three
   briefs, an audit document and the DECISIONS index because nobody opened the
   reason (§9.80, #84).
2. **A number with no artefact behind it will drift, and pinning is not always
   possible.** Four board cells (a check count, an issue total, a dead-run count,
   a "consolidated from twelve issues") had no artefact; three had already
   drifted. Where there is nothing to pin to, write a pointer, not a figure.
3. **A document that restates another document's job drifts, and refreshing it
   only resets the clock.** `P4_CHECKPOINT.md` restated the board and was wrong on
   nine counts thirteen days later.
4. **A stale-statement ban that names one wording bans one wording.** §9.79 banned
   *"layers pending the #32 re-harvest"*; the same false claim sat in STATUS's
   resume instructions as *"cannot pass until the harvest above is re-run"* and had
   to be found by hand.
5. **`git bash` heredocs eat backslashes.** `\n` inside a Python string in a
   `<<'PY'` heredoc reached the file as a literal newline and broke two source
   files mid-edit. Use the editing tools for backslash-bearing patches, and
   `compileall` immediately after.
6. **Git Bash `/tmp` and Python's `/tmp` are DIFFERENT directories on Windows.**
   Use the session scratchpad with an absolute path, and verify with `git status`.
7. **MATSim's change-events reader validates against the XSD and element order
   matters** (flowCapacity BEFORE freespeed). Cost: one aborted probe.
8. **A priority system may have NO competing signal group** (S3's mid-block
   crossings) — booking borrowed time against `longestCompetingGreen` NPEs on the
   null key. **Verified-in-toy is not verified-in-scenario.**
9. **The stock `AnalysisMainModeIdentifier` THROWS on a trip with two unknown leg
   modes** — `PtSubmodeMainModeIdentifier` folds submode legs to `pt`; do not
   remove it while `pt_submode_scoring=per_submode`.
10. **An unmapped route transportMode under raptor mode mapping yields a SILENT
   null passenger mode** — `split_schedule` refuses out-of-vocabulary modes at
   build time; keep that refusal.
11. **`run.py --run-config smoke` RESUME-MATCHES an earlier identical probe** —
   pass `--force` when the model changed underneath.
12. **PowerShell 5.1 `-Encoding utf8` writes a BOM** that breaks JSON readers —
   write files via Python.
13. Carried, all still live: a module emitted into the config MUST have its
   ConfigGroup registered on every stack that loads it (this is what killed
   `aborted_20260825T033406`); the A2 cluster ids are mostly not network nodes;
   removing the generic per-intersection delay over-subtracts on variants with
   partial removal; the signals contrib refuses `usingFastCapacityUpdate=true`; a
   detached launch is verified only by the run's own progress; OSM names differ
   from official ones; `os.kill(pid,0)` on Windows TERMINATES; a slow mobsim is
   not a dead run; verified-at-1% is not verified; `-Xms` pins to `-Xmx`; subset
   run-input builds OVERWRITE the report; PowerShell here-strings mangle (use
   `--body-file`); "Fix #NN" closes issues; `tail -f` holds a Windows directory
   lock; car vehicles carry the bare person id; CLEAR a re-moded leg's route;
   `render_docs` after registry edits; `git status` after every move; branch
   `<git-handle>/<kebab>`, no attribution.

---

═══════════════════════════════════════════════════════════════════════════════
§9  STATE OF THE PROJECT — THE SIX QUESTIONS (25 August 2026, eighth close)
═══════════════════════════════════════════════════════════════════════════════

### 1. Goals & achievement
**Research goal** (proposal §1/§3): hypotheses A1–A6, B1–B4 — **none tested**; no
counterfactual has run. **Operational goal**: the BUILD half is COMPLETE — every
mode physical or priced, every corridor mechanism explicit, declared, swept and
live in F6; the CHECKED half holds only the pre-repair answer (§2), now visible on
the front page. **Proposal §8 deliverables:** model 🟡 (built, unmeasured on F6) ·
data 🟡 (489 files) · calibration report 🟡 (C5 pre-repair, `feasible=False`, five
stated violations; **now also reports patronage as a level with why nothing scores
it**) · paper ⬜ · explorer 🟡 (replay + live view; the README's generated figures
are the first published view of fit) · method note 🟡 (the SCATS refusal is
citable, §9.21).

### 2. Phases — 4 of 8; P4 is one attended item and one arm from closing
P0 ✅ · P1 ✅ · P2 ✅ · P3 ✅ · **P4 🟡 (8 of 9 deliverables; only deliverable 0/0b
open)** · P5 ⬜ · P6 ⬜ · P7 ⬜. Evidence: [`STATUS.md`](../STATUS.md) phase table.

### 3. Tasks
Batches 4.1–4.6 as recorded. **4.7: ALL TEN BUILT**, the model-changing four
ACTIVATED (§9.77). **4.8: ALL NINE DONE** (§9.77/§9.78). **4.9: ALL SEVEN DONE**
(§9.79). **4.10 (this session): ALL SEVEN DONE** (§9.80) — the STATUS tables are
the record. **4.6.9 is the F6 arm, awaiting approval — the single open task in
P4.** P5 0/2 (5.4, 5.5) · P6 0/5 · P7 0/4; the 6.1/6.2 REWORK proposals still
await a decision.

### 4. Simulator vs real life
The §2 table (arm A, CLOSED F4 family, pre-calibration, pre-repair) is still the
latest converged fit — **by design: nothing was measured since, and the next number
comes from the F6 arm.** Full rows:
`results/20260821T175907_1000it_25pct/_fit.json` ·
[`CALIBRATION_REPORT.md`](../audit/CALIBRATION_REPORT.md) · the figures in
[`docs/reference/figures/`](../reference/figures/). **The patronage row is a level,
not an error** — nothing scores it (§9.80, #84). Two diagnostics sharpen what that
arm must explain: [`CORRIDOR_PT_COMPOSITION.md`](../audit/CORRIDOR_PT_COMPOSITION.md)
(the LR deficit is a COVERAGE structure — 98.3% of corridor-band demand has an end
the 6-stop alignment cannot reach without an interchange) and
[`DEMOGRAPHIC_MODES.md`](../audit/DEMOGRAPHIC_MODES.md) (the choice model is
sex-invariant where G62 is not). The traffic-count residual (−91.8%, 6
modelled-zero) is **#82**.

### 5. Issue ledger
Counts are in **§0** with their command. All open issues are gated, none
implementable in-session: **#84** (NEW, §9.80 — the unscorable-target correction;
its remaining substance is the open decision on what patronage is checked against)
· **#82** (the count residual; run-gated) · **#73 #68 #49 #48 #30 #50** await the
converged F6 arm · **#66** awaits the stall's recurrence (capture armed) · **#63**
awaits an attended ABS TableBuilder session · **#62** holds recorded design
follow-ups.

### 6. PR history, and the next PR
The merged sequence tells the build story from the P1 data package through the
network rebuild, the physical-mode campaign, the two-arm run, the ride/walk
repairs, the SUMO descope, the F6 activation and the document-currency gate — see
`gh pr list --state merged`. **This session's PR: the front door, the dead-run
cause and the unscorable-target correction** (see §0 — re-derive its state). The
next PR after it merges: **the F6 arm's close-out**
(`P4: First converged arm on the activated all-modes family`) — there is no other
candidate, and it is blocked only on the approval in §0.

---

### Bootstrap reading, in this order

```
docs/HANDOVER_CONTRACT.md                          the trust order + the six questions
README.md                                          what is modelled, and the fit, in pictures
cities/newcastle/docs/STATUS.md                    the board; batches 4.7-4.10
cities/newcastle/docs/DECISIONS.md §9.77-§9.80     activation, close-out, the doc gate, the front door
cities/newcastle/docs/audit/run_families.json      F1-F6, declared
results/INDEX.md                                   every run, labelled, with why the dead ones died
results/20260821T175907_1000it_25pct/_fit.json     the pre-repair report card - READ ITS unscorable LIST
cities/newcastle/docs/audit/CORRIDOR_PT_COMPOSITION.md   why demand rides buses past the tram
issues #84 #82 #73 #68 #49 #48 #30 #50             the measurement lanes the arm feeds
.claude/CLAUDE.md                                  conventions + hard constraints
```
