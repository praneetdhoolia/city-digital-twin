# TIA harvest log — the systematic corridor pass (#78 route 2)

Standing opportunistic lane recorded in `DECISIONS.md` §9.76 and
[08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md):
harvest public NSW Planning Portal exhibition documents near the light-rail
corridor for republished, TfNSW-supplied SCATS material (interpreted history,
TCS plans, phase splits, cycle times). This file is the factual record of what
has been checked, so the next pass does not repeat it. Nothing in this file is
a model input.

**Licence position (unchanged, §9.76):** TIA content is validation/sweep-basis
evidence ONLY. It is never merged into a CC-BY artefact, and no registry value
is ever set from it. `A.signals.scats_phasing` stays `unobtained` for the 14
modelled intersections.

## Method (verified 25 Aug 2026)

- A panel case's full document listing, **including the per-document timestamp
  each attachment URL needs**, is rendered server-side on its public case page
  at `www.planningportal.nsw.gov.au/planning-panel/<slug>` — no API key, no
  session. Attachment URLs have the form
  `https://apps.planningportal.nsw.gov.au/prweb/PRRestService/DocMgmt/v1/PublicDocuments/DATA-WORKATTACH-FILE%20PEC-DPE-EP-WORK%20<CASE>!<yyyymmdd>T<hhmmss.SSS>%20GMT`.
- Individual attachments are also indexed by web search engines under their
  full timestamped URLs, so site-restricted searches on
  `apps.planningportal.nsw.gov.au` (and `majorprojects.planningportal.nsw.gov.au`
  for SSD documents, URL form
  `.../prweb/PRRestService/mp/01/getContent?AttachRef=<CASE>!<timestamp>+GMT`)
  are a working discovery channel for traffic documents by keyword.
- Each candidate PDF was downloaded, text-extracted and searched for
  `SCATS`, `phase split`, `cycle time`/`cycle length`, `interpreted history`
  and `TCS <n>` before any archiving decision. Text-layer coverage was checked
  (a scanned appendix without a text layer would defeat the keyword search);
  every scanned document below had a usable text layer.

## Pass of 25 Aug 2026 — applications checked, outcome

**Result: no new SCATS evidence found. Nothing archived.** The archive still
holds exactly one document, PPSHCC-137
(`data/raw/planning_tia/PPSHCC-137_643_hunter_st_tia.pdf`), whose evidence
covers TCS 923 (King St / Steel St) and TCS 1138 (Hunter St / Steel St) for
Tuesday 19 July 2022 — neither of them one of the 14 modelled intersections.

### On or near the corridor — documents fetched and scanned

| Case | Site | Document(s) scanned | SCATS-relevant content |
|---|---|---|---|
| PPSHCC-306 (RE2024/00002) | East End Stages 3–4: 105, 109, 111, 121 Hunter St; 3 Morgan St; 22 Newcomen St; 66–74 King St, Newcastle | Attachment 3C *Addendum to Traffic and Parking Studies* (112 pp); Attachment 14 *CN Referral Advice – Engineering (Traffic)* (5 pp) | **None.** The addendum names the Scott St / Newcomen St signals and the signalised pedestrian crossing on Scott St qualitatively, then defers to the Concept-DA SIDRA model (GTA, D/2017/00701 era) rather than reproducing SCATS data. No interpreted history, phase splits or cycle times. |
| PPSHCC-204 (DA2023/00419) | Same project, detailed DA (determined 15 Dec 2024) | Determination and conditions located; no separate TIA indexed among its attachments | Its traffic material is the same GTA addendum exhibited on PPSHCC-306 (checked above). |
| PP-2021-459 | 233 Wharf Rd, 250 Scott St, part 150–150A Scott St, Newcastle (planning proposal, approved) | Appendix B *Traffic Impact Assessment* = UrbanGrowth NSW, Newcastle Urban Transformation and Transport Project, rezoning of surplus rail corridor lands, March 2017 (45 pp; the two exhibited copies are byte-identical) | **None.** Strategic network modelling; one qualitative remark that scenario differences partly reflect "changes in signal phasing". No operated data. |
| PPSHCC-160 (711 Hunter St, Newcastle West) | Mixed use development | Only non-traffic attachments indexed (waste management plan scanned); no TIA found in the public index | None. |
| PPSHCC-22 (309 King St, Newcastle West) | Mixed use development | *Green Travel Plan* (13 pp) | None. |
| PPSHCC-221 (309 King St, Newcastle West) | Height modification | Modification assessment report only; no traffic appendix indexed | Not fetched — no traffic document exists on the public index. |
| PPS-2016HCC035 (990 Hunter St, Newcastle West) | "UP UP" site | Landscape design report is what the index surfaces; no TIA found | None. |
| SSD-9827 | 45 Honeysuckle Drive ("Horizon at Lee 5") | DPIE assessment report (81 pp) | None. |
| SSD-10378 | 42 Honeysuckle Drive | DPIE assessment report (65 pp) | None. |
| SSD-10251 | 42 Honeysuckle Drive (earlier application, withdrawn) | Agency response letters only | None. |
| SSD-106536974 | 700 Hunter St, Newcastle West (pub, hotel, 165 dwellings + rezoning) | **No documents yet** — status "Prepare EIS" | Watch item: the EIS transport appendix, when exhibited, is a strong SCATS candidate for the corridor's western end. |

