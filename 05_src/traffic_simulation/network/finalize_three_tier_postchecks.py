"""Create acceptance, Request/Stop, and Research Portal handoff artifacts."""
from __future__ import annotations
import csv, json, hashlib, subprocess
from pathlib import Path
from traffic_simulation.paths import REPOSITORY_ROOT

ROOT=REPOSITORY_ROOT
RUN=ROOT/"reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_1"
REQ=ROOT/"03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/daily_requests.csv"
STOPS=ROOT/"03_data/processed/traffic_simulation/demand/household_parcel_v1/pipelines_v1/building_delivery_stops_scoped.csv"
NET=RUN/"three_tier.net.xml"

def count_csv(path:Path)->int:
    with path.open(encoding="utf-8",newline="") as f: return sum(1 for _ in csv.DictReader(f))
def write(name:str,value:dict)->None: (RUN/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def main()->int:
    quality=json.loads((RUN/"quality_accounting.json").read_text())
    sumo={"status":"FAIL","reason":"netconvert could not execute because installed SUMO lacks PROJ support","network_exists":NET.is_file()}
    requests=count_csv(REQ); stops=count_csv(STOPS)
    mapping={"artifact_status":"generated_non_normative_request_stop_mapping","run_id":"three_tier_run_1","status":"BLOCKED_BY_SUMO_BUILD","total_requests":requests,"total_stops":stops,"mapped":0,"unmapped":stops,"mapping_rate":0.0,"permitted_edge_mapping":None,"routeable_od":None,"reason":"new SUMO network was not materialized; no historical network was substituted"}
    write("request_stop_mapping.json",mapping)
    connectivity={"artifact_status":"generated_non_normative_network_postcheck","status":"BLOCKED_BY_SUMO_BUILD","connectivity":"NOT_EVALUATED","delivery_routeability":"NOT_EVALUATED","reason":"three_tier.net.xml is absent because netconvert requires unavailable PROJ library"}
    write("connectivity_routeability.json",connectivity)
    acceptance={"artifact_status":"generated_non_normative_three_tier_acceptance","run_id":"three_tier_run_1","direct":quality["direct"],"inferred":quality["inferred"],"fallback":quality["fallback"],"unresolved":quality["unresolved"],"formal_blocker":quality["formal_blocker"],"sumo_build":"FAIL","lane_validity":"NOT_EVALUATED","speed_validity":"NOT_EVALUATED","permission_validity":"NOT_EVALUATED","connectivity":"NOT_EVALUATED","delivery_routeability":"NOT_EVALUATED","request_stop_mapping":"BLOCKED","FORMAL_NETWORK_ACCEPTED":False,"remaining_technical_blockers":["SUMO_PROJ_LIBRARY_UNAVAILABLE","SUMO_VALIDITY_NOT_EVALUATED","CONNECTIVITY_NOT_EVALUATED","DELIVERY_ROUTEABILITY_NOT_EVALUATED","REQUEST_STOP_MAPPING_BLOCKED"]}
    write("acceptance_postcheck.json",acceptance)
    portal={"artifact_status":"generated_non_normative_research_portal_handoff","comparison_id":"STRICT-V17-VS-THREE-TIER-RUN-1","strict_v17":{"run_4":True,"run_5":True,"run_6":True,"historical_blockers":115935,"accepted_network":False},"three_tier":{"historical_blockers":115935,"direct":quality["direct"],"direct_percent":quality["tier_percent"].get("DIRECT",0),"inferred":quality["inferred"],"inferred_percent":quality["tier_percent"].get("INFERRED",0),"fallback":quality["fallback"],"fallback_percent":quality["tier_percent"].get("FALLBACK",0),"confidence":quality["confidence"],"accepted_network":False,"stop_mapping":mapping},"display_status":"three-tier values generated; network acceptance blocked by SUMO build"}
    write("research_portal_three_tier_comparison.json",portal)
    final={"artifact_status":"generated_non_normative_three_tier_final_manifest","run_id":"three_tier_run_1","quality":"quality_accounting.json","acceptance":"acceptance_postcheck.json","sumo":"sumo_materialization.json","connectivity":"connectivity_routeability.json","request_stop_mapping":"request_stop_mapping.json","research_portal":"research_portal_three_tier_comparison.json","FORMAL_NETWORK_ACCEPTED":False}
    write("final_manifest.json",final)
    print(json.dumps({"requests":requests,"stops":stops,"FORMAL_NETWORK_ACCEPTED":False,"remaining_technical_blockers":acceptance["remaining_technical_blockers"]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
