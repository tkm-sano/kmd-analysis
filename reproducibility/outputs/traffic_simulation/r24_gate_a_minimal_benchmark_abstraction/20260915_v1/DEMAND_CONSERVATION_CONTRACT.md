# Demand conservation contract

No new demand generation is authorized. Conservation is checked from immutable saved snapshots at three boundaries.

## Ledger equations

Source-to-mapping:

`73,547 records = 73,200 assigned records + 347 excluded records`

`82,246 parcel-equivalents = 81,859 assigned + 387 excluded`

Mapping-to-building aggregation:

`sum(customer.request_count) = 73,200`

`sum(customer.realized_parcel_equivalent) = 81,859`

`count(distinct customer) = count(distinct stable building_id) = 39,956`

Eligibility:

For each versioned decision, building-level candidate demand must equal eligible demand plus excluded demand plus pending/not-evaluated demand. Child-record counts and parcel-equivalents must be reported separately so aggregation cannot be mistaken for deletion.

## Required audit fields

Each stage records snapshot/hash, source-record count, distinct building count where applicable, parcel-equivalent total, exclusion/pending reason, affected source-record count, affected building count and affected parcel-equivalents. Reasons are mutually exclusive at the primary-disposition level; secondary flags such as duplicate proxy are non-excluding and may overlap.

## Current result

Saved source-to-building conservation passes exactly. All 39,956 building candidates / 81,859 parcel-equivalents are pending current Routing Baseline and depot-reachability evaluation, so no final eligible total is asserted. The generator provenance gap limits regeneration only and does not invalidate byte-level conservation of the saved snapshot.

