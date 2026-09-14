# Qubit and statevector estimate

Encoding 1 estimate uses `K=2`, `s=ceil(log2(Q+1))`, and `N=2(n²+n+1+s)`. The table uses the predeclared normalized capacity register `Q=4` (`s=3`) only as a transparent resource scenario; this is not an approved scientific input. Raw complex128 memory is `16*2^N` bytes.

| n | Routing vars | Assignment vars | Capacity/slack vars | Total logical qubits | Statevector memory |
|---:|---:|---:|---:|---:|---:|
| 2 | 8 | 4 | 8 | 20 | 16 MiB |
| 3 | 18 | 6 | 8 | 32 | 64 GiB |
| 4 | 32 | 8 | 8 | 48 | 4 PiB |
| 5 | 50 | 10 | 8 | 68 | 4 ZiB |
| 6 | 72 | 12 | 8 | 92 | 64 ZiB |

For Encoding 2 with two vehicles the counts are identical under this fixed slot representation. Encoding 3 counts are `N=2(n²+n+1+n(Q+1))`; for Q=4 this gives 34, 56, 82, 112, 146 qubits for n=2,...,6. The corresponding raw memories are approximately 256 GiB, 1 EiB, 64 YiB, 64 RiB, and 2^154 bytes respectively.

Resource verdict: n=2 `EXACT_STATEVECTOR_FEASIBLE`; n=3 `SMALL_SCALE_ONLY`; n=4–6 `EXACT_STATEVECTOR_NOT_RECOMMENDED`. R23's n=5 25-qubit CPU-Aer burden is evidence against assuming larger R24 instances are practical. n=2–3 are the initial resource gate; n=4 only with an explicit budget and no production-scale claim.
