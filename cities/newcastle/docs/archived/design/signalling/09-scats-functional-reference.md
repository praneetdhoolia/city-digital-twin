# SCATS functional reference, head to toe

> **FROZEN DOSSIER — research notes compiled 25 August 2026 as evidence for the SCATS build; the algorithm they describe is implemented (DECISIONS.md §9.88).** Current position: [`positions/signals-and-crossings.md`](../../../positions/signals-and-crossings.md).

The complete inventory of SCATS functionality in one document, consolidated
from the primary sources processed for this dossier — chiefly the RTA/Aldridge
*New Generation SCATS 6 Functional Description* (read verbatim, twice, most
recently 25 Aug 2026), TfNSW TTD 2018/002, the SNUG DS deck, the SCATS
Core/SPE brochures, and the peer-reviewed SCATS-model literature. Each entry
carries the **MATSim mapping**: how (or whether) the function is representable
in the signals contrib for this project. Detail already specified elsewhere in
this dossier is referenced, not repeated. Tags: **[documented]** /
**[commonly claimed]** / **[gap]** as in
[01-scats-mechanics.md](01-scats-mechanics.md).

## 1. System architecture

| Function | Specification [documented] | MATSim mapping |
|---|---|---|
| Three-tier hierarchy | Central Management Computer (global data, access control, graphics, backup — no real-time traffic decisions); regional computers (≤250 intersections each, ≤64 regions, 16,000 sites max; all strategic optimisation); local controllers (all safety timing, tactical control) | Controller code plays "region + local" per signal system; no CMC analogue needed |
| Comms | One message to and from every local controller **every second**; minimum 300 bit/s per link; serial / TCP-IP / dial-out / dial-in (DIDO) | `updateState(t)` is called every sim-second — the same cadence; comms loss (fallback trigger) is not modelled |
| Product forms | Full adaptive; SCATS Fixed Time Plan (plans by time of day/day of week with improved decision logic); Dial-In-Dial-Out for remote small sites | The project's rung 2 (fixed-time plans) ≙ the Fixed Time Plan product; rung 3 ≙ adaptive |
| Users/monitoring | ≤100 concurrent users system-wide, ≤30 per region, full access control; live per-intersection (lamps, demands, detectors occupied, cycle, mode, alarms, phase running, time-in-phase) and per-subsystem (splits, offset plan, system cycle, detector data) displays | Monitoring surface only — the *data items* mirror what `SignalEvents2ViaCSVWriter` and the sensor API expose |

## 2. Control philosophy

- **Three managed parameters**: cycle time, phase split (% of cycle), offset
  (between successive sets of signals). Coordination goal: divide major-road
  traffic into **platoons** and give each platoon just enough green —
  maximise network capacity, minimise stops.
- **Strategic control** (regional computer, per cycle): optimum cycle/splits/
  offsets per subsystem from stop-line flow + occupancy. See
  [01-scats-mechanics.md](01-scats-mechanics.md) §§2, 4, 5 and
  [05-algorithms.md](05-algorithms.md) §2 (including the plan-selection and
  cycle-decision formalisations).
- **Tactical control** (local controller, within cycle): early termination
  (gap-out) and skipping of undemanded phases; the main-road phase can do
  neither; saved time flows to subsequent phases or the main phase.
  Masterlink sequencing is region-determined; Isolated/Flexilink sequencing
  is local. See [05-algorithms.md](05-algorithms.md) §3; SYLVIA is the
  contrib analogue (§4).
- **Self-calibration**: per-lane maximum flow and optimum space time
  re-learned per 24 h period ([01-scats-mechanics.md](01-scats-mechanics.md)
  §4). MATSim mapping: fixed declared saturation flow (registry) — the
  self-calibration loop is unnecessary when the "true" value is an input.

## 3. Operating modes (the complete set) [documented]

| Mode | Behaviour | MATSim mapping |
|---|---|---|
| **Masterlink** | Real-time adaptive. Region commands phase sequence, transition points, max phase durations, walk durations and terminations; local controller enforces its own minimum green / minimum walk / yellow / all-red regardless — a safety floor no command can breach | The normal state of a SCATS-like controller; safety floors = plan minima that adaptive logic must respect |
| **Flexilink** | Fallback time-of-day coordination on region/comms failure; clocks synced to mains frequency or crystal so offsets survive; local actuation still active; plans/schedules held in controller RAM, master copy re-downloadable from region; controller clocks routinely checked/adjusted | Equivalent to fixed-time plans + gap-out (SYLVIA with plan) — i.e. rung 2/3 of the ladder is literally Flexilink-with-actuation |
| **Isolated** | Pure local vehicle actuation; sequence and maxima from local settings; skip/gap-out per local rules | TTD 2018/002's stretch-phase actuated recipe; SYLVIA without coordination constraints |
| **Hurry Call** | Local pre-programmed pre-emption — "usually associated with an emergency phase or local pre-emption such as a train or tram phase" | The tram-priority controller's hard-recall case ([05-algorithms.md](05-algorithms.md) §8) |
| **Police Off / Red / Manual** | Facility-key manual control at the cabinet | Not modelled (incident ops) |
| **Maintenance** | Technician on site | Not modelled |
| **Flashing Yellow** | All-approach flashing yellow (or yellow/red split); also the fault fallback of last resort | Not modelled; note the *ordering*: controller fault → Flashing Yellow; region/comms fault → Flexilink or Isolated |

