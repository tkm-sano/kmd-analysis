"""VRPTW ledger using the validated locking, atomic journal and lifecycle methods.

Only initialization, VRPTW budget invariants and supplemental sanity handling are
specialized. Old CVRP ledgers and the old 2000 ceiling are never opened or reused.
"""
import copy
import json
from pathlib import Path
from .contract import FREEZE,ROOT,read,rows,require,load,plan,identity,MANIFEST_SHA256,sha
from traffic_simulation.r24_qaoa_initial_state_cross_condition_worker.ledger import (
    Ledger as OriginalLedger,LedgerError,DuplicateRun,BudgetBlocked,atomic,now,digest,reservation_context,SPENT,STATUSES)

class Ledger(OriginalLedger):
    @staticmethod
    def summary(s):
        science=[v for r in s['runs'].values() for v in r['circuits'].values()];sanity=list(s['supplemental'].values());slots=science+sanity
        consumed=sum(v['status'] in SPENT for v in slots);reserved=sum(v['status']=='RESERVED' for v in slots)
        return dict(cap_total=s['cap_total'],existing_consumed=0,consumed_new=consumed,reserved=reserved,consumed=consumed,
            failed_counted=sum(v['status']=='FAILED_COUNTED' for v in slots),unknown_counted=sum(v['status']=='UNKNOWN_COUNTED' for v in slots),
            released_unused=sum(v['status']=='UNUSED_RELEASED' for v in slots),remaining_unallocated=s['cap_total']-consumed-reserved,
            scientific_consumed=sum(v['status'] in SPENT for v in science),scientific_reserved=sum(v['status']=='RESERVED' for v in science),
            sanity_consumed=sum(v['status'] in SPENT for v in sanity),sanity_reserved=sum(v['status']=='RESERVED' for v in sanity),
            shots_consumed=sum(v['status'] in SPENT for v in science)*s['shots'],
            shots_reserved=sum(v['status']=='RESERVED' for v in science)*s['shots'])

    @staticmethod
    def invariant(s):
        q=Ledger.summary(s)
        if s.get('totals')!=q:raise LedgerError('LEDGER_TOTALS_MISMATCH')
        if q['consumed']+q['reserved']>s['cap_total'] or q['consumed']<0:raise BudgetBlocked('STUDY_CIRCUIT_CAP')
        if q['scientific_consumed']+q['scientific_reserved']>s['scientific_cap']:raise BudgetBlocked('SCIENTIFIC_CAP')
        if q['sanity_consumed']+q['sanity_reserved']>s['sanity_cap']:raise BudgetBlocked('SANITY_CAP')
        if q['shots_consumed']+q['shots_reserved']>s['shot_cap']:raise BudgetBlocked('STUDY_SHOT_CAP')
        for cid in s['conditions']:
            science=[v for r in s['runs'].values() if r['identity']['condition']==cid for v in r['circuits'].values()]
            sanity=[v for v in s['supplemental'].values() if v['condition']==cid]
            charged=sum(v['status'] in SPENT or v['status']=='RESERVED' for v in science+sanity)
            if charged>min(s['condition_cap'],s['batch_cap']):raise BudgetBlocked('CONDITION_OR_BATCH_CAP')
        previous=None
        for i,e in enumerate(s['history']):
            payload={k:v for k,v in e.items() if k!='event_hash'}
            if e['sequence']!=i or e['previous_hash']!=previous or digest(payload)!=e['event_hash']:raise LedgerError('LEDGER_HISTORY_CORRUPTION')
            previous=e['event_hash']
        for rid,r in s['runs'].items():
            if s['identities'].get(rid)!=r['identity']:raise LedgerError('RUN_IDENTITY_MISMATCH')
            if r['status'] not in STATUSES:raise LedgerError('RUN_STATUS')
            expected={f'{phase}:{i}' for phase,n in [('training',s['training_cap']),('final',s['final_cap'])] for i in range(n)}
            if set(r['circuits'])!=expected:raise LedgerError('CIRCUIT_SLOTS_MISMATCH')
            if any(c['status'] not in STATUSES for c in r['circuits'].values()):raise LedgerError('CIRCUIT_STATUS')
        if any(v['status'] not in STATUSES for v in s['supplemental'].values()):raise LedgerError('SANITY_STATUS')

    def initialize(self,spec,identities,*,synthetic=False):
        require(spec==load(),'ledger config')
        expected=[identity(spec,plan(spec,r['run_id'])) for r in rows(FREEZE/'RUN_PLAN.csv')]
        require(identities==expected,'all21 frozen identities')
        canonical=ROOT/read(FREEZE/'LEDGER_SPEC.json')['planned_path']
        require((synthetic and self.path.resolve()!=canonical.resolve()) or (not synthetic and self.path.resolve()==canonical.resolve()),'ledger namespace')
        limits=spec['resource_gate']['execution_limits']
        baseline=dict(spec_hash=MANIFEST_SHA256,synthetic=synthetic,cap_total=limits['total_circuits'],planned_cap=limits['total_circuits'],
            existing_consumed=0,scientific_cap=limits['scientific_circuits'],sanity_cap=limits['preflight_circuits'],
            identities={i['run_id']:i for i in identities},conditions=list(dict.fromkeys(i['condition'] for i in identities)),
            training_cap=spec['optimizer']['training_evaluation_cap'],final_cap=1,condition_cap=limits['condition_p_circuits'],
            batch_cap=limits['batch_circuits'],shot_cap=limits['total_shots'],shots=spec['shots']['independent_final'],
            scope=dict(study_id=spec['study_id'],p=spec['p'],configurations=['STANDARD_QAOA'],cumulative_across_processes=True),
            batch_wall_cap=limits['batch_cumulative_wall_seconds'],study_wall_cap=limits['study_cumulative_wall_seconds'])
        with self.lock():
            if self.path.exists():
                s=self.read_locked()
                if any(s.get(k)!=v for k,v in baseline.items()):raise LedgerError('LEDGER_FROZEN_BASELINE_MISMATCH')
                return s
            s=dict(version=1,**baseline,runs={},supplemental={},history=[],halted=False,wall_seconds_new=0,batch_wall_seconds={})
            self.commit(s,'INITIALIZE',None,{},'VRPTW-only ledger; no previous CVRP consumption')
            return s

    def reserve_sanity(self,cid):
        with self.lock():
            s=self.read_locked();before=self.summary(s)
            if cid not in s['conditions']:raise LedgerError('WRONG_CONDITION')
            if cid in s['supplemental']:raise DuplicateRun('DUPLICATE_SANITY')
            if s['halted']:raise LedgerError('EXECUTION_HALTED')
            s['supplemental'][cid]=dict(condition=cid,phase='sanity',status='RESERVED',shots=0,timestamp=now())
            self.commit(s,'RESERVE_SANITY',None,before,cid);return s

    def transition_sanity(self,cid,status,receipt=None):
        with self.lock():
            s=self.read_locked();before=self.summary(s);c=s['supplemental'][cid]
            if s['halted']:raise LedgerError('EXECUTION_HALTED')
            if status=='STARTED':
                if c['status']!='RESERVED':raise DuplicateRun('NO_SANITY_RETRY')
            elif status in ['SUCCEEDED','FAILED_COUNTED','UNKNOWN_COUNTED']:
                if c['status']!='STARTED':raise LedgerError('INVALID_SANITY_TRANSITION')
                if status=='SUCCEEDED' and not receipt:raise LedgerError('RECEIPT_REQUIRED')
            else:raise LedgerError('INVALID_SANITY_TRANSITION')
            c.update(status=status,receipt=receipt,timestamp=now())
            if status in ['FAILED_COUNTED','UNKNOWN_COUNTED']:s['halted']=True
            self.commit(s,status,None,before,cid)

    def reserve_all(self,spec):
        for cid in self.snapshot()['conditions']:self.reserve_sanity(cid)
        for r in rows(FREEZE/'RUN_PLAN.csv'):self.reserve_run(identity(spec,plan(spec,r['run_id'])))
        return self.snapshot()

    def completed(self,ident):
        s=self.snapshot();r=s['runs'].get(ident['run_id'])
        if not r or r['status']!='SUCCEEDED':return None
        if r['identity']!=ident:raise LedgerError('COMPLETED_IDENTITY_MISMATCH')
        result=r.get('result');p=Path(result['path'])
        if not p.is_file() or sha(p)!=result['sha256']:raise LedgerError('COMPLETED_RESULT_HASH_MISMATCH')
        value=read(p)
        if value.get('identity')!=ident or value.get('status')!='SUCCEEDED':raise LedgerError('COMPLETED_RESULT_IDENTITY')
        manifest=p.parent/'ARTIFACT_SHA256.json'
        if not manifest.is_file():raise LedgerError('COMPLETED_MANIFEST_MISSING')
        if sha(manifest)!=r.get('artifact_manifest_sha256'):raise LedgerError('COMPLETED_MANIFEST_HASH_MISMATCH')
        for name,h in read(manifest).items():
            if sha(p.parent/name)!=h:raise LedgerError('COMPLETED_ARTIFACT_HASH_MISMATCH')
        return value

    def finish(self,rid,result_path):
        # Pin the entire run manifest in the same ledger transaction as completion.
        with self.lock():
            s=self.read_locked();before=self.summary(s);r=s['runs'][rid];p=Path(result_path)
            result=read(p);manifest=p.parent/'ARTIFACT_SHA256.json'
            if result.get('identity')!=r['identity'] or result.get('status')!='SUCCEEDED':raise LedgerError('RESULT_IDENTITY_MISMATCH')
            if s['halted'] or r['circuits']['final:0']['status']!='SUCCEEDED':raise LedgerError('FINAL_NOT_SUCCEEDED')
            if any(c['status'] in {'RESERVED','STARTED'} for c in r['circuits'].values()):raise LedgerError('PENDING_CIRCUITS')
            entries=read(manifest)
            if entries.get('RESULT.json')!=sha(p):raise LedgerError('RESULT_MANIFEST_MISMATCH')
            for name,h in entries.items():
                file=p.parent/name
                if not file.resolve().is_relative_to(p.parent.resolve()) or sha(file)!=h:raise LedgerError('ARTIFACT_MANIFEST_MISMATCH')
            r.update(status='SUCCEEDED',result=dict(path=str(p),sha256=sha(p)),artifact_manifest_sha256=sha(manifest))
            self.commit(s,'FINISH_RUN',rid,before,'Complete result AND immutable artifact manifest verified and pinned')

    def order_gate(self,ident):
        s=self.snapshot()
        if s['halted']:raise LedgerError('STUDY_HALTED')
        order=list(s['identities']);pos=order.index(ident['run_id'])
        if any(s['runs'].get(r,{}).get('status')!='SUCCEEDED' for r in order[:pos]):raise LedgerError('OUT_OF_ORDER_RUN')
        for rid in order[:pos]:self.completed(s['identities'][rid])
        sanity=s['supplemental'].get(ident['condition'],{})
        if sanity.get('status')!='SUCCEEDED':raise LedgerError('RUNTIME_SANITY_NOT_VALIDATED')
        receipt=sanity.get('receipt',{});p=Path(receipt.get('path',''))
        if not p.is_file() or sha(p)!=receipt.get('sha256'):raise LedgerError('SANITY_RECEIPT_MISMATCH')
        result=read(p)
        if result.get('condition')!=ident['condition'] or result.get('spec_hash')!=MANIFEST_SHA256 or result.get('status')!='PASS':raise LedgerError('SANITY_IDENTITY_MISMATCH')

    def wall_gate(self,ident,elapsed=0,required_seconds=None):
        s=self.snapshot();spec=load();limits=spec['resource_gate']['execution_limits']
        reserve=limits['run_wall_seconds'] if required_seconds is None else required_seconds
        if s['batch_wall_seconds'].get(ident['batch_id'],0)+elapsed+reserve>s['batch_wall_cap']:raise BudgetBlocked('BATCH_WALL_STOP')
        if s['wall_seconds_new']+elapsed+reserve>s['study_wall_cap']:raise BudgetBlocked('STUDY_WALL_STOP')
