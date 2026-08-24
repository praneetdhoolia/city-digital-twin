# Signal data: what is open, refused, purchasable, and borrowable

The project's premise — SCATS phasing is unobtained and handled by sweep
(`DECISIONS.md` §0, §9.21; `A.signals.scats_phasing` status `unobtained`) —
survives this research intact, with one material addition: the data is
**refused as open data but purchasable**, cheaply, under restrictive terms.

## 1. Open (TfNSW Open Data Hub, CC-BY)

- **Traffic Lights Location** dataset — locations of all NSW signals, CSV
  (+PDF), updated periodically (last June 2026). The equipment identifier is
  the SCATS site (TCS) number — already verified in this repo by the §9.24
  join (all 14 corridor intersections matched, `scats_site_id` filled from
  `Equipment_ID`).
- **NSW Roads Traffic Volume Counts API** and the **Traffic Volume Viewer** —
  AADT/hourly volumes from *permanent and sample roadside counter stations*,
  **not** SCATS stop-line detectors.
- A TfNSW open-data forum thread confirms signalised-intersection detector
  counts are **not** on the open hub; requests go to
  `SCATS.Traffic.Signal.Data@transport.nsw.gov.au` / the Traffic Signal Portal
  (transport.nsw.gov.au/trafficsignal), which supplies data under restrictive
  terms.
- **Planning-portal TIAs republish purchased SCATS data as public documents**
  (found 25 Aug 2026): development traffic impact assessments exhibited on
  the NSW Planning Portal attach TfNSW-supplied **TCS plans and SCATS
  Interpreted History** as appendices. A verified Newcastle instance
  (PPSHCC-137, 643 Hunter Street, Newcastle West — first recorded here as "121
Hunter Street"; corrected against the archived document) carries full 24 h × 15-min operated
  statistics for TCS 923 and TCS 1138 — see
  [08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md).
  Per-intersection and opportunistic, but free and citable.

## 2. Refused (documented, citable)

**[documented]** April 2025: WalkSydney, Better Streets and Jake Coppinger
formally requested SCATS signal phasing data. TfNSW replied that it *"does not
publish the SCATS Signal Phasing data you requested and currently has no plans
to make this information publicly available"*, maintained through follow-up
correspondence and a July 2025 meeting. Already recorded as the operative
contingency in `DECISIONS.md` §9.21; proposal §7.2 binds every headline to a
stated uncertainty band as a result.

## 3. Purchasable (the material new finding)

**[documented via Coppinger]** TfNSW sells signal data under terms barring
commercial exploitation; extraction is manual (TfNSW's stated 2025 rationale:
labour-intensive, no open platform yet). Approximate prices:

| Item | Price (AUD, approx.) |
|---|---|
| **LX file** (one SCATS region: cycle limits, split plans, offset and link plans for every site) | **~$200–220 / region** |
| Interpreted SCATS history | ~$400 / intersection |
| Actual cycle-time data | ~$400 / intersection |
| Phasing explanation | ~$600 |

For roughly $200–600 the project could replace its single most result-driving
assumption (110 s cycle, 45|15|30|10 split, swept 80–140 s) with the corridor's
real strategic configuration. **Open questions before buying** (decision
required, not made here): whether the restrictive licence is compatible with
this project's publication and reproducibility posture (the manifest publishes
hashes and provenance for every input; a non-redistributable input breaks the
"anyone can regenerate the package" property unless quarantined as a
validation-only artefact); and whether the LX file alone (no history) is worth
it without the ~$400/intersection operated cycle-time series.

## 4. Borrowable priors from elsewhere

Where NSW values are unobtainable, *typical SCATS behaviour* can be bounded
from jurisdictions that publish:

- **Victoria**: complete per-intersection operation sheets (including min/max
  greens) under CC-BY 4.0.
- **Main Roads WA**: signal-data spreadsheets (timings, link/offset plans,
  SCATS phase history) via TrafficMap, plus monthly cycle-time exports.
