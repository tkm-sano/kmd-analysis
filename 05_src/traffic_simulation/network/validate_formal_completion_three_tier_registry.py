from __future__ import annotations
import json
from pathlib import Path
import yaml, jsonschema
from traffic_simulation.paths import REPOSITORY_ROOT
ROOT=REPOSITORY_ROOT
REG=ROOT/"reproducibility/config/traffic_simulation/formal_completion_three_tier_registry_v17.yml"
DEC=ROOT/"reproducibility/config/traffic_simulation/decisions/phase13_formal_completion_three_tier_v1.yml"
SCHEMA=ROOT/"reproducibility/config/traffic_simulation/schemas/formal_completion_three_tier_v17.schema.json"
class ThreeTierRegistryError(ValueError): pass
def validate_registry()->dict:
 r=yaml.safe_load(REG.read_text()); d=yaml.safe_load(DEC.read_text()); s=json.loads(SCHEMA.read_text())
 jsonschema.Draft202012Validator(s,format_checker=jsonschema.FormatChecker()).validate({k:r[k] for k in ["schema_version","decision_id","status","tiers","confidence_levels","record_required_fields","blocker_definition","historical_baseline_policy"]})
 if r["decision_id"]!=d["decision_id"] or d["status"]!="adopted": raise ThreeTierRegistryError("Decision mismatch")
 if r["supersedes"]!="DEC-P13-NETWORK-COMPLETION-HIERARCHICAL-HYBRID-001": raise ThreeTierRegistryError("supersedes mismatch")
 if set(r["tiers"])!={"DIRECT","INFERRED","FALLBACK"}: raise ThreeTierRegistryError("tier set mismatch")
 if set(r["confidence_levels"])!={"HIGH","MEDIUM","LOW","FALLBACK"}: raise ThreeTierRegistryError("confidence set mismatch")
 if set(r["record_required_fields"])!={"final_value","resolution_tier","method_id","method_version","confidence","source_evidence","source_identity","assumption_id","provenance","original_missing_or_blocker_state"}: raise ThreeTierRegistryError("record contract mismatch")
 return {"three_tier_registry":"passed","decision_id":r["decision_id"],"superseded_decision":r["supersedes"]}
if __name__=="__main__": print(json.dumps(validate_registry(),sort_keys=True))
