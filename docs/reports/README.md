# Project reports

Dated, self-contained assessments of the whole repository, produced by the
`/project-report` skill ([`.claude/skills/project-report/SKILL.md`](../../.claude/skills/project-report/SKILL.md)).
Each is a reading of one commit: every file by area, code quality with
file-and-line evidence, the milestones of every pull request and commit, the
issue ledger, CI, runs, data and documents. Newest first; a report is never
overwritten.

[`reference/`](reference/README.md) is the **standing reference library** — the
survey of comparable city twins and the literature on what a decision simulator
must contain, each row carrying its sources and the date it was last verified.
The research phases read it before searching and spend their budget only on
what it does not answer. A dated report is prunable; the library is not, and it
is what survives one being deleted.

A row below with no link is a report whose file has been pruned from the tree.
The row stays: it is the dated record of what was assessed at which commit, and
the reference library cites it as the source of its seeded rows. The file itself
is recoverable from git history.

| Report | Commit read | Date | Headline |
|---|---|---|---|
| `20260907T013735_project_report.html` (pruned in `03b5220`) | `bdd40f3` (the session branch, five commits past the PR #144 merge) | 7 September 2026 | 33 defects, 34 risks and 8 smells at HEAD, four defects in the model itself (the engines' BeforeMobsim plan writes discarded, coherence proposals teleported, SCATS grants never undone, the ten-iteration reader blind under the new cadence); all 14 of the 3 Sep defects closed; top optimisation: route the fallback walk inside the engines (20-60 s an iteration, opens a family); alone on the top validation rung by design and no mode inside 10 % by result; top missing factor: an inert crowding utility against heavy rail at +234.7 %; the platform and factor research lanes were cut short by the search budget |
| `20260903T134517_project_report.html` (pruned in `03b5220`) | `9c99e54` (the PR #110 merge) | 3 September 2026 | 14 defects confirmed at HEAD; no unit tests; the gate watcher would kill a passing arm; two acquisition scripts cannot reproduce their outputs; 471 of 509 manifest rows carry no licence; findings filed as #112–#137 |
