# Scientific model

`R23_REDUCED_PROBLEM_CANONICAL.md` and `core.py` agree on depot 0, customers 1..n, closed directed route, one visit per customer/position, customer-only row-major `x[i,t]`, and `n²` variables. The model is route ordering only and has no EVRP feasibility constraints. Assessment: `SUPPORTED_WITH_LIMITATIONS`.
