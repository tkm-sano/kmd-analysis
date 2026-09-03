"""Validate a completed Phase 12 artifact directory and emit its manifest."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
import yaml
from traffic_simulation.network import execute_v17_phase12_successor_full_population as runner
from traffic_simulation.network import execute_v17_phase12_full_population as phase12
from traffic_simulation.network.validate_v17_phase12_successor_run import validate_successor_major_artifacts

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--run-id',required=True); a=p.parse_args()
    root=runner._repo_path(runner.OUTPUT_ROOT)/'runs'/a.run_id
    names={'structural_full_population':'structural/full_population.json','formal_full_population':'formal/full_population.json','complete_blocker_inventory':'formal/blocker_inventory.json','exclusion_manifest':'formal/exclusion_manifest.json','population_accounting':'population_accounting.json'}
    payloads={k:runner._load_json(root/v) for k,v in names.items()}
    contract=runner._load_yaml(runner._repo_path(runner.CONTRACT_PATH)); amendment=runner._load_yaml(runner._repo_path(runner.CONTRACT_AMENDMENT_PATH)); decision=runner._load_yaml(runner._repo_path(runner.PROFILE_DIFFERENCE_DECISION_PATH)); registry=runner._load_yaml(runner._repo_path(contract['fixed_inputs']['registry_bundle'])); policy=runner._load_yaml(runner._repo_path(contract['fixed_inputs']['blocker_policy']))
    results=validate_successor_major_artifacts(payloads,registry=registry,policy=policy,decision=decision)
    if set(results.values())!={'passed'}: raise SystemExit(results)
    refs=[]
    catalog={x['artifact_id']:x for x in contract['artifact_catalog']}; catalog['population_accounting']={**catalog['population_accounting'],'schema':amendment['overrides']['population_accounting_schema']}
    for aid,value in payloads.items():
        path=root/names[aid]; refs.append({'artifact_id':aid,'path':str(path.relative_to(runner.REPOSITORY_ROOT)),'schema':catalog[aid]['schema'],'byte_sha256':runner._sha256(path),'semantic_sha256':value['semantic_sha256']})
    source_commit=runner._require_clean_worktree(); config=runner._load_yaml(runner._repo_path(contract['fixed_inputs']['configuration']))
    manifest={'schema_version':1,'artifact_type':'phase12_successor_run_manifest','successor_run_id':runner.SUCCESSOR_ID,'run_id':a.run_id,'configuration_id':contract['configuration_id'],'configuration_version':config.get('configuration_version',config['schema_version']),'population_version':contract['population_version'],'profile_set':['structural','formal'],'governed_vclasses':list(config['permissions']['governed_vclasses']),'scenario_context_id':payloads['formal_full_population']['scenario_context_id'],'source_commit':source_commit,'base_repository_head':runner.BASE_HEAD,'dirty_tree':False,'started_at':datetime.now(timezone.utc).isoformat(),'ended_at':datetime.now(timezone.utc).isoformat(),'runtime_environment':runner._runtime_environment(),'input_hashes':runner._hash_map(tuple(Path(v) for k,v in contract['fixed_inputs'].items() if k!='hash_binding_required')),'adopted_authority_hashes':runner._hash_map(runner.ADOPTED_AUTHORITIES),'implementation_hashes':runner._hash_map(runner.IMPLEMENTATIONS),'schema_hashes':runner._hash_map(runner.RELEVANT_SCHEMAS),'artifacts':sorted(refs,key=lambda x:x['artifact_id']),'validation':{**results,'registered_values':'passed','blocker_exclusion':'passed','result':'passed'},'formal_state_mutated':False}
    runner._validate_json(manifest,runner._repo_path(runner.MANIFEST_SCHEMA)); runner._write_json(root/'successor_run_manifest.json',manifest); print(json.dumps({'run_id':a.run_id,'result':'passed','formal_blocker_count':payloads['complete_blocker_inventory']['counts']['total']})); return 0
if __name__=='__main__': raise SystemExit(main())
