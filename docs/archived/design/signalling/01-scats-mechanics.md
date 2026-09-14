# How SCATS works, mechanically

> **FROZEN DOSSIER — research notes compiled 25 August 2026 as evidence for the SCATS build; the algorithm they describe is implemented (DECISIONS.md §9.88).** Current position: [`positions/signals-and-crossings.md`](../../../positions/signals-and-crossings.md).

SCATS — the Sydney Coordinated Adaptive Traffic System, developed and owned by
Transport for NSW (formerly RMS/RTA/DMR) — controls every traffic signal in
NSW, Newcastle included. This file records its mechanics precisely enough to
emulate its behaviour in a simulator, with each claim tagged **[documented]**
(traceable to a cited primary source), **[commonly claimed]** (recurs in
secondary literature, not confirmed in a primary source), or **[gap]**.

Primary sources: the RTA/Aldridge *New Generation SCATS 6 Functional
Description* ("SCATS 6 FD", read in full); TfNSW Technical Direction
*TTD 2018/002 — Traffic Signals in Microsimulation Modelling* (read in full;
watermarked SUPERSEDED, so its values are indicative of ~2018 practice); a
SCATS user-group training deck on Degree of Saturation (SNUG); Main Roads WA
*Signal Data Information for Modelling*, Appendix A.

## 1. Hierarchy

**[documented]** Three tiers, distributed:

- **Central Management Computer** — global data, access control, graphics,
  backup. Makes **no real-time traffic decisions**.
- **Regional computers** — each controls up to **250 intersections**; a system
  supports up to 64 regions (16,000 intersections). All *strategic*
  optimisation happens here. The region exchanges a message with every local
  controller **once per second** (minimum 300 bit/s links).
- **Local controllers** — one per intersection ("TCS site", identified by a
  TCS/site number — the `Equipment_ID` in TfNSW's Traffic Lights Location
  dataset, already joined to the 14 corridor intersections in
  `cities/newcastle/data/processed/network/A2_signal_control_corridor.csv`).
  The local controller performs *tactical* control and holds **all safety
  timings** — minimum green, pedestrian clearance, yellow, all-red — which the
  regional computer **cannot override**.

## 2. Strategic vs tactical control

**[documented]**

- **Strategic** (regional computer): from stop-line loop flow and occupancy,
  determines on an area basis the optimum **cycle length, phase splits and
  offsets**. Runs once per cycle per subsystem.
- **Tactical** (local controller): absorbs cyclic variation in demand. Phases
  **gap out** (terminate early) or are **skipped entirely** when undemanded.
  One phase — the main-road **"stretch phase"**, usually A — can never be
  skipped or terminated early in linked operation, because every controller in
  a linked group must hold the common cycle time. Time saved by other phases
  gapping out or skipping is **given to the stretch phase in the next cycle**;
  the stretch phase can run a whole cycle if nothing else is demanded. The
  extent of tactical freedom always remains under regional-computer control.
- **Operating modes**: **Masterlink** (normal adaptive — region commands phase
  sequence, maximum phase durations, walk durations and phase transition
  points; local controller times minimum green/walk and clearances itself);
  **Flexilink** (fallback time-of-day plans on comms loss, clocks synchronised
  to mains frequency or crystal, so coordination survives); **Isolated** (pure
  vehicle actuation). **Hurry Call** invokes a pre-programmed pre-emption
  "usually associated with an emergency phase or local pre-emption such as a
  train or tram phase" — the classic hard-priority hook, directly relevant to
  the light rail (see [02-newcastle-signalling.md](02-newcastle-signalling.md)).
  Other modes: Police Off/Red/Manual, Maintenance, Flashing Yellow.

## 3. Subsystems, marriage and linking

**[documented]** The **subsystem** is the basic strategic unit: 1–10 signal
sites containing exactly **one critical intersection**, whose splits are
adaptively and directly controlled; the other sites in the subsystem receive
non-variable or compatible splits. All sites in a subsystem always share one
cycle length. Subsystems **link ("marry") and unlink ("divorce")** with
adjacent subsystems — permanently or adaptively — to form larger systems on a
common cycle. A SCATS 6 region holds up to 250 subsystems.

Coordination is coded at two levels: **Offset Plans (OP)** between sites within
a subsystem (typically four per site) and **Link Plans (LP)** between
subsystems (typically four per subsystem). Each plan carries low/high offset
values applying at the stretch cycle length (XCL) and highest cycle length
(HCL), interpolated between. (TTD 2018/002; SCATS 6 FD.)

## 4. Degree of Saturation — the control variable

