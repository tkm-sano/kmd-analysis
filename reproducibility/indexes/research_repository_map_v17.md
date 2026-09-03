# Research Repository Map v17

This map is a navigation document, not a second authority. The canonical pointer is [current_network_completion_authority_v17.yml](../config/traffic_simulation/current_network_completion_authority_v17.yml); the canonical pipeline is [network_completion_pipeline_v17.yml](../config/traffic_simulation/network_completion_pipeline_v17.yml).

```text
Conceptual Model
  └─ Decision
      └─ Specification
          └─ Registry / Schema
              └─ Implementation
                  └─ Validation
                      └─ Baseline / Run
                          └─ SUMO Network
                              └─ Mapping
                                  └─ Acceptance
                                      └─ Portal
                                          └─ Routing (next)
                                              └─ Optimization (future)
```

Current traceability:

| Role | Current pointer |
|---|---|
| Decision | `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001` |
| Normative specification | `05_src/traffic_simulation/specifications/15_formal_completion_three_tier_policy_v17.md` |
| Pipeline specification | `05_src/traffic_simulation/specifications/16_network_completion_pipeline_v17.md` |
| Registry / schema | `reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml` and `schemas/formal_completion_*three_tier*` |
| Accepted run | `.../phase13_20260903_three_tier_completion/run_2` |
| Accepted network | `three_tier.net.xml`, SHA `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| Acceptance | `run_2/network_acceptance.json` |
| Portal | `reproducibility/config/research_portal/three_tier_network_run2_status.yml` |

Normative documents contain policy and contracts only. Investigations, diagnostics, reports, and generated outputs remain non-normative and are referenced by indexes or manifests. Historical and superseded artifacts are retained and never promoted by filename alone.
