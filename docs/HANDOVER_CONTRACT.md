# The handover contract

**One definition, two consumers.** `/handoff` writes a handover to this contract;
`/onboard` reads one against it. Before this file existed, each skill carried its
own copy of the six questions and they had already begun to disagree — the same
duplication that let `README.md` and `STATUS.md` drift apart on four figures at
once.

This is **framework process**, not one city's study, which is why it lives here
rather than under `cities/<city>/docs/`. Throughout, `<city>` is the active city
(`CITYSIM_CITY`, default `newcastle`).

## Contents

- [The trust order](#the-trust-order)
- [The six state-of-the-project questions](#the-six-state-of-the-project-questions)
- [Facts that expire](#facts-that-expire) — the rule that made the last brief wrong on arrival
- [The brief's required shape](#the-briefs-required-shape)
- [The environment gate](#the-environment-gate)

## The trust order

When two sources disagree, the later one loses:

1. **The artefact** — a file, a run record, a `gh` query. Measurable now.
2. `.claude/CLAUDE.md` — conventions and hard constraints.
3. `cities/<city>/docs/DECISIONS.md` — the record. Dated entries are **frozen**.
4. `cities/<city>/docs/STATUS.md` — the board. Live state, must equal the artefacts.
5. `cities/<city>/docs/handover/NEXT_AGENT_BRIEF.md` — a **pointer**, never a source.

**Artefact > document > brief.** Anything load-bearing gets verified against the
artefact it cites, not accepted because the brief says it.

## The six state-of-the-project questions

A handover is complete when a reader with **zero session memory** can answer all
six from `main` alone. Every number must be traceable to a document section, an
artefact or a run record. Where evidence is missing, the answer is the word
**UNVERIFIED** and what would settle it — never a plausible number.

1. **Goals and achievement.** The research goal (proposal §1/§3: the untested
   Auditor-General claims; hypotheses A1–A6, B1–B4, secondary S-a–S-d) and the
   operational goal (the digital twin — *checked, not assumed*). Against them:
   what is built, what is **measured** to work, and the state of each of the six
   project deliverables (proposal §8).
2. **Phases.** P0–P7, each ✅/🟡/⬜ **with the evidence for the state**, verified
   against the artefacts the board cites.
3. **Tasks per phase.** The numbered plan: per batch, how many done, how many done
   **and evaluated** (*a task without its measurement is not evaluated*), which are
   open, which is the active lane, and which await a decision.
4. **Simulator versus real life.** The latest valid run's fit against the
   calibration targets — per-mode modelled / observed / error, occupancy, trip
   geometry, counts, patronage — labelled pre- or post-calibration and
   diagnostics or results. **If no valid run exists, say so.** Never infer a
   result from the inputs. **And never state an error against a target the fit
   marked unscorable**: `_fit.json`'s `unscorable` list carries the reason each
   one identifies nothing, so a modelled level beside such an observation is a
   level, not an error. The patronage comparison was quoted as an error through
   three briefs before anyone read the reason.
5. **Issue ledger.** Totals filed / closed / open, and per open issue: what it
   tracks, its last evidence date, and whether it needs evaluation, updating, or is
   queued work.
6. **PR history and the next PR.** One line per merged PR (what it changed in the
   model, the data or the record), what the next PR should achieve per the recorded
   value order, and whether that choice is pending a decision.

## Facts that expire

Some facts are true when the brief is written and false when it is read. The
sixth-session brief opened with *"THIS session's PR is OPEN at handoff — merging it
is the first item of unfinished business"*. It had merged overnight. The next agent
spent its opening moves disproving its own briefing.

**Rule for `/handoff`:** never state an expiring fact as settled. Write it with the
command that re-derives it, and collect every one under a single **§0 VERIFY FIRST**
block so the reader cannot miss them.

**Rule for `/onboard`:** re-derive every fact in that block **before** reading the
rest of the brief, and treat any mismatch as a finding to report, not a discrepancy
to smooth over.

These expire by nature — the list is not exhaustive:

| Expiring fact | Re-derive with |
|---|---|
| Whether this session's PR is open, merged or red | `gh pr list --state open` · `gh pr checks <n>` |
| Open-issue set and counts | `gh issue list --state open` |
| Whether a run is in progress | check for a MATSim `java` process; `results/` mtimes |
| Whether the machine is free | same |
| Which local/remote branches survive | `git branch -a` · `git status` |
| Whether an approval is still valid | **approvals are spent on use** — assume none stands |
| Any documented count | `python tests/check_doc_currency.py --strict` |
| Whether the front door draws the current base | `python src/analyse/build_fit_figures.py --check` |
| Whether a dead run can say why it died | `python src/run/run_failure.py --check` |

**A GitHub-derived count belongs in §0 and nowhere else.** "28 merged PRs", "10
open issues", "45 run directories" are the expiring class by construction, and a
brief that also states one in §6 or §9 has made a settled claim out of a
perishable one. Write it once, in §0, beside its command; let the later sections
point at §0. (Breached by the seventh-session brief, which said 28 merged PRs in
§6 and was wrong before its reader finished the environment gate.)

## The brief's required shape

Rewritten **in place** at `cities/<city>/docs/handover/NEXT_AGENT_BRIEF.md` — never a
second brief, never appended to.

| § | Holds |
|---|---|
| §0 | **VERIFY FIRST** — the expiring facts with their re-derive commands, then the environment gate, then standing directives and any decision the next agent must obtain |
| §1 | The goal, and where it now stands |
| §2 | The modes table — **every mode individually**, modelled vs observed, never an umbrella |
| §3 | The active lane: the single next task, its cost, and what it is blocked on |
| §4 | What is done — **do not redo any of it** |
| §5 | What invalidates the work (families, fractions, holdout, approvals) |
| §6 | Exact state — PRs, toolchain, registry, package, machine, runs, open issues, results |
| §7 | Decisions taken — do not re-litigate |
| §8 | Traps, newest first, each with what it cost |
| §9 | The six questions above, answered |

Two standing properties:

- **Completed sections flip from instruction to record** — what ran, what it
  measured, where it is recorded — so the next agent cannot redo finished work.
- **Consumed approvals are marked SPENT.** A multi-hour run needs a fresh
  stated-cost approval every time; none is ever standing.

## The environment gate

Both skills run the same set. It is cheap, and every command is a gate rather than a
courtesy:

```bash
python src/setup/bootstrap_toolchain.py --verify   # pins + compiles both class trees
python tests/check_manifest.py                     # committed subset intact
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
```

If the brief's §0 lists further checks (a probe suite, a scenario-specific gate),
run those too — the brief may know about a gate added after this contract was last
edited. **A failing gate is the session's first piece of work**, not a footnote.