- **Dublin**: raw SCATS detector volumes as open data (data.gov.ie).
- **TfNSW TTD 2018/002** (superseded, ~2018 practice) — TfNSW's *own* recipe
  for approximating SCATS in microsimulation, and the best single source of
  defensible parameter values: fixed-time is unacceptable for adaptive sites;
  SCATSIM in-the-loop is for special cases; the recommended approach is
  **vehicle-actuated logic replicating the stretch-phase mechanism** — phases
  called on demand, minimum green then gap-out to maximum, unused time
  returned to the stretch phase — with nominal cycle ≈ **140 s** (less
  off-peak/minor routes), min green 5 s vehicle / 6 s pedestrian, **gap
  3–5 s, headway 0.8–1.4 s, waste 3–10 s**, offsets reconstructed as OP+LP,
  and modelled-vs-actual average green within ±20%.

## 5. Academic access

**[gap]** No formal NSW academic access program was found; published
Australian research using SCATS data (Sydney ITLS working papers, SCATS-MF /
SIDRA calibration) relied on ad-hoc data-sharing agreements. TfNSW runs a
practitioner-facing SCATS training portal (learn.scats.nsw.gov.au).

## 6. Consequences for the registry

None applied yet — recorded here for the DECISIONS/registry update when this
dossier is absorbed:

1. `A.signals.scats_phasing` stays `unobtained` and swept — unchanged.
2. The cycle sweep 80–140 s gains external support: documented SCATS user
   limits ~30–150 s, TTD nominal modelling cycle 140 s, Sydney CBD peak
   maximum 90 s — and now **operated Newcastle values**: 104–113 s at
   King/Steel (major arterial, brackets the assumed 110 s) and 72–81 s at
   Hunter/Steel on the corridor street itself, at/below the sweep's lower
   bound (evidence for the lower half of the sweep; see
   [08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md)
   §4 caveats). Worth citing in the field's `sweep_basis`.
3. A new, cheap acquisition option exists (the LX file) that would move
   `scats_phasing` from `unobtained` to `measured` for the strategic layer —
   licence review first; decision required.
4. TTD 2018/002's actuated parameters (min green, gap, headway, waste) are
   the right priors for any explicit signal model in MATSim
   ([04-matsim-implementation.md](04-matsim-implementation.md)) and should be
   declared as `literature`-sourced registry fields if that path is taken.

## Sources

- TfNSW Traffic Lights Location dataset: https://opendata.transport.nsw.gov.au/data/dataset/traffic-lights-location
- Volume counts API: https://opendata.transport.nsw.gov.au/data/dataset/nsw-roads-traffic-volume-counts-api ; Traffic Volume Viewer: https://www.transport.nsw.gov.au/operations/roads-and-waterways/corporate-publications/statistics/traffic-statistics/traffic-volume
- Forum thread on SCATS detector data: https://opendataforum.transport.nsw.gov.au/t/traffic-signal-volume-data/2650
- Traffic Signal Portal terms: https://www.transport.nsw.gov.au/trafficsignal/traffic-signal-portal-terms
- TfNSW refusal: https://jakecoppinger.com/2025/05/no-signal-for-pedestrian-safety-tfnsw-refuses-signal-data-during-national-road-safety-week/ ; https://walksydney.org/2025/09/20/why-wont-transport-for-nsw-share-scats-traffic-signal-phasing-data/
- Pricing and Sydney observations: https://jakecoppinger.com/2023/07/shining-a-light-on-the-traffic-signals-of-sydney/
- TTD 2018/002: https://standards.transport.nsw.gov.au/_entity/annotation/edd99ea5-a835-ed11-9db2-000d3ae019e0
- Victoria operation sheets: https://transport.vic.gov.au/business/road-and-traffic-management/traffic-lights/signal-coordination-and-automation/scats
- Main Roads WA signal data: https://www.mainroads.wa.gov.au/globalassets/technical-commercial/technical-library/road-and-traffic-engineering/traffic-modelling/operational-modelling/signal-data-information-for-modelling-a.pdf
- Dublin SCATS detector volumes: https://data.gov.ie/dataset/dcc-scats-detector-volume-jul-dec-2024
- SCATS-MF / SIDRA calibration: https://www.researchgate.net/publication/375496558_Use_of_SCATS_MF_to_Calibrate_SIDRA_Saturation_Flow
