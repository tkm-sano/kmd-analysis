# Provenance and execution boundary

Date: 2026-09-15 JST  
Branch: `main`  
Start SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b`  
End SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b` (no commit)

## Repository evidence inspected

- `reproducibility/config/traffic_simulation/scenario_profiles/managed_urban_ev_delivery_v1.yml` (`8f837f7a...`)
- `reproducibility/config/traffic_simulation/datasets/urban_lastmile_vehicle_records_v1.csv` (`1d31779b...`)
- `reproducibility/config/traffic_simulation/datasets/urban_lastmile_vehicle_records_v1.yml` (`f49610df...`)
- `reproducibility/config/traffic_simulation/evidence/lastmile_delivery_sources_v1.yml` (`94986eba...`)
- `reproducibility/config/traffic_simulation/evidence/lastmile_delivery_deployment_evidence_v1.yml` (`7a22e2a0...`)
- `reproducibility/config/traffic_simulation/decisions/urban_lastmile_vehicle_population_decision_v1.yml` (`badaecbd...`)
- `05_src/traffic_simulation/specifications/urban_lastmile_vehicle_population_evidence_v1.md` (`ebf21fbf...`)
- `05_src/traffic_simulation/specifications/ROUTING_BASELINE_CANONICAL.md` (`9eb9966d...`)
- latest Gate A sign-off (`cb9521e6...`)
- prior Gate B open contract (`327b6214...`)
- `03_data/processed/ev_truck_specs_scenario.csv` (`795a5d60...`)
- `reproducibility/config/traffic_simulation/evrp_r10_ev_v1.yml` and historical R10 vehicle definition, used only to detect the prior mixed assumption/reference boundary.

## External primary sources accessed

Accessed 2026-09-15: Honda N-VAN e: official type/spec/charging pages; Mitsubishi Motors Minicab EV specification/charging pages; Suzuki e Every release, EV-performance and cargo pages; Hino Dutro Z EV 2026 release; Isuzu ELF EV product page; Sagawa lightweight-EV last-mile deployment page; Yamato N-VAN pilot and eCanter deployment/specification releases. Exact URLs are preserved in the evidence CSVs. Values are classified `MANUFACTURER_OFFICIAL`, primary operator `TECHNICAL_DOCUMENTATION`, or repository-only `REPOSITORY_FIXED_ASSUMPTION`; no secondary source supplies an adopted value.

Web pages are live sources and were not downloaded into the repository. Reproducibility rests on recorded URLs/access date plus the hashed local source registry; later source drift requires a new review version.

## Mutation and prohibited execution

Tracked input changes: none at start and end. Output directory is ignored by repository rules and uncommitted. Scientific/data mutation: **NONE**. Final `C_eligible` generation: **NONE**. Demand/capacity/parcel generation: **NONE**. Instance generation: **NONE**. Optimization/MILP/QUBO/QAOA/Aer: **NONE**. Output hashes are in `SHA256SUMS.txt`, excluding the manifest itself.
