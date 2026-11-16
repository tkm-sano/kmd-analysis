"""Serial controller for isolated Pricing component tests, not DWT execution."""
from pathlib import Path
import sys,os,json,subprocess,resource,time,hashlib,platform
R=Path(__file__).resolve().parents[1];E=R/'evidence';out=E/'measurements';out.mkdir(exist_ok=True)
assert 0 in os.sched_getaffinity(0)
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1','MPLCONFIGDIR':'/tmp/kmd-survey-mpl'}
def resources():
 os.sched_setaffinity(0,{0});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
files=[R/'BENCHMARK_PROTOCOL.md',*sorted((R/'code').glob('*.py'))]
(E/'protocol_freeze.json').write_text(json.dumps({'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2))
(E/'requirements.lock.txt').write_bytes(subprocess.check_output([sys.executable,'-m','pip','freeze']))
meta={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'cpu_info':Path('/proc/cpuinfo').read_text().split('\n\n')[0],'meminfo':Path('/proc/meminfo').read_text(),'loadavg':Path('/proc/loadavg').read_text(),'limits':{'address_space_GiB':4,'CPU_ID':0,'native_threads':1},'env':{k:env[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']},'runs':[]}
backends=['qiskit','qulacs','quri','qamomile_ising']
for case in ['macro','selection']:
 for n,seed in enumerate(range(1101,1106)):
  order=backends[n%4:]+backends[:n%4]
  for backend in order:
   dest=out/f'{case}_{backend}_{seed}.json';assert not dest.exists(),dest
   ts=time.perf_counter()
   proc=subprocess.run([sys.executable,'-B',str(R/'code/benchmark.py'),backend,str(seed),str(dest),case],env=env,preexec_fn=resources,capture_output=True,text=True,timeout=120)
   wall=time.perf_counter()-ts
   rec={'case':case,'seed':seed,'backend':backend,'order':order,'returncode':proc.returncode,'launch_import_run_export_wall_s':wall,'stdout':proc.stdout,'stderr':proc.stderr}
   meta['runs'].append(rec);(E/'benchmark_execution.json').write_text(json.dumps(meta,indent=2))
   print(case,backend,seed,proc.returncode,flush=True)
   if proc.returncode:print(proc.stderr,flush=True);raise SystemExit(1)
