# The algorithms, in pseudo-code

> **FROZEN DOSSIER — research notes compiled 25 August 2026 as evidence for the SCATS build; the algorithm they describe is implemented (DECISIONS.md §9.88).** Current position: [`positions/signals-and-crossings.md`](../../../positions/signals-and-crossings.md).

Reference specifications for every control algorithm named in this dossier —
what SCATS actually computes, what the MATSim contrib controllers compute, and
the bespoke pieces (SCATS-strategic emulator, tram priority) that would have to
be written. Notation: `C` cycle length (s), `g` green time (s), `DS` degree of
saturation, one *stage* = a set of non-conflicting movements shown green
together.

All numeric constants here are **literature/documented values, not Newcastle
observations** — if implemented, each becomes a declared registry field with
provenance and a sweep or held-fixed rule.

## 1. SCATS degree of saturation (per lane, per green)

The measured quantity every strategic decision rests on. Source: SNUG DS
training deck; SCATS 6 FD.

```text
inputs per green interval on one lane:
  g          effective green duration (s)
  gaps[]     loop-unoccupied intervals during g (s)
  n          vehicles counted during g
  t          optimum space time for this lane (self-calibrated, ≈1.0 s)

T  = sum(gaps)                    # total space time
W  = T - t*n                      # wasted (unused) green
DS = (g - W) / g                  # may exceed 1.0 when over-saturated

self-calibration, per 24 h period:
  track max observed flow MF and its mean gap; set t from it
  (so DS=1.0 corresponds to this lane's real saturation discharge)
```

MATSim emulation note: `LinkSensorManager` has no gap detector. Two honest
proxies: (a) throughput-based — `DS ≈ (q_measured / q_saturation) / (g/C)`
using per-green discharge counts from `LinkLeaveEvent`s and the declared
saturation flow; (b) occupancy-time-based per the DS-estimation literature.
(a) is simpler and adequate at 1 s resolution.

## 2. SCATS strategic adaptation (per subsystem, per cycle)

What the regional computer does. Source: SCATS 6 FD; increments tagged
[commonly claimed] where the primary source gives only "small amount".

```text
each cycle, for the subsystem's critical intersection:
  DS_max = max over lanes of DS

  # cycle length: hold DS_max at ~0.90
  if DS_max > 0.90 + deadband:  C += min(step_up,  21)     # ~6 s routine
  if DS_max < 0.90 - deadband:  C -= min(step_dn,  21)
  clamp C to [LCL, HCL]                                     # user limits,
                                                            # ~30-40 .. 100-150 s

  # splits: equalise DS across competing approaches
  for each phase p: split[p] += k * (DS[p] - mean_DS)       # bounded ~±4%/cycle
  renormalise to 100%; respect per-phase minima
  # (implemented as selection/blending among ~4 stored split plans, by DS "voting")

  # offsets: pick offset/link plan by dominant flow direction
  # bias: keep a longer C that yields good offsets across married subsystems
  #       even where a shorter C would carry the demand

marriage/divorce:
  adjacent subsystems with similar required C link onto a common cycle;
  divorce when their required cycles diverge
```

Two published formulations pin down the [commonly claimed] pieces:

**Split-plan selection** (Wei et al. 2020 §3.7, after Lowrie 1990) — the
"voting" made precise:

```text
given candidate split plans A = {a_1..a_N}, current plan a_c with greens g_p:
  measure DS_p per phase under a_c                     # Eq. (10), the DS formula
  for each candidate a_j with greens g_p^j:
      DS̄_p^j = DS_p * g_p / g_p^j                     # inferred DS under plan j
  next plan = argmin_j  Σ_p DS̄_p^j                    # ≙ most-equalised DS
  # secondary literature: tally the winner over ~5 cycles before committing
```

