"""Post-run artifact audit/report; not part of registered trial code or stopping."""
from pathlib import Path
from collections import Counter
import json
import subprocess
import xml.etree.ElementTree as ET
from jsonschema import Draft202012Validator
from kmd_toc.comparison_v1.contract import ROOT,read,digest,atomic

base=ROOT/'docs/research/termination_rules_20261116_v1'
root=ROOT/'output/toc_delivery/termination_rules_20261116_v1/scales_02'
manifest=read(root/'REGISTERED.json');rows=read(root/'ALL_RESULTS.json');telemetry=read(root/'TELEMETRY.json');audit=read(root/'FINAL_AUDIT.json')
assert len(rows)==15 and all(r['execution_state']!='NOT_STARTED' for r in rows),'ALL_15_REQUIRED'
schema=read(base/'RESULT_SCHEMA.json');validator=Draft202012Validator(schema)
for run in manifest['runs']:validator.validate(read(root/'runs'/run['run_id']/'RESULT.json'))
atomic(base/'SCHEMA_VALIDATION.json',{'pass':True,'executed_results_checked':15,'schema_sha256':digest(base/'RESULT_SCHEMA.json')})

baseline=read(base/'BASELINE.json');before=baseline['files'];preserved=[]
for name,value in {**before,**read(base/'OLD_OUTPUT_HASHES.json')}.items():
    expected=value['sha256'] if isinstance(value,dict) else value
    actual=digest(ROOT/name) if (ROOT/name).exists() else None
    preserved.append({'file':name,'before_sha256':expected,'after_sha256':actual,'unchanged':expected==actual})
exception=read(base/'PRETRIAL_UNRELATED_CHANGE.json')
changed=[x for x in preserved if not x['unchanged']]
pretrial_only=bool(changed) and all(x['file']==exception['file'] and x['before_sha256']==exception['initial_baseline_sha256'] and x['after_sha256']==exception['preserved_current_sha256'] for x in changed) and exception['all_registered_versions_equal']
preservation_ok=not changed or pretrial_only
old_results_unchanged=all(x['unchanged'] for x in preserved if x['file'].startswith(('output/','docs/research/comparison_design_20261116_v1/')))
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head==baseline['HEAD'],'HEAD_CHANGED'
atomic(base/'PRESERVATION_AFTER.json',{'pass':preservation_ok,'strict_all_baseline_files_unchanged':not changed,'pretrial_unrelated_change_preserved':pretrial_only,'exception_evidence':'PRETRIAL_UNRELATED_CHANGE.json','HEAD_before':baseline['HEAD'],'HEAD_after':head,
    'scope':'all initial source/config/scripts/old-report files in BASELINE plus critical old result/manifest/snapshot files; not a claim to rehash all 12833 historical output files',
    'files':preserved})
(base/'GIT_STATUS_AFTER.txt').write_text(subprocess.check_output(['git','status','--porcelain=v1','-uall'],cwd=ROOT,text=True))

q=[]
for scale in ('S1','S2','S3'):
    items=[t for t in telemetry if t['scale']==scale and t['method']=='D']
    calls=sum(t['quantum_call_attempts'] for t in items)
    q.append({'scale':scale,'quantum_calls':calls,'total_starts':calls,'training_attempts':sum(t['training_attempts'] for t in items),
        'training_shots_observed':sum(t['observed_training_shots'] for t in items),
        'training_shots_ceiling':calls*80*10000,'final_shots_observed':sum(t['observed_final_shots'] for t in items),
        'final_shots_planned_for_registered_calls':calls*10000,
        'max_evaluations_per_call_observed':max(t['max_attempted_evaluations_per_call_start'] for t in items),
        'optimizer_cache_hits':sum(t['counts'].get('quantum_optimizer_cache_hits',0) for t in items),
        'training_failures':sum(t['training_failures'] for t in items),
        'accounting_complete':all(t['shots_accounting_complete'] for t in items)})
atomic(base/'QUANTUM_ACTUAL_VS_PLANNED.json',q)

