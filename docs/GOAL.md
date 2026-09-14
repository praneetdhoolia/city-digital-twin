# The goal — a city digital twin whose ridership is checked, mode by mode

*The one document that says what this project is for. Every other document
serves it: the board ([`STATUS.md`](STATUS.md)) measures distance to it, the
position pages ([`positions/`](positions)) state where each part of the model
stands against it, and the record ([`DECISIONS.md`](DECISIONS.md)) holds the
history of how it got there. Set by the user on 24 August 2026 as the `/goal`
directive and restated in full on 30 August 2026; this file supersedes the
per-session restatement.*

## Why

Once the simulator reproduces how a real city actually moves — every mode, at
its real share, on its real roads and timetables — it becomes an instrument
that can be pointed at questions nobody can answer by observation alone:
Australia's low light rail usage, the modes that could relieve an existing
corridor's congestion, the transport demands of an event the size of the
Brisbane 2032 Olympics. Newcastle (NSW) is the first city because a light rail
was built there in 2019 without an ex-post evaluation; the original research
design for that question is kept as the frozen origin document at
[`design/newcastle-lr-proposal.md`](archived/design/newcastle-lr-proposal.md). The twin
comes first; the questions are applications of it.

## Hard requirements

1. **Exact replica of real life, physically.** Real roads, real lane and
   intersection layouts, real signalling behaviour, real timetables. Every
   mode is simulated in the mobsim — no teleportation.
2. **Nothing is set in stone.** A recorded decision that stands between the
   model and this goal is superseded, with its supersession recorded; the
   record is history, not precedent.
3. **Twelve modes, each present, physically simulated, monitored and scored
   live:** car · ride (vehicle passenger) · walk · bike · motorbike ·
   taxi/rideshare · bus · light rail · heavy rail · ferry · truck · freight
   rail.
4. **External traffic is a share, not a choice.** Trucks and freight trains
   are real-life shares of the traffic, placed where they occur (highways,
   freight routes, the coal chain), plus the small resident share with actual
   driving jobs.
5. **The population is real too.** Age, sex, employment, licence holding, car
   availability, household structure, jobs, needs and finances — every
   distribution that bears on how a person chooses a mode is taken from the
   published data for this city.
6. **Unavailable data is derived, never assumed and never marked impossible.**
   Where a value is disclosed, the exact official value is used. Where it is
   not, it is researched exhaustively and derived — SCATS signalling is
   implemented as its published algorithms, a ferry target is derived from
   the harbour's market. A sweep is the fallback only where derivation is
   genuinely impossible, and then the reason is stated.
7. **Ridership within 10 % of real life for every mode**, verified
   continuously against the official figures.
8. **Convergence in at most 250 iterations.**
9. **City-agnostic.** The framework (`src/`, `config/schema/`, `tests/`,
   `run.py`) may not be tuned to Newcastle; everything specific to a city —
   data, parameters, adapters, documents — lives under `cities/<city>/`.
10. **No open issue behind a run.** Before the simulator is tuned or tested —
    before any arm is launched — every GitHub issue is closed, or declares what
    it is waiting for. An issue that can be fixed without a run is fixed first.
    There are two ways to declare, and the declaration is CHECKED, never taken
    on the label alone (set by the user, 3 September 2026; the third state
    added 9 September 2026):
    - `awaiting-run` **plus a line `AWAITING-RUN: <the measurement>`** — the
      only thing left to do is a measurement that needs the run. **These block
      the launcher** until they are closed or measured.
    - `decision-needed` or `awaiting-implementation` **plus a line
      `AWAITING-DECISION: <what is awaited, and who takes it>`** — what it
      waits on is a decision, an acquisition or a mechanism, and no arm at any
      horizon settles it. **These are reported at every gate and every launch
      and do not block.** The third state exists because the rule was binary
      and four open issues were neither: the only ways to go green were to
      invent a measurement — the exact failure the evidence check exists to
      stop — or to strip the label and make the issue invisible again.
    The purpose is that nothing open passes quietly, not that everything open
    must be a run question.

## The loop

1. Every 100 iterations, read every mode's ridership against its target on
   the basis the target is stated on. Disclosed values are exact; the rest
   are the derived targets in
   `data/processed/validation/mode_targets_by_mode.csv`.
2. If any mode is past 20 % deviation, or heading there on the trend, stop
   the run and list the modes.
3. Find the cause — missing data, a bias, an over-manipulated parameter — and
   fix it from the root. No workarounds, no compensating constants. A
   deviation in one mode is often another mode's deficit: consider them
   together.
4. Work every open issue to closed, to `awaiting-run` with its measurement,
   or to `decision-needed` / `awaiting-implementation` with what it awaits
   (requirement 10); the arm then measures what the issues left to it.
5. Repeat until every mode is inside 10 %.

## Monitoring

Print all twelve modes individually, with a timestamp, against their
observed or derived targets — never an umbrella row. The reader is
`python src/analyse/report_mode_ridership.py --run <run> --trend`; the board
carries the latest reading as a generated block.

## Non-negotiables inherited from the method

These stay whatever the model becomes: no invented data (a value is observed,
derived or assumed-with-a-sweep, and labelled); no result before a run's
`_run.json` says `ran_to_last_iteration` — a run stopped at a gate is closed
out with a record too, and its reading is citable at its `reached_iteration`
and nowhere past it, but it is not a result; the 67/143 validation holdout is
never opened before the end; one network build per comparison; one arm at a
time; every controllable value declared in the registry.

## What this supersedes

- The light-rail counterfactual proposal's framing as *the* project goal. It
  is now the origin design and the first application of the twin.
- The proposal's §7.2 fallback "no SCATS → sweep the cycle time". Requirement
  6 replaces it; the SCATS algorithm is implemented ([`positions/signals-and-crossings.md`](positions/signals-and-crossings.md)).
- The per-session `/goal` restatement. The directive now lives here; a
  session reads it, it does not re-issue it.
