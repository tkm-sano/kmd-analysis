# System conditions

Benchmark runs use one fresh process each, with environment variables OMP_NUM_THREADS=1, MKL_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1 and NUMEXPR_NUM_THREADS=1. The run wrapper requests CPU affinity `[0]`; effective affinity, load average, free memory, swap and competing processes are recorded per run. Aer backend options are otherwise the frozen source defaults. Any failure is retained and invalidates the corresponding formal comparison.

