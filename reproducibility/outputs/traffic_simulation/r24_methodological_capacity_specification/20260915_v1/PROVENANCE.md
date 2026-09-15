# Provenance and execution boundary

Date: 2026-09-15 JST  
Branch: `main`  
Start SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b`  
End SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b` (no commit)

## Primary data inspected

- `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv`
- SHA-256: `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`
- rows: 39,956 data rows
- saved aggregate: 81,859 parcel-equivalents

The file was read only. Distribution statistics and `q_i>Q` counts were recomputed directly from its integer `parcel_equivalent` column using Python standard-library CSV/statistics logic. No customer set was sampled.

## Authority inspected

- Gate A minimal benchmark abstraction and demand-conservation contract
- Gate B vehicle-class decision and routing compatibility assessment
- Gate C capacity-dimension decision and Gate D handoff
- targeted demand-side mass evidence review and Gate C reassessment
- end-to-end workflow authority and historical R24 design/resource artifacts for terminology and QUBO context

## Scientific choices introduced

- methodological unit and `q_i=N_i` frozen
- `Q=14` frozen from the saved population maximum
- controlled targets 0.50/0.70/0.90 frozen
- `m` derivation and validation/degeneracy rules frozen
- Gate C and design-level Gate D closed with limitations

Input data mutation: `NONE`. Demand generation: `NONE`. Eligible population generation: `NONE`. Random/controlled/fixed-anchor instance generation: `NONE`. Routing revalidation: `NONE`. Physical mass/volume generation: `NONE`. MILP/QUBO/QAOA/Aer/optimization: `NONE`.

Tracked changes at start/end: `NONE`. This output directory is ignored and uncommitted. Output hashes are recorded in `SHA256SUMS.txt`, excluding the manifest itself.
