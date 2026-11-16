"""Descriptive inherited-target audit only; never called by trial execution."""
import hashlib
import json
from pathlib import Path
from kmd_toc.comparison_v1.contract import ROOT,read,atomic,digest

root=ROOT/'output/toc_delivery/termination_rules_20261116_v1/scales_02'
source=ROOT/'configs/toc_delivery/comparison_design_20261116_v1.json'
aux=read(source)['auxiliary'];targets=aux['target_values'];rows=read(root/'ALL_RESULTS.json');observed=[]
for row in rows:
    target=targets[row['case_id']]
    end=(row['D']<=target['D'] and row['W']<=target['W']) if row['adoptable'] else (None if row['execution_state']=='NOT_STARTED' else False)
    branches=[]
    for b in row['branches']:
        log=root/'runs'/row['run_id']/f"branch_{b['branch_id']:02d}"/'stages'/'work.jsonl'
        events=[json.loads(s) for s in log.read_text().splitlines()] if log.exists() else []
        hits=[e for e in events if e['event']=='candidate_checked' and e['valid'] and e['D']<=target['D'] and e['W']<=target['W']]
        branches.append({'branch_id':b['branch_id'],'first_observed_internal_target_s':min((e['elapsed_s'] for e in hits),default=None),
            'scope':'relative to that branch Ledger creation, including its input/import; NOT parent adoption time',
            'observation_rule':'first logged double-checked candidate; no interpolation or replacement by trial completion'})
    pieces=[row.get(k) for k in ('T_input','T_planning','T_final_processing')]
    observed.append({'run_id':row['run_id'],'target':target,'target_met_at_end':end,
        'first_parent_target_observed_s':None,
        'parent_arrival_reason':'no exact parent candidate-observation timestamp was logged; cannot reconstruct it from completion T',
        'parent_final_target_observation_upper_bound_s':sum(pieces) if end and all(x is not None for x in pieces) else None,
        'upper_bound_is_not_an_arrival':True,'branches':branches})
report={'purpose':'descriptive check against PRE-EXISTING common D/W thresholds; not a new stopping or adoption rule',
    'target_source':str(source.relative_to(ROOT)),'target_source_sha256':digest(source),'target_definition':aux['target'],
    'original_target_source':aux['target_source'],'analysis_code_sha256':digest(Path(__file__)),
    'preexisting_thresholds_not_fitted_to_new_outcomes':True,'trial_records_unchanged':True,'rows':observed}
atomic(root/'INHERITED_TARGET_OBSERVATIONS.json',report)
print(json.dumps({'rows':len(observed),'final_target_met':sum(x['target_met_at_end'] is True for x in observed),
                  'exact_parent_arrivals_unobserved':len(observed),'internal_first_observations_preserved':True}))
