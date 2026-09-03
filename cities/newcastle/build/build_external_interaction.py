#!/usr/bin/env python
"""The external tier's interaction with the core, from the held observations.

Two measured members of ``B.external.interaction_rate``'s identity
(DECISIONS.md 9.140, issue #63 item 7):

* ``B.external.commute_share_to_core`` - the share of the external tier's
  EMPLOYED residents whose place of work lies in the core LGAs, from the
  TfNSW Journey to Work 2011 Table 01 (origin SA2 x destination SA2), the
  newest origin-destination release the publisher still serves (2016 was
  withdrawn; 2021 is an attended ABS TableBuilder extract). The 2021
  external-tier SA2s are read under their 2011 names: the ASGS 2011 called a
  surrounding region "X Region" where 2021 says "X Surrounds".
* ``B.external.employed_share`` - employed persons over all persons in the
  external tier from the held 2021 Census G46 and G01 tables.

Writes ``data/processed/observed/external_interaction.json`` with both, per
SA2, and REFUSES to run if either declared registry value drifts from the
recomputation (the 9.116 guard: a declared value and its artefact must not
be able to part in silence).
"""
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'src'))
import city as _city  # noqa: E402
import registry as _registry  # noqa: E402
import pandas as pd  # noqa: E402

CFG = _registry.load()
RAW = _city.path('data/raw/jtw/bts_jtw_table01_2011_v1_0.zip')
OUT = _city.path('data/processed/observed/external_interaction.json')

# ASGS 2011 -> 2021 naming of the same surrounding-region SA2s.
NAME_2011 = {'Surrounds': 'Region'}


def name_2011(name_2021):
    for new, old in NAME_2011.items():
        if name_2021.endswith(' ' + new):
            return name_2021[:-len(new)] + old
    return name_2021


def main():
    zones = pd.read_csv(_city.path('data/processed/zones/zones_SA1.csv'), dtype=str)
    lga = pd.read_csv(_city.path('data/processed/zones/sa1_to_lga.csv'), dtype=str)
    core_lgas = sorted(lga[lga.zone_tier == 'core'].lga_name.unique())
    ext_sa1 = set(zones[zones.zone_tier == 'external'].SA1_CODE21)
    ext_sa2_2021 = sorted(zones[zones.zone_tier == 'external'].SA2_NAME21.unique())
    ext_sa2_2011 = {name_2011(n): n for n in ext_sa2_2021}

    z = zipfile.ZipFile(RAW)
    member = [n for n in z.namelist() if n.lower().endswith('.csv')][0]
    jtw = pd.read_csv(io.BytesIO(z.read(member)))
    missing = [n for n in ext_sa2_2011 if n not in set(jtw.O_SA2_NAME11)]
    if missing:
        raise SystemExit('external-tier SA2s absent from the 2011 table: %s' % missing)
    o = jtw[jtw.O_SA2_NAME11.isin(ext_sa2_2011)]
    employed_2011 = float(o.EMPLOYED_PERSONS.sum())
    to_core = float(o[o.D_LGA_NAME11.isin(core_lgas)].EMPLOYED_PERSONS.sum())
    commute_share = to_core / employed_2011
    by_sa2 = {}
    for n11, g in o.groupby('O_SA2_NAME11'):
        e = float(g.EMPLOYED_PERSONS.sum())
        c = float(g[g.D_LGA_NAME11.isin(core_lgas)].EMPLOYED_PERSONS.sum())
        by_sa2[ext_sa2_2011[n11]] = dict(sa2_2011=n11, employed_2011=e,
                                         to_core=c, share=round(c / e, 4) if e else None)

    g01 = pd.read_csv(_city.path('data/processed/census/census2021_G01_SA1.csv'), dtype=str)
    g46 = pd.read_csv(_city.path('data/processed/census/census2021_G46B_SA1.csv'), dtype=str)
    persons = pd.to_numeric(g01[g01.SA1_CODE_2021.isin(ext_sa1)]['Tot_P_P']).sum()
    employed = pd.to_numeric(g46[g46.SA1_CODE_2021.isin(ext_sa1)]['P_Tot_Emp_Tot']).sum()
    employed_share = float(employed) / float(persons)

    declared_c = CFG.get('B.external.commute_share_to_core')
    declared_e = CFG.get('B.external.employed_share')
    if abs(declared_c - commute_share) > 5e-4 or abs(declared_e - employed_share) > 5e-4:
        raise SystemExit(
            'declared B.external.commute_share_to_core %.4f / employed_share %.4f '
            'do not match the held observations %.4f / %.4f - change the registry '
            'with the artefact, never one without the other (9.116)'
            % (declared_c, declared_e, commute_share, employed_share))
    doc = dict(
        source=dict(commute='TfNSW Journey to Work 2011 Table 01 (origin SA2 x '
                            'destination SA2, employed persons), data/raw/jtw/',
                    employed='2021 Census G46 P_Tot_Emp_Tot over G01 Tot_P_P, '
                             'external-tier SA1s'),
        core_lgas=core_lgas,
        external_sa2_2021=ext_sa2_2021,
        commute_share_to_core=round(commute_share, 4),
        employed_residents_2011=employed_2011, working_in_core_2011=to_core,
        employed_share=round(employed_share, 4),
        persons_2021=int(persons), employed_2021=int(employed),
        interaction_rate_identity=dict(
            expression='commute_share_to_core x employed_share / purpose_split.HW',
            value=round(commute_share * employed_share
                        / CFG.get('B.external.purpose_split')['HW'], 4),
            declared=CFG.get('B.external.interaction_rate')),
        by_sa2=by_sa2,
        decisions_ref='9.140')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(doc, fh, indent=2)
    print('external tier: %d employed residents (2011), %d working in %s -> '
          'commute share %.4f; employed share %.4f (2021); interaction rate '
          'identity %.4f (declared %s)'
          % (employed_2011, to_core, '/'.join(core_lgas), commute_share,
             employed_share, doc['interaction_rate_identity']['value'],
             doc['interaction_rate_identity']['declared']))
    print('wrote %s' % os.path.relpath(OUT, _city.path('')))


if __name__ == '__main__':
    main()
