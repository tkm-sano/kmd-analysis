"""Separate-process audit of serialized outputs, unit identities and source immutability."""
from pathlib import Path
import sys,os,json,hashlib,math
from decimal import Decimal as D,localcontext
sys.dont_write_bytecode=True
import pandas as pd
SD=Path(__file__).resolve().parents[1];O=Path(os.environ.get('LEVEL2_OUTPUT',str(SD))).resolve()
checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def test(name,ok,detail=''):
 checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=str(detail)))
def read(name):return pd.read_csv(O/name)
for name in ['FINAL_REPORT_JA.md','PUBLIC_CASE_SELECTION.md','PUBLIC_QV_VALIDATION.csv','JOINT_INPUT_CASES.csv','T08_REPRESENTATIVE_RESULTS.csv','BOUNDARY_VALIDATION.csv','T09_COMPONENT_ACCOUNTING.md','T09_COMPONENT_REQUIREMENTS.csv','T08_T09_COMPARABILITY.md','DC_REUSE_DECISION.csv','CLAIM_EVIDENCE_MATRIX.csv','LEVEL2_COMPLETION_AUDIT.csv','README.md','RUN_CONFIG.json','scripts/validate.py','scripts/components.py','scripts/report.py']:
 test('required output '+name,(O/name).is_file())
q=read('PUBLIC_QV_VALIDATION.csv');m=read('T08_REPRESENTATIVE_RESULTS.csv');b=read('BOUNDARY_VALIDATION.csv');dc=read('evidence/DC_SMALL_VALIDATION.csv');j=read('JOINT_INPUT_CASES.csv')
for row in q.itertuples():
 raw=pd.read_csv(O/'evidence'/f'{row.case_id}_DISCHARGE.csv',dtype=str)
 with localcontext() as c:
  c.prec=60;Q=[D(x) for x in raw.q_mAh_g];V=[D(x) for x in raw.voltage_V]
  energy=sum((Q[i+1]-Q[i])*(V[i]+V[i+1])/2 for i in range(len(Q)-1));cap=Q[-1]-Q[0]
  test('serialized QV capacity '+row.case_id,abs(float(cap)-row.Q_discharge_mAh_g)<1e-9)
  test('serialized QV energy '+row.case_id,abs(float(energy)-row.specific_energy_Wh_kg_positive_active)<1e-8)
  test('serialized QV mean '+row.case_id,abs(float(energy/cap)-row.mean_discharge_V)<1e-10)
 test('source xlsx SHA '+row.case_id,sha(row.xlsx_file)==row.xlsx_sha256)
 test('positive active energy denominator '+row.case_id,row.mass_basis=='positive active material only')
for row in m.itertuples():
 M=20000/row.V*(1/(row.q*row.u*row.fp)+row.np/(row.qn*row.fn))+100*row.cellother+row.packother+row.extra
 test('serialized T08 formula '+row.case_id,abs(M-row.hypothetical_pack_kg)<1e-8)
 test('serialized mass conservation '+row.case_id,abs(row.positive_coating_kg+row.negative_coating_kg+row.other_total_kg-row.hypothetical_pack_kg)<1e-8)
 test('serialized cells plus pack '+row.case_id,abs(100*row.cell_mass_kg+row.packother+row.extra-row.hypothetical_pack_kg)<1e-8)
 test('actual masses stay NULL '+row.case_id,pd.isna(row.actual_pack_mass_kg) and pd.isna(row.actual_vehicle_mass_kg))
for row in b[b.boundary_id.str.startswith('B_')].itertuples():
 test('serialized boundary zero '+row.axis,abs(row.delta_on_kg)<1e-9)
 test('serialized boundary sign '+row.axis,row.delta_below_kg*row.delta_above_kg<0)
 test('serialized numerical root '+row.axis,abs(row.analytic_root-row.numerical_root)<1e-8)
 r=m[m.case_id=='ROOT_'+row.axis].iloc[0]
 test('boundary serialized representative agrees '+row.axis,abs(r.delta_reference_minus_case_kg)<1e-8)