**Cycle-length decision** (de Gier, Garoni & Rojas 2013, Appendix A.1 —
a peer-reviewed SCATS model built with VicRoads; their parameter values, not
NSW's):

```text
R = volume ratio (their DS proxy), band target [0.85, 0.95]
if C == MIN  and R > 0.4:  C = STOPPER                # fast start-up jump
if C == STOPPER and R < 0.2: C = MIN
if R > 0.95: C = min(C + STEP, MAX)                   # STEP = 6 s
if R < 0.85: C = max(C - STEP, STOPPER)
# their values: MIN 44 s, STOPPER 64 s, MAX 130 s (tram paper: 48-134 s)
# splits then S'_P = (S_P*DS_P / Σ S_P*DS_P) * (C' - n_phases*S_min - amber) + S_min
# fixed splits imposable on phases whose lane DS is unmeasurable (shared tram lanes)
```

## 3. SCATS tactical layer (local controller, within a cycle)

```text
given: phase sequence [A, B, C, ...], stretch phase = A (never skipped),
       per-phase min green + clearances (local safety times, not overridable)

for each non-stretch phase in sequence:
  if no demand registered:            skip phase entirely
  else: run min green, then extend second-by-second
        while detector shows headways < gap-out threshold
        until region-commanded max for this phase
  time saved (skips + early gap-outs) accrues to the stretch phase
  # => the stretch phase's realised green = its split + everything unused;
  #    it can run the whole cycle if nothing else is demanded

pedestrian phase: introduced on button demand (or automatically);
  walk >= 6 s; clearance-1 = crossing_length / 1.2 m/s; region may vary walk,
  never below local minimum
```

This is what TTD 2018/002 tells modellers to replicate with vehicle-actuated
logic: min green 5 s, gap 3–5 s, headway 0.8–1.4 s, waste 3–10 s, nominal
C ≈ 140 s, unused time returned to the stretch phase.

## 4. SYLVIA (as implemented in the contrib)

Source: `SylviaSignalController` / `SylviaPreprocessData`; Grether, Bischoff &
Nagel (2011).

```text
preprocess (offline, from the fixed-time plan):
  for each green setting: shorten to min green (5 s)      # "compressed" plan
  record extension points = seconds in compressed cycle where each
  group's green may be prolonged

runtime, every second t:
  advance compressed plan; fire scheduled onsets/droppings
  if t is at an extension point for group G and extension allowed:
     if cars within sensorDistance (10 m) of stop line on G's links/lanes
        and realised_green(G) < maxGreenScale * fixedtime_green(G)
        and (useFixedTimeCycleAsMaximalExtension =>
             realised_cycle <= fixedtime_cycle)
        and (checkDownstream => downstream links not full):
        extend G's green by 1 s (delay the dropping)
  # cycle- and offset-preserving by construction => coordination survives
```

Role in a SCATS approximation: SYLVIA ≈ the tactical layer (gap-out /
extension) running inside an engineered plan that stands in for the strategic
layer. Divergence from SCATS: saved time returns to the *plan*, not
specifically to a stretch phase — a stretch-faithful variant would bias all
recovered time to the declared main-road group (small change in the extension
budget accounting).

## 5. Lämmer (contrib `laemmerFix`)

Source: Lämmer & Helbing (2008); Kühnel, Thunig & Nagel (2018); Thunig et al.
(2019).

```text
every second, for each stage i:
  n̂_i(τ) = expected vehicles to clear if served after lead time τ
           (queue + arrivals forecast from sensor arrival rates)
  ĝ_i    = n̂_i / q_max_i                 # required green at saturation flow
  π_i    = n̂_i / (τ_i + ĝ_i)            # clearance efficiency (pressure-like)
  apply switching penalty τ_pen to stages != active (anti-thrashing)

stabilising regime (guarantee of service):
  approach j enters FIFO stabilisation queue when service interval
  since last green approaches its maximum (derived from desiredCycleTime T,
  maximalCycleTime 1.5T, and the approach's capacity utilisation via its
  determining lane, à la Webster)
  stages in the stabilisation queue pre-empt the optimising choice,
  served FIFO with guaranteed green g_s

combined regime = optimising unless stabilisation queue non-empty
overload: idle-time term floored at 0 => degenerates to periodic
          fixed-time-like service at the desired cycle  (engineered property)

parameters: desiredCycleTime 90 s, maximalCycleTime 135 s,
            intergreen 5 s, min green 5 s, fixed stage definitions
```

Note: Lämmer is *acyclic* — no fixed cycle or offsets — so it is **not** a
SCATS emulator; it is the "what would near-optimal adaptive control do"
comparator. Useful as an upper-bound arm, not as the S2 representation.

## 6. Webster fallback (no explicit signals)

For the implicit representation — capacity and delay instead of lights.
Source: Webster (1958); "Modeling Crossroads in MATSim" (2021).

```text
per signalised approach with assumed C and green share λ = g/C:
  capacity_link   = s * λ            # s = saturation flow ≈ 1800 veh/h/lane
  uniform delay   d1 = C(1-λ)² / (2(1-λx))     # x = v/c ratio
  (optional random-delay term d2 for x near 1)
  encode d1 as reduced freespeed on the approach link,
  or leave delay to emerge from the reduced capacity queue
# one representation only: EITHER reduced capacity/freespeed encodes the
# signal, OR an explicit signal meters a saturation-flow link. Never both.
```

This is the current repo state in generalised form: today the corridor's
signal effect is carried by `A.signals.delay_per_intersection_s` (24.75 s at
C=110) inside the run-time decomposition, swept via the cycle range.

## 7. Bespoke: SCATS-like strategic emulator for MATSim (design sketch)

A custom `SignalController` (seam in
[04-matsim-implementation.md](04-matsim-implementation.md) §4) that puts §2's
loop on top of fixed-time plans, mirroring what sumoITScontrol does for SUMO:

```text
state per signal system: current plan (cycle C, splits, offset)
sensors: per-approach discharge counts (LinkLeaveEvents during green)
         and queue estimates (getNumberOfCarsInDistance)

every cycle boundary:
  compute DS per approach   (throughput proxy, §1 note)
  adapt C by ±step toward DS_target=0.90 within [C_min, C_max]   # registry-swept
  shift splits ±k% toward DS equalisation, respect min greens
  keep offsets from the declared offset plan (recompute onsets/droppings
  for the new C by proportional stretch)

every second (tactical, optional):
  SYLVIA-style gap-out with saved time credited to the stretch group

corridor coordination: one shared C across the 14 systems (they are one
married subsystem chain in reality — Hunter/Scott is a single arterial),
offsets as a declared progression speed                       # assumed, swept
```

Everything the real SCATS would supply (C limits, initial splits, offsets,
stretch phase identity) is an assumed registry value with a sweep — the
emulator changes the *dynamics*, not the epistemic status.

## 8. Bespoke: tram priority controller (S2b/S3 as a mechanism)

```text
detection: LinkEnterEvent on the tram's approach link/lane
           (dedicated tramway => unambiguous; equivalent to a SCATS
            PT detector / Hurry Call input / SPE arrival estimate)
           detection distance ≈ 120 m (existing S2b assumption), i.e. the
           upstream tram link boundary nearest that distance

on tram detected, ETA = distance / v_tram:
  case green on tram stage and ETA <= extension_window (12 s assumed):
      hold green until tram clears or window exhausted        # green extension
  case red on tram stage:
      gap conflicting stages to min green, insert/advance tram stage
      after intergreen                                        # red truncation /
                                                              # phase recall
  conditionality (PTIPS-faithful variant):
      only grant when tram is behind schedule by > threshold  # conditional
                                                              # priority
compensation: following cycle returns borrowed green to cut stages
              (keeps the emulator's DS accounting honest)

sweep dimensions (replacing the scalar E.s2b.signal_delay_removed_share):
  full | partial | conditional priority; extension window; detection distance
  # Melbourne CA study (arXiv:1311.3590): partial/conditional keeps nearly
  # all tram benefit at a fraction of the cost to general traffic
```

The Melbourne study (same group as the SCATS model above; its "PU" scheme is
**VicRoads' operating practice**) specifies the machinery concretely enough to
port — reference values, all registry-declarable:

```text
detection: two detectors per priority approach —
  mid-link detector ~60 m after the last tram stop; end-link detector 7.5 m
  before the stop line; Δ tracks which the tram has passed (1: mid, 2: end,
  0: cleared the intersection)

partial priority (PU — VicRoads practice):
  budget: priority phases get at most 20% of C per cycle, taken from the
  nominal split of the biggest competing phase
  Δ=1 → run a CLEARANCE phase (ET, ~15%C) to flush queued cars (esp. right-
        turners) out of the tram's path, plus a short extension phase (B, 5%C)
  Δ=2 → run the EXTENSION phase (B, 20%C) to carry the tram through
  priority decisions commit at the next cycle start, not mid-cycle
  tram cleared (Δ=0) → terminate/skip ET and B; unused time returns to the
  phase it was taken from                                     # compensation

absolute priority (AU):
  on detection, terminate the running phase as soon as its min green is met,
  run the tram phase until the tram clears; skip DS/plan updates for any
  cycle whose phases were cut short          # keeps adaptation from polluting
                                             # its own statistics
conditional variants (PC/AC):
  grant only if tram late at detector d: travel_time > T̄_d where
  T̄_d = L_d / v̄_t + Σ_i ζ_i·ω_i   (distance/speed + expected dwell so far;
  their v̄_t = 27 km/h ex-dwell ≈ 18 km/h incl. dwell — cf. this repo's
  corridor speed assumptions)
```

The scalar `E.s2b.signal_delay_removed_share` (0.75, swept) remains the cheap
representation; this controller is the *mechanistic* alternative that produces
a delay-removed share as an **output** instead of an input. Comparing the two
on the same arm is itself a finding.

## Sources

- SNUG DS deck: https://snug.org.nz/wp-content/uploads/2023/07/12.3_DS.pdf
- SCATS 6 FD: https://www.aldridgetrafficcontrollers.com.au/ArticleDocuments/230/Introduction_To_New_Generation_Scats_6_5.pdf.aspx
- TTD 2018/002: https://standards.transport.nsw.gov.au/_entity/annotation/edd99ea5-a835-ed11-9db2-000d3ae019e0
- SYLVIA source: https://github.com/matsim-org/matsim-libs/tree/master/contribs/signals/src/main/java/org/matsim/contrib/signals/controller/sylvia
- Lämmer & Helbing (2008): https://arxiv.org/pdf/0802.0403 ; contrib laemmerFix: https://github.com/matsim-org/matsim-libs/tree/master/contribs/signals/src/main/java/org/matsim/contrib/signals/controller/laemmerFix
- Kühnel, Thunig & Nagel (2018): https://www.sciencedirect.com/science/article/pii/S1877050918304484 ; Thunig et al. (2019): https://www.sciencedirect.com/science/article/pii/S2352146518306343
- Webster delay in MATSim: https://www.sciencedirect.com/science/article/pii/S187705092100716X
- sumoITScontrol (SCATS-like controller design to port): https://arxiv.org/pdf/2604.23240 ; https://github.com/DerKevinRiehl/sumoITScontrol/
- Tram priority comparison (Melbourne; PU = VicRoads practice, algorithms 1–3 + conditional rule): https://arxiv.org/abs/1311.3590
- Wei, Zheng, Gayah & Li (2020), survey §3.7 (SCATS DS Eq. 10, plan-selection Algorithm 2): https://arxiv.org/pdf/1904.08117
- de Gier, Garoni & Rojas (2013), Appendix A.1 (cycle decision, split formula): https://arxiv.org/pdf/1112.3761
- de Gier, Garoni & Rojas (SCATS-inspired CA model): https://arxiv.org/pdf/1011.6211
