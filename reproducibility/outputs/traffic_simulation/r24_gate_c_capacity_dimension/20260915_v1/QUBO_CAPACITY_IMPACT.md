# Conceptual QUBO capacity impact

No QUBO was constructed or executed.

| dimension | representation | slack/encoding consequence | assessment |
|---|---|---|---|
| mass | convert only at an authority-preserving resolution such as integer grams or justified coarser units | one capacity slack per route/vehicle context; binary width grows with scaled Q; rounding must be conservative and declared | feasible, but evidence and scaling required |
| volume | integer litres or another justified resolution | analogous slack; fine m³ scaling can increase bit width and rounding error | feasible but unsupported data |
| parcel count | native integer if physical parcels and Q were authoritative | smallest scaling burden and simple slack | computational convenience cannot replace physical authority |
| load unit | integer by construction | simple only because normalization embeds the assumption | low encoding cost, very high semantic arbitrariness |
| mass+volume | two capacity constraints and separate slacks/penalties | roughly duplicates capacity-state/slack machinery and requires penalty balancing | unnecessary complexity for current R24 |

Logical-variable growth depends on the future formulation, number of vehicles/routes and Q bounds; no numeric qubit count is asserted. Binding behavior was not used as a selection criterion.

