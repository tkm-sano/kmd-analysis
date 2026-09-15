# Provenance and execution record

Date: 2026-09-15 JST  
Branch: `main`  
Start SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b`  
End SHA: `5bb6829ced63195dcbd3ce5785c8e66331994b6b` (no commit)

## Fixed inputs

| Artifact | SHA-256 |
|---|---|
| run_3 accepted network | `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2` |
| run_2 source network | `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| full candidate mapping CSV | `226ff0d1ae91f08ea872cd99a3da5092fee19cf99259f7da81db79135762df7a` |
| building demand aggregate | `fcfca5cb87bc482f1d98306c98823773e872f200c58ecb9090aa12985e3e80e0` |
| current network authority | `29ee5fe979c85eb1d11b0f5a55f33782b7b5b08fcf09b48d2fad3e47c0ae33ee` |
| Routing Baseline canonical specification | `9eb9966d922a0164d94cd0e4c1c1b805d172bb429c1efcd93d50d721d67f1260` |
| DEP_006 definition | `fd38e10752236652b825e2e25665b4189bcf4cb57fd92918a315fd3b41018822` |
| current R13 routing runner inspected | `13c89a026363256f60900488b9c77808a207f2b4d9546d4158d266ea50d10f54` |

Routing, mapping, Gate A/B/C/D and vehicle evidence artifacts inspected are described in the audit documents. SUMO 1.24.0 `sumolib` loaded the two fixed networks. No external source was added.

## Computation

`build_revalidation.py` verifies input hashes, exact run_2/run_3 acceptance lineage, IDs, nodes, permissions, coordinates and proxy transfer. It builds a connection-aware directed graph over `delivery` edges, computes SCCs and depot forward/reverse reachability, cross-checks the accepted R13 node-edge reachability semantics, joins frozen `q_i`, flags duplicate edge-offset proxies and writes the population ledger/summaries.

Candidates checked: 39,956. All-pairs OD: `NONE`. Manifest SHA is recorded in `SHA256SUMS.txt`.

Tracked changes at start/end: `NONE`; this output directory is gitignored and uncommitted. Scientific mutation is limited to the new routing eligibility decision and manifest. Existing network, mapping, depot, demand, capacity and vehicle artifacts were not modified.

Demand generation: `NONE`. `q_i/Q/rho/m` modification: `NONE`. Instance generation: `NONE`. Routing cost/OD generation: `NONE`. MILP/QUBO/QAOA/Aer/optimizer/R23 rerun: `NONE`.
