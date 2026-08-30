---
name: onboard
description: Rebuilds the picture of the city-digital-twin project from the repository and GitHub alone - the goal, the twelve-mode scoreboard, the phase and the lane, the fit, the unfinished business - in about 600 lines of reading, then verifies the environment and reports drift. Use at the START of any session in this repository, whenever the user runs /onboard, asks "where are we", "what's the state", "catch me up", or "what should I work on next". The counterpart of /handoff.
---

# /onboard — the picture from `main`, in 600 lines

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
   generated blocks (scoreboard, state, runs), whether the machine is busy, how
   far the branch is ahead of `origin/main`, the open PRs.
2. `cities/<city>/docs/GOAL.md` — what the twin is for, the loop, the
   non-negotiables.
3. `cities/<city>/docs/STATUS.md` — the one-page board. The generated blocks are
   what the artefacts say; the hand-written rest is what the last session
   decided.
4. `cities/<city>/docs/NEXT_AGENT_BRIEF.md` — **start at §0 and
   re-derive every fact in it before reading §1–§3.** The brief is a pointer,
   not a source; where it disagrees with the board or a position page, they win.
5. The **one** position page the lane names
   (`cities/<city>/docs/positions/<topic>.md`).

**Never read `DECISIONS.md` whole.** If a question needs a section, find it
with `grep -n "^## 9\.NNN" cities/<city>/docs/DECISIONS.md` and read that range
with `sed -n`. `.claude/CLAUDE.md` is loaded automatically; re-read its
hard-constraints list deliberately.

## Phase 1 — Verify what expires; run the gate

Re-derive, by command, every row of the brief's §0: is an arm running, is the
package on disk consistent, is a PR open, how many commits are ahead of `main`,
which issues are open. **A mismatch is a finding for the briefing**, never
something to smooth over.

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
- A run directory with no `_run.json` and no cause.
- A document that states the project's goal differently from `GOAL.md`.

Each gap goes in the briefing. **Fixing them is scoped work the user decides
on**, not something to do during onboarding.

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
   unscorable target.
4. **Unfinished business** — PRs, commits ahead, arms, red gates, overtaken
   issues, decisions awaiting the user, approvals (all spent unless stated).

## Phase 4 — Constraints recited

Confirm you can state these without looking them up, then read the brief's §2
traps — each has already cost a day:

- **No multi-hour run without explicit approval**; approvals are spent on use.
- **No invented data**; an unobserved value is derived, or declared with a sweep.
- **The 67/143 holdout is never opened.** **Never compare across families,
  fractions or network builds.** **One arm at a time**; never recompile
  `.tools/classes` while one runs. **A run without `_run.json` is not a result.**
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers, no
  session links; **never commit to `main`**; the session's ONE PR opens at
  `/handoff`.

## Phase 5 — The briefing, then stop

Report, in at most forty lines: the four answers (every mode individually in
any table), the gate result and what it blocks, the gaps found (mechanical
first), and **the lane** — the single next task, its cost, and whether it needs
a decision or an approval. Then **stop**. Do not begin the lane until the user
says to, or a standing directive in the brief already authorises it.
