# National Freight Flow Survey assessment

Source: MLIT, 11th National Freight Flow Survey (2021).

## What it provides

The three-day survey records each shipment's item, consignee industry, destination, weight, transport route, shipment time, duration and cost. Thus it is genuine empirical shipment-weight evidence with official provenance.

## Why it cannot authorize R24 parcel mass

The sampling frame is establishments in mining, manufacturing, wholesale and warehousing. MLIT explicitly states that retail businesses and individual shippers are outside scope, and that the survey fundamentally does not capture the small-lot corporation-to-individual or individual-to-individual flows needed here. Published results are aggregate tables. Restricted secondary-use records may be requestable through official statistical microdata procedures, but access does not cure the underlying design mismatch.

The reviewed public variables do not jointly identify:

- a household destination rather than an individual/business consignee category;
- courier/parcel-service identity at the physical final-delivery parcel level;
- B2C e-commerce origin;
- one delivered parcel as the observation denominator.

Accordingly:

- household destination identifiable: `NO`
- courier / parcel category isolatable: `NO` for the required final-parcel population
- B2C EC subset extractable: `NO`
- shipment-level weight field: `YES`
- public record-level observations: `NO`
- classification: **`INCOMPATIBLE_POPULATION`**
- R24 primary authority use: **`REJECT`**

Sources:

- https://www.mlit.go.jp/statistics/details/t-other-2_tk_000197.html
- https://www.mlit.go.jp/report/press/tokatsu01_hh_000697.html
- https://www.e-stat.go.jp/stat-search/files?toukei=00600620
- https://www.e-stat.go.jp/microdata/data-use
