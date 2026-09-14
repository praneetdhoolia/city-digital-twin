# Project reports

Dated, self-contained assessments of the whole repository, produced by the
`/project-report` skill ([`.claude/skills/project-report/SKILL.md`](../../.claude/skills/project-report/SKILL.md))
and rendered by `render_report.py` from the lanes' JSON (the first six were
written by hand). Each is a reading of one commit: every file by area, code
quality with file-and-line evidence, the milestones of every pull request, the
issue ledger, CI, runs, data and documents, and an audit of whether the earlier
reports were followed. A report runs once per reading — after a gate, a horizon
or a rebuild — never per session. Newest first; a report is never overwritten.

[`reference/`](reference/README.md) is the **standing reference library** — the
survey of comparable city twins and the literature on what a decision simulator
must contain, each row carrying its sources and the date it was last verified.
The research phases read it before searching. A dated report is prunable; the
library is not. A row below with no link is a pruned report; the row stays as
the record of what was assessed at which commit, and the file is recoverable
from git history.

| Report | Commit read | Date | Headline |
|---|---|---|---|
| [`20260914T014107_project_report.html`](20260914T014107_project_report.html) | `780c4c2` (the PR #195 merge; F35 arm 0 at iteration 288 of 300, unread) | 14 September 2026 | The board read heavy rail as 0 on the only result because the reader resolved stops through the rebuilt city schedule, not the run's own. 7 defects, 31 risks, 27 smells; 19 of the previous 20 recommendations taken, none moved the goal count; top missing factor: router–scorer consistency (the raptor mode cost), built and unrun. |
| [`20260911T210144_project_report.html`](20260911T210144_project_report.html) | `20ae4e9` (the PR #179 merge) | 11 September 2026 | Built, unrun, and a stall nobody killed: F33's arm 0 ran 20.9 h on a heap the registry's own rule forbade, 13.1 h of it in one iteration. 76 of 105 prior recommendations taken, none moved the goal count; every model-side control is built and unrun. First report rendered from JSON. |
| [`20260910T134723_project_report.html`](20260910T134723_project_report.html) | `4d1d1bc` (the PR #173 merge) | 10 September 2026 | The instruments were not attached to what they measured: the road-count rung scored the wrong roads for 25 days (the station map was cut 47 minutes before the network was rewritten). The observed city is a transient the search passes through near iteration 50–100, not a fixed point — car pays no fixed per-trip cost, and `fractionOfIterationsToStartScoreMSA` was undeclared. 60 launches, 6 reached their horizon. |
| [`20260909T003402_project_report.html`](20260909T003402_project_report.html) | `781cf41` (the PR #168 merge) | 9 September 2026 | The search method was never the binding constraint: `pt` is one alternative and the submode is chosen by a raptor with no mode constant, so a scoring constant reaches under 1 % of agents. Aitken extrapolation puts settling at iteration 200–210; ride is converged at −38 % and no constant will move it. |
| [`20260908T192638_project_report.html`](20260908T192638_project_report.html) | `6cf0ffd` (the PR #161 merge) | 8 September 2026 | Twelve targets, five knobs, no loop between them: the automated search reached 5 of 482 fields and had never executed a candidate; the objective was a mean over five folded categories against a goal that is a maximum over twelve. Recommended first move: restate the objective (zero machine hours). |
| [`20260907T231739_project_report.html`](20260907T231739_project_report.html) | `f40d332` (the PR #156 merge) | 7 September 2026 | The iteration was cut to 205 s with this project's own code at 0.4 % of it, yet the launcher still quoted 26 h against a measured 13.5–18; requirement 8 untested at a deepest reading of iteration 100; the board contradicted itself four ways. |
| [`20260907T173435_project_report.html`](20260907T173435_project_report.html) | `af7d718` (four commits past the PR #152 merge) | 7 September 2026 | The first pass to measure the synthetic demand against the package's own observations: 19.6 % of departures after 20:00 against 6.2 % observed, the public-transport day inverted against the Opal taps, income drawn independently of age. |
| [`20260907T130247_project_report.html`](20260907T130247_project_report.html) | `419b0da` (the PR #146 merge) | 7 September 2026 | A measured holdout breach (the heavy-vehicle share converting 31 count targets is a median over 20 holdout stations) and a hardcoding scanner reading only ALL-CAPS names. Cost is no longer the constraint; convergence has never been observed. |
| `20260907T013735_project_report.html` (pruned in `03b5220`) | `bdd40f3` (five commits past the PR #144 merge) | 7 September 2026 | 33 defects at HEAD, four in the model itself (BeforeMobsim plan writes discarded, coherence proposals teleported, SCATS grants never undone). |
| `20260903T134517_project_report.html` (pruned in `03b5220`) | `9c99e54` (the PR #110 merge) | 3 September 2026 | 14 defects confirmed; no unit tests; the gate watcher would kill a passing arm; 471 of 509 manifest rows carried no licence. Filed as #112–#137. |
