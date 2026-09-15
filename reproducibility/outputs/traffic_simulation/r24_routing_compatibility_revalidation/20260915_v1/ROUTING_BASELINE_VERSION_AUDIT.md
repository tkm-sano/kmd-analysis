# Routing Baseline version audit

## Current authority

- canonical specification: `05_src/traffic_simulation/specifications/ROUTING_BASELINE_CANONICAL.md`
- authority: `CURRENT-NETWORK-COMPLETION-AUTHORITY-V18-GEOMETRY-REACCEPTED`
- network ID: `P13-THREE-TIER-RUN-3-GEOMETRY-REACCEPTANCE`
- SUMO version: 1.24.0
- run_3 network SHA-256: `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`
- acceptance SHA-256: `078bc16ccef865ba18e3f6c8010c7929b3b9e77f3740ee992a62de15c716cbc4`
- modeled vehicle class: `delivery`

The Routing Baseline defines directed reachability, road distance in metres and travel time in seconds. R13 minimizes free-flow travel time computed from run_3 edge length/speed; distance is reported along that selected directed path. Edge-offset endpoints retain remaining-origin and destination-partial segments. Unreachable costs remain null, never zero.

## Run roles

### run_2

- SHA-256 `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f`
- produced/accepted the full 39,956-row deterministic nearest-delivery-edge mapping;
- mapping CSV SHA-256 `226ff0d1ae91f08ea872cd99a3da5092fee19cf99259f7da81db79135762df7a`;
- pre-repair geometry lengths and any historical costs are superseded.

### run_3

- derived from the exact run_2 network;
- repaired edge/lane geometry endpoints and declared lengths;
- changed the byte/semantic network hash;
- did not change topology, IDs, one-way direction, permissions, delivery access or stop-mapping edge IDs;
- current fixture R12/R13 contains 10 customers plus depot/charger and demonstrates current cost/offset execution, but is not the source of the full population map.

## Compatibility decision

The full run_2 mapping is transferable to run_3 at the edge/proxy level. The old selected shape point, rather than `shape[len(shape)//2]` recomputed after repair, is projected onto the preserved run_3 shape. This avoids an 84-row index-shift artifact caused by inserted geometry endpoints. All 39,956 transferred points have zero shape gap and reproduce stored mapping distance within 0.001 m.

IDs and connectivity transfer; **costs do not**. Every selected instance must compute distance/travel time on run_3 using current offsets and the frozen Routing Baseline.

Decision: `REMAP_REQUIRED = NO`; `NETWORK_REBUILD_REQUIRED = NO`.