stage=Counter();cp=[]
for t in telemetry:
    for e in t['stage_terminations']:
        if e['event']=='CP_end':cp.append(e)
        stage[e['event']+':'+str(e.get('algorithm_termination',e.get('reason',e.get('status',e.get('termination')))))]+=1
max_threads=0
for run in manifest['runs']:
    path=root/'runs'/run['run_id']/'RESOURCE_SAMPLES.jsonl'
    if path.exists():
        for line in path.read_text().splitlines():
            sample=json.loads(line)
            for b in sample['branches']:
                for p in b['processes']:max_threads=max(max_threads,p['threads'])
unit=ET.parse(base/'UNIT_RELEASE.xml').getroot();suites=unit.findall('testsuite')
unit_pass=all(int(s.get('failures','0'))+int(s.get('errors','0'))==0 for s in suites)
unit_count=sum(int(s.get('tests','0')) for s in suites)
checks={'registered_trial_audit':audit['pass'],'registered_current_source_matches':audit['current_source_matches'],
    'snapshot_hash_matches':digest(root/'SOURCE_SNAPSHOT.tar.gz')==manifest['snapshot_sha256'],
    'schema_checked':True,'preservation':preservation_ok,'new_unit_tests':unit_pass,
    'all_15_procedures_completed':all(r['execution_state']=='NORMAL' for r in rows),'main_stays_nonexecutable':read(base/'MAIN_MANIFEST.json')['executable'] is False}
atomic(base/'FINAL_AUDIT.json',{'pass':all(checks.values()),'checks':checks,'actual_trials':15,'adoptable':sum(r['adoptable'] for r in rows),
    'strict_all_baseline_files_unchanged':not changed,'pretrial_unrelated_change_preserved':pretrial_only,'old_regression_all_passed':False,'old_regression_evidence':'REGRESSION_01:127 passed/2 failed; isolated:1 passed/1 legacy15s timeout reproduced; legacy source hashes unchanged',
    'stage_termination_counts':dict(stage),'CP_client_calls':len(cp),'max_CP_client_conflicts':max(e['conflicts'] for e in cp),
    'max_process_threads_observed':max_threads,'analysis_code_sha256':digest(Path(__file__))})
complete=all(checks.values())
status={'experiment_id':manifest['experiment_id'],'non_time_rules_configuration_complete':True,'implementation_complete':True,
    'required_functional_validation_complete':complete,'actual_scale_attempts':15,'adoptable_attempts':sum(r['adoptable'] for r in rows),
    'failures_preserved':sum(not r['adoptable'] for r in rows),'unfinished_actual_scale_attempts':sum(r['execution_state'] in ('NOT_STARTED','USER_CANCELLED','EXTERNAL_INTERRUPTION') for r in rows),
    'main_start_allowed':False,'main_started':False,'R_a_fixed':False,'h_D_adopted':False,
    'remaining_before_main':['new-setting variance and cost measurement','adopt R, precision and analysis/multiplicity conditions; formal seed/order/A reference registration'],
    'old_results_unchanged':old_results_unchanged,'strict_all_baseline_files_unchanged':not changed,'pretrial_unrelated_change_preserved':pretrial_only,'README_unchanged':next(x['unchanged'] for x in preserved if x['file']=='README.md'),
    'main_manifest':'MAIN_MANIFEST.json','scale_manifest':str((root/'REGISTERED.json').relative_to(ROOT))}
atomic(base/'COMPLETION_STATUS.json',status)

