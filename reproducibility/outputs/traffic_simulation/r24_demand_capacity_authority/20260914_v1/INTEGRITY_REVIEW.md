# Integrity review

- Starting HEAD: `82f92faead19dedd30eb22653d4a55c1bc4c53e9`
- Existing R23 closure and scientific artifacts: not modified.
- Existing population: 39,956 rows, unique `building_id`: 39,956.
- Customer kg file: 39,956 data rows; every `q_kg_customer_day` is blank by design because parcel-weight authority is insufficient.
- `Q_kg=2000` is present as inherited profile capacity on every row, with the fixed-profile caveat.
- No random draw, routing recomputation, QUBO construction, optimizer, QAOA, Aer, or statevector execution occurred.
- Ota kg/day, capacity-only lower bound, and capacity pressure were not computed and are recorded as null/blank rather than inferred.
- Generated artifacts are covered by `SHA256SUMS`; source hashes used by the builder are in `PROVENANCE.md`.
