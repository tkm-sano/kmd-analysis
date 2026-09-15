# Eligible population rules

## Frozen predicate

Let `S` be the frozen 2026-01-01 source snapshot. A building customer `i` is eligible iff:

`i in C_eligible` iff all of the following are true:

1. every aggregated child is a member of `S`;
2. aggregate realized demand is a positive integer in parcel-equivalents;
3. `source_building_id` is non-null, stable and unique at customer level;
4. source coordinates are finite, in the declared CRS/domain, and consistent across joined files;
5. a versioned routing mapping is present and accepted for the current Routing Baseline and required access profile;
6. directed reachability `DEP_006 -> i` and `i -> DEP_006` is true on that same accepted baseline;
7. no exclusion-class mapping inconsistency remains unresolved.

For an actual generated instance, complete directed reachability for every ordered pair in `{DEP_006} union C_instance` is an additional instance-level requirement under the canonical Routing Baseline.

## Verification status from saved data

| condition | current verification |
|---|---|
| 2026-01-01 source membership | PASS: 73,547/73,547 records |
| positive realized demand | PASS: 73,547 records; building sums positive |
| stable building ID | PASS for 73,200 records / 39,956 buildings; 347 source records are exceptions |
| generic saved road mapping | PASS for 39,956 candidates on historical R03 run_2 |
| valid source geometry | PASS for 39,956 candidates |
| current Routing Baseline compatibility | NOT_EVALUATED for full population; run_3 acceptance is fixture-scoped |
| directed `DEP_006 <-> i` reachability | NOT_EVALUATED for full population |

## Freeze consequence

The construction policy is frozen, but `eligible=true` must not be assigned while a required field is `NOT_EVALUATED`. The saved data safely support a 39,956-row candidate frame and its summary. They do not safely support a final `C_eligible` manifest today. Gate B may determine the required vehicle/access profile; subsequent routing validation applies the frozen predicate without changing customer semantics.

