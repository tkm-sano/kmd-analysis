# Tokyo traffic-simulation raw data

This directory contains local, third-party source material for the additive
Tokyo traffic-simulation layer. Downloaded files are ignored by Git; only this
documentation and the empty directory skeleton are tracked.

Use the following source-specific directories:

- `boundaries/`: administrative and study-area boundaries, including MLIT N03.
- `charging/`: charging-station API responses and source snapshots.
- `driver_behavior/`: licensed external driver-behavior datasets or extracts.
- `demand_proxy/`: official aggregate statistics used only to derive synthetic
  demand proxies; parcel counts here are not customer or stop records.
- `freight/`: freight-flow and aggregate freight-demand source tables.
- `freight_network/`: designated freight-road GIS data, including MLIT N12.
- `gtfs/`: public-transport GTFS and GTFS-RT snapshots.
- `jartic/`: time-stamped JARTIC WFS API responses.
- `logistics_hubs/`: logistics-facility GIS data, including MLIT P31.
- `osm/`: date-pinned OpenStreetMap PBF or XML extracts.
- `population/`: e-Stat population and household mesh source files.
- `road_census/`: MLIT road-census segment and time-band tables.
- `tokyo_police/`: Tokyo Metropolitan Police traffic-count archives.
- `vehicles/`: official vehicle specification source snapshots.

For every acquired file, add one record to
`03_data/metadata/traffic_simulation_sources.csv` before processing it. Preserve
the original download, record its SHA-256 digest, and write derived data only
under `03_data/processed/traffic_simulation/`.

Also create a human-readable acquisition and validation record by copying
`03_data/metadata/acquisition/_template.md`. The acquisition-record index and
the completed JARTIC example are under `03_data/metadata/acquisition/`.
