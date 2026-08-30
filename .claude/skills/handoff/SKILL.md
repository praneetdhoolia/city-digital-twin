---
name: handoff
description: Closes out a work session in the city-digital-twin repository - consolidates every topic the session touched into its position page, appends one record section, regenerates the board, rewrites the brief from its template, grooms GitHub issues on evidence, runs the gate, and lands everything as ONE pull request watched to merge. Use at the END of any session that changed the model, the data, the documents or the plan, and whenever the user runs /handoff, says "close this out", "wrap up", "write the handover", or "open the PR for this session". The counterpart of /onboard.
---

# /handoff — session close-out

Produce a handover in which **every claim is evidenced, every fact lives in its
one home, and the next agent can resume from `main` alone in 600 lines of
reading**. The definitions — the document layers, the trust order, the four
questions, the brief's and the record's required shape, the gate — are in
**[`docs/HANDOVER_CONTRACT.md`](../../../docs/HANDOVER_CONTRACT.md)**; this file
is the procedure. `<city>` is the active city (`CITYSIM_CITY`, default `newcastle`).

Run the phases **in order**. If a phase finds nothing to do, say so and move on;
**do not manufacture work.** Never run scenarios, never touch holdouts, never
re-litigate a settled decision without new evidence.

```
Handoff:
- [ ] Phase 0  Inventory the session, verified against artefacts
- [ ] Phase 1  Consolidate: the position pages
- [ ] Phase 2  Record: one DECISIONS section, one index row, one §14 row
- [ ] Phase 3  Board: hand lines, then regenerate
- [ ] Phase 4  Brief: rewritten from the template
- [ ] Phase 5  Issues, on evidence
- [ ] Phase 6  Gate, then land ONE pull request
- [ ] Phase 7  Green, merged, branch deleted
```

## Phase 0 — Inventory the session

1. `git status`, `git log origin/main..HEAD --oneline`, and **confirm no arm is
   running** (`python src/run/session_gate.py --digest`). A handover written
   mid-run is stale on arrival; if an arm must keep running, say so in §0.
2. Write down what the session did: decisions taken, measurements produced,
   defects found, families opened, directives given, approvals spent.
3. **Verify each item against an artefact** — a file, a diff, a run record —
   before recording it anywhere. Never record a number you cannot point at.

## Phase 1 — Consolidate: the position pages

For **every topic the session touched**, rewrite its page in
`cities/<city>/docs/positions/` so it states the current truth:

- Keep the template's headings (*What is built · What is measured · What is
  open · Refused — do not re-raise · History*), at most 130 lines.
- **Every line that carries a figure carries its source on the same line** —
  a `§9.x`, an issue `#NN`, or a backticked path or run name. The shape check
  enforces this.
- **Retire superseded sentences**; do not append "update:" paragraphs. The page
  is the current position, not a log. The history list at the bottom gains one
  entry (`§9.x — five-word summary`, newest first, at most fifteen).
- Update the `**Updated:**` line and, if a family opened, the families table on
  `sampling-and-families.md`.
- A new topic gets a new page only when no existing page owns it; propose it in
  the PR body.

**This phase is where a correction lands.** A figure or conclusion an earlier
record section got wrong is fixed here, with a §14 row in Phase 2 — never by a
new "CORRECTION" section and never by editing the dated text.

## Phase 2 — Record: one section, one index row, one §14 row

Append **one** `## 9.x` section for the session — numbered next, **after the
last `## 9.x` section** (before `## 14.`), at most 140 lines — on this template:

```
## 9.NNN <plain title> (<date>, <session>; issues #..)

**What was wrong.** One paragraph, measured.
**What changed.** The mechanism, the fields (`KEY` value, sweep), the family boundary if one opened.
**Measured.** The numbers, each with the run or artefact it came from.
**Deliberately not done.** What this leaves alone, and why.
**Consequences.** What no longer compares; what the next session must do.
```

Then a row in the **topical index** (top of the file) and a row in **§14**
(newest first) stating what changed in the model or the data, with the standing
caveats where true: *no target value changed, the 67/143 split is untouched,
nothing here is a finding*. Dated sections and §14 rows are **frozen**: never
"corrected" to match today. Every assumed value introduced this session must
already be in the registry with a sweep — if not, that is unfinished work.