Mode transitions can be operator-invoked from any workstation or scheduled by
time of day; Flexilink/Isolated/Flashing sites remain centrally monitored
while comms hold.

## 4. Fallback machinery [documented]

- Triggers: regional computer failure, comms loss, **failure of all strategic
  detectors**, certain local malfunctions.
- Target mode is **user-specified per site**: Flexilink (coordinated) or
  Isolated (uncoordinated).
- **Cascade option**: fallback at one site can force the rest of its
  subsystem — and optionally adjacent linked subsystems — into fallback too,
  so that Flexilink coordination is preserved *as a group* rather than one
  site coordinating against an adaptive rest.
- MATSim mapping: not modelled (no comms failures in the QSim); relevant
  only as evidence that **fixed-time plans are an engineered, first-class
  SCATS state**, not a foreign approximation — every SCATS site carries a
  maintained fixed-time personality at all times.

## 5. Detection (full requirements) [documented]

- Stop-line loops, one per lane; optimum detection-zone length **4.5 m**
  (the loop-vs-zone nuance and DS sensitivity:
  [01-scats-mechanics.md](01-scats-mechanics.md) §6).
- **Strategic detectors** must be at the stop line (they measure green-time
  utilisation; remote placement would force assumptions about achieved flow).
- **Tactical detectors** at the stop line distinguish movements by lane usage
  and, in shared lanes, by **speed differential**; remote placement would
  lose movement identity to lane changing. Advance detectors "found
  unnecessary".
- **Coverage principle**: tactical detection belongs on movements that
  benefit from tactical control (the minor ones); strategic detection on the
  approaches that drive the subsystem (the major ones) — the two are
  complementary, so *most* approaches carry one kind. May be left
  undetected: lightly used kerb lanes on strategically detected approaches;
  main-road approaches at minor intersections not immediately upstream of a
  major one.
- MATSim mapping: `LinkSensorManager` distance-based virtual detection
  ([04-matsim-implementation.md](04-matsim-implementation.md) §2.4); the
  movement-identity constraint maps to lanes — without the lanes model a
  "detector" cannot tell turning movements apart, which is the same
  physical fact SCATS solves with stop-line placement.

## 6. Pedestrian handling

Push-button (or scheduled automatic) demand; region-controlled walk
termination above a local minimum (~6 s NSW); two-part clearance sized to
crossing length; mid-block crossings as SCATS sites; automation where buttons
pressed ≥85% of cycles ([01-scats-mechanics.md](01-scats-mechanics.md) §7).
Interpreted history logs each pedestrian movement's runs — verified against
real Newcastle data in
[08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md)
§3. MATSim mapping: pedestrian phases exist in the plan as green settings for
no vehicular group (time reserved from the cycle); pedestrian *demand*
frequency is the registry-declared probability a walk runs
(`pedestrian_phase_flag` / call proportions per Appendix-G-style data).

## 7. Priority and pre-emption (all mechanisms)

1. **Hurry Call** — local, pre-programmed, hard (mode table above).
2. **Route Pre-emption** — operator/system-managed sequential green window
   along a route (emergency vehicles), a workstation facility.
3. **SCATS Priority Engine (SPE)** — network-level PT/freight/emergency
   priority via authorised clients issuing requests with ETA + entry/exit
   lanes; arbitration among competing requests
   ([01-scats-mechanics.md](01-scats-mechanics.md) §8).
4. **PTIPS** — GPS lateness-conditional bus priority feeding SCATS; operates
   in Newcastle ([02-newcastle-signalling.md](02-newcastle-signalling.md) §2).
5. **ITS port** — the licence-gated data interface through which third-party
   systems (SPE, TMIS, PTIPS-class systems) exchange operational data with
   SCATS — the architectural seam all of the above plug into.

MATSim mapping: one custom controller with detection-driven green extension /
red truncation / phase recall and a conditionality switch covers 1, 3 and 4
behaviourally; specified with reference parameters in
[05-algorithms.md](05-algorithms.md) §8 (including VicRoads' operated partial
priority: ≤20% of cycle, clearance + extension phases, next-cycle commit,
compensation).

## 8. Variation, special routines and operator control [documented]

- **Timetable**: almost any manual function schedulable by time and day
  (e.g. automatic pedestrian introduction on late-shopping nights).
- **Special routines**: a library for event-detection and site-specific
  behaviour beyond general operation — the per-site tailoring machinery
  (with **Strategic Inputs** as the hook binding detectors/phases/intervals
  into strategic control).
- **Operator control**: lamps on/flash/off; mode selection; split/cycle/
  offset overrides per intersection or subsystem; **dwell** (hold any signal
  on a nominated green indefinitely); all parameters editable on-line with
  the region live.
