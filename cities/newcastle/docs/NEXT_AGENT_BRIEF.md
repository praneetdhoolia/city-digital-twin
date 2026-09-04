# Brief for the next agent

**Written:** 4 September 2026, twenty-eighth session · **Open family:** `F24-balanced-destinations` (declared at its first launch, §9.142) · **Commit:** on `praneetdhoolia/stopped-runs-carry-their-record`
*A pointer, not a source: [`GOAL.md`](GOAL.md), [the board](STATUS.md) and
the [position pages](positions) win wherever this disagrees with them.*

The twenty-eighth session made a stopped run close itself out and launched
the first F24 arm. **An arm is RUNNING** - `20260904T181203_300it_25pct`,
under an approval stated and given TO THE ITERATION-100 GATE ONLY. No target
value changed and the 67/143 split is untouched.

**A run that ends at a defined boundary now carries its completion materials.**
The record was written on rc=0 alone, so every arm since F4 - each stopped at
its gate, which is what the gate is FOR - left an orphan directory. A gate stop
and an operator stop are now closed out with a record, a summary and extracted
findings; a CRASH still gets none. The record's required `completion` field is
the result gate now, not the file's presence: only `ran_to_last_iteration` is a
result, satisfies resume or anchors a calibrated base, and a stopped arm's
reading is citable at its `reached_iteration` and nowhere past it.

## §0 Verify first — facts that expire, each with its command

| Fact at handoff | Re-derive with |
|---|---|
| **AN ARM IS RUNNING**: `20260904T181203_300it_25pct`, the first F24 arm, launched 4 Sep 18:12. Approved to its iteration-100 gate ONLY - if the gate watcher has not stopped it on a breach by then, it is stopped with `run.py --stop` and closes out as `stopped_by_operator`. | `python src/run/session_gate.py --digest` (MACHINE line) |
| **The package on disk is the F24 build** (§9.142): destination choice constrained at both ends, C2 re-measured, chains + plans + the 30 run-input sets rebuilt 4 Sep. | `python tests/check_package.py` (~10 min) |
| **Every open issue is closed or `awaiting-run`**, so the launcher's requirement-10 refusal is clear. If `issues gated` is red, an issue was opened or a label lost. | `python src/run/issue_gate.py` · `gh issue list --state open` |
| **PR #140 is MERGED** (4 Sep, all nine CI checks green) and carries the whole session; a second docs-only PR closes the handoff out. Check whether that one merged too. | `gh pr list --state open` · `gh pr list --state merged --limit 3` |
| Registry 464 fields, 30 run-input sets, family `F23-behaviour-channels` in the ledger (F24 is declared at launch). | `python src/analyse/build_status_board.py --check` |
| **No run approval stands.** Every approval to date is SPENT; **25% runs only** (1 Sep directive) governs any launch. | assume none; ask |

Then the gate: `python src/run/session_gate.py` — the machine is idle, so it
runs the toolchain compile too. Every line should be green.

## §1 The lane

**Read the running F24 arm at its iteration-100 gate.** `F24` is declared
(`F24-balanced-destinations`, `decisions_ref` 9.142). The arm is `--run-config
f24_gate_25pct` (25% × 300 declared, graph rendering off) and is approved only
as far as iteration 100; it will carry a `_run.json` when it stops, so its
reading is citable without re-deriving anything from the log.

What the arm answers, in order:

1. **The corridor.** Light rail (−66.1 %) and heavy rail (+193.2 %) on a draw
   that now delivers each zone its own attraction share of arrivals (#30, #98,
   #84). This is the first test of the §9.142 repair.
2. **Taxi should read HIGHER** than F23's +76.6 % (#113): a refused taxi trip
   now keeps taxi in plan memory instead of becoming a walk. A rise is the
   repair working.
3. **Walk (−27.2 %) and car (+14.8 %)** once the short-trip mass is drawn
   against balanced arrivals — does §9.139's seesaw stop overshooting?
4. **Ride (−40.1 %)**: a flat reading is evidence for the §9.142 class (46,345
   bound trips never reach plan memory), not for the pairing rule.
5. The `awaiting-run` measurements: #93, #96, #94, #98, #108, #107, #82, #131.

**The iteration is already repaired** (§9.142), so the arm costs ~24 h rather
than 45–50: the detour pass's router is hoisted (`elapsed_ms` 2,868 → 300 ms an
iteration at 1 %) and the routing log storm is silenced (17,375 → 0 warnings,
~164 GiB → ~3 GiB a run). Both are in this session's PR. The pace figure is
PROJECTED from a 1 % probe; this arm measures the real one.

