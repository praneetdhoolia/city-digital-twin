# Request to TfNSW Open Data: four bespoke Household Travel Survey tables (#50)

*Drafted 12 September 2026 (forty-fourth session). **SENT 8 October 2026** by the operator to opendataprogram@transport.nsw.gov.au (D31, #50), as the text in "As sent" below: the draft's four tables plus five lower-priority tables the sixteenth report's results point to. The hub's
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

## As sent, 8 October 2026

The text the operator sent, with each link written out after the thing it names. The draft above is kept as it was.

```text
To: opendataprogram@transport.nsw.gov.au
Subject: Request for aggregate Household Travel Survey tables for the Newcastle region

Dear Open Data team,

I am building an open, reproducible agent-based transport model of the Newcastle region. It covers the Newcastle, Lake Macquarie, Maitland, Cessnock and Port Stephens local government areas (https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files/LGA_2021_AUST_GDA2020_SHP.zip). The code and data package are public (https://github.com/praneetdhoolia/city-digital-twin) under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) and, for the OpenStreetMap-derived layers, the ODbL (https://opendatacommons.org/licenses/odbl/1-0/).

The model is checked against TfNSW's published data on the Open Data Hub (https://opendata.transport.nsw.gov.au):

- the Household Travel Survey (https://opendata.transport.nsw.gov.au/data/dataset/c0f9a300-38e5-4086-90fb-c7a1f0b0fe31) mode shares in the data by LGA, 2020/21 to 2024/25 workbook (https://opendata.transport.nsw.gov.au/data/dataset/c0f9a300-38e5-4086-90fb-c7a1f0b0fe31/resource/8b0a7e54-9dea-43c3-9804-5e2917bf4f1f/download/data-by-lga-2020_21-to-2024_25.xlsx), read with its data document (https://opendata.transport.nsw.gov.au/data/dataset/c0f9a300-38e5-4086-90fb-c7a1f0b0fe31/resource/5a0ac96e-4562-4ffe-bb96-beb0cb0dca89/download/hts-data-document-2020_2024.pdf);
- the Opal Patronage daily series (https://opendata.transport.nsw.gov.au/data/dataset/opal-patronage);
- the train station entries and exits (https://opendata.transport.nsw.gov.au/data/dataset/3977df59-a1fa-422e-91ff-cfaeac355cc9) and the light rail patronage (https://opendata.transport.nsw.gov.au/data/dataset/6641ea76-4818-4e38-864f-4e3cb6bb98ee) series.

The published workbooks do not carry the tables below. I understand unit records are not released, so I am asking only for aggregate tables, with your usual suppression of small cells. Each table would cover residents of the five LGAs above, or the Hunter SA4 (https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026) if that is the geography you hold. Each would be pooled over the 2020/21 to 2024/25 waves, or the latest pooled period you publish, for an average weekday.

MOST NEEDED

1. Trips by mode and age band. Modes as published (vehicle driver, vehicle passenger, train, bus, light rail, ferry, walk only, bicycle, taxi or rideshare, other). Age bands as published, for example 5-14, 15-24, 25-44, 45-64 and 65+. Counts or shares, with reliability flags.

2. Trip length distribution by mode. Trips by mode in distance bands (0-1, 1-2, 2-5, 5-10, 10-20 and 20+ km, or your standard bands), rather than the mean distance the workbooks give.

3. Vehicle occupancy by trip purpose. Mean occupants per vehicle-driver trip, or the ratio of passenger trips to driver trips. Purposes: commute, education, shopping, social and recreation, serve passenger, other.

4. The "Other" mode unfolded. Bicycle, taxi or rideshare, and other reported separately, by LGA where the cells allow.

ALSO USEFUL, IF THEY CAN BE PRODUCED FROM THE SAME SURVEY

5. Trips by mode and household vehicle availability. Households with no vehicle against households with one or more.

6. Access mode to train stations. Walk, drive and park, dropped off, bus or other, for trips that board a train.

7. Vehicle passenger trips by who drives. A member of the same household against someone outside it.

8. Departure time by trip purpose. Trips by hour of departure for each purpose.

9. Persons who made no trip on the travel day. The share of persons, by age band if possible.

Any of these, at whatever geography and pooling keeps the cells releasable, would materially improve the model. I will attribute Transport for NSW as the source under the CC BY licence the Hub uses. The tables would be published with the model's data package and its provenance record.

If this belongs with the Transport Performance and Analytics request form (https://www.transport.nsw.gov.au/about-us/access-to-information/request-information-from-transport-performance-and-analytics) instead, I am happy to resubmit it there.

Thank you for considering this request.

Kind regards,
[your name, affiliation, contact details]
```
