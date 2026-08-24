# Mode × demographics: the observed inventory, and one run measured against it

**DIAGNOSTIC MEASUREMENT OF AN EXISTING RUN — NOT A RESULT ABOUT THE LIGHT
RAIL.** This document records (a) which mode × demographic cells are actually
*observed* in the held data, and (b) how the trips of one completed run
distribute across age, sex and employment against those cells. Nothing here
compares scenario against scenario, and nothing here is current model output:

> **The run measured is `results/20260821T175907_1000it_25pct` — arm A of the
> CLOSED `F4-walk-wedge` comparability family (DECISIONS.md §9.58–§9.64), the
> PRE-REPAIR baseline. The §9.68/§9.69 ride and walk repairs post-date it. Do
> not read any number below as the current model.**

Produced by `src/analyse/measure_demographic_modes.py` (issue #50); the full
machine-readable report is
`results/20260821T175907_1000it_25pct/_demographic_modes.json`. Reproduce:

```
python src/analyse/measure_demographic_modes.py results/20260821T175907_1000it_25pct
```

Measured 25 Aug 2026. The 67/143 holdout under `data/processed/validation/`
is not read by the script and is untouched here.

---

## 1. Inventory — what is observable, and what is not

Checked table by table in the held data (consistent with
[`docs/design/mode-individualisation.md`](../design/mode-individualisation.md) §3):

| observable cell | held? | where | size / geography |
|---|---|---|---|
| JTW mode × **sex** | **✅ held** | `data/processed/census/census2021_G62_SA1.csv` (2021 Census G62, one-method journeys to work) | 1,500 core-tier SA1s; identified one-method journeys M = 97,348, F = 77,962 |
| JTW mode × **age** | ❌ not held | G62 carries no age dimension | acquisition item (issue #63: ABS TableBuilder JTW mode × age), not a modelling gap |
| HTS mode × age / employment / income | ❌ not held | `data/processed/hts/hts_mode.csv`, `hts_purpose.csv` are LGA-level aggregates with **no demographic column** (verified mechanically by the script) | — |
| mode × **employment** | ⚠ only implicitly | G62 is journeys *to work* — workers-only by construction; no mode split by employment category exists | — |
| population age × employment | ✅ held, no mode dimension | G46A/B (already consumed by B1) | — |
| occupation × age × sex | ✅ held, no mode dimension | G60A/B (unconsumed) | — |
| industry × age × sex | ✅ held, no mode dimension | G54A/B (unconsumed) | — |

So the **only** observed mode × demographic family today is **commute
mode × sex**. Everything else in §3 below is a modelled table with no observed
counterpart, published for the record, not for comparison.

### Thin observed cells (cannot constrain anything)

Cells under 100 journeys (the script's `THIN_CELL_MIN` reporting flag) carry
ABS small-cell perturbation noise on top of sampling noise: **Ferry (M 11,
F 27), Tram/light rail (M 35, F 15), Taxi/Rideshare (M 9, F 14), Train F
(63), Motorbike F (42), Truck F (0)**. These rows are inventory, not
constraints.

### Caveats that must travel with every observed number

- **2021 was a COVID census.** Car share is WFH-inflated (56,619 worked at
  home; 45,289 did not go to work on census day, against 179,761 one-method
  journeys) and PT had collapsed. Treat the observed shares as *structure*
  (relative splits, sex ratios), never as level targets.
- **Commute only.** G62 observes journeys to work; the comparable modelled
  slice is trips ending at a `work` activity, nothing broader.
- **Denominator.** Shares are within the sum of the twelve identified
  one-method mode cells per sex, which sits ~2.5% below the `One_method_Tot`
  column (small-cell perturbation/suppression); tables dividing by
  `One_method_Tot` will differ slightly.
- **Sample.** The run is a 25% population sample; modelled counts are sample
  counts, shares are the comparable quantity.

## 2. Commute mode × sex — modelled vs observed (the one real comparison)

Modelled: arm A trips ending at a `work` activity, joined to B1 sex
(n: M 29,308, F 28,185). Observed: G62 one-method JTW, core-tier SA1s,
shares within each sex. Every mode individually; the model's single `pt`
qsim mode is compared against the union of the four observed PT modes,
which are listed separately first.

| observed mode | model mode | obs M n | obs M share | obs F n | obs F share |
|---|---|---:|---:|---:|---:|
| Train | pt | 126 | 0.13% | 63 † | 0.08% |
| Bus | pt | 363 | 0.37% | 573 | 0.74% |
| Ferry | pt | 11 † | 0.01% | 27 † | 0.03% |
| Tram/light rail | pt | 35 † | 0.04% | 15 † | 0.02% |
| Taxi/Rideshare | *(not modelled, §9.42)* | 9 † | 0.01% | 14 † | 0.02% |
| Car as driver | car | 87,813 | 90.21% | 69,812 | 89.55% |
| Car as passenger | ride | 4,236 | 4.35% | 4,962 | 6.37% |
| Truck | *(model truck = freight tier, no person)* | 1,561 | 1.60% | 0 † | 0.00% |
| Motorbike/scooter | motorbike | 541 | 0.56% | 42 † | 0.05% |
| Bicycle | bike | 596 | 0.61% | 202 | 0.26% |
| Other | *(no counterpart)* | 223 | 0.23% | 122 | 0.16% |
| Walked only | walk | 1,834 | 1.88% | 2,130 | 2.73% |

† thin cell (< 100 journeys) — perturbation-dominated, listed for inventory only.

Modelled against observed, per model mode (Δ = modelled − observed, percentage
points; observed Taxi/Truck/Other have no modelled counterpart and are absent
here, so the observed column sums to slightly under 100%):

| model mode | observed modes | obs M | mod M | Δ M (pp) | obs F | mod F | Δ F (pp) |
|---|---|---:|---:|---:|---:|---:|---:|
| bike | Bicycle | 0.61% | 7.77% | **+7.16** | 0.26% | 7.57% | **+7.31** |
| car | Car as driver | 90.21% | 82.02% | **−8.19** | 89.55% | 82.47% | **−7.08** |
| motorbike | Motorbike/scooter | 0.56% | 0.31% | −0.25 | 0.05% † | 0.32% | +0.27 |
| pt | Train + Bus + Ferry + Tram/light rail | 0.55% | 5.56% | **+5.01** | 0.87% | 5.44% | **+4.57** |
| ride | Car as passenger | 4.35% | 0.18% | **−4.17** | 6.36% | 0.15% | **−6.22** |
| walk | Walked only | 1.88% | 4.16% | +2.28 | 2.73% | 4.05% | +1.32 |

### What the comparison says

1. **The model's commute mode split is nearly sex-invariant; the observed one
   is not.** Modelled M and F columns differ by ≲0.5 pp everywhere, because
   nothing in the choice model is sex-conditioned. The observed data has real
   sex structure the model cannot reproduce: bus F ≈ 2× M (0.74% vs 0.37%),
   motorbike M ≈ 10× F (0.56% vs 0.05%), car-as-passenger F ≈ 1.5× M (6.37%
   vs 4.35%). These *ratios* are the COVID-robust part of G62.
2. **Bike +7.2 pp and ride −4.2/−6.2 pp are the same defect seen from two
   sides** — the known pre-repair bike overshoot absorbing unpairable
   passenger demand (DECISIONS.md §9.68's motivation). The commute slice
   shows it is not only a child/escort phenomenon: employed adults' work
   trips carry it too.
3. **car −7 to −8 pp and pt +4.6/+5.0 pp carry the COVID caveat in opposite
   directions.** 2021 observed car is WFH-inflated and observed PT collapsed
   (bus 0.37–0.74% against HTS-era PT near 3.8% of all trips), so the true
   level gaps are smaller than these deltas; sign and rough size remain
   informative, levels do not.
4. **motorbike is the one mode inside noise** (|Δ| ≤ 0.3 pp) — though the
   model misses its strong observed sex skew (point 1).

## 3. Modelled tables with no observed counterpart (record only)

No observed cell exists for any table in this section (see §1) — published
so the next repair family has a pre-repair reference, **not** for
calibration. New observables, when acquired, enter as constraints, never
targets; the 67/143 split does not move. Trips tabulated: 554,922 by B1
residents (29,110 further trips by freight/external-tier agents carry no
person attributes and are excluded).

### All trips, mode share by age band

| age band | bike | car | motorbike | pt | ride | walk | n |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0–4 | 0.462 | 0.000 | 0.000 | 0.179 | 0.006 | 0.353 | 6,913 |
| 5–11 | 0.484 | 0.000 | 0.000 | 0.155 | 0.006 | 0.356 | 19,951 |
| 12–17 | 0.496 | 0.000 | 0.000 | 0.154 | 0.003 | 0.346 | 23,471 |
| 18–24 | 0.172 | 0.625 | 0.002 | 0.080 | 0.001 | 0.120 | 56,546 |
| 25–34 | 0.071 | 0.838 | 0.002 | 0.037 | 0.000 | 0.052 | 94,182 |
| 35–44 | 0.049 | 0.884 | 0.003 | 0.025 | 0.000 | 0.039 | 90,712 |
| 45–54 | 0.045 | 0.894 | 0.003 | 0.023 | 0.000 | 0.035 | 89,336 |
| 55–64 | 0.051 | 0.884 | 0.003 | 0.022 | 0.000 | 0.040 | 82,261 |
| 65–74 | 0.065 | 0.848 | 0.002 | 0.030 | 0.001 | 0.055 | 54,212 |
| 75–84 | 0.121 | 0.731 | 0.003 | 0.054 | 0.001 | 0.089 | 27,673 |
| 85+ | 0.235 | 0.494 | 0.001 | 0.103 | 0.003 | 0.164 | 9,665 |

The children's rows remain the sharpest diagnostic (as recorded on issue
#50): 46–50% bike and ~0% ride against literature ~61% of school trips by
private vehicle — displaced escort demand, the population the §9.68
round-trip escort repair covers first. No *observed* mode × age cell exists
to formalise this; that acquisition is issue #63's.

### All trips, mode share by sex / licence / employment

| group | bike | car | motorbike | pt | ride | walk | n |
|---|---:|---:|---:|---:|---:|---:|---:|
| F | 0.111 | 0.758 | 0.002 | 0.046 | 0.001 | 0.082 | 282,303 |
| M | 0.115 | 0.749 | 0.002 | 0.048 | 0.001 | 0.085 | 272,619 |
| licence = 0 | 0.488 | 0.000 | 0.000 | 0.182 | 0.005 | 0.325 | 104,365 |
| licence = 1 | 0.026 | 0.928 | 0.003 | 0.016 | 0.000 | 0.027 | 450,557 |
| employed_full_time | 0.066 | 0.851 | 0.002 | 0.032 | 0.000 | 0.048 | 227,368 |
| employed_part_time | 0.095 | 0.790 | 0.003 | 0.043 | 0.001 | 0.068 | 137,465 |
| unemployed | 0.133 | 0.703 | 0.003 | 0.061 | 0.001 | 0.098 | 6,157 |
| not_in_labour_force | 0.184 | 0.607 | 0.002 | 0.068 | 0.002 | 0.138 | 183,932 |

### Commute trips (ending at `work`), mode share by age band and employment

| group | bike | car | motorbike | pt | ride | walk | n |
|---|---:|---:|---:|---:|---:|---:|---:|
| 12–17 | 0.479 | 0.000 | 0.000 | 0.270 | 0.013 | 0.238 | 534 |
| 18–24 | 0.187 | 0.575 | 0.002 | 0.130 | 0.004 | 0.103 | 6,177 |
| 25–34 | 0.077 | 0.824 | 0.003 | 0.057 | 0.001 | 0.039 | 13,697 |
| 35–44 | 0.053 | 0.872 | 0.004 | 0.041 | 0.001 | 0.029 | 13,009 |
| 45–54 | 0.047 | 0.890 | 0.003 | 0.033 | 0.001 | 0.025 | 12,453 |
| 55–64 | 0.054 | 0.873 | 0.004 | 0.038 | 0.001 | 0.030 | 9,476 |
| 65–74 | 0.075 | 0.822 | 0.003 | 0.056 | 0.000 | 0.043 | 2,038 |
| 75–84 | 0.147 | 0.661 | 0.009 | 0.110 | 0.009 | 0.064 | 109 |
| employed_full_time | 0.073 | 0.830 | 0.003 | 0.053 | 0.002 | 0.040 | 37,285 |
| employed_part_time | 0.083 | 0.809 | 0.003 | 0.060 | 0.002 | 0.044 | 20,208 |

(Only employed agents generate work-ending trips — a construction sanity
check that holds. The 0–4 and 5–11 bands are absent, as they must be.)

## 4. Where this leaves issue #50

- **Observed side**: mode × sex (commute) is now measured and joined; it is
  the *only* observed demographic conditioning of mode in the held data.
  Mode × age remains a named acquisition (issue #63), not a modelling gap.
- **Model side**: nothing sex-conditions mode choice, and the comparison
  shows exactly that. Whether the observed sex structure (bus, motorbike,
  car-passenger skews) *should* be reproduced — and by what mechanism that
  is not a target-fit — is a design decision for after the §9.68/§9.69
  repair family produces a valid arm; any new observable enters as a
  constraint, never a target.
- **Next measurement**: rerun the same script unchanged over the first
  valid post-repair arm; the bike/ride commute deltas in §2 are the
  numbers the repair is expected to move.
