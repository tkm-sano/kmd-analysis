# Tokyo traffic simulation extension

This directory is an additive research layer. It must not overwrite the
existing synthetic EVRP analysis or its frozen inputs and outputs.

## Source-code boundaries

- `network/`: OSM acquisition adapters, clipping, map matching, and SUMO
  network generation.
- `demand/`: time-of-day traffic and freight-demand construction.
- `calibration/`: JARTIC/road-census calibration and validation.
- `simulation/`: SUMO configurations, runners, and result extraction.
- `validation/`: structural and empirical checks for the new layer.

## Data boundaries

- Raw inputs: `03_data/raw/traffic_simulation/`
- Processed road networks: `03_data/processed/traffic_simulation/road_network/`
- Processed traffic profiles:
  `03_data/processed/traffic_simulation/traffic_profiles/`
- Generated SUMO inputs: `03_data/processed/traffic_simulation/sumo_inputs/`
- Reproducible run products:
  `reproducibility/outputs/traffic_simulation/`
- Curated final artifacts: `06_outputs/traffic_simulation/`

All paths stored in metadata must be relative to the repository root. Runtime
code should discover that root instead of relying on the process working
directory or a fixed `Path.parents[...]` index.

