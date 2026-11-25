"""Physical evaluation archive independent of greedy exploration state."""
from dataclasses import asdict
from pathlib import Path
from kmd_toc.common_initial_v1.plans import dump
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.measurement_audit_v1.measurement import cross_evaluate,physical_payload,digest_payload
from .objective import measure,record,retained,selection_key

class MeasuredSet:
    """Pure measured-candidate store; production callers must validate physics."""
    def __init__(self,reference):self.reference=reference;self.entries={}

    def add(self,m,stable_id,payload,*,initial=False,branch_id=0):
        if not initial and not retained(self.reference,m):return False
        row={'metrics':m,'stable_id':stable_id,'payload':payload,'initial':initial,'branch_id':branch_id}
        old=self.entries.get(stable_id)
        if old is None or self.key(row)<self.key(old):self.entries[stable_id]=row
        return True

    def key(self,r):
        return selection_key(r['metrics'],self.reference,initial=r['initial'],branch_id=r['branch_id'],stable_id=r['stable_id'])

    def best(self):return min(self.entries.values(),key=self.key)

class Archive:
    def __init__(self,p,initial,output=None):
        self.p=p;self.reference=measure(p,initial);self.output=Path(output) if output else None
        if self.output:self.output.mkdir(parents=True,exist_ok=False)
        self.rows=[];self.candidates={}
        self.measured=MeasuredSet(self.reference)
        self.add(initial,origin='shared_initial',initial=True)

    def add(self,plan,*,origin,initial=False,branch_id=0):
        try:
            validation=require_valid(self.p,plan)
            independent=cross_evaluate(self.p,plan)
            if independent['status']!='PASS':raise ValueError('INDEPENDENT_MEASUREMENT_NOT_PASS')
            m=measure(self.p,plan);sid=digest_payload(physical_payload(plan))
        except ValueError as e:
            self.rows.append({'origin':origin,'status':'INFEASIBLE_OR_MEASUREMENT_FAIL','reason':str(e)})
            if initial:raise
            return False
        keep=initial or retained(self.reference,m)
        row={'origin':origin,'stable_id':sid,'branch_id':branch_id,'initial':initial,
             'feasible':True,'site_feasibility':validation['stopping_site_feasibility'],
             'status':'RETAINED' if keep else 'OUTSIDE_INITIAL_NONWORSENING_SET',**record(m,self.reference)}
        self.rows.append(row)
        if keep:
            entry={'plan':plan,'metrics':m,'row':row}
            old=self.candidates.get(sid)
            if old is None or self._key(entry)<self._key(old):self.candidates[sid]=entry
            self.measured.add(m,sid,entry,initial=initial,branch_id=branch_id)
        if self.output:
            target=self.output/(sid+'.json')
            if not target.exists():dump(target,asdict(plan))
        return keep

    def _key(self,entry):
        r=entry['row'];return selection_key(entry['metrics'],self.reference,initial=r['initial'],
                                           branch_id=r['branch_id'],stable_id=r['stable_id'])

    def best(self):
        winner=self.measured.best()['payload']
        return winner['plan'],dict(winner['row'])

    def save(self,path):
        _,winner=self.best();dump(path,{'evaluations':self.rows,'winner':winner,
            'selection':'pi0 I_dual, relative sum, D, W, initial, fixed branch, physical hash',
            'same_completed_set_order_invariant':True,'candidate_discovery_order_invariance':'NOT_CLAIMED'})
