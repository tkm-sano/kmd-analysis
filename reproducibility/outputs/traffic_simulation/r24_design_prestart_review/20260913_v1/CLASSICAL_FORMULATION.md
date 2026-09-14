# Classical formulation first

Depot is `0`; customers are `i in C={1,...,n}`; trips are `k in {1,2}`; positions are `t in {1,...,n}`. Parameters are demand `q_i`, capacity `Q`, directed travel cost `c_ij`, and reachability `a_ij`. Unreachable arcs are forbidden and never assigned a finite penalty surrogate.

Binary variables: `x[i,t,k]` means customer `i` occupies position `t` of trip `k`; `y[i,k]` means customer `i` is assigned to trip `k`; `z[k]` activates trip `k`. Each trip has a first and last depot connection. The load slack `u[k]` is an integer variable used only in the exact classical model and is encoded later.

Minimize total directed travel cost over active closed trips. Subject to: `sum[k,t] x[i,t,k]=1` for every customer; `sum[i] x[i,t,k]=z[k]` for every trip-position; `sum[t] x[i,t,k]=y[i,k]`; `sum[i] q_i y[i,k] + u[k] = Q z[k]`; `0<=u[k]<=Q`; `z[1]>=z[2]` to remove unused-trip label symmetry; and all selected arcs reachable. A trip with no customers has zero route cost and is inactive.

The model is fixed before any QUBO or optimizer choice. Objective remains directed total travel time/cost comparable with R23.

