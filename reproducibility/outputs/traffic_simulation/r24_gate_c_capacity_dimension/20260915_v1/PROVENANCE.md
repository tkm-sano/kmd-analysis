# Provenance and execution boundary

Date: 2026-09-15 JST  
Branch: `main`  
Start SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b`  
End SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b` (no commit)

## Repository evidence inspected

- Gate B decision `b27cf942...` and Gate C handoff `88c6ad52...`.
- Gate A minimal abstraction `3585e574...`.
- Planning-horizon decision `cfc27078...`.
- End-to-end authority `6adf24a3...`.
- R24 kg design audit `95101a9b...`.
- Parcel-weight decision `59c9fe0a...` and evidence CSV `cd3256b0...`.
- Demand/capacity authority v2 `3b5dce47...` and weight-source CSV `12d9cb5c...`.
- Gate B vehicle inventory `bdb67611...`.
- `daily_requests.csv` `4bb78cf2...` and `building_delivery_stops_scoped.csv` `fcfca5cb...`.

## External evidence used

Bounded web review on 2026-09-15 checked Japanese government, research and industry searches for B2C parcel weight/size and vehicle parcel-count capacity. No newly found source met the primary-authority conditions. Supporting/rejected evidence retained:

- MLIT domestic air-cargo survey reports: `https://www.mlit.go.jp/statistics/details/content/002016456.pdf` and historical reports, actual aggregate weight/count but air-cargo and B2B/B2C-mixed population.
- MLIT parcel/service and statistics pages: counts or service limits, not a matching parcel-mass distribution.
- J-STAGE roll-box-pallet measurement: `https://www.jstage.jst.go.jp/article/josh/19/1/19_JOSH-2025-0010-CHO/_html/-char/ja`, cage-level rather than parcel-level denominator.
- MLIT logistics standardization: `https://www.mlit.go.jp/seisakutokatsu/freight/seisakutokatsu_freight_tk1_000200.html`, pallet/unit-load scope rather than residential loose-parcel kei-van capacity.
- Existing foreign peer-reviewed/industry sources remain sensitivity-only because population transfer is unsupported.

This was not an exhaustive systematic review, and does not claim no suitable source exists. It establishes that no accessible reviewed authority is presently sufficient.

## Execution record

Tracked changes at start/end: none. This output directory is ignored and uncommitted. Scientific/data mutation: **NONE**. Demand generation: **NONE**. Parcel mass/volume/LU generation: **NONE**. `q_i/Q/m` freeze: **NONE**. Eligible population/instance generation: **NONE**. Optimization/MILP/QUBO/QAOA/Aer: **NONE**. Output hashes are in `SHA256SUMS.txt`, excluding the manifest itself.
