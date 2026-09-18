---
name: project-report
description: Assess the whole city-digital-twin project, its code, run performance, history, twelve modes, data gaps and research context. Produce a dated HTML report with evidence and ranked recommendations. Use for a full project assessment or $project-report, not routine onboarding or session handoff.
---

# Project report

Produce one dated, self-contained HTML report under `docs/reports/`.
Every number needs an artefact, every code finding a `file:line`, every milestone
a PR or record section, and every research claim a source URL actually read.
Apply the conventions in `.agents/AGENTS.md` and the goal in `docs/GOAL.md`.

`REPORT_DIR` means `docs/reports/`. `REFERENCE_DIR` means
`docs/reports/reference/`. `<city>` is selected through `src/city.py`.
Run commands from the repository root. Keep temporary report inputs under
`.agents/.local/project-report/<timestamp>/`, referred to below as `<scratch>`.

Write only the dated report, its index, the recommendation ledger and the
reference library, plus temporary inputs. Do not change the model, data, living
documents or issues. Do not launch or stop a run, or recompile the toolchain.
The report lands through the session's authorised `$handoff`.

Normally assess once per new run reading, gate, horizon or family rebuild.
An explicit user request can authorise another pass. Inspect the previous report
before asking about cadence. Ask a choice only when a missing decision blocks
the request; use the available Codex question tool with the recommendation first.
Respect the user's existing authorisation and any stated budget.

## Procedure and resources

Read the relevant procedure before each stage. Preserve all its evidence and
output requirements; report an unread area as a gap, never as a completed review.

1. [Ground and collect](references/ground.md): phases 0–1 establish HEAD, gate,
   prior report and reference library, then run the three collectors.
2. [Review](references/review.md): phases 2–5 inspect code, performance, history,
   documents, controls and issues. Each phase writes its own review JSON.
3. [Research](references/research.md): phases 6–7 refresh the field survey and
   factor literature. Each phase gets at most 40 searches or page fetches.
   Reuse sourced facts within their freshness horizon. Re-read model status at
   HEAD every pass. Save unresolved questions in the reference library.
4. [Synthesise and publish locally](references/publish.md): phases 8–9 combine
   findings, verify citations, render the report, update its index and ledger,
   and check the result. Follow-on implementation needs its own authorised scope.

## Codex execution

Phase 1 precedes phases 2–7. This report workflow requests one delegated owner
for each of phases 2–7 when Codex collaboration tools are available. Use native
`spawn_agent` and messaging, limited to the actual available slots. Queue the
remaining phases as slots become free; do not assume six concurrent workers.
Use the current model unless the user specifies otherwise. Without delegation,
perform the same phases sequentially and state the execution method.

Give each owner its phase reference, HEAD, input paths, output path, evidence
requirements and search budget. Only phase 6 writes `field-survey.json`; only
phase 7 writes the library's `factors.json`. Other reviewers write temporary
review JSON only. The coordinator owns synthesis, the report index and the
recommendation ledger. Never assign a second owner to the same phase.

Use Codex shell/process tools for collectors and bounded waits for long work.
Use `rg` for local evidence and web search/page-open tools for external research.
Do not assume Claude tools, Monitor, slash-command execution, or Artifact hosting.
Deliver a clickable link to the local HTML file. Use `browser-harness` for visual
inspection when needed. Change the renderer's design only when authorised, using
the available `frontend-design` skill.
