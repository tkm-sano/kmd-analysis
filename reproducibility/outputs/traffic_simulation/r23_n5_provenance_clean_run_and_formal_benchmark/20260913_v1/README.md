# R23 N5 provenance-complete clean run and benchmark

The protocol was frozen and sealed before execution. Three fresh v4 clean runs were executed from the frozen source/input/environment. Benchmarking was performed as a separate controlled n=3 fresh-process comparison because a full n=5 baseline run is prohibitive (historical rank01 was 42.62 hours). Existing scientific artifacts were not modified.

Clean-run gate: `R23_PROVENANCE_CLEAN_RUN_PASSED` for the three new v4 runs. Benchmark gate: `FORMAL_BENCHMARK_PASSED_WITH_LIMITATIONS` (controlled n=3 only; n=5 full baseline comparison not executed). Final independent gate remains `CODE_AUDIT_FAIL` / `RESULT_REPRODUCED_WITH_LIMITATIONS`.

