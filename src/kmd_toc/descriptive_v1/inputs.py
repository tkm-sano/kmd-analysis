"""Read-only saved-plan gateway. Scalar data are allowed only in marked fixtures."""
from pathlib import Path
from kmd_toc.common.config import read_json
from .policy import VERSION,digest
from .statistics import finite


class Reader:
    def __init__(self,registration):
        self.base=Path(registration).resolve().parent;self.hashes={};self.cases={}

    def json(self,record):
        if not isinstance(record,dict) or not record.get('path') or not record.get('sha256'):
            raise ValueError('HASH_PINNED_EVIDENCE_REQUIRED')
        path=(self.base/record['path']).resolve();actual=digest(path)
        if actual!=record['sha256']:raise ValueError('EVIDENCE_OR_PLAN_HASH_MISMATCH:'+str(path))
        self.hashes[str(path)]=actual
        return read_json(path)

    def evidence(self,record):return self.json(record)

    def case(self,scale,record):
        if scale in self.cases:return self.cases[scale]
        from kmd_toc.common.models import load_problem
        path=(self.base/record['input_path']).resolve();base=load_problem(path)
        for f in [path/'input.json',path/'od/manifest.json',*(path/'od').glob('*.npy')]:
            self.hashes[str(f)]=digest(f)
        if base.fingerprint!=record['base_problem_hash'] or base.od.fingerprint!=record['od_hash']:
            raise ValueError('REGISTERED_INPUT_HASH_MISMATCH')
        version=record['operating_version']
        if version=='FCFS_v1':p=base
        elif version=='duty-break-20261121-v1':
            from kmd_toc.duty_break_v1.models import activate,RestOptions
            raw=record['rest_options']
            options=RestOptions(raw['allow_assumed_locations'],raw.get('allow_post_final_depot_break',True),
                                tuple(tuple(x) for x in raw.get('confirmed_locations',[])))
            p=activate(base,version=version,rest_options=options)
        else:raise ValueError('EXPLICIT_SUPPORTED_OPERATING_VERSION_REQUIRED')
        self.cases[scale]=(p,version);return p,version

    def metrics(self,raw,case):
        p,version=self.case(raw['scale'],case)
        path=(self.base/raw['plan']['path']).resolve();self.json(raw['plan'])
        proof=self.json(raw['outer_evidence'])
        for name in ('trial_id','outer_unit_id','scale','method'):
            if proof.get(name)!=raw[name]:raise ValueError('OUTER_EXECUTION_IDENTITY_MISMATCH:'+name)
        if (proof.get('unit_type')!='outer_trial' or proof.get('problem_hash')!=p.fingerprint or
                proof.get('od_hash')!=p.od.fingerprint or proof.get('plan_sha256')!=raw['plan']['sha256'] or
                proof.get('comparison_profile')!=case['comparison_profile']):
            raise ValueError('OUTER_PLAN_OR_COMPARISON_CONDITIONS_UNCONFIRMED')
        if version=='FCFS_v1':
            from kmd_toc.common.models import load_plan
            from kmd_toc.fcfs_v1.evaluation import evaluate
            plan=load_plan(path);check=evaluate(p,plan);d,w=check['D_km'],check['W_min']
        else:
            from kmd_toc.duty_break_v1.models import load_plan
            from kmd_toc.duty_break_v1.evaluation import evaluate
            plan=load_plan(path);check=evaluate(p,plan);d,w=check['D_km'],check['W_total_loading_min']
        if plan.method_id!=raw['method']:raise ValueError('PLAN_METHOD_MISMATCH')
        finite([d,w],nonnegative=True)
        return d,w

    def unchanged(self):
        return [name for name,expected in self.hashes.items() if digest(name)!=expected]


def load_rows(reg,reader):
    if reg.get('version')!=VERSION:raise ValueError('STATISTICS_VERSION_REQUIRED')
    role=reg.get('data_role')
    if role not in ('verified_outer_trials','synthetic_statistics_fixture'):raise ValueError('EXPLICIT_DATA_ROLE_REQUIRED')
    rows=[];ids=set();outer_ids=set()
    for i,t in enumerate(reg.get('trials',[])):
        if t.get('scale') not in ('S1','S2','S3') or t.get('method') not in ('B','C','D'):
            raise ValueError('NO_A_TRIAL_DISTRIBUTION_OR_UNKNOWN_CELL')
        if not isinstance(t.get('trial_id'),str) or not t['trial_id'] or t['trial_id'] in ids:raise ValueError('UNIQUE_TRIAL_ID_REQUIRED')
        ids.add(t['trial_id'])
        status=t.get('status')
        if status not in ('SUCCESS','INFEASIBLE','FAILED','MISSING','INCOMPLETE','NOT_STARTED'):raise ValueError('EXPLICIT_TRIAL_STATE_REQUIRED')
        row={**t,'D':None,'W':None,'eligible':False,'exclusion_reason':None,
             'outer_attempt':t.get('unit_type')=='outer_trial' and not t.get('retry_of') and 'branch_id' not in t}
        if type(t.get('order')) is not int or t['order']<0:raise ValueError('REGISTERED_NONNEGATIVE_ORDER_REQUIRED')
        if t.get('seed_identity') is not None and not isinstance(t['seed_identity'],str):
            raise ValueError('SEED_IDENTITY_MUST_BE_A_CANONICAL_STRING')
        if not row['outer_attempt']:row['exclusion_reason']='NOT_AN_INDEPENDENT_OUTER_UNIT_OR_RETRY'
        else:
            oid=t.get('outer_unit_id')
            if not isinstance(oid,str) or not oid or oid in outer_ids:raise ValueError('UNIQUE_OUTER_EXECUTION_ID_REQUIRED')
            outer_ids.add(oid)
        if row['outer_attempt'] and status=='SUCCESS':
            try:
                if role=='synthetic_statistics_fixture':
                    d,w=t['D'],t['W'];finite([d,w],nonnegative=True)
                else:d,w=reader.metrics(t,reg['cases'][t['scale']])
                row.update(D=d,W=w,eligible=True)
            except (ValueError,KeyError,OSError) as error:row['exclusion_reason']=str(error)
        elif row['exclusion_reason'] is None:row['exclusion_reason']='NO_VALID_SUCCESS_METRICS:'+status
        for resource in ('planning_wall_s','CPU_s','max_RSS_MiB'):
            if t.get(resource) is not None:finite([t[resource]],nonnegative=True)
        rows.append(row)
    return rows
