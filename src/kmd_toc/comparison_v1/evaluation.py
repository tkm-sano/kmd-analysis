"""Complete-attempt tables, prespecified A medians, matched raw comparisons."""
from collections import defaultdict
import csv
import math
from pathlib import Path
from statistics import median

from .contract import (ROOT,CONTRACT_ID,IDENTITY_KEYS,REGISTRY,TIME_KIND,dump,read,run_identity,validate_manifest)

J_REASONS = ('DEFINED','A_REFERENCE_PLAN_MISSING','A_TIME_REFERENCE_INCOMPLETE','REFERENCE_TRIAL_FAILED',
    'A_REFERENCE_PLAN_MISMATCH','ZERO_REFERENCE_DENOMINATOR','NONFINITE_VALUE','TARGET_PLAN_INVALID',
    'INPUT_CONDITIONS_MISMATCH','TIME_SCOPE_MISMATCH','RESOURCE_CONTRACT_MISMATCH','LEGACY_METHOD_OR_CONTRACT')


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def mismatch(left,right):
    if left.get('contract_id')!=CONTRACT_ID or right.get('contract_id')!=CONTRACT_ID:
        return 'LEGACY_METHOD_OR_CONTRACT'
    if left.get('T_kind')!=right.get('T_kind') or left.get('T_kind')!=TIME_KIND:return 'TIME_SCOPE_MISMATCH'
    if left.get('resource_contract_hash')!=right.get('resource_contract_hash'):return 'RESOURCE_CONTRACT_MISMATCH'
    if any(left.get(k)!=right.get(k) for k in IDENTITY_KEYS):return 'INPUT_CONDITIONS_MISMATCH'
    return None


def build_reference(group,by_id):
    result={'group_id':group['group_id'],'purpose':group['purpose'],'run_ids':group['run_ids'],
            'required_count':group['required_count'],'established':False,'reason':None,
            'D_A':None,'W_A':None,'T_A_ref':None}
    rows=[by_id.get(i) for i in group['run_ids']]
    present=[r for r in rows if r and r.get('termination_reason')!='NOT_STARTED']
    if any(not r.get('adoptable') for r in present):result['reason']='REFERENCE_TRIAL_FAILED';return result
    if len(present)!=len(rows):result['reason']='A_TIME_REFERENCE_INCOMPLETE';return result
    if any(r.get('method')!='A' or r.get('implementation_id')!=REGISTRY['A']['implementation_id'] or
           r.get('algorithm_version')!=REGISTRY['A']['algorithm_version'] for r in rows):
        result['reason']='LEGACY_METHOD_OR_CONTRACT';return result
    for row in rows:
        reason=mismatch(rows[0],row)
        if reason:result['reason']=reason;return result
    if any(not finite(r.get(k)) for r in rows for k in ('D','W','T_program')):
        result['reason']='NONFINITE_VALUE';return result
    if len({(r.get('plan_semantic_hash'),r['D'],r['W']) for r in rows})!=1 or not rows[0].get('plan_semantic_hash'):
        result['reason']='A_REFERENCE_PLAN_MISMATCH';return result
    d,w,t=rows[0]['D'],rows[0]['W'],median(r['T_program'] for r in rows)
    if min(d,w,t)==0:result['reason']='ZERO_REFERENCE_DENOMINATOR';return result
    if min(d,w,t)<0:result['reason']='NONFINITE_VALUE';return result
    return {**result,'established':True,'reason':'DEFINED','D_A':d,'W_A':w,'T_A_ref':t,
            'identity':{k:rows[0][k] for k in IDENTITY_KEYS},'plan_semantic_hash':rows[0]['plan_semantic_hash'],
            'T_rule':'median of every prespecified member; no success-only reduction',
            'formal_reference':group['purpose']=='formal'}


def score(row,reference):
    if not row.get('adoptable'):return {'J':None,'J_reason':'TARGET_PLAN_INVALID'}
    if row.get('contract_id')!=CONTRACT_ID or row.get('implementation_id')!=REGISTRY.get(row.get('method'),{}).get('implementation_id'):
        return {'J':None,'J_reason':'LEGACY_METHOD_OR_CONTRACT'}
    if reference is None:return {'J':None,'J_reason':'A_REFERENCE_PLAN_MISSING'}
    if not reference['established']:return {'J':None,'J_reason':reference['reason']}
    reason=mismatch(row,reference['identity'])
    if reason:return {'J':None,'J_reason':reason}
    values=[row.get(k) for k in ('D','W','T_program')]
    denominators=[reference[k] for k in ('D_A','W_A','T_A_ref')]
    if any(not finite(x) for x in values+denominators) or any(x<0 for x in values):
        return {'J':None,'J_reason':'NONFINITE_VALUE'}
    if any(x==0 for x in denominators):return {'J':None,'J_reason':'ZERO_REFERENCE_DENOMINATOR'}
    if any(x<0 for x in denominators):return {'J':None,'J_reason':'NONFINITE_VALUE'}
    return {'J':math.fsum(v/d for v,d in zip(values,denominators))/3,'J_reason':'DEFINED'}


