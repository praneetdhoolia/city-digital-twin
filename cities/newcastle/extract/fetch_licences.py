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
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', '..', '..', 'src'))
import city as _city  # noqa: E402
import os, json, hashlib, urllib.request, datetime  # noqa: E402

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
root = _city.path('data/raw')
prov = []
for rel, url, desc, lic in M:
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p) and os.path.getsize(p) > 500:
        print("SKIP %s" % rel)
    else:
        print("GET  %s" % rel, flush=True)
        req = urllib.request.Request(url, headers={'User-Agent': 'city-digital-twin/0.1 (research)'})
        with urllib.request.urlopen(req, timeout=600) as r, open(p, 'wb') as f:
            while True:
                c = r.read(1 << 20)
                if not c:
                    break
                f.write(c)
    sz = os.path.getsize(p)
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    print("  %13s B" % format(sz, ','))
    prov.append({"path": rel, "url": url, "description": desc, "licence": lic, "bytes": sz,
                 "sha256": h, "retrieved": datetime.date.today().isoformat()})
json.dump(prov, open(os.path.join(root, 'provenance_licences.json'), 'w'), indent=2)
print("\nwrote data/raw/provenance_licences.json  (%d files)" % len(prov))
