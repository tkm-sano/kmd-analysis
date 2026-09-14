# R24 design pre-start review

Review version: `20260913_v1`; reviewed 2026-09-14. This directory freezes the design gate only. No R24 QAOA, Aer, production, or large-statevector run was performed.

Current authority is `05_src/traffic_simulation/R23_STATUS.md`. R23 remains closed with exact optimal route recovery 3/3 and optimizer-reported success 2/3. R24 remains `R24_NOT_STARTED`.

Decision: capacity-only is trivial for the R23 single-tour model. A two-trip single-vehicle formulation is scientifically meaningful and is recommended, subject to demand and capacity authority revisions recorded here. Design status: `R24_DESIGN_APPROVED_WITH_REVISIONS`; implementation is gated.

## Contents

The companion files define the delta, candidate comparison, classical model, exact reference, QUBO, resource gate, metrics, arbitrariness controls, protocol, stop conditions, and integrity review. SHA-256 values are in `SHA256SUMS`.

