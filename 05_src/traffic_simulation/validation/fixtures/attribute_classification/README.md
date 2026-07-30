# Attribute Classification Production Fixtures

This directory contains the specification-derived fixture collection for the
implemented Predicate Generator and the future Classifier and Resolver. The
collection was authored before those production components existed. No
production transformation code generated the checked-in oracle. The Predicate
Generator now exists; independent human acceptance and pinned
Classifier-Resolver execution remain pending.

## Structure

- `inputs.json` contains normalized, machine-readable case inputs.
- `oracles.json` contains expected classification-resolution results.
- `cases/*.fixture.json` binds one input case and oracle by SHA-256.
- `manifest.json` fixes case membership and required coverage.
- `repeat/` contains the two pinned outputs for the repeat case.
- `review.json` records the separate human-acceptance state.

The manifest pins the input and oracle catalogues. `review.json` then records
expected and observed hashes for the manifest, inputs, oracles and source
specification. This direction avoids a manifest-review hash cycle.

The fixture descriptors conform to
`attribute_classification_fixture.schema.json`. Inputs and oracles are
separate files so a future fixture runner can pass the input to production
code without using the oracle as an input.

## Coverage

The collection includes:

- `AC001-NEG-001` through `AC010-NEG-001`;
- lane levels `L0` through `L3`;
- speed levels `S0` through `S3`;
- excluded and topology-support ways;
- permitted and prohibited structural placeholders;
- evidence applicability and conflict;
- incomplete review and invalid state combinations;
- structural-to-formal reclassification;
- post-critical promotion and dependent-artifact invalidation;
- unsupported conditional speed semantics; and
- deterministic byte-equal repeat output.

## Independence And Acceptance

`oracle.independently_authored=true` means that the oracle was authored from
the normative specification rather than copied from production output. It
does not mean that independent human review is complete. The research owner
waived independent human review on 2026-07-30. `review.json` therefore keeps
`acceptance_allowed=false` and records the waiver; Classifier and Resolver
development proceeds using the pinned oracle, automated integrity checks and
semantic validation. Research reporting must not describe the fixture as
independently human accepted.

Production code MUST NOT update `oracles.json`. A changed specification or
fixture decision requires a reviewed fixture revision and refreshed hashes;
silently regenerating the oracle from classifier output is prohibited.

## Validation

Run the pinned repository validation with:

```bash
docker compose run --rm -T analysis \
  python -m pytest \
  05_src/traffic_simulation/validation/test_attribute_classification_production_fixtures.py \
  -q
```
