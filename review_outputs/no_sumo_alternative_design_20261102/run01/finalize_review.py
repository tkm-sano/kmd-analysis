"""Independent final readback/preservation review, then artifact sealing."""
from support import *
import difflib
def main():
 t=time.monotonic();checks=[]
 def ck(label,expected,actual):checks.append({'check':label,'expected':str(expected),'actual':str(actual),'status':'PASS' if expected==actual else 'FAIL'})
 docs=list(O.glob('0[0-7]_*.md'));ck('required documents',8,len(docs))
 aa=rows(O/'A_SMALL_CASES.csv');tasks=rows(O/'A_SMALL_CASE_TASKS.csv');ck('A few route cases',10,len(aa));ck('A task rows',40,len(tasks));ck('A no full evaluation',0,js(O/'A_SUMMARY.json')['new_full_cohort_evaluations'])
 for x in aa:
  tt=[y for y in tasks if y['case_id']==x['case_id']];den=sum((F(y['q_PE']) for y in tt),F(0));on=sum((F(y['q_PE']) for y in tt if y['on_time']=='True'),F(0));ck(x['case_id']+' fixed PE denominator',F(x['denominator_PE']),den);ck(x['case_id']+' numerator',F(x['on_time_PE']),on);ck(x['case_id']+' rate',F(x['F_PE']),on/den)
 ck('boundary equality',F(0),F(next(x for x in aa if x['case_id']=='exact_deadline_fixture')['min_slack_s']));ck('late fixture negative',F(-1),F(next(x for x in aa if x['case_id']=='late_plus1_fixture')['min_slack_s']))
 cert=rows(O/'B_REFERENCE_CERTIFICATE_STATUS.csv');ck('B reference PK',460,len({x['problem_id'] for x in cert}));ck('B exact missing explicit',53,sum(not x['exact_optimum_seconds'] for x in cert));ck('B few route cost checks',18,len(rows(O/'B_SMALL_ROUTE_CHECKS.csv')));ck('B no full evaluation',0,js(O/'B_SUMMARY.json')['new_full_cohort_evaluations'])
 bias=rows(O/'B_RECOVERY_BIAS_DESCRIPTIVE.csv');ck('B bias all refs retained',36800,sum(int(x['references']) for x in bias if x['dimension']=='scale'));ck('B recovered coverage',24333,sum(int(x['references']) for x in bias if x['dimension']=='scale' and x['recovery_stratum']=='ORIGINAL_RECOVERED'))
 prot=js(O/'ANALYSIS_PROTOCOL.json');ck('B no added deadline',None,prot['B']['customer_deadline']);ck('B primary no energy claim','B-E3_PRIMARY_NO_ENERGY_EFFECT_CLAIM',prot['B']['energy']);ck('C pack unknown',183,js(O/'C_SUMMARY.json')['T09_complete_mass_HOLD_rows']);ck('C failure retained',1,len(rows(O/'C_T09_PRESERVED_FAIL.csv')))
 matrix=rows(O/'CAUSAL_PATH_EVIDENCE_MATRIX.csv');ck('causal edges explicit',13,len(matrix));ck('evidence categories',{'OBSERVED','DERIVED','CONDITIONAL','UNTESTED','INVALID'},{x['evidence_class'] for x in matrix});ck('quantum material untested','UNTESTED',next(x for x in matrix if x['edge_id']=='P2-06')['evidence_class'])
 allchecks=[]
 for name in ['BASELINE','A','B','C','ROAD','TOY']:allchecks.extend(rows(O/(name+'_CHECKS.csv')))
 ck('component independent check failures',0,sum(x['status']!='PASS' for x in allchecks))
 # Register preservation hashes from all stages and compare with older pinned values where present.
 allsrc={}
 for p in sorted(O.glob('*_SOURCES.json')):
  for x in json.loads(p.read_text()):
   if not Path(x['path']).is_relative_to(O):
    if x['path'] in allsrc and allsrc[x['path']]['sha256']!=x['sha256']:raise RuntimeError('Source changed during audit '+x['path'])
    allsrc[x['path']]=x
 oldexpected={x['path']:x['sha256'] for x in rows(P3/'COMBINED_SOURCE_FILES.csv')};oldexpected.update({x['path']:x['sha256'] for x in rows(P1/'COMBINED_SOURCE_INVENTORY.csv')})
 result=[]
 for path,x in sorted(allsrc.items()):
  actual=sha(Path(path));expected=oldexpected.get(path);result.append({'path':path,'start_sha256':x['sha256'],'previous_audit_sha256':expected,'final_sha256':actual,'status':'PASS' if actual==x['sha256'] and (expected is None or expected==actual) else 'FAIL','storage':x['storage']})
 table('SOURCE_INVENTORY.csv',list(allsrc.values()));table('SOURCE_HASH_FINAL.csv',result);ck('source hash differences',0,sum(x['status']!='PASS' for x in result))
 initial=js(O/'INITIAL_GIT_STATE.json');status=subprocess.check_output(['git','status','--short'],cwd=R,text=True);diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R,text=True);ck('tracked diff unchanged',initial['diff'],diff);ck('HEAD unchanged',initial['HEAD'],subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip());(O/'GIT_DIFF_FINAL.patch').write_text(diff);(O/'GIT_STATUS_FINAL.txt').write_text(status)
 expected_new='?? review_outputs/no_sumo_alternative_design_20261102/'
 ck('only new review added to status',set(initial['status'].splitlines())|{expected_new},set(status.splitlines()))
 # Save before/after for the audit-code assumption correction; scientific inputs untouched.
 prev=O/'revisions/attempt01_b_existing_metrics.py';now=O/'b_existing_metrics.py';(O/'revisions/B_AUDIT_FIX.diff').write_text(''.join(difflib.unified_diff(prev.read_text().splitlines(True),now.read_text().splitlines(True),fromfile=str(prev),tofile=str(now))))
 (O/'revisions/REVIEW_CORRECTIONS.md').write_text('''# 監査実装の修正と再検証

初回B監査は参照最適値が全件存在すると仮定し、NULL53入力で停止した。attempt01コードとログを保存。元CSV/JSONは変更せず、exact未確定を明示的に保持し、既存gapのNULLを保存したまま分布を照合するコードへ修正した。差分はB_AUDIT_FIX.diff、再検証はB_CHECKS.csvとFINAL_REVIEW_CHECKS.csv。不整合を0gapで埋めていない。

group推定は親IDの文字列切取りだけでなく、古典元JSONのgroup_idへ対応付け、26親・25需要groupを確認した。道路版表は同名grouped候補のrun01/run02を明記した。いずれも科学入力・既存成果の修正なし。
''')
 table('FINAL_REVIEW_CHECKS.csv',checks)
 summary={'independent_final_checks':len(checks),'final_passed':sum(x['status']=='PASS' for x in checks),'final_failed':[x['check'] for x in checks if x['status']!='PASS'],'component_checks':len(allchecks),'component_failed':sum(x['status']!='PASS' for x in allchecks),'source_files_rehashed':len(result),'hash_mismatches':sum(x['status']!='PASS' for x in result),'previous_hashes_crosschecked':sum(bool(x['previous_audit_sha256']) for x in result),'prior_artifacts_verified':js(O/'BASELINE_SUMMARY.json')['prior_artifacts_verified'],'existing_tracked_diff_bytes':len(diff.encode()),'new_regional_SUMO':0,'new_road_repairs':0,'new_full_A_or_B_evaluations':0,'metrics':metrics(t)};dump('PRESERVATION_FINAL.json',summary);print(json.dumps(summary,ensure_ascii=False))
 if summary['final_failed']:raise RuntimeError('Review failure retained; correct new artifact only')
 artifacts=[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['ARTIFACT_MANIFEST.json','FINALIZE.log']];dump('ARTIFACT_MANIFEST.json',artifacts)
if __name__=='__main__':main()
