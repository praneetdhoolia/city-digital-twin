# The SCATS documentation corpus: what is restricted, what is public, and where

Result of a targeted hunt (25 Aug 2026) for SCATS technical documentation.
Bottom line: **the restricted set is small and precisely identifiable, and most
of its technical substance is legitimately public** — spread across a vendor
functional description, TfNSW's own public standards, other jurisdictions'
publications, and practitioner-tool manuals. This file is the map.

**Boundary applied.** No paywall circumvention and no pirated copies: TfNSW's
licensed SCATS manuals and personality data were not obtained through
unauthorised mirrors (e.g. Scribd uploads of licensed material were
disregarded). Everything below is either officially published or published by
its own author/vendor. A document obtained illegitimately could not be cited
or shipped in a reproducible package anyway.

## 1. What is actually restricted (the real "paywalled set")

| Item | Holder | Access route | Approx. cost |
|---|---|---|---|
| SCATS product manuals (Operations Manual, version reference manuals, WinTraff/Traffic Reporter user guides) | TfNSW (SCATS is its commercial product; scats.nsw.gov.au) | SCATS licence / SCATSLEARN practitioner training (learn.scats.nsw.gov.au); customer service desk | licence-bound |
| Region **LX file** (site/subsystem structure, cycle limits, split/offset/link plans) | TfNSW | Traffic Signal Portal request, restrictive terms | ~AU$200–220 / region |
| Interpreted SCATS history / actual cycle-time data / phasing explanation | TfNSW | same | ~AU$400–600 / item |
| SCATSIM interface + regional personality data (`.tc`, `.lx`, `.ram`) | TfNSW | licensed with SCATSIM | licence-bound |

The **open-data refusal** (April 2025, DECISIONS §9.21) covers publication of
phasing *data*; the items above remain purchasable/licensable individually.
The official scats.nsw.gov.au site publishes **no technical manuals** — only
case studies, strategy documents and a third-party licence list (verified).
One crack in the wall (25 Aug 2026): the SCATSLEARN portal's **SMUG 2026
conference resource index is publicly reachable without a login**
(https://learn.scats.nsw.gov.au/mod/resource/view.php?id=1468), listing
presentations on bus/emergency priority, pedestrian analysis and jurisdiction
deployments — the technical depth is inside the linked files, access to which
was not further probed here.

## 2. The public corpus, by substance

### 2.1 System behaviour (the operating-manual substance)

- **SCATS 6 Functional Description** (RTA/Aldridge, officially public) — the
  closest public equivalent of a system reference manual: hierarchy, modes,
  subsystems/marriage, DS control, tactical gap-out/skip, Hurry Call, cycle
  limits. Basis of [01-scats-mechanics.md](01-scats-mechanics.md).
  https://www.aldridgetrafficcontrollers.com.au/ArticleDocuments/230/Introduction_To_New_Generation_Scats_6_5.pdf.aspx
- **SNUG Degree-of-Saturation training deck** (SCATS user group, NZ) — the DS
  formula with worked detail, loop-length effects, self-calibration.
  https://snug.org.nz/wp-content/uploads/2023/07/12.3_DS.pdf
- **A Review of SCATS Operation and Deployment in Dublin** (McCann, JCT
  Symposium 2014) — an operator-city's account of SCATS architecture and
  management functions.
  https://www.jctconsultancy.co.uk/Symposium/Symposium2014/PapersForDownload/A%20Review%20of%20SCATS%20Operation%20and%20Deployment%20in%20Dublin.pdf
- **LinSig SCATS™-version User Guide** (JCT Consultancy, free download) —
  practitioner modelling tool built around SCATS concepts; documents SCATS
  phase/split-plan/stretch-phase data structures as a modeller consumes them.
  Index: http://www.jctconsultancy.co.uk/Support/documentation.php (3.3 SCATS
  edition PDF linked from there; direct fetches of the PDF URLs returned
  404/blocked in this session — retrieve via the index page).
- **TransCore SCATS overview** (US distributor, 4-page): deployment-level
  description. https://transcore.com/wp-content/uploads/2018/05/SCATS_4_Page_Digital.pdf

### 2.2 TfNSW's own public documents (the NSW-practice substance)

- **TTD 2018/002 Traffic Signals in Microsimulation Modelling** (superseded
  watermark) — TfNSW's recipe for approximating SCATS: stretch-phase actuated
  logic, nominal 140 s cycle, min greens, gap/headway/waste ranges, OP/LP
  offset reconstruction, ±20% green validation. The single most useful
  document for this project.
  https://standards.transport.nsw.gov.au/_entity/annotation/edd99ea5-a835-ed11-9db2-000d3ae019e0
- **Traffic Signal Design guideline suite** — public on the standards portal,
  16 sections + 5 appendices: geometry (Section 5), phasing and signal-group
  display, signs (Section 10), special situations (Section 15), **Appendix F
  Level Crossing Interface**, and the **Single Diamond Overlap Phasing**
  standard. This is the official design-side documentation of NSW phasing
  practice — never paywalled. Entry points:
  https://standards.transport.nsw.gov.au/_entity/annotation/f6e9dc3d-9bdb-f011-8544-6045bde5f32c (suite),
  https://standards.transport.nsw.gov.au/_entity/annotation/9421335b-b935-ed11-9db2-000d3ae019e0 (diamond overlap),
  https://standards.transport.nsw.gov.au/_entity/annotation/1fbd3c26-b535-ed11-9db1-000d3ae011f9 (Appendix F),
  https://www.transport.nsw.gov.au/system/files/media/documents/2023/Traffic%20signal%20design%20Section%2015%20Special%20situations.pdf (Section 15).
