# Operated SCATS data for Newcastle found in a public planning document

Discovery made 25 Aug 2026, extending [03-data-availability.md](03-data-availability.md)
and partially reopening the "documentation hunt is closed" conclusion of
[07-documentation-corpus.md](07-documentation-corpus.md) on the *data* (not
documentation) side: **real, operated SCATS configuration and history for two
Newcastle intersections is public**, republished inside a traffic impact
assessment on the NSW Planning Portal. Tags as elsewhere: **[documented]**,
**[gap]**.

**Status of the numbers below: evidence, not inputs.** Nothing here has been
acquired into `data/raw/`, joined to a layer, or used to change a registry
value. Bringing any of it into the package is an decision required that must
follow the provenance rules (immutable raw download + `provenance_*.json`,
manifest regeneration) and a licence check (planning-portal documents are
public records exhibited under the EP&A Act; the SCATS data inside them was
supplied by TfNSW to the applicant's consultant — republication terms for
third-party reuse are not stated in the document).

## 1. The channel

**[documented]** Development applications assessed through the NSW Planning
Portal exhibit their traffic impact assessments as public documents, and NSW
practice requires signalised-intersection SIDRA models to be built from
**TfNSW-supplied SCATS data**. The TIAs therefore republish, in their
appendices, exactly the material TfNSW refuses to release as open data
(`DECISIONS.md` §9.21) and sells through the Traffic Signal Portal
([03-data-availability.md](03-data-availability.md) §3):

- **Traffic Control Signal (TCS) plans** — the intersection layout / signal
  design drawing;
- **SCATS Interpreted History** — per-site operated statistics (see §3, the
  actual content is richer than the §9.21 refusal implied was withheld);
- **pedestrian call proportions** derived from the history.

The channel is per-intersection and opportunistic — it yields data only where
someone has recently sought development consent nearby — but it is free,
public, and citable.

## 2. The specific find: PPSHCC-137 (643 Hunter Street, Newcastle West)

*(Correction, 25 Aug 2026, made when the document was archived: this file
first recorded the site as "121 Hunter Street". The document's own title page
says **643 Hunter Street, Newcastle West** — consistent with its two study
intersections both being at Steel St, at the corridor's western end. Archived
copy: `data/raw/planning_tia/PPSHCC-137_643_hunter_st_tia.pdf`, sha256
`e351b84f…`, with `provenance_planning_tia.json`.)*

**[documented]** Traffic impact assessment prepared for Next Level Seven Pty
Ltd, dated 1 September 2022 (report ref 22106-R01V03-220901), exhibited as
document `PPSHCC-137` on the NSW Planning Portal (245 pp., ~10.9 MB):

https://apps.planningportal.nsw.gov.au/prweb/PRRestService/DocMgmt/v1/PublicDocuments/DATA-WORKATTACH-FILE%20PEC-DPE-EP-WORK%20PPSHCC-137!20230328T025624.102%20GMT

(Retrieved and read in full 25 Aug 2026. A related Section 8.2 review for the
same site is exhibited as PPSHCC-306.)

Contents relevant here:

- **Appendix E — TCS plans** for the two modelled intersections;
- **Appendix F — SCATS Interpreted History**: *"Periodic statistics"* reports
  for **site 923 (King St / Steel St)** and **site 1138 (Hunter St / Steel
  St)**, full 24 h of **15-minute intervals** for **Tuesday 19 July 2022**
  (post-light-rail operation);
- **Appendix G** — peak-hour pedestrian-call proportions derived from the
  history;
- narrative confirmation (§5.2.1 of the TIA) that phasing arrangement and
  cycle times in SIDRA came from this data.

## 3. What SCATS Interpreted History actually contains (verified example)

Each 15-minute interval reports, as `Frequency / Minimum / Maximum / Average /
Total` (durations in seconds):

- **per phase** (A, D, E, G… as configured at the site) — how many times it
  ran and its duration statistics;
- **cycle length three ways** — `Nominal cycle length` (the strategic
  commanded cycle), `Active cycle length`, and `Actual cycle` (realised,
  including tactical variation);
- **per signal group** (site 1138 shows groups 1–16) — realised green
  durations per group, i.e. movement-level resolution below phase level;
