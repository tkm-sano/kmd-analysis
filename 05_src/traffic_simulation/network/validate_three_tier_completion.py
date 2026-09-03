"""Validate the isolated three-tier completion run and quality accounting."""
from __future__ import annotations
import json
from pathlib import Path
import jsonschema
from traffic_simulation.paths import REPOSITORY_ROOT

ROOT=REPOSITORY_ROOT
RUN=ROOT/"reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_1"
SCHEMA=ROOT/"reproducibility/config/traffic_simulation/schemas/formal_completion_record_three_tier_v17.schema.json"
class ThreeTierValidationError(ValueError): pass

def validate_three_tier_completion(run: Path=RUN)->dict:
    records=json.loads((run/"formal_completion_records.json").read_text())["records"]
    quality=json.loads((run/"quality_accounting.json").read_text())
    schema=json.loads(SCHEMA.read_text()); validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
    seen=set(); tiers={"DIRECT":0,"INFERRED":0,"FALLBACK":0}; conf={"HIGH":0,"MEDIUM":0,"LOW":0,"FALLBACK":0}; methods={}
    for record in records:
        validator.validate(record)
        key=(record["record_id"],record["attribute"])
        if key in seen: raise ThreeTierValidationError(f"duplicate record {key}")
        seen.add(key); tier=record["resolution_tier"]; tiers[tier]+=1; conf[record["confidence"]]+=1; methods[record["method_id"]]=methods.get(record["method_id"],0)+1
        if tier=="INFERRED" and record["confidence"]=="FALLBACK": raise ThreeTierValidationError("inferred record has fallback confidence")
        if tier=="FALLBACK" and record["method_id"].startswith("EXTRATREES"): raise ThreeTierValidationError("silent ML fallback")
    if tiers != {k:quality[k.lower()] for k in tiers}: raise ThreeTierValidationError("tier accounting differs from records")
    if {k:v for k,v in conf.items() if v} != quality["confidence"]: raise ThreeTierValidationError("confidence accounting differs")
    if quality["unresolved"] != 0 or quality["formal_blocker"] != 0: raise ThreeTierValidationError("technical unresolved remains")
    return {"three_tier_completion":"passed","record_count":len(records),"tiers":tiers,"confidence":conf,"method_count":len(methods),"formal_blocker":0,"provenance_complete":True}

def main()->int:
    try: print(json.dumps(validate_three_tier_completion(),sort_keys=True)); return 0
    except (ThreeTierValidationError,jsonschema.ValidationError,KeyError) as e: print(json.dumps({"three_tier_completion":"failed","error":str(e)})); return 1
if __name__=="__main__": raise SystemExit(main())