def not_run(manifest,run):
    return {**run_identity(manifest,run),'input_state':'NOT_CHECKED','termination_reason':'NOT_STARTED',
        'validation_state':'NOT_RUN','adoptable':False,'D':None,'W':None,'W_first':None,'W_reload':None,
        'T_program':None,'T_attempt':None,'T_input':None,'T_planning':None,'T_validation':None,
        'T_adapter':None,'T_setup':None,'T_export':None,'J':None,'J_reason':'TARGET_PLAN_INVALID',
        'plan_sha256':None,'plan_semantic_hash':None,'error':None}


def validate_result(row,expected):
    from jsonschema import Draft202012Validator
    Draft202012Validator(read(ROOT/'configs/toc_delivery/comparison_v1_result_schema.json')).validate(row)
    keys=(*IDENTITY_KEYS,'method','implementation_id','algorithm_version','method_config_hash',
          'case_id','pair_id','attempt_id','repeat_id','retry_of','run_id','source_hashes','method_config_file_hash')
    if any(row.get(k)!=expected.get(k) for k in keys):raise ValueError('RESULT_IDENTITY_MISMATCH:'+row.get('run_id','missing'))
    if row.get('input_state') not in ('NOT_CHECKED','VALID','INVALID'):raise ValueError('INPUT_STATE')
    if row.get('validation_state') not in ('NOT_RUN','NO_PLAN','NO_FEASIBLE_PLAN','INVALID_PLAN','VALIDATED','NATIVE_DEADLINE_REJECTED'):
        raise ValueError('VALIDATION_STATE')
    if row.get('adoptable'):
        if row['validation_state']!='VALIDATED' or row['input_state']!='VALID':raise ValueError('FALSE_ADOPTABILITY')
        if any(not finite(row.get(k)) or row[k]<0 for k in ('D','W','W_first','W_reload','T_program')):
            raise ValueError('INVALID_ADOPTED_METRIC')
        if row['T_program']>row['budget_wall_s'] or abs(row['W']-row['W_first']-row['W_reload'])>1e-9:
            raise ValueError('METRIC_TIME_OR_WAIT_MISMATCH')
    elif any(row.get(k) is not None for k in ('D','W','W_first','W_reload','T_program')):
        raise ValueError('REJECTED_VALUES_IN_ADOPTED_COLUMNS')
    return row


def summarize(rows):
    summaries=[]
    for method in REGISTRY:
        own=[r for r in rows if r['method']==method]
        valid_input=[r for r in own if r['input_state']=='VALID' and r['termination_reason']!='NOT_STARTED']
        verified=sum(r['adoptable'] for r in valid_input)
        summaries.append({'method':method,'planned':len(own),
            'target_case_ids':sorted({r['case_id'] for r in own}),
            'target_case_count':len({r['case_id'] for r in own}),
            'planned_run_ids':[r['run_id'] for r in own],
            'adopted_run_ids':[r['run_id'] for r in own if r['adoptable']],
            'excluded_from_adopted_values':[{'run_id':r['run_id'],'input_state':r['input_state'],
                'termination_reason':r['termination_reason'],'validation_state':r['validation_state']}
                for r in own if not r['adoptable']],
            'executed':sum(r['termination_reason']!='NOT_STARTED' for r in own),
            'valid_input_executed':len(valid_input),'validated_plan_count':verified,
            'no_plan_count':sum(r['validation_state'] in ('NO_PLAN','NO_FEASIBLE_PLAN') for r in own),
            'invalid_plan_count':sum(r['validation_state'] in ('INVALID_PLAN','NATIVE_DEADLINE_REJECTED') for r in own),
            'limit_stop_count':sum(r['termination_reason']=='OUTER_WALL_LIMIT' or r.get('native_limit_stop',False) for r in own),
            'runtime_error_count':sum(r['termination_reason'] in ('RUNTIME_ERROR','CHILD_PROCESS_ERROR','CLEANUP_ERROR') for r in own),
            'input_invalid_count':sum(r['input_state']=='INVALID' for r in own),
            'not_executed_count':sum(r['termination_reason']=='NOT_STARTED' for r in own),
            'retry_count':sum(r['retry_of'] is not None for r in own),
            'success_rate':verified/len(valid_input) if valid_input else None,
            'success_rate_denominator':'all executions with valid common input, including runtime errors and timeouts',
            'D_values':[r['D'] for r in own if r['adoptable']],
            'W_values':[r['W'] for r in own if r['adoptable']],
            'T_attempt_all_executed':[r['T_attempt'] for r in own if r['termination_reason']!='NOT_STARTED']})
    return summaries


