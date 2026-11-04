from pathlib import Path
import json,csv,hashlib,datetime,subprocess,os
import pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
required=['RQ_INDICATOR_ALIGNMENT.md','POLICY_CONSISTENCY_AUDIT.md','PATH1_COMPARISON_BASELINES.md','PATH1_METRIC_SPECIFICATION.md','PATH1_REFERENCE_COVERAGE.csv','PATH1_RUNTIME_SCOPE_INVENTORY.csv','PATH1_RESOURCE_SCOPE.md','PATH1_TIME_CONDITION_SPEC.md','PATH2_MODEL_ROLE_SPECIFICATION.md','PATH2_INPUT_PARAMETER_DICTIONARY.csv','PATH2_BOUNDARY_DEFINITION_TABLE.csv','CONTROLLED_DC_SCOPE_AUDIT.md','PATH1_STATISTICAL_ANALYSIS_PLAN.md','PATH2_UNCERTAINTY_ANALYSIS_PLAN.md','STEP2_ADDITIONAL_EXPERIMENT_CANDIDATES.csv','README.md','SOURCE_PROVENANCE.csv','STEP1_DECISION_RECORD.md','STEP1_COMPLETION_MATRIX.csv','STEP2_HANDOFF.md','STEP1_FINAL_AUDIT.md']
checks=pd.concat([pd.read_csv(O/'evidence'/n) for n in ['NUMERICAL_CHECKS.csv','SUPPLEMENT_CHECKS.csv','HISTORY_CHECKS.csv']],ignore_index=True);assert checks.status.eq('PASS').all()
src=pd.read_csv(O/'SOURCE_PROVENANCE.csv',keep_default_na=False);pres=[]
for x in src.to_dict('records'):
 p=Path(x['path']);h=sha(p) if p.is_file() else '';pres.append({'path':str(p),'start_sha256':x['sha256'],'final_sha256':h,'status':'PASS' if h==x['sha256'] else 'FAIL'})
pd.DataFrame(pres).to_csv(O/'evidence/SOURCE_PRESERVATION_CHECKS.csv',index=False)
tracked=json.loads((O/'evidence/TRACKED_HASH_BASELINE.json').read_text());tr=[]
for x in tracked:
 h=sha(x['path']) if Path(x['path']).is_file() else '';tr.append({**x,'final_sha256':h,'status':'PASS' if h==x['sha256'] else 'FAIL'})
pd.DataFrame(tr).to_csv(O/'evidence/TRACKED_PRESERVATION_CHECKS.csv',index=False)
base=json.loads((O/'evidence/EXISTING_FILE_STAT_BASELINE.json').read_text());changed=[];missing=[]
for x in base:
 p=Path(x['path'])
 if not p.is_file():missing.append(x['path']);continue
 s=p.stat()
 if s.st_size!=x['size'] or s.st_mtime_ns!=x['mtime_ns']:changed.append(dict(path=str(p),old_size=x['size'],new_size=s.st_size,old_mtime_ns=x['mtime_ns'],new_mtime_ns=s.st_mtime_ns))
