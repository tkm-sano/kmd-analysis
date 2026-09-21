"""Comparison accounting: immutable historical debit, existing atomic lifecycle.
DryLedger runs inherited reservation/claim lifecycle entirely in memory. No disk
ledger is initialized by preflight. STARTED/failed/unknown remain charged.
"""
from contextlib import contextmanager
import fcntl
from .contract import *
from traffic_simulation.r24_vrptw_qaoa_worker.ledger import Ledger as StandardLedger
from traffic_simulation.r24_qaoa_initial_state_cross_condition_worker.ledger import Ledger as Lifecycle,SPENT,STATUSES,LedgerError,BudgetBlocked,digest as history_digest,now

def baseline():
    b=read(SPEC/'BUDGET_PLAN.json');p=ROOT/b['baseline']['source'];require(sha(p)==b['baseline']['sha256'],'historical ledger changed')
    state=read(p);StandardLedger.invariant(state);require(state['totals']==b['baseline']['totals'] and not state['halted'],'historical debit')
    return b,state

def projection():
    b,state=baseline();plans=rows(SPEC/'RUN_PLAN.csv');require(len(plans)==9 and len({r['group'] for r in plans})==3,'plan shape')
    rr=[];cumulative=0
    for r in plans:
        r0,_,_,_=run_plan(r['run_id']);n=int(r['training_cap'])+int(r['final_cap']);shots=int(r['training_cap'])*int(r['training_shots'])+int(r['final_cap'])*int(r['final_shots']);cumulative+=n
        rr.append(dict(run_id=r['run_id'],group=r['group'],batch=r['batch'],repetition=int(r['repetition']),max_circuits=n,max_shots=shots,cumulative_circuits=cumulative,cumulative_shots=sum(x['max_shots'] for x in rr)+shots))
    caps=b['inherited_caps'];q=state['totals'];new=sum(r['max_circuits'] for r in rr);shots=sum(r['max_shots'] for r in rr)
    require(new==900 and shots==1843200,'comparison maximum')
    require(q['scientific_consumed']+new<=caps['scientific'] and q['consumed']+new<=caps['total'] and q['shots_consumed']+shots<=caps['shots'],'budget ceiling')
    require(all(g['projected_charge']<=caps['condition_p'] for g in b['per_group']),'group ceiling')
    return dict(status='PASS',mode='READ_ONLY_PROJECTION',runs=rr,per_group=b['per_group'],caps=caps,baseline=q,new_max_circuits=new,new_max_shots=shots,projected_scientific=q['scientific_consumed']+new,projected_all=q['consumed']+new,projected_shots=q['shots_consumed']+shots,remaining_scientific_after_max=caps['scientific']-q['scientific_consumed']-new,actual_circuits=0,actual_shots=0,actual_optimizer_evaluations=0,actual_Aer_calls=0)

