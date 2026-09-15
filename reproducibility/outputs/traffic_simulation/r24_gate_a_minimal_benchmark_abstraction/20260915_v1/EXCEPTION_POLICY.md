# Exception policy

Every exception is detected, counted and written to a versioned exception ledger with customer/request IDs, parcel-equivalents, rule code, evidence, disposition and reason. No silent drop or automatic co-location merge is permitted.

| exception | detection | current count | disposition | reason |
|---|---|---:|---|---|
| no stable building ID | null/non-assigned building after source join | 347 source records / 387 parcel-equivalents | exclude from customer candidates; retain source ledger | no stable customer identity (`unsupported_housing_type=321`, `no_candidate=26`) |
| no routing mapping | missing mapping relation/edge/proxy fields | 0 of 39,956 historical candidates | exclude from eligible; retain exception | routing endpoint undefined |
| invalid geometry | null/non-finite/out-of-range coordinate, CRS mismatch or inconsistent joined coordinate | 0 of 39,956 historical candidates | exclude from eligible | geographic/routing input invalid |
| depot unreachable | either directed depot reachability false | not evaluated for full population | exclude from eligible when detected | closed depot tour impossible |
| Routing Baseline incompatible | mapping network/hash/access profile differs from accepted baseline | 39,956 pending current-baseline evaluation, not counted as confirmed failures | candidate retained; never mark eligible until resolved | R03 all-population map is run_2; accepted run_3 routing is fixture-scoped |
| duplicate proxy location/node | duplicate accepted proxy coordinate or routing node; edge duplication also reported | historical edge: 28,294 members in shared groups; exact source coordinate: 0 | retain as separate customers and flag | co-location is not customer/event identity; instance validator checks zero-cost effects |
| other mapping inconsistency | ID cardinality mismatch, conflicting edge/node/version, coordinate mismatch, broken child lineage | 0 in audited saved building-to-R03 join | exclude from eligible pending correction | provenance or topology is ambiguous |

`pending/not evaluated` is not silently recoded as an exclusion or a pass. Counts are recomputed for each mapping/baseline version.

