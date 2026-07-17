# Tokyo traffic simulation extension

This directory is an additive research layer. It must not overwrite the
existing synthetic EVRP analysis or its frozen inputs and outputs.

The data-governance, minimum-area validation, CI, and server-migration tasks
are recorded in [`implementation_plan.md`](implementation_plan.md).

## Source-code boundaries

- `network/`: OSM acquisition adapters, clipping, map matching, and SUMO
  network generation.
- `demand/`: time-of-day traffic and freight-demand construction.
- `calibration/`: JARTIC/road-census calibration and validation.
- `simulation/`: SUMO configurations, runners, and result extraction.
- `validation/`: structural and empirical checks for the new layer.

All new modules must import canonical locations from `traffic_simulation.paths`.
They must not infer the repository root from a fixed `Path.parents[...]` index
or contain a host-specific absolute path.

## Data boundaries

- Raw inputs: `03_data/raw/traffic_simulation/`, separated into the
  source-specific directories documented in that directory's `README.md`.
- Processed road networks: `03_data/processed/traffic_simulation/road_network/`
- Processed traffic profiles:
  `03_data/processed/traffic_simulation/traffic_profiles/`
- Generated SUMO inputs: `03_data/processed/traffic_simulation/sumo_inputs/`
- Processed calibration data: `03_data/processed/traffic_simulation/calibration/`
- Processed demand data: `03_data/processed/traffic_simulation/demand/`
- Processed driver-behavior parameters:
  `03_data/processed/traffic_simulation/driver_behavior/`
- Processed validation data: `03_data/processed/traffic_simulation/validation/`
- Source registry: `03_data/metadata/traffic_simulation_sources.csv`
- Reproducible run products:
  `reproducibility/outputs/traffic_simulation/`
- Curated final artifacts: `06_outputs/traffic_simulation/`

All paths stored in metadata must be relative to the repository root. Runtime
code uses `traffic_simulation.paths` to discover that root independently of
the process working directory.
