---
name: handoff
description: Closes out a work session in the city-digital-twin repository - consolidates every topic the session touched into its position page, appends one record section, regenerates the board, rewrites the brief from its template, grooms GitHub issues on evidence, runs the gate, and lands everything as ONE pull request watched to merge. Use when the user requests session close-out or landing changes, including when the user runs $handoff, says "close this out", "wrap up", "write the handover", or "open the PR for this session". The counterpart of $onboard.
---

# $handoff — session close-out

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

This workflow applies within the user's authorised close-out scope. A request to
adapt or inspect this skill is not a request to run it. Do not infer permission
to publish, merge or message others from merely reaching the end of another task.
Preserve explicit authorisation already given. Use Codex's process sessions for
watches; do not depend on a Claude Monitor or background-task tool.

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
`docs/positions/` so it states the current truth:

- Keep the template's headings (*What is built · What is measured · What is
  open · Refused — do not re-raise · History*), at most 130 lines and 14,000
  bytes, no line over 600 characters. *What is measured* holds the open
  family's readings and the newest result; a closed family's reading is one
  History line naming its record section.
- **Every line that carries a figure carries its source on the same line** —
  a `§9.x`, an issue `#NN`, or a backticked path or run name. The shape check
  enforces this.
- **Retire superseded sentences**; do not append "update:" paragraphs. The page
  is the current position, not a log. The history list at the bottom gains one
  entry (`§9.x — five-word summary`, newest first, at most fifteen).
- **Stamp with the tool, not by hand**: `python src/analyse/positions.py --stamp <topic>
  --session "<date> (<nth> session)" --ref 9.NNN --history "§9.NNN — five words"` rewrites
  the `**Updated:**` line, puts the History entry at the top and caps the list at fifteen,
  then prints the page's lines, bytes and longest line against the caps. Run
  `python src/analyse/positions.py --check` (or `python tests/check_doc_shape.py --strict`,
  seconds) after every page edit — not the full gate. If a family opened, update the
  families table on `sampling-and-families.md` and the page's `**Written against family:**`.
- **The intro paragraph is fixed text and names no run** (`intro_no_run_names`, §9.176):
  which runs are results is the board's runs block. Do not restate results, counts or
  deviations that the board or another page owns; cite them.
- A new topic gets a new page only when no existing page owns it; propose it in
  the PR body.

**This phase is where a correction lands.** A figure or conclusion an earlier
record section got wrong is fixed here, with a §14 row in Phase 2 — never by a
new "CORRECTION" section and never by editing the dated text.

## Phase 2 — Record: one section, one index row, one §14 row

Append **one** `## 9.x` section for the session — numbered next (`python
src/analyse/record.py --next`), at most 140 lines — on this template, written to a
scratch file and placed with `python src/analyse/record.py --append --file <section.md>
--index "<topical-index row>" --change "<§14 row>"`, which puts the section before
`## 14.`, the index row below the previous section's (the index runs oldest-first
within its block) and the §14 row at the head of the change log, and refuses a wrong
number or a duplicate:

```
## 9.NNN <plain title> (<date>, <session>; issues #..)

**What was wrong.** One paragraph, measured.
**What changed.** The mechanism, the fields (`KEY` value, sweep), the family boundary if one opened.
**Measured.** The numbers, each with the run or artefact it came from.
**Deliberately not done.** What this leaves alone, and why.
**Consequences.** What no longer compares; what the next session must do.
```

The index row and the §14 row (newest first) state what changed in the model or
the data, with the standing caveats where true: *no target value changed, the 67/143 split is untouched,
nothing here is a finding*. Dated sections and §14 rows are **frozen**: never
"corrected" to match today. Every assumed value introduced this session must
already be in the registry with a sweep — if not, that is unfinished work.

## Phase 3 — Board

