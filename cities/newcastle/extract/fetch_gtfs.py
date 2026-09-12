#!/usr/bin/env python
"""Download era-variant GTFS bundles from the TfNSW historical GTFS S3 archive."""

import city as _city
import os, urllib.request, hashlib, json, datetime
BASE="https://opendata-gtfs.transport.nsw.gov.au/"
OUT=_city.path("schedules/raw")
# era_key -> list of (feed_label, s3_key)
ERAS={
 "era2_2016_rail_truncated":[
   ("sydneytrains","historical_gtfs/sydneytrains/2016/2016-09/sydneytrains_schedule_data_20160920000000.zip"),
   ("nswtrains","historical_gtfs/nswtrains/2016/2016-09/nswtrains_schedule_data_20160923000000.zip"),
   ("complete","historical_gtfs/complete_gtfs/2016/2016-08/full_greater_sydney_gtfs_static_20160829.zip"),
 ],
 "era3_2018_keolis_interchange":[
   ("nisc001","historical_gtfs/NISC001/2018/2018-10/NISC001_scheduled_data_20181019.zip"),
   ("sydneytrains","historical_gtfs/sydneytrains/2018/2018-10/SydneyTrains_scheduled_data_20181030.zip"),
   ("nswtrains","historical_gtfs/nswtrains/2018/2018-10/nswtrains_scheduled_data_20181007011000.zip"),
 ],
 "era4_2019_lr_open":[
   ("nisc001","historical_gtfs/NISC001/2019/2019-03/NISC001_scheduled_data_20190325210300.zip"),
   ("sydneytrains","historical_gtfs/sydneytrains/2019/2019-03/sydneytrains_scheduled_data_20190331010300.zip"),
   ("nswtrains","historical_gtfs/nswtrains/2019/2019-03/nswtrains_scheduled_data_20190330010300.zip"),
   ("lightrail","historical_gtfs/lightrail-newcastle/2020/2020-02/lightrail-newcastle_scheduled_data_20200218010200.zip"),
 ],
 "base2026":[
   ("nisc001","historical_gtfs/NISC001/2026/2026-08/NISC001_scheduled_data_20260805190800.zip"),
   ("lightrail","historical_gtfs/lightrail-newcastle/2026/2026-08/lightrail-newcastle_scheduled_data_20260804010800.zip"),
   ("regionbuses","historical_gtfs/regionbuses-newcastlehunter/2026/2026-08/regionbuses-newcastlehunter_scheduled_data_20260801200800.zip"),
   ("sydneytrains","historical_gtfs/sydneytrains/2026/2026-08/sydneytrains_scheduled_data_20260808010800.zip"),
   ("nswtrains","historical_gtfs/nswtrains/2026/2026-08/nswtrains_scheduled_data_20260801010800.zip"),
 ],
}
# 9.151 (#149): the retrieval date. These records carried none, so 15 raw
# feeds and everything built from them showed a blank `retrieved` in the
# manifest. It is stamped for a feed this run ACTUALLY downloads; a feed that
# is skipped because it is already on disk keeps the date the earlier run
# recorded, because today is not when it was retrieved. A file whose date
# nobody recorded stays blank rather than acquiring one now.
_PREV={}
_prev_path=os.path.join(OUT,"provenance.json")
if os.path.exists(_prev_path):
    try:
        for _r in json.load(open(_prev_path,encoding='utf-8')):
            if _r.get("retrieved"):
                _PREV[(_r.get("era"),_r.get("feed"))]=_r["retrieved"]
    except Exception:
        pass
TODAY=datetime.date.today().isoformat()

prov=[]
for era,items in ERAS.items():
    d=os.path.join(OUT,era); os.makedirs(d,exist_ok=True)
    for label,key in items:
        p=os.path.join(d,f"{label}.zip")
        fetched=False
        if os.path.exists(p) and os.path.getsize(p)>1000:
            print(f"SKIP {era}/{label}"); 
        else:
            fetched=True
            url=BASE+key
            print(f"GET  {era}/{label} <- {key}",flush=True)
            try:
                urllib.request.urlretrieve(url,p)
            except Exception as e:
                print(f"  FAIL {e}"); continue
        # the FULL digest, like every other raw record and every manifest
        # row: a 16-character truncation was the only integrity claim these
        # feeds carried (eighth project report, 11 September 2026). The
        # truncation is kept beside it for readers of the old records.
        full=hashlib.sha256(open(p,'rb').read()).hexdigest()
        h=full[:16]
        sz=os.path.getsize(p)
        print(f"  {sz:>12,} B sha256:{h}")
        rec={"era":era,"feed":label,"s3_key":key,"url":BASE+key,"bytes":sz,
             "sha256":full,"sha256_16":h,
             "source":"TfNSW Open Data Hub historical GTFS archive",
             "licence":"CC-BY 4.0"}
        retrieved=TODAY if fetched else _PREV.get((era,label))
        if retrieved:
            rec["retrieved"]=retrieved
        prov.append(rec)
json.dump(prov,open(os.path.join(OUT,"provenance.json"),"w",encoding="utf-8",newline="\n"),indent=2)
print("\nwrote",os.path.join(OUT,"provenance.json"))
