# Classical CVRP formulation

For a selected representative instance, let `V={0} union C`, vehicles `k=1,...,m`, demand `q_i`, capacity `Q`, directed cost `c_ij`, and reachability `a_ij`. Binary `x_ijk` indicates vehicle k traverses arc i to j; `u_ik` is a load/order variable for subtour elimination and capacity propagation.

Minimize `sum_k sum_{i != j} c_ij x_ijk`. Hard constraints are: each customer has exactly one incoming and outgoing arc; each used vehicle leaves and returns to the depot once; depot flow is balanced; customer flow is continuous for every vehicle; `sum_i q_i y_ik <= Q`; load/order propagation eliminates subtours; unused vehicle variables are zero; and `x_ijk=0` whenever `a_ij=0`. Time windows, SOC, charging, weather, and dynamic traffic are excluded.

The exact reference and QUBO must use the same directed cost matrix, customer demands, vehicle count, capacity, depot, and reachability mask.

