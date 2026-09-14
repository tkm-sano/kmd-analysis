# R24 demand conversion specification

Status: `PARCEL_PROXY_TRACEABLE; PHYSICAL_KG_CONVERSION_BLOCKED`

## Existing lineage

The customer population is the immutable current artifact `building_delivery_stops_scoped.csv`: 39,956 unique building stops. Its upstream expected demand is `household_daily_expected_demand.csv`, joined to `household_building_assignment_scoped.csv` on `household_id`, filtered to `mapping_status in {matched, matched_cross_boundary}`, and summed by `building_id`. The existing one-day realized field in the stop file is `parcel_equivalent`; it is a Poisson realization produced on 2026-01-01 with seed 20260829 and is not an observed delivery record.

The upstream mesh baseline is independently specified by `baseline_demand.yml` and `prepare_baseline_demand.py`:

```text
q_base = annual_national_parcel_count / national_population / 365
       = 5,031,470,000 / 123,802,000 / 365
       = 0.111345933951539499... parcel-equivalent / person / day

N_m = largest_remainder(736,652 * area_weighted_2020_population_m /
                        sum_m(area_weighted_2020_population_m))
E_m = N_m * q_base * target_days
```

At customer level, the reproducible expected proxy is:

```text
N_i^(parcel/day) = sum_{h assigned to building i}
                   expected_parcel_equivalent_per_day_h
```

This reconstruction is deterministic and uses no new random draw. For the 39,956 active stops, the sum is 61,793.0020700188 parcel-equivalent/day. The realized current stop file totals 81,859 parcel-equivalent on its single evaluation date; this difference is expected from conditioning on active realized stops and the Poisson realization and must not be silently treated as a physical observation.

## Physical conversion gate

The requested conversion would be:

```text
q_i [kg/customer/day] = N_i^(parcel/day) * E[W_parcel] [kg/parcel]
```

or, with a justified distribution, `q_i = sum_r W_ir`. No authorized `E[W_parcel]`, parcel-level weight distribution, or category-conditioned weight distribution was found. Size classes and service maximum weights are not converted to mass. Therefore `q_kg_customer_day` is intentionally blank in `customer_demand_kg.csv`; no assumed 5 kg or other value is used.

`STOP_PARCEL_WEIGHT_AUTHORITY_INSUFFICIENT` remains open. To resolve it, add a source with a defined parcel universe matching the demand proxy and either parcel-level weights or a documented mean/weighted distribution, plus source file hash and a fixed join/weighting rule.

Sampling/realization policy for the blocked physical version is not frozen. Once weight authority exists, deterministic expected mass is the primary candidate; distributional realizations are a separate protocol with fixed RNG/version/realization ID.
