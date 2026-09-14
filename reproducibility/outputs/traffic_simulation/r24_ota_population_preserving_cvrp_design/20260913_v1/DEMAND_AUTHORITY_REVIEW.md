# Demand authority review

Status: `DERIVED_DEMAND_AVAILABLE`, `STOP_DEMAND_AUTHORITY_INSUFFICIENT` remains open for execution.

The current authority is `reproducibility/config/traffic_simulation/baseline_demand.yml`: 2020 e-Stat 500m census population is area-weighted to the 2024 Ota population, then multiplied by the 2024 national parcel count per capita per day. The resulting unit is `parcel_equivalent/day`; the documented one-day total is 82,023.2049 expected and 82,023 integer. This is a spatial demand proxy, not observed customers, orders, delivery requests, or stops.

The candidate stop population is a separate derived B2C-style artifact with 39,956 stops, request and parcel-equivalent fields, and R04 mesh-derived `w_i`. It is suitable for a governed sampling frame and density stratification. Before execution, R24 must freeze whether `q_i=request_count`, `q_i=parcel_equivalent`, or another explicitly justified unit is used, and how its relation to the ward proxy is interpreted.

