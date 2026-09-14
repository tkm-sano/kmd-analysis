# Demand authority review

Status: `DERIVED_DEMAND_AVAILABLE`, but `STOP_DEMAND_AUTHORITY_INSUFFICIENT` remains for production R24 until the derived proxy is explicitly adopted for this experiment.

Repository evidence: `reproducibility/config/traffic_simulation/baseline_demand.yml` and its current specification derive integer `parcel_equivalent/day` from 2020 500m mesh population, the 2024 Ota population, and 2024 national parcel counts. The current total is 82,023 parcel-equivalents/day. The registry explicitly says this is synthetic, not customer count, request count, order data, or observed stops. The 39,956 stop artifact is a candidate B2C pipeline output and does not by itself authorize customer demands for R24.

Therefore no real customer demand claim is permitted. For the design-scale quantum instance, the authority must be a new frozen normalized experimental demand record derived from an identified stop sample or an explicitly approved transformation of the proxy. It must state: parcel-equivalent unit, mapping to one customer, distribution/parameters, sampling method, seed, rounding, bounds, normalization, and selection relationship. Until then this is a revision gate, not a run input.

