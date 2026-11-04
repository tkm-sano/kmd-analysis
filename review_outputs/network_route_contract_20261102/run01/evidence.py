"""Read-only evidence registry for the network/route/contract review."""
from pathlib import Path
import csv,json,hashlib,subprocess,platform,time,resource
R=Path('/home/takuma/kmd-analysis');U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');L=B.parent/'relocated'
O=Path(__file__).resolve().parent;P1=R/'review_outputs/integrated_causal_audit_20261102/run01';P2=R/'review_outputs/complete_run_validation_20261102/run01';SC='01_research_design/scenario_evaluation/'
NET=R/'reproducibility/outputs/traffic_simulation/attribute_resolution_v17/phase13_20260903_three_tier_completion/run_3_geometry_reacceptance/three_tier.net.xml'
SOURCES={};EXPECTED={}
for x in json.loads((P2/'SOURCE_FILES.json').read_text()):EXPECTED[x['path']]=x['sha256']
with (P1/'COMBINED_SOURCE_INVENTORY.csv').open() as h:
 for x in csv.DictReader(h):EXPECTED[x['path']]=x['sha256']
def sha(p):
 with Path(p).open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def resolve(p):
 p=Path(p)
 if p.is_file():return p
 for root in [R,U,B,L]:
  if p.is_relative_to(root):
   rel=p.relative_to(root)
   for alt in [R,U,B,L]:
    if (alt/rel).is_file():return alt/rel
 raise FileNotFoundError(p)
def use(p,expected=None):
 p=resolve(p);k=str(p)
 if k not in SOURCES:SOURCES[k]={'path':k,'sha256':sha(p),'bytes':p.stat().st_size,'expected_sha256':EXPECTED.get(k),'storage':'WORKTREE' if p.is_relative_to(R) else 'EXTERNAL_UNTRACKED' if p.is_relative_to(U) else 'PRESERVATION'}
 exp=expected or EXPECTED.get(k)
 if exp and exp!=SOURCES[k]['sha256']:raise ValueError('Source hash mismatch '+k)
 return p
def read(p,expected=None):return json.loads(use(p,expected).read_text())
def rows(p):
 with use(p).open() as h:return list(csv.DictReader(h))
def write(name,x):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(name,x,fields=None):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 if fields is None:fields=list(x[0]) if x else ['status']
 with p.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(x)
def sources(name):write(name,list(SOURCES.values()))
def metrics(start):
 rr=resource.getrusage(resource.RUSAGE_SELF)
 return {'wall_s':time.monotonic()-start,'CPU_s':rr.ru_utime+rr.ru_stime,'max_RSS_bytes':rr.ru_maxrss*1024,'scope':'static_readback_or_unit_validation_not_delivery_simulation'}
def baseline():
 start=time.monotonic();bad=[];n=0
 for root,name in [(P1,'REVIEW_ARTIFACT_MANIFEST.json'),(P2,'ARTIFACT_MANIFEST.json')]:
  for x in read(root/name):
   p=use(root/x['path']);n+=1
   if sha(p)!=x['sha256']:bad.append(str(p))
 a=rows(P2/'A_COMPLETE_RUNS.csv');b=rows(P2/'B_COMPLETE_RUNS.csv');leg=rows(P2/'B_REQUIRED_POSITIONAL_LEGS.csv')
 actual={'A_operations':len(rows(P2/'A_OPERATION_RUN_LINKS.csv')),'A_policy_candidates':len(a),'A_mechanism_extra':len(rows(P2/'A_ADDITIONAL_MECHANISM_RUNS.csv')),'B_plan_references':len(rows(P2/'B_PLAN_RUN_LINKS.csv')),'B_candidates':len(b),'B_complete':sum(bool(x['run_id']) for x in b),'B_unbound':sum(not x['run_id'] for x in b),'B_positional_requests':len(leg),'prior_test_methods':read(P2/'UNIT_TEST_RESULTS.json')['test_methods'],'prior_readback_checks':read(P2/'INDEPENDENT_VALIDATION.json')['checks'],'prior_native_units':read(P2/'NATIVE_UNIT_SUMMARY.json')['cases']}
 expected={'A_operations':2808,'A_policy_candidates':303,'A_mechanism_extra':15,'B_plan_references':36800,'B_candidates':4987,'B_complete':37,'B_unbound':4950,'B_positional_requests':219211,'prior_test_methods':26,'prior_readback_checks':6605,'prior_native_units':7}
 diffs=[{'field':k,'expected':v,'actual':actual[k]} for k,v in expected.items() if actual[k]!=v]
 write('BASELINE_RECONFIRMATION.json',{'artifacts_checked':n,'hash_mismatches':bad,'expected':expected,'actual':actual,'differences':diffs,'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'git_status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'metrics':metrics(start)})
 sources('BASELINE_SOURCES.json')
 if bad or diffs:raise RuntimeError('Baseline discrepancy: retain and report')
 print('baseline',n,'artifacts',actual,'differences',diffs)
if __name__=='__main__':baseline()
