"""Strict registration and identities. No solver or plan imports."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_ID = 'whole-method-A_rule_v1-20261115-comparison-v1'
TIME_KIND = 'comparison_parent_wall_including_process_setup_v1'
MEANING = ('Compare entire delivery-plan generation methods under identical inputs, physical conditions '
           'and available resources; loading decisions are method decisions. Differences are not '
           'attributed to quantum processing alone or to improvement of operator actual performance.')
FREEZE = 'configs/toc_delivery/comparison_a_rule_v1_freeze_20261115.json'
BCD_CONFIG = 'configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json'
A_CONFIG = 'configs/toc_delivery/a_rule_v1_20261115.json'
REGISTRY = {
    'A': {'implementation_id':'frozen_A_rule_v1_direct_FCFS','algorithm_version':'A_rule_v1-20261115'},
    'B': {'implementation_id':'existing_dwt_directed_CW_shared_completion_parallel4','algorithm_version':'DWT-v1.4-CPU-parallel-multistart-20261113'},
    'C': {'implementation_id':'existing_dwt_OR_Routing_shared_completion_parallel4','algorithm_version':'DWT-v1.4-CPU-parallel-multistart-20261113'},
    'D': {'implementation_id':'existing_dwt_Huang_AOA_shared_completion_parallel4','algorithm_version':'DWT-v1.4-CPU-parallel-multistart-20261113'},
    'D_CLASSICAL_REPLACEMENT': {'implementation_id':'dwt_Huang_macro_exact_permutations_parallel4','algorithm_version':'macro-replacement-v1-20261116'},
}
IDENTITY_KEYS = ('contract_id','phase','scenario_id','scale','input_hash','OD_hash','physical_hash',
                 'resource_contract_hash','T_kind','budget_wall_s','case_parameters_hash','A_frozen_hash')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('DUPLICATE_JSON_KEY:'+k)
            result[k]=v
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))


def dump(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def atomic(path,value):
    path=Path(path)
    temporary=path.with_name(path.name+'.pending')
    with temporary.open('w') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    os.replace(temporary,path)


def check_freeze():
    freeze=read(ROOT/FREEZE)
    for name,expected in freeze['files'].items():
        if digest(ROOT/name)!=expected:raise ValueError('FROZEN_A_ASSET_CHANGED:'+name)
    return freeze


def check_profile(cpus):
    if len(cpus)!=4 or len(set(cpus))!=4 or not set(cpus)<=os.sched_getaffinity(0):
        raise ValueError('FOUR_CPU_ALLOCATION_REQUIRED')
    topology=[]
    for cpu in cpus:
        base=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        topology.append(((base/'physical_package_id').read_text().strip(),(base/'core_id').read_text().strip()))
    if len(set(topology))!=4:raise ValueError('DISTINCT_PHYSICAL_CORES_REQUIRED')
    return topology


def input_inventory(directory):
    directory=Path(directory)
    names=['input.json','od/manifest.json','od/distance_m.npy','od/duration_s.npy','od/reachable.npy']
    data,od=read(directory/'input.json'),read(directory/'od/manifest.json')
    if data['experiment']['kind']!='synthetic_validation' and (
            od['metadata'].get('table_distances_used') is not False or
            od['metadata'].get('matrix_service')!='Route per ordered pair with annotated node path; distance and duration from same Route object'):
        raise ValueError('REAL_ROAD_CASE_REQUIRES_ROUTE_PAIR_OD_NOT_TABLE')
    return {'directory':str(directory.resolve()),'input_hash':data['problem_hash'],'OD_hash':od['od_hash'],
            'files':{n:digest(directory/n) for n in names},'kind':data['experiment']['kind'],
            'counts':[len(data['stops']),len(data['vehicles']),len(data['berths'])]}


def validate_manifest(manifest):
    if manifest.get('contract_id')!=CONTRACT_ID:raise ValueError('COMPARISON_CONTRACT_MISMATCH')
    if manifest.get('phase') not in ('contract_check','formal','selection_pilot','variance_pilot','confirmation'):raise ValueError('PHASE_REQUIRED')
    if manifest.get('T_kind')!=TIME_KIND:raise ValueError('TIME_SCOPE_MISMATCH')
    if not manifest.get('cases') or not manifest.get('runs'):raise ValueError('EXPLICIT_CASES_AND_RUNS_REQUIRED')
    if any(k in manifest for k in ('reference','Tref','T_reference_multipliers')):
        raise ValueError('LEGACY_REFERENCE_FORBIDDEN')
    cases={c['case_id']:c for c in manifest['cases']}
    if manifest['physical_hash']!=digest(ROOT/'configs/toc_delivery/common_conditions_v1_1.json'):
        raise ValueError('PHYSICAL_CONFIG_HASH_MISMATCH')
    if len(cases)!=len(manifest['cases']):raise ValueError('DUPLICATE_CASE_ID')
    for case in cases.values():
        wall=case.get('budget_wall_s')
        if type(wall) not in (int,float) or not math.isfinite(wall) or wall<=0:
            raise ValueError('EXPLICIT_POSITIVE_COMMON_WALL_BUDGET_REQUIRED')
        if not all(case.get(k) is not None for k in ('scenario_id','scale','input','physical_hash','case_parameters')):
            raise ValueError('COMMON_CASE_IDENTITY_REQUIRED')
        if case['physical_hash']!=manifest['physical_hash']:raise ValueError('PHYSICAL_CONDITIONS_MISMATCH')
        if 'BCD_epsilon_W_min' not in case['case_parameters']:
            raise ValueError('EXPLICIT_BCD_SEARCH_BOUND_REQUIRED')
        epsilon=case['case_parameters']['BCD_epsilon_W_min']
        if epsilon is not None and (type(epsilon) not in (int,float) or not math.isfinite(epsilon) or epsilon<0):
            raise ValueError('EPSILON_RANGE')
        cap=case['case_parameters'].get('BCD_native_cap_s')
        if cap is not None and (type(cap) not in (int,float) or not math.isfinite(cap) or not 0<cap<=wall):
            raise ValueError('EXPLICIT_BCD_NATIVE_CAP_RANGE')
        if case['input']['kind']=='frozen_research':
            if case['scale'] not in ('S1','S2','S3'):raise ValueError('FROZEN_SCALE')
            registered=manifest['A_config']['inputs']['scenarios'][case['scale']]
            if case['input']['files']!=registered['files']:
                raise ValueError('FROZEN_ROUTE_INPUT_PIN_MISMATCH')
    runs={r['run_id']:r for r in manifest['runs']}
    if len(runs)!=len(manifest['runs']):raise ValueError('DUPLICATE_RUN_ID')
    for run in runs.values():
        if run.get('method') not in REGISTRY or run.get('case_id') not in cases:
            raise ValueError('UNKNOWN_METHOD_OR_CASE')
        if not all(k in run for k in ('attempt_id','repeat_id','pair_id','retry_of','solver_seed','quantum_seed')):
            raise ValueError('EXPLICIT_TRIAL_IDENTIFIERS_REQUIRED')
        if any(type(run[k]) is not int or run[k]<1 for k in ('attempt_id','repeat_id')):
            raise ValueError('POSITIVE_ATTEMPT_AND_REPEAT_IDENTIFIERS_REQUIRED')
        name=run['run_id']
        if not isinstance(name,str) or not name or name in ('.','..') or '/' in name or '\\' in name:
            raise ValueError('SAFE_UNIQUE_RUN_NAME_REQUIRED')
        if any(k in run for k in ('input','input_hash','OD_hash','budget_wall_s','physical_hash','T_kind','config')):
            raise ValueError('METHOD_SPECIFIC_COMMON_OVERRIDE_FORBIDDEN')
        if run['method']!='A' and (type(run['solver_seed']) is not int or run['solver_seed']<0):
            raise ValueError('EXPLICIT_BCD_SOLVER_SEED_REQUIRED')
        if run['method']=='D' and (type(run['quantum_seed']) is not int or run['quantum_seed']<0):
            raise ValueError('EXPLICIT_D_QUANTUM_SEED_REQUIRED')
        if run['method']=='A' and (run['solver_seed'] is not None or run['quantum_seed'] is not None):
            raise ValueError('FROZEN_A_USES_NO_RANDOM_SEED')
        if run['retry_of'] is not None:
            original=runs.get(run['retry_of'])
            if not original or any(original[k]!=run[k] for k in ('case_id','method','pair_id','repeat_id')):
                raise ValueError('INVALID_RETRY_RELATION')
            if original['run_id']==run['run_id']:raise ValueError('CYCLIC_RETRY')
            seen={run['run_id']};current=original
            while current['retry_of'] is not None:
                if current['run_id'] in seen:raise ValueError('CYCLIC_RETRY')
                seen.add(current['run_id']);current=runs[current['retry_of']]
    groups=manifest.get('reference_groups')
    if not isinstance(groups,list):raise ValueError('EXPLICIT_REFERENCE_GROUPS_REQUIRED')
    if len({g['group_id'] for g in groups})!=len(groups):raise ValueError('DUPLICATE_REFERENCE_GROUP')
    for group in groups:
        ids=group.get('run_ids')
        if (not isinstance(ids,list) or not ids or len(set(ids))!=len(ids) or
                group.get('required_count')!=len(ids) or group.get('purpose')!=manifest['phase']):
            raise ValueError('EXPLICIT_REFERENCE_MEMBERSHIP_REQUIRED')
        if any(i not in runs or runs[i]['method']!='A' for i in ids):raise ValueError('REFERENCE_MUST_BE_REGISTERED_NEW_A')
        if len({runs[i]['case_id'] for i in ids})!=1:raise ValueError('REFERENCE_CASE_MISMATCH')
    for run in runs.values():
        if run.get('reference_group_id') is not None:
            group=next((g for g in groups if g['group_id']==run['reference_group_id']),None)
            if group is None or runs[group['run_ids'][0]]['case_id']!=run['case_id']:
                raise ValueError('REFERENCE_ASSIGNMENT_MISMATCH')
    # A/B/C/D versions and settings are pinned; no algorithm tuning here.
    if fingerprint(manifest['A_config'])!=manifest['A_config_hash']:
        raise ValueError('A_CONFIG_PAYLOAD_MISMATCH')
    if fingerprint(manifest['BCD_config'])!=manifest['BCD_config_hash']:
        raise ValueError('BCD_CONFIG_PAYLOAD_MISMATCH')
    if manifest['A_config_file_hash']!=digest(ROOT/A_CONFIG):raise ValueError('FROZEN_A_CONFIG_FILE_HASH_MISMATCH')
    if manifest.get('design_extension'):
        from .design import validate_extension
        validate_extension(manifest)
    elif manifest['BCD_config']!=read(ROOT/BCD_CONFIG):raise ValueError('BCD_SEARCH_CONFIG_CHANGED')
    if manifest['A_config']!=read(ROOT/A_CONFIG):raise ValueError('FROZEN_A_CONFIG_CHANGED')
    if any(manifest['resource_contract'].get(k)!=v for k,v in
           {'available_physical_cores':4,'A_processes':1,'BCD_internal_branches':4,
            'native_threads_per_process':1,'method_concurrency':1}.items()):
        raise ValueError('RESOURCE_CONTRACT_MISMATCH')
    frozen=check_freeze()
    if manifest['A_frozen_hash']!=fingerprint(frozen):raise ValueError('A_FREEZE_IDENTITY_MISMATCH')
    supplied=manifest.get('registry',REGISTRY)
    if supplied!=REGISTRY and supplied!={k:v for k,v in REGISTRY.items() if k!='D_CLASSICAL_REPLACEMENT'}:
        raise ValueError('METHOD_REGISTRY_MISMATCH')
    if any(r['method'] not in supplied for r in manifest['runs']):raise ValueError('METHOD_REGISTRY_MISMATCH')
    return manifest


def register(plan_path,output):
    plan=read(plan_path)
    freeze=check_freeze()
    from kmd_toc.dwt.parallel import cpu_profile
    profile=cpu_profile({'threads':4,'cpu_parallel':{'workers':4,'native_threads_per_branch':1,
                        'cpu_ids':None,'coordinator_reserve_fraction':.2}})
    check_profile(profile['cpu_ids'])
    physical=ROOT/'configs/toc_delivery/common_conditions_v1_1.json'
    a_config,bcd=read(ROOT/A_CONFIG),read(ROOT/BCD_CONFIG)
    if plan.get('design_extension'):
        from .design import profile_config
        bcd=profile_config(plan['design_extension']['profile'])
    sources=sorted((ROOT/'src/kmd_toc').rglob('*.py'))+[ROOT/'scripts/run_comparison_v1.py',ROOT/FREEZE,
        ROOT/A_CONFIG,ROOT/BCD_CONFIG,physical,ROOT/'configs/toc_delivery/frozen_demand_v1.json']
    sources.append(ROOT/'configs/toc_delivery/comparison_v1_result_schema.json')
    if plan.get('design_extension'):
        sources.extend([ROOT/'scripts/run_comparison_design.py', ROOT/plan['design_extension']['rules_path']])
    manifest={**plan,'contract_id':plan.get('contract_id'),'T_kind':plan.get('T_kind'),
        'meaning':MEANING,'physical_hash':digest(physical),'physical_config':str(physical),
        'A_config':a_config,'A_config_hash':fingerprint(a_config),'A_config_file_hash':digest(ROOT/A_CONFIG),
        'BCD_config':bcd,'BCD_config_hash':fingerprint(bcd),'A_frozen_hash':fingerprint(freeze),
        'freeze':freeze,'registry':REGISTRY,'cpu_profile':profile,
        'resource_contract':{'available_physical_cores':4,'cpu_ids':profile['cpu_ids'],
            'A_processes':1,'BCD_internal_branches':4,'native_threads_per_process':1,
            'method_concurrency':1,'cache':'new processes; uncontrolled shared OS page cache',
            'memory':'frozen A RLIMIT_AS 4096MiB; BCD existing memory behavior; no new BCD memory cap'},
        'source_hashes':{str(p.relative_to(ROOT)):digest(p) for p in sources},
        'code_version':{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                        'workspace':'dirty; source_hashes and SOURCE_SNAPSHOT are authoritative'},
        'timestamp_utc':datetime.now(timezone.utc).isoformat()}
    if plan.get('design_extension'):
        manifest['BCD_config_file_hash']=digest(ROOT/plan['design_extension']['rules_path'])
        manifest['resource_contract']['design_process_tree_memory_limit_MiB']=plan['design_extension']['tree_memory_limit_MiB']
    for case in manifest['cases']:
        case['physical_hash']=digest(physical)
        case['input']=input_inventory(case['input_dir'])
        # Common input audit, not method work. Every timed attempt still rereads
        # and hashes the complete input; no plan or route pool is prepared.
        from kmd_toc.common.models import load_problem
        load_problem(case['input']['directory'])
        case['input']['preflight_physical_validation']='VALID'
    validate_manifest(manifest)
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    import tarfile
    with tarfile.open(out/'SOURCE_SNAPSHOT.tar.gz','x:gz') as archive:
        for p in sources:archive.add(p,arcname=str(p.relative_to(ROOT)))
    dump(out/'REGISTERED.json',manifest)
    return out/'REGISTERED.json'


def run_identity(manifest,run):
    case=next(c for c in manifest['cases'] if c['case_id']==run['case_id'])
    identity={'contract_id':CONTRACT_ID,'phase':manifest['phase'],'scenario_id':case['scenario_id'],
        'scale':case['scale'],'input_hash':case['input']['input_hash'],'OD_hash':case['input']['OD_hash'],
        'physical_hash':case['physical_hash'],'resource_contract_hash':fingerprint(manifest['resource_contract']),
        'T_kind':TIME_KIND,'budget_wall_s':case['budget_wall_s'],
        'case_parameters_hash':fingerprint(case['case_parameters']),'A_frozen_hash':manifest['A_frozen_hash']}
    return {**identity,**run,**REGISTRY[run['method']],
            'method_config_hash':manifest['A_config_hash'] if run['method']=='A' else manifest['BCD_config_hash'],
            'method_config_file_hash':manifest['A_config_file_hash'] if run['method']=='A' else manifest.get('BCD_config_file_hash',digest(ROOT/BCD_CONFIG)),
            'source_hashes':manifest['source_hashes'],'resource_contract':manifest['resource_contract'],
            'code_version':manifest.get('code_version'),
            'comparison_meaning':MEANING,'demand_seed':None,'T_A_human_reference':None}
