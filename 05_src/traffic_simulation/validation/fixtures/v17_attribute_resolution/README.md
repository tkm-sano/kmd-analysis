# v17 Attribute Resolution Fixtures and Oracles

This directory is the fixed Phase 2 specification-derived collection for
`ota_ward_attribute_resolution_policy_v17`.

- `inputs.json` contains 57 input cases without expected outputs.
- `oracle.json` contains the corresponding production-independent expectations.
- `manifest.yml` binds the specification, fixture catalog, and oracle catalog
  by SHA-256 and records coverage and independence review.

The oracle was authored from the normative specification. No production v17
Resolver code or production output was used to calculate or adjust an expected
value. A future runner may read `inputs.json`; it must never pass `oracle.json`
to production code or rewrite the oracle from observed output.

Coverage includes every required Section 19 case family, all 30 registered
stop codes, and five metamorphic families: independent-record order,
determinism, source immutability, direction symmetry, and JSON canonicalization.

Validate the fixed collection with:

```bash
PYTHONPATH=05_src python -m \
  traffic_simulation.network.validate_v17_fixture_oracle
```

Phase 2 fixation does not mean production implementation or runtime acceptance
has passed. Production comparison begins in Phase 3 and later phases.
