---
name: onboard
description: Rebuilds the picture of the city-digital-twin project from the repository and GitHub alone - the goal, the twelve-mode scoreboard, the phase and the lane, the fit, the unfinished business - in about 600 lines of reading, then verifies the environment and reports drift. Use for session onboarding and state reconstruction, whenever the user runs $onboard, asks "where are we", "what's the state", "catch me up", or "what should I work on next". The counterpart of $handoff.
---

# $onboard — the picture from `main`, in 600 lines

Assume **zero session memory**. Everything is read from the repository and
GitHub; nothing is taken from the brief without checking it. The definitions —
the reading budget, the trust order by question, the four questions, the facts
that expire, the gate — are in
**[`docs/HANDOVER_CONTRACT.md`](../../../docs/HANDOVER_CONTRACT.md)**; this file
is the procedure. `<city>` is the active city (`CITYSIM_CITY`, default `newcastle`).

The deliverable is the Phase 5 briefing. **Do not start the lane** until it is
delivered and the gate passes.

```
Onboarding:
- [ ] Phase 0  Digest, then the four documents
- [ ] Phase 1  Verify what expires; run the gate
- [ ] Phase 2  Drift scan
- [ ] Phase 3  The four questions
- [ ] Phase 4  Constraints recited
- [ ] Phase 5  Briefing delivered, then stop
```

## Phase 0 — Digest, then the four documents

**Reading budget: about 600 lines.** Do not open anything else until Phase 3
needs it.

1. `python src/run/session_gate.py --digest` — the goal's title, the board's
   generated blocks (scoreboard, state, runs), whether the machine is busy —
   **and whether the arm's harness is dead under a live JVM** (`ORPHANED`, §9.176:
   a run with no ceiling, stall or gate watcher; `run.py --stop` now or
   `run.py --close-out` at its horizon) — how far the branch is ahead of
   `origin/main`, the open PRs, the lane's top task, the decisions unanswered, the
   report recommendations open, and whether the newest arm's price still describes
   the committed build.
2. `docs/GOAL.md` — what the twin is for, the loop, the
   non-negotiables.
3. `docs/STATUS.md` — the one-page board. The generated blocks are
   what the artefacts say; the hand-written rest is what the last session
   decided.
4. `docs/NEXT_AGENT_BRIEF.md` — **start at §0 and
   re-derive every fact in it before reading §1–§3.** The brief is a pointer,
   not a source; where it disagrees with the board or a position page, they win.
5. The **one** position page the lane names
   (`docs/positions/<topic>.md`). The city's own facts — study area, sources,
   package counts, targets — are `cities/<city>/docs/README.md` and
   `targets.md`; open them only when the lane needs one.

**Never read `DECISIONS.md` whole.** If a question needs a section, find it
with `rg -n "^## 9\.NNN" docs/DECISIONS.md` and read that range
with a bounded file read (`Get-Content | Select-Object` in PowerShell). `.agents/AGENTS.md` is loaded automatically; re-read its
hard-constraints list deliberately.

## Phase 1 — Verify what expires; run the gate

Re-derive, by command, every row of the brief's §0: is an arm running, is the
package on disk consistent, is a PR open, how many commits are ahead of `main`,
which issues are open. **A mismatch is a finding for the briefing**, never
something to smooth over. An arm's state is one line —
`python src/run/watch_run.py --run <name>`: the last ended iteration and its
seconds, the recent median, where the ceiling lands at that median and with the
post-cutoff tail, the card's status, whether the harness and a JVM are alive, the
log's age, and whether `_run.json` exists — never a scratch script.

Then the gate — one script, one line per check:

```bash
python src/run/session_gate.py
```

It skips the toolchain compile while an arm runs (that step recompiles
`.tools/classes` under the arm). **A failing gate is this session's first work
item.** If the harness put you on a `claude/*` branch, rename it now
(`<git-handle>/<kebab>`). Work starts from `main` unless the brief says otherwise.

## Phase 2 — Drift scan

The mechanical part already ran inside the gate — document currency, document
shape, the board's generated blocks, dead runs stating their cause. Read its
output; a `PATTERN NOT FOUND`, a stamp mismatch or a stale block is a finding.