### Checked and ruled out as off-corridor or off-region

PPSHCC-87 (Warrigal St / Park Rd, Adamstown — conditions of consent),
PPSHCC-32 (Kotara — school; its supplementary report's SCATS mention is for
Kotara intersections), PPSHCC-163 (Taree), PPSHCC-325 (Singleton),
PP-2020-323 (Chatswood — methodologically useful: its TIA states SIDRA models
were "calibrated based on historical SCATS data provided by TfNSW", confirming
the channel is standard practice state-wide), PAN-533624 (Kooragang Island),
PP-2023-1620 (Concord West).

## PPSHCC-306 — resolved, and a correction

The previous session could not fetch PPSHCC-306 because its attachment URLs
need per-document timestamps. Resolved this pass: the timestamps are on the
case page (`www.planningportal.nsw.gov.au/planning-panel/section-82-review`).
Both traffic attachments were fetched and scanned; neither contains SCATS
data, so neither was archived (rule: archive only documents carrying signal
evidence).

**Correction:** file 08 recorded PPSHCC-306 as "a related Section 8.2 review
for the same site" as PPSHCC-137 (643 Hunter St, Newcastle West). It is not.
PPSHCC-306 is the Section 8.2 review (RE2024/00002) of the **East End Stages
3–4** project at 105–121 Hunter Street, Newcastle — the corridor's **eastern**
end, around the Hunter/Newcomen, Hunter/Wolfe and Scott/Newcomen
intersections. (This is also the likely origin of file 08's original
"121 Hunter St" address slip, corrected on 25 Aug 2026.) File 08 carries a
matching correction note.

## Standing watch items for the next pass

- **SSD-106536974 (700 Hunter St, Newcastle West)** — EIS not yet exhibited;
  its transport assessment is the best known upcoming candidate for operated
  SCATS data at the corridor's western end (Hunter/Stewart Ave vicinity).
- **DA2025/00512 (711 Hunter St, Newcastle West)** — under assessment by the
  Hunter & Central Coast Regional Planning Panel; a TIA should appear on its
  panel case page when the assessment report is published.
- **City of Newcastle DA tracker** (`newcastle.nsw.gov.au` / `ncc.nsw.gov.au`)
  — the local-DA channel for the same document class sits outside the
  sandbox's network allowlist; harvesting it would need the domain added to
  `.claude/settings.json` with a provenance record, per the project's network
  rule.
- Searches for `"SCATS Interpreted History"` on the portal's document store
  currently surface **only** PPSHCC-137 for Newcastle. The corpus grows as new
  corridor DAs are exhibited; re-run the site-restricted searches in the
  Method section on a later pass.
