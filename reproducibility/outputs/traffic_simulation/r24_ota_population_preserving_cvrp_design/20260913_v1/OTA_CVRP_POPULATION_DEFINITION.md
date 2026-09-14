# Ota Ward CVRP population definition

The candidate population is `C_all = {i: i is a row in building_delivery_stops_scoped.csv}`. It contains 39,956 unique building delivery stops within the accepted Ota Ward scope, each with `stop_id`, building, chocho code, representative point, request count, and parcel-equivalent fields. It is a governed synthetic/candidate delivery population, not a census of observed operator customers.

Candidate locations are the building representative points from `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv`. Demand-related fields are joined by `stop_id` to the R04 weight artifact. The current network status records all 39,956 stops mapped, with delivery routeability accepted as a network-candidate result; all-pairs CVRP reachability still requires a future frozen routing artifact.

The depot authority is a public logistics-facility proxy. The current fixture selects `DEP_006`, Keihin Truck Terminal, Ota Ward, under the registered priority rule. It is not an observed operator depot. A multi-depot model is deferred; the current R24 comparison uses one fixed depot so reduction effects remain interpretable.

