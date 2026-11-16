"""Independent arithmetic, retained-source, and preservation checks."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent
checks=[]
def require(value,label):
    checks.append({'check':label,'passed':bool(value)})
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

rows=list(csv.DictReader((ROOT/'EVIDENCE.csv').open()))
indexed={r['id']:r for r in rows}
manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
sources={r['id']:r for r in manifest}
require(len(rows)==20 and len(indexed)==20,'20 unique evidence conditions')
for r in rows:
    score=sum(int(r[k]) for k in ['source_score','time_score','scale_score','staff_score','boundary_score'])
    require(score==int(r['total_score']) and 0<=score<=10,'score:'+r['id'])
    require(r['S1_direct_adoption']=='HOLD','no unverified S1 adoption:'+r['id'])
    require(r['source_url']==sources[r['source_id']]['url'],'source identity:'+r['id'])
for s in manifest:
    if s.get('status')==200:
        require(digest(Path(s['path']))==s['sha256'],'retained original hash:'+s['id'])
        if s.get('text_path'):require(digest(Path(s['text_path']))==s['text_sha256'],'extracted text hash:'+s['id'])

units={'SUWA':(150*60,180*60),'OKUMURA':(2*3600,2*3600),'TOMAS':(4*3600,4*3600),
       'SPRINGHOPE':(4*3600,4*3600),'MSJ':(4*3600,4*3600),'JP_EXPERT':(5*60,10*60),
       'JP_NOVICE':(30*60,60*60),'ZENRIN_EXPERT':(10*60,10*60),
       'ZENRIN_NOVICE':(30*60,60*60),'MLIT_TAMANO':(20*60,20*60),
       'FAREYE':(120*60,120*60)}
for name,(low,high) in units.items():
    r=indexed[name];require(Decimal(r['before_s_low'])==low and Decimal(r['before_s_high'])==high,'independent unit conversion:'+name)
require(indexed['STOPSTART']['numeric_relation']=='greater_than_reported_threshold' and not indexed['STOPSTART']['before_s_high'],'open upper bound:Stop Start')
for name in ['MLIT_NAGOYA','HITACHI_MONTH','COOP_REDESIGN','VISSER1989','METI_LEAD']:
    require(not indexed[name]['before_s_low'] and not indexed[name]['before_s_high'],'no invented seconds:'+name)
require(indexed['DEGRAAF']['evidence_role']=='EXCLUDE_PURE_MANUAL_CALIBRATION','semi-automated separated')
require(indexed['SMRJ_BILLING']['evidence_role']=='EXCLUDE_WRONG_BOUNDARY','billing separated')
require(indexed['HANDUP']['evidence_role']=='HOLD_TIME_UNIT','team hours unresolved')

text_checks={
    'suwa':['100〜150','6〜7台','2時間30分から3時間','重量のチェック','指示ができる状態'],
    'okumura':['毎日2時間','配車担当である私'],
    'tomas':['50件','10台','約4時間'],
    'stopstart':['three employees over four hours','1200','1,000','50 vehicles'],
    'msj':['全6拠点','合計150台','毎日平均4時間'],
    'routific':['Landon Goold spent four hours'],
    'mlit172':['半日','粗大ごみ'],
    'mlit_tamano':['配車計画作成：20分'],
    'degraaf':['semi-automated','at least three hours'],
    'fareye':['Each route took 120 minutes'],
}
for name,phrases in text_checks.items():
    text=Path(sources[name]['text_path']).read_text()
    for phrase in phrases:require(phrase in text,'original correspondence:'+name+':'+phrase)

model=list(csv.DictReader((ROOT/'OLD_MODEL_COMPATIBILITY.csv').open()))
for m in model:
    N=Decimal(m['N']);V=Decimal(m['V'])
    independent=Decimal(600)+N*Decimal(28)+V*Decimal(180)
    require(independent==Decimal(m['old_central_model_s']),'old model arithmetic:'+m['N']+':'+m['V'])
require(min(Decimal(m['old_central_model_s']) for m in model)==4480 and max(Decimal(m['old_central_model_s']) for m in model)==6060,'old model corner interval')

before=json.loads((ROOT/'PRESERVATION_BEFORE.json').read_text())
for name,expected in before['files'].items():require(digest(Path(name))==expected,'unchanged adopted file:'+name)
require(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==before['head'],'no commit')
doc=Path('docs/research/toc_delivery_a/A_HUMAN_T_CROSS_SECTOR_REVIEW_20261113.md')
require(doc.read_bytes()==(ROOT/doc.name).read_bytes(),'report copies identical')
require((Path('docs/research/toc_delivery_a/A_HUMAN_T_CROSS_SECTOR_EVIDENCE_20261113.csv')).read_bytes()==(ROOT/'EVIDENCE.csv').read_bytes(),'evidence CSV copies identical')
result={'all_passed':all(c['passed'] for c in checks),'checks':len(checks),'results':checks,
        'scope':'research evidence/arithmetic/preservation; not new human experiment or regression of unchanged algorithms',
        'not_measured':['S1 human planning T','S1 calibrated task coefficients','actual Sagawa human T']}
(ROOT/'VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('checks',len(checks),'passed',result['all_passed'])
for c in checks:
    if not c['passed']:print('FAILED',c['check'])
if not result['all_passed']:raise SystemExit(1)
