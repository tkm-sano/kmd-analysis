# Eligible population dependencies after horizon freeze

## Required to define the candidate/eligible frame

1. Membership in `R24-SOURCE-DAY-2026-01-01-v1`.
2. Positive realized synthetic demand with stable request/building lineage.
3. Stable destination/building and routing-proxy identifiers.
4. Valid coordinate/CRS and an existing road-mapping relation with method/network hash.
5. An accepted `ROUTING_PROXY_STOP` interpretation, including limitations and missing-access reason.
6. Versioned inclusion/exclusion and row/content conservation rules.
7. Depot reachability status for routing eligibility; unresolved/unreachable records retained as exceptions, not silently dropped.

Vehicle-class-specific legality and final OD compatibility remain downstream B/D validation dependencies. If they remove records, version the eligible frame and review the effect; do not reopen the synthetic-date source horizon unless its records/date change.

## Not required for source-horizon freeze

Observed entrance, actual service-event identity, parcel mass/volume, vehicle class/capacity and q/Q/m. These may be necessary for stronger operational claims or concrete instances, but making them prerequisites for the temporal source boundary would conflate stages.

The current 39,956 mapped positive-demand buildings are reconstructable candidates only. No eligible manifest is frozen here.
