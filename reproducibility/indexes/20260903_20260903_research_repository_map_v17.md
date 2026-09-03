# Research Repository Map v17

Document ID: `DOC-RESEARCH-REPOSITORY-MAP-V17`
Role: `CURRENT_REFERENCE`
Lifecycle: `CURRENT`
Created: `2026-09-03`
Last Updated: `2026-09-03`
Current Authority: `reproducibility/indexes/research_repository_index_v17.yml`

Start with the [Research Overview and Roadmap v17](../../20260903_20260903_RESEARCH_OVERVIEW.md) for the research question, full Stage 1–11 plan, milestones, gates, and current position. Use [`./research`](../../docs/20260903_20260903_research_cli.md) as the unified execution and validation entry point; `./research commands` is the command index.

This map is a navigation document, not a second authority. The canonical network pointer is [current_network_completion_authority_v17.yml](../config/traffic_simulation/current_network_completion_authority_v17.yml); the canonical network-completion pipeline is [network_completion_pipeline_v17.yml](../config/traffic_simulation/network_completion_pipeline_v17.yml).

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
                                          └─ Research Overview
                                              └─ Routing Baseline (next)
                                                  └─ Common Instance / Optimization / Evaluation / Interpretation (future)
```

Current traceability:

| Role | Current pointer |
|---|---|
| Research overview / roadmap | `20260903_20260903_RESEARCH_OVERVIEW.md`; stable entry: `RESEARCH_OVERVIEW.md` |
| Research execution CLI | `research`; reference: `docs/20260903_20260903_research_cli.md` |
| Decision | `DEC-P13-FORMAL-COMPLETION-THREE-TIER-001` |
| Normative specification | `05_src/traffic_simulation/specifications/20260903_20260903_formal_completion_three_tier_policy_v17.md` |
| Pipeline specification | `05_src/traffic_simulation/specifications/20260903_20260903_network_completion_pipeline_v17.md` |
| Registry / schema | `reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml` and `schemas/formal_completion_*three_tier*` |
| Accepted run | `.../phase13_20260903_three_tier_completion/run_2` |
| Accepted network | `three_tier.net.xml`, SHA `4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f` |
| Acceptance | `run_2/network_acceptance.json` |
| Portal | `reproducibility/config/research_portal/three_tier_network_run2_status.yml` |

Normative documents contain policy and contracts only. Investigations, diagnostics, reports, and generated outputs remain non-normative and are referenced by indexes or manifests. Historical and superseded artifacts are retained and never promoted by filename alone.
