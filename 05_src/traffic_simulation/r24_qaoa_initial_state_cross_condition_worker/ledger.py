"""Adapted validated ablation ledger: only scope/arm, initialization and caps change.
Lifecycle, locking, receipts, failure accounting and claim semantics are retained.
Atomic reservation/attempt ledger. STARTED spends a reservation permanently.

Authoritative current JSON contains immutable event history in the same fsynced
transaction. JSONL is an append-only mirror repaired from that history on open.
All reads/checks/writes share a flock; a separate worker lock enforces concurrency1.
"""
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime,timezone
import os,json,fcntl,copy,hashlib,tempfile
STATUSES={'RESERVED','CLAIMED','STARTED','SUCCEEDED','FAILED_COUNTED','UNKNOWN_COUNTED','UNUSED_RELEASED','BLOCKED_BY_BUDGET'}
SPENT={'STARTED','SUCCEEDED','FAILED_COUNTED','UNKNOWN_COUNTED'}
def now():return datetime.now(timezone.utc).isoformat()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def reservation_context(identity,scope,training_cap,final_cap):
    """Runtime metadata only; frozen scientific run identity remains unchanged."""
    return dict(identity=copy.deepcopy(identity),configuration=identity['arm'],
        requested_circuits=training_cap+final_cap,training_circuits=training_cap,final_circuits=final_cap,
        owner='r24-cross-condition:'+identity['execution_spec_sha256'],scope=copy.deepcopy(scope))

def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(name,path)
        d=os.open(path.parent,os.O_DIRECTORY);os.fsync(d);os.close(d)
    finally:
        if os.path.exists(name):os.unlink(name)