**[documented]** SCATS adapts on **DS**: the ratio of *effectively used* green
time to *available* green time, computed **per lane** from stop-line loop data
during green. The mechanically important detail: SCATS does not use volume or
occupancy directly — it uses **space time**, the loop-unoccupied time between
vehicles:

- Over one green of length `g`: total space time `T = Σ gaps`, vehicle count
  `n`, and **optimum space time** `t ≈ 1.0 s` — the average gap observed when
  the lane discharges at saturation flow (typically ~1,800 veh/h/lane).
- Wasted time `W = T − t·n`, and **`DS = [g − (T − t·n)] / g`**.
- `T = t·n` → DS = 100% (saturation flow for the whole green);
  `T > t·n` → undersaturated; `T < t·n` → **DS > 100%** — SCATS measures
  over-saturation and responds quickly to it.
- **Self-calibration**: every cycle SCATS measures flow and space time per lane
  and stores the **maximum flow (MF)** and its associated optimum space time
  for each 24 h period, so `t` tracks the lane's real saturation behaviour.

(SNUG DS training deck; SCATS 6 FD; consistent with the
`DS = (g − (h′ − h·n))/g` formulation in the academic DS-estimation
literature.)

## 5. How cycle, splits and offsets adapt

**[documented]** unless noted:

- **Cycle length**: adjusted to hold **DS ≈ 0.90 on the most saturated lane**
  of the subsystem's critical intersection. Absolute range **20–240 s**; user
  limits normally ~**30–40 s lower**, ~**100–150 s upper**. Cycle time "can
  vary by up to 21 seconds [per cycle], but this upper limit is resisted unless
  a strong trend is recognised" (SCATS 6 FD). **[commonly claimed]** the
  routine per-cycle increment is ±6 s, with the large step reserved for strong
  trends.
- **Phase splits**: expressed as **percentages of cycle time**, varied "by a
  small amount each cycle … to maintain equal degrees of saturation on
  competing approaches" (SCATS 6 FD). **[commonly claimed]** the Incremental
  Split Selection adjustment is bounded at roughly **±4% of cycle per cycle**;
  a site typically holds **four split plans** and selects/blends among them.
  The **plan-selection ("voting") rule now has a citable formalisation**
  (Wei, Zheng, Gayah & Li 2020, §3.7, attributing it to Lowrie 1990): for each
  candidate plan `j`, infer what each phase's DS *would have been* by scaling
  the measured DS by the green-time ratio — `DS̄ʲ_p = DS_p · g_p / gʲ_p` —
  then **select the plan minimising Σ_p DS̄ʲ_p** (equivalently, approaching
  equal DS across phases); secondary literature adds that votes are tallied
  over ~the last 5 cycles before a plan change commits. Peer-reviewed SCATS
  models corroborate the increment scale: de Gier, Garoni & Rojas (2011/2013,
  Melbourne, built with VicRoads) use a **fixed cycle STEP of 6 s** inside a
  deadband-controlled loop (their volume-ratio target band [0.85, 0.95], with
  MIN/STOPPER/MAX cycle structure), and their tram-priority companion paper
  adapts splits as **S′_P ∝ S_P·DS_P** renormalised over
  `C − Σ min-greens − amber`, with fixed splits imposable on hard-to-measure
  phases (shared tram/car lanes). Both remain models-of-SCATS, not SCATS
  source — hence still [commonly claimed] at the primary-document level.
  The mechanism's proper name is confirmed across independent secondary
  sources as **Incremental Split Selection (ISS)**: increment/decrement
  splits by small amounts each cycle, bounded at **±4% of cycle time**,
  aiming to minimise the DS of the busiest movement / equalise DS across
  approaches (or bias the main road). Deployed-behaviour corroboration from
  an adversarial source: US Patent 11,210,942 (trajectory-data SCATS
  optimisation) observes that in practice SCATS "green split plans are often
  designed to be very similar to each other, and the conditions for
  initiating plan change are usually conservatively set, resulting in a
  nearly-fixed green split regardless of actual traffic conditions" —
  independent support (with the Sydney-CBD/Coppinger evidence) for the
  defensibility of fixed-time-plus-gap-out approximations of SCATS.
- **Offsets**: chosen within each subsystem and between linkable subsystems.
  A deliberate bias: when a cycle time yields good offsets across several
  subsystems, SCATS **maintains that longer cycle even where a shorter one
  would carry the demand**, because good offsets on heavy links minimise total
  stops (SCATS 6 FD).
- **Phase terminology**: phases are labelled **A, B, C…**; any phase except the
  stretch phase can be skipped when undemanded (sequence A–C–A if B has no
  call). NSW practice adds **diamond overlap phasing** (F with half-diamonds
  F1/F2, and G/G1/G2 sets), where a phase set runs in combinations F, F2, F3,
  F+F1, F+F2 (TTD 2018/002, referencing RTA TS-TN-026/027).

