"""Pinned VRPTW contract. No backend/optimizer import or implicit execution."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import importlib.metadata
import sys

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reproducibility/outputs/traffic_simulation'
FREEZE=BASE/'r24_vrptw_qaoa_execution_spec/20260921_v1'
ENC=BASE/'r24_vrptw_quantum_encoding_preflight/20260921_v1'
BENCH=BASE/'r24_vrptw_benchmark_spec/20260921_v1'
OUT=BASE/'r24_vrptw_qaoa_execution/20260921_v1/implementation_preflight'
MANIFEST_SHA256='51267f3c194a6b54d755ee2633e08b59ffe33592047a58528c85a80a29453a29'

class Stop(RuntimeError):pass
def require(ok,reason,code='SPEC_MISMATCH'):
    if not ok:raise Stop(code+': '+str(reason))
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def rows(p):
    with Path(p).open() as f:return list(csv.DictReader(f))
def table(p,records,fields=None):
    fields=fields or list(dict.fromkeys(k for r in records for k in r))
    with Path(p).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in records:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def load():
    require(sha(FREEZE/'FINAL_FREEZE_MANIFEST.json')==MANIFEST_SHA256,'freeze trust anchor','WRONG_SPEC_HASH')
    manifest=read(FREEZE/'FINAL_FREEZE_MANIFEST.json')
    for p,h in manifest['artifacts'].items():require(sha(FREEZE/p)==h,p,'WRONG_SPEC_HASH')
    spec=read(FREEZE/'QAOA_CONFIGURATION.json')
    require(spec['p']==1 and spec['configuration_id']=='STANDARD_QAOA','primary definition')
    return spec

def validate(spec):require(spec==load(),'configuration changed','CONFIGURATION_OR_SEED_MISMATCH')

def plan(spec,run_id):
    validate(spec);matches=[r for r in rows(FREEZE/'RUN_PLAN.csv') if r['run_id']==run_id]
    require(len(matches)==1,run_id,'WRONG_CONDITION_OR_RUN')
    r=matches[0];r['repetition']=int(r['repetition']);r['p']=int(r['p'])
    mapping=copy.deepcopy(spec['seed_mapping'][r['repetition']])
    source=[s for s in rows(FREEZE/'SEED_PLAN.csv') if s['run_id']==run_id]
    training=sorted((s for s in source if s['phase']=='training'),key=lambda s:int(s['evaluation_index']))
    final=[s for s in source if s['phase']=='final']
    require([int(s['simulator_seed']) for s in training]==mapping['training_simulator_seeds'],'training seed plan','CONFIGURATION_OR_SEED_MISMATCH')
    require(len(final)==1 and int(final[0]['simulator_seed'])==mapping['final_simulator_seed'],'final seed plan','CONFIGURATION_OR_SEED_MISMATCH')
    require(all(int(s['transpiler_seed'])==mapping['transpiler_seed'] for s in source),'transpiler seed','CONFIGURATION_OR_SEED_MISMATCH')
    require(digest(mapping)==r['seed_mapping_sha256'],'seed digest','CONFIGURATION_OR_SEED_MISMATCH')
    r['seeds']=mapping;r['initial_parameters']=[float(r['initial_alpha']),float(r['initial_beta'])]
    require(r['initial_parameters']==[spec['parameters']['initial_alpha'],spec['parameters']['initial_beta']],'initial parameters')
    require(float(r['scale'])==spec['parameters']['scale'],'scale')
    return r

def condition(cid):
    result=[r for r in rows(FREEZE/'SCIENTIFIC_CONDITION_SET.csv') if r['condition']==cid]
    require(len(result)==1,cid,'WRONG_CONDITION_OR_RUN')
    return result[0]

def identity(spec,run):
    require(run==plan(spec,run['run_id']),'run plan changed','RUN_IDENTITY_MISMATCH')
    c=condition(run['condition']);gate=read(FREEZE/'IDENTITY_GATES.json')['conditions'][run['condition']]
    selected=read(ENC/'SELECTED_ENCODING_SPEC.json')
    return dict(study_id=spec['study_id'],batch_id=run['batch'],condition=run['condition'],base_id=c['base_id'],
        TW_regime=c['TW_regime'],repetition=run['repetition'],run_id=run['run_id'],arm='STANDARD_QAOA',
        execution_spec_sha256=MANIFEST_SHA256,qubo_hash=gate['qubo_coefficients_sha256'],
        variable_order_hash=gate['variable_order_sha256'],encoding_hash=gate['selected_encoding_sha256'],
        penalty_rule_hash=digest(dict(rule=selected['penalty_rule'],A=read(ENC/'conditions'/run['condition']/'QUBO.json')['penalty_A'],
            M=read(ENC/'conditions'/run['condition']/'QUBO.json')['AND_M'])),
        seed_mapping_hash=digest(run['seeds']),configuration_hash=digest(spec),
        condition_role={k:c[k] for k in ['role','wide_control','temporal_active','waiting_required','benchmark_role']})

def check_condition_sources(cid):
    gate=read(FREEZE/'IDENTITY_GATES.json')['conditions'][cid]
    for p,h in gate['file_sha256'].items():
        category='VALIDATOR_MISMATCH' if '/r24_vrptw/validator.py' in p or '/r24_vrptw/instance.py' in p else 'CLASSICAL_REFERENCE_MISMATCH' if p.endswith(('EXACT.json','MILP.json','EXACT_ROUTE_PROOF.json')) else 'BENCHMARK_MISMATCH' if '/instances/' in p else 'QUBO_HASH_MISMATCH' if p.endswith('QUBO.json') else 'ENCODING_MISMATCH'
        require(sha(ROOT/p)==h,p,category)
    # Additional compiler-pattern artifact identity is anchored in protected preflight.
    for filename in ['TEMPORAL_COMPILER.json','QUBO.json']:
        key=f'conditions/{cid}/{filename}'
        require(sha(ENC/key)==read(FREEZE/'PROTECTED_AFTER.json')[str((ENC/key).relative_to(ROOT))],key,'QUBO_HASH_MISMATCH')
    return gate

def environment():
    policy=read(FREEZE/'RUNTIME_PREFLIGHT_POLICY.json');p=ROOT/policy['environment_manifest']
    require(sha(p)==policy['environment_sha256'],'environment manifest')
    expected=read(p)
    require(sys.executable==expected['python'],'Python executable','ENVIRONMENT_MISMATCH')
    actual={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    require(actual==expected['packages'],'package versions','ENVIRONMENT_MISMATCH')
    return dict(status='PASS',python=sys.executable,packages=actual)
