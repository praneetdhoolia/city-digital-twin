## Phase 8 — Synthesise

1. **Merge the findings into one ranked table**: severity (defect / risk /
   smell), area, `file:line`, one sentence, failure scenario. Deduplicate
   across reviewers; keep the sharper citation.
2. **Merge the optimisation ledgers** (Phases 2 and 3) into one table, sorted
   by expected saving within "touches a result = none" first, then the
   family-opening ones, then the unmeasured.
3. **Ratings**: one row per area, the five dimensions, each cell carrying its
   evidence in a tooltip or footnote. Never average ratings across areas.
4. **Milestones against the goal**: for each hard requirement in
   `docs/GOAL.md`, met / unmet / unmeasured, with the PR and the
   record section that decided it, and the date from the timeline.
4b. **The twelve modes, one row each.** Built from the board's reader
   (`report_mode_ridership.py` on the newest RESULT and, separately, on the
   newest citable reading), the validation targets, the registry, the position
   pages and the reviewers' reports — never from memory. Columns: modelled ·
   target · deviation at the newest result · at the newest citable reading
   (labelled as not a result) · **target provenance** (disclosed / derived /
   vintage, with the file) · **how the mode is simulated** (which engine
   carries it, physical or teleported, which legs are not) · **data it has**
   (the observations in the package that bear on it) · **data it lacks** (the
   observation that would settle its deviation, whether it is obtainable, and
   from whom) · **the mechanism** the evidence names for its deviation · the
   **controls** that exist for it (built / run / unrun, by registry key) · the
   **next measurement**. Then a **supply-fidelity table** for the physical
   layer the modes share — roads and lanes, speeds, signals, level crossings,
   PT timetables and dwell, vehicles and capacity, parking, fares and
   pricing, freight and external traffic — each row: what is real (from which
   artefact), what is derived, what is assumed, what is absent. These two
   tables answer, from evidence, whether more data is needed for a mode and
   whether a more realistic implementation of the traffic system is needed.
5. **The project in its field**: where our row sits on the validation ladder,
   what no other project attempts, what several do that we do not, and the
   factor ledger's counts (IN / PARTIAL / INERT / ASC / OUT) with the top
   movers.
6. **Since the last report**: findings closed, still open, new; survey rows
   changed; factor statuses changed; recommendations taken up or not, with the
   PR that did so.
7. **Verify a sample**: re-read ten cited `file:line`s yourself, and re-fetch
   the sources of **five rows that were searched this pass**. Rows reused from
   the library are verified by inspection — each must carry at least one
   source URL and a `last_verified` inside its horizon — and are not
   re-fetched; re-fetching them is the duplicated work this design exists to
   stop. A finding or a row that does not survive the check is dropped, not
   softened, and a reused row that fails inspection is sent back to `gaps`.
8. **Recommendations**, ranked by (what it would prevent or move) × (how
   cheap), each naming the file or registry key to change, whether it opens a
   family, and the check that would then catch a regression. At most twenty,
   each tagged `model`, `data`, `code` or `process` (the session-process audit
   of Phase 5 feeds the last); the ledger keeps the tag, so the next report can
   say whether the process ones were taken at the same rate as the rest.

## Phase 9 — Write, lodge, index, verify

1. **The report is rendered, not hand-written.** Every lane writes JSON
   (`<scratch>/reviews/phase{2,3,4,5}_*.json`, `<scratch>/research/{field,factors}.json`),
   Phase 8 writes `<scratch>/modes_table.json` and `<scratch>/synthesis.json`
   (verdict, method, the goal table, the merged findings and ledger, ratings,
   since-last-report, recommendations, own verifications), and

   ```bash
   python .agents/skills/project-report/scripts/render_report.py <scratch> REPORT_DIR/<stamp>_project_report.html
   ```

   renders the whole file: a standalone `<!doctype html>`, `<html lang="en-AU">`,
   inline CSS, Google Fonts with real fallback stacks, light and dark themes,
   every table inside `overflow-x:auto`, the charts as inline SVG from the same
   JSON (the per-mode deviation bars, the stage strip, the growth and
   report-series lines), and the `report-data` block at the end. A lane's key
   that is missing renders as a stated gap, never as an empty box, and an
   unknown shape falls back to a generic table or list, so a lane may add a
   field without the renderer changing. For an authorised renderer design change,
   use the available `frontend-design` skill and verify the output with
   `browser-harness`. Preserve chart units, source data, accessible labels and
   colour contrast. Ordinary report passes supply JSON to the existing renderer. The
   six reports before 11 September 2026 were written by hand at 0.8–1.8 MB
   each; the renderer is what makes the ninth pass cost what the eighth did.
2. Sections, in order: masthead (date, HEAD, branch, gate result, one-paragraph
   verdict) · at-a-glance tiles · method (what was read, by whom, the rating
   rubric, the search rounds run) · **the timeline from day 0** (stage strip,
   milestone table, cadence) · repository anatomy (inventory, growth series,
   churn) · code quality by area · the ranked findings table · **the
   optimisation ledger** (redundancy / quality / efficiency / simplification,
   with the touches-a-result column) · **the simulator performance pass**
   (phase shares, pace scaling, memory, writing, the ranked changes, the
   250-iteration verdict) · testing and CI · the PR ledger · the commit log ·
   **the issue ledger** (past, present, upcoming) · runs on disk and their
   cost · milestones against the goal · **the twelve modes, one row each, and
   the supply-fidelity table** · **the project in its field** (the survey
   table, the platform table, the validation ladder, what the comparison
   says) · **the factor ledger** (by layer, with the status tiles and the
   ranked movers) · the document and process layer (placement and currency
   included) · in-flight work seen in the tree · **since the last report, and
   the report process itself** · recommendations · appendix (rubric, sources,
   how this report was produced and how to reproduce it, search rounds per
   lane).
