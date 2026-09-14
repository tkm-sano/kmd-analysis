# Recommended R24 problem

`R24_SINGLE_VEHICLE_MULTI_TRIP_RECOMMENDED`.

The vehicle starts at the depot, performs up to `K=2` labelled depot-to-depot trips, and returns to the depot after each active trip. Every customer is served exactly once. Each trip has load at most `Q`. Empty trip 2 is allowed for low-pressure scenarios, but trip labels are canonicalized in the exact reference and duplicate labelings are not counted as distinct scientific solutions.

Scenario levels are fixed before execution by total-demand ratio `rho = sum(q_i)/Q`: low `rho=1.25`, medium `rho=1.50`, high `rho=1.75`, using predeclared integer demand vectors that satisfy `max(q_i)<=Q` and `rho<=2`. These are design levels, not post-hoc selections.

