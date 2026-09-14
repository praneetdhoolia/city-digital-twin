# Signalling in Newcastle specifically

> **FROZEN DOSSIER — research notes compiled 25 August 2026 as evidence for the SCATS build; the algorithm they describe is implemented (DECISIONS.md §9.88).** Current position: [`positions/signals-and-crossings.md`](../../../positions/signals-and-crossings.md).

What is known — and provably not knowable from public sources — about how the
signals on and around the Hunter/Scott Street corridor actually operate. Tags
as in [01-scats-mechanics.md](01-scats-mechanics.md): **[documented]**,
**[commonly claimed]**, **[gap]**.

## 1. SCATS coverage and operation

**[documented]** All NSW traffic signals operate under SCATS, run by TfNSW
Network Operations: ">4,300 sites connected to SCATS" (TTD 2018/002, 2018),
~4,860 statewide by late 2025. The 24/7 operations hub is the **Transport
Management Centre** (Eveleigh, Sydney; opened 1999, recently upgraded), which
handles ~700 incidents/day with CCTV, VMS and signal intervention statewide.
Newcastle's signals are SCATS sites operated by TfNSW; PTIPS's stated coverage
of "greater metropolitan Sydney, **Newcastle** and Wollongong" corroborates the
SCATS interface is live there.

**[partially closed]** The *administrative* region is in data the repo already
holds: every signal site in the Newcastle box (295 sites, −33.05<lat<−32.75,
151.55<lon<151.85) carries **`RMS_Region = "HV"` (Hunter Valley)** in TfNSW's
Traffic Lights Location dataset
(`cities/newcastle/data/raw/signals/tfnsw_traffic_lights_location.xlsx`;
542 HV sites statewide, vs HARZ 1,949 / PARZ 886 / RIVZ 902 / IL 293 —
verified 25 Aug 2026). **[gap — remains]** whether the SCATS *regional
computer* region coincides with the RMS maintenance region, and the subsystem
structure of the corridor (which of the 14 intersections is the critical one,
what is married to what) — that still comes only from the region's LX file
(purchasable — see [03-data-availability.md](03-data-availability.md)).

**Already in the repo:** the 14 corridor intersections carry their real SCATS
site numbers (`Equipment_ID` from TfNSW's Traffic Lights Location dataset,
matched at mean 8.0 m / max 26.4 m — `DECISIONS.md` §9.24), and install dates
showing **8 of 14 were installed in 2018 for the light rail** (the
pre-intervention corridor had 6 signalised intersections). The signals can be
named in a request or a controller definition; their operation remains unknown
for the 14 modelled sites — but **operated SCATS history for two intersections
at the corridor's western approach (TCS 1138 Hunter/Steel: 72 s AM / 81 s PM;
TCS 923 King/Steel: 113 s AM / 104 s PM, 19 July 2022) is public** in a
planning-portal TIA — see
[08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md).

## 2. Newcastle Light Rail signal treatment

**[documented]** NLR context: opened 17–18 Feb 2019; 2.7 km, Newcastle
Interchange (at Wickham) to Pacific Park; ~500 m in the former heavy-rail
corridor then on-street via Hunter and Scott streets; **dedicated tramway
between Stewart Avenue and Newcomen Street, mixed running between Newcomen and
Pacific streets**; 40 km/h limit for trams and general traffic; six CAF Urbos
100 trams, catenary-free with charge-at-stop; 7–8 min peak headway.

