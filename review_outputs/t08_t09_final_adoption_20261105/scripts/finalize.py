from pathlib import Path
import json,hashlib,sys,importlib.util
import numpy as np,pandas as pd
R=Path('/home/takuma/kmd-analysis');O=Path(__file__).resolve().parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate
run=json.loads((O/'evidence/RUN_RESULT.json').read_text());mass=pd.read_csv(O/'data/MASS_SENSITIVITY.csv');dc=pd.read_csv(O/'data/DC_TRANSMISSION.csv.gz');su=pd.read_csv(O/'data/DC_SUMMARY.csv');op=pd.read_csv(O/'data/OPERATION_RESPONSE.csv');bounds=pd.read_csv(O/'data/BOUNDARIES.csv');checks=[]
# Independent direct frozen evaluation for all cases on short/median/long trajectories.
saved=pd.read_csv(R/'review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv');freeze=json.loads((O/'evidence/DC_FREEZE_SNAPSHOT.json').read_text());rank=op[op.rolling_case=='CRR_LOWER_BOUND'].sort_values('distance_km');selected=rank.iloc[[0,len(rank)//2,-1]].trajectory_sha256
for h in selected:
 p=Path(saved[saved.trajectory_sha256==h].iloc[0].trajectory_path)
 if not p.exists() and p.is_relative_to(R):p=U/p.relative_to(R)
 df=pd.read_csv(p,usecols=['timestamp_s','speed_m_s'])
 for r in dc[dc.trajectory_sha256==h].to_dict('records'):
  pressure=4.5 if r['rolling_case']=='CRR_LOWER_BOUND' else 2.6
  for side in ['LP','S']:
   result,_=evaluate(df.timestamp_s.to_numpy(),df.speed_m_s.to_numpy(),freeze,pressure,{'running_mass_kg':r[side+'_vehicle_running_kg']});err=abs(result['net_DC_Wh']-r[side+'_DC_Wh']);assert err<1e-7
   checks.append(dict(check='independent full frozen kernel',case_id=r['case_id'],trajectory=h,side=side,error_Wh=err,status='PASS'))
# Exact decimal arithmetic independently checks T08 endpoints.
from decimal import Decimal as D
for q,expected in [('171.875',run['T08_LP_kg']),('195.959596',run['T08_S_kg'])]:
 v=D(20000)/D('3.5')*(1/(D(q)*D('.75'))+D('1.1')/(D(360)*D('.98')))+34;assert abs(float(v)-expected)<1e-10
 checks.append(dict(check='Decimal T08 equation',case_id=q,error_Wh=None,status='PASS'))
# Original T08 callable, imported from preserved package without executing runner.
sys.path.insert(0,str(U/'src'))
# Package paths may already be loaded from public src, so extend only the package search path.
import kmd_quantitative
kmd_quantitative.__path__.append(str(U/'src/kmd_quantitative'))
from kmd_quantitative.material_ev.stage2.battery import pack_budget
sc=json.loads((U/'review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json').read_text())
for s in sc['scenarios'][:2]:
 b=pack_budget(s);expected=run['T08_LP_kg'] if s['parameters']['q_ref']['value']==171.875 else run['T08_S_kg'];assert abs(b['pack_mass_kg']-expected)<1e-10
 checks.append(dict(check='original T08 pack_budget callable',case_id=s['scenario_id'],status='PASS'))
pd.DataFrame(checks).to_csv(O/'evidence/INDEPENDENT_AUDIT.csv',index=False)
# Enrich ledger: keep historical adoption HOLD separate from permission to calculate.
ld=pd.read_csv(O/'data/PARAMETER_ADOPTION.csv').fillna('');ld['practical_adoption']='HOLD';ld['numerical_use']='CONDITIONAL GO'
# Unknown original inputs are not promoted by matching references.
ld.loc[ld.parameter.isin(['voltage','q_negative','cell_other_mass','pack_other_mass']),'decision']='HOLD'
ld.loc[ld.parameter_id=='I08','decision']='HOLD'
ld['source_evidence']=ld.primary_source
ld.loc[ld.parameter_id=='I08','source_evidence']='Chen2020 DOI 10.1038/s41467-020-17126-3 Fig5g; saved CHEN2020_TEXT.txt lines604-609; denominator cycle unresolved'
ld.to_csv(O/'data/PARAMETER_ADOPTION.csv',index=False)
# Explicit provenance for every newly introduced axis point.
new=[]
for axis,g in mass[mass.axis!='u_V'].groupby('axis'):
 vals=sorted(g.value.unique());new.append(dict(axis=axis,values=json.dumps(vals),origin='new hypothetical +/-20% around inherited density, not literature uncertainty' if axis in ['rhop','rhon','rhol'] else 'hypothetical wetting diagnostic' if axis in ['wet','sat'] else 'mixed prior probes/references; q=180,210 new hypothetical; fp=.94/.96 and fn=.96 BatPaC alternative recipe, conditional transfer',uncertainty='no probability distribution; one-factor S-side intervention; LP fixed',physical_independence='NOT DEMONSTRATED'))
pd.DataFrame(new).to_csv(O/'data/SENSITIVITY_RANGE_ORIGINS.csv',index=False)
# DC fixed values are traceable to freeze, plus source limitations in report.
fixed=[]
def flatten(x,path=''):
 if isinstance(x,dict):
  for k,v in x.items():flatten(v,path+'.'+k if path else k)
 elif isinstance(x,list):
  for i,v in enumerate(x):flatten(v,path+f'[{i}]')
 else:fixed.append(dict(parameter=path,value=x,source='01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json',adoption='GO for frozen controlled model only',target_vehicle_validation='HOLD'))
flatten(freeze);pd.DataFrame(fixed).to_csv(O/'data/DC_PARAMETER_LEDGER.csv',index=False)
# Model boundaries and code mapping.
rows=[('gross/usable','20000Wh mass;18000Wh stock','same','battery.pack_budget; frozen evaluate'),('Q','gross/V; per-cell Q/100','same','battery.pack_budget; analyze.py'),('positive','Q/(q*u*fp)','same coating','battery.pack_budget; model.geometry'),('negative','Q*NP/(qn*fn)','Q*NP/[qn*(1-loss)*fn]','battery.pack_budget; model.negative_mass'),('area','not resolved','active/loading; fixed LP area alternative','model.geometry'),('foil','within19kg','faceArea/2*t*rho; margins unknown','model.foil_mass'),('separator','within19kg','max(faceAreas)*areal mass','analyze.py'),('liquid','within19kg','(electrode pores+separator pores)*wet*sat+excess, then density','model.liquid_mass'),('other','19kg+15kg assumed','casing/tabs/structure NULL; do not add34kg','model.account_cell'),('vehicle','1155-20000/180+new pack','1043.888889+known+unknown','controlled_dc.evaluate'),('DC','sum(max(total interval wheel work,0))/.9','same; unknown absolute mass prevents unique DC','frozen evaluate')]
pd.DataFrame(rows,columns=['item','T08','T09','code']).to_csv(O/'data/MODEL_BOUNDARY_COMPARISON.csv',index=False)
# concise numeric tables
base=su[su.case_id=='T08_fixed_loading_baseline_0'];base.to_csv(O/'data/BASELINE_TRANSMISSION.csv',index=False)
lines=[]
for rc,g in op.groupby('rolling_case'):
 lines.append(f"{rc}: DC基準合計{g.LP_DC_Wh.sum():.6f} Wh、S合計{g.S_DC_Wh.sum():.6f} Wh、平均削減{g.delta_DC_Wh.mean():.6f} Wh、範囲{g.delta_DC_Wh.min():.6f}–{g.delta_DC_Wh.max():.6f} Wh、合計比削減率{100*g.delta_DC_Wh.sum()/g.LP_DC_Wh.sum():.6f}%。対応質量感度{g.Wh_per_kg.min():.6f}–{g.Wh_per_kg.max():.6f} Wh/kg。")
num='\n\n'.join(lines)
text=f'''# T08・T09採用・感度・経路2最終報告

## 結論と採用判定

計算モデルとしてT08を主解析、T09を部材構造の補完にCONDITIONAL GOとする。逆算容量を実用全電池の初期容量として採用すること、完成T09パックの質量・走行DC絶対値を一意に決めることはHOLD。科学的採用HOLDと条件付き数値実行の許可は別列で管理した。既存凍結値は変更していない。

実行結果: T09保存{run['original_T09_rows']}行を再現。追加・既存探索合計{run['mass_cases']}質量条件、T08のDC接続{run['dc_rows']}行。保存460軌跡×2Crrは920独立走行実験ではない。COMPUTATIONAL_CHECKSとINDEPENDENT_AUDITに検算を保存。別プロセス・別計算経路の監査であり、別研究者による査読を意味しない。

## Chen容量の確定した意味

原著: Qing Chen et al., Highly reversible oxygen redox in layered compounds enabled by surface polyanions, Nature Communications 11,3411 (2020), DOI10.1038/s41467-020-17126-3。保存原著抽出CHEN2020_TEXT.txtを確認。Fig5g本文:1C=200mA/g、100cycle後LP121mAh/g・70.4%、S200194mAh/g・99.0%。121/.704=171.875、194/.990=195.959595...。実行値195.959596を維持し、旧表示195.960を上書きしない。

Fig5b/cは0.5Cの初回特性。LP初回充電238mAh/g、FCE65.2%から放電155.176mAh/gが算術的に得られるが、丸めを含み、1C保持率系列とは別物。S200の同条件初回容量の確定値と、保持率分母のcycle/activation定義は未取得。本文の100cycle報告だけから逆算分母を初回値と断定しない。初回容量としてHOLD、逆算参照容量としてのみCONDITIONAL GO。分母原系列・補足・生データを取得するまでは解除しない。今回原著サイト再取得は認証制限、保存本文が根拠。

## モデル監査

T08: M=Eg/V[1/(q*u*fp)+NP/(qn*fn)]+100*m_other+Fpack+extra。gross20000Whで部材設計しusable18000Whは走行stock。保持率・ICEを再適用しない。負極は必要Ahから算定し、正極qの増加だけでは減少しない。V変更時は正負極とも変化する。

T09: A=mactive/L、Vsolid=mcoat/rho、Vcoat=Vsolid/(1-epsilon)、pore=epsilon*Vcoat、tcoat=Vcoat/A。箔面積は両面共有でA/2。膜面積はmax(Ap,An)。乾燥膜と空隙液を分離し液を一度だけ計上。既知小計は両極乾燥塗工材+Al+Cu+膜+液。活物質と添加材は塗工材内であり重ねない。余白・外装・タブ・構造はNULL。既存全面対向FAILを数値再現PASSで解除しない。

T09全183行の既知小計とNULL完成パックを元model.py関数で確認した。これは原データの独立した物性実証ではない。今回追加の一要因比較はLPを固定、S側だけ設定変更。fixed_area_LPでは元LPの面積を保持する。従来の両材料共通条件変更とは比較設計が異なるため同じ結果と見なさない。

車両置換: 走行質量=1155−20000/180+Mnew=1043.888888889+Mnew。運転者55kgは残余に一度含まれる。運転者を除く車両質量は走行質量−55kg。新パックを1155へ単純加算しない。回転等価61kgは固定。車体、補強、積載を固定するモデル仮定。

凍結DC: 各1秒区間末速度で距離、Crr、空力を評価し、転がり+空力+並進+回転を合算後に正値化し効率.9で割る。平坦・回生なし・補機/旋回除外・観測末端の未知区間を除外。凍結核SHA検証、920条件の両端点を元核と照合、追加全T08ケースを短/中/長の3軌跡で元核へ直接照合した。

## 基準参考例と成立境界

q増加率は{100*(195.959596/171.875-1):.6f}%。T08パック{run['T08_LP_kg']:.9f}→{run['T08_S_kg']:.9f}kg、差{run['delta_kg']:.9f}kg。セル質量合計81.145654799→75.697357384kg、1セル0.811456548→0.756973574kg。走行質量1140.034543688→1134.586246273kg。追加部材差δの相殺境界{run['delta_kg']:.9f}kg、利用率境界{run['u_boundary']:.9f}、S平均電圧境界{run['V_boundary']:.9f}V（LP側3.5V固定）。同一V/u/fp/負極/部材ならqS>qLPで正極質量差が生じる。より一般にはV、u、負極、面積部材込みの会計式を解く。

T09既知差は固定担持9.722608121kg、固定面積5.977891152kg。未知差δ=US−ULPとして完成パック差=b−δ。δ<bで削減、δ=bで相殺、δ>bで逆転。ULP/USは非負だが差δは正負があり得る。T09絶対完成パック、絶対車両質量、絶対DC、完成パックに対する相対変化はHOLD。NULLを0として補完しない。数値が必要なら未知BOMを入力してDC式を再評価する。

{num}

DC合計は有限保存集合の記述集計で、現実配送の年間消費ではない。相対伝達係数は(DC削減率)/(q増加率)と定義しDC_SUMMARYへ保存。百分率同士の比であり、エネルギー保存率や量子技術の寄与率ではない。q変化ゼロの場合は未定義。DC段階の車両質量は走行質量で統一した。

## 感度と不確実性

MASS_SENSITIVITYは正極q/V/u/fp、負極fn/qn/NP、密度、担持、両極空隙、箔厚、膜面密度、液密度/過剰液/含浸/飽和、セルその他、パック付加、追加質量を収録。単一変数変更ではLPを基準固定し、相殺を隠さない。密度±20%、含浸診断、q180/210は新しい仮想点で文献範囲ではない。既存探索点とBatPaC別設計配合の移用はSENSITIVITY_RANGE_ORIGINSと採用台帳を参照。確率分布や信頼区間に変換しない。

材料の比容量・担持量・密度・空隙率・寿命・安全は独立に変更できると証明されていない。数学的ゼロ境界はモデルで確定できるが、その境界を実セルが満たせるかは全電池・製造・熱・寿命実験が必要。

## 最新修士論文との整合

確認対象はreview_outputs/quantum_ev_step5_20261105/THESIS_FULL_TEXT.mdと同系列DOCX/PDF。要旨と経路2節は逆算容量を参考例へ限定し、主成果を記号感度・部材相殺・材料非依存DC応答に置いている。今回もこの採用判断を維持する。論文原本は保全し、差し込み用文章をTHESIS_INSERT_JA.mdに出力した。

## 最終監査と残課題

算術再現・単位・源泉対応・仮定区分・科学解釈・量子帰属・論文主張をevidence/FINAL_AUDIT.csvに個別記録。数値再現PASSは実用入力採用PASSを意味しない。凍結コード、原論文、旧成果のhash不変を確認した。

未解決:保持率分母の原系列、S200の同条件初回放電、黒鉛全電池Vとq/u、負極360の厳密出典、対象混合密度、実担持・空隙・箔余白、実電解液量、外装/タブ/冷却/BMS構造、熱/寿命/安全。これらの推測補完は行っていない。

次の作業は(1)Chen補足・cycle原系列の取得、(2)同条件全電池の容量と平均放電電圧・formationの確認、(3)完成BOMと製造条件の確定、(4)確定入力による本スクリプトの別run実行。QAOAやSUMOの再実行は今回の下流条件評価には必要ない。材料改善を量子計算機が実現した証拠は本研究にない。
'''
(O/'FINAL_REPORT_JA.md').write_text(text)
(O/'THESIS_INSERT_JA.md').write_text('''# 論文差し込み用文章（方法・結果・考察・限界）

## 方法

因果経路2を、正極参照比容量から部材質量、パック質量、走行質量、走行時DC電力量へ至る条件付き変換として評価した。T08を簡略質量会計の主モデル、T09を面積・空隙・箔・膜・電解液の構造依存性を調べる補完モデルとした。入力は直接報告値、逆算参照値、他材料・他製品からの移用値、設計仮定、未取得値へ区分した。質量設計にはgross20kWh、走行stockには研究仮定usable18kWhを用いた。未取得部材はNULLを維持した。同一保存460軌跡に対し、凍結Controlled-DCモデルで電池交換後の質量応答を比較した。感度解析はLP条件を固定したS側一要因変更を基本とし、平均電圧と利用率の二変数条件も評価した。

## 結果

T09の既存183条件の既知部材小計を保存計算関数により再現した。完成パック質量は全条件で未確定である。逆算参照容量171.875/195.959596Ah/kgを用いたT08参考例では、パック質量は96.145655/90.697357kg、差5.448297kgとなった。共通部材条件下の追加質量差5.448297kg、S利用率約0.877094、S平均電圧約3.193156Vがそれぞれ一要因変更時の相殺境界であった。T09では既知小計の差が固定担持9.722608kg、固定面積5.977891kgとなり、設計方針によって部材への伝達が異なった。DCの絶対値・対応差・相対伝達係数は付属BASELINE_TRANSMISSION.csvおよびDC_SUMMARY.csvに示す。

## 考察

共通エネルギー・電圧・利用率・配合・負極条件では、正極比容量の向上は正極塗工材を減らす。しかし、その削減が完成パックへ伝わるかは面積依存部材と追加構造質量に依存する。完成パックの正味質量差が走行質量へ1対1で伝わるのは車体・積載等を固定した交換条件である。走行DCへの伝達量は軌跡の距離、速度、加減速および転がり条件に依存する。本研究の貢献は材料改善の実現を主張することではなく、中間変換の会計と成立・相殺条件を追跡可能に示す点にある。

## 限界

Chenの保持率から逆算した容量は初回放電容量として採用しない。保持率分母のcycle/activationおよび実用全電池への移用適格性はHOLDである。別材料の固相密度、別製品の膜・電解液物性、仮定した担持・空隙・固定質量を使用しており、対象完成パック・実車の予測値ではない。T09の未測定部材を0として補完していない。数学的境界の存在は製造性、出力、寿命、安全性の達成を意味しない。正極表面処理の成果を量子計算機の実証成果に帰属させない。運行電力量の評価範囲は既存Controlled-DCの観測走行時消費に限定し、補機、回生、未知の末端区間を含めない。
''')
audit=[('数値再現性','PASS','183 T09 rows; 920 DC endpoint pairs; all T08 cases on three trajectories; Decimal and original T08 callable'),('単位','PASS','Wh/V=Ah;Ah/(Ah/kg)=kg;kg/(kg/m2)=m2; A/2*t*rho=kg; pore*rho=kg; J/3600=Wh'),('出典対応','CONDITIONAL','source manifest and parameter ledger complete at saved evidence level; unresolved original acquisition and Chen denominator HOLD'),('実測/仮定','PASS','numerical use separate from practical HOLD; new ranges explicitly hypothetical'),('科学解釈','CONDITIONAL','conditional references only; no target practical pack acceptance'),('量子帰属','PASS','no quantum hardware attribution of surface treatment'),('論文主張範囲','CONDITIONAL','symbolic mass/DC transfer and conditional boundary; fullpack/real vehicle HOLD')]
pd.DataFrame(audit,columns=['audit','status','evidence_or_limit']).to_csv(O/'evidence/FINAL_AUDIT.csv',index=False)
(O/'README.md').write_text('''# T08/T09最終評価

入口: FINAL_REPORT_JA.md。論文用: THESIS_INSERT_JA.md。data/に採用台帳、境界、感度、効果伝達、evidence/に入力hash・検算、figures/にPNG/PDF。

再実行（既存保存入力と.conda環境が必要）:

```bash
.conda/bin/python review_outputs/t08_t09_final_adoption_20261105/scripts/analyze.py
.conda/bin/python review_outputs/t08_t09_final_adoption_20261105/scripts/finalize.py
```

新規出力先だけを書き換える。元成果物は読取りのみ。T09完成質量/DCはHOLD。source manifestの外部保全パス依存があり、このディレクトリ単独では完全再現しない。
''')
manifest=[]
for p in O.rglob('*'):
 if p.is_file() and p.name!='OUTPUT_SHA256.csv' and '__pycache__' not in str(p):manifest.append(dict(path=str(p.relative_to(O)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
pd.DataFrame(manifest).to_csv(O/'OUTPUT_SHA256.csv',index=False)
print('Independent checks',len(checks));print(base.to_string(index=False));print(num)