for row in dc.itertuples():
 key=row.case_id+' '+row.trajectory_sha256[:8]+' '+row.rolling_case
 comp=sum(getattr(row,f'W{i}_saving_Wh') for i in range(1,5))+row.branch_correction_Wh
 test('serialized DC absolute '+key,abs(row.reference_DC_Wh-row.comparison_DC_Wh-row.saving_DC_Wh)<1e-7)
 test('serialized DC components '+key,abs(comp-row.saving_DC_Wh)<1e-7)
 test('serialized DC percent '+key,abs(100*row.saving_DC_Wh/row.reference_DC_Wh-row.saving_percent)<1e-9)
 test('serialized DC per distance '+key,abs(row.saving_DC_Wh/row.distance_km-row.saving_Wh_km)<1e-9)
 test('serialized vehicle substitution '+key,abs(1155-20000/180+float(m[m.case_id==row.case_id].hypothetical_pack_kg.iloc[0])-row.comparison_running_kg)<1e-7)
 if abs(row.delta_mass_kg)>1e-8:test('serialized DC per kg '+key,abs(row.saving_DC_Wh/row.delta_mass_kg-row.saving_Wh_kg)<1e-8)
 test('fixed aero rotation '+key,abs(row.W2_saving_Wh)<1e-9 and abs(row.W4_saving_Wh)<1e-9)
test('small DC rows only',len(dc)==24 and dc.trajectory_sha256.nunique()==3)
test('T08 point count',len(m)==17)
test('QV rows',len(q)==4)
test('effective capacity is not penalized twice',j[(j.parameter=='u')].value.astype(float).eq(1).all())
test('explicit actual unknown inputs',j[(j.parameter.str.startswith('actual_'))].value.isna().all())
ledger=json.loads((O/'evidence/T09_SYNTHETIC_LEDGER.json').read_text())
test('T09 complete pack unknown',ledger['complete_pack_kg'] is None)
test('T09 complete system unknown',ledger['complete_system_kg'] is None)
test('T09 thermal and protection explicit unknown',{'internal thermal parts and coolant','protection and gas release'}.issubset(ledger['unknown_pack_parts']))
claims=read('CLAIM_EVIDENCE_MATRIX.csv').set_index('claim_id')
test('prohibited claims rejected',all(claims.loc[k,'thesis_adoption']=='NOT_ADOPT' for k in ['C09','C10','C11','C12','C13']))
levels=read('LEVEL2_COMPLETION_AUDIT.csv');test('all A to H assessed',set(levels.condition)==set('ABCDEFGH'))
test('scope conditions retained',set(levels[levels.condition.isin(['A','C','F'])].status)=={'CONDITIONAL PASS'})
for name in ['evidence/NUMERICAL_CHECKS.csv','evidence/T09_COMPONENT_CHECKS.csv','evidence/LEGACY_REFERENCE_CHECKS.csv']:
 f=read(name);test('all pass '+name,f.status.eq('PASS').all(),len(f))