- MATSim mapping: none needed at runtime — these are configuration-time
  facilities. Their modelling significance: any observed SCATS behaviour may
  be a routine, not the core algorithm, which is a reason corridor behaviour
  cannot be fully predicted from the algorithm alone (supports the sweep
  discipline).

## 9. Alarms and health monitoring [documented]

Comprehensive alarm set for fault and unusual conditions, logged on occurrence
and clearance, queryable; **congestion alarms per subsystem**; detector-fault
tolerance (radar substitution noted in
[01-scats-mechanics.md](01-scats-mechanics.md) §6). MATSim mapping: none
(no equipment faults in simulation); congestion alarms correspond loosely to
downstream-occupancy checks (`DownstreamSensor`).

## 10. Ramp metering — SRMS [documented existence]

The **SCATS Ramp Metering System (SRMS)** controls motorway entry ramps and is
faithfully simulated by SCATSIM alongside intersections. No algorithmic
detail is published in the sources processed here **[gap — algorithm]**; no
evidence of any ramp metering in the Newcastle area
([02-newcastle-signalling.md](02-newcastle-signalling.md) §3), so the gap is
moot for this project: **model none**.

## 11. Data products and tooling (what exists around the core)

| Product | Function | Relevance here |
|---|---|---|
| SCATS Access + Graphics, Picture, SCATS Log | Operator UI, graphics, logging (core client) | None (UI) |
| Central Manager, Region (+Configuration) | Core servers | None |
| **Traffic Reporter** | Detector volume / performance reports, graphical or tabular | The VO/VK volume data family purchasable from TfNSW |
| **SCATS History reader** | View phase sequence and phase times after the event | The reader for the history files whose content is verified in [08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md) §3 |
| SCATS Alert / Alarm Analyser / Communication monitor | Event alerting; fault statistics; comms/adaptive uptime | None |
| Event Generator / SMS Server / Congestion Server + Unusual Congestion Monitor / SCATSMap | Server-side add-ons | None |
| **ITS port** | Licensed real-time data exchange with third-party ITS | The SPE/PTIPS seam (§7) |
| **WinTRAFF** (single / simulation / test) | Software emulation of RTA standard (TRAFF) controllers, connectable to a live region | Evidence that controller behaviour is fully software-defined; not usable here (licensed, and no MATSim interface) |
| **SCATSIM** | SCATS software-in-the-loop for microsimulators (intersections + SRMS ramps) | The fidelity gold standard; no MATSim interface and needs restricted personality data ([04-matsim-implementation.md](04-matsim-implementation.md) §3) |
| **TMIS** | Uniform live view over SCATS data (phase, alarm, dwell, lamp, congestion, subsystem), map-based | None |

## 12. Functional coverage checklist (closure statement)

Everything the processed primary corpus attributes to SCATS is now recorded in
this dossier, at the depth the source publishes:

- architecture, capacity, comms — §1 here; [01](01-scats-mechanics.md) §1 ✔
- strategic algorithm (DS; cycle; splits incl. plan selection; offsets;
  subsystems/marriage) — [01](01-scats-mechanics.md) §§3–5,
  [05](05-algorithms.md) §§1–2 ✔
- tactical algorithm (gap-out, skip, stretch phase) — [01](01-scats-mechanics.md)
  §2, [05](05-algorithms.md) §3 ✔
- operating modes, fallback, safety floors — §§3–4 here ✔
- detection — §5 here; [01](01-scats-mechanics.md) §6 ✔
- pedestrians — §6 here; [01](01-scats-mechanics.md) §7 ✔
- priority/pre-emption (Hurry Call, Route Pre-emption, SPE, PTIPS, ITS port)
  — §7 here; [05](05-algorithms.md) §8 ✔
- variation/routines/operator control — §8 here ✔
- alarms — §9 here ✔
- ramp metering — §10 here (existence; algorithm unpublished, not needed) ✔
- data products / tooling / SCATSIM — §11 here ✔
- configuration data model (LX files, local times, history) —
  [01](01-scats-mechanics.md) §9, verified against real data in
  [08](08-operated-signal-data-discovery.md) ✔

Residual unknowns are **parameter values and per-site configuration**
(exact split-increment bound, region/subsystem assignments, the NLR priority
settings), not functionality; each is tagged where it lives, with its
acquisition route. Within what TfNSW and its distributors publish, SCATS
functionality is documented here head to toe.

## Sources

Same corpus as [01-scats-mechanics.md](01-scats-mechanics.md) and
[07-documentation-corpus.md](07-documentation-corpus.md); the SCATS 6
Functional Description was re-read in full for this consolidation
(https://www.aldridgetrafficcontrollers.com.au/ArticleDocuments/230/Introduction_To_New_Generation_Scats_6_5.pdf.aspx,
retrieved 25 Aug 2026). Additional: SCATSLEARN's SMUG 2026 conference
resource index is publicly reachable (https://learn.scats.nsw.gov.au/mod/resource/view.php?id=1468 —
presentations on bus/emergency priority and pedestrian analysis listed;
technical depth sits inside the linked files).