## 6. Detection

**[documented]** **Inductive loops at the stop line, one per lane.** Loop /
detection-zone length is critical to DS accuracy — too short over-registers
space in slow dense traffic, too long goes "blind"; the research optimum is a
**4.5 m detection zone** (SCATS 6 FD; the SNUG deck says a 4.0 m *loop* — the
discrepancy is loop vs zone length). **Strategic detectors** must be at the
stop line (they measure how effectively green is used); **tactical detectors**
at the stop line also distinguish turning movements by lane usage and speed
differential. Advance detectors were "found unnecessary". Radar can substitute
temporarily when loops fail.

## 7. Pedestrians and variation routines

**[documented]**

- Pedestrian phases are **called by push-button** (or automated). The regional
  computer controls **walk termination** but can never cut below the local
  controller's minimum. NSW standard minimum walk ≈ **6 s**; clearance is
  split into **Clearance 1** (flashing red, ≈ crossing length ÷ 1.2 m/s) and
  **Clearance 2**; TTD screenshots show walk 6 s, clearance-1 11–18 s,
  clearance-2 6–7 s at a real site. In CBDs and high-demand locations walks
  are introduced automatically — TfNSW automates where the button is pressed
  in ≥85% of cycles. SCATS also runs **mid-block pedestrian crossings** as
  sites of their own.
- **Variation by timetable and special routines**: almost any manual function
  can be scheduled (e.g. automatic pedestrian introduction on late-shopping
  nights); a library of "special routines" tailors each site's behaviour —
  this is the action-list machinery. **Strategic Inputs** bind detectors,
  phases and time intervals into the strategic calculation and are the
  standard hook for feeding priority calls into strategic control.

## 8. Priority mechanisms

**[documented]** Three distinct mechanisms:

1. **Hurry Call** — local pre-emption to a pre-programmed phase (train / tram /
   emergency).
2. **Route Pre-emption** — an operator- or system-managed sequential green
   window through a set of intersections, typically for emergency vehicles.
3. **SCATS Priority Engine (SPE)** — network-level public-transport priority
   (developed from 2015 by Prioritize for RMS ITS, now a TfNSW product):
   authorised clients issue priority requests for buses, light rail, freight
   and emergency vehicles; each request carries the vehicle's **estimated
   arrival time, entry lane and departure lane**; SPE arranges an earlier
   green or a green extension and arbitrates competing requests. **PTIPS**
   (see [02-newcastle-signalling.md](02-newcastle-signalling.md)) is the
   GPS-tracking system that generates lateness-conditional bus priority
   requests into SCATS.

## 9. What a SCATS "phasing" dataset contains

**[documented]** Two artefact families define a site's behaviour (TTD 2018/002
§3–6; Main Roads WA publishes the same structure openly):

- **LX file** (one per SCATS region, SCATS command syntax): TCS number
  (`INT=`), subsystem (`SS=`), lowest/highest cycle length (`LCL=`, `HCL=`),
  stretch cycle (XCL), **split plans** (running order + initial % splits,
  stretch phase coded `0P…`), **offset plans** (`PPn=low,high` to the start of
  a named phase), **link plans** (`LPn=` subsystem offsets low/high against a
  master site), phase clearance times, walk green times, special times (late
  starts). *Not* in the LX: phase minimum greens, late start and red-arrow
  times — those live in controller ROM/RAM "Local Times" (late start, min
  green, early cut-off, yellow, all-red, max green, walk/clearance per phase).
- **History files**: per-site logs of **actual phase sequence, phase durations
  and cycle times** (24 h, retained ~6–24 months); **event history**
  additionally logs every signal-group and Walk activation (usable to estimate
  pedestrian and alternative-phase demand frequency). **Traffic Reporter**
  subsystem graphics give the day's split plan, link plan, nominal vs required
  cycle length, and marriage state over 24 h. Detector-level volume (VO/VK)
  and occupancy series round out the set.

A complete phasing package per site is therefore: site id + region +
subsystem; phase configuration and sequence; split plans (%); cycle limits and
plans; offset/link plans; safety times; pedestrian times; plus operated history
(phase and cycle time series). This is exactly what Main Roads WA publishes and
TfNSW does not (see [03-data-availability.md](03-data-availability.md)).

## 10. Key numbers at a glance

