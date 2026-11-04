from common import *
import ast,zipfile

def main():
 t=time.perf_counter();required=['README.md','EXECUTIVE_SUMMARY.md','STEP2_COMPLETION_MATRIX.csv','STATISTICAL_METHODS.md','ADDITIONAL_EXPERIMENT_LOG.md','CONTRIBUTION_CONDITION_TABLE.csv','STEP3_HANDOFF.md','UNRESOLVED_ITEMS.md','REPRODUCIBILITY_REPORT.md','FINAL_AUDIT_REPORT.md','EXACT_REFERENCE_FAILURE_AUDIT.md','EXACT_REFERENCE_STATUS.csv','EXACT_REFERENCE_RECHECK_RESULTS.csv','EXACT_REFERENCE_IMPACT.md','PATH1_STATISTICAL_RESULTS.csv','PATH1_PAIRED_COMPARISONS.csv','PATH1_SUCCESS_RATE_ANALYSIS.csv','PATH1_UNCERTAINTY_ANALYSIS.md','PATH1_STATISTICAL_REPORT.md','QAOA_CONTROLLED_EXPERIMENT_DESIGN.md','QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv','QAOA_CONTROLLED_EXPERIMENT_REPORT.md','PATH1_RUNTIME_RESULTS.csv','PATH1_RUNTIME_SCOPE_COMPARISON.md','PATH1_RUNTIME_DISTRIBUTIONS.md','PATH2_SENSITIVITY_RESULTS.csv','PATH2_BOUNDARY_ANALYSIS.csv','PATH2_MODEL_UNCERTAINTY.md','PATH2_OPERATION_CONDITION_ANALYSIS.csv','PATH2_STATISTICAL_REPORT.md','PATH1_CONDITION_EVIDENCE_MATRIX.csv','PATH2_CONDITION_EVIDENCE_MATRIX.csv','STEP2_CONTRIBUTION_CONDITIONS_SUMMARY.md','NUMERICAL_VERIFICATION.csv','STATISTICAL_VALIDITY_AUDIT.md','CLAIM_EVIDENCE_MATRIX.csv','STEP2_FINAL_AUDIT.md']
 # Collect immutable inputs and record interim generated dependency versions separately.
 base=frame(O/'evidence/INPUT_HASH_BASELINE.csv',dtype=str);sources={};history=[];conflicts=[]
 for x in base.to_dict('records'):
  ck('Step1/start baseline agrees',x['status']=='PASS',x['path']);sources[x['path']]=dict(path=x['path'],start_sha256=x['sha256'],role='Step1-verified input or preserved Step1 artifact',version='baseline content SHA256')
 for p in sorted((O/'evidence').glob('*_SOURCES.csv')):
  if p.stat().st_size<3:continue
  d=pd.read_csv(p,keep_default_na=False)
  for x in d.to_dict('records'):
   path=Path(x['path']);local=path.is_relative_to(O);history.append(dict(stage=p.stem,path=str(path),used_sha256=x['sha256'],dependency_class='NEW_TRIAL_CODE_OR_INTERMEDIATE' if local else 'IMMUTABLE_SOURCE'))
   if not local:
    if str(path) in sources and sources[str(path)]['start_sha256']!=x['sha256']:conflicts.append(str(path))
    else:sources[str(path)]=dict(path=str(path),start_sha256=x['sha256'],role=x.get('role','additional original input'),version=x.get('version','SHA256'))
 ck('no immutable source version conflict',not conflicts,detail=conflicts)
 preservation=[]
 for i,x in enumerate(sources.values(),1):
  p=Path(x['path']);h=sha(p) if p.is_file() else '';preservation.append(x|dict(final_sha256=h,bytes=p.stat().st_size if p.is_file() else None,status='PASS' if h==x['start_sha256'] else 'FAIL'))
 table('SOURCE_PROVENANCE.csv',preservation);table('SOURCE_HISTORY.csv',history);table('evidence/SOURCE_PRESERVATION_CHECKS.csv',preservation)
 ck('all immutable input/source hashes preserved',all(x['status']=='PASS' for x in preservation),detail=len(preservation))
 tracked=js(O/'evidence/TRACKED_BASELINE.json');tp=[]
 for x in tracked:
  h=sha(x['path']) if Path(x['path']).is_file() else '';tp.append(x|dict(final_sha256=h,status='PASS' if h==x['sha256'] else 'FAIL'))
 table('evidence/TRACKED_PRESERVATION_CHECKS.csv',tp);ck('all tracked hashes preserved',all(x['status']=='PASS' for x in tp),detail=len(tp))
 statbase=js(O/'evidence/EXISTING_STAT_BASELINE.json');changed=[];missing=[]
 for x in statbase:
  p=Path(x['path'])
  if not p.is_file():missing.append(str(p));continue
  s=p.stat()
  if s.st_size!=x['size'] or s.st_mtime_ns!=x['mtime_ns']:changed.append(dict(path=str(p),old_size=x['size'],new_size=s.st_size,old_mtime_ns=x['mtime_ns'],new_mtime_ns=s.st_mtime_ns))
 dump('evidence/EXISTING_STAT_PRESERVATION.json',dict(files=len(statbase),changed=changed,missing=missing,scope='broader size/mtime check; environments/third-party tool dirs excluded; hashes separately for protected sources'))
 ck('broad existing-file stat preservation',not changed and not missing,detail=f'{len(statbase)} files')
 finalstatus=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=R);finaldiff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R);(O/'evidence/GIT_STATUS_FINAL.txt').write_bytes(finalstatus);(O/'evidence/GIT_DIFF_FINAL.patch').write_bytes(finaldiff)
 prefix=str(O.relative_to(R))+'/'
 def outside(b):return set(l for l in b.decode().splitlines() if not l[3:].startswith(prefix))
 startstatus=(O/'evidence/GIT_STATUS_START.txt').read_bytes();adds=sorted(outside(finalstatus)-outside(startstatus));removed=sorted(outside(startstatus)-outside(finalstatus));dump('evidence/OUTSIDE_TRIAL_GIT_CHANGES.json',dict(added=adds,removed=removed));ck('Git HEAD unchanged',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==json.loads((O/'evidence/START.json').read_text())['head']);ck('tracked diff unchanged',finaldiff==(O/'evidence/GIT_DIFF_START.patch').read_bytes());ck('outside-trial git status unchanged',not adds and not removed,detail=f'added{len(adds)} removed{len(removed)}')
 # Final interfaces and numerical keys.
 files=[]
 for p in sorted((O/'scripts').glob('*.py')):ast.parse(p.read_text());files.append(dict(path=str(p.relative_to(O)),sha256=sha(p),bytes=p.stat().st_size))
 table('CODE_SHA256.csv',files);ck('all trial scripts parse',len(files)>0,detail=len(files))
 stat=frame(O/'PATH1_STATISTICAL_RESULTS.csv');ref=frame(O/'EXACT_REFERENCE_STATUS.csv');ctrl=frame(O/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv');csummary=frame(O/'QAOA_CONTROLLED_CELL_SUMMARY.csv');p2=frame(O/'PATH2_SENSITIVITY_RESULTS.csv');rt=frame(O/'PATH1_RUNTIME_RESULTS.csv');cond=frame(O/'CONTRIBUTION_CONDITION_TABLE.csv');fig=frame(O/'FIGURE_INDEX.csv')
 ck('main data interface dimensions',len(stat)==112 and ref.exact_fraction.ne('').sum()==414 and len(ctrl)==9312 and len(csummary)==96 and len(p2)==132480 and len(rt)==9603)
 ck('97 independent learning fits per controlled cell',ctrl.groupby(['problem_id','support','initial_state','mixer','layers','method']).size().eq(97).all())
 ck('all required condition classifications used',set(cond.classification).issubset({'必要十分条件','必要条件','観測された依存関係','モデル上の仮定','未検証事項'}))
 for row in fig.to_dict('records'):
  ck('PNG and PDF figure files exist',(O/row['png']).is_file() and (O/row['pdf']).is_file(),row['png'])
 # Record visual review made with view_image and contact sheet, without claiming every page was externally peer reviewed.
 table('evidence/VISUAL_REVIEW.csv',[dict(figure=x['png'],status='PASS',review='contact sheet plus direct detailed inspection of quality, boundary, dephasing and runtime representative figures; code/CSV linkage checked',scope='internal visual QA, not independent scientific peer review') for x in fig.to_dict('records')])
 # Preserve the final audit checks and combine all stage check files. Counts are checks, never sample size.
 table('evidence/FINAL_INTEGRITY_CHECKS.csv',CHECKS);allchecks=[]
 for p in sorted((O/'evidence').glob('*_CHECKS.csv')):
  if p.stat().st_size<3:continue
  df=pd.read_csv(p,keep_default_na=False)
  if len(df):allchecks.extend([dict(stage=p.stem,**x) for x in df.to_dict('records')])
 table('NUMERICAL_VERIFICATION.csv',allchecks);assert all(x['status']=='PASS' for x in allchecks)
 claims=frame(O/'CLAIM_EVIDENCE_MATRIX.csv');start=js(O/'evidence/START.json');completion=frame(O/'STEP2_COMPLETION_MATRIX.csv');runtime_summary=frame(O/'PATH1_RUNTIME_SUMMARY.csv');newids=ref[(ref.old_exact_available==False)&ref.exact_fraction.ne('')].problem_id.tolist()
 audit=f'''# Step 2 総合監査

**総合判定：TRIAL COMPLETE。研究解釈CONDITIONAL。Task2-1〜2-6は全て作業上COMPLETE。**

このtrialは計画だけではなく、元入力照合、既存統計評価、追加有理数LP、追加QAOA統制、CPU時間、T08/T09感度・走行条件、図表、根拠台帳を実行した。HOLD解消や量子優位性を完了条件にしていない。

## 実行結果と根拠

- Task2-1：旧欠測53はR4=21/R5=32、全てoptimal終了後のExactBound/Witness微小不一致。53の元LP係数/索引/solution/log、全large148モデル、234小規模全列挙、78保存128bit DPの入力/整数scale/実行binary/source/witnessを監査。148を独立有理数LPで再検査し61の等値証明（既存54＋新規7）。新規={', '.join(newids)}。参照414、残46HOLD。旧407への反例0。41は保存MIP等値のみの条件付き証拠で外部VIPRなし。上下界の証拠強度を分離した。
- Task2-2：B460入力×8設定×10測定=36,800、PKと原NPZ/測定JSONを照合。主greedy正改善0件、全best可行。2対照対応73,600行、input設定対照7,360行、summary112行、interval672行。mean/median/SD/IQR/min/max/取得率/gapと分母を保存。exact414/欠測46を分離し旧407結果も残した。測定10repを独立学習としない。
- Task2-3：小規模3診断input、96cell、97学習start/cell、10測定/fit×8192shots、9,312fit/93,120測定。全条件を保持。R1_020で制限支持最適取得0、全支持でも初期/mixer/layer/最適化に依存。同角度脱位相4,656診断、測定予算感度37,248行。主greedyに正改善はない。direct expm/確率正規化/全支持可行性/shot histogramからのbest再構成を照合。raw std丸め77fitは目的分数一致からpublic SD0へ正規化、raw実験保持。
- Task2-4：旧3680fit/初期460/近似920をscope別集計、新fit9312と新greedy291の計9,603pipeline時間を計測。1thread/同core条件、warmup/pilot別、wall/CPU/内訳。Q/dephasedは対応するがgreedy1出力対Q10出力等の差を明記。H_plan/QPU/compiled/物理資源は未確定。
- Task2-5：旧C460trajectory×2Crr、144parameter case=132,480行、T09共通入力162行。T08主のb≈5.448297kg、u*≈.877094、V*≈3.193156、DC総和比.412579/.413590%を検証。共通fixed/追加unknown/u/V/geometryと運転covariate依存を分析。920のDC(m)正傾きを1000〜1250kgに確認し、delta=bでmass/DC差ゼロ。T09完成packはNULL。
- Task2-6：両経路の条件台帳{len(cond)}行、claim台帳{len(claims)}行を分類。定義/モデル内同値と新しい観測依存を区別。Step3へ使用できる数値・限定・根拠を保存し、統合考察自体は実行していない。

NUMERICAL_VERIFICATION.csvは今回{len(allchecks):,}検査行、最終FAIL0。検査行数は独立実験数ではない。CLAIM_EVIDENCE_MATRIX.csvのFAILはQPU時間読み替え・完成pack断定・任意成功基準という棄却解釈を示し、計算失敗を隠してPASSへ変えたものではない。

## 統計と解釈

主DeltaJはgreedy−Q。初期差は補助、最適参照は共通J*。input内10rep→input等重み、25group感度と固定fit測定感度を分離。group区間は実配送母集団の校正済みCIではない。ゼロ改善bootstrapの[0,0]を将来確率0とせず、Wilsonと条件付き測定stream上限を併記。新97はexact期待値・random-start条件の学習反復で、旧10測定とは別。

mirror support最小=初期は全460で新しい独立matching DPを検算したため、支持内改善余地がない不成立条件として使用可。full supportだけでは初期状態/最適化/有限shotsの条件を満たさない。期待値の干渉差をsampled-best対古典近似の改善へ置換しない。

T08モデル計算と材料proxy/仮定、T09既知subtotalとunknown BOM、CPU実測とシミュレーション・bootstrap感度を区別。zero effectはdelta=b、任意0.25%は成功基準不採用。旧Aの時間窓/定時率、旧Cの速度460と新B460、B100顧客と旧99を混合しない。実材料の量子改善・実道路運用改善・実機量子優位は未実証。

## 保全と版

開始HEAD `{start['head']}`、remoteは`https://github.com/tkm-sano/kmd-analysis.git`。Step1成果物とその読取元を開始hashで照合し、追加元LP/log/solution/DP/sourceを読取前にpinした。SOURCE_PROVENANCE.csvの旧入力/旧trial/コード{len(preservation):,}件は全て終了hash一致、Git追跡{len(tp)}件も全一致。広い既存{len(statbase):,}ファイルのsize/mtime検査は変更{len(changed)}・欠落{len(missing)}（全バイト監査ではなく環境/第三者ツールを除外）。trial外Git変化追加{len(adds)}/除去{len(removed)}、tracked diffは開始時と同一。

新trial内の中間派生物/コードの使用時hashはSOURCE_HISTORY.csv、最終コード版はCODE_SHA256.csv。生成中に更新した派生表を旧研究ファイルの保全対象と混同していない。旧データ・コード・既存trial・DOCXを変更せず、commit/push/公開/正式原稿反映を行っていない。新規SUMOは0、追加計算は本trialで事前仕様/数値/資源gateを固定して実行した範囲だけ。

## 成果物と残課題

必要37ファイルと4図ディレクトリを確認。CSV由来図は{len(fig)}組のPNG/PDF、FIGURE_INDEX.csvに出典/再生成scriptを記録。画像の内部表示点検とCSV対応を確認したが、外部第三者査読を受けたとはしない。

HOLDはUNRESOLVED_ITEMS.mdのH01〜H13。厳密46、保存MIP外部証明41、旧staged8予算、未見入力/学習、H_plan/総計画時間、QPU/compiled、raw-invalid一部、材料full-cell、未知BOM、量子材料改善、道路/実車/B→DC、tail/除外物理、正式採用を保持する。旧道路受入FAIL・T09_ROW183対向FAILも維持。

Step3はSTEP3_HANDOFF.mdの確定結果と限定を使って統合考察を開始できる。本成果物は独立した1回のStep2 trialであり、正式採用・研究成果への統合・原稿への反映は未実施。
'''
 text('FINAL_AUDIT_REPORT.md',audit);text('STEP2_FINAL_AUDIT.md',audit.replace('# Step 2 総合監査','# Step 2 完了監査',1))
 for n in required:ck('required deliverable exists',(O/n).is_file() and (O/n).stat().st_size>0,n)
 for d in ['PATH1_STATISTICAL_FIGURES','QAOA_CONTROLLED_EXPERIMENT_FIGURES','PATH1_RUNTIME_FIGURES','PATH2_FIGURES']:ck('required figure directory populated',bool(list((O/d).glob('*.png'))),d)
 # Final integrity checks include file presence assertions, merge once without double-counting this stage.
 table('evidence/FINAL_INTEGRITY_CHECKS.csv',CHECKS);others=[x for x in allchecks if x.get('stage')!='FINAL_INTEGRITY_CHECKS'];allfinal=others+[dict(stage='FINAL_INTEGRITY_CHECKS',**x) for x in CHECKS];table('NUMERICAL_VERIFICATION.csv',allfinal)
 dump('evidence/FINAL_VERIFICATION.json',dict(overall='TRIAL COMPLETE',interpretation='CONDITIONAL',tasks_complete=6,required_files=len(required),figure_directories=4,figure_pairs=len(fig),scientific_checks=len(allfinal),scientific_failures=0,protected_sources=len(preservation),tracked_files=len(tp),broad_stat_files=len(statbase),preservation='PASS',B_inputs=460,B_plans=36800,old_exact=407,additional_proved=7,audited_exact=414,unproved=46,controlled_learning_fits=9312,controlled_measurement_reps=93120,controlled_learning_reps_per_cell=97,T08_T09_DC_rows=132480,T09_common_rows=162,Step3_executed=False,formal_adoption=False,completed_at=datetime.datetime.now().astimezone().isoformat(),wall_s=time.perf_counter()-t))
 # Reconcile the audit text count with final file-interface checks.
 for fn in ['FINAL_AUDIT_REPORT.md','STEP2_FINAL_AUDIT.md']:
  p=O/fn;s=p.read_text().replace(f'今回{len(allchecks):,}検査行',f'今回{len(allfinal):,}検査行');p.write_text(s)
 # Include every output except the manifest itself; timings do not influence scientific pass/fail.
 manifest=[]
 for p in sorted(O.rglob('*')):
  if p.is_file() and p.name!='OUTPUT_SHA256_MANIFEST.csv':manifest.append(dict(path=str(p.relative_to(O)),sha256=sha(p),bytes=p.stat().st_size))
 table('OUTPUT_SHA256_MANIFEST.csv',manifest)
 print(json.dumps(js(O/'evidence/FINAL_VERIFICATION.json'),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
