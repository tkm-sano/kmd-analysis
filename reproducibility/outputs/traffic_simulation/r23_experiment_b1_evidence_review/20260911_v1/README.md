# R23 Experiment B1 Evidence Review

Classification: `EXPERIMENT_B1_EVIDENCE_ACCEPTED_WITH_LIMITATIONS`

This review analyzes the frozen B1 v2 artifacts only. No B1 rerun, B2, n≥5, Experiment C, finite-shot, noise, QPU, or Full EVRP execution was performed.

## Key interpretation

`exact_optimum_found` means the best decoded feasible route in the final statevector was the exact route. It does not mean `P_optimal` is near 1; `P_optimal` is the probability mass assigned to the exact optimal state.

## Main findings

- 36/36 scientific runs valid; 36/36 exact best decoded routes; relative optimality gap 0.
- Initialization produces observable distributional variation in every instance×p cell; best decoded route does not materially change in this sample.
- p=3 improves P_feasible and P_optimal in 15/18 pairs each, so the effect is not uniform; p=3 increases CPU simulation burden.
- COBYLA reports success in 5 runs and MAXFUN failure in 31; this is not converted into scientific failure, and convergence is not claimed.

## Artifacts

- `run_level_dataset.csv` / `run_level_dataset.json`: Table 1
- `initialization_sensitivity.json` / `table_2_initialization_sensitivity.csv`: Table 2
- `p_depth_comparison.json` / `table_3_p_depth_paired.csv`: Table 3
- `optimizer_diagnostics.json`: Table 4
- `formal_a_reproducibility.json`: Table 5
- `runtime_analysis.json`, `evidence_review.json`, `integrity.json`, `b2_readiness.json`
- `figure_1_P_feasible_by_initialization.png` through `figure_4_P_optimal_vs_P_feasible.png`

Manifest SHA-256: `8db16a3f66191c1de34b4f1cbaededdf9760cf0fb13f9e1d852b2c4e26cae767`