- **SCATS Core / SPE brochures, NSW case study** — product-level capability
  descriptions (see [01-scats-mechanics.md](01-scats-mechanics.md) sources).

### 2.3 Other jurisdictions publishing the same structures openly

- **Main Roads WA — Signal Data Information for Modelling** (Appendix A):
  the LX-file content family (split/offset/link plans, phase history) with
  real published examples; the template for what a purchased NSW LX would
  contain.
  https://www.mainroads.wa.gov.au/globalassets/technical-commercial/technical-library/road-and-traffic-engineering/traffic-modelling/operational-modelling/signal-data-information-for-modelling-a.pdf
- **Victoria** — per-intersection operation sheets, CC-BY 4.0.
- **Dublin** — raw SCATS detector volumes, open data (data.gov.ie).

### 2.4 Deployment and evaluation literature (behaviour under load)

- Sims & Dobinson (1980), Lowrie (1982) — origin papers (paywalled at IEEE,
  but the substance is reproduced across the free sources above).
- FHWA/NTL evaluations of SCATS deployments (public):
  *Incident Management Under SCAT Adaptive Control*
  (https://ntlrepository.blob.core.windows.net/lib/16000/16700/16706/PB2000104542.pdf).
  Note: Utah UT-03.28 *Adaptive Signal Control II* was checked and is
  SCOOT-focused — only ~2 pages on SCATS; not a manual substitute.
- SCOOT/SCATS comparison and Master Isolated evaluation papers (ResearchGate,
  author-shared) — the ±4%/cycle split increment and plan-selection detail.
- **Wei, Zheng, Gayah & Li (2020)** — open-access survey whose §3.7 gives the
  formal SCATS DS equation and plan-selection algorithm (after Lowrie 1990):
  https://arxiv.org/pdf/1904.08117
- **de Gier, Garoni & Rojas** (Melbourne, with VicRoads) — peer-reviewed
  SCATS models with full algorithm appendices: cycle decision with 6 s STEP
  and [0.85,0.95] band (https://arxiv.org/pdf/1112.3761, Appendix A.1) and
  tram priority as operated in Melbourne, PU = VicRoads practice
  (https://arxiv.org/pdf/1311.3590, §3, Algorithms 1–3). Extracted into
  [01-scats-mechanics.md](01-scats-mechanics.md) §5 and
  [05-algorithms.md](05-algorithms.md) §§2, 8 on 25 Aug 2026.
- **AS 1742.14:2014** stays paywalled, but its tram-signal substance is
  publicly documented by official supplements: VicRoads NTG Supplement
  (https://www.vicroads.vic.gov.au/-/media/files/technical-documents-new/traffic-engineering-manual-v2/tem-vol-2-part-214--as-174214-traffic-signals-v20.ashx)
  and the TfNSW Supplement to AS 1742
  (https://standards.transport.nsw.gov.au/_entity/annotation/3f87feae-e27b-f011-b4cc-7c1e52623d32).

### 2.5 Archival channels (checked; thin)

- **National Library of Australia**: holds *SCATS, Sydney Co-ordinated
  Adaptive Traffic System* (Department of Main Roads, **1983**, 8 pp.,
  illustrated) — a promotional booklet, not a manual; in copyright to 2033,
  readable in the reading room or copyable under fair dealing via Copies
  Direct. https://catalogue.nla.gov.au/catalog/2525800
- **Internet Archive**: no lawfully archived SCATS manual or functional
  description found.
- **RTA-era product brochure** (Armitage mirror of RTA532, ~2007):
  https://armitagegroup.com.au/wp-content/uploads/2020/06/512152-RTA532_SCATS_A4_Product_Brochure_07.pdf
- University library catalogues hold the Lowrie (1982) conference paper via
  IEEE/ITE subscriptions — the standard interlibrary-loan route for the two
  origin papers.

## 3. What remains genuinely unobtainable without payment/licence

Only two things of value to this project are *not* in the public corpus:

1. **The Newcastle region's operated configuration** — its LX file and cycle
   time history (purchasable; the licence-vs-reproducibility question in
   [03-data-availability.md](03-data-availability.md) §3 stands).
2. **The SCATS product manuals verbatim** — but their algorithmic substance
   is covered by §2.1 to the depth a simulator needs; what they add is
   operator procedure and UI, which this project does not need.

Conclusion: **the documentation hunt is closed.** The public corpus above is
sufficient to specify SCATS-like behaviour for MATSim
([05-algorithms.md](05-algorithms.md)) with every parameter carrying a citable
basis; the only purchase that would materially improve the model is the LX
file, and that is a data acquisition decision (decision required), not a documentation
gap.

Post-scriptum (25 Aug 2026): on the *data* side the second listed item is
narrower than first recorded — operated interpreted history for specific
intersections leaks legitimately into the public record through
planning-portal TIAs, including two Newcastle sites near the corridor
([08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md)).
The Newcastle region's LX file (subsystem structure, split/offset/link plans)
remains purchase-only.