Then the classes no checker covers, each a one-line question:

- A board line, a position page or the brief contradicted by an artefact.
- An open issue the record has overtaken (a position page says *built* or
  *measured* under an issue number that is still open).
- Uncommitted work in the tree, or commits ahead of `main` with no PR.
- A run directory with no `_run.json` and no cause. (A run that was STOPPED
  deliberately should carry both - a record saying `stopped_at_gate` or
  `stopped_by_operator`, and the cause on its `_meta.json`; one that carries
  neither is a run nobody closed out.)
- A document that states the project's goal differently from `GOAL.md`.

Each gap goes in the briefing. **Fixing them is scoped work the user decides
on**, not something to do during onboarding. Then `python src/analyse/report_recs.py`:
the report recommendations still open are gaps too, listed by id.

## Phase 3 — The four questions

Answer all four per the contract, with numbers, every mode individually, and
**UNVERIFIED** where the evidence is missing:

1. **Distance to the goal** — the scoreboard, verified by re-running
   `python src/analyse/report_mode_ridership.py --run <run> --it <n>` on the run
   the board names; which goal requirements are met, unmet, unmeasured.
2. **Phase and lane** — the phase table, the open family (the ledger's newest
   key), the package's consistency, the single next task with its cost and its
   blocker.
3. **The fit, honestly** — the last completed arm's `_fit.json`: scored modes,
   the unscorable list and its reasons. Never quote an error against an
   unscorable target. A pair arm is read against its control with
   `python src/analyse/compare_runs.py <control> <arm> --modes` (all twelve
   modes from both `_fit.json`, the comparability rule enforced), never with an
   inline script.
4. **Unfinished business** — PRs, commits ahead, arms, red gates, overtaken
   issues, decisions awaiting the user, approvals (all spent unless stated).

## Phase 4 — Constraints recited

Confirm you can state these without looking them up, then read the brief's §2
traps — each has already cost a day:

- **No multi-hour run without explicit approval**; approvals are spent on use.
- **No invented data**; an unobserved value is derived, or declared with a sweep.
- **The 67/143 holdout is never opened.** **Never compare across families,
  fractions or network builds.** **One arm at a time**; never recompile
  `.tools/classes` while one runs. **A run is a result only if its `_run.json`
  says `ran_to_last_iteration`**; a stopped arm's record is a citable reading at
  its `reached_iteration`, not a result.
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers, no
  session links; **never commit to `main`**; the session's ONE PR opens at
  `$handoff`.

## Phase 5 — The briefing, then the decisions, then stop

Report, in at most forty lines: the four answers (every mode individually in
any table), the gate result and what it blocks, the gaps found (mechanical
first, then the open report recommendations by id), and **the lane** — the
single next task, its cost, and whether it needs a decision or an approval.

**If the user asks you to keep watching an arm**, start ONE event reader with
`python src/run/watch_run.py --run <name> --events --read` through Codex's shell
tool. Retain its process session ID and collect output through `write_stdin`.
Use bounded waits so you can report changes and accept user input. Exit when
`_run.json` appears. If the environment ends the reader, check whether it is
still running before restarting it. There is no Claude Monitor or fixed
30-minute expiry in Codex. Never run `report_mode_ridership.py --trend` in a
foreground call under an arm: it competes with the arm for CPU (§9.176).
Report only what changed.

Then inspect `python src/analyse/lane.py --ask`. Ask only unanswered decisions
that block the user's current task. Use the available Codex choice tool with
the recommended choice first, within its supported question limit. In Default
mode prefer `request_user_input_async`; `request_user_input` may be Plan-only.
Continue independent work while an answer is pending. Never treat elapsed time
or a preselected option as an answer. Record each actual answer with
`python src/analyse/lane.py --answer <D> "<label>"`. The handoff carries it to
§14 and the issue. Never re-ask a recorded answer. Report other pending decisions
without diverting a concrete user task. Start the lane only when the user or a
standing directive already authorises it. When onboarding is the entire request,
finish after the briefing and required questions.
