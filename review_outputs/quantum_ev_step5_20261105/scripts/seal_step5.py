from pathlib import Path
import hashlib,json,subprocess
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];E=O/'evidence'
required=['STEP5_BASELINE_AND_PRESERVATION.md','STEP5_OBJECTIVE_GAP_ANALYSIS.md','STEP5_OPERATIONAL_IMPACT.md','STEP5_PATHWAY1_CONDITIONS.md','STEP5_PATHWAY2_EVIDENCE.md','STEP5_INTEGRATED_DISCUSSION.md','STEP5_ACADEMIC_CONTRIBUTIONS.md','STEP5_CLAIM_EVIDENCE_AUDIT.md','THESIS_STEP5_REVISED.docx','THESIS_STEP5_REVISED.pdf','STEP5_FINAL_REPORT.md']
assert all((O/x).is_file() and (O/x).stat().st_size>0 for x in required)
assert json.loads((E/'FINAL_AUTOMATED_RESULT.json').read_text())['failures']==0
assert json.loads((E/'PRESERVATION_RESULT.json').read_text())['research_input_failures']==0
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True)==(E/'GIT_HEAD_START.txt').read_text()
assert subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R)==(E/'GIT_DIFF_START.patch').read_bytes()
(E/'GIT_STATUS_AT_SEAL.txt').write_text(subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=R,text=True))
# No current output claims all repository files are unchanged; external detected mutations remain disclosed.
result=dict(status='CONDITIONAL COMPLETE',required_files=len(required),all_required_present=True,automated_checks=28,science_checks=1386,numerical_checks=len(pd.read_csv(E/'NUMERICAL_CHECKS.csv')),research_source_mismatches=0,external_baseline_changes=13,pages=118,native_Word='HOLD',submission_format='HOLD',legacy_reference_intent='HOLD',independent_peer_review=False)
(E/'STEP5_DELIVERY_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
rows=[]
for p in sorted(O.rglob('*')):
 if not p.is_file() or p.name in ['OUTPUT_SHA256_MANIFEST.csv','close.log'] or any(x in p.relative_to(O).parts for x in ['profile','cache','config','__pycache__']):continue
 rows.append(dict(path=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
pd.DataFrame(rows).to_csv(O/'OUTPUT_SHA256_MANIFEST.csv',index=False)
# Read back every sealed output; the live closing log and renderer caches are excluded explicitly.
for x in rows:assert hashlib.sha256((O/x['path']).read_bytes()).hexdigest()==x['sha256']
print(json.dumps(dict(**result,sealed_files=len(rows)),ensure_ascii=False))
