from pathlib import Path
import hashlib,json,sys,importlib.util
import numpy as np,pandas as pd
R=Path('/home/takuma/kmd-analysis');O=Path(__file__).resolve().parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');T9=U/'review_outputs/t09_open_data_model_20261029/run01'
d=pd.read_csv(T9/'PACK_20KWH_SENSITIVITY.csv');checks=[]
for i,r in d.iterrows():
 Q=r.gross_design_Wh/r.mean_voltage_design_V
 vals={'positive_active_kg':Q/(r.q_reference_Ah_kg*r.positive_utilization),'negative_active_kg':Q*r.NP_after_formation/(r.negative_q_Ah_kg*(1-r.negative_unavailable_fraction)),'all_cells_capacity_sum_Ah':Q,'pack_terminal_capacity_Ah':Q/100}
 A=Q/171.875/r.positive_active_loading_input_kg_m2 if r.area_policy=='fixed_area_LP' else vals['positive_active_kg']/r.positive_active_loading_input_kg_m2
 vals['positive_face_area_m2']=A
 for k,v in vals.items():
  err=abs(v-r[k]);assert err<1e-7,(i,k,err);checks.append(dict(row=i+1,quantity=k,absolute_error=err,status='PASS'))
pd.DataFrame(checks).to_csv(O/'evidence/CHARGE_AREA_AUDIT.csv',index=False)
# Preserve detailed original evidence table as standalone artifact; record original hash.
e=U/'review_outputs/t09_remaining_acceptance_20261029/run01/INPUT_EVIDENCE.csv'
(O/'evidence/PRIMARY_INPUT_EVIDENCE.csv').write_bytes(e.read_bytes())
# All original model sources and latest thesis files remain read-only; include current identities.
man=pd.read_csv(O/'evidence/SOURCE_MANIFEST.csv')
extra=[U/'src/kmd_quantitative/material_ev/stage2/battery.py',T9/'raw/warwick_article.txt',R/'review_outputs/quantum_ev_step5_20261105/THESIS_STEP5_REVISED.docx',R/'review_outputs/quantum_ev_step5_20261105/THESIS_STEP5_REVISED.pdf']
man=pd.concat([man,pd.DataFrame([dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in extra])],ignore_index=True);man.to_csv(O/'evidence/SOURCE_MANIFEST.csv',index=False)
# One compact table contains absolute and relative stage transmission, with explicit missing fullpack T09.
m=pd.read_csv(O/'data/MASS_SENSITIVITY.csv');s=pd.read_csv(O/'data/DC_SUMMARY.csv');t=m.merge(s,on='case_id',how='left');t['LP_running_mass_kg']=np.where(t.model=='T08',1043.888888888889+t.LP_complete_pack_kg,np.nan);t['S_running_mass_kg']=np.where(t.model=='T08',1043.888888888889+t.S_complete_pack_kg,np.nan);t['LP_vehicle_without_driver_kg']=t.LP_running_mass_kg-55;t['S_vehicle_without_driver_kg']=t.S_running_mass_kg-55;t['running_mass_saving_percent']=100*t.delta_mass_kg/t.LP_running_mass_kg;t['cell_sum_saving_percent']=100*(t.LP_cell_sum_kg-t.S_cell_sum_kg)/t.LP_cell_sum_kg;t['weighted_q_to_DC_transfer']=t.weighted_saving_percent/t.delta_q_percent.replace(0,np.nan);t['weighted_mass_to_DC_transfer']=t.weighted_saving_percent/t.running_mass_saving_percent.replace(0,np.nan);t.to_csv(O/'data/STAGE_TRANSMISSION_TABLE.csv',index=False)
# q-derived quantities have no unique initial-capacity interpretation; HOLD remains.
p=O/'FINAL_REPORT_JA.md';txt=p.read_text();selected=m[(m.model=='T09')&m.axis.isin(['L','ep','en'])][['policy','axis','value','delta_mass_kg']]
rows=['|方針|S側変更項目|値|既知小計差LP−S kg|','|---|---|---:|---:|']
for r in selected.itertuples():rows.append(f'|{r.policy}|{r.axis}|{r.value:g}|{r.delta_mass_kg:.6f}|')
txt+='\n## 担持量・空隙率の具体的感度\n\nLP基準は担持0.10kg/m²・両極空隙0.25で固定。LはS正極担持kg/m²、ep/enはS正/負極空隙率。固定面積方針でもL変更はS側の設計基準面積を変更する介入であり、「LP/S両面積が常に等しい」比較ではない。基準L=.10の時だけLP面積と一致する。\n\n'+'\n'.join(rows)+'\n\n負の値は仮定モデル内でS側既知部材が重くなることを表す。\n'
txt+='\n追加監査: CHARGE_AREA_AUDIT.csvに183条件の容量・正負極活物質・面積・端子容量の'+str(len(checks))+'照合を保存。STAGE_TRANSMISSION_TABLE.csvに段階別絶対/相対変化を統合した。T09の完成値は空欄を維持。\n'
p.write_text(txt)
# Validate source hashes after all computation.
for r in man.itertuples():assert hashlib.sha256(Path(r.path).read_bytes()).hexdigest()==r.sha256
files=[dict(path=str(p.relative_to(O)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in O.rglob('*') if p.is_file() and p.name!='OUTPUT_SHA256.csv' and '__pycache__' not in str(p)]
pd.DataFrame(files).to_csv(O/'OUTPUT_SHA256.csv',index=False)
print('Charge/area checks:',len(checks),'PASS; preservation PASS')