class LedgerError(RuntimeError):pass
class BudgetBlocked(LedgerError):pass
class DuplicateRun(LedgerError):pass
class Ledger:
    def __init__(self,path):self.path=Path(path);self.log=self.path.with_name('CIRCUIT_LEDGER.jsonl')
    @contextmanager
    def lock(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.with_suffix('.lock').open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(f,fcntl.LOCK_UN)
    @staticmethod
    def summary(s):
        slots=[v for r in s['runs'].values() for v in r['circuits'].values()]+list(s['supplemental'].values())
        new=sum(v['status'] in SPENT for v in slots);reserved=sum(v['status']=='RESERVED' for v in slots)
        return dict(cap_total=s['cap_total'],existing_consumed=s['existing_consumed'],consumed_new=new,reserved=reserved,consumed=s['existing_consumed']+new,failed_counted=sum(v['status']=='FAILED_COUNTED' for v in slots),unknown_counted=sum(v['status']=='UNKNOWN_COUNTED' for v in slots),released_unused=sum(v['status']=='UNUSED_RELEASED' for v in slots),remaining_unallocated=s['cap_total']-s['existing_consumed']-new-reserved)
    @staticmethod
    def invariant(s):
        q=Ledger.summary(s)
        if not (0<=q['consumed']<=q['cap_total'] and 0<=q['reserved']<=q['cap_total'] and q['consumed']+q['reserved']<=min(s['cap_total'],s['planned_cap'])):raise LedgerError('LEDGER_INVARIANT')
        if s.get('totals')!=q:raise LedgerError('LEDGER_TOTALS_MISMATCH')
        if q['consumed']+q['reserved']>s['shot_cap']//s['shots']:
            raise LedgerError('STUDY_SHOT_CAP')
        for cid in {i['condition'] for i in s['identities'].values()}:
            slots=[v for r in s['runs'].values() if r['identity']['condition']==cid for v in r['circuits'].values()]
            if sum(v['status'] in SPENT or v['status']=='RESERVED' for v in slots)>s['condition_cap']:
                raise LedgerError('CONDITION_CIRCUIT_CAP')
        prior=None
        for i,e in enumerate(s['history']):
            h=e['event_hash'];payload={k:v for k,v in e.items() if k!='event_hash'}
            if e['sequence']!=i or e['previous_hash']!=prior or digest(payload)!=h:raise LedgerError('LEDGER_HISTORY_CORRUPTION')
            prior=h
        for r in s['runs'].values():
            if r['status'] not in STATUSES:raise LedgerError('RUN_STATUS')
            if any(c['status'] not in STATUSES for c in r['circuits'].values()):raise LedgerError('CIRCUIT_STATUS')
        if any(c['status'] not in STATUSES for c in s['supplemental'].values()):raise LedgerError('SUPPLEMENTAL_STATUS')
    def mirror(self,s):
        existing=[];valid_bytes=0
        if self.log.exists():
            with self.log.open('rb') as f:
                for line in f:
                    if not line.endswith(b'\n'):break
                    try:existing.append(json.loads(line))
                    except ValueError:raise LedgerError('HISTORY_MIRROR_CORRUPTION')
                    valid_bytes+=len(line)
        if existing!=s['history'][:len(existing)]:raise LedgerError('HISTORY_MIRROR_DIVERGED')
        with self.log.open('a+b') as f:
            # Only discard an uncommitted torn suffix, never a complete event.
            f.truncate(valid_bytes);f.seek(0,2)
            for e in s['history'][len(existing):]:f.write((json.dumps(e,sort_keys=True)+'\n').encode())
            f.flush();os.fsync(f.fileno())
    def read_locked(self):
        s=json.loads(self.path.read_text());self.invariant(s);self.mirror(s);return s
    def snapshot(self):
        with self.lock():return self.read_locked()
    def commit(self,s,operation,run_id,before,reason):
        for r in s['runs'].values():
            if 'reservation' in r:r['reservation']['status']=r['status']
        s['totals']=self.summary(s);s['timestamp']=now()
        e=dict(sequence=len(s['history']),timestamp=s['timestamp'],operation=operation,run_id=run_id,before=before,delta={k:s['totals'][k]-before.get(k,0) for k in s['totals']},after=copy.deepcopy(s['totals']),reason=reason,previous_hash=s['history'][-1]['event_hash'] if s['history'] else None)
        e['event_hash']=digest(e);s['history'].append(e);self.invariant(s);atomic(self.path,s);self.mirror(s)
    def initialize(self,spec,identities):
        from contract import validate, identity as run_identity, require
        validate(spec)
        expected=[run_identity(spec,r) for r in spec['new_runs']]
        require(identities==expected,'ledger frozen new-run identities')
        b=spec['circuit_budget']
        baseline=dict(spec_hash=identities[0]['execution_spec_sha256'],
            cap_total=b['total_cap'],planned_cap=b['total_counted_max'],
            existing_consumed=b['anchor_inherited_ledger_charge'],
            identities={i['run_id']:i for i in identities},
            training_cap=spec['optimizer']['training_evaluation_cap'],
            final_cap=spec['new_runs'][0]['final_circuits'],
            condition_cap=b['condition_p_cap'],shot_cap=b['total_shots_cap'],
            shots=spec['shots']['independent_final'],
            scope=dict(study_id=identities[0]['study_id'],p=spec['p'],
                       configurations=['A','B'],cumulative_across_processes=True))
        with self.lock():
            if self.path.exists():
                s=self.read_locked()
                if any(s.get(k)!=v for k,v in baseline.items()):
                    raise LedgerError('LEDGER_FROZEN_BASELINE_MISMATCH')
                return s
            s=dict(version=1,**baseline,runs={},supplemental={},history=[],
                halted=False,wall_seconds_new=0,batch_wall_seconds={})
            self.commit(s,'INITIALIZE',None,{},'Frozen inherited charge; no reuse reservations or simulator validation slots')
            return s
    def reserve(self,identity):
        rid=identity['run_id']
        with self.lock():
            s=self.read_locked();before=self.summary(s)
            if s['identities'].get(rid)!=identity:raise LedgerError('RUN_IDENTITY_MISMATCH')
            if rid in s['runs']:raise DuplicateRun('DUPLICATE_RUN: no automatic resume/retry')
            if s['halted']:raise LedgerError('EXECUTION_HALTED')
            requested=s['training_cap']+s['final_cap']
            condition_charge=sum(c['status'] in SPENT or c['status']=='RESERVED'
                for r in s['runs'].values() if r['identity']['condition']==identity['condition']
                for c in r['circuits'].values())
            if (before['consumed']+before['reserved']+requested>min(s['cap_total'],s['planned_cap'],s['shot_cap']//s['shots'])
                or condition_charge+requested>s['condition_cap']):
                self.commit(s,'BLOCKED_BY_BUDGET',rid,before,'Requested run reservation exceeds cumulative ledger limit')
                raise BudgetBlocked('BLOCKED_BY_BUDGET')
            circuits={}
            for phase,count in [('training',s['training_cap']),('final',s['final_cap'])]:
                for i in range(count):circuits[f'{phase}:{i}']=dict(run_id=rid,repetition=identity['repetition'],phase=phase,circuit_index=i,status='RESERVED',timestamp=now())
            context=reservation_context(identity,s['scope'],s['training_cap'],s['final_cap'])
            reservation=dict(reservation_id='r24-'+digest(context),run_id=rid,repetition=identity['repetition'],
                configuration=identity['arm'],requested_circuits=requested,owner=context['owner'],scope=context['scope'],
                spec_hash=identity['execution_spec_sha256'],created_timestamp=now(),status='RESERVED',context=context)
            s['runs'][rid]=dict(identity=identity,status='RESERVED',circuits=circuits,claimed=False,result=None,reservation=reservation)
            self.commit(s,'RESERVE_RUN',rid,before,f'{requested} circuits; training/final separate');return s
    def claim_reservation(self,reservation_id,context):
        """Atomically claim one exact, pristine reservation. Never reserve/fallback."""
        with self.lock():
            s=self.read_locked();before=self.summary(s)
            identity=context.get('identity',{});rid=identity.get('run_id')
            if s['identities'].get(rid)!=identity:raise LedgerError('RESERVATION_IDENTITY_MISMATCH')
            expected=reservation_context(identity,s['scope'],s['training_cap'],s['final_cap'])
            if context!=expected:raise LedgerError('RESERVATION_CONTEXT_MISMATCH')
            r=s['runs'].get(rid)
            if r is None:raise LedgerError('RESERVATION_NOT_FOUND')
            meta=r.get('reservation',{})
            if (meta.get('reservation_id')!=reservation_id or reservation_id!='r24-'+digest(expected)
                or meta.get('context')!=expected or r['identity']!=identity
                or any(meta.get(k)!=v for k,v in dict(run_id=rid,repetition=identity['repetition'],configuration=identity['arm'],
                    requested_circuits=expected['requested_circuits'],owner=expected['owner'],scope=expected['scope'],
                    spec_hash=identity['execution_spec_sha256'],status=r['status']).items())):
                raise LedgerError('RESERVATION_IDENTITY_MISMATCH')
            if r['claimed'] or r['status']!='RESERVED' or s['halted']:raise DuplicateRun('DUPLICATE_RUN')
            expected_slots={f'{phase}:{i}':(phase,i) for phase,n in [('training',s['training_cap']),('final',s['final_cap'])] for i in range(n)}
            if set(r['circuits'])!=set(expected_slots) or any(
                c['status']!='RESERVED' or c['run_id']!=rid or c['repetition']!=identity['repetition'] or
                (c['phase'],c['circuit_index'])!=expected_slots[key] for key,c in r['circuits'].items()):
                raise LedgerError('RESERVATION_BUDGET_OR_SLOT_MISMATCH')
            r['claimed']=True;r['status']='CLAIMED'
            self.commit(s,'CLAIM_RUN',rid,before,'Exclusive claim of '+reservation_id+'; no new reservation or consumption')
            return s
    def claim(self,rid):
        """Legacy ledger-only API; scientific worker supplies explicit ID/context."""
        s=self.snapshot();r=s['runs'].get(rid)
        if r is None or 'reservation' not in r:raise LedgerError('RESERVATION_NOT_FOUND')
        return self.claim_reservation(r['reservation']['reservation_id'],r['reservation']['context'])
    reserve_run=reserve
    def transition(self,rid,phase,index,status,receipt=None,reason=''):
        if status not in {'STARTED','SUCCEEDED','FAILED_COUNTED','UNKNOWN_COUNTED'}:raise LedgerError('INVALID_TRANSITION')
        with self.lock():
            s=self.read_locked();before=self.summary(s);r=s['runs'][rid]
            c=s['supplemental'][rid+':validation'] if phase=='validation' else r['circuits'][f'{phase}:{index}']
            if status=='STARTED':
                if not r['claimed'] or c['status']!='RESERVED' or s['halted']:raise LedgerError('NO_RETRY_OR_RESERVATION')
                r['status']='STARTED'
            elif c['status']!='STARTED':raise LedgerError('INVALID_COMPLETION_NO_RETRY')
            if status=='SUCCEEDED' and not receipt:raise LedgerError('COMPLETION_RECEIPT_REQUIRED')
            c.update(status=status,timestamp=now(),receipt=receipt)
            if status in {'FAILED_COUNTED','UNKNOWN_COUNTED'}:s['halted']=True;r['status']=status
            self.commit(s,status,rid,before,reason or f'{phase}:{index}')
    def release_training(self,rid):
        with self.lock():
            s=self.read_locked();before=self.summary(s)
            for c in s['runs'][rid]['circuits'].values():
                if c['phase']=='training' and c['status']=='RESERVED':c.update(status='UNUSED_RELEASED',timestamp=now())
            self.commit(s,'RELEASE_UNUSED_TRAINING',rid,before,'Final reservation retained; STARTED never refunded')
    def finish(self,rid,result_path):
        with self.lock():
            s=self.read_locked();before=self.summary(s);r=s['runs'][rid];p=Path(result_path)
            result=json.loads(p.read_text())
            if result.get('identity')!=r['identity'] or result.get('status')!='SUCCEEDED':raise LedgerError('RESULT_IDENTITY_MISMATCH')
            if s['halted'] or r['circuits']['final:0']['status']!='SUCCEEDED':raise LedgerError('FINAL_NOT_SUCCEEDED')
            if any(c['status'] in {'RESERVED','STARTED'} for c in r['circuits'].values()):raise LedgerError('PENDING_CIRCUITS')
            r.update(status='SUCCEEDED',result=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
            self.commit(s,'FINISH_RUN',rid,before,'Durable complete result verified; unused static-only validation released')
    def halt(self,rid,reason):
        with self.lock():
            s=self.read_locked();before=self.summary(s);s['halted']=True
            self.commit(s,'HALT',rid,before,reason)
    def recover(self,rid,receipt_directory):
        """Explicit inspection only. Never restart a worker or submit a circuit."""
        with self.lock():
            s=self.read_locked();before=self.summary(s);r=s['runs'][rid];s['halted']=True
            for c in list(r['circuits'].values()):
                if c['status']!='STARTED':continue
                p=Path(receipt_directory)/f"{c['phase']}_{c['circuit_index']}_RECEIPT.json";valid=False
                if p.exists():
                    try:
                        receipt=json.loads(p.read_text());artifact=p.parent/receipt.get('artifact','')
                        valid=receipt.get('identity')==r['identity'] and receipt.get('phase')==c['phase'] and receipt.get('index')==c['circuit_index'] and artifact.is_file() and receipt.get('artifact_sha256')==hashlib.sha256(artifact.read_bytes()).hexdigest() and receipt.get('validated') is True
                    except (OSError,ValueError,TypeError):valid=False
                c.update(status='SUCCEEDED' if valid else 'UNKNOWN_COUNTED',timestamp=now(),receipt=str(p) if valid else None)
            r['status']='UNKNOWN_COUNTED' if any(c['status']=='UNKNOWN_COUNTED' for c in r['circuits'].values()) else r['status']
            self.commit(s,'CRASH_RECOVERY',rid,before,'Completed receipt identity/hash checked; incomplete STARTED counted unknown; RESERVED retained; manual review required')
            return s
    def account_wall(self,rid,seconds,batch=None):
        with self.lock():
            s=self.read_locked();before=self.summary(s);s['wall_seconds_new']+=seconds
            if batch is not None:s['batch_wall_seconds'][batch]=s['batch_wall_seconds'].get(batch,0)+seconds
            self.commit(s,'ACCOUNT_WALL',rid,before,str(seconds))
