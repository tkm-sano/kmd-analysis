# Vehicle-count rule

For every frozen sub-instance, define `m_min = ceil(sum_i q_i / Q)`. The primary CVRP condition is `m=m_min`, provided every individual customer satisfies `q_i<=Q` and the routing instance is feasible. This makes capacity pressure `rho=sum_i q_i/(mQ)` explicit and avoids arbitrary extra vehicles.

An optional sensitivity with `m=m_min+1` is a separate protocol version, justified only to test spare fleet capacity. The number of vehicles is not chosen to fit a desired qubit count. Vehicle identity, capacity, depot, and reachability remain common across classical, QUBO, and QAOA evaluations.

