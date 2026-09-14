# Remaining MAJOR findings precheck

| finding_id | description | affected_scope | why_major | closure condition | resolvable here? | required evidence |
|---|---|---|---|---|---|---|
| F02 | Historical rank02/03 executions used dirty/uncommitted source and incomplete attestation | historical n5 rank02/03 lineage | exact historical execution cannot be independently attested | complete new runs or immutable historical attestation | partially | new clean run manifests plus explicit historical limitation |
| F03 | Historical compact results omit full state/trace needed to regenerate the complete metric path | all historical n5 compact records | full numerical trajectory is not reproducible from retained bytes | complete payload and independent reconstruction | partially | new complete clean-run records and hash-bound traces |

The n=5 benchmark cannot automatically erase historical provenance defects.

