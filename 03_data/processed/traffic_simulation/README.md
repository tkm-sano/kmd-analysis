# Tokyo traffic-simulation processed data

This directory contains regenerable, traffic-simulation-specific derivatives.
Generated files are ignored by Git; only this documentation and the directory
skeleton are tracked.

- `calibration/`: observations mapped to network elements and calibration
  targets.
- `demand/`: passenger, freight, and origin-destination demand derivatives.
- `driver_behavior/`: documented driver-skill and driving-style parameter
  scenarios.
- `road_network/`: clipped and normalized road-network intermediates.
- `sumo_inputs/`: generated SUMO networks, routes, additional files, and
  configurations.
- `traffic_profiles/`: time-of-day volume, speed, and vehicle-mix profiles.
- `validation/`: derived reference tables used to validate simulation runs.

Source downloads remain under `03_data/raw/traffic_simulation/`; run products
belong under `reproducibility/outputs/traffic_simulation/`; only reviewed final
artifacts belong under `06_outputs/traffic_simulation/`.
