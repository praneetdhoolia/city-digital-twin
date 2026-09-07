"""The ONE map from an HTS travel purpose to this model's purpose vocabulary.

It existed twice - once in the demand builder and once in the run-input
assembler - and the two disagreed on `Serve passenger`: the demand generated
it as HX, its own tour purpose since DECISIONS.md 9.15, while the assembler
folded it into NHB and priced it as a non-home-based leg. HX carries 351,645
weekday legs, so the disagreement reached the scoring parameters of every
escort trip in the model (#147, DECISIONS.md 9.151).

The demand's reading wins: an escort is a tour purpose, and a purpose the
demand generates under one name may not be priced under another. Both callers
import this map; there is nowhere left for a second copy to drift.
"""

# `Serve passenger` -> HX. `solve_secondary_rates` once folded NHB's weight
# into HO because a non-home-based leg is not a tour purpose, which preserved
# the trip rate and lost the trip type: an escort became a two-hour
# discretionary stay made by anyone, rather than a drop-off made by a driver.
HTS_PURPOSE = {
    'Commute': 'HW',
    'Education/childcare': 'HE',
    'Shopping': 'HS',
    'Personal business': 'HO',
    'Social/recreation': 'HO',
    'Serve passenger': 'HX',
    'Work related business': 'WB',
    'Other': 'HO',
}