Edit only the hand-written lines of `docs/STATUS.md` that the
session made wrong: *Last updated*, the goal table's *where it stands* cells,
the phase table (its P4 cell keeps the shape "the newest run on disk is `<name>`, which
is **<STATE>**" — a currency claim pins it), the package-consistency paragraph, *Open
work*. **An *Open work* row carries the mechanism, the issue and the next measurement,
never a deviation the scoreboard states** (§9.176): the scoreboard is regenerated, a
re-typed number is a second home that goes stale. Then regenerate the blocks:

```bash
python src/analyse/build_status_board.py
```

**The board is one page.** `tests/check_doc_shape.py` caps its hand-written
lines, its *Last updated* paragraph at two lines, and allows only its own
headings; narrative goes to the record. If a count the board states moved, the
generated block already carries it; a hand-written count is a defect. The
*Next* section is the generated `lane` block: edit `docs/lane.json` with
`python src/analyse/lane.py` (`--done <task> --ref 9.x`, `--answer <D> "<label>"`),
never the block.

## Phase 3b — The lane and the recommendation ledger

`docs/lane.json` is the one home of what is next. Mark the task the session
finished (`python src/analyse/lane.py --done <id> --ref 9.NNN`), add the task
that follows it (`--add-task <json>`: id, title, kind, cost from `arm_cost.py`,
blocked_on, answers_issues, evidence), add any decision the session surfaced
(`--add-decision <json>`: id, question, options with labels and details,
recommended index, issues, evidence — asked today, unanswered), and record every
decision the user took this session (`--answer <D> "<label>"`) — then write the same answer in §14 and on the
issue's `AWAITING-DECISION:` line. A decision the user has NOT taken stays
unanswered; the next `$onboard` asks it. Then the recommendation ledger:
`python src/analyse/report_recs.py --taken <id> --evidence "9.NNN"` for each
report recommendation the session did, `--declined` for one the user refused.
`build_status_board.py` renders the lane into the board and the brief.

## Phase 4 — Brief, from the template

Rewrite `docs/NEXT_AGENT_BRIEF.md` **in place from this
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
<!-- generated:lane start -->
<!-- generated:lane end -->
At most five lines the block cannot say (a probe to take first, a sequence the user set).

## §2 Traps — newest first, at most ten, each with what it cost
A trap that a gate or the launcher now enforces is RETIRED (name the check); what
remains is what only prose can hold.

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
python tests/check_doc_shape.py --strict
python tests/check_doc_currency.py --strict
python src/analyse/build_status_board.py --check
python src/run/session_gate.py --handoff  # every gate plus the close-out checks, ONCE at the end; must PASS
python tests/check_package.py             # LOCAL, if a data artefact changed
```

The full gate takes minutes (the unit suite, the toolchain compile on an idle
machine); the document checks take seconds. A session that ran the gate four
times to find one reworded currency claim (§9.176) paid three of them for nothing.

If a data artefact changed: `normalise_eol` → `build_manifest.py` →
`normalise_eol` (git stores LF; hashing CRLF on disk fails CI's manifest check).
If the registry changed: `render_docs.py` and `render_schema.py`. If a run
finished or died: `build_run_index.py`, and its reading against its control is
`python src/analyse/compare_runs.py <control> <run> --modes` (the twelve modes from
both `_fit.json`, under the comparability rule) — the table the record, the pages
and the issues quote. A run whose harness died while its JVM reached the horizon
and shut down cleanly is closed out with `python run.py --close-out <run>` (§9.176);
one that ended short of it is a reading, not a result, and `reconcile_stale()`
records it at the next launch. If the calibrated base moved: `build_fit_figures.py`
and `report.py`.

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
- [ ] Is every decision the user took recorded in `docs/lane.json`, §14 and the issue, and every open one still asked?
- [ ] Does `python src/run/session_gate.py --handoff` pass?
- [ ] Is every issue action backed by evidence in the repository?
- [ ] Is the PR green, mergeable, watched, and the branch deletion queued?
- [ ] Did the session place anything by hand that a tool in `docs/HANDOVER_CONTRACT.md`'s
      table does — and if it did something by hand three sessions running, is that a
      tool to add (say so in the PR body under *Process*)?
