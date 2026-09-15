# Customer demand definition

## Frozen rule

For each R24 benchmark customer `i`:

\[
q_i=N_i=\texttt{building\_delivery\_stops\_scoped.parcel\_equivalent}.
\]

`N_i` is the exact sum of realized household-day parcel-equivalents assigned to the positive-demand building. It is read from the saved 2026-01-01 building aggregate; it is not resampled, reweighted or converted.

Contract:

- type: integer
- unit: `METHODOLOGICAL_PARCEL_EQUIVALENT`
- general mathematical domain: non-negative integer
- R24 eligible-customer domain: positive integer (`q_i >= 1`)
- provenance: frozen synthetic snapshot and child-record aggregation
- physical interpretation: none asserted

## Snapshot-observed distribution

Source: `03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv`  
SHA-256: `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0`

| Statistic | Value |
|---|---:|
| customer count | 39,956 |
| sum | 81,859 |
| min | 1 |
| max | 14 |
| mean | 2.0487286015 |
| median | 2 |
| P01 / P05 / P10 / P25 | 1 / 1 / 1 / 1 |
| P50 / P75 / P90 / P95 | 2 / 3 / 4 / 5 |
| P99 / P99.5 / P99.9 | 7 / 8 / 10 |

Quantiles use the linear `(n-1)p` index convention; all reported values happen to be integers.

| `q_i` | customers | share |
|---:|---:|---:|
| 1 | 19,904 | 49.814796% |
| 2 | 9,082 | 22.730003% |
| 3 | 5,241 | 13.116929% |
| 4 | 2,902 | 7.262989% |
| 5 | 1,515 | 3.791671% |
| 6 | 725 | 1.814496% |
| 7 | 345 | 0.863450% |
| 8 | 141 | 0.352888% |
| 9 | 54 | 0.135149% |
| 10 | 25 | 0.062569% |
| 11 | 13 | 0.032536% |
| 12 | 5 | 0.012514% |
| 13 | 3 | 0.007508% |
| 14 | 1 | 0.002503% |

These are properties of a saved synthetic realization. “Observed” here means observed in that file, not empirically observed physical deliveries.

## Conservation and lineage

Before final routing eligibility, the candidate aggregate conserves 81,859 mapped parcel-equivalents. Final instances must store source building ID, source row/hash, `q_i`, and the sum `D`. Routing-based exclusions can change an instance or final eligible-population total, but must never change the `q_i` value of a retained building.