class Ledger(StandardLedger):
    @staticmethod
    def summary(s):
        slots=[v for r in s['runs'].values() for v in r['circuits'].values()];spent=sum(x['status'] in SPENT for x in slots);reserved=sum(x['status']=='RESERVED' for x in slots);h=s['historical']
        return dict(cap_total=s['cap_total'],existing_consumed=h['consumed'],consumed_new=spent,reserved=reserved,consumed=h['consumed']+spent,remaining_unallocated=s['cap_total']-h['consumed']-spent-reserved,scientific_consumed=h['scientific_consumed']+spent,scientific_reserved=reserved,sanity_consumed=h['sanity_consumed'],sanity_reserved=0,shots_consumed=h['shots_consumed']+spent*s['shots'],shots_reserved=reserved*s['shots'],failed_counted=sum(x['status']=='FAILED_COUNTED' for x in slots),unknown_counted=sum(x['status']=='UNKNOWN_COUNTED' for x in slots),released_unused=sum(x['status']=='UNUSED_RELEASED' for x in slots))
    @staticmethod
    def invariant(s):
        q=Ledger.summary(s)
        if q!=s.get('totals'):raise LedgerError('TOTALS_MISMATCH')
        if q['consumed_new']+q['reserved']>900 or q['scientific_consumed']+q['reserved']>2100 or q['consumed']+q['reserved']>2107 or q['shots_consumed']+q['shots_reserved']>5000000:raise BudgetBlocked('COMPARISON_CEILING')
        if s['supplemental']:raise LedgerError('NO_NEW_SANITY')
        for group,h in s['group_history'].items():
            charge=sum(c['status'] in SPENT or c['status']=='RESERVED' for r in s['runs'].values() if r['identity']['group']==group for c in r['circuits'].values())
            if charge>300 or charge+h>600:raise BudgetBlocked('GROUP_CEILING')
        prev=None
        for i,e in enumerate(s['history']):
            if e['sequence']!=i or e['previous_hash']!=prev or history_digest({k:v for k,v in e.items() if k!='event_hash'})!=e['event_hash']:raise LedgerError('HISTORY_CORRUPTION')
            prev=e['event_hash']
        for rid,r in s['runs'].items():
            if r['identity']!=s['identities'][rid] or r['status'] not in STATUSES:raise LedgerError('IDENTITY_OR_STATUS')
            if set(r['circuits'])!={*[f'training:{i}' for i in range(99)],'final:0'}:raise LedgerError('SLOTS')
            if any(c['status'] not in STATUSES for c in r['circuits'].values()):raise LedgerError('STATUS')
    @contextmanager
    def lock(self):
        b,_=baseline();external=(ROOT/b['baseline']['source']).with_suffix('.lock')
        # NFS requires a writable descriptor for exclusive flock. This is the
        # existing dedicated lock inode, NOT the immutable ledger data file.
        # r+b neither truncates nor creates it; missing/permission errors fail closed.
        with external.open('r+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            try:
                baseline()
                with super().lock():yield
            finally:fcntl.flock(lock,fcntl.LOCK_UN)
    def read_locked(self):
        s=super().read_locked();b,h=baseline()
        if s['spec_hash']!=COMPARISON_HASH or s['historical']!=h['totals'] or s['identities']!={run_identity(r['run_id'])['run_id']:run_identity(r['run_id']) for r in rows(SPEC/'RUN_PLAN.csv')}:raise LedgerError('FROZEN_BASELINE_MISMATCH')
        return s
    def reserve(self,identity):
        s=self.snapshot();order=list(s['identities']);pos=order.index(identity['run_id'])
        if any(s['runs'].get(rid,{}).get('status')!='SUCCEEDED' for rid in order[:pos] if s['identities'][rid]['batch_id']!=identity['batch_id']):raise LedgerError('PREVIOUS_BATCH_INCOMPLETE')
        return super().reserve(identity)
    reserve_run=reserve
    def initialize(self,authorization):
        require(authorization==dict(comparison_spec_sha256=COMPARISON_HASH,scientific_execution_authorized=True),'separate controlled launch authorization')
        b,_=baseline();require(self.path==ROOT/b['ledger_namespace'],'comparison namespace')
        with self.lock():
            if self.path.exists():return self.read_locked()
            s=initial_state(False);self.commit(s,'INITIALIZE',None,{},'Immutable Standard external debit');return s
    def order_gate(self,ident):
        s=self.snapshot();order=list(s['identities']);pos=order.index(ident['run_id'])
        if s['halted']:raise LedgerError('HALTED')
        for rid in order[:pos]:
            if s['runs'].get(rid,{}).get('status')!='SUCCEEDED':raise LedgerError('OUT_OF_ORDER')
            self.completed(s['identities'][rid])
    def wall_gate(self,ident,elapsed=0,required_seconds=None):
        s=self.snapshot();reserve=900 if required_seconds is None else required_seconds
        if s['batch_wall_seconds'].get(ident['batch_id'],0)+elapsed+reserve>3600 or s['historical_wall']+s['wall_seconds_new']+elapsed+reserve>25200:raise BudgetBlocked('WALL_CAP')

def initial_state(synthetic):
    b,h=baseline();caps=b['inherited_caps'];identities=[run_identity(r['run_id']) for r in rows(SPEC/'RUN_PLAN.csv')]
    s=dict(version=1,synthetic=synthetic,spec_hash=COMPARISON_HASH,cap_total=2107,planned_cap=1270,existing_consumed=h['totals']['consumed'],historical=copy.deepcopy(h['totals']),historical_wall=h['wall_seconds_new'],identities={i['run_id']:i for i in identities},group_history={g['group']:g['historical_scientific_including_duplicate_controls']+g['historical_sanity'] for g in b['per_group']},training_cap=99,final_cap=1,condition_cap=600,shot_cap=5000000,shots=2048,scope=dict(study_id='VRPTW_UNIFORM_VS_STRUCTURED',p=1,configurations=['STRUCTURED_A'],external_debit_sha256=b['baseline']['sha256']),runs={},supplemental={},history=[],halted=False,wall_seconds_new=0,batch_wall_seconds={})
    s['totals']=Ledger.summary(s);return s

class DryLedger(Ledger):
    """Inherited lifecycle, in-memory persistence seam; no real circuit calls."""
    def __init__(self):self.state=initial_state(True)
    @contextmanager
    def lock(self):yield
    def read_locked(self):self.invariant(self.state);return copy.deepcopy(self.state)
    def commit(self,s,operation,run_id,before,reason):
        for r in s['runs'].values():
            if 'reservation' in r:r['reservation']['status']=r['status']
        s['totals']=self.summary(s);e=dict(sequence=len(s['history']),operation=operation,run_id=run_id,previous_hash=s['history'][-1]['event_hash'] if s['history'] else None,after=copy.deepcopy(s['totals']),reason=reason);e['event_hash']=history_digest(e);s['history'].append(e);self.invariant(s);self.state=copy.deepcopy(s)
    def initialize(self,*a,**k):raise LedgerError('DRY_ONLY_NO_DISK_INITIALIZATION')
    def order_gate(self,ident):
        s=self.snapshot();pos=list(s['identities']).index(ident['run_id'])
        if s['halted'] or any(s['runs'].get(r,{}).get('status')!='SUCCEEDED' for r in list(s['identities'])[:pos]):raise LedgerError('OUT_OF_ORDER')
