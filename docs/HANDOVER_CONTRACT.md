# The handover contract

**One definition, two consumers.** `/handoff` writes a handover to this contract;
`/onboard` reads one against it. It is **framework process**, not one city's
study, which is why it lives here; `<city>` throughout is the active city
(`CITYSIM_CITY`, default `newcastle`).

## Contents

- [What a session reads, and how much](#what-a-session-reads-and-how-much)
- [The trust order, by question](#the-trust-order-by-question)
- [The four state-of-the-project questions](#the-four-state-of-the-project-questions)
- [Facts that expire](#facts-that-expire)
- [The brief's required shape](#the-briefs-required-shape)
- [The record's required shape](#the-records-required-shape)
- [The gate](#the-gate)

## What a session reads, and how much

The documents are layered so that a session reads **about 600 lines** before it
can state where the project is, and opens the record only for a section it
needs. The old shape — a 900 KB record, an 800-line board and a 400-line brief,
each pointed at whole — cost forty minutes of reading before any work.

| Layer | File | Lines | What it answers |
|---|---|---|---|
| Goal | `cities/<city>/docs/GOAL.md` | ~100 | what the twin is for; the loop; the non-negotiables |
| Board | `cities/<city>/docs/STATUS.md` | ≤ 170 hand + generated | the scoreboard, where the build is, what runs, what is next |
| Brief | `cities/<city>/docs/NEXT_AGENT_BRIEF.md` | ≤ 180 | what expires, the lane, the traps, the approvals |
| Position | `cities/<city>/docs/positions/<topic>.md` | ≤ 130 each | the current truth for the lane's topic, every figure sourced |
| Record | `cities/<city>/docs/DECISIONS.md` | 13,000+ | why — one section at a time, never whole |

**Never read `DECISIONS.md`, `SESSION_LOG.md` or `reference/CONFIG_REFERENCE.md`
whole.** Find a section with `grep -n "^## 9\.NNN"` and read it with `sed -n`.
The digest (`python src/run/session_gate.py --digest`) prints the goal, the
board's generated blocks and the machine state in two seconds; start there.

## The trust order, by question

A frozen record never answers a live question, and a live document never
overrides a dated one about its own date.

| Question | Read, in order |
|---|---|
| What is true **now** about a topic | the artefact → the position page → the board's generated block |
| **Why** a value is what it is | the record, at the section the position page cites |
| What the project is **for** | `GOAL.md`; `.claude/CLAUDE.md` for the constraints |
| What to do **next** | the board's *Next*, then the brief's §1 |

**Artefact > document > brief.** Anything load-bearing is verified against the
artefact it cites, not accepted because a document says it.

## The four state-of-the-project questions

A handover is complete when a reader with zero session memory can answer these
from `main` alone. Every number traceable to an artefact, a position page or a
record section; anything unevidenced is the word **UNVERIFIED** plus what would
settle it.

1. **Distance to the goal.** Every mode individually, modelled against its
   target on the target's own basis, from the latest reading and the run it
   came from — the board's scoreboard, verified against the reader. Which of the
   goal's requirements are met, which are measured unmet, which are unmeasured.
2. **Phase and lane.** The phase table with its evidence, the open family, the
   package's consistency on disk, and the single next task with its cost and
   what it is blocked on.
3. **The fit, honestly.** What the last *completed* arm measured, pre- or
   post-calibration, what `_fit.json` refused to score and why. Never an error
   against an unscorable target; never a result from a run without `_run.json`.
4. **Unfinished business.** Open PRs, commits ahead of `main`, a running or
   dead-but-unclosed arm, a red gate, issues the record has overtaken, decisions
   awaiting the user, approvals (all spent unless stated).

## Facts that expire

Some facts are true when the brief is written and false when it is read — an
open PR, a running arm, an issue count, whether the machine is free. **`/handoff`
never states one as settled**: it goes in §0 with the command that re-derives
it, and nowhere else. **`/onboard` re-derives every §0 fact before reading on**
and reports a mismatch as a finding. Approvals are spent on use; none is ever
standing.

## The brief's required shape

Rewritten **in place** from the template in the `/handoff` skill — never
patched, never a second brief. At most 180 lines. Four sections:

| § | Holds |
|---|---|
| §0 | **Verify first** — every expiring fact with its command; then the gate command |
| §1 | **The lane** — the single next task, its cost, what blocks it, the decisions required |
| §2 | **Traps** — newest first, at most ten, each with what it cost; older ones are pruned |
| §3 | **Standing directives and approvals** — each approval marked SPENT or absent |

The header carries the date, the commit and the **open family**
(`**Open family:** \`<key>\``); `tests/check_doc_shape.py` fails the brief when
that stamp is not the ledger's newest family, which is what a brief patched
across families looks like. Everything else — the goal, the scoreboard, the
phase table, the history — is a link to the board, a position page or the
record, not a copy.

## The record's required shape

`DECISIONS.md` is frozen through the section named in
`cities/<city>/tests/doc_shape.json` (`frozen_through`). A new section is
**appended after the last `## 9.x` section**, numbered next, at most 140 lines,
on the template in the `/handoff` skill, with a row in the topical index and a
row in the §14 change log. **A correction to an earlier section is an edit to
the position page plus a §14 row** — not a new section, and never a rewrite of
the dated text. A family opens with one ledger row, one section and one position
edit; the board and the brief are regenerated or rewritten, not patched.

## The gate

One script, called by both skills, so they cannot disagree:

```bash
python src/run/session_gate.py --digest   # the opener: goal, scoreboard, state, machine, branch, PRs
python src/run/session_gate.py            # every gate, one line each; exit 1 on any failure
```

It runs the manifest, compile, hardcoding, document-currency, document-shape,
board-block, city-contract, city-agnostic, dead-run and fit-figure checks, and
the toolchain verification — which it **skips while an arm is running**, because
that step recompiles `.tools/classes` under the arm. `tests/check_package.py`
is local and separate: run it on a workstation before declaring a data phase
complete. A failing gate is the session's first work item, and a pull request
cannot open while the document gates are red (`.claude/hooks/gate-pr-on-docs.sh`).
