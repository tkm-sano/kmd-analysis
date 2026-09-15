# Problem Size Definition

## Frozen sets

- `R24_QUANTUM_COMPARABLE_N = {2,3,4}`
- `R24_CLASSICAL_EXTENSION_N = {5,8,10,15,20}`
- `R24_PRIMARY_N = {2,3,4,5,8,10,15,20}`

`n` is the number of customers in a base computational benchmark instance. The depot is excluded. It is not a statistical sample-size claim, route-stop estimate, dispatch-wave size, or evidence about an Ota carrier.

## Basis

R23 covered n=2–5 using a customer-position encoding with n² logical variables: 4, 9, 16, and 25 before any multi-vehicle/capacity variables or auxiliaries. R24 adds assignment to multiple vehicles, capacity representation, and depot-tour structure, so its eventual QUBO cannot be assumed to retain the R23 count and will be at least materially more demanding for comparable n. Exact statevector cost grows as `2^L` in the final logical-qubit count `L`.

Accordingly, n=2–4 is the prespecified set allowed to proceed to later QUBO/resource-gate evaluation; inclusion does not guarantee QAOA authorization. n=5 preserves the upper R23 size for classical cross-layer comparison. n=8,10,15,20 provide a finite classical/MILP scaling extension while keeping exact capacity preflight and full ordered-pair routing tractable. No R24 QUBO formulation, logical-variable estimate, QAOA run, or MILP run is performed here.

The sets may not be altered after observing generation, packing, routing, or solver results. Any future larger-size study is a separately versioned extension, not a silent change to this suite.