3. **Embed the data** the report was written from at the end of the file, in
   `<script type="application/json" id="report-data">`: the summaries from
   the three collectors, the findings table, the optimisation ledger,
   `field.json`, `factors.json`, the recommendations. The next report diffs
   against it (Phase 0.4). Keep the file under 4 MB; trim the embedded
   per-run detail before trimming anything a reader sees.
4. Name it `REPORT_DIR/<yyyymmddThhmmss>_project_report.html` with the stamp
   from `Get-Date -Format yyyyMMddTHHmmss` in PowerShell (or the platform
   equivalent) at the time of writing. Never overwrite an
   earlier report; the directory is a dated series.
5. Add a row for the new report to `REPORT_DIR/README.md` (create it from the
   previous report's row if absent) — newest first, with its ORDINAL (the
   previous row's plus one, #204), the reading it followed, the HEAD it read and a
   headline of **at most 80 words** that states the verdict, the count of
   findings, the top optimisation, where we sit on the validation ladder and
   the top missing factor. The headline is an index entry, not the report:
   every earlier row that ran to several hundred words made the index
   unreadable, and the detail it carried is in the report it points at.
6. **Confirm the reference library was written.** `REFERENCE_DIR/field-survey.json`
   and `factors.json` must carry this pass's stamp, and `REFERENCE_DIR/README.md`
   must state, for each file, its row count, how many rows were reused, refreshed
   and added this pass, and how many gaps remain open. If a research phase
   returned without writing its file, the report says the library is unchanged
   for that lane and why — it never silently keeps the old file and claims a
   fresh pass. The library is committed: the dated reports are prunable, it is
   not.
7. `python src/analyse/report_recs.py --sync` pulls the new report's
   recommendations into the ledger as open rows, and
   `python src/run/session_gate.py --quick` must still pass; the report, the index, the
   ledger and the reference library are the only files this skill changes. Publish the same file as an Artifact
   as well when the harness offers one, so the user has a link, but the file
   under `REPORT_DIR` is the deliverable.
8. Close with the ranked recommendations in the reply, at most twelve lines,
   the report's path, and the one-line placing in the field. Then stop: the
   change lands at `$handoff`.

## After the report - the follow-on the report feeds

The report changes only its deliverables. Follow-on implementation needs the
user's authorisation. Honour scope already authorised and ask only for missing
decisions that block it, with the recommended choice first. The sequence is:

1. **The issue ledger becomes the tracker.** Every *upcoming* risk in Phase 5's
   ledger is filed as an issue under its one-line title, in the
   `P<phase>: <summary>` scheme; every *present* issue the record has
   overtaken is closed on the evidence the report cites (a PR, a run, a
   measurement), or moved to `awaiting-run` with its `AWAITING-RUN:` line or
   `decision-needed` with its `AWAITING-DECISION:` line (GOAL.md requirement
   10). A risk filed twice is one issue; check the open set first.
2. **Everything fixable without a run is fixed before the next run.** Work the
   ranked findings, the optimisation ledger's `touches a result = none` rows
   and every open issue that needs no arm, in the ranking the report gave,
   on the session branch; `check_hardcoding.py --strict` and the doc gates
   stay green after each. A row that opens a family is worked only if the
   next arm was going to open one anyway, and the record says so.
3. **The run is handed off when nothing else stands in front of it.** When the
   issue gate is green, every remaining issue names the measurement or
   decision it waits on and the brief's lane is the arm, `$handoff` closes the
   session; the next agent's first item is the stated-cost approval and the
   launch, and the next report runs after that arm's gate - one per reading.
   Complete the authorised work and report anything outside that scope.
   Do not start unrelated work or ask the user to reconfirm existing authority.

## What this skill never does

- Never edits the model, the data, the registry, the board, the brief, a
  position page or the record. A finding about them goes in the report.
- Never launches or stops a run, never recompiles the toolchain, never reads a
  `matsim.log` whole.
- Never rates an area without citing the evidence, and never states a number
  it did not collect or read.
- Never carries a **status in this model** forward: every factor's IN / PARTIAL
  / INERT / ASC / OUT is re-read at `HEAD` from the registry or a `file:line`,
  every pass, by `rg` and never by search. The external half — what the
  research says, what a comparable project is — is reused from `REFERENCE_DIR`
  under Phase 6's horizons.
- Never re-searches what the reference library already answers, never runs more
  than one agent on a phase, and never spends a research lane past its 40-call
  budget: what is left over is a named gap in the library, not another round.
- Never returns from a research phase without writing the library, and never
  deletes a stored row because this pass could not re-find it.
- Never presents a literature value as observed, never fills an `unknown`
  from memory, never fetches with `curl`.
- Never reads `DECISIONS.md` or `CONFIG_REFERENCE.md` whole.
- Never proposes a simplification that drops a function the component has:
  that is a defect proposal, and is filed as one.
- Never judges its own series kindly: the process audit counts this report's
  repeats too.
