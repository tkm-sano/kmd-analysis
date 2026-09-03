# Formal network completion policy v17

Status: **normative, adopted 2026-09-03**

Decision: `DEC-P13-NETWORK-COMPLETION-HIERARCHICAL-HYBRID-001`

Registry: `reproducibility/config/traffic_simulation/network_completion_method_registry_v17.yml`

The keywords **MUST**, **MUST NOT**, **SHALL**, **SHALL NOT**, and **MAY** are normative.

## 1. Context and evidence

The Phase 13 model-selection artifacts are read-only research authority for this Decision. They compare 3,286 source-explicit or deterministic-derived lane labels with 22,624 Ways lacking lane evidence. Explicit and missing populations are not exchangeable: highway total variation is 0.785, directionality total variation is 0.447, and endpoint-degree standardized mean difference is 0.856.

The candidate hybrid's type-fallback stage produced approximately 49.7% exact accuracy and −0.600 prediction bias. The complete hybrid reached only 68.7% spatial accuracy, MAE 0.423, and bias −0.367. Local propagation performed better on explicit-domain spatial holdout (83.9%, MAE 0.203, bias −0.029) but covered only 13.6% there and has no missing-domain external validation. ExtraTrees at probability ≥0.8 reached 96.5% on a selective explicit-domain subset, while macro recall remained 0.25 and rare classes were not recovered. None of those results proves accuracy on missing Ways.

## 2. Decision and alternatives

The project SHALL use an **attribute-specific hierarchical hybrid with mandatory abstention and a separate simulation-only fallback layer**. A single universal imputer, unconditional local propagation, a highway-class mode, and SUMO or MATSim defaults are rejected as Formal completion policies. External fusion, local propagation, empirical models, and statistical/ML models remain candidates only behind their specified validation gates.

## 3. Formal definition

**Formal** means a model-ready value that is acceptable for research use, whose method validity was verified before use, and whose provenance is complete.

Formal is not limited to explicit source facts: normalized values, adopted deterministic derivations, validated external data, and validated inferred/model-derived values can be Formal. Formal is also not an arbitrary simulation fallback. A source assertion and a model-ready value MUST be represented separately; inferred values MUST NOT be written back or presented as source truth.

## 4. Three layers and data flow

1. **Structural** preserves source representation, topology, lineage, raw values, normalized state, and registered structural assumptions. It makes no claim that an assumption is research-valid.
2. **Formal** consumes Structural records and only methods currently allowed by the registry. It contains validated research-use values and a complete Formal-unresolved inventory.
3. **Simulation-ready** overlays Formal with separately labelled simulation-only defaults where an executable attribute is still absent.

The flow is `source → Structural → Formal → Simulation-ready`. Every transformation SHALL append provenance rather than replace upstream provenance. Simulation-only output SHALL point to the unresolved Formal record it overlays. Reverse flow, write-back to source, and promotion by copying a simulation value into Formal are prohibited.

## 5. Epistemic status and provenance

Formal records may use only `OBSERVED`, `NORMALIZED`, `DETERMINISTIC_DERIVED`, `EXTERNAL_DATA_DERIVED`, `VALIDATED_LOCAL_INFERRED`, or `VALIDATED_MODEL_DERIVED`. Simulation-only overlays may use only `TYPE_DEFAULTED`, `SIMULATION_DEFAULTED`, or `CONSERVATIVE_FALLBACK`.

Implementations SHALL store these in distinct fields such as `formal_epistemic_status` and `simulation_epistemic_status`. Compatibility mappings to the existing v17 `value_origin` are permitted, but a simulation-only class MUST NOT appear as a Formal origin. `model_assumed` remains non-Formal.

All values SHALL carry record and source identity, source snapshot/hash, attribute semantic kind, method/rule/model ID and version, Decision ID, input evidence IDs, applicable temporal and directional extent, output value/unit, epistemic status, and deterministic regeneration inputs. Model-derived values additionally require training-population and code hashes, features or their immutable hash, prediction distribution, calibrated confidence, applicability/OOD result, validation split and metrics, and abstention/sensitivity metadata.

