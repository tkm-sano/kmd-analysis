# Data Provenance

| Provider / dataset | Original material | Access context | Analytical use | Limitations |
|---|---|---|---|---|
| e-Stat, 2020 Population Census | Tokyo population tables and mesh archive | frozen processed snapshot retained; raw material must be reacquired from the recorded provider | population-weighted synthetic customer proxy | not observed delivery demand |
| Open Charge Map | Tokyo-area charging-location records | frozen processed snapshot retained; accessed 2026-07 | charging-station candidate geography | availability, access, connector fit, congestion, and hours are not guaranteed |
| MLIT National Land Numerical Information | Tokyo boundary and logistics/highway datasets | processed analytical tables retained; raw archives are not redistributed | boundary clipping, depot/logistics and network proxies | facilities and links are not validated operator routes |
| Geofabrik/OpenStreetMap | Kanto shapefile archive | raw archive is not redistributed; reacquisition and attribution are required | planned road-network distance enhancement | license attribution and network preprocessing required |
| MLIT Freight Flow Census | prefecture freight CSVs | processed summaries retained; raw tables must be reacquired | logistics context and potential demand calibration | aggregate statistics are not customer-level routes |
| Vehicle manufacturers | Hino, Mitsubishi Fuso, Isuzu, Toyota source pages/PDF | derived specification table retained; source snapshots are not redistributed | EV payload/range/charging scenario parameters | specifications vary by configuration and operating conditions |
| EVRP/CVRP benchmark repositories | Augerat, Schneider/Mendeley and E-CVRP instances | source identifiers retained; benchmark files must be reacquired under upstream terms | problem-scale and constraint comparison | benchmark instances are not Tokyo operations |
| World Bank LPI API | Japan logistics performance indicators | retained JSON, accessed 2026-07-04 | contextual evidence | national-level, not scenario input |
| IEA EV Data Explorer | downloaded workbooks | raw workbooks are not redistributed; accessed 2026-06-30/2026 | contextual EV evidence | not used as direct routing demand |

Processing lineage is represented by the scripts under `05_src/`, the reproducibility registries, and dataset-specific metadata files. Final literature URLs are recorded in `02_literature/references/reference_inventory.csv`. The public repository intentionally excludes raw downloads, third-party PDFs, extracted full text, and ZIP archives. This is a computational reproduction package from frozen processed inputs, not a full raw-data-acquisition archive.
