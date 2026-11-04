"""Evidence IO for this review only. Never writes outside this new output tree."""
from pathlib import Path
import csv,json,hashlib,subprocess,platform,sys
R=Path('/home/takuma/kmd-analysis')
U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup')
L=B.parent/'relocated'
O=Path(__file__).resolve().parent
PREV=R/'review_outputs/integrated_causal_audit_20261102/run01'
SC='01_research_design/scenario_evaluation/'
NET=R/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml'
SOURCES={}; EXPECTED={}
with (PREV/'COMBINED_SOURCE_INVENTORY.csv').open() as h:
 EXPECTED={x['path']:x['sha256'] for x in csv.DictReader(h)}
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def sha(p):
 with Path(p).open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()
def resolve(p):
 p=Path(p)
 if p.is_file():return p
 for base in [R,U,B,L]:
  if p.is_relative_to(base):
   rel=p.relative_to(base)
   for other in [R,U,B,L]:
    if (other/rel).is_file():return other/rel
 raise FileNotFoundError(p)
def use(p):
 p=resolve(p);key=str(p)
 if key not in SOURCES:
  h=sha(p);expected=EXPECTED.get(key)
  if expected and expected!=h:raise ValueError('Protected source hash mismatch: '+key)
  SOURCES[key]={'path':key,'sha256':h,'bytes':p.stat().st_size,'prior_audit_sha256':expected,'prior_match':h==expected if expected else None}
 return p
def read(p):return json.loads(use(p).read_text())
def rows(p):
 with use(p).open() as h:return list(csv.DictReader(h))
def write(name,x):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(name,a,fields=None):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 if not fields:fields=list(a[0]) if a else ['status']
 with p.open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(a)
def save_sources(name):write(name,list(SOURCES.values()))
def protect_previous():
 manifest=read(PREV/'REVIEW_ARTIFACT_MANIFEST.json');bad=[]
 for x in manifest:
  if sha(use(PREV/x['path']))!=x['sha256']:bad.append(x['path'])
 if bad:raise ValueError('Previous review modified: '+str(bad))
 write('PREVIOUS_REVIEW_VERIFICATION.json',{'files':len(manifest),'mismatches':bad,'arithmetic_rerun':False})
def environment():
 binary=use(R/'.local/sumo-1.24.0/bin/sumo');fork=use(L/SC/'canonical_delivery_trajectories_20261006/canonical_sumo_fork')
 deps=[];ldd={}
 for p in [binary,fork,use(R/'.local/sumo-1.24.0/lib/libsumocpp.so')]:
  proc=subprocess.run(['ldd',str(p)],text=True,capture_output=True,timeout=15);ldd[str(p)]={'returncode':proc.returncode,'output':proc.stdout,'stderr':proc.stderr}
  for line in proc.stdout.splitlines():
   if 'not found' in line:raise ValueError('Unresolved native dependency '+line)
   for token in line.split():
    if token.startswith('/') and Path(token).is_file():
     pp=use(Path(token).resolve());deps.append({'path':str(pp),'sha256':SOURCES[str(pp)]['sha256']})
 version=subprocess.run([str(binary),'--version'],capture_output=True,text=True,timeout=15)
 model={'engine':'NATIVE_TIME_ZERO_FORK','fork_sha256':sha(fork),'sumo_cli_sha256':sha(binary),'libsumocpp_sha256':sha(use(R/'.local/sumo-1.24.0/lib/libsumocpp.so')),'dependencies':sorted({x['path']:x for x in deps}.values(),key=lambda x:x['path']),'kernel':platform.release(),'machine':platform.machine(),'os':platform.platform(),'python':sys.version,'python_executable_sha256':sha(use(Path(sys.executable).resolve())),'env_selected':{k:__import__('os').environ.get(k) for k in ['LD_LIBRARY_PATH','SUMO_HOME','LANG','LC_ALL','TZ']},'clean_build_acceptance':'HOLD_NOT_REBUILT','historical_environment_equality':'HOLD_NOT_PROVEN'}
 write('ENVIRONMENT.json',{'fingerprint':digest(model),'model':model,'ldd':ldd,'sumo_version_stdout':version.stdout,'sumo_version_returncode':version.returncode})
 return model
