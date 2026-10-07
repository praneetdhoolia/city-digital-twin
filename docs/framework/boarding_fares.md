# Per-boarding fare contract

`BoardingFareHandler` is an optional alternative to the linked-journey fare
handler. A city enables it with `boardingFare.tableFile`. The baseline launcher
binds this path from the optional `boarding_fares` entry in its declared inputs.
Each completed boarding emits one negative `PersonMoneyEvent` for native
money scoring, including the person's income sensitivity when enabled.

The UTF-8 CSV contains these columns:

| Column | Meaning |
|---|---|
| `match_kind` | `line` or `mode`; an exact line match takes precedence |
| `match_id` | Native transit-line ID or scheduled transport mode |
| `profile_id` | Audit identifier using letters, digits, dots, underscores or hyphens |
| `upper_bounds_m` | Pipe-separated increasing inclusive distance bounds, in metres |
| `fares_money` | One non-negative monetary amount per distance bound |
| `linear_rate_money_per_m` | Rate for a linear-only profile, or for distance beyond the last bound |
| `currency_code` | Three-letter currency code; amounts and native money utility must use the same currency |

Additional provenance columns are permitted. Every scheduled line must resolve
to a rule. Empty bounds and fares define a linear-only profile. Extrapolated
boardings are counted separately so a modelled tail is not mistaken for a
published tariff. The city adapter owns tariff acquisition, class assignment,
eligibility assumptions and extrapolation. The framework supplies no prices.

Distance is the sum of network links entered between boarding and alighting.
Each passenger retains their own boarding distance on a shared vehicle.
This is a modelled distance basis, not automatically an operator's fare-stage
definition. Transfers generate separate tickets. Drivers are excluded and
unfinished boardings are counted without inventing an alighting distance.

The handler refuses simultaneous linked-journey fare charging and non-zero
native monetary distance rates for transit modes. Money events are deferred
until after mobsim, before scoring finishes. The native output
`boarding_fares.csv` records completed and unfinished boardings, distance in
metres, charged money with currency, and extensions beyond the published bands.
The behavioural analyser retains these readings in its permanent report.

`boardingFare.routeChoice=true` also prices every candidate transit ride before
RAPTOR prunes paths. `BoardingFareTable` supplies the same tariff to routing and
executed scoring; the person's scoring provider supplies money utility. The
router retains the existing submode-constant term when that separate gate is
enabled. The optional fare-routing gate defaults to false for existing cities.

The pinned engine's public cost callback omits line and stop identities. A
read-only adapter obtains its boarding/alighting indices and accumulated network
distance from the pinned iterator. It does not mutate or advance the iterator,
and refuses unsupported iterator types or invalid distances. The native probe
must pass on a toolchain upgrade. This is an explicit private-API dependency;
neither the engine jar nor its version has changed.

Caps, transfer discounts, concessions and passes must not be inferred from this
contract. City tariffs and eligibility still need evidence. The analyser reads
the run's own configuration to distinguish scoring-only from fare-aware routing.

Verify the native event contract with `python tests/check_boarding_fares.py`.
The probe tests concurrent riders, inclusive boundaries, extrapolation,
operator precedence, separate transfers, driver exclusion, unfinished rides
and rejection of duplicate distance charges. A real RAPTOR competition checks
that a slower cheaper service survives pruning, lower money sensitivity reverses
the choice, and the inclusive network-distance band is charged once per ride.
