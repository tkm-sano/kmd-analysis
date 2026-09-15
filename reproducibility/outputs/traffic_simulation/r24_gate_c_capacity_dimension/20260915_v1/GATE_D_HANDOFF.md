# Gate D handoff contract

Gate D is not executable yet because Gate C is not accepted.

## Provisional handoff after remediation

- Selected dimension: expected to be reviewed first as mass `[kg]`; not frozen.
- Demand authority required: Japanese residential B2C parcel-level actual gross mass with parcel identifier/count, observation period, sampling frame, missingness and B2C/destination scope; a mean must include uncertainty or bins/distribution must be reproducible.
- Vehicle authority: Gate B's variant-preserving kei-class official payload references; no universal 350 kg constant yet.
- Aggregation requirement: retain each source parcel-equivalent/weight draw or justified expectation, then sum by benchmark building without losing source IDs; specify whether expected or realized mass is constrained.
- Conversion requirement: never equate `parcel_equivalent` to kg; document population transfer and uncertainty if an external distribution is used.
- Limitations: synthetic demand, no observed service event, no Ota carrier fleet/load observation, and potential non-binding capacity.
- Routing: `ROUTING_REVALIDATION_REQUIRED_AFTER_VEHICLE_FREEZE` remains.

After Gate C accepts a dimension, routing compatibility revalidation should occur before final `C_eligible` and before Gate D closes concrete instance authority. It may precede or run independently of numerical `q_i/Q/m` research because vehicle class is already frozen, but all results must share one accepted network/access profile before instance generation.

Gate D alone will decide concrete `q_i`, `Q` and `m`; none is supplied here.

`NEXT_EXECUTABLE_TASK = targeted demand-side mass evidence acquisition`

