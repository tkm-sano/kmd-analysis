# Requirements Traceability

## Registry Rule

The machine-readable authority is `requirements_traceability.yml`. Every normative requirement in specifications 00-06 MUST have exactly one registry entry, one or more test IDs, a fixture class and a current implementation state. Test IDs may be `specified_not_implemented`; this blocks the relevant readiness gate but does not make the specification ambiguous.

## Coverage Summary

| Prefix | Requirements | Test family | Fixture specification | Current implementation |
|---|---:|---|---|---|
| `SIM-REQ` | 8 | `SIM-TST` | research comparison fixtures | specified, downstream pending |
| `ARC-REQ` | 6 | `ARC-TST` | config/manifest state fixtures | partial |
| `RS-REQ` | 13 | `RS-TST` | resolver XML/JSON fixtures | v14 artifact implemented; registered extract pending |
| `PM-REQ` | 11 | `PM-TST` | materializer plain-XML fixtures | not implemented |
| `TLS-REQ` | 10 | `TLS-TST` | reviewed TLS fixtures | not implemented |
| `BLD-REQ` | 11 | `BLD-TST` | pinned final-build fixtures | not implemented |
| `PA-REQ` | 11 | `PA-TST` | post-build audit fixtures | not implemented |

## Evidence Chain

```text
requirement ID
  -> traceability registry entry
  -> test ID
  -> fixture ID and hashes
  -> exact execution evidence
  -> result artifact
  -> readiness requirement state
```

The validator MUST reject duplicate IDs, missing test mappings, unknown failure codes and a requirement marked implemented without an implemented test. Runtime pass status is recorded separately from implementation status.
