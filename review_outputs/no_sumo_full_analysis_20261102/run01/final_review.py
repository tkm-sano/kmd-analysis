"""Seal schemas, input preservation, resource-pointer checks and all results."""
from common import *
import difflib,importlib.metadata
def main():
 t=time.monotonic();ver=js(O/'VERIFY_FULL_RUN.json');stats=js(O/'STATISTICS_VERIFICATION.json');check('Independent scientific failures',0,ver['failures']);check('Independent statistics failures',0,stats['errors']);check('Primary replay mismatches',0,stats['replay_mismatches']);check('Primary replay file count',14,stats['replay_primary_files'])
 gate=js(O/'BATCH_GATE.json')
 for name,h in gate['primary_code_hashes'].items():check('Frozen primary code '+name,h,sha(O/name))
 # Validate each persisted resource against its actual original JSON pointer.
 cache={};resource=rows(O/'B_SAVED_RESOURCES_LONG.csv');pointerchecks=0
 for x in resource:
  p=x['source_path']
  if p not in cache:cache[p]=js(use(p,x['source_sha256']))
  value=cache[p]
  for token in x['json_pointer'].split('/')[1:]:value=value[token]
  check('Resource pointer value',float(value),float(x['value']),0,x['fit_id']+x['json_pointer']);pointerchecks+=1
 # Required CSV counts and primary keys, with nullable/reference columns retained.
 pk={'A_POLICY_DECISIONS_2808.csv':(['condition_id','problem_id'],2808),'A_DELIVERY_COMPLETION_BY_STOP.csv':(['comparison_scope','condition_id','problem_id','arm','task_id'],59328),'A_MECHANISM_COMPARISON.csv':(['condition_id','problem_id','arm'],9216),'A_SUMMARY_BY_CONDITION.csv':(['condition_id'],36),'B_PLAN_REFERENCES_36800.csv':(['problem_id','config_id','measurement_rep'],36800),'B_SUMMARY_BY_SCALE_AND_METHOD.csv':(['scale','config_id'],56),'B_EXACT_REFERENCE_COVERAGE.csv':(['problem_id'],460),'C_T08_ENERGY_FULL.csv':(['condition_id'],4464),'C_BRIDGE_MASS_DC_FULL.csv':(['condition_id'],25760),'C_T09_COMPONENTS_183.csv':(['condition_id'],183)}
 schemas=[]
 for p in sorted(O.glob('*.csv')):
  if p.name in ['SOURCE_AND_OUTPUT_HASHES.csv','INPUT_HASH_FINAL.csv','FINAL_REVIEW_CHECKS.csv']:continue
  with p.open() as f:
   reader=csv.DictReader(f);cols=reader.fieldnames;count=0;nulls=collections.Counter();kinds={k:set() for k in cols};unique=set();keys=pk.get(p.name,(None,None))[0]
   for x in reader:
    count+=1
    if keys:unique.add(tuple(x[k] for k in keys))
    for k,val in x.items():
     if val in ('','null','NULL'):nulls[k]+=1;continue
     if len(kinds[k])>2:continue
     if val in ('True','False'):kinds[k].add('boolean_text')
     else:
      try:float(val);kinds[k].add('numeric_text')
      except ValueError:kinds[k].add('identifier_or_structured_text')
  schemas.append({'file':p.name,'row_count':count,'columns':cols,'csv_value_classes':{k:sorted(v) for k,v in kinds.items()},'nulls':dict(nulls),'primary_key':keys,'duplicate_primary_key':count-len(unique) if keys else None})
  if p.name in pk:check('Count '+p.name,pk[p.name][1],count);check('Unique PK '+p.name,0,count-len(unique))
 dump('DATA_SCHEMA_AUDIT.json',schemas)
 # Existing inputs and old results are checked once more at completion.
 sources={}
 for p in sorted(O.glob('*_SOURCES.json')):
  for x in json.loads(p.read_text()):
   path=x['path']
   if not Path(path).is_relative_to(O):
    if path in sources:check('Source stable across stages',sources[path]['sha256'],x['sha256'])
    sources[path]=x
 for x in rows(O/'PRIOR_ARTIFACTS_PINNED.csv'):sources[x['path']]={'path':x['path'],'sha256':x['sha256'],'storage':'PRIOR_REVIEW_ARTIFACT'}
 # Explicit road authorities remain protected even though no road calculation is run.
 network=js(P3/'NETWORK_DIAGNOSIS_SUMMARY.json')
 for k in ['N0','N1']:
  x=network[k];p=use(x['path'],x['sha256']);sources[str(p)]={'path':str(p),'sha256':x['sha256'],'storage':'PROTECTED_ROAD_NO_NEW_DIAGNOSIS'}
 final=[]
 for path,x in sorted(sources.items()):
  actual=sha(Path(path));final.append({'path':path,'initial_sha256':x['sha256'],'final_sha256':actual,'status':'PASS' if actual==x['sha256'] else 'FAIL','role':x.get('storage','SOURCE')})
 table('INPUT_HASH_FINAL.csv',final);check('Preserved input differences',0,sum(x['status']!='PASS' for x in final))
 state=js(O/'INITIAL_GIT_STATE.json');diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R,text=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();status=subprocess.check_output(['git','status','--short'],cwd=R,text=True);check('Tracked diff unchanged',state['diff'],diff);check('HEAD unchanged',state['HEAD'],head);check('No unrelated status changes',set(),set(status.splitlines())-set(state['status'].splitlines())-{f'?? {O.relative_to(R).parents[0]}/'});(O/'GIT_DIFF_FINAL.patch').write_text(diff);(O/'GIT_STATUS_FINAL.txt').write_text(status)
 environment={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':{k:importlib.metadata.version(k) for k in ['numpy','pandas','pyarrow']},'bootstrap_rng':'PCG64;multinomial cluster counts;seed20261102;10000draws','floating_tolerances':{'A_time_s':1e-9,'B_objective_s':1e-7,'C_DC_Wh':1e-7,'C_mass_kg':1e-8},'resource_scope':'wall inside main; CPU process cumulative; peak RSS per process; thread/import scopes may differ'};dump('ANALYSIS_ENVIRONMENT.json',environment)
 before=O/'revisions/before_metric_name_fix_verify_statistics.py';after=O/'verify_statistics.py'
 if before.is_file():(O/'revisions/VERIFY_STATISTICS_FIX.diff').write_text(''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile=str(before),tofile=str(after))))
 (O/'revisions/REVIEW_CHANGES.md').write_text('''# レビュー中の修正

統計検証初回は、変数metricによる関数名遮蔽のため資源記録で停止。数値不一致0の検算CSV・修正前コード・ログを保存し、audit_io.metricへ修正。VERIFY_STATISTICS_FIX.diffと修正後STATISTICS_VERIFICATION.json参照。科学入力・評価条件を変更していない。

集計CSVへ親・条件・入力ledger/table hashのscopeを追加した。T08補助R0/R1集計はdatasetだけで混ぜずmethodをcondition IDに保持し、重複軌跡参照を独立標本として読めないよう明示した。主CLASSICAL460の数値は不変。変更後に全区間・集計検証を再実行した。

資源fieldはFIT/selected state/final validation/active RESULTの範囲を区別した。Noneを0秒やhardware値で補完せず、旧CPU-matched資料は補助としてscopeを明示した。
''')
 table('FINAL_REVIEW_CHECKS.csv',CHECK)
 summary={'status':'PASS_ARITHMETIC_CONDITIONAL_INTERPRETATION','input_files_rehashed':len(final),'input_hash_mismatches':sum(x['status']!='PASS' for x in final),'prior_artifacts_preserved':len(rows(O/'PRIOR_ARTIFACTS_PINNED.csv')),'final_checks':len(CHECK),'final_failures':sum(x['status']!='PASS' for x in CHECK),'resource_json_pointer_checks':pointerchecks,'independent_scientific_checks':ver['checks'],'independent_statistics_checks':stats['checks'],'replay_primary_CSVs':stats['replay_primary_files'],'replay_mismatches':stats['replay_mismatches'],'tracked_diff_bytes':len(diff.encode()),'new_SUMO':0,'new_route_search':0,'new_QAOA':0,'existing_scientific_inputs_changed':0,'thesis_docs_changed':0,'C_complete_pack_HOLD':183,'C_footprint_FAIL_preserved':1,'B_exact_HOLD_inputs':53,'B_DC':'UNTESTED_NOT_CALCULATED','metrics':metric(t)};dump('FINAL_REVIEW.json',summary)
 report=O/'08_REPRODUCIBILITY_AND_FINAL_REVIEW.md'
 if report.is_file():
  textbody=report.read_text().split('\n<!-- FINAL_AUDIT -->')[0];report.write_text(textbody+'\n<!-- FINAL_AUDIT -->\n\n## 最終保全照合\n\n'+f"調査入力・旧成果{len(final):,}ファイルを終了時に再ハッシュし、不一致0。旧4レビューの1,047成果物を保持。保存資源の元JSON pointer照合{pointerchecks:,}件、最終検査{len(CHECK):,}項目はPASS。tracked Git差分{len(diff.encode())}bytes。主CSV14件の再実行はbyte一致。詳細はFINAL_REVIEW.jsonとINPUT_HASH_FINAL.csv。\n")
 records=[{'role':'INPUT_OR_PRIOR_RESULT','path':x['path'],'sha256':x['final_sha256'],'scope':x['role']} for x in final]
 for p in sorted(O.rglob('*')):
  if p.is_file() and p.name not in ['SOURCE_AND_OUTPUT_HASHES.csv','ARTIFACT_MANIFEST.json','FINAL_REVIEW.log']:records.append({'role':'CODE' if p.suffix=='.py' else 'NEW_OUTPUT','path':str(p),'sha256':sha(p),'scope':'CURRENT_REVIEW_ONLY'})
 table('SOURCE_AND_OUTPUT_HASHES.csv',records)
 dump('ARTIFACT_MANIFEST.json',[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['ARTIFACT_MANIFEST.json','FINAL_REVIEW.log']]);print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