## 6. Method boundary

The registry classifications are normative:

| Family | Status | Formal effect |
|---|---|---|
| Explicit source evidence | `FORMAL_ALLOWED_NOW` | `OBSERVED` |
| Lossless normalization | `FORMAL_ALLOWED_NOW` | `NORMALIZED` |
| Adopted deterministic derived rule | `FORMAL_ALLOWED_NOW` | `DETERMINISTIC_DERIVED` |
| External official data | `FORMAL_ALLOWED_AFTER_VALIDATION` | no value until exact linkage and validation pass |
| Same-corridor/local propagation | `FORMAL_ALLOWED_AFTER_VALIDATION` | no value until promotion |
| Empirical group model | `FORMAL_ALLOWED_AFTER_VALIDATION` | no value until promotion |
| Statistical/ML prediction for lanes or speed | `FORMAL_ALLOWED_AFTER_VALIDATION` | no value until promotion |
| Vehicle-specific access evidence | `FORMAL_ALLOWED_NOW` | `OBSERVED` under the adopted vehicle ontology |
| Deterministic OSM access semantics | `FORMAL_ALLOWED_NOW` | `DETERMINISTIC_DERIVED` |
| Validated policy-derived access | `FORMAL_ALLOWED_AFTER_VALIDATION` | no value until authority/scope validation and promotion |
| Road-type/highway-class/generic type default | `SIMULATION_ONLY` | never Formal evidence |
| SUMO typemap default | `SIMULATION_ONLY` | never Formal evidence |
| MATSim default | `SIMULATION_ONLY` | never Formal evidence |
| Conservative fallback | `SIMULATION_ONLY` | never Formal evidence |
| Governance fallback | `UNRESOLVED_RESEARCH_DECISION_REQUIRED` | route to Decision or unresolved; never invent a value |
| Fail-closed conflict policy | `FORMAL_ALLOWED_NOW` control | select only via adopted precedence, otherwise abstain |
| ML legal-access grant | `PROHIBITED` | none |
| Silent/unregistered inference or lower-tier override | `PROHIBITED` | none |

`FORMAL_ALLOWED_AFTER_VALIDATION` is not an allowlist entry for runtime Formal output. Promotion requires all gates plus a separate adopted promotion Decision and registration in the existing Formal evidence-method registry.

## 7. Resolution hierarchy by attribute

### 7.1 Lanes

Formal priority is:

`EXPLICIT → DETERMINISTIC_DERIVED → VALIDATED_EXTERNAL_DATA → VALIDATED_LOCAL_PROPAGATION → VALIDATED_EMPIRICAL_OR_ML → UNRESOLVED_FORMAL`

Simulation-only priority after Formal abstention is:

`TYPE_DEFAULT → SUMO/MATSim default → conservative lane fallback`

Total physical lanes, shared bidirectional lanes, directional lanes, and lane-vector semantics SHALL remain distinct. A lower stage MUST NOT override higher-stage evidence or hide a conflict.

### 7.2 Speed

Formal priority is:

`explicit maxspeed → normalized value → adopted deterministic rule → validated external data → validated empirical/model value → UNRESOLVED_FORMAL`

Simulation-only priority is `road-type default → SUMO/MATSim default → conservative fallback`. Posted/legal `maxspeed`, free-flow speed, and average operating speed are different semantic targets. A predicted free-flow or average speed MUST NOT acquire legal/posted `maxspeed` provenance.

### 7.3 Permission/access

Formal priority is:

`explicit access → vehicle-specific evidence through adopted specificity semantics → deterministic OSM semantics → validated policy/external authority → UNRESOLVED_FORMAL`

The registry represents the middle deterministic stages with the adopted deterministic-rule method. Simulation defaults are a separate overlay. Statistical or ML inference MAY prioritize manual review but MUST NOT grant legal access. Ambiguous conditional syntax, missing context, and incomparable specificity conflicts SHALL abstain.

## 8. Validation gates and thresholds