report=['# 非時間終了規則の実装・検証報告', '',
'非時間終了規則の設定・実装・必要な動作確認は'+('完了した。' if complete else '未完了である。')+'本実験は未開始であり、R・h_D等は採択していない。', '',
'対象は凍結A_rule_v1+FCFS、有向CWのB、OR-Tools RoutingのC、限定Huang AOA+車両日列のD、同じ最大3群の順列を列挙するD_CLASSICAL_REPLACEMENTである。S1/S2/S3すべてを対象とした。', '',
'|手法/段階|採用値・終了規則|根拠・適用範囲|', '|---|---|---|',
'|A|最大V受理改善、10000候補、または有限近傍の無改善1巡|凍結規則を変更せず、既存の有限構造を利用。1枝=1試行|',
'|B|全N(N−1)有向savings走査→共通完成|既存構築の自然な有限完了、各枝1回|',
'|C|max(256,16N) CustomLimit確認。S1/S2/S3=16000/32000/64000|初期/局所/LNSに共有する操作予算。GLSと割当自由度を維持。初期可行候補を保全|',
'|共通CP|内部SAT solve衝突256、改善解callback8、または有限整数探索完了|全体累積衝突256とは異なる。NO_RESTART/単一worker、time/dtime制限なし。検証済みincumbent保全|',
'|D|2round×元CWルート、各call総start1、p=2、最大3群、目的評価最大80、tol0.001|旧非時間設定を継承。80は初期を含む評価上限、80最適化反復ではない。失敗/空/重複でも次の有限IDへ進む|',
'|古典置換|同じ最大3群の全順列≤6、同じ2roundと後段|量子省略対照とは別。実行時間を人為的に合わせない|',
'|車両日/列生成|全車両に単便+2方向被覆隣接パターン（≤3VK試行）、40round、20新規列/round|旧時間打切りprefixを有限カタログへ変更。割当を固定しない。閉包/最適性の範囲は宣言pool内|',
'|LP/IP|LP max(1000,4×(行+列))simplex反復、IP4V節点/solve（40/80/160）|規模に基づく公開仕事量。内部routineの全操作数や実時間上界の保証ではない|', '',
'詳細な位置・単位・失敗経路・API根拠はSTOPPING_RULES.md、STOPPING_AUDIT.md、COUNTER_DEFINITIONS.jsonである。値を旧150秒へ近づけたり勝者を選ぶために調整していない。', '',
'外側240秒、native150秒、A wrapper180秒/計画150秒、Routing0.5配分、LNS既定時間、HiGHS/CP時間制限、残り時間による候補/round削減、全体残り時間での省略を新経路で撤廃した。SAT inprocessing/symmetry等の内側dtime依存前処理も無効化した。旧モードは保全している。', '',
'物理条件（1地点1単位、60/便、最大2便、積込1800秒、地点作業120秒、8〜20時、有向Route OD、全地点/便接続/バース排他）と最終二重検査を維持した。4物理コア、内部4枝各1コア/native1thread、RSS32GiB、A AS4GiBも維持した。pollは監視のみである。', '',
'T_kind=comparison_parent_wall_including_process_setup_v1を維持した。入力hash/読込からfresh child/import、全枝終了、転送・選択・親二重検査までを含む。計時内テレメトリI/Oと共有NFS/page cacheの影響を含み、ソルバー単体時間ではない。', '',
'## 実規模15試行の実測', '',
'単位はD=km、W=min、T=秒である。各cell1試行は運用確認件数であり、統計的Rの採用値ではない。', '',
'|規模|手法|終了/計画/採用|D|W|T|', '|---|---|---|---:|---:|---:|']
for r in rows:report.append(f"|{r['scale']}|{r['method']}|{r['execution_state']}/{r['plan_state']}/{'採用' if r['adoptable'] else '不採用'}|{r['D'] if r['D'] is not None else 'null'}|{round(r['W'],4) if r['W'] is not None else 'null'}|{round(r['T_attempt'],3)}|")
report+=['',f"15試行中{sum(r['adoptable'] for r in rows)}採用、未完了{status['unfinished_actual_scale_attempts']}、失敗{status['failures_preserved']}である。全体試行の終了理由はCONSTRUCTION_COMPLETE、内側のWORK_BUDGET_REACHED/SEARCH_EXHAUSTED/native statusと全カウンタはTELEMETRY.jsonに別記した。全枝成功を新条件にせず、全枝回収後の距離0.1m→W秒→branch IDで採択した。",'',
f"試行T合計は{sum(r['T_attempt'] for r in rows):.3f}秒、観測された最大tree RSS合計は{max(r['sampled_tree_peak_RSS_KiB'] for r in rows)/1024:.1f}MiB、プロセスthread数の観測最大は{max_threads}であった。CPU・各枝HWM・候補由来もRESULT.jsonに保存した。",'',
'## 実測shotsと計数', '',
'訓練はone-hot tensorからの確率に対するNumPy multinomial(10000)の有限標本平均であり、厳密期待値ではない。最終抽出はQiskit2.1.1 Statevector.sample_counts(10000)である。各成功sampleで実際のsum(counts)=10000を記録した。訓練tensor/最終回路/状態検査tensor/samplingを別計数し、SciPyの初期評価・cache hitも区別した。', '',
'|規模|量子call/総start|実評価|訓練shots実測|訓練shots上限予定|最終shots実測=予定|', '|---|---:|---:|---:|---:|---:|']
for x in q:report.append(f"|{x['scale']}|{x['quantum_calls']}|{x['training_attempts']}|{x['training_shots_observed']:,}|{x['training_shots_ceiling']:,}|{x['final_shots_observed']:,}|")
report+=['','QUANTUM_ACTUAL_VS_PLANNED.json、各枝work.jsonl、roundXX_routeYYY.jsonが証拠である。内部call数やshotsを外側Rへ加算しない。restarts=1は初回を含む総1startである。', '',
'## 検証・保全・適用範囲', '',
f'最終の非時間検証{unit_count}件が通過した。人工fixture25試行は修正前5失敗を保全し、修正後20件は採用された。最終small_05は5手法全て通過した。修正と未起動scales_01登録の撤回をAMENDMENTS.json/WITHDRAWN.jsonへ保存した。実規模はscales_02の15試行だけであり、成功を得るための追加試行は行っていない。', '',
'既存回帰は127通過/2失敗であった。単独再確認では旧10秒invalid-plan試験は通過、旧15秒置換対照の時間切れは再現した。旧ソースを変更せず証拠を残しており、全回帰通過とは記載しない。', '',
'既存README/AGENTS/未コミット差分、凍結入力/OD、旧manifest/結果/確認失敗記録を保全した。PRESERVATION_AFTER.jsonで照合した。開始時と比べhuman_comparison_v1/session.pyのhashが1件異なるが、変更は最初の小規模登録前であり、全snapshotと現行版は一致する。変更元は特定しておらず、本作業の編集対象でも実行経路でもない。現行ファイルを上書きせず保全し、開始時hashとPRETRIAL_UNRELATED_CHANGE.jsonを残した。全baselineファイルが不変だったとは記載しない。HEADは変更せずcommit/pushしていない。再現コマンドはREPRODUCE.mdにある。', '',
'## 残る事項', '',
'本実験前には、この新設定で分散・費用を測定し、R・h_D等の精度/検出力・比較群/多重性・解析条件・正式seed/順序/A時間参照を固定する必要がある。旧分散/費用は流用しない。S1/S2/S3は全て本実験範囲とし、今回Rやh_Dの採択、Aの事業者代表性再検証を完了条件へ追加していない。MAIN_MANIFEST.jsonは非実行である。', '',
'既存D/W目標への記述用照合はINHERITED_TARGET_OBSERVATIONS.jsonである。観測できた内部候補時刻は枝単位で保存した。厳密な親側の初到達時刻は未観測でありnullとした。最終検査後の時刻は上界として区別し、終了Tを初到達へ置換していない。未達を到達扱いにしていない。', '',
'規定の有限処理を終えたことは、最適性・真の収束・10000shots/80評価の十分性・実事業者への改善を証明したことを意味しない。']
(base/'FINAL_REPORT.md').write_text('\n'.join(report)+'\n')
validation=(base/'VALIDATION.md').read_text().split('\n最終監査:')[0]
(base/'VALIDATION.md').write_text(validation+'\n最終監査: '+json.dumps(status,ensure_ascii=False)+'\n\n全15行のD/W/T、実測shotsと費用はFINAL_REPORT.mdおよびscales_02/RESULTS.csvに保存した。厳密な全baseline不変と、無関係な登録前変更を保持した保全判定を区別する。根拠はPRETRIAL_UNRELATED_CHANGE.jsonである。\n')
print(json.dumps({'complete':complete,'adoptable':status['adoptable_attempts'],'trials':15,'total_T_s':sum(r['T_attempt'] for r in rows),'quantum':q},ensure_ascii=False))
