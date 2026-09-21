"""NFS lock acceptance; production data is read-only, writes are synthetic only."""
import os,fcntl,time,json,copy,multiprocessing as mp,unittest,io,subprocess,tarfile,hashlib
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
from traffic_simulation.r24_vrptw_structured_worker import ledger as module,execution
from traffic_simulation.r24_vrptw_structured_worker.contract import *
from traffic_simulation.r24_vrptw_structured_worker.guard import ZeroShotGuard
from traffic_simulation.r24_vrptw_direct_build_preflight.audit import NoUniform
from traffic_simulation.r24_qaoa_initial_state_cross_condition_worker import ledger as lifecycle
OUT=BASE/'r24_vrptw_structured_initial_state/20260922_v6_ledger_lock_preflight'
TESTROOT=OUT/'synthetic_ledgers'/str(time.time_ns())
COMMIT=lifecycle.Ledger.commit

def dump(n,x):(OUT/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def production():
 b,h=module.baseline();return module.Ledger(ROOT/b['ledger_namespace']),ROOT/b['baseline']['source'],h

class SandboxLedger(module.Ledger):
    """Use real locks/lifecycle; permit commit ONLY under the test namespace."""
    def commit(self,s,*a,**k):
        require(self.path.resolve().is_relative_to(TESTROOT.resolve()) and s['synthetic'] is True,'synthetic-only persistence')
        return COMMIT(self,s,*a,**k)
    def initialize_test(self):
        with self.lock():
            require(not self.path.exists(),'test path must be unique')
            self.commit(module.initial_state(True),'INITIALIZE',None,{},'SYNTHETIC NFS TEST ONLY')

def sandbox(name):
 l=SandboxLedger(TESTROOT/name/'LEDGER.json');l.initialize_test();return l

def reserve_process(path,identity,q):
 try:
  l=SandboxLedger(path);l.reserve_run(identity);q.put('RESERVED')
 except lifecycle.DuplicateRun:q.put('DUPLICATE_REJECTED')
 except BaseException as e:q.put('ERROR:'+repr(e))

def writer_a(path,ready,release,q):
 try:
  l=SandboxLedger(path)
  with l.lock():
   q.put(('A_ENTER',time.monotonic()));ready.set()
   if not release.wait(10):raise RuntimeError('release timeout')
   q.put(('A_EXIT',time.monotonic()))
 except BaseException as e:q.put(('ERROR',repr(e)))

def writer_b(path,trying,entered,q):
 try:
  l=SandboxLedger(path);q.put(('B_TRY',time.monotonic()));trying.set()
  with l.lock():q.put(('B_ENTER',time.monotonic()));entered.set()
 except BaseException as e:q.put(('ERROR',repr(e)))

class LockTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.prod,cls.historical,cls.hist=production();cls.ids=[run_identity(r['run_id']) for r in rows(SPEC/'RUN_PLAN.csv')[:3]];cls.failures=[]
 def test_01_real_path_acquire_release_reacquire(self):
  original=fcntl.flock;observed=[]
  def audit(fd,op):
   descriptor=fd.fileno() if hasattr(fd,'fileno') else fd
   observed.append(dict(op=op,access_mode=fcntl.fcntl(descriptor,fcntl.F_GETFL)&os.O_ACCMODE));return original(fd,op)
  with patch.object(fcntl,'flock',audit):
   for _ in range(2):
    with self.prod.lock():self.assertEqual(read(self.historical)['totals'],self.hist['totals'])
  exclusive=[x for x in observed if x['op']==fcntl.LOCK_EX];self.assertEqual(len(exclusive),4);self.assertTrue(all(x['access_mode']==os.O_RDWR for x in exclusive))
  self.assertFalse(self.prod.path.exists());self.assertEqual(self.prod.path.with_suffix('.lock').stat().st_size,0)
  dump('NFS4_REAL_PATH_PREFLIGHT.json',dict(status='PASS',filesystem=subprocess.check_output(['findmnt','-T',str(self.prod.path.parent),'-o','TARGET,FSTYPE,OPTIONS'],text=True),historical_data=str(self.historical),historical_lock=str(self.historical.with_suffix('.lock')),comparison_data=str(self.prod.path),comparison_lock=str(self.prod.path.with_suffix('.lock')),historical_lock_open='r+b',comparison_lock_open='a+',method='fcntl.flock LOCK_EX/LOCK_UN, advisory',observations=observed,reacquire='PASS',production_data_created=False))
 def test_02_dry_reservation_inside_real_lock(self):
  with self.prod.lock():
   dry=module.DryLedger();before=dry.snapshot();dry.reserve_run(self.ids[0]);self.assertEqual(dry.snapshot()['totals']['reserved'],100);self.assertEqual(dry.snapshot()['totals']['scientific_consumed'],363)
  self.assertFalse(self.prod.path.exists())
 def test_03_concurrent_exclusion(self):
  l=sandbox('exclusion');ctx=mp.get_context('fork');ready=ctx.Event();release=ctx.Event();trying=ctx.Event();entered=ctx.Event();q=ctx.Queue()
  a=ctx.Process(target=writer_a,args=(l.path,ready,release,q));b=ctx.Process(target=writer_b,args=(l.path,trying,entered,q));a.start()
  try:
   self.assertTrue(ready.wait(10));b.start();self.assertTrue(trying.wait(10));self.assertFalse(entered.wait(.5));release.set();self.assertTrue(entered.wait(10))
   a.join(10);b.join(10);self.assertEqual(a.exitcode,0);self.assertEqual(b.exitcode,0);events=[q.get(timeout=2) for _ in range(4)];times=dict(events);self.assertGreaterEqual(times['B_ENTER'],times['A_EXIT']);self.assertEqual(l.snapshot()['totals']['reserved'],0)
   dump('CONCURRENCY_LOCK_TEST.json',dict(status='PASS',events=events,blocked_observation_seconds=.5,overlap=False,scope='Two processes, same current NFS4 client; not a multi-host/NFS-failover claim'))
  finally:
   release.set()
   for p in [a,b]:
    if p.pid and p.is_alive():p.terminate();p.join()
 def race(self,name,ids):
  l=sandbox(name);ctx=mp.get_context('fork');q=ctx.Queue();pp=[ctx.Process(target=reserve_process,args=(l.path,i,q)) for i in ids]
  for p in pp:p.start()
  try:
   for p in pp:p.join(20);self.assertEqual(p.exitcode,0)
   results=[q.get(timeout=2) for _ in pp];state=l.snapshot();module.Ledger.invariant(state);return results,state
  finally:
   for p in pp:
    if p.is_alive():p.terminate();p.join()
 def test_04_no_lost_update(self):
  results,s=self.race('different_runs',self.ids[:2]);self.assertEqual(results,['RESERVED','RESERVED']);self.assertEqual(len(s['runs']),2);self.assertEqual(s['totals']['reserved'],200);self.assertEqual(s['totals']['scientific_consumed'],363);dump('SYNTHETIC_RESERVATION_RACE.json',dict(status='PASS',results=results,totals=s['totals'],scientific=False))
 def test_05_no_duplicate_reservation(self):
  results,s=self.race('same_run',[self.ids[0]]*2);self.assertEqual(sorted(results),['DUPLICATE_REJECTED','RESERVED']);self.assertEqual(len(s['runs']),1);self.assertEqual(s['totals']['reserved'],100);dump('SYNTHETIC_DUPLICATE_RACE.json',dict(status='PASS',results=results,totals=s['totals'],scientific=False))
 def failure(self,name,stage):
  l=sandbox(name);before=sha(l.path)
  if stage=='read':target=patch.object(l,'read_locked',side_effect=ValueError('injected read failure'))
  elif stage=='validation':target=patch.object(l,'invariant',side_effect=ValueError('injected validation failure'))
  elif stage=='before_write':target=patch.object(lifecycle,'atomic',side_effect=OSError('injected before write'))
  else:target=patch.object(lifecycle.os,'replace',side_effect=OSError('injected replace failure'))
  with target,self.assertRaises((ValueError,OSError)):l.reserve_run(self.ids[0])
  self.assertEqual(sha(l.path),before);self.assertEqual(l.snapshot()['totals']['reserved'],0)
  with l.lock():self.assertEqual(sha(l.path),before)
  self.failures.append(dict(stage=stage,lock_released=True,reacquired=True,ledger_hash_unchanged=True,partial_reservation=False))
 def test_06_read_exception(self):self.failure('read_exception','read')
 def test_07_validation_exception(self):self.failure('validation_exception','validation')
 def test_08_before_write_exception(self):self.failure('before_write_exception','before_write')
 def test_09_replace_exception(self):self.failure('replace_exception','replace')
 def test_10_invalid_reservation_no_mutation(self):
  l=sandbox('bad_identity');before=sha(l.path);bad=copy.deepcopy(self.ids[0]);bad['qubo_hash']='bad'
  with self.assertRaises(lifecycle.LedgerError):l.reserve_run(bad)
  self.assertEqual(sha(l.path),before)
 def test_11_historical_counts(self):
  _,h=module.baseline();self.assertEqual(h,self.hist);self.assertEqual(h['totals']['scientific_consumed'],363);self.assertEqual(h['totals']['shots_consumed'],743424);self.assertEqual(h['totals']['reserved'],0)
 def test_12_budget_projection(self):
  v=read(BASE/'r24_vrptw_structured_initial_state/20260922_v4_direct_build_preflight/LEDGER_PROJECTION_V2.json');self.assertEqual(module.projection(),v)
 def test_13_claim_semantics(self):
  l=sandbox('claim');s=l.reserve_run(self.ids[0]);r=s['runs'][self.ids[0]['run_id']]['reservation'];l.claim_reservation(r['reservation_id'],r['context']);s=l.snapshot();self.assertEqual(s['totals']['reserved'],100);self.assertEqual(s['totals']['consumed_new'],0)
  with self.assertRaises(lifecycle.DuplicateRun):l.claim_reservation(r['reservation_id'],r['context'])
 def test_14_no_production_mutation(self):self.assertFalse(self.prod.path.exists());self.assertEqual(read(self.historical),self.hist)
 def test_15_atomic_write_unchanged(self):
  import inspect
  text=inspect.getsource(lifecycle.atomic)
  for phrase in ['os.fsync','os.replace','tempfile.mkstemp']:self.assertIn(phrase,text)
 def test_16_missing_lock_fails_closed(self):
  missing=TESTROOT/'absent_historical.json'
  with patch.object(module,'baseline',return_value=({'baseline':{'source':str(missing)}},self.hist)):
   with self.assertRaises(FileNotFoundError):
    with self.prod.lock():self.fail('unlocked entry')
  self.assertFalse(missing.with_suffix('.lock').exists())
 @classmethod
 def tearDownClass(cls):dump('FAILURE_PATH_AUDIT.json',dict(status='PASS',cases=cls.failures))

def main():
 from traffic_simulation.r24_vrptw_direct_build_preflight import test_direct as d
 from traffic_simulation.r24_vrptw_structured_worker.test_preflight import PreflightTests
 from traffic_simulation.r24_vrptw_structured_initial_state.test_design import DesignTests
 from traffic_simulation.r24_vrptw_structured_initial_state_audit.tests import AuditTests
 # A legacy AST-only test inspects the publisher preserved by cleanup. Supply
 # that exact archived source as a read fixture, without restoring/executing it.
 archive=BASE/'r24_vrptw_structured_initial_state/20260922_v5_pre_s01_git_baseline'
 legacy='05_src/traffic_simulation/r24_vrptw_structured_initial_state_audit/publish.py'
 item=next(x for x in read(archive/'STASH_FILE_INVENTORY.json') if x['path']==legacy)
 with tarfile.open(archive/'PRESERVED_UNRELATED_WORK.tar.gz') as tf:source=tf.extractfile(legacy).read()
 require(hashlib.sha256(source).hexdigest()==item['sha256'],'archived publisher identity')
 original_read=Path.read_text
 def fixture_read(path,*a,**k):
  if path==ROOT/legacy:return source.decode()
  return original_read(path,*a,**k)
 dump('LEGACY_SOURCE_FIXTURE.json',dict(path=legacy,sha256=item['sha256'],source_archive=str(archive/'PRESERVED_UNRELATED_WORK.tar.gz'),AST_inspection_only=True,restored_to_workspace=False))
 stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [LockTests,d.DirectTests,PreflightTests,DesignTests,AuditTests])
 with ZeroShotGuard() as guard,NoUniform() as no,patch.object(execution,'supervised_run',side_effect=execution.ExecutionForbidden('NO_SCIENCE')),patch.object(Path,'read_text',fixture_read):
  result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
  require(no.full.call_count==no.initial.call_count==0,'Uniform construction')
 (OUT/'TEST_RESULTS.txt').write_text(stream.getvalue());print(stream.getvalue())
 dump('TEST_RESULTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),Uniform_full=0,Uniform_initial=0,backend_calls=0,optimizer_evaluations=0,scientific_circuits=0,scientific_shots=0,ledger_increment=0))
 if not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
