from pathlib import Path
import pandas as pd,json,hashlib
O=Path(__file__).resolve().parents[1]
# Make copied Step2 datasets unmistakably archival values governed by corrected Step3 interpretation.
rows=[]
for p in sorted((O/'data').glob('*.csv')):
 name=p.name
 if name.startswith('PATH2_') and name not in ['PATH2_ANALYTICAL_SENSITIVITY.csv']:
  dep='YES';role='Step2条件付き参考シナリオの保存値（Chen逆算q依存）'
 elif name.startswith('DC_MASS_'):dep='NO';role='材料入力を使わない凍結kernel再検算'
 elif name=='DC_ENDPOINT_RECHECK.csv':dep='YES';role='Chen依存参考端点の元値再集計'
 elif name=='PATH2_ANALYTICAL_SENSITIVITY.csv':dep='NO_SYMBOLIC';role='T08主分析の記号感度；数値範囲HOLDを併記'
 elif name=='TABLE2_CONDITIONS.csv':dep='MIXED_EXPLICIT';role='主分析/参考例ラベル付き最終条件表'
 else:dep='NO_OR_MIXED_EXPLICIT';role='経路1集計または最終表示データ；各行のラベルを参照'
 rows.append(dict(path=str(p.relative_to(O)),Chen_dependency=dep,interpretation=role))
pd.DataFrame(rows).to_csv(O/'data/DATA_ROLE_INDEX.csv',index=False)
(O/'data/SOURCE_COPY_INTERPRETATION.md').write_text('''# 保存CSVの扱い
PATH2_SENSITIVITY_SUMMARY、PATH2_BOUNDARY_ANALYSIS、PATH2_T09_COMMON_INPUT_SENSITIVITY、PATH2_OPERATION_STRATA、PATH2_GROUP_SENSITIVITY_INTERVALSはStep2の保存値を変更せず複製したデータである。数値の存在は主分析への採用を意味しない。これらの具体的なシナリオ/格子はChen逆算qに依存し、Step3では条件付き参考例とする。
PATH2_ANALYTICAL_SENSITIVITYは数式上の主分析、DC_MASS_KERNEL_INDEPENDENT/SUMMARYは材料入力を使用しない追加検算である。最終条件表はTABLE2_CONDITIONS.csvに主分析/参考例を明記した。過去のCSV中のscopeやstatusだけを現在の採用判断として読まない。data/DATA_ROLE_INDEX.csvおよびroot/CHEN_DEPENDENCY_AUDIT.csvを併読する。
''')
p=O/'CHEN_DEPENDENCY_AUDIT.csv';d=pd.read_csv(p,keep_default_na=False);extra=[]
for val,label,src in [('171.875/195.959596 Ah/kg','保持試験からの逆算入力','PATH2_INPUT_PROVENANCE.csv'),('96.145655/90.697357 kg','T08条件付き参考質量','data/PATH2_SENSITIVITY_SUMMARY.csv'),('5.448297 kg','参考質量相殺境界','data/PATH2_BOUNDARY_ANALYSIS.csv'),('0.877094','参考利用率境界','data/PATH2_BOUNDARY_ANALYSIS.csv'),('3.193156 V','参考電圧境界','data/PATH2_BOUNDARY_ANALYSIS.csv'),('0.412579/0.413590 %','参考DC総和比','data/DC_ENDPOINT_RECHECK.csv'),('9.722608/5.977891 kg','T09設計方針別既知差','data/PATH2_T09_COMMON_INPUT_SENSITIVITY.csv')]:extra.append(dict(object_type='numeric_reference',object_id=val,dependency='YES',role='主分析確定値として未採用；条件付き参考例',reason=label+'；'+src,status='CONDITIONAL;INPUT_ADOPTION_HOLD'))
for name in ['PATH2_CONTRIBUTION_CONDITIONS.md','PATH2_CONDITION_CLASSIFICATION.csv','PATH2_MODEL_DEPENDENCE.md','PATH2_LIMITATIONS.md','CROSS_PATH_CONDITION_MATRIX.csv','SYNTHESIZED_RESEARCH_FINDINGS.md','RESEARCH_CONTRIBUTION_STATEMENT.md','THESIS_RESULTS_DRAFT.md','THESIS_DISCUSSION_DRAFT.md','THESIS_CONCLUSION_DRAFT.md','THESIS_STEP3_TRIAL.docx']:
 extra.append(dict(object_type='final_artifact',object_id=name,dependency='MIXED_EXPLICIT',role='主分析と条件付き参考例を分離',reason='Chen主材料入力未採用、完成pack/実EV未実証を保持',status='CONDITIONAL'))
pd.concat([d,pd.DataFrame(extra)],ignore_index=True).to_csv(p,index=False)
# Additional provenance for the nonpack mass used only by inherited reference scenario.
p=O/'PATH2_INPUT_PROVENANCE.csv';d=pd.read_csv(p,keep_default_na=False)
r=dict(input_id='nonpack reference running mass',variable='nonpack_plus_driver_kg',value=1043.888888888889,unit='kg',input_type='凍結条件からの計算',Chen_dependency='NO_DIRECT;LP/S outputYES_via_pack',source_path=str(O.parents[1]/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'),locator='B0 vehicle1100−pack111.111111+driver55',adoption='CONDITIONAL_REFERENCE',allowed_use='参考LP/S走行質量への接続',unresolved='車両設計/実積載の妥当性未実証')
pd.concat([d,pd.DataFrame([r])],ignore_index=True).to_csv(p,index=False)
with (O/'README.md').open('a') as f:f.write('\n論文草稿：[独立Word](THESIS_STEP3_TRIAL.docx)、[表示PDF](render/THESIS_STEP3_TRIAL.pdf)、[結果](THESIS_RESULTS_DRAFT.md)、[考察](THESIS_DISCUSSION_DRAFT.md)、[結論](THESIS_CONCLUSION_DRAFT.md)。Chen修正の入口はCHEN_2020_ADOPTION_CORRECTION.md、主分析/参考区分はPATH2_MAIN_VS_REFERENCE_RESULTS.mdである。data内の旧Step2複製CSVはdata/SOURCE_COPY_INTERPRETATION.mdに従って解釈する。\n')
# Retain exact source files for the 46/41 caveat, generic formulas, statistics and revised output.
print('Closure interpretation and reference provenance saved')
