# R24 routing compatibility revalidation

Decision ID: `R24-ROUTING-COMPATIBILITY-20260915-v1`  
Scope: `ROUTING COMPATIBILITY / REACHABILITY / ELIGIBILITY REVALIDATION ONLY`

## Verdict

`ROUTING_COMPATIBILITY_VERDICT = ROUTING_COMPATIBILITY_ACCEPTED_WITH_LIMITATIONS`

`VEHICLE_GRAPH_VERDICT = CURRENT_GRAPH_COMPATIBLE_WITH_LIMITATIONS`

`FINAL_C_ELIGIBLE_READY = YES_WITH_LIMITATIONS`

The accepted run_3 network can reuse the historical run_2 full-population edge mapping without rebuild or nearest-edge remapping. Run_3 explicitly preserves topology, edge IDs, one-way direction, lane permissions, delivery access and stop-mapping edge IDs. This audit checked every mapping row against run_3 and reconstructed the exact run_2-selected proxy point on the corresponding run_3 edge shape.

## Population result

| Result | Customers | Parcel-equivalents |
|---|---:|---:|
| routing candidates checked | 39,956 | 81,859 |
| final `C_eligible` | **39,930** | **81,793** |
| excluded | 26 | 66 |

Reachability classifications are 39,930 `ROUNDTRIP_REACHABLE`, one `OUTBOUND_ONLY`, one `INBOUND_ONLY`, 24 `UNREACHABLE`, and zero `MAPPING_INVALID`.

## Graph and SCC method

The population graph contains 112,625 run_3 external edges permitting SUMO `delivery` and 260,249 permitted edge-to-edge transitions. Connection-aware SCC decomposition produced 561 SCCs. `DEP_006` edge `617631294` belongs to `DELIVERY_SCC_000001`, containing 111,428 delivery edges.

All 39,930 eligible proxy edges are in the depot SCC. In a directed graph, membership in the same SCC means a directed path exists in both directions for every pair of vertices. It therefore certifies population-level directed pairwise reachability without constructing approximately 1.596 billion ordered customer pairs. Selected instances must still compute and validate their complete ordered-pair costs.

The repository's accepted R13 runner uses a less restrictive delivery-permitted node-edge reachability implementation rather than connection transitions. A full-population cross-check produced the same outbound/inbound classification for all 39,956 candidates. Instance-level path validation must nevertheless check consecutive SUMO connections so that a shortest path does not silently ignore a turn restriction.

## Mapping result

- all 39,956 run_2 edge IDs exist in run_3;
- all stored from/to node IDs match run_3;
- all mapped edges permit SUMO `delivery`;
- all source coordinates are valid;
- the run_2-selected proxy point lies on its run_3 edge shape with maximum transfer gap 0 m;
- all mapping distances reproduce within 0.001 m;
- maximum retained mapping distance is 94.628786 m;
- run_2 distances/travel times are not reused; instance costs must use run_3 repaired lengths and speeds.

No new distance threshold was introduced. The historical maximum remains a geometric-proxy limitation, not an observed entrance or curb-access claim.

## Vehicle boundary

The kei-class electric commercial van is represented by the existing SUMO `delivery` permission domain. Its small reference envelope (3.395 m × 1.475 m and approximately 1.9 m high) does not establish unrestricted physical/legal access. The graph models one-way and delivery access/permission restrictions and this audit uses SUMO connections; it does not provide complete field authority for road width, height, gross-weight, temporary/time-dependent restrictions, private authorization, legal stopping or loading.

No separate kei-specific graph filter is supported or required for this controlled benchmark. This is model compatibility, not an assertion of real-world access to every building.

## Execution boundary

`C_ELIGIBLE_MANIFEST.csv` is an assessed candidate ledger: only rows with `eligibility_status=ELIGIBLE` constitute final `C_eligible`. It is not a sampled routing instance. Building identities sharing one proxy remain separate.

Capacity values `q_i`, `Q=14`, rho regimes and fleet derivation were not modified. No all-pairs OD, demand generation, instance generation or optimization was performed.

`NEXT_EXECUTABLE_TASK = freeze R24 instance generation specification`
