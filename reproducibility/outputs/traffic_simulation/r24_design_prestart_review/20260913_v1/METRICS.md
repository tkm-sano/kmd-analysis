# Metrics

Inherited quantum metrics are raw full-state `P_feasible`, raw full-state `P_optimal`, optimality gap, and runtime. Added operational metrics are capacity-valid probability, trip count, capacity utilization, and capacity violation amount. Customer completeness is a hard feasibility component and is reported separately from probability metrics. Vehicle count is always one in R24 and is not a performance metric.

No probability is renormalized. Optimizer success, exact route recovery, and `P_optimal` remain distinct. Runtime is software simulation burden, not QPU time or quantum advantage.

