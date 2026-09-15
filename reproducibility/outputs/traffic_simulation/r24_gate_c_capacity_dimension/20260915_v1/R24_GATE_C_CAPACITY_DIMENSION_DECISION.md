# R24 Gate C capacity-dimension decision

Decision ID: `R24-GATE-C-CAPACITY-DIMENSION-20260915-v1`  
Scope: `CAPACITY DIMENSION EVIDENCE / COMPARISON / DECISION ONLY`  
Verdict: **`GATE_C_REQUIRES_TARGETED_REMEDIATION`**

`R24_PRIMARY_CAPACITY_DIMENSION = NOT_FROZEN`

`PRIMARY_CANDIDATE = mass [kg]`

Mass is physically meaningful and the selected kei-class electric commercial van has strong official payload evidence. It is not accepted as the R24 primary dimension because the demand snapshot has no matching parcel-level mass, mass distribution or population-valid conversion authority. Vehicle-side evidence alone cannot satisfy `unit(q_i)=unit(Q)`.

## Candidate decisions

- Mass — `PRIMARY_CANDIDATE`; requires one targeted demand-side authority remediation.
- Parcel-equivalent count — `METHODOLOGICAL_ONLY`; directly traceable on the demand side, but manufacturers provide no physical parcels-per-vehicle capacity and `parcel_equivalent` is not an observed parcel.
- Volume — `DEFER`; neither parcel volume nor comparable manufacturer usable cargo volume is established.
- Standardized load unit — `REJECT_FOR_R24`; pallet/unit-load standards do not match residential loose-parcel kei-van delivery, while a custom `1 parcel = 1 LU` would be researcher-defined.
- Multi-dimensional mass+volume — `DEFER`; physical in principle, but both demand dimensions are not available and it adds unnecessary constraints/encoding cost at this stage.

## Evidence boundary

The frozen source contains 73,547 synthetic household-day records with 82,246 parcel-equivalents, and the mapped building aggregate contains 39,956 benchmark customers with 81,859 parcel-equivalents. `parcel_equivalent` is a calibrated, synthetically realized abstract content count. It is not an actual parcel ID/count, kg, m³, product category or shipment class. No automatic conversion is authorized.

The existing Japanese evidence remains insufficient for primary B2C mass conversion. Air-cargo surveys provide actual aggregate weight and counts for an air-cargo survey-day population; the rural Ogawa demonstration is small and lacks an extractable distribution; roll-box-pallet measurements use cages rather than parcels; service/fee limits are not observed weights; and foreign evidence has population-transfer problems. `STOP_PARCEL_WEIGHT_AUTHORITY_INSUFFICIENT = REMAINS`.

## Selection logic

Capacity binding behavior was **not** used to select a dimension. A physically valid capacity may be non-binding for small benchmark instances. Evidence, physical meaning, unit compatibility and downstream traceability were prioritized.

No physical and methodological scenario is mixed. A future normalized/count capacity-active test may be separately labeled `METHODOLOGICAL_CAPACITY`; it cannot close physical Gate C or be called the R24 primary physical scenario.

No `q_i`, `Q`, `m`, final eligible population, instance or optimization artifact was created.

`BLOCKING_ITEM = Japanese residential B2C parcel-level actual gross-mass authority with matching parcel denominator and documented sampling frame`

`NEXT_EXECUTABLE_TASK = targeted demand-side mass evidence acquisition`

