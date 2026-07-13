# Data Provenance

| Provider / dataset | Original material | Access context | Analytical use | Limitations |
|---|---|---|---|---|
| e-Stat, 2020 Population Census | Tokyo population tables and mesh archive | retained under raw population inputs; accessed 2026-07 | population-weighted synthetic customer proxy | not observed delivery demand |
| Open Charge Map | Tokyo-area charging-location records | retained processed snapshot; accessed 2026-07 | charging-station candidate geography | availability, access, connector fit, congestion, and hours are not guaranteed |
| MLIT National Land Numerical Information | Tokyo boundary and logistics/highway datasets | retained raw ZIP archives; accessed 2026-07 | boundary clipping, depot/logistics and network proxies | facilities and links are not validated operator routes |
| Geofabrik/OpenStreetMap | Kanto shapefile archive | retained raw ZIP archive dated 2026-07-03 | planned road-network distance enhancement | license attribution and network preprocessing required |
| MLIT Freight Flow Census | prefecture freight CSVs | retained raw CSVs | logistics context and potential demand calibration | aggregate statistics are not customer-level routes |
| Vehicle manufacturers | Hino, Mitsubishi Fuso, Isuzu, Toyota source pages/PDF | retained source snapshots, accessed 2026-07 | EV payload/range/charging scenario parameters | specifications vary by configuration and operating conditions |
| EVRP/CVRP benchmark repositories | Augerat, Schneider/Mendeley and E-CVRP instances | retained raw benchmark files | problem-scale and constraint comparison | benchmark instances are not Tokyo operations |
| World Bank LPI API | Japan logistics performance indicators | retained JSON, accessed 2026-07-04 | contextual evidence | national-level, not scenario input |
| IEA EV Data Explorer | downloaded workbooks | retained raw workbooks, accessed 2026-06-30/2026 | contextual EV evidence | not used as direct routing demand |

Processing lineage is represented by the scripts under `05_src/`, the reproducibility registries, and dataset-specific metadata files. Final literature URLs are recorded in `02_literature/references/reference_inventory.csv`.
