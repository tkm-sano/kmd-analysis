"""Independent checks of adopted reference values, source counts, preservation."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def require(v,what):checks.append({'check':what,'passed':bool(v)})

rows=list(csv.DictReader((ROOT/'EVIDENCE.csv').open()))
refs=load(Path('configs/toc_delivery/a_human_route_time_reference_v1.json'))
require(len(rows)==13 and len({r['id'] for r in rows})==13,'unique evidence records')
classes={}
for r in rows:classes.setdefault(r['category'],[]).append(r)
require(len(classes['anchor'])==1,'one anchor, not22 postal offices')
require(len(classes['paired_experience_match'])==1,'one additional experience-paired report')
require(len(classes['individual_duration_support'])==2,'two individual duration reports')
require(len(classes['aggregate_duration_support'])==3,'three aggregate duration reports')
require(len(classes['adjacent_task_duration_support'])==1,'one adjacent task report')
require(sum(len(classes[k]) for k in ['paired_experience_match','individual_duration_support','aggregate_duration_support','adjacent_task_duration_support'])==7,'seven distinct supporting clients')
require(len(classes['duplicate'])==3 and all(r['counts_as_separate_case']=='False' for r in classes['duplicate']),'reprints not counted')
require(len(classes['general_vendor_claim'])==1 and classes['general_vendor_claim'][0]['counts_as_separate_case']=='False','general example not counted')
require(len(classes['scope_counterexample'])==1,'counter evidence retained')

unit=refs['experience_conditions']
require(unit['experienced']=={'min_s':5*60,'max_s':10*60},'experienced minutes to seconds')
require(unit['novice']=={'min_s':30*60,'max_s':60*60},'novice minutes to seconds')
require(refs['distribution'] is None and refs['default_midpoint'] is None,'no invented probability distribution or central value')
require(all(v is None for v in refs['mapping'].values()),'no unverified scale/worker/episode/fullT mapping')
require(not refs['automatically_used_in_existing_experiments'],'external reference only')
require(not refs['replaces_a_rule_baseline_v1_coefficients'],'no hidden coefficient replacement')
require(refs['do_not_map_experience_to_A1_A2_A3'],'experience not assigned to algorithms')
require(Path('configs/toc_delivery/a_human_route_time_reference_v1.json').read_bytes()==(ROOT/'ADOPTED_REFERENCE.json').read_bytes(),'reference copies identical')

byid={r['id']:r for r in rows}
expected={'TOSA':(30*60,60*60),'SAGAMI':(60*60,60*60),'COMPACT':(30*60,40*60),'WINWASTE':(45*60,60*60),'SAINTCARE':(30*60,60*60),'TRIVALUE':(3*3600,3*3600)}
for key,(low,high) in expected.items():
 r=byid[key];require(int(r['before_s_low'])==low and int(r['before_s_high'])==high,'before time conversion:'+key)
require(not byid['SUPERPHARMACY']['before_s_low'] and int(byid['SUPERPHARMACY']['before_s_high'])==3600,'up-to60 has no invented lower bound')
passages=load(ROOT/'WEB_VERIFIED_PASSAGES.json')
require('indexed original' in passages['SAGAMI']['verification'],'indexed-only source limitation retained')
manifest=load(ROOT/'SOURCE_MANIFEST.json')
for source in manifest:
 if source.get('status')==200:
  require(digest(Path(source['path']))==source['sha256'],'original hash:'+source['id'])
  require(digest(Path(source['text_path']))==source['text_sha256'],'extracted text hash:'+source['id'])
for key,phrases in {
 'ZENRIN':['10分ほど','30分～1時間'],
 'TOSA':['30分〜1時間','全7名','毎日30分'],
 'COMPACT':['30-40 minutes','six vehicles','60 points'],
 'SAINTCARE':['30 分～1 時間','平成26 年11 月13 日'],
 'TRIVALUE':['92件','10台','手作業で3時間'],
}.items():
 source=next(r for r in manifest if r['id']==key)
 text=Path(source['text_path']).read_text()
 for phrase in phrases:require(re.sub(r'\s+','',phrase) in re.sub(r'\s+','',text),'original text correspondence:'+key+':'+phrase)

before=load(ROOT/'PRESERVATION_BEFORE.json')
for p,h in before['files'].items():require(digest(Path(p))==h,'existing adopted file unchanged:'+p)
require(before['head']==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'no commit')
oldroot=Path('output/toc_delivery/ad_pipeline_20261112_route_v2')
for item in load(oldroot/'PRESERVATION_RESULT.json')['frozen_files']:
 require(digest(Path(item['path']))==item['sha256'],'frozen unchanged:'+item['path'])
oldindex=load(oldroot/'FINAL_ARTIFACT_INDEX.json')['files']
for p in ['docs/research/A_TO_D_COMPARISON.csv',str(oldroot/'A_TO_D_COMPARISON.csv')]:
 require(digest(Path(p))==oldindex[p]['sha256'],'existing comparison unchanged:'+p)
doc=Path('docs/research/toc_delivery_a/A_JAPAN_POST_T_CORROBORATION.md')
require(doc.read_bytes()==(ROOT/doc.name).read_bytes(),'report copies identical')
require(Path('docs/research/toc_delivery_a/A_JAPAN_POST_T_CORROBORATION_EVIDENCE.csv').read_bytes()==(ROOT/'EVIDENCE.csv').read_bytes(),'CSV copies identical')
result={'all_passed':all(r['passed'] for r in checks),'checks':len(checks),'results':checks,
        'scope':'Evidence/ref-value review only; not human timing measurement, S1 recalibration, or algorithm execution.'}
(ROOT/'VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('checks',len(checks),'passed',result['all_passed'])
for r in checks:
 if not r['passed']:print('FAILED',r['check'])
if not result['all_passed']:raise SystemExit(1)
