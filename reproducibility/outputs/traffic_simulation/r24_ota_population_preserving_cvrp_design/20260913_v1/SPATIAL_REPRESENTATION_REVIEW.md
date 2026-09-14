# Spatial representation review

The primary spatial variables are depot-to-stop shortest-path travel time, geodesic coordinates for coverage checks, and local road-network density. Network travel time is the governing service relation; coordinates are retained for dispersion and map-level audit. Straight-line distance cannot replace network distance in the CVRP objective.

The candidate population has broad Ota Ward coverage but the current accepted network artifact does not yet provide the complete customer-to-customer OD matrix required for a final CVRP. Therefore spatial representation is design-supported, not execution-ready. A future input lock must include depot-to-customer and customer-to-customer reachability, travel time, network hash, and unreachable-arc counts.