protected=read('evidence/PROTECTED_BEFORE.csv')
for row in protected.itertuples():test('preserved '+row.path,Path(row.path).is_file() and sha(row.path)==row.sha256)
source=read('evidence/SOURCE_MANIFEST.csv')
for row in source.itertuples():test('source '+row.path,Path(row.path).is_file() and sha(row.path)==row.sha256)
R=next(p for p in SD.parents if (p/'src/kmd_quantitative').exists())
thesis_paths=set((R/'docs/thesis').rglob('*.tex'))|set(R.glob('*.docx'))
thesis_paths.update((R/'review_outputs').glob('quantum_ev*/**/*.docx'))
pd.DataFrame([dict(path=str(p),sha256=sha(p),stage='FINAL_SNAPSHOT_NOT_TURN_START_BASELINE') for p in sorted(thesis_paths)]).to_csv(O/'evidence/THESIS_FINAL_SNAPSHOT.csv',index=False)
test('no generated bytecode',not any(O.rglob('*.pyc')))
pd.DataFrame(checks).to_csv(O/'evidence/SERIALIZED_AUDIT.csv',index=False)
pd.DataFrame([dict(path=r.path,sha256_before=r.sha256,sha256_after=sha(r.path),status='PASS' if sha(r.path)==r.sha256 else 'FAIL') for r in protected.itertuples()]).to_csv(O/'evidence/PROTECTED_AFTER.csv',index=False)
fail=[r for r in checks if r['status']=='FAIL']
report=f'''# 最終学術・数値監査

総合判定はCONDITIONAL GO（限定Level2の検算範囲で完了）である。対象LP/S実用全電池、完成パック、実車DC、出力・寿命・安全性の実証HOLDは維持する。A/C/FのCONDITIONAL PASSは原図対応、共同入力の不足、対象BOM未確定によるものである。

計算プロセスの数値確認は{len(read('evidence/NUMERICAL_CHECKS.csv'))}項目、別プロセスで保存CSV・単位・成分和・境界符号・採用区分を読んだ監査は{len(checks)}項目であり、FAILは{len(fail)}項目である。項目数にはファイルごとの初期/最終ハッシュ照合が含まれ、科学的に独立な実証数ではない。

保護対象{len(protected)}ファイルはSHA-256が不変である。対象は旧最終採用/交互作用/追加調査の全ファイルと、前回保護台帳が参照する凍結コード・原データ・論文PDF等である。`evidence/PROTECTED_BEFORE.csv`と`PROTECTED_AFTER.csv`に各パスとハッシュを記録した。凍結DC核の固定ハッシュは`4ece8782fc6c4a5fd2731ea310d2042973d2f0f996f016c148ca29c6b935e39b`であり、今回の旧参照6行も再現した。論文tex/docxは書込操作の対象にしていない。追加の`THESIS_FINAL_SNAPSHOT.csv`は原本等の最終時点ハッシュであり、着手前との比較証拠ではない。

容量・電圧・正極活物質エネルギーの単位を明記し、QspanとQendを区別した。4曲線はopenpyxl/numpyとZIP/XML/Decimal60で検算済みである。測定精度や未収録区間の推定精度は算出していない。Zhang原図末尾とSource Dataの完全一致、Song代表曲線とサイクル容量系列の同一記録性は未確認として残した。

T08は既存関数を抽出して17点を評価し、別のpercell SI式と照合した。6境界では解析/二分法/前後符号を確認し、域外・根不存在を区別した。初回容量へのChen逆算の転用は行っていない。公開近縁q/Vと移用qn・仮定NP/固定34kgを別分類にし、実効容量へ再度ICE/保持率を乗じていない。

T09ではNULLを0へ置換せず、必要分類の明示・部材重複拒否・pack/system境界を実装した。人工単位例は対象パックBOMではない。T08固定34kgへのT09部材追加、共通冷却装置の絶対質量の材料差化は行っていない。Uの不明なT09について完成車両質量や絶対DCは算出していない。

DCの新規数値は仮想T08の3軌跡・2Crrに限定し、全460軌跡へ外挿しない。回生・HVAC・勾配・停止補機等を追加していない。独立していない形成サイクル/軌跡条件を独立標本にせず、CI/確率/有意差を算出していない。

対象LP/S完成パック確定、実車省電力実証、量子計算による材料改善という主張はCLAIM_EVIDENCE_MATRIX.csvで採用不可である。修士論文原本の編集、大規模追加計算、外部研究者への連絡は行っていない。

再実行はREADME.mdの3スクリプトを順に実施する。既存資料は参照パス・出典URL・ハッシュで追跡できる。新出力のハッシュは`evidence/OUTPUT_SHA256.csv`に記録する（当該台帳自体は自己参照を避け除外する）。
'''
(O/'FINAL_AUDIT.md').write_text(report)
paths=sorted(p for p in O.rglob('*') if p.is_file() and p.name!='OUTPUT_SHA256.csv')
pd.DataFrame([dict(path=str(p.relative_to(O)),sha256=sha(p),bytes=p.stat().st_size) for p in paths]).to_csv(O/'evidence/OUTPUT_SHA256.csv',index=False)
print(json.dumps(dict(serialized_checks=len(checks),failures=len(fail),protected_files=len(protected),output_files=len(paths)+1),ensure_ascii=False))
if fail:raise AssertionError(fail)
