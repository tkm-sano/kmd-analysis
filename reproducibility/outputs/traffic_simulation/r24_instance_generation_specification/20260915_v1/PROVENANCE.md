# Provenance Contract

Every generated record must support this reverse chain:

\[
Instance\rightarrow C_{eligible}\rightarrow Routing\ Proxy\rightarrow Synthetic\ Demand.
\]

The execution must preserve:

- specification protocol ID and SHA-256 of every file in this package;
- source `C_ELIGIBLE_MANIFEST.csv` path and SHA-256 `245aad97ea49f7676dcebd414b46eb364d64e9d0fbeb4defa0c8e8b90604ca5c`;
- source eligibility row ID, stable building ID, routing proxy/edge/offset, duplicate group, q_i, source horizon, and source provenance reference;
- seed material, full seed digest, uint64 rendering, sampling/structural method, and canonical input ordering;
- accepted run_3 graph ID/hash `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2` and Routing Baseline version;
- repository start SHA, generator code SHA, execution commit SHA, runtime/tool versions, command/config, UTC timestamps, and host-independent output ordering rules;
- individual output hashes, q-vector hash, OD hash, packing certificate hash, and suite-manifest/output-root hash.

Source demand values and customer identities are referenced and conserved, never regenerated. Run_2 proxy lineage is retained, but all selected-instance costs are newly computed on run_3. Timestamp, filesystem order, process count, and solver results must have no effect on customer selection.

For this freeze task: branch `main`; start SHA `41fa3f111e8798c1d4cd5ca71f6938d9f2353a5b`; scientific experiment `NONE`; instance generation `NONE`; optimization `NONE`. The committed end SHA is recorded by Git and reported in the task handoff because a file cannot contain the hash of the commit that contains itself without circularity.
