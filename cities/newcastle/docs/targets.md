# The twelve targets and their bases

The artefact is [`data/processed/validation/mode_targets_by_mode.csv`](../data/processed/validation/mode_targets_by_mode.csv)
(built by `build/build_mode_targets.py`); this page is its reading, after
[`positions/public-transport-and-yardsticks.md`](../../../docs/positions/public-transport-and-yardsticks.md).
Sweeps are the CSV's `sweep_low`–`sweep_high`; `—` is a target with no sweep.

| mode | target | basis | status | sweep | source |
|---|---:|---|---|---|---|
| car | 58.32% of resident trips | HTS Vehicle driver 59.0% × census G62 car-as-driver share of driver journeys | derived | 43.74–72.90% | `mode_targets_by_mode.csv`, §9.87 |
| ride | 20.60% | HTS Vehicle passenger, read directly | observed | — | `mode_targets_by_mode.csv` |
| walk | 13.40% | HTS Walk only, read directly | observed | — | `mode_targets_by_mode.csv` |
| taxi | 0.99% | `B.taxi.daily_trips_band` over study-area weekday trips, not the census | derived | 0.74–1.24% | `mode_targets_by_mode.csv`, §9.91 |
| bike | 2.21% | HTS Other 3.2% minus the point-to-point share | derived | 1.96–2.46% | `mode_targets_by_mode.csv` |
| motorbike | 0.3785% | HTS Vehicle driver × G62 motorbike/scooter share of driver journeys | derived | 0.28–0.47% | `mode_targets_by_mode.csv`, §9.112 |
| bus | 2.38% of resident trips | HTS PT 3.8% × Opal/station boardings share 62.681% over 2024-10..2025-03 | derived | 2.38–3.09% | `mode_targets_by_mode.csv`, §9.100 |
| heavy_rail | 6,529 boardings/weekday | disclosed station entries at the 24 mapped stations, 6,086/day × `CAL.pt.weekday_factor` 1.0727 | measured | 6,086–7,912 | `pt_boardings_targets.json`, §9.130 |
| light_rail | 2,954 boardings/weekday | the line's own disclosed Opal series, 2,754/day × `CAL.pt.weekday_factor` | measured | 2,754–3,580 | `pt_boardings_targets.json`, §9.130 |
| ferry | 790 boardings/weekday | the TPA daily Opal patronage series, Ferry, 300 weekdays: the mean of each day's midpoint between its published lower and upper bound (hourly cells rounded to 100); both wharves, both directions | measured | 234–1,347 | `mode_targets_by_mode.csv`, §9.211 (supersedes §9.89) |
| truck | 15.47% of weekday vehicles at classified stations | TfNSW classified counts; not a person-trip share | derived | 13.73–17.40% | `mode_targets_by_mode.csv`, §9.101 |
| freight_train | 405 crossing closures/weekday | 313 timetable-derived plus 92 freight derived from the Cobbora survey (44 Saint James Road + 48 Clyde Street); the train is not a mobsim vehicle | derived | — | `mode_targets_by_mode.csv`, §9.90, §9.167 |

- **Bus** is the only PT mode still on the composition basis, because its
  published series is one contract region with an 88% structural break at
  2025-04 (§9.100); the window is the contiguous break-free overlap chosen by
  `CAL.pt_split.break_ratio` 0.5, stations are scoped by
  `CAL.pt_split.station_scope` = `target_lga`, and light rail's one reported stop
  is scaled to the line by `CAL.pt_split.lr_observed_stop_share` 0.3696 (§9.100).
- **Heavy rail and light rail** are disclosed counts, used exactly: every
  traveller who boards, all subpopulations, × 1/fraction, heavy rail at the 24
  disclosed stations only (§9.130). The PT total is still read against the HTS
  3.8% level. **Ferry** is on the same basis since the roots rebuild (D8,
  §9.211): the disclosed daily tap-on series carries an interval per day, never
  a point, so the sweep is the bounds' own means; the census G62 lockdown-month
  cell (§9.89) is superseded.

The 143 holdout targets in
[`data/processed/validation/validation_targets.csv`](../data/processed/validation/validation_targets.csv)
are pre-registered and never read before the end (§12).
