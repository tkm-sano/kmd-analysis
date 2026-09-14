# Integrity review

Benchmark protocol and runner were committed before execution. Baseline and V4 each ran in a fresh process with the same input, source modules, environment and CPU affinity wrapper. Run start/end records and result hashes are retained. Existing scientific, audit and B2 artifacts were not modified. New benchmark files are independently hash-sealed. Final recommendation is `R23_CLOSED_WITH_DOCUMENTED_LIMITATIONS`; until explicit status mutation, operational status remains R23_OPEN/R24_BLOCKED.

Final axes: `CODE_AUDIT_PASS_WITH_LIMITATIONS`; `RESULT_REPRODUCED_WITH_LIMITATIONS`.
