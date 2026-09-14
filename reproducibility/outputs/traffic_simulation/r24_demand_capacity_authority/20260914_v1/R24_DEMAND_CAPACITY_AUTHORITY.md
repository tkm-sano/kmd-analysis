# R24 demand and capacity authority

## Purpose

Freeze traceable Ota Ward customer parcel demand lineage and the current vehicle payload authority before physical-unit CVRP implementation. This review is design/evidence work only. R23 remains closed and no QAOA, Aer, optimizer, QUBO, production CVRP, or large-statevector execution was performed.

## Existing R24 authority

The current R24 design retains `39,956` unique building delivery stops from `building_delivery_stops_scoped.csv`. The depot is `DEP_006` Keihin Truck Terminal, explicitly a public logistics-facility proxy and not an observed operational depot. The existing R24 design is hierarchical/population-preserving; it does not promote a random small instance to the Ota population.

Input hashes and command are in `PROVENANCE.md`. Existing R23 authority remains `05_src/traffic_simulation/R23_STATUS.md` and `reproducibility/outputs/traffic_simulation/r23_formal_closure/20260913_v1/R23_FORMAL_CLOSURE.md`; neither was modified.

## Current vehicle profile and Q authority

`managed_urban_ev_delivery_v1` is the active fixed scalar research profile: SUMO `delivery`, battery electric, maximum permissible mass 3,500 kg, unladen mass 1,500 kg, maximum payload 2,000 kg, dimensions 4.70 m × 1.70 m × 2.00 m. It is not a measured specific commercial vehicle. Therefore:

```text
Q = 2,000 kg
```

is adopted as the primary R24 payload capacity only as an inherited fixed-model assumption. It is not an observed payload capacity of a specific commercial vehicle. Registered Honda N-VAN e, Mitsubishi Minicab EV, Suzuki e Every, Hino Dutro Z EV, Isuzu ELF EV, and Mitsubishi Fuso eCanter records remain plausibility/sensitivity evidence only; they are not averaged or used to replace the runtime profile.

## Demand proxy lineage and meaning

The national parcel source is MLIT FY2024, 5,031,470,000 parcels; the national population denominator is Statistics Bureau 2024-10-01, 123,802,000; the spatial population support is 2020 e-Stat 500 m JGD2011 mesh population, rescaled to Ota's 2024-04-01 population 736,652. The mesh formula and largest-remainder rules are fixed in `baseline_demand.yml` and `prepare_baseline_demand.py`.

The customer-level expected proxy is `N_i^(parcel/day)`, the model-derived expected parcel-equivalent amount per active building stop per day, obtained by summing upstream expected household values over the scoped building assignment. It is not an observed parcel count, customer order record, or operator stop count. The current integer `parcel_equivalent` field is a one-day Poisson realization (`2026-01-01`, seed `20260829`).

For the frozen 39,956 active stops, the reconstructed expected total is `61,793.0020700188 parcel-equivalent/day`; the realized stop artifact total is `81,859`. Distribution diagnostics for the expected proxy are in `ota_capacity_summary.json`.

## Parcel-weight evidence

The reviewed sources are listed in `parcel_weight_sources.csv`. MLIT provides national parcel counts and the e-Stat/MLIT transport survey defines aggregate宅配便貨物重量, but the reviewed public outputs do not provide a parcel-level weight distribution or a representative mean with a denominator matching this B2C-style customer proxy. Japan Post's 25 kg/30 kg limits are service maxima, not observed parcel weights. Consequently:

```text
STOP_PARCEL_WEIGHT_AUTHORITY_INSUFFICIENT
```

remains open. No physical `kg/customer/day` value is fabricated.

## Chosen conversion and units

The intended deterministic expected-mass conversion is:

```text
q_i [kg/customer/day] = N_i^(parcel/day) * E[W_parcel] [kg/parcel]
```

It cannot yet be evaluated because `E[W_parcel]` lacks authority. `customer_demand_kg.csv` contains the traceable parcel proxy and blank kg fields with an explicit blocked status. The future CVRP constraint is:

```text
sum_i q_i y_ik <= Q,  Q = 2,000 kg
```

where `y_ik` indicates assignment of customer `i` to vehicle `k`. Weight capacity only is planned; parcel volume may bind in real last-mile delivery and is deferred.

## Ota-wide capacity and representativeness

`D_total = sum_i q_i [kg/day]`, `m_min_capacity = ceil(D_total / 2,000 kg)`, and `rho = D_total/(mQ)` are not computable until parcel-weight authority passes. The value `m_min_capacity` is a capacity-only theoretical lower bound on fleet size, never a required fleet size: route geometry, service time, working hours, time windows, charging, and traffic are excluded.

The current customer artifact has no frozen R24 all-pairs directed OD/reachability matrix and no completed representativeness diagnostics. The existing hierarchical design (`C_all -> C_s -> C_{s,r}`) remains the applicable candidate-generation policy. No stratum-level kg totals or small-instance capacity activity result is claimed here. In particular, `STOP_CAPACITY_NON_BINDING_AT_QUANTUM_SCALE` is conditional/not assessed, not resolved by artificial scaling.

## Limitations and final verdict

The parcel proxy is derived, population-calibrated, and partly conditioned on a synthetic Poisson realization. Depot is a public-facility proxy. Runtime vehicle Q is a fixed research-model scalar, not an observed fleet distribution. Volume capacity and full operational feasibility are deferred.

Final verdicts:

```text
STOP_PARCEL_WEIGHT_AUTHORITY_INSUFFICIENT
STOP_REPRESENTATIVENESS_UNVERIFIED
```

`R24_DEMAND_AND_CAPACITY_AUTHORITY_ESTABLISHED` is not granted because the physical kg conversion and Ota-wide capacity lower bound remain blocked. R24 production implementation and all quantum/optimizer work remain unauthorized.

Next permitted task after resolving both stops: freeze the R24 physical-unit CVRP specification and derive the exact classical reference formulation, QUBO encoding, qubit/resource formulas, and penalty bounds. Do not run QAOA yet.
