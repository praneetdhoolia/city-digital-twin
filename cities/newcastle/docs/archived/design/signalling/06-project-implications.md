# What SUMO's removal changes for signalling

> **FROZEN — written on 25 August 2026 before the SCATS algorithm was implemented (DECISIONS.md §9.88).** Its "open decisions" are decided; the current position is [`positions/signals-and-crossings.md`](../../../positions/signals-and-crossings.md).

The proposal's twin-simulator split assigned "signal-accurate" to SUMO
(proposal §" Supply and operations … **SUMO** — microscopic, signal-accurate,
dwell-explicit"). With SUMO being removed (the descope direction of the
absorption task list's B7 — to be made real by a DECISIONS entry, never by
history rewrite), **MATSim becomes the only place a signal effect can live**.
This file maps the research onto that world. Nothing here is implemented;
sequencing defers to the active lane (4.6.9 re-approval and launch first) and
to the family-boundary batching rule.

## 1. What the corridor loses with SUMO, in signal terms

- The only **explicit** signal programs in the toolchain
  (`tls_<signal_variant_ref>.add.xml`, netconvert phase structure + A2
  timings) and the actuated-vs-static sweep
  (`RUN.sumo.tls_default_type`) that stood in for unobtained SCATS phasing.
- The stated home of the **S-b question** ("what would full transit signal
  priority have been worth?") as a microscopic measurement, and of
  reliability variance from signal delay (whose ≥30 replications never fit
  this machine anyway — issue #6).

What it does *not* lose: the signal **assumption set** — `A.signals.*`,
`E.s2b.signal_delay_removed_share`, `E.s2c.signal_delay_removed_share`,
`E.bus.signal_delay_share`, the run-time decomposition
(`A.signals.delay_per_intersection_s` = 24.75 s at C=110, ~26 s × 14
intersections ≈ 318 s of scheduled corridor run time) — all of that lives in
the registry and the MATSim-side scenario assembly and is untouched by the
descope.

## 2. The revised implementation ladder (MATSim-only)

In increasing effort and risk; each rung is honest under the sweep discipline.

**Rung 0 — current state (already built, stays valid).** No explicit signals.
Signal delay is carried in the mapped schedule via the run-time decomposition
and scenario deltas; priority scenarios (S2b, S2c, S3) are scalar delay-share
sweeps. With SUMO gone, **S-b is reported as a swept band from this
representation** — which §7.2 and §9.21 already require of any corridor
number. Zero new code; the descope decision only needs to say this out loud.

**Rung 1 — sharpen rung 0 with the new evidence (docs/registry only).**
Cite the documented SCATS parameter ranges
([01-scats-mechanics.md](01-scats-mechanics.md) §10,
[03-data-availability.md](03-data-availability.md) §4) in the sweep bases of
the existing fields; fix the known outstanding derivation
(`E.s2b.lr_segment_count` should come from the mapped feed); optionally re-anchor
`A.signals.delay_per_intersection_s` against Webster's formula
([05-algorithms.md](05-algorithms.md) §6) at the swept cycle values instead of
a bare proxy. No model change; sharpens the band's justification.

**Rung 2 — explicit fixed-time signals at the 14 corridor intersections**
(signals contrib; task-list rows B6+B8, currently deferred). Fixed-time plans
generated from the same A2 registry values; corridor approach capacities
raised to saturation flow (the double-count rule,
[04-matsim-implementation.md](04-matsim-implementation.md) §6); lanes
(row B5) for the approaches with protected turns. Cost: new pinned jar or
Maven run-stack build (§14 toolchain change), QSim-assembly integration risk
against the hand-built `citysim` engine set, and the sample-percentage
discretisation constraint. Benefit: the road-space externality (B3's lane
loss, banned turns, cycle changes) and tram-car signal interaction become
*mechanical* on the corridor instead of parameterised.

**Rung 3 — SCATS-like behaviour.** SYLVIA over rung 2's plans (the tactical
layer; ships with the contrib, parameters registry-declared) and, if wanted,
the bespoke strategic emulator ([05-algorithms.md](05-algorithms.md) §7) —
DS-driven cycle/split adaptation with the corridor as one married subsystem.
Nobody has published a SCATS emulator for MATSim; this would be new code with
new assumptions, all swept. Justified only if a corridor question demands
signal *dynamics* (e.g. how priority degrades under saturation) rather than
mean delay.

**Rung 4 — tram priority as a mechanism** ([05-algorithms.md](05-algorithms.md)
§8): a custom controller granting green extension / red truncation /
conditional (PTIPS-style) priority on tram detection, turning
`E.s2b.signal_delay_removed_share` from an input into an **output**. This is
the only rung that answers S-b mechanistically rather than by band — and the
comparison of mechanism-derived vs scalar-swept delay share is itself a
reportable finding.

**Not on the ladder:** SCATSIM software-in-the-loop (no MATSim interface, and
it needs the restricted personality data regardless); Lämmer as the S2
representation (acyclic — not SCATS-like; legitimate only as an upper-bound
comparator arm).

## 3. Decision and bookkeeping consequences

To be actioned when this dossier is absorbed (family-boundary and PR rules
apply; **none of it precedes the 4.6.9 lane**):

1. **DECISIONS entry for the SUMO descope** (B7 — decision required): must state where each
   SUMO-unique deliverable lands — S-b as a swept band (rung 0) or explicit
   (rungs 2–4); reliability variance already limited by issue #6. The
   `RUN.sumo.*` registry section and the SUMO corridor artefacts retire with
   it (retired-by-decision, not deleted from history; manifest regenerated).
2. **Registry updates** (rung 1): sweep-basis citations; `E.s2b.lr_segment_count`
   derived from the feed; every value stays declared, `check_hardcoding`
   count must not grow.
3. **Decision required — LX purchase** (~AU$200/region,
   [03-data-availability.md](03-data-availability.md) §3): the only path that
   makes the strategic layer *measured*. Licence review first — a
   non-redistributable input conflicts with the package-reproducibility gate
   unless quarantined as validation-only.
4. **Validation path without SUMO and without GTFS-Realtime**: §9.22 records
   that no GTFS-RT collection exists and delay evidence "accrues only
   forward" — so the §7.2 realtime-inference leg still has no data. The
   checkable quantities remain: scheduled run times (static GTFS, already the
   decomposition's anchor), the 12.00 min end-to-end schedule, and any
   forward-collected realtime feed if that lane is ever opened. TTD 2018/002's
   ±20% modelled-vs-actual green check is unusable without purchased history
   data.
5. **Level crossings** (B1, issue #68) are a *separate* signalling-adjacent
   mechanism — suburban boom-gated crossings on the Main Northern line,
   modelled as `networkChangeEvents` closures, not SCATS sites. The corridor's
   Stewart Avenue crossing is a T-aspect SCATS site, not a boom gate
   ([02-newcastle-signalling.md](02-newcastle-signalling.md) §3), and must not
   be double-treated by both mechanisms.

## 4. Recommendation

Rung 0 + rung 1 now (docs and registry sharpening — cheap, no boundary);
hold rungs 2–4 unless a named corridor question requires mechanism over band,
and if one does, take rung 2+4 together in one family boundary (fixed-time +
tram-priority controller), skipping rung 3 unless saturation dynamics are
themselves the question. The LX purchase decision dominates all of it: for
~$200 the strategic layer stops being assumed, which narrows the band more
cheaply than any code on this list.