## Phase 3 — Board

Edit only the hand-written lines of `cities/<city>/docs/STATUS.md` that the
session made wrong: *Last updated*, the goal table's *where it stands* cells,
the phase table, the package-consistency paragraph, *Next*, *Open work*.
Then regenerate the blocks:

```bash
python src/analyse/build_status_board.py
```

**The board is one page.** `tests/check_doc_shape.py` caps its hand-written
lines and allows only its own headings; narrative goes to the record or to
`archived/SESSION_LOG.md`. If a count the board states moved, the generated
block already carries it; a hand-written count is a defect.

## Phase 4 — Brief, from the template

Rewrite `cities/<city>/docs/NEXT_AGENT_BRIEF.md` **in place from this
template** — never patch the old one — at most 180 lines:

```
# Brief for the next agent

**Written:** <date> · **Open family:** `<ledger's newest key>` · **Commit:** `<sha>`
*A pointer, not a source: GOAL.md, the board and the position pages win.*

## §0 Verify first — facts that expire, each with its command
| Fact at handoff | Re-derive with |
|---|---|
| <arm running / machine idle> | ... |
| <package consistent / inconsistent, and the first build if not> | ... |
| <this session's PR open / merged> | `gh pr list --state open` |
| <open issues touched> | `gh issue list --state open` |
Then: `python src/run/session_gate.py`

## §1 The lane
The single next task, its cost, what blocks it; the decisions the user must take.

## §2 Traps — newest first, at most ten, each with what it cost

## §3 Standing directives and approvals
Each approval marked SPENT or absent. No approval is ever standing.
```

Everything else is a link. A count derived from GitHub or `results/` lives in
§0 beside its command and nowhere else.

## Phase 5 — Issues, on evidence

For every open issue the session bears on: **close** only when the repository
holds the evidence (the closing comment names it and a REOPEN IF condition);
**update** a body whose halves are now false; **comment** the session's measured
numbers with their `§` reference. File one issue per defect found and not fixed,
with the measured numbers. No umbrella issues; no invented data.

## Phase 6 — Gate, then land ONE pull request

```bash
python src/run/session_gate.py            # every gate; must PASS
python tests/check_package.py             # LOCAL, if a data artefact changed
```

If a data artefact changed: `normalise_eol` → `build_manifest.py` →
`normalise_eol` (git stores LF; hashing CRLF on disk fails CI's manifest check).
If the registry changed: `render_docs.py` and `render_schema.py`. If a run
finished or died: `build_run_index.py`; if the calibrated base moved:
`build_fit_figures.py` and `report.py`.

**Landing:** branch `<git-handle>/<kebab>` (never `claude/*`); commits state
what changed in the model or the data; **no attribution trailers, no session
links**; title `P<phase>: <plain summary>` (≤ ~72 chars, issue refs in parens at
the end, no house idiom); body in Summary / Changes / Testing / Breaking
changes form. **One PR, based on `main`, never stacked.** The hook
`gate-pr-on-docs.sh` refuses `gh pr create` while the document gates are red —
fix the documents, do not bypass it.

## Phase 7 — Green, merged, branch deleted

`gh pr checks <n> --watch` and `gh pr view <n> --json mergeable,mergeStateStatus`
must both be clean **before** anything else; a failing check is this session's
defect to fix now. Then arm a watch for the merge; when it merges and the remote
branch is gone, delete the local branch. **Only then is the handoff complete.**
If the session ends first, the open PR is the next session's first item of
unfinished business — and the brief's §0 says so with the command to check it.

## Final self-check

- [ ] Could the next agent resume from `main` in 600 lines — digest, GOAL, board, brief, one position page?
- [ ] Does every figure in the brief, the board and the touched position pages carry its source?
- [ ] Did any fact acquire a second home this session?
- [ ] Is every expiring fact in §0 with its command, and nowhere else as settled prose?
- [ ] Is the brief stamped with the ledger's newest family, and under 180 lines?
- [ ] Does `python src/run/session_gate.py` pass?
- [ ] Is every issue action backed by evidence in the repository?
- [ ] Is the PR green, mergeable, watched, and the branch deletion queued?
