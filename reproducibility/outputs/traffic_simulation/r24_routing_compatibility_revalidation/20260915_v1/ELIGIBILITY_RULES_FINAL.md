# Final routing eligibility rules

The final set is:

\[
C_{eligible}=\{i\mid positive\ demand \land stable\ building\ ID \land valid\ geometry
\land valid\ run3\ edge\text{-}offset\ proxy \land delivery\ compatible
\land edge(i)\in SCC(edge(DEP\_006))\}.
\]

Required row-level conditions:

1. source horizon equals `2026-01-01`;
2. frozen building `q_i` is a positive integer;
3. stable `stop_id` and `building_id` are present and unique as identities;
4. longitude/latitude are finite and valid;
5. run_2 mapping source/hash is exact;
6. mapped edge ID exists in run_3 and stored from/to nodes match;
7. run_2 proxy point exists on the run_3 edge shape;
8. mapped edge permits SUMO `delivery`;
9. `DEP_006 -> i` and `i -> DEP_006` are true;
10. candidate edge belongs to the depot delivery SCC.

`C_ELIGIBLE_MANIFEST.csv` contains all assessed candidate rows for auditability. The set itself is exactly the 39,930 rows where `eligibility_status=ELIGIBLE`. Excluded rows retain one mutually exclusive primary reason.

The endpoint is edge-offset based. `routing_node_id` is intentionally empty; substituting a single node would change offset semantics. The manifest instead supplies `routing_edge_id`, from/to node IDs and current offset.

Duplicate proxy locations do not merge building identities. Downstream generators filter eligible rows, preserve stable IDs, and perform instance-level duplicate/zero-arc checks.
