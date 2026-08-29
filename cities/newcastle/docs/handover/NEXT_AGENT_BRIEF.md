# Brief for the next agent — THE YARDSTICK WAS THE DEFECT, THE GATE WAS READING A TRANSIENT, AND FIVE MECHANISMS WERE ASSERTED WITHOUT MEASUREMENT

*Updated 30 August 2026, FOURTEENTH session (§9.100–§9.115) — a diagnosis session. The
iteration-100 gate fired with 9 of 11 fittable modes past 20%. **Three yardstick defects
were found and fixed** (another city's light rail stop, a broken bus series, a truck
target compared against the wrong population). **Then the gate itself was found to be
reading a transient**: car, walk and pt are all converging and arrive between iterations
200 and 350. **The real defect is upstream in the demand** — 42.4% of ride legs are
unservable at iteration 0. Two fixes are identified, measured and deliberately NOT
applied, because both cross a family boundary. **Five causes were asserted from
plausible mechanisms and later refuted; three reached committed entries before that
happened.***

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
| **This session's PR is OPEN and is the first item of unfinished business** | `gh pr list --state open` · `gh pr checks <n>` |
| Open issues, including **#92 #93 #94 filed this session** | `gh issue list --state open` |
| Issue / PR totals | `gh issue list --state all` · `gh pr list --state all` |
| **Machine FREE — no run in progress** | look for a MATSim `java` process (VS Code's `redhat.java` is NOT one); `results/` mtimes |
| Run directories, and every dead one stating its cause | `ls -1d results/*/` · `results/INDEX.md` · `python src/run/run_failure.py --check` |
| Registry field count | `python src/registry/check_hardcoding.py --strict` |
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

**⚠ STANDING DIRECTIVES**

1. **NO MULTI-HOUR RUN WITHOUT EXPLICIT APPROVAL.** Measured: **~100 s/it at 10%**,
   ~30 s/it at 1%. A 1000-iteration arm is ~28 h at 10%.
2. **READ THE TREND, NOT THE LEVEL.** §9.108 is the most important thing in this brief:
   every gate reading this session was at iteration 100 of an arm whose innovation runs
   to 800, and **car, walk and pt were converging the whole time.** Four repairs chased
   a transient.
3. **A CAUSE MUST CARRY ITS MEASUREMENT.** Five mechanisms were asserted this session on
   fit with numbers already in hand; three reached committed entries and were refuted
   (§9.107, §9.110, §9.114). If you name a cause in a DECISIONS entry, either measure
   what distinguishes it from the obvious alternative, or mark it unmeasured.
4. **Every mode individually in every numbers table** — never an umbrella row.
5. **Never commit directly to `main`; the session's ONE PR opens at `/handoff`.**
6. `python src/analyse/report_mode_ridership.py --run <dir> --it <n>` is the twelve-mode
   reader; it now prints **mean trip length beside every share** (§9.107). Add
   `--truck-stations` to score truck on its own ground (§9.101).

**⚠ DECISIONS REQUIRED**
- **Whether to cross the family boundary** and apply #92 + #93 together in one rebuild.
  Every run on disk becomes incomparable, including the F4 arms the front door draws
  from. Both fixes are written up and neither is committed.
- **Approve a converged arm** — ~28 h at 10%, innovation off at 800. **No arm in F11,
  F12 or F13 has ever reached its cutoff**, so no post-cutoff twelve-mode level has ever
  been read.

---

═══════════════════════════════════════════════════════════════════════════════
§1  THE GOAL — and where it now stands
═══════════════════════════════════════════════════════════════════════════════

> Twelve modes present, **physically simulated**, monitored and scored — no teleportation.
> **<10% deviation from real life for every mode.** Unavailable data must be DERIVED.
> Gate every 100 iterations; stop on any mode past 20%; fix the cause from the root.

**Physical simulation: 12 of 12.** Taxi gained a finite fleet at §9.99 and it binds.

**<10% per mode: not met.** On a share basis no mode is inside; **truck is inside on its
own correct basis (+5.4%)**. But see §2 — the level is not the model's answer.

---

═══════════════════════════════════════════════════════════════════════════════
§2  THE MODES — every mode individually, and the TREND that matters more
═══════════════════════════════════════════════════════════════════════════════

**Basis:** linked main-mode trips, target-LGA residents, from the arm's own
`100.trips.csv.gz`. Arm `aborted_20260829T172145_1000it_10pct`, **iteration 100 of 1000,
innovation still running.** Reproduce with
`python src/analyse/report_mode_ridership.py --run results/aborted_20260829T172145_1000it_10pct --it 100`.

| # | mode | modelled % | target % | deviation | mean km | vs obs |
|---|---|---:|---:|---:|---:|---:|
| 1 | car | 47.3368 | 58.1631 | −18.6% | 11.09 | +9% |
| 2 | ride | 7.2909 | 20.6000 | −64.6% | 8.34 | −15% |
| 3 | walk | 25.3988 | 13.4000 | +89.5% | 6.66 | **+852%** |
| 4 | bike | 8.9926 | 2.2084 | +307.2% | 10.04 | +93% |
| 5 | motorbike | 0.1210 | 0.2406 | −49.7% | 11.94 | +17% |
| 6 | taxi | 1.5394 | 0.9916 | +55.2% | 11.43 | +120% |
| 7 | bus | 7.2065 | 2.3819 | +202.6% | 13.18 | −44%* |
| 8 | light_rail | 0.0446 | 0.6444 | −93.1% | 13.18 | −44%* |
| 9 | heavy_rail | 2.0599 | 0.7737 | +166.2% | 13.18 | −44%* |
| 10 | ferry | 0.0096 | 0.1013 | −90.6% | 13.18 | −44%* |
| 11 | truck | 7.7951 | — | **+5.4% on its own ground** | — | — |
| 12 | freight_train | 314 | 314 | representation, not a fit | — | — |

\* one folded HTS observation shared by four PT submodes; not independent.

**THE TREND IS THE FINDING (§9.108), from planned shares over the first 100 iterations:**

| mode | it 0 | it 100 | target | verdict |
|---|---:|---:|---:|---|
| car | 0.3409 | 0.4429 | 0.5816 | **converging, ~136 more** |
| walk | 0.2888 | 0.2116 | 0.1340 | **converging, ~100 more** |
| pt | 0.0688 | 0.0603 | 0.0390 | **converging, ~248 more** |
| **ride** | 0.1903 | 0.1457 | 0.2060 | **DIVERGING** |
| **bike** | 0.0708 | 0.0847 | 0.0221 | **DIVERGING** |
| taxi | 0.0000 | 0.0147 | 0.0099 | overshot |
| motorbike | 0.0020 | 0.0018 | 0.0024 | flat, wrong side |

Walk's **geometry** converges with its share too: 21,475 trips → 15,955, mean 8.12 →
6.66 km.

---

═══════════════════════════════════════════════════════════════════════════════
§3  THE ACTIVE LANE
═══════════════════════════════════════════════════════════════════════════════

**Merge this session's PR first** (§0 has the command).

**Then, one of two, and both need a decision you must obtain:**

**(a) Cross the family boundary and apply #92 + #93 in one rebuild.** #92 is the largest
measured, untouched quantity in the model: 69.9% of 73,258 refused joint bindings name
the companion as their own driver, and `p_thin` thins a pool a third of which is
unbindable. #93 is exact arithmetic — the motorbike carve is its own target times a
ratio that should have cancelled. Neither is committed, deliberately: a builder change
without its rebuild breaks the reproducibility gate.

**(b) Run one arm to its innovation cutoff** (~28 h at 10%) so that, for the first time,
a level means something. Car, walk and pt are on track to arrive; ride and bike are not.

**Do NOT** start by repairing car, walk or pt. §9.108 measured them converging, and four
repairs this session went into a transient.

---

═══════════════════════════════════════════════════════════════════════════════
§4  WHAT IS DONE — record, not instruction. DO NOT REDO ANY OF IT
═══════════════════════════════════════════════════════════════════════════════

**§9.100 — the PT yardstick had three defects.** A light rail stop belonging to another
city (30,241 boardings, 15.6% of the leg, while five of six real stops contributed
nothing); a train leg pooling THREE LGAs (53.7% in the target LGA); a window lying
entirely inside a bus series that falls 319,770 → 37,414 in one month. Station
membership is now derived from the city's own schedule and boundary, the window must be
contiguous and break-free, and a line reported at one stop is scaled by a measured
share. Targets moved: bus 1.3039 → 2.3819, heavy rail 2.0922 → 0.7737, light rail 0.4039
→ 0.6444. **Heavy rail's −1.5% "fit" was an artefact.** +3 registry fields.

**§9.101 — truck was scored against the wrong population.** Its own basis says the target
is *not comparable* with a person-trip share. Scored where the target was measured:
**+5.4%**, not −49.6%. The reader no longer prints a deviation on the wrong basis;
`--truck-stations` scores it properly. **20 of 24 classifying stations are holdout and
were not opened.**

**§9.102 — the pairing rule is not the lever.** `route_contains` was built and measured
against a committed control: pair rate 0.5069 → 0.5113, ride share went the **wrong**
way. §9.92's ruling that `both_links` stays is **confirmed by measurement**.

**§9.104 — resume matched two runs differing in a declared value** and handed back the
wrong one. `_run.json` now carries `values_sha256`; records predating it do not match, by
design.

**§9.105 — a denied lift becomes a drive.** `B.ride.unpaired_fallback` (+1 field). Six of
seven modes moved toward target and **taxi came inside the bar at +7.5%** — but pt moved
away and walk's geometry barely moved.

**§9.106 — a walk feasibility bound does NOT work.** Derived at 3.22 km, it first killed
the run on the chain invariant, then made the fit worse (509.9% → 577.1%). Set to **0.0,
disabled and reproducing**. +2 registry fields.

**§9.107 — the gate now prints geometry.** `mode_targets_by_mode.csv` gained
`target_mean_km` from the survey's own TRIP_AVG_DISTANCE.

**§9.109/§9.111 — the demand cannot serve the ride legs it generates.** 42.4% unservable
at iteration 0; 69.9% of refusals are `driver_is_the_companion`; **`driver_party_full`
is 2 of 73,258**, vindicating that field's own claim.

**§9.113 — supply is ruled out for light rail and ferry** on departures (252 and 107),
not on route-id day tags, which lie.

---

═══════════════════════════════════════════════════════════════════════════════
§5  WHAT INVALIDATES THE WORK
═══════════════════════════════════════════════════════════════════════════════

- **Applying #92 or #93 opens a FAMILY BOUNDARY.** Nothing before compares to anything
  after, including the F4 arms `README.md` draws its fit figures from.
- **Never compare across sample fractions.** This session's diagnostics are 1%; the arm
  is 10%.
- **One arm at a time** (#66). No probe while an arm is up.
- **The 67/143 holdout split is never opened or peeked.**
- **A run without `_run.json` is not a result.** No arm in F10–F13 has one.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers; no session links.

---

═══════════════════════════════════════════════════════════════════════════════
§6  EXACT STATE
═══════════════════════════════════════════════════════════════════════════════

Counts that expire live in **§0**.

- **Phase:** P4 calibration. The yardstick is now sound; the demand is not.
- **Machine:** free.
- **Toolchain:** JDK 25.0.4+7, pt2matsim 26.6, Maven 3.9.9, run-stack 201 jars. Recompile
  with `bootstrap_toolchain.py --verify` after ANY Java change.
- **Two fixes written and NOT committed**, by design: #92 (candidate-pool filter) and
  #93 (motorbike carve). Each is fully specified in its issue and its DECISIONS entry.
- **A pre-fix WEEKDAY demand backup** with a verified `baseline.sha256` was taken this
  session; the instrumented rebuild round-tripped byte-identical twice.

---

═══════════════════════════════════════════════════════════════════════════════
§7  DECISIONS TAKEN — do not re-litigate
═══════════════════════════════════════════════════════════════════════════════

- **`B.ride.pairing_rule` stays `both_links`** (§9.92, confirmed by §9.102's measurement).
- **The walk/bike feasibility bounds stay 0.0** (§9.106) — measured, worse.
- **`B.ride.max_passengers_per_vehicle` does not bind** (§9.111) — 2 refusals of 73,258.
- **The seed stays uniform** (§9.92).
- **SCATS offsets are not adapted** (§9.88); **freight trains are not mobsim vehicles**
  (§9.70, §9.90); **the taxi fare is not a lever** (§9.91).

---

═══════════════════════════════════════════════════════════════════════════════
§8  TRAPS — newest first, each with what it cost
═══════════════════════════════════════════════════════════════════════════════

1. **AN EXPLANATION IS NOT EVIDENCE, HOWEVER WELL IT FITS.** Five times this session a
   cause was adopted because it would explain the numbers already in hand, and three
   reached committed entries before being refuted: destination placement for walk
   (§9.103/§9.106 → refuted §9.107), full days for the joint bindings (§9.109 → refuted
   §9.110), displaced ride for bike (§9.109/§9.112 → refuted §9.114). Every check was
   cheap. **Ask what else would produce the same number.**
2. **A LEVEL READ WHILE INNOVATION RUNS IS NOT THE MODEL'S ANSWER** (§9.108). Car at
   −18.6% and walk at +89.5% at iteration 100 are what a *correct* model looks like a
   tenth of the way through its search from a deliberately uniform seed.
3. **SPLIT A COMPOUND CONDITION BEFORE ATTRIBUTING ANYTHING TO IT** (§9.111). One
   counter served a five-clause test; the two clauses anyone would suspect account for
   **2 refusals and 0**.
4. **NEVER READ SERVICE FROM A `transitRoute` ID** (§9.113). Ferry and tram show ZERO
   weekday routes and run 107 and 252 weekday departures. **Count departures.** This was
   three minutes from being recorded as a finding.
5. **A `main_mode` IS NEVER A PT SUBMODE** (§9.112). It is `pt`; the submode comes from
   the legs table. Counting off `main_mode` reports all four PT modes as absent.
6. **CHECK THE YARDSTICK BEFORE THE MODEL** (§9.91, §9.100, §9.101). Two of this
   session's three "worst" modes were measurement defects.
7. **A REFUSAL INSIDE A SUBTOUR MUST REJECT THE WHOLE PROPOSAL** (§9.106) — otherwise
   `IllegalStateException: Subtour contains a mix of chain- and non-chainbased modes`,
   rc=1 at the first iteration.
8. **A BUILDER CHANGE WITHOUT ITS REBUILD BREAKS REPRODUCIBILITY.** That is why #92 and
   #93 are uncommitted rather than "ready".
9. Carried: `modestats.csv` is PLANNED and the trips table is REALISED; git-bash
   heredocs eat backslashes (write patches via a file); compiling is not installing;
   stopping a run needs BOTH `Stop-ScheduledTask` and `taskkill /PID <pid> /T /F`; a
   `java.exe` at ~0.5 GB is VS Code's language server.

---

═══════════════════════════════════════════════════════════════════════════════
§9  THE SIX STATE-OF-THE-PROJECT QUESTIONS
═══════════════════════════════════════════════════════════════════════════════

**1 · Goals and achievement.** Research goal: test the Auditor-General's claims by
counterfactual microsimulation. Operational goal: a twin whose per-mode ridership is
*checked*. **Physical simulation 12 of 12.** **<10% per mode not met** — no mode inside
on a share basis, truck inside on its own. **No hypothesis tested; no scenario
comparison exists.** Deliverables: 1 🟡 · 2 🟡 · 3 🟡 · 4 ⬜ · 5 🟡 · 6 🟡.

**2 · Phases.** P0 ✅ · P1 ✅ for P4's needs · P2 ✅ · P3 ✅ · **P4 🟡** · P5–P7 ⬜.

**3 · Tasks.** This session: three yardstick defects fixed, two model changes measured
and rejected on evidence, one harness correctness defect fixed, the demand's ceiling
located and classified, three issues filed, three of the session's own conclusions
corrected. Open: #92, #93, #94, and a converged arm.

**4 · Simulator versus real life.** See **§2**. **No valid post-cutoff arm exists** — no
`_run.json` in F10–F13, and no arm has ever reached its innovation cutoff. The standing
calibrated base is still the pre-repair **F4** arm `20260821T175907_1000it_25pct` (MAE
10.65 pp), a **different family**.

**5 · Issue ledger.** Totals in §0. **#92** (NEW) the joint-binding candidate pool;
**#93** (NEW) motorbike generated against one share and scored against another; **#94**
(NEW) the ferry's 450-trip detour market. Commented with measured evidence: **#86**,
**#91**, **#48**, **#30** — the last partly refuted, since the demand *has* the sub-1 km
trips (16.31% under 1 km). Untouched: #84, #82, #73, #68, #66, #63, #62, #50, #49, #21.

**6 · PR history and the next PR.** Totals in §0. This session's PR carries §9.100–§9.115.
The next PR should carry **either** the #92 + #93 rebuild **or** a converged arm — both
need a decision recorded in §0 first.
