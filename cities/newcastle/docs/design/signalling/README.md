# Signalling research dossier

Research dossier on how traffic signalling actually works in Newcastle, NSW —
SCATS and everything around it — and how to implement it in **MATSim**, written
against the decision that **SUMO is being removed from the toolchain** (the
corridor microsimulator descope; see
[06-project-implications.md](06-project-implications.md)).

**Status: research notes, not results, and not decisions.** Nothing in this
directory is an output of the model, and nothing here changes a registry value,
a scenario or a run input. Values quoted from external sources are evidence for
sweep ranges, not observations of the Newcastle corridor. Where a claim could
not be traced to a primary source it is tagged **[commonly claimed]**; where it
could, **[documented]** with the source; genuine unknowns are tagged **[gap]**.

**Placement.** Landed 25 Aug 2026 at `cities/newcastle/docs/design/signalling/`
— the design-dossier class (evidence for a build decision), following the
point-to-point-mode precedent. File 04 and parts of 05 are generic MATSim
material and could be split to the framework's `docs/` if a second city ever
needs them; deliberately not split while this study is the only consumer.

## Contents

| File | What it holds |
|---|---|
| [01-scats-mechanics.md](01-scats-mechanics.md) | How SCATS works, mechanically: hierarchy, strategic vs tactical control, subsystems and marriage, degree of saturation, cycle/split/offset adaptation, detection, pedestrians, priority machinery, and what a "phasing" dataset contains |
| [02-newcastle-signalling.md](02-newcastle-signalling.md) | Newcastle specifics: SCATS coverage and operation, the light rail's signal priority and T-aspects, PTIPS, pedestrian crossings, level crossings, what remains unknown |
| [03-data-availability.md](03-data-availability.md) | What is open, what is refused, what is purchasable (the ~AU$200 LX file), and the free calibration priors from other jurisdictions and TfNSW's own modelling guidance |
| [04-matsim-implementation.md](04-matsim-implementation.md) | The MATSim signals contrib in detail — data model, engine, controllers, sensors, custom-controller seam — and the integration path for this repository |
| [05-algorithms.md](05-algorithms.md) | The algorithms in pseudo-code: DS computation, SCATS strategic adaptation, SYLVIA, Lämmer, tram priority, Webster fallback, TfNSW's stretch-phase actuated recipe |
| [06-project-implications.md](06-project-implications.md) | What SUMO's removal changes: the revised implementation ladder, the S2b/S-b question, registry and toolchain consequences, open decisions required |
| [07-documentation-corpus.md](07-documentation-corpus.md) | The SCATS documentation map: what is genuinely licence-restricted, the legitimately public corpus that covers its substance (with URLs), and what only a purchase can supply |
| [08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md) | Operated SCATS data for Newcastle found public: planning-portal TIAs republish TfNSW-supplied TCS plans and interpreted history; verified instance with 24 h operated statistics and cycle times for TCS 923 and TCS 1138 (19 July 2022), and what that evidence does and does not change |
| [09-scats-functional-reference.md](09-scats-functional-reference.md) | The consolidated head-to-toe functional inventory: architecture, comms, all operating modes, fallback machinery, detection requirements, pedestrians, every priority mechanism, variation/routines/operator control, alarms, SRMS ramp metering, the data-product and tooling suite — each mapped to its MATSim representation, with a functional-coverage closure checklist |

## Provenance of these notes

Compiled 25 Aug 2026 from primary sources (RTA/Aldridge *SCATS 6 Functional
Description*; TfNSW Technical Direction TTD 2018/002 — superseded watermark,
treat as ~2018 practice; SCATS user-group DS training material; Main Roads WA
signal-data documentation; the MATSim signals contrib source in
`matsim-org/matsim-libs` and the Grether/Kühnel/Thunig papers) plus secondary
literature. Extended the same day with a second research pass: the
Wei et al. survey formalisation of SCATS plan selection, the de Gier/Garoni
SCATS-model algorithm appendices (cycle STEP, split formula, Melbourne tram
priority as operated by VicRoads), the AS 1742.14 jurisdiction supplements,
two locally verified items (all Newcastle-box signal sites are
`RMS_Region = HV` in the Traffic Lights dataset; boom-gated suburban level
crossings confirmed in the repo's OSM harvest), and the public
planning-portal TIA carrying operated SCATS interpreted history for two
Newcastle intersections (file 08). Full source URLs are listed at the end of each file. Related repo
records: `cities/newcastle/docs/DECISIONS.md` §5 (the SCATS proxy), §9.21 (the
phasing refusal), §9.24 (corridor SCATS site identities).