dump('evidence/EXISTING_FILE_STAT_CHECK.json',{'files_checked':len(base),'changed':changed,'missing':missing,'scope':'size and mtime only for broader discovery; hashes separately for sources/tracked; third-party tools/environments excluded'})
status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=R);diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R);(O/'evidence/GIT_STATUS_FINAL.txt').write_bytes(status);(O/'evidence/GIT_DIFF_FINAL.patch').write_bytes(diff)
rel=str(O.relative_to(R))+'/'
def outside(b):return set(l for l in b.decode().splitlines() if not l[3:].startswith(rel))
before=(O/'evidence/GIT_STATUS_START.txt').read_bytes();added=sorted(outside(status)-outside(before));removed=sorted(outside(before)-outside(status));dump('evidence/OUTSIDE_TRIAL_GIT_CHANGES.json',{'added':added,'removed':removed})
safe=all(x['status']=='PASS' for x in pres+tr) and not changed and not missing and diff==(O/'evidence/GIT_DIFF_START.patch').read_bytes() and not added and not removed
# Cross-condition audit: retained scientific FAIL is distinguished from execution failures.
rows=[]
for num,item,status_,reason in [
(1,'RQと指標','PASS','RQ0/1/2/Iの二経路対応を固定。正式採用文面H01は別'),
(2,'量子/古典対照','CONDITIONAL','近似920原経路・初期460・厳密407を確認。現行予算H02'),
(3,'実測/推定/モデル値','PASS','CPU工程実測、モデル質量/DC、proxy入力、未計測QPUを分離'),
(4,'系列の分離','PASS','旧A時間窓、新B460、旧C460、B100/旧99を分離'),
(5,'T08/T09部材仮定','PASS','主/補完・固定/幾何・未知BOMを辞書/境界へ'),
(6,'完成pack実証を主張しない','PASS','T09全183NULL、T08仮定。T09_ROW183既存FAIL保持'),
(7,'Controlled-DC範囲','CONDITIONAL','同一軌跡/2Crr/正値化/除外を確認。道路/末端/実車はH11/12'),
(8,'統計観測単位','PASS','25group26parent460input8config10測定rep。49点独立化しない'),
(9,'追加実験の研究目的','PASS','E1/E3/E2/E4/E5と必要性・pilot gateを指定'),
(10,'未検証接続の断定なし','PASS','量子材料改善と実道路運用は考察後段HOLD')]:rows.append(dict(item=num,audit=item,status=status_,reason=reason))
pd.DataFrame(rows).to_csv(O/'CROSS_CONSISTENCY_AUDIT.csv',index=False)
a=json.loads((O/'evidence/AUDIT_SUMMARY.json').read_text());su=json.loads((O/'evidence/SUPPLEMENT_SUMMARY.json').read_text());hi=json.loads((O/'evidence/HISTORY_SUMMARY.json').read_text());head=json.loads((O/'evidence/START.json').read_text())['head'];ratio=pd.read_csv(O/'evidence/C_ENDPOINT_RATIO_READBACK.csv');versions=json.loads((O/'evidence/MANUSCRIPT_VERSIONS.json').read_text())
root=next(x for x in versions if Path(x['path']).name=='tmp_RsrchMstrDc_1026_results_integrated.docx');v7=next(x for x in versions if Path(x['path']).name=='v07_results_integrated.docx');textsame=(O/root['text_output']).read_text()==(O/v7['text_output']).read_text()
report=f'''# Step 1 最終監査

**作業上COMPLETE、総合CONDITIONAL。** Task1-1〜1-5の全成果物を保存し、Step2を開始できる評価設計を具体化した。HOLDの解消、正式採用、Step2の実行は完了条件としない。

## 入力と版

開始HEAD `{head}`。Sの3アルゴリズム群は保存PROTOCOL.json/SOURCE_SNAPSHOTとhashで固定。主数値はPの11月2日全件CSVを元NPZ/測定/証明へ再接続。Tの11月4日統合trialは参照資料として再検査した。材料モデルはT8/run02、T9/run01、BR/run01、Controlled-DCは凍結JSONとhash保護kernel。SOURCE_MAP.mdに実在絶対パス、SOURCE_PROVENANCE.csvに{len(src):,}入力・コード・既存成果の版/hash/サイズ/時刻を保存した。

ルート統合DOCX SHA256は`{root['sha256']}`。v07との抽出全文（表内含む）一致={textsame}、バイトhash一致={root['sha256']==v7['sha256']}。revisedとT/THESIS_TRIALも別候補として読取。最新trialを正式版と誤認していない。AGENTS.mdは祖先とrepo内（環境・第三者ツール除外）に該当なし。evidence/AGENTS_DISCOVERY.json参照。

## 今回の独立検査

計{len(checks):,}件の監査行は全PASS（元NPZ36,800経路検算など一部は1行へ集約しており、行数を試行数としない）。主検査{a['checks']:,}、補足{su['checks']:,}、履歴{hi['checks']:,}。既存trialの検査件数を今回の検査件数に流用していない。

- Bの460元NPZ、3,680保存測定原本、36,800計画の経路/分数目的/順列/216PE/帰庫制約を照合。不一致0、保存best可行36,800。float CSVとの差最大{a['B_float_csv_max_error_s']:.3g}秒は表示/parse精度の差で、効果判定は元Fraction。
- B規模は3/4/5/25/100/125、入力78/78/78/78/78/70。8設定×10測定repを確認。厳密参照407、未証明53（R4=21、R5=32）。53すべての元terminationはEXACT_BOUND_WITNESS_MISMATCH。単なる未保存や時間切れとは扱わず、近似値/下界で補完しない。
- 古典近似2法×460=920原経路のinput hash・目的分数・可行性・共通初期経路を検算。古典初期の上流460RESULTと時間の転記も確認。初期は3構成＋relocate/有向reversal最大3sweep。初期差と近似差・厳密参照を区別。
- T/PATH1_INPUT_SEED_STATISTICS.csvの3,680行を平均/SD/min/max/nから再集計し一致。36,800独立標本ではない。学習済みfitの10測定repである。既存group bootstrapコードも読取確認し、新規区間計算はしていない。
- 旧Aの元入力/古典/量子結果へ接続し78入力・取得64・36政策/2,808行を確認。時間窓ありの履歴として保持、定時率を今回の主指標にしていない。
- T08式からLP96.14565479871602kg、S90.6973573836391kg、差{a['T08_mass_saving_kg']:.15g}kg、u境界{a['utilization_boundary']:.15g}、V境界{a['voltage_boundary_V']:.15g}Vを再現。モデル計算・proxy・仮定であり完成品の実測ではない。
- T09既知8成分を全183条件×8=1,464件で独立算術照合、完成pack全NULLを確認。B015はT09_ROW031/032、B051は103/104。既知差9.722608121107783kg/5.977891152148871kgを元行から確認。ROW183の全面対向FAILは保持。
- C古典460軌跡の保存hashを確認し、代表1軌跡の2Crr×LP/Sを凍結kernelで軽量照合。全軌跡の新規物理再計算はしていない。端点の保存電力量を対応再集計し、総和比lower={ratio.iloc[0]['total_weighted_saving_percent']:.12g}%、upper={ratio.iloc[1]['total_weighted_saving_percent']:.12g}%を確認。49点感度45,080行のPK/範囲/端点も確認。

## 横断整合性

CROSS_CONSISTENCY_AUDIT.csvの10項目はPASS/CONDITIONALで整理。旧研究にあるFAIL（地域道路受入・T09全面対向・旧主方針の残存）を今回の算術検査PASSで消去していない。

主比較はΔJ=古典近似JC−JQ、greedy adjacentを主、random swap別対照、初期補助、J*共通参照。exact Fractionに基づくεJ=0。古典は初期incumbent保持、Q主保存値はraw bestという出力規則差を明示。現行8設定の予算統制はHOLD。τtotal≤Hplanは数式を定義したがHplan数値を設定せず、32,400秒を計算締切にしない。CPU計測をQPUへ換算しない。

T08主/T09構造補完、b/deltaの部材を分離。T08の固定部材をT09へ再加算しない。同一軌跡mass置換で、総仕事の正値化・branch補正を保持。約0.413%は総電力量比、個別率平均とは別。49点やCrr条件を独立nにしない。

## 未解決と引継ぎ

HOLD_REGISTER.mdのH01〜H12：正式採用版、現行8予算、厳密53、総時間/Hplan、compiled/QPU、学習seed、raw invalid一部、材料full-cell適格性、未知BOM、量子材料改善、実道路/B→DC、末端/除外物理。既存数値の算術PASSはこれらの実証を意味しない。

既存有限cohort記述を主に、Step2ではJC対応差、中央値/SD/IQR、測定乱数・需要group感度を分離、規模/設定/欠測層を示す。T08/T09は感度・構造不確実性を主とする。新規実験優先はE1支持統制→E3時間再計測→E2証明53→E4共通モデル感度→E5保存走行条件。pilotの回数は診断用で全量実験の妥当回数を確定したものではない。詳細と実行gateはSTEP2_HANDOFF.md/候補CSV。

## 保全・境界

読取元{len(src):,}件の開始時/終了hashは{'全一致' if all(x['status']=='PASS' for x in pres) else '不一致あり'}、Git追跡{len(tr)}件の開始/終了hashは{'全一致' if all(x['status']=='PASS' for x in tr) else '不一致あり'}。広い探索対象{len(base):,}件のsize/mtime検査：変更{len(changed)}、欠落{len(missing)}。この広域検査は全バイトhash監査ではなく、環境・第三者ツール等を除外する。元データ・原稿の保全主張はhash台帳対象で保証する。

Git tracked diffは開始時と{'一致' if diff==(O/'evidence/GIT_DIFF_START.patch').read_bytes() else '不一致'}、trial外Git状態の追加{len(added)}/除去{len(removed)}件。保全総合={'PASS' if safe else 'HOLD: see preservation evidence'}。SOURCE_PRESERVATION_CHECKS.csv、TRACKED_PRESERVATION_CHECKS.csv、EXISTING_FILE_STAT_CHECK.json、OUTSIDE_TRIAL_GIT_CHANGES.jsonに証拠を保存。

本trial以外へ書き込む処理、新規QAOA/SUMO/厳密求解、Step2統計推定・追加実験、commit/push/公開、正式原稿への反映は実施していない。全て独立したStep1 trial案であり、正式な研究成果への採用・統合は未実施。
'''
(O/'STEP1_FINAL_AUDIT.md').write_text(report)
assert all((O/n).is_file() and (O/n).stat().st_size>0 for n in required)
# Parse CSVs and check delivered interfaces; every reference path in source ledger exists.
cov=pd.read_csv(O/'PATH1_REFERENCE_COVERAGE.csv');assert len(cov)==460 and cov.problem_id.nunique()==460
assert len(pd.read_csv(O/'STEP2_ADDITIONAL_EXPERIMENT_CANDIDATES.csv'))==5
assert len(pd.read_csv(O/'STEP1_COMPLETION_MATRIX.csv'))==5
assert len(pd.read_csv(O/'PATH2_BOUNDARY_DEFINITION_TABLE.csv'))==5
for p in O.glob('*.csv'):pd.read_csv(p)
assert safe,'Preservation discrepancy; report written, inspect before finishing'
dump('evidence/FINAL_VERIFICATION.json',{'overall':'CONDITIONAL','work':'COMPLETE','required_outputs':len(required),'required_present':True,'scientific_checks':len(checks),'scientific_check_failures':0,'input_sources':len(src),'tracked_files':len(tr),'broad_stat_files':len(base),'preservation':'PASS','outside_trial_git_changes':{'added':len(added),'removed':len(removed)},'B_inputs':460,'B_saved_plans':36800,'exact_available':407,'exact_unproved':53,'step2_executed':False,'new_qaoa':0,'new_sumo':0,'new_exact_solves':0,'completed_at':datetime.datetime.now().astimezone().isoformat()})
manifest=[]
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='OUTPUT_SHA256_MANIFEST.csv':manifest.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
pd.DataFrame(manifest).to_csv(O/'OUTPUT_SHA256_MANIFEST.csv',index=False)
print(json.dumps(json.loads((O/'evidence/FINAL_VERIFICATION.json').read_text()),ensure_ascii=False,indent=2))
