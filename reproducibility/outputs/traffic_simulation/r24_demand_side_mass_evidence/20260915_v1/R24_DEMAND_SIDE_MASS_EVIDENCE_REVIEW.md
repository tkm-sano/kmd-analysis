# R24 targeted demand-side mass evidence review

Decision ID: `R24-DEMAND-SIDE-MASS-EVIDENCE-20260915-v1`  
Scope: `TARGETED DEMAND-SIDE MASS EVIDENCE ACQUISITION ONLY`  
Target population: Japanese residential B2C last-mile parcels  
Mass-authority verdict: **`DEMAND_SIDE_MASS_AUTHORITY_INSUFFICIENT`**

## Decision

No reviewed, publicly accessible source supplies a population-compatible parcel-level gross-mass distribution, numerical histogram/CDF, or individual observations that can authorize sampling for R24. Consequently:

- `RECOMMENDED_F_W = NOT_AUTHORIZED`
- `GATE_C_VERDICT = GATE_C_REQUIRES_TARGETED_REMEDIATION`
- `R24_PRIMARY_CAPACITY_DIMENSION = NOT_FROZEN`
- mass `[kg]` remains a physically preferred candidate, not an accepted primary dimension.

The closest domestic evidence is the MLIT Ogawa-district delivery demonstration: three carriers supplied actual daily parcel count, type, size and weight data over 33 days, excluding inter-company transport. The public report presents daily aggregate charts, not parcel-level numerical observations, bins, CDF, moments or downloadable microdata. Its rural, small-sample operating context also differs materially from Ota residential B2C. It is therefore `CLOSE_PROXY_EVIDENCE`, but cannot define `F_W`.

The MLIT Domestic Air Cargo Flow Survey has stronger measurement provenance and reports actual weight and counts, including an air-courier category. It is nevertheless a one-day domestic-air-freight population, mixes sender/receiver purposes, reports shipment/case aggregates rather than a parcel-level distribution, and does not identify Ota-like residential B2C deliveries. It is `WEAK_PROXY_EVIDENCE`, not the sampling authority.

## Acceptance-criteria test

| Requirement | Result | Basis |
|---|---|---|
| Target or close-proxy empirical evidence | Partial | Ogawa is close in delivery semantics but rural, small and publicly aggregate-only |
| Source provenance | Pass | MLIT and peer-reviewed sources are traceable |
| Mass unit | Pass | kg is stated in the closest sources |
| Usable distribution / sampling rule | **Fail** | no numerical parcel-level observations, histogram/CDF or supported parametric fit |
| Parcel-equivalent mapping rule | Conditional only | mathematically definable, but no authorized `F_W` |
| Uncertainty / limitation | Pass | population and aggregation mismatches are documented |
| Vehicle payload unit compatibility | Pass on vehicle side only | kei-class payload is expressed in kg; demand-side `q_i` remains unauthorized |

Failure of the usable-distribution criterion is decisive. A mean, service maximum or chart image cannot be promoted to an empirical sampling distribution.

## Frozen demand semantics

The existing `parcel_equivalent` is a **calibrated synthetic realized abstract content count**. It is not an observed parcel identifier or verified physical parcel count. The frozen source horizon and counts are not changed:

- source horizon: `2026-01-01`
- synthetic household-day records: `73,547`
- source parcel-equivalents: `82,246`
- mapped-building aggregate parcel-equivalents: `81,859`

If a valid `F_W` is later authorized, the result would be a **synthetic parcel mass realization**, not reconstruction of actual delivered parcels.

## Fallback decision

Three fallbacks were compared:

- Fallback A — keep physical mass and import a proxy distribution as an explicit assumption. This retains kg but introduces the largest population-transfer and distribution-shape choices.
- Fallback B — use parcel-equivalent count as the R24 capacity dimension. This is demand-traceable, but physical vehicle capacity in parcels has no manufacturer authority.
- **Fallback C — separate an explicitly methodological capacity-active benchmark from a deferred physical-kg scenario.** This makes the fewest unsupported physical claims and preserves a clean path back to kg if appropriate evidence becomes available.

`RECOMMENDED_FALLBACK = FALLBACK_C`

Fallback C does not itself freeze a capacity dimension or `Q`. A subsequent contract must decide how the methodological constraint is represented and labeled without implying physical payload validity.

No demand generation, mass generation, `q_i/Q/m` definition, routing revalidation, instance generation or optimization was performed.

`NEXT_EXECUTABLE_TASK = methodological capacity contract review`
