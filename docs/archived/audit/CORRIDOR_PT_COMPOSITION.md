# Corridor PT composition: why the demand rides buses past the tram

> **FROZEN RECORD — a diagnostic of the F4 base arm (August 2026).** Kept as evidence, never edited. The current position is [`positions/light-rail-and-ferry.md`](../../positions/light-rail-and-ferry.md).

**DIAGNOSTIC MEASUREMENT OF AN EXISTING RUN — NOT A RESULT ABOUT THE LIGHT
RAIL.** On the closed pre-repair family the light rail carried 1,260
weekday boardings while the PT aggregate overshot its own scored target
(+116% relative; DECISIONS.md §9.64) — the modelled demand rides buses past
the tram.

> **The 1,260 is not an error of −63%, and this document said so until
> 25 August 2026 (§9.80).** The 3,417 boardings/day it was measured against is
> the March 2019 – February 2020 series, and `fit.py` **marks that target
> unscorable**: PT mode share roughly halved between that vintage and the
> 2024/25 market a 2026 base calibrates to (DECISIONS.md §12.1), so V001/V002
> identify nothing about this run. The modelled level is reported here as a
> LEVEL. The gap between it and a pre-pandemic observation is not a fit
> statistic and must not be quoted as one. This document quantifies *why*, on one completed run,
so the candidate explanations each carry a number before the next family
runs. Nothing here compares scenario against scenario:

> **The run measured is `results/20260821T175907_1000it_25pct` — arm A of the
> CLOSED `F4-walk-wedge` comparability family (DECISIONS.md §9.58–§9.64),
> S2 WEEKDAY at a 25% sample, the PRE-REPAIR baseline. The §9.68/§9.69 ride
> and walk repairs post-date it, and the §9.77 activation (signals with tram
> priority, boarding-load dwell, taxi/rideshare) changes the tram's own
> offering — this question RE-MEASURES on the first F6 arm. Do not read any
> number below as the current model, and none of it is a result about the
> light rail intervention.**

Produced by `src/analyse/measure_corridor_composition.py`; the full
machine-readable report is
`results/20260821T175907_1000it_25pct/_corridor_pt_composition.json`.
Reproduce:

```
python src/analyse/measure_corridor_composition.py results/20260821T175907_1000it_25pct
```

Measured 25 Aug 2026, entirely from the run's own artefacts (config
snapshot, mapped day-filtered schedule, final-iteration realised legs and
trips — the tables MATSim writes from the last iteration's events). Counts
are **25%-sample counts**; the ×4 scaling is applied only where a number is
compared against an observed daily figure. The 67/143 holdout under
`data/processed/validation/` is not read.

---

## 0. The catchment, derived — no typed rectangle

The corridor band is derived from declared values only:

| ingredient | value | source |
|---|---|---|
| tram stops | 10 stop locations, 6 named stops (Newcastle Interchange, Honeysuckle, Civic, Crown Street, Queens Wharf, Newcastle Beach) | the run's own mapped schedule (`output/output_transitSchedule.xml.gz`), every route with `<transportMode>tram</transportMode>` |
| band radius | **300 m** | the transit router's declared `maxBeelineWalkConnectionDistance` in the run's `config.xml` — the distance the router itself treats as a walkable connection |
| stop facilities inside the band | 63 (all submodes) | schedule stop coordinates vs the band |

Reconciliation: the per-submode boarding counts recomputed here from
`output_legs.csv.gz` equal the run's events-derived `_metrics.json` exactly
(bus 29,066 · rail 9,415 · ferry 269 · tram 315). Tram 315 × 4 = the 1,260
of §9.64.

## 1. The headline decomposition

**26,143** realised PT trips in the run; **2,140** of them (8.2%) have an
origin or destination inside the tram band — the corridor-catchment trips
this document decomposes.

Submode split of the 2,140 corridor-catchment trips:

| submodes boarded | trips | share |
|---|---:|---:|
| bus only | 1,680 | 78.5% |
| bus+rail | 209 | 9.8% |
| rail only | 75 | 3.5% |
| rail+tram | 70 | 3.3% |
| tram only | 40 | 1.9% |
| bus+tram | 31 | 1.4% |
| ferry only | 29 | 1.4% |
| other combinations | 6 | 0.3% |

Any-tram trips: **143 (6.7%)**; any-bus trips: 1,926 (90.0%). At the stops
*inside the tram's own 300 m walk band* the boardings split **bus 3,404 :
tram 315 : rail 277 : ferry 123** — 10.8 bus boardings per tram boarding
within sight of the tram platforms. The demand is present on the corridor;
it boards buses there.

## 2. The four candidate explanations, each with its number

### (a) Frequency — NOT the carrier

From the run's day-filtered schedule (WEEKDAY departures; two tram routes =
the two directions of `lightrail:NT_NLR`):

| service | departures/day | mean headway | busiest hour |
|---|---:|---:|---:|
| tram, per direction | 126 | 11.4 min | 8/h |
| tram, both directions | 252 | — | 16/h |
| corridor-parallel bus routes combined (485 route patterns serving ≥2 distinct in-band stop locations, of 497 touching the band) | 814 | — | 65/h |