Every local, empirical, or ML promotion SHALL pass all of the following on immutable data: source-Way train/test separation; spatial/corridor holdout; leakage audit; explicit-domain validation; independently labelled missing-domain validation; external validation; accuracy, MAE, and signed bias; class/stratum support; calibration and confidence; selective-risk/coverage reporting; abstention support; complete provenance; deterministic regeneration; and network/research sensitivity analysis.

Lane promotion uses the following screening envelope on a common eligible, independently labelled missing-domain population, with 95% confidence intervals:

- exact-accuracy lower bound SHALL exceed 0.694454, the strongest observed type-default accuracy comparator;
- MAE upper bound SHALL be below 0.401196, the best observed type-default MAE comparator;
- absolute signed-bias upper bound SHALL be below 0.141693, the least-biased naive group comparator;
- coverage has no fixed minimum because abstention is required; coverage and selective risk SHALL be reported together;
- classes without adequate prospective support SHALL remain unresolved, and dominant two-lane prediction SHALL NOT substitute for rare-class evidence.

These are minimum screening floors derived from the current benchmark, not sufficient evidence and not a universal “95% accuracy” rule. Final acceptance thresholds SHALL be preregistered per attribute semantic target and deployment stratum, and SHALL also reflect downstream research sensitivity. Speed thresholds require units and separate legal versus simulation-speed targets. Permission validation SHALL be rule/authority based; predictive accuracy cannot authorize legal access.

Confidence cutoffs SHALL be selected and calibrated on held-out missing-domain labels. The explicit-domain ExtraTrees ≥0.8 result is not a valid cutoff by itself.

## 9. Missing-domain requirement

Formal promotion requires both explicit-domain validation and missing-domain validation. Cross-validation on explicit-tagged Ways estimates donor-domain fit only. If missing-domain ground truth is insufficient, the method SHALL remain `FORMAL_ALLOWED_AFTER_VALIDATION`, irrespective of explicit-domain accuracy or model confidence.

## 10. Abstention and conflicts

A method SHALL abstain on missing or failed domain validation, OOD input, insufficient class/stratum support, low or uncalibrated confidence, leakage, lineage/date/extent/direction/semantic mismatch, unsupported syntax, or conflict. Conflicts SHALL stop unless an adopted deterministic precedence/specificity rule selects an already evidenced value. Voting, silent overwrite, and fallback-based conflict concealment are prohibited.

## 11. Blocker semantics

A **Formal blocker** is an attribute for which Formal policy cannot establish a research-use value. A **simulation readiness blocker** is an attribute still lacking an executable value after applicable Formal resolution and registered simulation-only fallback. Therefore `Formal blocker > 0` with `Simulation-ready blocker = 0` is valid and expected.

## 12. Network completion semantics

`FORMAL_RESEARCH_READY` requires complete Formal provenance, a complete Formal-unresolved inventory, no silent inference, and satisfaction of every accepted validation gate. It does not require zero Formal blockers.

`SIMULATION_NETWORK_READY` additionally requires an executable value for every simulation-required attribute, complete provenance for every Formal or simulation-only value, SUMO materialization PASS, connectivity PASS, and delivery routeability PASS. It requires zero simulation readiness blockers but may retain Formal blockers.

Neither state is claimed by adoption of this Decision alone.

## 13. Rollback

A promoted method SHALL be deactivated when its validation metric, calibration, class-specific error, signed bias, source/model lineage, determinism, provenance, or sensitivity result exits its approved envelope. Affected Formal records SHALL return to `UNRESOLVED_FORMAL`. Simulation scenarios may remain only as explicitly labelled simulation-only outputs. Rollback SHALL NOT alter source truth or historical v17 artifacts.

## 14. Current scope and next dependency

This Decision changes policy, specification, and registry only. It does not reduce lane, speed, or permission blockers; run the full population; build SUMO; promote a type default; or promote an unvalidated local/empirical/ML model.

The dependency order is: **(1) missing-domain external validation → (2) Formal model promotion Decision/registration → (3) blocker-reduction implementation → (4) simulation-ready fallback implementation**. A simulation-only fallback can be researched independently, but its production implementation SHALL follow Formal promotion/accounting so the overlay cannot contaminate Formal provenance.
