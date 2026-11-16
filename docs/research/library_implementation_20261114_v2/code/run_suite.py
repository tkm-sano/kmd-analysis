"""Reproducible isolated experiments; sequential trials, four cores for each D.
Usage: python -B code/run_suite.py smoke|components|pricing|end_to_end
Existing successful outputs are reused; logs and failed attempts are retained.
"""
from pathlib import Path
import os,sys,json,time,subprocess,resource,hashlib,platform,signal
R=Path(__file__).resolve().parents[1];REPO=R.parents[2];E=R/'evidence'
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','RAYON_NUM_THREADS':'1','POLARS_MAX_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(REPO/'src'),'MPLCONFIGDIR':'/tmp/kmd-library-validation-mpl-v2'}
os.environ.update(env)
# Resolve four distinct physical cores without a solver or input read.
available=sorted(os.sched_getaffinity(0));cpus=[];physical=set()
for c in available:
 t=Path(f'/sys/devices/system/cpu/cpu{c}/topology');key=((t/'physical_package_id').read_text(),(t/'core_id').read_text())
 if key not in physical:cpus.append(c);physical.add(key)
 if len(cpus)==4:break
assert len(cpus)==4,'No serial fallback permitted'
os.sched_setaffinity(0,set(cpus))

def limits(parallel):
 def f():
  os.sched_setaffinity(0,set(cpus if parallel else cpus[:1]));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
 return f

def tree_rss(pid):
 total=0;stack=[pid]
 while stack:
  p=stack.pop()
  try:
   status=Path(f'/proc/{p}/status').read_text()
   total+=int(next(s for s in status.splitlines() if s.startswith('VmRSS:')).split()[1])
   stack.extend(map(int,Path(f'/proc/{p}/task/{p}/children').read_text().split()))
  except (OSError,StopIteration,ValueError):pass
 return total

phase=sys.argv[1];ledger=E/f'execution_{phase}.json'
records=json.loads(ledger.read_text())['jobs'] if ledger.exists() else []

def job(name,args,output,parallel=False,timeout=300):
 output=Path(output)
 if output.exists():print('reuse',name,flush=True);return
 logs=E/'logs';logs.mkdir(exist_ok=True);attempt=sum(r['name']==name for r in records)
 logfile=logs/f'{phase}_{name}_{attempt}.log'
 with logfile.open('x') as log:
  start=time.perf_counter();proc=subprocess.Popen([sys.executable,'-B',*map(str,args)],env=env,preexec_fn=limits(parallel),start_new_session=True,stdout=log,stderr=subprocess.STDOUT)
  peak=0
  while proc.poll() is None:
   peak=max(peak,tree_rss(proc.pid))
   if time.perf_counter()-start>timeout:
    os.killpg(proc.pid,signal.SIGKILL);proc.wait();break
   time.sleep(.01)
  elapsed=time.perf_counter()-start
 rec={'name':name,'argv':[str(a) for a in args],'returncode':proc.returncode,'wall_including_import_output_s':elapsed,'executor_tree_peak_RSS_KiB_sampled_10ms':peak,'parallel':parallel,'log':str(logfile.relative_to(R))}
 records.append(rec)
 ledger.write_text(json.dumps({'phase':phase,'CPU_ids':cpus,'python':sys.version,'platform':platform.platform(),'jobs':records,'memory_limit_GiB_per_process':4},indent=2))
 print(phase,name,proc.returncode,f'{elapsed:.3f}s',flush=True)
 if proc.returncode or not output.exists():raise RuntimeError('Experiment failed; inspect '+str(logfile))

config=json.loads((REPO/'configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json').read_text())
config['cpu_parallel']['cpu_ids']=cpus
config['trial_cg']={'max_rounds':4,'batch_size':20,'domain':'top-dual and rotating-nearest triples, singleton groups','slots':3}
config['version']='isolated-library-validation-v2'
(E/'trial_config.json').write_text(json.dumps(config,indent=2))
if not (E/'requirements.lock.txt').exists() or phase=='smoke':
 (E/'requirements.lock.txt').write_bytes(subprocess.check_output([sys.executable,'-m','pip','freeze']))
if phase!='smoke' and not (E/f'freeze_{phase}.json').exists():
 files=list((R/'code').glob('*.py'))+[E/'trial_config.json']
 (E/f'freeze_{phase}.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))

def spec_for(n,seed,backend,algorithm,tag):
 inp=E/'inputs'/f'ART_N{n}'
 if not inp.exists():
  # Preparation is outside all T; this is the same artificial fixture as tests.
  sys.path.insert(0,str(REPO/'src'));from kmd_toc.baseline_a.fixtures import artificial_problem
  from kmd_toc.common.models import save_problem
  inp.parent.mkdir(exist_ok=True);save_problem(artificial_problem(n,2,1),inp)
 out=E/'trials'/f'{tag}_N{n}_{seed}_{algorithm}_{backend}'
 if out.exists() and (out/'branches').exists() and not (out/'trial_result.json').exists():
  failed=E/'failed_trials';failed.mkdir(exist_ok=True)
  target=failed/(out.name+'_'+str(sum(p.name.startswith(out.name+'_') for p in failed.iterdir())))
  out.rename(target)
 out.mkdir(parents=True,exist_ok=True)
 spec={'trial_id':out.name,'scenario_id':f'ART_N{n}','instance_id':f'artificial_N{n}',
       'method':'D','phase':'isolated_library_validation','repetition_id':seed,'input_dir':str(inp.resolve()),'tau_s':20.,'epsilon_W_min':30.,
       'seeds':{'solver_seed':seed,'quantum_seed':seed+10000,'validation_seed':None},'config':config,
       'config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
       'trial_backend':backend,'trial_algorithm':algorithm}
 path=out/'spec.json'
 if path.exists():assert json.loads(path.read_text())==spec
 else:path.write_text(json.dumps(spec,indent=2))
 return path,out/'trial_result.json'

if phase=='smoke':
 for backend,algorithm in [('quri','legacy'),('quri','updated'),('qamomile_quri','updated')]:
  spec,out=spec_for(6,1101,backend,algorithm,'smoke');job(out.parent.name,[R/'code/trial_driver.py',spec],out,True)
elif phase=='components':
 dest=E/'backend';dest.mkdir(exist_ok=True)
 for nodes in [3,4]:
  for slots in [3,5]:
   for p in [1,2,4]:
    for b in ['qiskit','qulacs','quri']:
     name=f'{b}_n{nodes}_s{slots}_p{p}';out=dest/(name+'.json');job(name,[R/'code/backend_bench.py',b,nodes,slots,p,out],out)
 job('model_validation',[R/'code/model_validation.py',E/'model_validation_final.json'],E/'model_validation_final.json')
elif phase=='pricing':
 dest=E/'pricing';dest.mkdir(exist_ok=True)
 for seed in [1101,1102,1103]:
  for b in ['original','qiskit','qulacs','quri','qamomile_quri']:
   name=f'{b}_{seed}';out=dest/(name+'.json');job(name,[R/'code/pricing_trial.py',b,seed,out],out)
elif phase=='end_to_end':
 variants=[('original','legacy'),('qiskit','legacy'),('qulacs','legacy'),('quri','legacy'),('qamomile_quri','legacy'),('qiskit','updated'),('qulacs','updated'),('quri','updated'),('qamomile_quri','updated')]
 for n in [6,8]:
  for k,seed in enumerate([1101,1102,1103]):
   for b,a in variants[k:]+variants[:k]:
    spec,out=spec_for(n,seed,b,a,'main');job(out.parent.name,[R/'code/trial_driver.py',spec],out,True)
else:raise ValueError(phase)