The tram's own frequency is competitive — 11.4 min mean per-direction
headway is denser than almost any single bus route in the schedule. What
the bus system offers is not a more frequent *line* but 814 daily corridor
departures **fanning out to different destinations**. Frequency alone
cannot explain a 10.8:1 boarding ratio at the same kerbs; it points at (c).

### (b) In-vehicle + wait time — secondary, and itself a transfer artefact

Realised times of the corridor-catchment trips (final iteration):

| group | n | door-to-door mean (median) | wait mean | in-vehicle mean |
|---|---:|---|---:|---:|
| used bus, no tram | 1,893 | 52.3 min (45.2) | 4.6 min | 25.6 min |
| used tram (any combination) | 143 | 61.1 min (52.2) | 7.5 min | 24.6 min |
| bus, both ends inside the band | 23 | 13.5 min (12.4) | 1.0 min | 4.5 min |

The tram's scheduled offering is 12.0 min end-to-end over 6 stops
(2.5 km terminus-to-terminus straight line, measured from the schedule's
stop coordinates). Trips that used the tram took **8.8 min longer door-to-door**
than corridor bus trips despite *equal* in-vehicle time — the whole gap is
extra waiting (7.5 vs 4.6 min) and the extra boarding (tram users averaged
1.78 boardings). And for the short hops wholly inside the corridor, a bus
along Hunter/Scott St delivers 4.5 min in-vehicle — the tram's 12-min
end-to-end schedule plus a ~5.7-min expected wait (half the 11.4 min
headway) cannot beat it. Time does not favour the tram anywhere in this
run's offering, but the time gap is itself produced by the interchange, not
by a slow vehicle.

### (c) Network coverage — THE CARRIER OF THE COMPOSITION

| quantity | trips | share of catchment |
|---|---:|---:|
| corridor-catchment trips | 2,140 | 100% |
| **both** ends inside the band (the tram could serve alone) | **36** | **1.7%** |
| one end inside, far end beyond the tram's reach | 2,104 | 98.3% |

**98.3% of corridor PT demand connects the corridor to somewhere the
six-stop tram alignment does not go.** For every one of those 2,104 trips the tram
can only ever be one *leg* — it structurally requires an interchange —
while the bus network runs through: 1,893 of the 2,140 used bus without
tram, and 1,870 of those (98.8%) had their far end outside the band. Even
the 36 wholly-intra-corridor trips split bus 23 : tram 13 — consistent
with (b): for a sub-3 km hop the parallel buses are as fast and arrive
first at 65 corridor departures in the peak hour.

### (d) The transfer penalty — the mechanism that prices (c)

| quantity | value |
|---|---:|
| corridor bus trips that are one-seat rides | 1,413 of 1,893 (74.6%) |
| … of which far end outside the band (a tram alternative = interchange) | 1,390 |
| tram trips needing ≥2 boardings | 103 of 143 (72.0%) |
| tram users' mean boardings | 1.78 |
| declared interchange price (`utilityOfLineSwitch`) | −2.2614 utils per switch |
| declared waiting price (`waitingPt`) | −27.9216 utils/h — ~2.5× the pt in-vehicle marginal utility (−10.9608 utils/h) |

Under the run's declared scoring, replacing a one-seat bus ride with
bus/rail + tram costs one line switch (−2.2614 utils, ≈ 12 min of pt
in-vehicle marginal utility) **plus** the added transfer wait priced at
2.5× in-vehicle time. 74.6% of the corridor bus demand holds a one-seat
ride the tram cannot match; the scoring correctly refuses to break it.
The 143 trips that *did* use the tram are exactly the ones already forced
to interchange (72% multi-boarding, dominated by rail+tram at Newcastle
Interchange — the transfer `beta_transfer_penalty_min` prices).

## 3. The answer, in one paragraph

**Coverage carries the composition; the transfer penalty is the mechanism;
frequency is exonerated; the time gap is a symptom.** The tram is a 6-stop,
12-minute spine spanning 2.5 km, and only 1.7% (36 of 2,140) of the corridor's PT
trips both start and end on it. The other 98.3% must leave the corridor,
which the bus network does one-seat (74.6% of corridor bus trips) at 65
corridor departures in the peak hour, while the tram alternative always
costs an interchange (−2.2614 utils) plus transfer waiting priced at 2.5×
in-vehicle time — realised tram users paid 8.8 min more door-to-door for
the same in-vehicle time. Given the declared parameters, the router and the
scoring are behaving *correctly* on this network: the tram loses not
because it is slow or rare but because in this run's offering it goes
almost nowhere by itself.

## 4. What this does and does not license

- It does **not** say the light rail "fails" — this is the uncalibrated,
  pre-repair base with the PT aggregate itself +116% relative, no signal
  priority, no boarding-load dwell, no taxi/rideshare competitor, and the
  §9.68 ride repair absent. The 3,417/day sometimes quoted beside it is a
  2019–20 observation the fit refuses to score against a 2026 base (§12.1),
  achieved by the real system under conditions this arm does not model.
- It **does** say that any repair aiming at the tram share must move one of
  the measured levers: the effective interchange cost at Newcastle
  Interchange, the tram's connective reach (through-routing/feeders in the
  offering), or the relative wait pricing — not the tram's headway, which
  is already competitive.
- Re-measure on the first F6 arm after the §9.77 activation; the script is
  run-agnostic (`python src/analyse/measure_corridor_composition.py
  results/<run-dir>`).
