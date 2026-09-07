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
| [`20260907T130247_project_report.html`](20260907T130247_project_report.html) | `419b0da` (the PR #146 merge, on `main`) | 7 September 2026 | 34 defects, 37 risks and 24 smells at HEAD, led by a **measured holdout breach** — the heavy-vehicle share converting 31 of 34 count targets is a median over 23 stations of which 20 are holdout, and the artefact prints the contradiction itself — and by a hardcoding scanner that reads only module-level ALL-CAPS names, so a CI gate is green on a rule that is broken; 7 of the 7 Sep report's 87 findings closed, 80 still open on a six-file diff; the iteration was fixed rather than the model — our listeners fell from 56.2 % of an iteration to 0.8 %, the median iteration from 639 s to 258.5 s, and a 250-iteration arm now fits in 18–19 h against 44 h, so **cost is no longer the constraint and convergence has still never been observed** (highest `reached_iteration` across 153 runs is 100); top optimisation: let trim reclaim the two pre-§9.142 arms (336 GiB of a 87 %-full cache, touches nothing); still the only project of 41 aiming at the per-mode-ridership rung and still not on it — 1 of 12 modes inside 10 % (car +6.6 %, the first ever at a gate), 7 past the stop bar; top missing factor: the inert crowding utility against heavy rail at +295.1 %; the reference library's two dead lanes are closed — **0 → 12 platform rows, 0 → 58 factor literature halves** |
| `20260907T013735_project_report.html` (pruned in `03b5220`) | `bdd40f3` (the session branch, five commits past the PR #144 merge) | 7 September 2026 | 33 defects, 34 risks and 8 smells at HEAD, four defects in the model itself (the engines' BeforeMobsim plan writes discarded, coherence proposals teleported, SCATS grants never undone, the ten-iteration reader blind under the new cadence); all 14 of the 3 Sep defects closed; top optimisation: route the fallback walk inside the engines (20-60 s an iteration, opens a family); alone on the top validation rung by design and no mode inside 10 % by result; top missing factor: an inert crowding utility against heavy rail at +234.7 %; the platform and factor research lanes were cut short by the search budget |
| `20260903T134517_project_report.html` (pruned in `03b5220`) | `9c99e54` (the PR #110 merge) | 3 September 2026 | 14 defects confirmed at HEAD; no unit tests; the gate watcher would kill a passing arm; two acquisition scripts cannot reproduce their outputs; 471 of 509 manifest rows carry no licence; findings filed as #112–#137 |