- **per pedestrian movement** — how often each walk ran (the basis of
  Appendix G's call proportions).

This confirms, against a real Newcastle example, the history-file description
in [01-scats-mechanics.md](01-scats-mechanics.md) §9, and shows phase
*frequencies* (skipping visible as frequency < cycle count) and tactical
variation (Actual vs Nominal cycle spread) are directly observable from the
product TfNSW supplies.

## 4. Extracted operated values (evidence for the sweep ranges)

**[documented]** SIDRA site cycle times the consultant derived from the
interpreted history (AM ≈ 08:00, PM ≈ 17:00 peak-hour models):

| Site | Intersection | AM cycle | PM cycle |
|---|---|---|---|
| TCS 1138 | Hunter St / Steel St (western corridor, dedicated-tramway section) | **72 s** | **81 s** |
| TCS 923 | King St / Steel St (parallel arterial) | **113 s** | **104 s** |

Directly read from Appendix F for site 1138, 08:00–08:15 on 19 July 2022:
nominal cycle length 60–76 s (avg 68), actual cycle 42–82 s (avg 65) over 13
cycles; 08:15–08:30: nominal 68–81 s (avg 72). Phases A, D, E all ran every
interval; groups 3/4/11–16 ran in only some cycles (demand-dependent
phases/walks visibly skipped).

Implications for the registry's assumed values (`A.signals`, cycle 110 s swept
80–140 s) — *evidence, not yet a change*:

- King/Steel's 104–113 s operated cycle sits close to the assumed 110 s —
  the assumption is realistic for a major Newcastle arterial intersection.
- Hunter/Steel — an intersection **on the light-rail street itself** — runs
  **72–81 s**, at/below the sweep's lower bound of 80 s. One plausible
  reading: corridor sites are operated on shorter cycles than the assumed
  110 s (shorter cycles cut tram and pedestrian delay at the cost of
  capacity). This strengthens the case for the sweep's lower half and argues
  against narrowing the sweep upward.
- Caveats before any registry change: **TCS 1138 is not one of the 14
  modelled corridor intersections** (A2 `scats_site_id` values: 4762, 4770,
  4764, 782, 4765, 1656, 1655, 1977, 4766, 2901, 4767, 4768, 1875, 4769) —
  it sits at the corridor's western approach; the observation is one
  mid-winter Tuesday in 2022; and school-holiday/COVID-era effects were not
  checked. Treat as a prior, not a measurement of the modelled sites.

## 5. What this changes, and what it does not

1. **`A.signals.scats_phasing` stays `unobtained`** for the 14 modelled
   intersections — nothing here observes them. The §0/§13 sweep discipline is
   unchanged.
2. **A third acquisition route now exists** alongside "refused as open data"
   and "purchasable ~AU$200–600": *harvest public TIAs* near the corridor for
   republished interpreted history. Zero cost, public provenance, but
   coverage is accidental. A systematic pass over Newcastle DA/SSD documents
   (City of Newcastle DA tracker + Planning Portal major projects) for the
   corridor intersections is a bounded, legitimate task — **decision required
   whether to spend the effort; if adopted, each PDF lands under `data/raw/`
   with provenance like any acquisition.**
3. **The sweep's lower bound gains empirical support** (§4). Worth citing in
   `sweep_basis` when the rung-1 registry sharpening
   ([06-project-implications.md](06-project-implications.md) §2) happens.
4. The find validates the §9.21 framing: TfNSW's refusal governs *bulk open
   publication*, not the existence of public per-site instances.

## Sources

- PPSHCC-137 TIA (Next Level Seven Pty Ltd, 1 Sep 2022): https://apps.planningportal.nsw.gov.au/prweb/PRRestService/DocMgmt/v1/PublicDocuments/DATA-WORKATTACH-FILE%20PEC-DPE-EP-WORK%20PPSHCC-137!20230328T025624.102%20GMT (retrieved 25 Aug 2026)
- NSW Planning Portal, state development applications (the exhibition channel): https://www.planningportal.nsw.gov.au/development-and-assessment/state-development-applications
- City of Newcastle DA tracker (local channel for the same document class): https://newcastle.nsw.gov.au/development/development-applications
- Context: TfNSW refusal and pricing — [03-data-availability.md](03-data-availability.md) §§2–3
