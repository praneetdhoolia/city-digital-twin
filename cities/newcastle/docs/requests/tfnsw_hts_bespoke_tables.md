# Request to TfNSW Open Data: four bespoke Household Travel Survey tables (#50)

*Drafted 12 September 2026 (forty-fourth session). Not yet sent. The hub's
CKAN API was searched first (12 September 2026): the published HTS
workbooks by Region, LGA and SA3 (2020/21–2024/25 and the revised
2009/10–2019/20 release) carry mode × region, purpose × region and the
LGA/SA3 splits only — none of the four cells below on any geography — and
TfNSW's stated policy is that unit records are not released but aggregate
tables are supplied on request. HELD by the user's decision of 14 September
2026 (D2) pending an exhaustive search, made that day (forty-ninth session):
the hub's CKAN catalogue lists eleven HTS resources - the Region, LGA and SA3
workbooks for 2020/21-2024/25 and 2009/10-2019/20 and their data documents -
and their sheets carry mode x area (trips, distance, mean distance, mean
time), purpose x area and, pre-2020, a demographics sheet (population,
households, vehicles): none of the four cells. No dataset of format API on
the hub is an HTS product, so `api.transport.nsw.gov.au` has nothing to ask.
data.gov.au and Data.NSW mirror the same package. The three dashboards (by
Region, LGA, SA3) and the LGA Profiler's four views (total travel, mode
trips, mode distance, population and vehicles) are the workbooks drawn. The
only published cells of the four kinds are in the Bureau of Transport
Statistics' *Household Travel Survey Report: Sydney 2012/13* (November
2014): Table 4.7.2 mode share by age (eight bands, six modes), Table 4.4.6
trips by six distance bands x nine modes with bicycle, taxi and ferry
separate, Table 4.8.3 vehicle occupancy for work and non-work trips and
Table 4.8.4 the occupancy distribution - all for the Sydney GCCSA, not the
Hunter, at the 2012/13 vintage: shapes, not Newcastle targets. Commute-only
mode x age and distance-to-work band x mode for the five LGAs are derivable
from ABS Census 2021 TableBuilder (MTWP x AGE5P, DTWP x MTWP), behind the
operator's free ABS login. TfNSW's formal channel is the Transport
Performance and Analytics request form
(https://www.transport.nsw.gov.au/about-us/access-to-information/request-information-from-transport-performance-and-analytics),
which refuses scripted clients; the hub's contact remains the address below.*

**To:** opendataprogram@transport.nsw.gov.au
**Subject:** Bespoke HTS aggregate tables for the Newcastle region (five LGAs), for an open agent-based transport model

Dear Open Data team,

I am building an open, reproducible agent-based transport model of the
Newcastle region (the Newcastle, Lake Macquarie, Maitland, Cessnock and
Port Stephens LGAs; repository https://github.com/praneetdhoolia/city-digital-twin,
CC-BY / ODbL). The model is held to the published HTS mode shares by LGA and
to the Opal patronage series, and it needs four aggregate tables that the
published HTS workbooks do not carry. I understand unit records are not
released; I am asking for aggregate tables with the usual suppression of
small cells, pooled over the 2020/21–2024/25 waves (or the latest pooled
period you publish), for residents of the five LGAs above (or the Hunter
SA4 if that is the geography you hold), average weekday:

1. **Trips by mode × age band** — modes as published (vehicle driver,
   vehicle passenger, train, bus, light rail, ferry, walk-only, bicycle,
   taxi/rideshare, other), age bands as published (e.g. 5–14, 15–24,
   25–44, 45–64, 65+). Counts or shares with RSE flags.
2. **Trip length distribution by mode** — trips by mode in distance bands
   (0–1, 1–2, 2–5, 5–10, 10–20, 20+ km, or your standard bands), rather than
   the mean distance the workbooks give.
3. **Vehicle occupancy by trip purpose** — mean occupants per vehicle-driver
   trip (or the passenger/driver trip ratio) by purpose (commute, education,
   shopping, social/recreation, serve passenger, other).
4. **The "Other" mode cell unfolded** — bicycle, taxi/rideshare and other
   separately, by LGA where the cells allow.

Any of the four, at whatever geography and pooling keeps the cells
releasable, would materially improve the model; I will attribute TfNSW as
the source under the CC-BY licence the hub uses, and the tables would be
published with the model's data package and provenance record.

Thank you for considering it.

Kind regards,
[name, affiliation, contact]

---

*Record: when sent, add the date and any reference number to issue #50; when
answered, land the tables under `data/raw/hts/` through
`cities/<city>/extract/fetch_open_data.py` with their provenance.*
