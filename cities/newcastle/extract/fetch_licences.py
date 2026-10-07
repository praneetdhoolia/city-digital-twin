#!/usr/bin/env python
"""Download the driver-licence holders snapshot and the population-by-age
denominator it needs, with provenance (DECISIONS.md 9.131).

Two official series, both CC-BY:

* TfNSW Driver Licence Statistics - the monthly snapshot of licence holders
  by licence type, class, gender, age group and customer-address LGA. Counts
  of five or fewer are published as "<=5".
* ABS Regional population by age and sex, 2024 - estimated resident
  population by five-year age group and LGA at 30 June 2024, the denominator
  a holding RATE needs. The synthetic population's own age structure is not
  used as a denominator because a rate must be observed over observed.

Both land under data/raw/ and are never edited in place; the rates are built
from them by cities/<city>/build/build_licence_rates.py.
"""
import city as _city
from fetch_with_provenance import fetch_all

B = "https://opendata.transport.nsw.gov.au/data/dataset/"
M = [
    ("tfnsw/driver_licences_snapshot_2026.zip",
     B + "63c6e401-4cca-4a2c-adcc-365d205d0a3e/resource/10987cf1-79a4-4ee9-b17e-10fe1b24819f/download/tfnsw_driver_licences_snapshot_2026.zip",
     "TfNSW Driver Licence Statistics - Driver Licences Snapshot 2026 (monthly; licence type, class, primary flag, gender, age group, customer address LGA, count)",
     "CC-BY 4.0"),
    ("abs/32350DS0003_2024.xlsx",
     "https://www.abs.gov.au/statistics/people/population/regional-population-age-and-sex/2024/32350DS0003_2024.xlsx",
     "ABS Regional population by age and sex, 2024 - estimated resident population by age and sex, Local Government Areas, 30 June 2024 (released 28 Aug 2025)",
     "CC-BY 4.0"),
]


def main():
    # a failed fetch here is fatal: both files are needed and nothing else
    # is on this list to land without them
    fetch_all(M, _city.path('data/raw'), 'provenance_licences.json', min_bytes=500,
              timeout=600, undated='today', continue_on_error=False)


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
