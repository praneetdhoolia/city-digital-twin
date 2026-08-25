---
name: onboard
description: Rebuilds the complete picture of the city-digital-twin project from the repository and GitHub alone - goals, phases, tasks, simulator-vs-reality fit, issues, PRs - verifies the environment, scans for drift between documents and artefacts, and states the single active lane. Use at the START of any session in this repository, especially with no prior context, whenever the user runs /onboard, asks "where are we", "what's the state", "catch me up", or "what should I work on next". The counterpart of /handoff.
---

# /onboard — reconstruct the whole picture from `main` alone

Assume **zero session memory**. Everything is read from the repository and GitHub;
nothing is taken from recollection, and nothing is taken from the brief without
checking it.

The rules this shares with `/handoff` — the trust order, the six questions, the
facts that expire, the environment gate — live in one place:
**[`docs/HANDOVER_CONTRACT.md`](../../../docs/HANDOVER_CONTRACT.md). Read it as part
of Phase 0.** It is the definition; this file is the procedure.

The deliverable is the Phase 6 briefing. **Do not start the work the brief assigns**
until the briefing is delivered and the gates pass.

Throughout, `<city>` is the active city — `CITYSIM_CITY`, default `newcastle`.

Copy this checklist and tick it off as you go:

```
Onboarding:
- [ ] Phase 0  Read, in order
- [ ] Phase 1  Environment gate
- [ ] Phase 2  Live state from GitHub
- [ ] Phase 3  Drift scan (mechanical first)
- [ ] Phase 4  The six questions
- [ ] Phase 5  Constraints recited
- [ ] Phase 6  Briefing delivered
```

## Phase 0 — The reading, in order

1. `.claude/CLAUDE.md` — loaded automatically; **re-read the hard-constraints list
   deliberately**, it is the part sessions skim.
2. [`docs/HANDOVER_CONTRACT.md`](../../../docs/HANDOVER_CONTRACT.md) — the trust
   order and the six questions.
3. `cities/<city>/docs/handover/NEXT_AGENT_BRIEF.md` — **start at its §0 VERIFY
   FIRST block and re-derive every fact in it before reading on.** The brief is a
   pointer, not a source; treat §0 as claims to test.
4. `cities/<city>/docs/STATUS.md` — the board: phase table, deliverable checklist,
   numbered plan, runs on disk, run economics.
5. `cities/<city>/docs/DECISIONS.md` — start at its topical index (*"How to find
   something in this file"* — sections are **not** in file order and §9 holds
   unrelated topics). Read what the brief and board point at: the newest §9.x
   family and the top of the §14 change log.
6. `cities/<city>/docs/design/newcastle-lr-proposal.md` §1, §3, §7, §8 — the
   research goal, hypotheses A1–A6/B1–B4, phases, deliverables.
7. Only as needed after that: `cities/<city>/docs/audit/` and `docs/design/`.

## Phase 1 — Environment gate

Run the gate from the contract, plus anything extra the brief's §0 lists:

```bash
python src/setup/bootstrap_toolchain.py --verify   # ~2 min, compiles both class trees
python tests/check_manifest.py
python src/registry/check_hardcoding.py --strict   # must exit 0
python tests/check_doc_currency.py --strict        # must exit 0
python src/run/run_failure.py --check              # every dead run says WHY it died
python src/analyse/build_fit_figures.py --check    # the front door draws the current base
```

Then establish, by measurement rather than assumption:

- `git status` and the current branch. Work starts from `main` unless the brief says
  otherwise; if the harness put you on a `claude/*` branch, rename it now
  (`<git-handle>/<kebab>`).
- **Is a run in progress?** Look for a MATSim `java` process and check `results/`
  mtimes. Do not assume the machine is free — and note that a `java` process you
  started yourself (a probe) is not a run.

**A failing gate is this session's first work item.** Report it in Phase 6 and say
what it blocks.

## Phase 2 — The live state from GitHub, not from documents

1. `gh issue list --state open` — per issue: title, last-updated date, and whether
   its numbers predate the newest `DECISIONS.md` entry. If they do it needs
   updating: **flag it, do not silently absorb it.**