def paired(rows,left,right):
    groups=defaultdict(dict)
    retries=[]
    for row in rows:
        if row['method'] not in (left,right):continue
        if row['retry_of'] is not None:retries.append(row['run_id']);continue
        key=(row['case_id'],row['pair_id'])
        if row['method'] in groups[key]:raise ValueError('AMBIGUOUS_PRIMARY_PAIR')
        groups[key][row['method']]=row
    entries=[]
    for (case,pair),methods in sorted(groups.items()):
        a,b=methods.get(left),methods.get(right)
        reason=None
        if not a or not b:reason='UNPLANNED_COUNTERPART'
        elif any(r['termination_reason']=='NOT_STARTED' for r in (a,b)):reason='NOT_EXECUTED'
        elif any(r['input_state']!='VALID' for r in (a,b)):reason='INVALID_OR_UNCHECKED_INPUT'
        else:reason=mismatch(a,b)
        status=('EXCLUDED' if reason else 'BOTH_SUCCESS' if a['adoptable'] and b['adoptable'] else
                'LEFT_ONLY_SUCCESS' if a['adoptable'] else 'RIGHT_ONLY_SUCCESS' if b['adoptable'] else 'BOTH_FAILED')
        entry={'case_id':case,'pair_id':pair,'left_method':left,'right_method':right,'status':status,
            'reason':reason,'left_run_id':a['run_id'] if a else None,'right_run_id':b['run_id'] if b else None,
            'raw_exclusion_reason':None if status=='BOTH_SUCCESS' else reason or status,
            'left_state':{k:a.get(k) for k in ('input_state','termination_reason','validation_state')} if a else None,
            'right_state':{k:b.get(k) for k in ('input_state','termination_reason','validation_state')} if b else None,
            'raw':None,'J':None}
        if status=='BOTH_SUCCESS':
            entry['raw']={k:{left:a[k],right:b[k],'right_minus_left':b[k]-a[k]} for k in ('D','W','T_program')}
            entry['J']={left:a['J'],right:b['J']} if a.get('J') is not None and b.get('J') is not None else None
        entries.append(entry)
    return {'pair':[left,right],'target_cases':len(entries),'raw_adopted_cases':sum(e['status']=='BOTH_SUCCESS' for e in entries),
        'excluded_from_raw_count':sum(e['status']!='BOTH_SUCCESS' for e in entries),
        'J_adopted_cases':sum(e['J'] is not None for e in entries),'entries':entries,
        'retries_not_substituted_for_primary':retries,'units':{'D':'km','W':'min','T_program':'s','J':'dimensionless'}}


def aggregate(manifest_path,output):
    manifest_path=Path(manifest_path);manifest=validate_manifest(read(manifest_path))
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    rows=[]
    expected_ids={r['run_id'] for r in manifest['runs']}
    directory=manifest_path.parent/'runs'
    if directory.exists() and any(p.name not in expected_ids for p in directory.iterdir() if p.is_dir()):
        raise ValueError('UNREGISTERED_RUN_PRESENT')
    for run in manifest['runs']:
        path=directory/run['run_id']/'result.json'
        row=read(path) if path.exists() else not_run(manifest,run)
        rows.append(validate_result(row,run_identity(manifest,run)))
    by_id={r['run_id']:r for r in rows}
    refs={g['group_id']:build_reference(g,by_id) for g in manifest['reference_groups']}
    for row in rows:row.update(score(row,refs.get(row.get('reference_group_id'))))
    common={'contract_id':CONTRACT_ID,'phase':manifest['phase'],'units':{'D':'km','W':'min','T_program':'s'},
            'independent_sample_count':None,'p_values':None,'confidence_intervals':None}
    dump(out/'ALL_ATTEMPTS.json',{'metadata':common,'rows':rows})
    summaries=summarize(rows)
    dump(out/'ATTEMPT_COUNTS.json',{'metadata':common,'rows':summaries})
    dump(out/'A_REFERENCES.json',{'metadata':common,'groups':refs,'formal_T_A_ref_registered':manifest['phase']=='formal' and all(r['established'] for r in refs.values()) and bool(refs)})
    pairs=[paired(rows,a,b) for a,b in [('A','D'),('C','D'),('A','B'),('A','C'),('B','C'),('B','D')]]
    dump(out/'PAIRED_COMPARISONS.json',{'metadata':common,'pairs':pairs})
    fields=['run_id','case_id','pair_id','method','attempt_id','retry_of','phase','contract_id','input_state',
        'termination_reason','validation_state','adoptable','D','W','W_first','W_reload','T_program','T_attempt','J','J_reason']
    with (out/'ALL_ATTEMPTS.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    return {'all_attempts':len(rows),'adoptable':sum(r['adoptable'] for r in rows),'references':refs,'pair_summaries':[{k:p[k] for k in ('pair','target_cases','raw_adopted_cases','J_adopted_cases')} for p in pairs]}
