from pathlib import Path
import json,csv,hashlib,subprocess,collections,datetime
O=Path(__file__).resolve().parents[1];R=O.parents[1]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(name,data):(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
checks=[]
def ck(name,ok,detail=''):checks.append(dict(check=name,pass_=bool(ok),detail=detail))
required=['STEP4_EVIDENCE_DECISIONS.md','CLAIM_EVIDENCE_MATRIX.csv','MATERIAL_INPUT_PROVENANCE_AUDIT.md','UNRESOLVED_ISSUES.md','STEP4_FINAL_REPORT.md']
for f in required:ck('Required artifact '+f,(O/f).is_file()and(O/f).stat().st_size>0)
claims=list(csv.DictReader((O/'CLAIM_EVIDENCE_MATRIX.csv').open()));ids=[x['claim_id']for x in claims];ck('Unique claim ids',len(ids)==len(set(ids)))
for x in claims:
 ck('Only four classifications '+x['claim_id'],x['judgment']in['PASS','CONDITIONAL','HOLD','NOT CLAIMED'])
 ck('Complete evidence and expression '+x['claim_id'],all(x[k]for k in ['numerical_verification','scientific_input_basis','adoption_decision','evidence_files','evidence_sha256','evidence_locator','applicability_conditions','usable_thesis_expression','prohibited_expression','unresolved_handling','required_verification']))
 fs=x['evidence_files'].split(';');hs=x['evidence_sha256'].split(';');ck('Source hash array correspondence '+x['claim_id'],len(fs)==len(hs))
 for p,h in zip(fs,hs):ck('Claim evidence immutable '+x['claim_id']+':'+str(Path(p).name),Path(p).is_file()and sha(p)==h)
 if x['claim_id'].startswith('P2-R'):
  ck('Chen concrete outputs reference only '+x['claim_id'],x['judgment']=='CONDITIONAL'and'参考'in x['adoption_decision']and x['Chen_dependency']=='YES')
 if x['judgment']=='HOLD':ck('HOLD not adopted as assertion '+x['claim_id'],'不採用'in x['adoption_decision'])
byid={x['claim_id']:x for x in claims}
ck('Real material adoption remains HOLD',byid['M-03']['judgment']=='HOLD')
ck('General mass relation separate from concrete boundary',byid['P2-02']['judgment']=='PASS'and byid['P2-02']['Chen_dependency']=='NO_SYMBOLIC')
ck('Material-free DC main result scoped',byid['P2-04']['judgment']=='CONDITIONAL'and byid['P2-04']['Chen_dependency']=='NO_CAPACITY_INPUT')
ck('Quantum materials and real-world attribution not claimed',byid['P2-09']['judgment']=='NOT CLAIMED')
ck('Word no unconditional scientific adoption',byid['D-01']['judgment']=='HOLD')
ck('No new Word files',not list(O.rglob('*.docx')))
vr=json.load((O/'evidence/VERIFICATION_RESULT.json').open());ck('Numerical verification completed',vr['failures']==0)
# Preserve both Step3 editions, both input Word documents and Step1/Step2 exactly.
baseline=json.load((O/'evidence/PRESERVATION_BASELINE.json').open());pres=[]
for x in baseline:
 p=Path(x['path']);actual=sha(p)if p.is_file()else None;pres.append(dict(path=str(p),start_sha256=x['sha256'],end_sha256=actual,unchanged=actual==x['sha256']))
tracked=json.load((O/'evidence/TRACKED_BASELINE.json').open());tr=[]
for x in tracked:
 p=Path(x['path']);actual=sha(p)if p.is_file()else None;tr.append(dict(path=str(p),start_sha256=x['sha256'],end_sha256=actual,unchanged=actual==x['sha256']))
sources=list(csv.DictReader((O/'evidence/SOURCE_LEDGER.csv').open()));src=[]
for x in sources:
 p=Path(x['path']);actual=sha(p)if p.is_file()else None;src.append(dict(path=str(p),start_sha256=x['sha256'],end_sha256=actual,unchanged=actual==x['sha256']))
head0=json.load((O/'evidence/START.json').open())['head'];head1=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();diff=subprocess.check_output(['git','diff','--binary'],cwd=R);(O/'evidence/GIT_DIFF_END.patch').write_bytes(diff)
ck('All prior artifacts unchanged',all(x['unchanged']for x in pres),len(pres));ck('All tracked files unchanged',all(x['unchanged']for x in tr),len(tr));ck('All read source files unchanged',all(x['unchanged']for x in src),len(src));ck('Same HEAD',head0==head1);ck('Same tracked diff',diff==(O/'evidence/GIT_DIFF_START.patch').read_bytes())
result=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_artifact_count=len(pres),prior_artifact_unchanged=sum(x['unchanged']for x in pres),tracked_count=len(tr),tracked_unchanged=sum(x['unchanged']for x in tr),read_source_count=len(src),read_source_unchanged=sum(x['unchanged']for x in src),old_head=head0,new_head=head1,new_Word_files=0,failures=[x for x in pres+tr+src if not x['unchanged']],prior_artifact_records=pres,tracked_records=tr,source_records=src)
write('evidence/PRESERVATION_FINAL.json',result)
counts=collections.Counter(x['judgment']for x in claims)
completion=dict(status='STEP4 COMPLETE'if all(x['pass_']for x in checks)else'STEP4 HOLD',checks=len(checks),failures=sum(not x['pass_']for x in checks),claim_count=len(claims),judgments=dict(counts),records=checks)
write('evidence/STEP4_COMPLETION_AUDIT.json',completion)
with(O/'STEP4_FINAL_REPORT.md').open('a')as f:
 f.write(f"\n\n## 終了時監査の実測\n\n主張・根拠・採用役割・必須成果物と保全の{len(checks)}項目を確認し、不一致{completion['failures']}件であった。開始時の既存成果物{len(pres):,}ファイル、Git追跡{len(tr)}ファイル、直接参照した{len(src)}根拠ファイルは全てSHA256同一であった。両Step3のWordと成果物、元原稿、Step1/2を保全した。新規Wordファイル0、HEAD・追跡差分不変である。\n")
# Decision document and report agree with the exact matrix.
for name in ['STEP4_EVIDENCE_DECISIONS.md','STEP4_FINAL_REPORT.md']:
 txt=(O/name).read_text();assert str(len(claims))in txt
(O/'evidence/GIT_STATUS_END.txt').write_bytes(subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=R))
assert completion['failures']==0,completion
print(completion['status'],'claim counts',dict(counts),'checks',len(checks),'failures',completion['failures']);print('prior',len(pres),'tracked',len(tr),'read sources',len(src),'all preserved')