2. `gh pr list --state all` — the merged sequence is the project's story. **Any OPEN
   PR is unfinished business** and is surfaced before any new work.
3. **Cross-check the brief's ledger against what GitHub actually shows.** A mismatch
   is a finding to report, never something to paper over. Expect the brief to be
   wrong about its own PR — it was written before that PR's fate was known.

## Phase 3 — Drift scan (mechanical first, then judgement)

Run the mechanical check before looking by hand — it is faster and it does not get
tired:

```bash
python tests/check_doc_currency.py     # every pinned live figure vs its artefact
python src/run/run_failure.py --check  # a dead run that cannot say why it died
python src/analyse/build_fit_figures.py --check   # figures vs the calibrated base
```

A `PATTERN NOT FOUND` result means a document was reworded and a claim needs
re-aiming; that is a real finding, not noise.

Then the classes no checker covers yet:

- **A board line contradicted by an artefact** that is not pinned — a count, a
  state, a "pending" that has since happened.
- **A stale statement** — prose that was true once and is now false (a closed issue
  described as open, a retired tool described as current).
- **Uncommitted work in the tree** that no document mentions.
- **An in-progress or crashed run nobody closed out** (a run directory with no
  `_run.json` and no `_meta.json` cause).
- **An open issue whose numbers predate the newest DECISIONS entry.**
- **An open PR** that should merge or close before new work starts.
- **A "done" task with no measurement** — done is not evaluated, and the plan
  distinguishes them.
- **A number in the brief that GitHub disagrees with.** Counts of merged PRs, open
  issues and run directories expire; the contract puts them in §0 with their
  re-derive command, and any that leaked into §6 or §9 as settled prose is a
  finding to report.
- **A living document that duplicates the board or the record.** Both figures the
  doc-currency gate exists for began this way - one table in two files. If you find
  a second home for a fact, say so; the fix is to freeze or retire the copy, not to
  refresh it.

Each gap goes in the briefing. **Fixing them is scoped work the user decides on, not
something to do silently during onboarding.**

## Phase 4 — The six state-of-the-project questions

Answer all six exhaustively, per
[`docs/HANDOVER_CONTRACT.md`](../../../docs/HANDOVER_CONTRACT.md). Every number
traceable to its source; anything you cannot evidence is **UNVERIFIED** plus what
would settle it.

Verify as you go rather than transcribing: for question 4, read the fit artefact
itself (`results/<run>/_fit.json`) rather than the brief's summary of it — that is
where a mode's number is either confirmed or found stale.

**Check what the fit REFUSED to score before quoting any comparison.** A target in
`_fit.json`'s `unscorable` list carries the reason it identifies nothing, and a
modelled level set beside such an observation is not an error statistic. The
patronage figure is the standing example: the model's boardings against a
pre-pandemic vintage was quoted as "-63%" through three briefs before anyone
opened the reason (§9.80).

## Phase 5 — The constraints that invalidate work

Confirm you can state these **without looking them up**, then read the brief's traps
section — each trap has already cost a day:

- **No multi-hour run without explicit approval.** State the cost, get a yes.
  Approvals are **spent on use**; none is ever standing.
- **No invented data.** An unmeasured value is assumed or modelled, labelled as
  such, and recorded in `DECISIONS.md` with a sweep.
- **The 67/143 holdout split is never opened or peeked.** Need a holdout? Say so and
  stop.
- **Never compare across families, sample fractions or network builds.**
- **One arm at a time**; raw data is immutable; every assumed value is declared in
  the registry with a sweep.
- **A run without `_run.json` is not a result.**
- Branch `<git-handle>/<kebab>`, never `claude/*`; no attribution trailers, no
  session links; **never commit directly to `main`.**

## Phase 6 — The briefing (the deliverable)

Report to the user in this order, with numbers:

1. **The six answers** — compressed but complete, every mode individually in any
   table (never an umbrella row).
2. **Environment gate results** and anything they block.
3. **Gaps found**, mechanical ones first.
4. **The active lane** — the single next task per the brief, its cost, and whether
   it needs a decision or an approval before it can start.

Then **stop**. Do not begin the active lane until the user says to, or a standing
directive in the brief already authorises it.