| Parameter | Value | Source |
|---|---|---|
| DS target (most saturated lane) | ≈ 0.90 | SCATS 6 FD |
| DS formula | DS = [g − (T − t·n)]/g, t ≈ 1.0 s | SNUG deck |
| Cycle range (absolute / usual user limits) | 20–240 s / ~30–40 min, ~100–150 max | SCATS 6 FD |
| Max cycle change per cycle | up to 21 s, resisted; ~6 s routine [commonly claimed] | SCATS 6 FD / literature |
| Split increment | small per cycle; ~±4% of cycle [commonly claimed] | SCATS 6 FD / literature |
| Nominal cycle for NSW microsimulation | 140 s | TTD 2018/002 |
| Minimum green | 5 s vehicles, 6 s pedestrians | TTD 2018/002 |
| VA gap / headway / waste (modelling) | 3–5 s / 0.8–1.4 s / 3–10 s | TTD 2018/002 |
| Yellow / all-red | ~4.0–6.4 s / ~1–3.5 s (site-specific) | TTD; NSW wiki; MRWA |
| Detection zone | 4.5 m, stop line, one per lane | SCATS 6 FD |
| Subsystem size | 1–10 sites, exactly 1 critical | SCATS 6 FD |
| NSW SCATS sites | >4,300 (2018); ~4,860 (2025) | TTD; Wikipedia |

Note for the registry: the repo's assumed corridor cycle (110 s, swept
80–140 s, `A.signals` fields) sits comfortably inside the documented user
limits, and the sweep's upper bound coincides with TTD 2018/002's nominal
modelling cycle — the existing sweep range is better supported by this research
than previously recorded. Sydney CBD is operated at a 90 s maximum cycle and
behaves near-fixed-time in peak [documented via Coppinger] — evidence that a
fixed-time or gap-extension approximation of SCATS is defensible in a dense
signalised area.

## Sources

- SCATS 6 Functional Description (RTA/Aldridge): https://www.aldridgetrafficcontrollers.com.au/ArticleDocuments/230/Introduction_To_New_Generation_Scats_6_5.pdf.aspx
- TfNSW TTD 2018/002 Traffic Signals in Microsimulation: https://standards.transport.nsw.gov.au/_entity/annotation/edd99ea5-a835-ed11-9db2-000d3ae019e0
- SCATS User Group, Degree of Saturation training deck: https://snug.org.nz/wp-content/uploads/2023/07/12.3_DS.pdf
- Main Roads WA, Signal Data Information for Modelling, Appendix A: https://www.mainroads.wa.gov.au/globalassets/technical-commercial/technical-library/road-and-traffic-engineering/traffic-modelling/operational-modelling/signal-data-information-for-modelling-a.pdf
- TfNSW SCATS Core brochure: https://www.transport.nsw.gov.au/system/files/media/documents/2022/SCATS-Core-brochure-Final-web-spreads_0.pdf
- SCATS Priority Engine: https://www.transport.nsw.gov.au/system/files/media/documents/2022/CST125-SCATsPriorityEngine-WCAG.pdf and https://www.aldridgetrafficcontrollers.com.au/scats/adaptive-traffic-management/scats-priority-engine-spe
- Wikipedia — SCATS: https://en.wikipedia.org/wiki/Sydney_Coordinated_Adaptive_Traffic_System ; Traffic signal operation in NSW: https://en.wikipedia.org/wiki/Traffic_signal_operation_in_New_South_Wales
- Sims & Dobinson (1980), IEEE Trans. Veh. Tech.: https://ieeexplore.ieee.org/document/1622746/
- SCOOT and SCATS: A Closer Look into Their Operations: https://www.researchgate.net/publication/274137098_SCOOT_and_SCATS_A_Closer_Look_into_Their_Operations
- DS estimation (KSCE): https://link.springer.com/article/10.1007/BF02829156 and https://www.sciencedirect.com/science/article/pii/S1226798824026722
- Coppinger (2023), Shining a Light on the Traffic Signals of Sydney: https://jakecoppinger.com/2023/07/shining-a-light-on-the-traffic-signals-of-sydney/
- Wei, Zheng, Gayah & Li (2020), A Survey on Traffic Signal Control Methods (§3.7 formalises SCATS DS + plan selection): https://arxiv.org/pdf/1904.08117
- de Gier, Garoni & Rojas (2013), MFDs under adaptive signal systems, Appendix A.1 "SCATS cycle length decision" (STEP 6 s, band [0.85,0.95], MIN/STOPPER/MAX): https://arxiv.org/pdf/1112.3761
- Same group, A Comparison of Tram Priority at Signalized Intersections (split rule S′∝S·DS, §3.2): https://arxiv.org/pdf/1311.3590
- US Patent 11,210,942 (background characterisation of deployed SCATS split behaviour): https://patents.google.com/patent/US11210942B2/en
