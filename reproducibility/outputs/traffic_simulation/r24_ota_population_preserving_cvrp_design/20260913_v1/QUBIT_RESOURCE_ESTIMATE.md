# Qubit and resource estimate

These are transparent design counts, not experiment results. For a position-based model with m vehicles, n sampled customers, binary assignment and activation variables, and binary capacity slack, use `N_pos = mn² + mn + m + ms`, where `s=ceil(log2(Q+1))`. For comparison, arc-based routing with binary rank/order auxiliaries uses `N_arc = m(n+1)n + ms + mn ceil(log2(n+1))`. Illustrative values below use normalized `q_i=1`, `Q=4`, `m=ceil(n/4)`, so `s=3`; this Q is not yet authoritative.

| n | m | Position N | Arc N | Position raw memory | Arc raw memory |
|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 10 | 13 | 16 KiB | 128 KiB |
| 3 | 1 | 16 | 21 | 1 MiB | 32 MiB |
| 4 | 1 | 24 | 35 | 256 MiB | 512 GiB |
| 5 | 2 | 68 | 96 | 4 ZiB | 1 QiB |
| 6 | 2 | 92 | 126 | 64 ZiB | about 1.07e9 QiB |

Raw memory is `16*2^N` bytes. The numbers illustrate why the solver unit must be a separate layer from the 39,956-stop Ota system. The resource gate is `EXACT_STATEVECTOR_FEASIBLE` for the n=2 position fixture, `SMALL_SCALE_ONLY` for n=3–4, and `EXACT_STATEVECTOR_NOT_RECOMMENDED` for n>=5. The selection rule cannot be changed to reach these sizes; if representative sub-instances exceed the gate, the result is a resource stop or a separately versioned classical-only tier.
