# Retained data-processing scripts

The scripts in this directory support provenance for processed artifacts that
predate the additive Tokyo traffic-simulation layer. Some retain historical
input names and output-table relationships and must not be used as new traffic
data acquisition entry points.

New network, demand, calibration, simulation, and validation code belongs under
`05_src/traffic_simulation/` and imports locations from
`traffic_simulation.paths`. New raw files are stored only under
`03_data/raw/traffic_simulation/`; new generated inputs are stored only under
`03_data/processed/traffic_simulation/`. Port individual transformations from
this directory only after replacing their legacy paths and removing writes to
frozen synthetic-EVRP artifacts.