**Decisions the user must take** (the board's *Next*): the stated-cost
approval; the root-cause pick after the gate; the Task Scheduler operational
log (#66); whether the S2 base grants the tram signal priority
([positions/signals-and-crossings](positions/signals-and-crossings.md)).

## §2 Traps — newest first, at most ten

1. **`singly_constrained` is the comparison, not the fallback** (§9.142):
   `B.activity.destination_balancing` reproduces the previous build exactly at
   that member, which is what makes the balancing measurable. Switching it
   there and rebuilding is a family boundary like any other.
2. **The chains build is much slower now** (§9.142): the decay solve runs
   three passes over the balancing. Budget tens of minutes, and never pipe its
   output through `tail` — the pipe buffers until exit and you see nothing.
3. **Do not re-declare `RUN.controler.last_iteration` to 250.** §9.7 measured
   250 insufficient; requirement 8's 250 is a property to be shown, and a
   300-iteration arm's post-cutoff window already straddles it (§9.142).
4. **The taxi level is not comparable to F23's** (#113, §9.141): every earlier
   reading was taken with refused trips amputated from plan memory.
5. **`F24` is not in `run_families.json` yet** — declared at the first launch
   with `decisions_ref` 9.142, in the same change as the launch.
6. **The next launch trims ~170 GiB on a daemon thread** beside the arm
   (#132): `results/raw` is over the 500 GB cap, so the disk is busy for the
   first hours.
7. **A 25% arm's log is ~51 GiB by its gate** (§9.139) and essentially all of
   it is one `NetworkRoutingProvider` warning (§9.142): never grep
   `matsim.log`; the digest and the watcher read it incrementally.
8. **Read `cause`, never `cause_detail`, for why a run died**
   ([positions/runs-and-economics](positions/runs-and-economics.md)).
9. **A named run overlay that is absent now raises** (#124) — a mistyped
   `--run-config` no longer runs the base under the tag's name.
10. **Heredocs with mixed quotes and backslashes break the shell**: write the
    script to the scratchpad and run the file. One explicit `gh` write per
    issue.

## §3 Standing directives and approvals

- **No multi-hour run without a stated-cost approval.** Every approval to date
  is **SPENT**; none stands. **A gate is a cost boundary** (§9.136).
- **25% runs only** (user directive, 1 Sep) — the 10% pace tables are history.
- **No open issue behind a run** (user directive, 3 Sep; GOAL.md requirement
  10) — enforced by `src/run/issue_gate.py` in the session gate and `run.py`.
- **"Proceed" on a verified plan authorises the lane and its PR, never an
  arm** (user directive, 3 Sep).
- **Optimise the iteration to the fullest extent** (user directive, 4 Sep):
  the profile is in §9.142 and the ranked items are named there. A change that
  moves a result is a family boundary and is recorded as one, never slipped in.
- **The goal directive lives in [`GOAL.md`](GOAL.md)**: twelve modes physical,
  monitored, scored; <10% each; gate every 100 iterations; stop on >20% or
  heading there; fix from the root; converge in ≤250; derive, never assume.
- **A whole-repository assessment is `/project-report`** (user directive,
  3 Sep): it reads, it changes nothing, it lodges a dated file and files a
  finding as an issue, never as a fix.
- **Read the trend, not the level** (§9.108); every mode individually in every
  table; **one arm at a time** (#66); launch detached; never commit to `main`;
  the session's one PR opens at `/handoff`.
