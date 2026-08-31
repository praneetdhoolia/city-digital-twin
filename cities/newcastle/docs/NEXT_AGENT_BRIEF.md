# Brief for the next agent

**Written:** 31 August 2026, twentieth session · **Open family:** `F21-licence-rate-demand` · **Commit:** the PR that carries §9.135
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

This session priced public transport: the published Opal fare schedule is
acquired, declared (36 `A.fare.*` fields) and charged on every pt journey by
`citysim.PtFareChargeHandler` (§9.135) — until now every ride was free while
car paid fuel and parking and taxi the meter. The cause was picked by
measurement on the stopped F21 arm's own outputs: heavy rail is **+131% even
on the entries basis**, over at every suburban station, with the Interchange
UNDER. The gate-stop diagnostics the last brief queued are all read. **The
next lane is the first F22 arm on the fare-priced model — it needs the
user's stated-cost approval (~18–21 h at 10% × 300).**

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **No arm is running; the machine is idle.** The last runs are the completed smoke `20260831T145828_2it_1pct` (fares live, caps verified) and the F21 gate-stop arm `aborted_20260830T222642_300it_10pct` — still the scoreboard's reading. | `python src/run/session_gate.py --digest` (the MACHINE line) · `ls -t results/ \| head` |
| **The package on disk is consistent under the fare change.** The 30 run-input sets carry the `ptFare` module; `check_package.py` ALL CHECKS PASSED, re-run 31 Aug after the regeneration. | `python tests/check_package.py` (about ten minutes) |
| **This session's PR** is open at handoff, or merged — check; the branch is `praneetdhoolia/pt-fares`. | `gh pr list --state open` · `gh pr checks <n>` |
| Issues #98, #93, #86, #48, #82, #99 and #30 carry this session's measured comments (§9.135); no issue was closed or opened. | `gh issue list --state open` |
| Registry 450 fields, manifest 509 files, 30 run-input sets, family `F21-licence-rate-demand` open from `20260830T222641` — all generated into the board's *State* block. F22 is DECLARED ONLY AT the next arm's launch. | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** The F21 approval was spent on the gate-stop arm; nothing was approved since. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — every check on one line; it
skips the toolchain compile only while an arm runs.

## §1 The lane

**Launch the first F22 arm on the fare-priced model** once the user grants a
stated-cost approval: S2 × WEEKDAY, 10%, 300 iterations is **~18–21 h at the
measured late pace** (§9.134, median ~250 s/it by iteration 100). Launch
detached, family `F22` declared at launch (`decisions_ref` 9.135), gate at
every 100th iteration under the GOAL.md loop. What its gate measures: the
fare's effect on heavy rail (+161.8% at the F21 gate, #98), bus (+15.6%,
#99), taxi's relative price position (#49), and where the displaced pt trips
land (car/ride/walk).

**Lanes measured and waiting, none needing a run** (§9.135, the position
pages):

1. **Walk/car**: the imbalance is inside the car-available group — 86.4% car,
   2.9% walk on 78.3% of trips; a short car trip costs nearly nothing
   (`accessEgressType` `none` §9.54, car constant 0, parking free outside 150
   zones) ([positions/walk-and-bike](positions/walk-and-bike.md), #30).
2. **Ride**: pairing healthy (it.0: 2,814 picked up, 0 unroutable); the
   ceiling is bound volume — the generation side (#86,
   [positions/ride-and-pairing](positions/ride-and-pairing.md)).
3. **Motorbike carve identity** (#93): target-LGA delivery 0.4715–0.5411%
   against the 0.3785% LGA identity and a 0.2652% core solve; next step is
   the per-LGA split of the carve's draws
   ([positions/motorbike-truck-and-freight](positions/motorbike-truck-and-freight.md)).
4. **Corridor attraction** (#30): the Interchange reads UNDER (610 vs 1,683
   entries) while every suburban station is over — the CBD end is missing
   ([positions/light-rail-and-ferry](positions/light-rail-and-ferry.md)).
5. **Truck at its stations** read −51.0% on thin n (24 of 433 vehicles, 3
   stations) — #82's next question is the freight tier under the
   licence-rate demand.

**Decisions required from the user** (also on the board):
1. **The stated-cost approval for the first F22 arm** (~18–21 h at 10% × 300).
2. Enable the Task Scheduler operational log (`wevtutil sl
   Microsoft-Windows-TaskScheduler/Operational /e:true`, elevated) (#66).
3. The fraction and cost of a confirmation arm after the 10% loop — 25% × 300
   ≈ 25 h stated (§9.129).
4. Whether bus moves to a boardings basis once a regional count is acquired
   (#99).
5. Whether the S2 base grants the tram signal priority — the emitted config
   says `green_extension` while the record's S2 probe ran with it off
   ([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## §2 Traps — newest first, at most ten

1. **A raw file written on Windows hashes CRLF while git stores LF** —
   `check_manifest` then fails only in CI. Run `normalise_eol.py` →
   `build_manifest.py` → `normalise_eol.py`, in that order (§9.135's close-out;
   the handoff contract states it and it still almost shipped wrong).
2. **The fare tables live in the pages' server-rendered JSON payload** — the
   visible accordions are collapsed and a text scrape reads "no fares here".
   Grep the raw HTML for the dollar values (`data/raw/fares/`, §9.135).
3. **The scorer counts boardings; the rail target counts entries** (§9.135):
   9.8% of rail journeys re-board (rail>rail at Hamilton). The gap is real
   but small — do not spend a session on it; the excess is demand.
4. **A launch costing understates a long arm** (§9.134): iteration time rises
   with route-set growth (solo ~171–182 s, ~250 s by iteration 100). Cost a
   300-iteration 10% arm at ~18–21 h, never the solo pace.
5. **The board's scoreboard holds back a running arm's newest iteration**
   (`build_status_board.py`): with iterations {0, 10} on disk it reads 0.
   Wait for the next milestone before regenerating.
6. **`citysim` analysis tools run on `.tools/run-stack/lib/*.jar` plus
   `.tools/classes-signals`** — the wrong classpath fails only at runtime
   (`NoClassDefFoundError`), after minutes of reading (§9.134).
7. **The gate recompiled `.tools/classes` under a running arm** (seventeenth
   session). Never run `bootstrap_toolchain.py --verify` with a big
   `java.exe` up; the gate script skips the compile while an arm runs.
8. **A run's identity includes the population it sampled from** (§9.127) —
   and now also its price system: nothing before §9.135 compares with
   anything after. F22 opens at the next arm's launch.
9. **A mode's excess is often another mode's deficit** (§9.123, §9.134): walk
   −36.6% under car +16.0% is one movement; split by car availability before
   touching any constant.
10. **A cause must carry its measurement** (§9.128). This session's cause was
    picked only after the per-station, per-availability and pairing readings;
    keep that order.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** The F21 approval is
  **SPENT** on `aborted_20260830T222642_300it_10pct`; every earlier approval
  is **SPENT**. The F22 arm is NOT approved. No approval stands.
- **The goal directive lives in [`GOAL.md`](GOAL.md)** and is not re-issued
  per session: twelve modes physical, monitored and scored; <10% each; gate
  every 100 iterations; stop on >20% or heading there; fix from the root;
  converge in ≤250; derive, never assume; disclosed values exact.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
