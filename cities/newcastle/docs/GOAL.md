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
4. Repeat until every mode is inside 10 %.

## Monitoring

Print all twelve modes individually, with a timestamp, against their
observed or derived targets — never an umbrella row. The reader is
`python src/analyse/report_mode_ridership.py --run <run> --trend`; the board
carries the latest reading as a generated block.

## Non-negotiables inherited from the method

These stay whatever the model becomes: no invented data (a value is observed,
derived or assumed-with-a-sweep, and labelled); no result before a run
completes with `_run.json`; the 67/143 validation holdout is never opened
before the end; one network build per comparison; one arm at a time; every
controllable value declared in the registry.

## What this supersedes

- The light-rail counterfactual proposal's framing as *the* project goal. It
  is now the origin design and the first application of the twin.
- The proposal's §7.2 fallback "no SCATS → sweep the cycle time". Requirement
  6 replaces it; the SCATS algorithm is implemented ([`positions/signals-and-crossings.md`](positions/signals-and-crossings.md)).
- The per-session `/goal` restatement. The directive now lives here; a
  session reads it, it does not re-issue it.
