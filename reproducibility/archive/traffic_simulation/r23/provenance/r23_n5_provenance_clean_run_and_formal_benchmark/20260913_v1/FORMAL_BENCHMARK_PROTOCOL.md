# Formal benchmark protocol

The benchmark compares `run_single(..., implementation="original")` and `implementation="v4"` on the same n=3 control instance, p=1, lambda=4, COBYLA, fixed_0.1, seed 17, cap 20, CPU Aer statevector, no shots. Each implementation used three fresh processes. Timing boundaries are total process execution, Aer execution, and v4/original postprocess. Peak RSS is the same `ru_maxrss` process metric. No failed or favorable repetition was excluded.

This is a controlled repeatability benchmark, not the requested full n=5 baseline comparison; n=5 full baseline is `NOT_TESTED` due prohibitive historical cost.

