"""Immutable full-plan capsule and method start receipts. No result references."""
from dataclasses import asdict, dataclass, replace
from pathlib import Path
import hashlib
import json
import time

from kmd_toc.duty_break_v1.models import load_plan
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.duty_break_v1.local import metrics
from kmd_toc.measurement_audit_v1.measurement import cross_evaluate, physical_payload, digest_payload

VERSION='common-initial-20261122-v1'


def sha(path):
    return hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()


def dump(path,data):
    with Path(path).open('x') as f:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False)


def exact_metrics(p,plan):
    report=require_valid(p,plan);d,w=metrics(p,plan)
    return {'D':float(d),'W':float(w),'D_exact':str(d),'W_exact':str(w),
            'model_feasible':report['model_feasible'],'site_feasibility':report['stopping_site_feasibility']}


@dataclass(frozen=True)
class InitialInput:
    directory: Path
    manifest_bytes: bytes
    plan_bytes: bytes | None

    @property
    def manifest(self): return json.loads(self.manifest_bytes)

    def checked_plan(self,p):
        m=self.manifest
        if m['status']!='COMPLETE':raise ValueError('COMMON_INITIAL_UNAVAILABLE_FOR_BOTH_METHODS')
        path=self.directory/'plan.json'
        if path.read_bytes()!=self.plan_bytes or sha(path)!=m['plan_sha256']:
            raise ValueError('IMMUTABLE_INITIAL_CHANGED')
        if (self.directory/'INITIAL.json').read_bytes()!=self.manifest_bytes:
            raise ValueError('IMMUTABLE_INITIAL_MANIFEST_CHANGED')
        plan=load_plan(path)
        if p.fingerprint!=m['problem_hash'] or p.od.fingerprint!=m['od_hash']:
            raise ValueError('COMMON_INITIAL_PHYSICAL_PROFILE_MISMATCH')
        if digest_payload(physical_payload(plan))!=m['physical_plan_hash']:
            raise ValueError('COMMON_INITIAL_PHYSICAL_CONTENT_CHANGED')
        if exact_metrics(p,plan)!=m['metrics']:raise ValueError('COMMON_INITIAL_DW_MISMATCH')
        return plan


def read_initial(directory):
    path=Path(directory).resolve()
    return InitialInput(path,(path/'INITIAL.json').read_bytes(),
                        (path/'plan.json').read_bytes() if (path/'plan.json').exists() else None)


def create_initial(p,directory,*,experiment_id,scale,trial_id,seed,config,generator=None):
    """Exclusive creation; an existing terminal capsule is verified, never rerun."""
    from .policy import require_policy
    require_policy()
    out=Path(directory).resolve()
    if (out/'INITIAL.json').exists():
        capsule=read_initial(out);m=capsule.manifest
        if (m['experiment_id'],m['scale'],m['trial_id'],m['seed'])!=(experiment_id,scale,trial_id,seed):
            raise ValueError('INITIAL_IDENTITY_CONFLICT')
        if m['configuration']!=config or m['problem_hash']!=p.fingerprint:
            raise ValueError('INITIAL_CONFIGURATION_OR_PROBLEM_CONFLICT')
        if m['status']=='COMPLETE':capsule.checked_plan(p)
        return capsule
    out.mkdir(parents=True,exist_ok=False);begin=time.perf_counter()
    common={'version':VERSION,'experiment_id':experiment_id,'scale':scale,'trial_id':trial_id,'seed':seed,
        'problem_hash':p.fingerprint,'od_hash':p.od.fingerprint,
        'base_conditions_sha256':p.experiment.conditions_sha256,
        'duty_policy_sha256':p.activated_policy_sha256,'rest_options':p.rest_options.payload(),
        'customer_ids':[s.stop_id for s in p.stops],
        'algorithm':('directed Savings + route-count insertion + duty/FCFS finite-pool CP completion'
                     if generator is None else 'explicit artificial validation generator; not a CW result'),
        'generator_role':'existing_B_algorithm' if generator is None else 'explicit_validation_fixture',
        'configuration':config,'main_experiment':False}
    try:
        if generator is None:
            from kmd_toc.pipeline.classical import directed_cw
            from kmd_toc.duty_break_v1.cp import complete
            from kmd_toc.termination_v1.work import Ledger
            routes,settings=directed_cw(p)
            plan=complete(p,routes,'B',config,Ledger(),seed,settings)
        else:plan=generator(p,seed)
        if plan.method_id!='B':raise ValueError('INITIAL_MUST_BE_TRADITIONAL_PLAN')
        audit=cross_evaluate(p,plan)
        if audit['status']!='PASS':raise ValueError('INITIAL_COMMON_MEASUREMENT_FAIL')
        dump(out/'plan.json',asdict(plan));(out/'plan.json').chmod(0o444)
        common.update(status='COMPLETE',plan_id=plan.plan_id,plan_sha256=sha(out/'plan.json'),
            physical_plan_hash=digest_payload(physical_payload(plan)),metrics=exact_metrics(p,plan),
            generation_wall_s=time.perf_counter()-begin)
    except Exception as error:
        common.update(status='FAILED',reason=f'{type(error).__name__}:{error}',
                      metrics=None,both_methods_status='COMMON_INITIAL_UNAVAILABLE',
                      generation_wall_s=time.perf_counter()-begin)
    dump(out/'INITIAL.json',common);(out/'INITIAL.json').chmod(0o444)
    return read_initial(out)


def start(p,initial,method,output):
    if method not in ('C','D'):raise ValueError('ONLY_OPTIMIZATION_METHODS')
    m=initial.manifest
    if m['status']!='COMPLETE':
        dump(output/'START.json',{'method':method,'status':'COMMON_INITIAL_UNAVAILABLE',
             'initial_manifest_sha256':sha(initial.directory/'INITIAL.json')})
        return None
    original=initial.checked_plan(p)
    plan=replace(original,method_id=method,
                 execution_kind='quantum_circuit_simulator' if method=='D' else 'classical')
    record={'method':method,'status':'STARTED_FROM_SHARED_INITIAL','initial_plan_sha256':m['plan_sha256'],
        'physical_plan_hash':digest_payload(physical_payload(plan)),'metrics':exact_metrics(p,plan),
        'problem_hash':p.fingerprint,'od_hash':p.od.fingerprint,'trial_id':m['trial_id'],
        'initial_manifest_sha256':sha(initial.directory/'INITIAL.json'),
        'permitted_input_roles':['common_problem','common_initial','own_configuration','own_random_stream'],
        'classical_final_result_input':False,'administrative_reference_input':False}
    if record['physical_plan_hash']!=m['physical_plan_hash'] or record['metrics']!=m['metrics']:
        raise ValueError('METHOD_START_NOT_SAME_INITIAL')
    dump(output/'start_plan.json',asdict(plan))
    record['start_plan_sha256']=sha(output/'start_plan.json')
    dump(output/'START.json',record)
    return plan
