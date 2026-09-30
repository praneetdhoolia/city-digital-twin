# Brief for the next agent

**Written:** 30 September 2026 (sixty-fourth session) · **Open family:** `F39-motorcycles-by-daily-use-trip-ends-on-carrying-links-and-a-bounded-walk` · **Commit:** this handoff's
*A pointer, not a source: [GOAL.md](GOAL.md), the [board](STATUS.md) and the [position pages](positions/) win.*

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **No arm runs; the machine is idle.** F39's control `20260929T072135_250it_25pct` is a RESULT (`ran_to_last_iteration` at 250, 27.9 h): 2 of 12 inside 10 % (car, motorbike −4.1 %), read in §9.219. | `python src/analyse/report_mode_ridership.py --run 20260929T072135_250it_25pct --it 250` |
| **F39's treatment is unrun.** Its overlays set `C.time_weights.service_interval_function` = `atap_m1`; the three probes on disk (`20260930T111836`, `T123858`, `T140500` `_4it_25pct`) priced EARLIER builds of the charge and are citable for their clocks only. D29 (the form and the ceiling) is unanswered. | `python src/analyse/lane.py --ask` · `python src/analyse/arm_cost.py --run-config f39_headway_25pct` |
| Windows Update is paused until **2 October 2026 21:28 AEST** (the user's pause, D19); the launcher refuses a launch whose ceiling outlasts it — a 40 h arm must start before 05:28 on 1 October or wait for a new pause. | `python -c "import sys; sys.path.insert(0,'src/run'); import procs,time; print(time.ctime(procs.updates_paused_until()))"` |
| Registry **600** fields (six ATAP M1 fields added, §9.219); manifest **968** files (**733 CC-BY / 220 ODbL** + 15 bespoke), both cities verifying. | `python src/run/session_gate.py` |
| This session's one PR (`praneetdhoolia/f37-quality-to-four`): open, or merged and the branch deleted. | `gh pr list --state all --head praneetdhoolia/f37-quality-to-four` |
| Open issues after this handoff's issue pass (#258 closed on §9.219; F39's control measurements posted on #30 #86 #94 #107 #145 #162 #175). | `gh issue list --state open --limit 100` · `python src/run/issue_gate.py` |

Then: `python src/run/session_gate.py`.

## §1 The lane

<!-- generated:lane start -->
1. **Run F39's treatment arm: f39_control_25pct plus the service-interval charge on the boarded line's interval at the boarding stop, valued by ATAP M1 (C.time_weights.service_interval_function = atap_m1, #175), and read it against the control 20260929T072135_250it_25pct with compare_runs.py --modes** **(recommended)** - a 25 % probe on the ATAP build (f39_headway_probe_25pct, ~45 min), then one 25 % arm: the control ran 27.9 h against a 27.7 h quote, the treatment's daytime probes quoted 37.0-50.5 h on a loaded host; no family boundary; blocked on: D29 - the charge's form and the arm's cost ceiling (9.219: the probe found the approved charge keyed on route variants (1,080 of 1,270 once-a-day) and a once-a-day line-stop charged 900 IVT-minutes; fixed, and ATAP M1 eq 4.3.2 declared; #94 #98 #175)
2. **A 10 % probe of the Mumbai core on the D15 host (384-512 GB): the live set after full collections, the iteration time, the stuck share and the twelve-mode reading at a fraction the flow identity carries, priced by arm_cost.py before any approval** - no run on this host; on the D15 host one short case (4 iterations at 10 %: 2.7 M agents, 247 GiB live by the rule, an iteration of hours on 8 threads) to price the arm; opens no family (the first Mumbai family opens with the first reading); no family boundary; blocked on: the D15 host: the user procures it (cloud or workstation, 384-512 GB); nothing else - the inputs are assembled with the crossings and the evidenced fleet (9.207) (9.207: the pass-through merge measured at 62.7 -> 69.0 m median and not applied (the user keeps the network as converted); 9.206: 1 % gridlocks on the flow identity; the 0.1 % check 20260922T031226_2it_0.1pct ran to its last iteration with the 430 crossing departures; #239)
3. **Import the Time Use Survey 2024 unit records (microdata.gov.in, the user's logged-in download), derive the activity timing and participation of Maharashtra urban persons from them, and replace the declared departure-time and out-of-home assumptions (B.baseline.activity_start_s, B.activities.out_of_home_*) with the derived distributions** - an extractor over the unit files (the layout is tus_2024_data_layout) and a plans rebuild (~2 min); no run; no family boundary; blocked on: the user's browser: the first download (22 September 2026) carried the documentation only (layout, codes, instructions, README, sample design, Vol II - all already acquired); the unit data files under the Data block of the Get Microdata tab are still to download (9.209: the layout, codes and instructions are acquired and declared reference; the state aggregate tables are the current basis;)
4. **Switch Mumbai's household vehicle roster to `census` and ride pairing on: the citywide plans carry households and each household's cars since 9.205, so a driver can share the household's car and a passenger can name a driver, as the reference city does** - two gate values (B.population.vehicle_roster, B.ride.pairing_enabled) in adopt_framework_fields.py GATES, a re-assembly and a 0.1 % structural check (8 min); no reading on this host; no family boundary; blocked on: nothing - the gates were set when the plans carried no households; a reading needs the D15 host (9.209: the framework files still say "the baseline population carries no households"; B1_households.csv and the plans' householdId exist since 9.205;)
5. **Run Line 7 and Line 9 as the one through corridor MMRDA operates (Gundavali-Kashigaon) instead of two lines meeting at Dahisar East with a transfer** - a generated relation pair spanning the two OSM relations in build_baseline_transit_feed.py, a feed rebuild and one mapping (~4 min); no run; no family boundary; blocked on: nothing (9.209: the press release of 6 April 2026 states the integrated corridor and its 276 weekday trips; the feed generates 537 departures over the two relations against 552 counted twice;)
6. **Design, from observed inputs, the two mechanisms walk's error traces to on F39's control: (1) a car terminal time - the walk to and from a parked car and the manoeuvre - so the car-available stop driving 75.9 % of sub-kilometre trips (walk 7.6 %); (2) the car-less' alternative on a trip no driver is bound to and no transit serves (they walk 14-24 % of 10-20+ km trips; ride is reachable only on bound trips, coverage 19.02 % below its 20.60 % target)** - no run: the literature and data search (ATAP M1 and the HTS for terminal time; the NSW HTS passenger tables for lifts outside the household), a registry proposal with sweeps and a representation gate each, and a probe; opens the next family when built; opens a family; blocked on: nothing - design work; an arm only after F39's treatment (9.219: mode_by_demographics.py distance bands and _bound_trips.json on 20260929T072135_250it_25pct (sub-1 km trips 13.5 % of trips, 59.2 % driven; chosen walks in no-ride tours 26,721 at 6.21 km); #30 #86 #162)
7. **The ASC contraction test for bike alone** - HELD - ~15 h, no family; no family boundary; blocked on: D7 - the first pair has run (§9.176); the user's hold (§9.159) is lifted by that event, not by this session (§9.163: 20.46 pp of headroom on bike; #107)

**Decisions required** (`python src/analyse/lane.py --ask`; recorded with `--answer`):
- **D29.** F39's treatment arm: which service-interval charge should it test, and at what cost ceiling? The control is a result (2 of 12 inside 10 %, motorbike -4.1 %). The approved linear charge was keyed on route variants and is fixed to the boarded line at its stop; the linear form still charges a once-a-day service 900 IVT-minutes, and the daytime probes quote 37-50 h against the control's actual 27.9 h. Options: ATAP M1 function, 40 h cap (Recommended) · Linear as approved, 40 h cap · Hold it; fix walk and no-route first (9.219; asked 30 September 2026, answered 'Make any fixes and handoff' - the fixes are in, the form and the ceiling are still open; #175)

Decided: D24 = Keep using the PC; accept the risk (2026-09-27) · D25 = Warm start at 75, 34 h cap (Recommended) (2026-09-28) · D26 = Warm start at 175, 18 h cap (Recommended) (2026-09-28) · D27 = Resume at 225, 4 h cap (Recommended) (2026-09-29) · D28 = Pair: fixes vs fixes+headway (Recommended) (2026-09-29)
<!-- generated:lane end -->

Ask D29 first. If the treatment goes ahead, probe it on the ATAP build (`f39_headway_probe_25pct`) in the host's quiet hours — the daytime probes priced the host (27.7 → 50.5 h on one code path, §9.219) — and read it against the control with `python src/analyse/compare_runs.py 20260929T072135_250it_25pct <treatment> --modes`. The walk design (`short-trip-and-carless-choice`) needs no arm and can run alongside. A fresh `/project-report` follows the treatment's reading.

## §2 Traps — newest first, at most ten, each with what it cost

1. **A Java class with no probe has never run** (§9.219): `ServiceQualityScoring` was compiled in
   §9.164 and keyed its headway on route variants; the first probe of the approved treatment
   charged an all-day bus 900 IVT-minutes a boarding. Write the probe before the arm.
2. **A daytime probe prices the host, not the build** (§9.219): three probes of one code path
   recurred at 392, 526 and 721 s with every phase slowing together. Quote a pair's second arm
   from the first arm's own wall; probe at night when the price decides an approval.
3. **An environment variable picks the city** (§9.219): `adopt_framework_fields.py` read Newcastle
   as "mine" and wrote nothing until run with `CITYSIM_CITY=mumbai`; every city script needs it.
4. **An arm launched `--foreground` from a session dies with the session** (§9.215): the launcher
   now refuses it without the scheduler's nonce; `run.py --stop` records a dead run as `died`.
5. **A demand rebuild moves the measured access reach** (§9.214): re-measure over every scenario
   and day and re-declare `RUN.transit_router.access_max_radius_m` (reach + 200).
6. **The chains build doubles under the mobility kernel** (§9.214): ~85 min; never wrap a build in `timeout`.
7. **A JSON writer at the wrong indent rewrites the whole file** (§9.213): read the file's own indent.
8. **A refactor is proven by a run, and only the integers are exact** (§9.213, §9.211).
9. **A patch prepared on an issue must be re-anchored before it is applied** (§9.211).
10. **A keyed failure quotes its URL** (§9.209): never print a request URL.
Retired by checks this session: a heredoc or bare `python -` (`.claude/hooks/block-stdin-trap.sh`),
a CI check the gate skips (`tests/unit/test_gate_covers_ci.py`), a second city's stale generated
reference (`render_docs.py --all-cities`), a NUL byte in a source (`test_sources_are_text.py`), a
resume whose cutoff moves (`run_matsim.refuse_cutoff_mismatch`).

## §3 Standing directives and approvals

- **No run approval stands.** D28's control approval is SPENT on `20260929T072135_250it_25pct`; its
  treatment approval was for the LINEAR charge at 34 h and does not carry to the ATAP form or a
  higher ceiling — D29 decides both. D23, D25, D26 and D27 are spent.
- **25 % arms only** for Newcastle; a structural smoke may use 1 %. One arm at a time.
- **The user pauses Windows Update before a launch** (D19); never change the update settings yourself.
- **The user's goal (25 September 2026):** the simulator tuned as close as possible to a real-life
  replica from real data; every report criterion at 4/5 or better; modes chosen by the simulated
  population, never thrown in.
- **"Make any fixes and handoff"** (30 September 2026) authorised this session's fixes and its PR,
  never an arm.
- Compare only within a family, fraction and network build; F38's result is F39's direction only.
  The 67/143 holdout stays shut.
- Never commit to `main`; one PR per session, based on `main`.