**Tram aspects [documented]:** crossings between light rail and general
traffic display a **T instead of an arrow, white instead of green**; where
trams may proceed with parallel traffic a **white T is added below the green**
of the general lantern. Legal basis: **NSW Road Rules 2014, Part 17, rules
274–279** (red/yellow/white T lights for tram drivers; B-light equivalents for
buses). The governing standard is **AS 1742.14:2014** (paywalled), but its
tram-signal substance is publicly documented in official jurisdiction
supplements: the **VicRoads Network Technical Guide Supplement to
AS 1742.14** ("T lanterns shall be provided where the tram has conflicting
movements") and the **TfNSW Supplement to AS 1742** on the standards portal —
so the practice is **[documented]** even though the standard text is not open.

**How priority is delivered — partly documented, centrally a gap:**

- The mechanisms that exist in NSW are documented: **Hurry Call** local
  pre-emption is "usually associated with … a train or tram phase" (SCATS 6
  FD); the **SCATS Priority Engine** accepts arrival-time-based priority
  requests for buses and light rail; and **PTIPS** (GPS units on 5,000+
  buses reporting over cellular; vehicles running sufficiently late are
  automatically selected and priority requests passed to SCATS for a "green
  light run") **operates in Newcastle for buses** — it grew from a 2012 Route
  400 trial to all Greater Sydney operators and 15+ regional centres by 2022.
- **[gap]** No public document states *which* mechanism — PTIPS, SPE, local
  tram detection driving a Hurry Call phase, or a combination — is configured
  on the NLR corridor, nor with what parameters (detection distance, extension
  window, conditionality on lateness).
- What is documented around the gap: TfNSW/RMS **adjusted traffic-light
  phasing at Stewart Avenue** and installed signage after **200+ near misses**
  around Stewart Avenue, Steel Street and Worth Place in 2019 — motorists
  running reds against trams "that have the right of way" (Rail Express;
  Newcastle Herald, which also reported manual traffic controllers at the
  Stewart Avenue crossing in the opening period). The Engineers Australia REF
  submission (May 2016) records a tram crossing Stewart Avenue roughly **every
  5 minutes** at 10-minute headways (single track into the terminus) "with
  consequential stopping of road traffic", and criticised the REF's SIDRA
  modelling (LoS F forecast at Stewart Avenue and Union Street by 2028).
  Community commentary after opening criticised slow running through the city
  **[documented as commentary, not measurement]**. Precedent: for Sydney's CBD
  light rail, "proper prioritisation … came after some time" (Coppinger) — NSW
  on-street LRT priority is tuned post-opening; no equivalent public account
  exists for Newcastle.

**Modelling implication.** Treat NLR intersections as SCATS sites with a tram
phase callable on approach (detection → recall/extension), tram right of way at
the dedicated-tramway crossings, and **sweep the aggressiveness of priority**
(recall probability / extension window / share of delay removed) rather than
pinning it. The true configuration is not publicly knowable, which is exactly
the situation `DECISIONS.md` §0/§13 and the `E.s2b.signal_delay_removed_share`
sweep already encode. The research *changes the evidence base, not the
decision*: sweeping priority is right even in principle, because the real
setting is an operational choice TfNSW tunes over time.

## 3. Other signalling on Newcastle streets

- **Pedestrian crossings [documented]:** NSW does not use UK-style
  puffin/pelican classes; signalised crossings are SCATS sites (intersection
  walks or mid-block crossings) with push-button demand, ~6 s minimum walk,
  flashing-red clearance sized to crossing width (≈1.2 m/s), optional
  countdown timers, automated walk introduction where buttons are pressed in
  ≥85% of cycles.
- **Ramp metering [gap → likely none]:** SCATS has a ramp-metering subsystem
  (SRMS), used on Sydney motorways, but **no evidence of ramp metering
  anywhere in the Newcastle area** was found (M1 / Newcastle Link Road /
  Hunter Expressway sources make no mention). Reasonable to model none.
- **Rail level crossings [documented in general, thin for Newcastle]:** SCATS
  practice coordinates signal sites with rail crossings — early cut-off timed
  to boom-gate descent and clearance of the "no man's land" (Main Roads WA
  Appendix A §A.3.3.1; the NSW interface standard is TS 02670.3 "Level
  Crossing Interface"). In the corridor study area the 2014 heavy-rail
  truncation removed the CBD road/rail crossings; the light rail's Stewart
  Avenue crossing is controlled by **road traffic signals with T aspects, not
  boom gates**. Boom-gated crossings on the suburban lines are now
  **[verified in repo data]** (25 Aug 2026, grep of
  `cities/newcastle/networks/osm/railways.osm`, 191 `railway=level_crossing`
  nodes in the Newcastle box): **St James Road, Adamstown**
  (−32.9333, 151.7206: `crossing:barrier=double_half`, lights, bells, remote
  activation, camera supervision), **Clyde Street** (half barrier) and
  **Beaumont Street, Hamilton** (double_half), among others; the harvest's
  crossing nodes near the Honeysuckle corridor carry `crossing:barrier=no,
  crossing:light=yes` — consistent with signal-controlled, not boom-gated,
  light-rail crossings. This matters for the level-crossing
  workstream (issue #68 / task B1 in
  [06-project-implications.md](06-project-implications.md)): the closure
  mechanism being built in MATSim is about those suburban boom-gated
  crossings, not the corridor.
- **The light rail's own signalling [commonly claimed]:** street-running LRT
  of this type is driven **on sight** under the Road Rules, with the T-aspect
  intersections as the only wayside signalling on-street; no source describes
  any cab-signalled or interlocked section beyond the interchange throat. The
  catenary-free traction system has no bearing on intersection control. Treat
  as line-of-sight with signalised conflict points.

## Sources

- Wikipedia — Newcastle Light Rail: https://en.wikipedia.org/wiki/Newcastle_Light_Rail ; PTIPS: https://en.wikipedia.org/wiki/Public_Transport_Information_and_Priority_System ; Traffic signal operation in NSW: https://en.wikipedia.org/wiki/Traffic_signal_operation_in_New_South_Wales
- NSW Road Rules 2014 (Part 17, rr. 274–279): https://legislation.nsw.gov.au/view/whole/html/2021-10-20/sl-2014-0758
- Newcastle LR REF: https://www.transport.nsw.gov.au/system/files/media/documents/2019/Newcastle%20Light%20Rail%20Review%20of%20Environmental%20Factors%20(REF).pdf
- Engineers Australia REF submission (Apr 2016): https://www.engineersaustralia.org.au/sites/default/files/2022-07/response-review-environmental-factors-newcastle-light-rail-submission-apr-2016.pdf
- Stewart Ave phasing adjustment / near misses: https://www.railexpress.com.au/nsw-govt-adjusts-traffic-lights-in-newcastle-to-improve-tram-awareness/ ; https://www.newcastleherald.com.au/story/5829225/traffic-controllers-keep-trams-rolling-at-stewart-avenue-light-rail-crossing/
- NLR operations: https://www.railjournal.com/passenger/light-rail/first-test-run-for-newcastles-catenary-free-light-rail-line/ ; https://www.newcastletransport.info/plan-your-trip/light-rail/ ; https://nswtrains.fandom.com/wiki/Newcastle_Light_Rail
- SCATS Priority Engine: https://www.transport.nsw.gov.au/system/files/media/documents/2022/CST125-SCATsPriorityEngine-WCAG.pdf ; Prioritize: https://prioritize.net.au/?page_id=13
- TfNSW bus-priority case study: https://www.transport.nsw.gov.au/projects/strategy/transport-technology-strategy/delivering-transport-outcomes-technology/transport-2
- TMC: https://www.transport.nsw.gov.au/news-and-events/media-releases/revamped-transport-management-nerve-centre-reopens
- Main Roads WA Appendix A (level-crossing interface practice): https://www.mainroads.wa.gov.au/globalassets/technical-commercial/technical-library/road-and-traffic-engineering/traffic-modelling/operational-modelling/signal-data-information-for-modelling-a.pdf
- Coppinger on Sydney LRT prioritisation: https://jakecoppinger.com/2023/07/shining-a-light-on-the-traffic-signals-of-sydney/
- VicRoads NTG Supplement to AS 1742.14:2014 (T-lantern practice, public): https://www.vicroads.vic.gov.au/-/media/files/technical-documents-new/traffic-engineering-manual-v2/tem-vol-2-part-214--as-174214-traffic-signals-v20.ashx
- TfNSW Supplement to AS 1742 (standards portal, public): https://standards.transport.nsw.gov.au/_entity/annotation/3f87feae-e27b-f011-b4cc-7c1e52623d32
- PPSHCC-137 TIA with SCATS Interpreted History for TCS 923/1138: see [08-operated-signal-data-discovery.md](08-operated-signal-data-discovery.md)
