#!/usr/bin/env python
"""Slice the national/state open datasets down to Greater Newcastle."""

import city as _city
import pandas as pd, os, json

LGAS=['Newcastle','Lake Macquarie','Maitland','Cessnock','Port Stephens']
# the light rail's stops, as the Opal tap-on station series names them
NST=['Newcastle Interchange','Honeysuckle','Civic','Crown Street','Queens Wharf','Newcastle Beach']
# the Hunter line's stations within the study area, as the station usage series names them
STN=['Newcastle Interchange','Wickham','Hamilton','Broadmeadow','Adamstown','Cardiff','Cockle Creek',
     'Teralba','Booragul','Fassifern','Warabrook','Sandgate','Waratah','Kotara','Thornton','Maitland',
     'East Maitland','Victoria Street','Metford','Tarro','Hexham','Morisset','Awaba','Dora Creek','Wyee']


def slice_opal(rep):
    """The Opal light rail, light rail by stop, bus by contract region and
    station entries series, each cut to the study area."""
    # --- Opal light rail: Newcastle line only ---
    d=pd.read_csv(_city.path('data/raw/opal/lightrail_trips_by_line_cardtype.csv'))
    n=d[d['Line'].str.contains('Newcastle',case=False,na=False)].copy()
    n['Trip']=pd.to_numeric(n['Trip'],errors='coerce')
    n.to_csv(_city.path('data/processed/observed/opal_lr_newcastle_by_month_cardtype.csv'),index=False, lineterminator='\n')
    rep['lr_lines_available']=sorted(d['Line'].dropna().unique().tolist())
    rep['lr_newcastle_months']=[str(n['Year_Month'].iloc[0]),str(n['Year_Month'].iloc[-1])] if len(n) else []
    rep['lr_newcastle_rows']=len(n)

    # --- Opal LR by tap-on station ---
    d=pd.read_csv(_city.path('data/raw/opal/lightrail_trips_by_tapon_station.csv'))
    m=d[d['Location'].str.contains('|'.join(NST),case=False,na=False)]
    m=m[~m['Location'].str.contains('Sydney|Dulwich|Arlington|Randwick|Kingsford',case=False,na=False)]
    m.to_csv(_city.path('data/processed/observed/opal_lr_newcastle_by_stop.csv'),index=False, lineterminator='\n')
    rep['lr_stop_rows']=len(m); rep['lr_stops_found']=sorted(m['Location'].unique().tolist())

    # --- Opal bus by contract region ---
    # The contract region is DECLARED in schedules/operators.json, the feed
    # metadata, and matched exactly - never typed here (#116): the filter once
    # looked for 'Newcastle|Hunter', which no Opal region contains, matched
    # nothing, and the committed slice (1,363 NISC 1 rows) had no producer.
    ops=json.load(open(_city.path('schedules/operators.json'),encoding='utf-8'))
    contracts=sorted({f.get('contract','') for f in ops.get('feeds',{}).values() if f.get('contract')})
    d=pd.read_csv(_city.path('data/raw/opal/bus_trips_by_contract_region.csv'))
    regs=sorted(d['Contract_region'].dropna().unique().tolist())
    nb=d[d['Contract_region'].isin(contracts)]
    nb.to_csv(_city.path('data/processed/observed/opal_bus_newcastle_hunter.csv'),index=False, lineterminator='\n')
    rep['bus_contracts_declared']=contracts
    rep['bus_regions_newcastle']=sorted(nb['Contract_region'].unique().tolist())
    rep['bus_all_regions']=regs

    # --- Station entries/exits (Hunter line + Newcastle area) ---
    d=pd.read_csv(_city.path('data/raw/opal/station_entries_exits_monthly.csv'))
    pat='|'.join(STN)
    s=d[d['Station'].str.contains(pat,case=False,na=False)]
    s.to_csv(_city.path('data/processed/observed/station_entries_exits_newcastle.csv'),index=False, lineterminator='\n')
    rep['station_rows']=len(s); rep['stations_found']=sorted(s['Station'].str.strip().unique().tolist())


def slice_counts(rep):
    """The road count stations of the study LGAs and their yearly AADT."""
    d=pd.read_csv(_city.path('data/raw/counts/rms_station_reference.csv'),low_memory=False)
    st=d[d['lga'].isin(LGAS)].copy()
    st.to_csv(_city.path('data/processed/observed/traffic_count_stations_newcastle.csv'),index=False, lineterminator='\n')
    rep['count_stations']=len(st)
    rep['count_stations_by_lga']=st['lga'].value_counts().to_dict()
    ids=set(st['station_key'].astype(str))
    # yearly AADT for those stations
    y=pd.read_csv(_city.path('data/raw/counts/rms_yearly_summary.csv'),low_memory=False)
    rep['yearly_cols']=list(y.columns)
    kcol='station_key' if 'station_key' in y.columns else y.columns[0]
    yn=y[y[kcol].astype(str).isin(ids)]
    yn.to_csv(_city.path('data/processed/observed/traffic_aadt.csv'),index=False, lineterminator='\n')
    rep['aadt_rows']=len(yn)
    if 'year' in yn.columns: rep['aadt_years']=[int(yn['year'].min()),int(yn['year'].max())]


def main():
    os.makedirs(_city.path('data/processed/observed'),exist_ok=True)
    rep={}
    slice_opal(rep)
    slice_counts(rep)
    with open(_city.path('data/processed/observed/_slice_report.json'),'w',encoding='utf-8',newline='\n') as fh:
        json.dump(rep,fh,indent=2,default=str)
    print(json.dumps(rep,indent=2,default=str)[:4000])


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
