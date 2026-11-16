"""Read completed numerical output, independently audit and write Japanese reports.
This process does not import or execute the analysis runner.
"""
from pathlib import Path
import os,sys,json,hashlib,copy,itertools,shutil
sys.dont_write_bytecode=True
from decimal import Decimal as D,localcontext
import numpy as np
import pandas as pd
SCRIPT_DIR=Path(__file__).resolve().parents[1]
R=next(p for p in SCRIPT_DIR.parents if (p/'src/kmd_quantitative').exists())
O=Path(os.environ.get('T08_T09_OUTPUT',str(SCRIPT_DIR))).resolve()
OLD=R/'review_outputs/t08_t09_final_adoption_20261105'
U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
run=json.loads((O/'evidence/RUN_RESULT.json').read_text())
mass=pd.read_csv(O/'INTERACTION_RESULTS.csv');su=pd.read_csv(O/'data/DC_SUMMARY.csv')
op=pd.read_csv(O/'data/BASELINE_OPERATION_RESPONSE.csv');fac=pd.read_csv(O/'FACTOR_IMPORTANCE.csv')
bounds=pd.read_csv(O/'BOUNDARY_SURFACES.csv');members=pd.read_csv(O/'data/CASE_MEMBERSHIP.csv')
mix=pd.read_csv(O/'data/MIXED_DIFFERENCES.csv');checks=[]

def check(name,ok,detail=''):
    checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=str(detail)))
    if not ok:
        pd.DataFrame(checks).to_csv(O/'evidence/INDEPENDENT_AUDIT.csv',index=False)
        raise AssertionError((name,detail))
def csv(name,rows):
    df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    df.to_csv(O/name,index=False,float_format='%.12g');return df
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def table(df,columns=None,digits=6):
    df=df[columns] if columns else df
    header='| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'
    rows=[]
    for values in df.itertuples(index=False,name=None):
        cells=[]
        for v in values:
            if pd.isna(v):cells.append('未定義 / HOLD')
            elif isinstance(v,(float,np.floating)):cells.append(f'{v:.{digits}f}')
            else:cells.append(str(v).replace('|','/'))
        rows.append('| '+' | '.join(cells)+' |')
    return header+'\n'.join(rows)

# Independent original T08 per-cell budget and 60-digit aggregate, all design inputs.
sys.path.insert(0,str(R/'src'))
import kmd_quantitative
kmd_quantitative.__path__.append(str(U/'src/kmd_quantitative'))
from kmd_quantitative.material_ev.stage2.battery import pack_budget
templatepath=U/'review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json'
template=json.loads(templatepath.read_text())['scenarios'][0]
mapping=dict(q='q_ref',u='utilization',V='voltage',fp='f_positive',fn='f_negative',qn='q_negative',np='np_ratio',cellother='cell_other_mass',packother='pack_other_mass',extra='additional_mass')
original_sources=[templatepath,U/'src/kmd_quantitative/material_ev/stage2/battery.py',U/'src/kmd_quantitative/material_ev/ledger.py']
originhash={str(p):sha(p) for p in original_sources}
for row in mass[mass.model=='T08'].to_dict('records'):
    for side in ['LP','S']:
        p={k:row[side+'_'+k] for k in mapping};scenario=copy.deepcopy(template)
        for k,v in p.items():scenario['parameters'][mapping[k]]['value']=v
        got=pack_budget(scenario)['pack_mass_kg'];expected=row[side+'_mass_or_known_kg']
        check('original T08 per-cell callable '+row['case_id']+side,abs(got-expected)<1e-8,abs(got-expected))
        with localcontext() as ctx:
            ctx.prec=60;d={k:D(str(v)) for k,v in p.items()}
            dm=D(20000)/d['V']*(D(1)/(d['q']*d['u']*d['fp'])+d['np']/(d['qn']*d['fn']))+100*d['cellother']+d['packother']+d['extra']
        check('Decimal mass '+row['case_id']+side,abs(float(dm)-expected)<1e-8,abs(float(dm)-expected))

# Audit every serialized DC row, independently of in-memory checks.
counts={};maxclosure=0.;minstock=np.inf;minsign=np.inf;totals={};rows=0;origins={}
for chunk in pd.read_csv(O/'DC_INTERACTION_RESULTS.csv',chunksize=50000):
    rows+=len(chunk)
    err=(chunk.delta_DC_Wh-chunk.W1_rolling_mask_saving_Wh-chunk.W3_translation_mask_saving_Wh-chunk.positive_branch_correction_Wh).abs().max()
    maxclosure=max(maxclosure,err);minstock=min(minstock,chunk.minimum_terminal_stock_Wh.min())
    check('serialized absolute differences '+str(rows),np.max(np.abs(chunk.LP_DC_Wh-chunk.S_DC_Wh-chunk.delta_DC_Wh))<1e-7)
    check('serialized relative differences '+str(rows),np.max(np.abs(100*chunk.delta_DC_Wh/chunk.LP_DC_Wh-chunk.saving_percent))<1e-8)
    check('serialized distance normalization '+str(rows),np.max(np.abs(chunk.delta_DC_Wh/chunk.distance_km-chunk.delta_Wh_per_km))<1e-8)
    check('mass replacement '+str(rows),np.max(np.abs(chunk.LP_vehicle_running_kg-chunk.S_vehicle_running_kg-chunk.delta_vehicle_mass_kg))<1e-7)
    nz=chunk.delta_vehicle_mass_kg.abs()>1e-8
    check('mass DC sign '+str(rows),np.all(chunk.loc[nz,'delta_DC_Wh']*chunk.loc[nz,'delta_vehicle_mass_kg']>0))
    check('Wh per kg normalization '+str(rows),np.max(np.abs(chunk.loc[nz,'delta_DC_Wh']/chunk.loc[nz,'delta_vehicle_mass_kg']-chunk.loc[nz,'delta_Wh_per_kg']))<1e-7)
    check('zero delta Wh/kg NULL '+str(rows),chunk.loc[~nz,'delta_Wh_per_kg'].isna().all())
    check('W2 W4 mass contribution zero '+str(rows),(chunk.W2_aero_mask_saving_Wh==0).all() and (chunk.W4_rotation_mask_saving_Wh==0).all())
    for key,g in chunk.groupby(['case_id','rolling_case']):
        counts[key]=counts.get(key,0)+len(g)
        totals[key]=totals.get(key,np.zeros(3))+g[['LP_DC_Wh','S_DC_Wh','delta_DC_Wh']].sum().to_numpy()
    for origin,n in chunk.origin.value_counts().items():origins[origin]=origins.get(origin,0)+int(n)
check('DC serialized row count',rows==run['DC_rows'],rows)
check('460 matched rows every case/Crr',all(v==460 for v in counts.values()),len(counts))
check('serialized component closure',maxclosure<1e-7,maxclosure)
check('no trajectory stock exhaustion',minstock>=0,minstock)
for r in su.itertuples():
    check('DC summary sums '+r.case_id+r.rolling_case,np.max(np.abs(totals[(r.case_id,r.rolling_case)]-np.array([r.LP_sum_Wh,r.S_sum_Wh,r.delta_sum_Wh])))<2e-5)
check('T09 complete masses NULL',mass[mass.model=='T09'][['LP_complete_pack_kg','S_complete_pack_kg']].isna().all().all())
check('all boundary residuals',bounds.mass_residual_kg.abs().max()<1e-8)
for r in pd.read_csv(O/'evidence/SOURCE_MANIFEST.csv').itertuples():check('source preserved '+r.path,sha(r.path)==r.sha256)
for p,h in originhash.items():check('audit source preserved '+p,sha(p)==h)
csv('evidence/ADDITIONAL_AUDIT_SOURCES.csv',[dict(path=p,sha256=h) for p,h in originhash.items()])
csv('evidence/INDEPENDENT_AUDIT.csv',checks)

# Pairwise interactions in final DC: finite mixed differences with matched trajectory sum.
base=mass[(mass.model=='T08')&(mass.S_q==195.959596)&(mass.S_u==1)&(mass.S_V==3.5)&(mass.S_extra==0)&(mass.LP_q==171.875)&(mass.S_np==1.1)&(mass.S_qn==360)&(mass.S_fn==.98)&(mass.LP_np==1.1)&(mass.LP_qn==360)&(mass.LP_fn==.98)].iloc[0]
dcbase=su[su.case_id==base.case_id]
DCI=[]
for family,g in mix[mix.family.isin(['q_V','q_u','q_extra','u_extra'])].groupby('family'):
    g=g.copy();g['x_value']=pd.to_numeric(g.x_value);g['y_value']=pd.to_numeric(g.y_value)
    x,y=g.iloc[0]['x'],g.iloc[0]['y'];xa=float(g.iloc[0].x_anchor);ya=float(g.iloc[0].y_anchor)
    for r in g.itertuples():
        # All one-axis anchors are in sampled Cartesian designs (base values included).
        gx=g[(np.abs(g.x_value-r.x_value)<1e-8)&(np.abs(g.y_value-ya)<1e-8)]
        gy=g[(np.abs(g.x_value-xa)<1e-8)&(np.abs(g.y_value-r.y_value)<1e-8)]
        if len(gx)!=1 or len(gy)!=1:continue
        for rc in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
            def val(cid):return su[(su.case_id==cid)&(su.rolling_case==rc)].mean_delta_Wh.iloc[0]
            dc_inter=val(r.case_id)-val(gx.case_id.iloc[0])-val(gy.case_id.iloc[0])+val(base.case_id)
            DCI.append(dict(family=family,case_id=r.case_id,rolling_case=rc,x_value=r.x_value,y_value=r.y_value,mass_mixed_difference_kg=r.mixed_difference_kg,mean_DC_mixed_difference_Wh=dc_inter,
                            definition='matched finite mixed difference in mean saving; deterministic, no significance test'))
csv('data/DC_MIXED_DIFFERENCES.csv',DCI)

# Three-factor anode contrasts versus fixed LP and common anode redesign.
anodes=mass[mass.case_id.isin(members[members.family.str.startswith('NP_qn_fn')].case_id)].copy()
rows_an=[]
for _,g in anodes.groupby(['S_np','S_qn','S_fn']):
    for r in g.itertuples():
        mode='COMMON_ANODE' if np.allclose([r.LP_np,r.LP_qn,r.LP_fn],[r.S_np,r.S_qn,r.S_fn]) else 'S_ONLY'
        rows_an.append(dict(case_id=r.case_id,comparison=mode,NP=r.S_np,qn_Ah_kg=r.S_qn,fn=r.S_fn,
                             negative_active_kg=r.S_negative_active_kg,negative_coating_kg=r.S_negative_coating_kg,
                             LP_pack_kg=r.LP_mass_or_known_kg,S_pack_kg=r.S_mass_or_known_kg,delta_kg=r.delta_mass_kg))
ant=csv('data/ANODE_DESIGN_COMPARISON.csv',rows_an)
anodemixed=[]
def anoded(n,qn,fn):
    # Original per-cell callable, fixed LP, independent of the analysis mass helper.
    sc=copy.deepcopy(template)
    for key,value in [('q_ref',195.959596),('np_ratio',n),('q_negative',qn),('f_negative',fn)]:
        sc['parameters'][key]['value']=value
    return run['M0']-pack_budget(sc)['pack_mass_kg']
anchor=dict(n=1.1,qn=360.,fn=.98)
for family,x,y,xs,ys in [('NP_qn','n','qn',[1.,1.1,1.2],[300.,360.,400.]),('NP_fn','n','fn',[1.,1.1,1.2],[.94,.98,.99]),('qn_fn','qn','fn',[300.,360.,400.],[.94,.98,.99])]:
    for xv,yv in itertools.product(xs,ys):
        p=anchor|{x:xv,y:yv}
        mixed=anoded(**p)-anoded(**(anchor|{x:xv}))-anoded(**(anchor|{y:yv}))+anoded(**anchor)
        anodemixed.append(dict(family=family,x_value=xv,y_value=yv,mixed_difference_kg=mixed,comparison='S_ONLY_LP_FIXED',anchor='NP1.1 qn360 fn0.98'))
for n,qn,fn in itertools.product([1.,1.1,1.2],[300.,360.,400.],[.94,.98,.99]):
    mixed=0.
    for bits in itertools.product([0,1],repeat=3):
        pp=dict(n=n if bits[0] else 1.1,qn=qn if bits[1] else 360.,fn=fn if bits[2] else .98)
        mixed+=(-1)**(3-sum(bits))*anoded(**pp)
    anodemixed.append(dict(family='NP_qn_fn_THIRD_ORDER',x_value=n,y_value=qn,fn=fn,mixed_difference_kg=mixed,comparison='S_ONLY_LP_FIXED'))
amt=csv('data/ANODE_MIXED_DIFFERENCES.csv',anodemixed)
policies=[]
z=mass[mass.model=='T09']
for keys,g in z.groupby(['S_L','S_ep','S_en']):
    if len(g)!=2:continue
    a=g[g.policy=='fixed_loading'].iloc[0];b9=g[g.policy=='fixed_area_LP'].iloc[0]
    policies.append(dict(L_kg_m2=keys[0],ep=keys[1],en=keys[2],fixed_loading_known_delta_kg=a.delta_mass_kg,
                         fixed_area_known_delta_kg=b9.delta_mass_kg,policy_gap_kg=a.delta_mass_kg-b9.delta_mass_kg,
                         delta_Al_kg=b9.S_Al_kg-a.S_Al_kg,delta_Cu_kg=b9.S_Cu_kg-a.S_Cu_kg,
                         delta_separator_kg=b9.S_separator_kg-a.S_separator_kg,delta_liquid_kg=b9.S_liquid_kg-a.S_liquid_kg))
pt=csv('data/T09_POLICY_COMPARISON.csv',policies)
unknownreps=[]
for policy in ['fixed_loading','fixed_area_LP']:
    g=mass[mass.policy==policy]
    if policy=='fixed_loading':g=g[g.model=='T09']
    baseline9=g[(g.S_L==.1)&(g.S_ep==.25)&(g.S_en==.25)].iloc[0]
    for offset in [-1.,0.,1.]:
        bk=baseline9.delta_mass_kg;du=bk+offset;d=bk-du
        check('T09 representative unknown sign '+policy+str(offset),abs(d+offset)<1e-10)
        unknownreps.append(dict(policy=policy,known_difference_kg=bk,unknown_S_minus_LP_kg=du,delta_complete_pack_kg=d,
                                LP_complete_pack_kg=None,S_complete_pack_kg=None,interpretation='hypothetical unknown DIFFERENCE only; absolute unknowns remain NULL'))
csv('data/T09_UNKNOWN_REPRESENTATIVES.csv',unknownreps)

# Preserve the adopted source classification and annotate each numerical axis separately.
shutil.copyfile(OLD/'data/PARAMETER_ADOPTION.csv',O/'data/INHERITED_PARAMETER_ADOPTION.csv')
provenance=[]
empirical=dict(q='RETENTION_DERIVED_REFERENCE_NOT_INITIAL_MEASUREMENT',fp='REPORTED_COIN_CELL_RECIPE_TRANSFERRED_TO_HYPOTHETICAL_FULL_CELL',
               rhop='OTHER_CHEMISTRY_THEORETICAL_DENSITY_TRANSFER',rhon='MATHEMATICAL_DESIGN_POINT',
               al='OTHER_DESIGN_REFERENCE',cu='OTHER_DESIGN_REFERENCE',sep='CROSS_PRODUCT_REFERENCE_DERIVATION',
               rhol='OTHER_PRODUCT_REFERENCE_TRANSFER',ts='MANUFACTURER_TYPICAL_REFERENCE_TRANSFER',es='MANUFACTURER_TYPICAL_REFERENCE_TRANSFER')
for key in mapping.keys()|{'rhop','rhon','L','ep','en','al','cu','sep','rhol','ts','es','wet','sat','nf','excess','unavail'}:
    vals=sorted(mass['S_'+key].dropna().unique())
    for val in vals:
        baseline_val=float(mass[mass.case_id==base.case_id]['S_'+key].iloc[0])
        cls=empirical.get(key,'INHERITED_MODEL_ASSUMPTION') if np.isclose(val,baseline_val,rtol=1e-11,atol=1e-12) else 'MATHEMATICAL_EXPLORATION'
        if key=='q' and np.isclose(val,171.875):cls='RETENTION_DERIVED_REFERENCE_NOT_INITIAL_MEASUREMENT'
        provenance.append(dict(parameter=key,value=val,input_class=cls,source='data/INHERITED_PARAMETER_ADOPTION.csv; EXPERIMENT_DESIGN.md',
                                target_experiment='NO_MATCHED_TARGET_FULL_CELL_MEASUREMENT',practical_adoption='HOLD'))
csv('data/PARAMETER_PROVENANCE.csv',provenance)

# Compact numerical evidence tables used verbatim in report.
baseops=[];extreme=[]
for rc,g in op.groupby('rolling_case'):
    baseops.append(dict(Crr=rc,LP合計_Wh=g.LP_DC_Wh.sum(),S合計_Wh=g.S_DC_Wh.sum(),差合計_Wh=g.delta_DC_Wh.sum(),平均差_Wh=g.delta_DC_Wh.mean(),最小差_Wh=g.delta_DC_Wh.min(),最大差_Wh=g.delta_DC_Wh.max(),削減率_pct=100*g.delta_DC_Wh.sum()/g.LP_DC_Wh.sum()))
    for typ,idx in [('最小Wh',g.delta_DC_Wh.idxmin()),('最大Wh',g.delta_DC_Wh.idxmax())]:
        r=op.loc[idx];extreme.append(dict(Crr=rc,point=typ,trajectory_sha256=r.trajectory_sha256,distance_km=r.distance_km,mean_speed_kmh=r.mean_speed_kmh,rms_acceleration_m_s2=r.rms_acceleration_m_s2,restarts_per_km=r.restarts_per_km,LP_Wh=r.LP_DC_Wh,S_Wh=r.S_DC_Wh,差_Wh=r.delta_DC_Wh,差_Wh_km=r.delta_Wh_per_km,差_Wh_kg=r.delta_Wh_per_kg))
bot=csv('data/BASELINE_SUMMARY.csv',baseops);et=csv('data/DRIVING_EXTREMES.csv',extreme)
components=[]
for rc,g in op.groupby('rolling_case'):
    components.append(dict(Crr=rc,W1転がり合計_Wh=g.W1_rolling_Wh.sum(),W2空力差_Wh=0.,W3並進合計_Wh=g.W3_translation_Wh.sum(),W4回転差_Wh=0.,正枝補正合計_Wh=g.branch_correction_Wh.sum(),切替区間数=g.switch_intervals.sum(),正枝補正最小_Wh=g.branch_correction_Wh.min(),正枝補正最大_Wh=g.branch_correction_Wh.max()))
cot=csv('data/BASELINE_COMPONENT_SUMMARY.csv',components)
sel=[]
for fam in ['q_V','q_u','q_extra','u_extra']:
    g=mass[mass.case_id.isin(members[members.family==fam].case_id)]
    for typ,idx in [('最小差',g.delta_mass_kg.idxmin()),('最大差',g.delta_mass_kg.idxmax())]:
        r=g.loc[idx];d=su[(su.case_id==r.case_id)&(su.rolling_case=='CRR_LOWER_BOUND')].iloc[0]
        sel.append(dict(family=fam,点=typ,case_id=r.case_id,q_Ah_kg=r.S_q,u=r.S_u,V_V=r.S_V,extra_kg=r.S_extra,LP_kg=r.LP_mass_or_known_kg,S_kg=r.S_mass_or_known_kg,差_kg=r.delta_mass_kg,平均DC差_Wh=d.mean_delta_Wh))
st=csv('data/INTERACTION_EXTREMES.csv',sel)

design='''# 追加計算の分析設計

T08を条件付き完成質量・走行DCの主モデル、T09を幾何・既知部材小計の補完モデルとする。目的は材料からDCへの効果伝達条件の評価であり、実用パック予測ではない。既存239行を入力fingerprint（小数11桁の同定、質量は別途1e-8kg以内で確認）で整理し、DC115条件との重複を照合した。再現用評価と新規入力の評価を区別する。

入力は固定のgross20,000Wh、usable18,000Wh、100セル、LP参照q=171.875、S参照q=195.959596Ah/kg。qは保持率からの逆算参照で、初回放電の実測値ではない。平均全電池電圧3.5V、利用率1、正極活物質割合.75、負極360Ah/kg・活物質割合.98・N/P1.1、セルその他19kg/pack、packその他15kgは既存条件の継承である。対象セルでの適格性はHOLD。

|設計|探索点|比較方法|
|---|---|---|
|q×V|q=150〜240Ah/kgの9点＋171.875/195.959596、V=3.0〜3.8Vの9点|LP固定、Sのみ変更|
|q×u|同q、u=.7〜1の9点|LP固定、Sのみ変更|
|q×追加質量|同q、extra=0〜20kgの9点＋既存相殺点|LP固定、Sのみ変更|
|u×追加質量|u=.7〜1の9点＋既存相殺点、同extra|LP固定、Sのみ変更|
|担持×正極空隙×負極空隙|L=.02/.05/.10/.15/.20kg活物質/m²片面、ep/en=.25/.35/.45|fixed_loading / fixed_area_LP別、LP基準固定|
|N/P×qn×fn|1/1.1/1.2 × 300/360/400Ah/kg × .94/.98/.99|Sだけ変更と、LP/S共通負極変更を分離|
|局所感度と一要因範囲|上記の各軸の端点、解析微分|入力の1%を共通診断幅、extraは1kg基準幅の1%|
|既存その他・配合感度の再利用|fp=.75〜.96、cell_other=.095〜.285kg/cell、pack_other=7.5〜22.5kg/pack|LP固定、保存DC条件を同じ正規化で評価|
|境界連続評価|q181点、u121点、q-u31×31面、T09 L19×ep5×en5×2方針|解析式代入と符号確認|

すべての新規点は数学的設計探索であり、実験範囲・製造可能範囲・確率区間ではない。u>1や追加質量<0となる境界は、基本定義域外または差質量の数学的領域と表示する。0<u<=1等の基本定義域を満たしても物理的達成を確認したことにはならない。担持量.02kg/m²=2mg/cm²は原著記載の担持範囲に重なるが、当該q・全電池・空隙・電圧との組合せは実測されていない。

T09のfixed_area_LPは既存S-only定義を継承する。LP基準面積を維持し、S設計基準面積をA_LP(L)=E/(3.5 qLP L)とする。L=.10だけLP/S面積一致、L変更はS側設計基準面積の介入である。LP側の基準担持.10を同時変更する比較ではない。両材料を同じ条件に再設計する比較とは区別する。

正値化DCのE(m)=Σmax(a_i m+c_i,0)/.9を利用し、検証質量区間で常時正の区間と切替区間へ厳密分解する。核の式・定数・軌跡・車両置換を変更しない。既存DC条件は保存絶対値を再利用し、圧縮式との一致を確認。新規条件も同一質量なら一度だけ計算する。460軌跡全部で基準2質量を凍結evaluateへ照合し、短・中・長3観測窓では全ユニーク質量を直接照合する。

軌跡の平均速度は右端速度積算距離/観測時間、加速度は隣接速度差/1s、RMSは全区間、停止はv<=.1m/s、再発進はその閾値の上向き横断、頻度は回/km。停止割合は保存サンプル割合。走行距離・速度・加減速・停止の層別は有限集合の記述統計であり、交絡を除いた走行因果効果とはしない。CRR二条件は係数包絡で、タイヤ圧を介入した実験でも独立標本でもない。parent/group情報を保存し、検定、独立標本推定、信頼区間、発生確率は算出しない。

W1=転がり、W2=空力、W3=並進、W4=回転。LP正枝maskを用いる会計で成分差と枝切替補正を分ける。寄与配分はこの基準mask規約に依存し、一意の物理因果配分ではない。回生・HVAC・勾配・停止時補機・旋回固有損失・未知の観測末端区間は既存対象外のままとする。長い停車時間の補機消費を0Whの実測と解釈しない。

入力出典は既存PARAMETER_ADOPTION.csv、STAGE_TRANSMISSION_TABLE.csv、FINAL_AUDIT.csvを参照。追加計算で新規文献値を採用していない。未確定実物入力は推定分布に置換しない。論文の変更、QAOA/SUMOの再実行は行わない。
'''
(O/'EXPERIMENT_DESIGN.md').write_text(design)

comparability='''# T08/T09比較可能性

共通するのはE/Vからの必要Ah、正極活物質/乾燥添加材、負極活物質/乾燥添加材。今回の負極loss=0で共通だが、T09の未利用負極容量を導入した場合はT08の有効qn定義との整合を先に取る必要がある。

|会計対象|T08|T09|比較上の注意|
|---|---|---|---|
|正負極乾燥塗工材|明示|明示|E,V,q,u,fp,NP,qn,fnが一致すれば比較可|
|箔・膜・電解液|19kg/packのcell_other内に集約|面積・厚さ・空隙から明示|T08の19kgへT09部材を追加すると二重計上|
|セル外装・タブ・端子・余白|cell_otherへ集約した仮定|未確定|既知小計の差と完成質量差を同一視できない|
|パック構造・冷却・BMS・配線|pack_other=15kgの仮定|未確定|T08固定値をT09へ黙って足さない|
|材料固有追加部材|明示extra|未知BOM差へ含める|共通部材との差を二重に加えない|
|電極面積・厚さ・空隙液・箔共有|内部幾何を解かない|明示|T09にのみある算定経路。物理部材自体がT08から除外された意味ではない|
|完成質量・絶対走行質量・絶対DC|条件付き数値可能|HOLD|未知質量を0へ置換不可|

T08にだけ明示される質量は19kgと15kgの一括仮定、extraである。T09にだけ明示されるのはAl、Cu、膜、液およびそれらの幾何依存性。いずれも会計解像度の差であり、T08に電解液が存在しないという意味ではない。

T09でKを既知小計、Uを未測定部材総量とし、U_LP,U_S>=0、δU=U_S−U_LPとする。完成質量差はD=K_LP−K_S−δU=bK−δU。δU<bKで軽量、等号で消失、δU>bKで逆転。δU自体は負にもなれる。δU=0を仮定する例は「未知差が等しい」仮説であり、U_LP=U_S=0の補完ではない。任意の有限δUは十分大きな非負共通Uを取れば代数上構成できるが、そのBOMが実在する証拠にはならない。

両モデルの完成差を直接比較するには、同一エネルギー・Ah基準・平均電圧・損失定義・活物質割合・負極設計を揃え、T08一括その他とT09既知＋未知BOMの会計範囲を一致させ、面積比較方針も指定する必要がある。未知部材がLP/Sで相殺される根拠があるときに限り、T09既知差を完成差へ昇格できる。絶対未知質量が未確定なら、その場合でも完成パック絶対質量とDC絶対値はHOLD。

基準ではT08正極乾燥材の差5.448297415kg、負極差0kgに対し、T09固定担持の既知差9.722608121kgは面積依存材の削減を含む。固定面積の既知差5.977891152kgでは箔・膜が相殺され、正極空隙液の削減が加わる。したがってT09の値が大きいことはT08の誤り、あるいは実用パックの軽量化が大きいことの証拠ではない。担持・空隙・密度の同時達成、外装/タブ/構造/冷却の測定が必要である。既存ROW183の対向FAILや道路受入FAILは本計算の算術一致で解除しない。
'''
(O/'T08_T09_COMPARABILITY.md').write_text(comparability)

# Explicit run settings and source lineage, without fabricated probabilities.
settings=dict(task='T08 T09 additional interaction and boundary evaluation',date='2026-11-05',
              root=str(R),output=str(O),archive_root=str(U),base_reference=dict(q_LP=171.875,q_S=195.959596,V=3.5,u=1,fp=.75,fn=.98,qn=360,NP=1.1,E_Wh=20000,usable_Wh=18000),
              trajectories=460,Crr_cases=['CRR_LOWER_BOUND','CRR_UPPER_BOUND'],
              execution='analyze.py then audit_and_report.py; T08_T09_OUTPUT overrides output',
              numerical_tolerance=dict(original_mass_kg=1e-8,direct_DC_Wh=1e-7,boundary_kg=1e-9),
              statistical_inference='none; dependent deterministic finite trajectories',
              range_interpretation='mathematical exploration; practical adoption HOLD',run_result=run)
(O/'RUN_CONFIG.json').write_text(json.dumps(settings,indent=2,ensure_ascii=False)+'\n')

claims=[
 ('C01','指定6値は表示精度内で再現','evidence/REPRODUCTION.csv; evidence/NUMERICAL_AUDIT.csv','GO','数値再現の確認、入力の実物適格性を意味しない'),
 ('C02','正極q改善は共通V/u/fp/負極で正極必要量のみを減らす','INTERACTION_RESULTS.csv; data/ANODE_DESIGN_COMPARISON.csv','GO_MODEL','負極量はqに依存しない'),
 ('C03','q×V、q×uには質量の非加算効果がある','data/MIXED_DIFFERENCES.csv; data/DC_MIXED_DIFFERENCES.csv','GO_MODEL','探索された有限差分、製造可能性未検証'),
 ('C04','q×追加質量、u×追加質量は質量上加算的','data/MIXED_DIFFERENCES.csv; BOUNDARY_SURFACES.csv','GO_MODEL','同時にゼロ境界を跨ぐため実用判断上は結合条件'),
 ('C05','担持×空隙率は現T09の独立入力式で加算的','data/MIXED_DIFFERENCES.csv; INTERACTION_RESULTS.csv','GO_MODEL','独立物性達成の証明ではなく式の分離可能性'),
 ('C06','負極共通再設計でq由来絶対質量差は不変','data/ANODE_DESIGN_COMPARISON.csv','GO_MODEL','共通V等の条件下、S-only再設計では異なる'),
 ('C07','連続相殺境界と符号を解析・数値で確認','BOUNDARY_SURFACES.csv; data/BOUNDARY_REPRESENTATIVES.csv; evidence/NUMERICAL_AUDIT.csv','GO_MODEL','基本定義域外の根を物理採用しない'),
 ('C08','5.448kgによるDC差は軌跡・Crrに依存','data/BASELINE_SUMMARY.csv; DC_INTERACTION_RESULTS.csv; data/DRIVING_EXTREMES.csv','CONDITIONAL GO','保存観測窓の駆動DC限定、独立実験ではない'),
 ('C09','W1/W3と正枝補正でDC差を閉じる','data/BASELINE_COMPONENT_SUMMARY.csv; evidence/INDEPENDENT_AUDIT.csv','GO_MODEL','基準正枝maskの会計規約'),
 ('C10','正極容量・全電池平均電圧・利用率・正極配合等の局所効果とその他質量の範囲効果を区別','FACTOR_IMPORTANCE.csv','CONDITIONAL GO','正規化と探索幅に依存、確率的寄与率ではない'),
 ('C11','T09完成差は既知差−未知差','T08_T09_COMPARABILITY.md; BOUNDARY_SURFACES.csv','GO_MODEL','未知差を記号変数として保持'),
 ('C12','T09完成絶対質量と絶対DCは確定できない','INTERACTION_RESULTS.csv; T08_T09_COMPARABILITY.md','HOLD','未知BOMと実物入力不足'),
 ('C13','Chen逆算値は初回放電実測として採用しない','EXPERIMENT_DESIGN.md; data/INHERITED_PARAMETER_ADOPTION.csv','HOLD','保持率分母・cycle/activation未確定、原著再取得なし'),
 ('C14','量子計算による材料改善実証を主張しない','FINAL_REPORT_JA.md','GO_SCOPE','本追加計算は古典的条件付き変換評価'),
 ('C15','既存成果物・論文・凍結核・原軌跡を保存','evidence/SOURCE_MANIFEST.csv; evidence/INDEPENDENT_AUDIT.csv','GO','読み取り対象のSHA256照合'),
]
csv('CLAIM_EVIDENCE_MATRIX.csv',[dict(claim_id=a,claim=b,evidence=c,decision=d,limit=e) for a,b,c,d,e in claims])

# Report: numerical discoveries, algebraically certain relationships, assumptions, and HOLD separated.
local=fac[(fac.model=='T08')&(fac.rolling_case=='CRR_LOWER_BOUND')]
localtab=local[['factor','local_delta_saving_kg_for_step','local_mean_delta_DC_Wh_for_step','mass_range_span_kg','min_mean_DC_saving_Wh','max_mean_DC_saving_Wh']].copy()
localtab.columns=['因子','局所軽量差_kg','局所平均DC差_Wh','探索質量幅_kg','探索最小平均DC差_Wh','探索最大平均DC差_Wh']
mixedtab=mix.groupby('family').mixed_difference_kg.agg(['min','max']).reset_index()
t9tab=[]
for policy,g in mass[mass.model=='T09'].groupby('policy'):
    for label,idx in [('最小既知差',g.delta_mass_kg.idxmin()),('最大既知差',g.delta_mass_kg.idxmax())]:
        r=g.loc[idx];t9tab.append(dict(方針=policy,点=label,L_kg_m2=r.S_L,ep=r.S_ep,en=r.S_en,LP既知_kg=r.LP_mass_or_known_kg,S既知_kg=r.S_mass_or_known_kg,既知差_kg=r.delta_mass_kg))
t9tab=pd.DataFrame(t9tab)
anoderanges=ant.groupby('comparison').agg(負極活物質最小_kg=('negative_active_kg','min'),負極活物質最大_kg=('negative_active_kg','max'),負極塗工材最小_kg=('negative_coating_kg','min'),負極塗工材最大_kg=('negative_coating_kg','max'),質量差最小_kg=('delta_kg','min'),質量差最大_kg=('delta_kg','max')).reset_index()
reps=pd.read_csv(O/'data/BOUNDARY_REPRESENTATIVES.csv')
repmerged=reps.merge(mass[['case_id','LP_mass_or_known_kg','S_mass_or_known_kg']],on='case_id').merge(su[su.rolling_case=='CRR_LOWER_BOUND'][['case_id','mean_delta_Wh']],on='case_id')
csv('data/BOUNDARY_REPRESENTATIVE_DC.csv',repmerged)
range_whkm={rc:(g.delta_Wh_per_km.min(),g.delta_Wh_per_km.max()) for rc,g in op.groupby('rolling_case')}
range_slope={rc:(g.delta_Wh_per_kg.min(),g.delta_Wh_per_kg.max()) for rc,g in op.groupby('rolling_case')}
rho=csv('data/DESCRIPTIVE_CORRELATIONS.csv',pd.read_csv(O/'data/DESCRIPTIVE_CORRELATIONS.csv'))
lines=[]
for rc,g in op.groupby('rolling_case'):
    lines.append(f"{rc}: 距離当たり差{g.delta_Wh_per_km.min():.6f}〜{g.delta_Wh_per_km.max():.6f} Wh/km、質量1kg当たり差{g.delta_Wh_per_kg.min():.6f}〜{g.delta_Wh_per_kg.max():.6f} Wh/kg。平均速度{g.mean_speed_kmh.min():.3f}〜{g.mean_speed_kmh.max():.3f} km/h、距離{g.distance_km.min():.3f}〜{g.distance_km.max():.3f} km。")
report=rf'''# T08・T09追加計算：因果経路2の成立条件・消失境界・交互作用

## 判定と研究範囲

**CONDITIONAL GO**：T08の条件付き質量・DC伝達とT09の既知部材構造に関する追加計算・数値監査を完了した。数学的関係の採用はGO。対象実用電池の性能予測、Chen逆算値の初回容量採用、T09完成パックの絶対質量・絶対走行DCはHOLDとする。今回の結果は材料改善を量子計算で実現した成果ではない。

既存最終採用報告を読取り専用の出発点とし、指定6値をすべて表示丸め精度内で再現した。追加の質量計算へ進む前の再現ゲートはPASS（evidence/REPRODUCTION.csv）。元の5.448297415kg等は既存再現値、新しい探索点・連続境界・複数因子交互作用は本runの追加結果としてorigin列で区別した。論文原本と既存成果物を変更していない。

## 再現・重複整理と入力の意味

{table(pd.read_csv(O/'evidence/REPRODUCTION.csv'),['item','recomputed','reported','unit','status'],9)}

既存239質量行は入力条件でまとめると{run['old_unique_inputs']}条件、既存T08の115 DC条件は{run['old_unique_T08']}入力条件となる。重複一覧はdata/EXISTING_CASE_INVENTORY.csv。今回の出力は{run['mass_cases']}ユニーク比較条件、うち新規入力{run['new_inputs']}、既存入力再利用{run['reused_inputs']}。T08は{run['T08_cases']}条件×460軌跡×2Crr＝{run['DC_rows']:,}対応DC行。実際のユニーク走行質量は{run['unique_masses']}点で、同質量を重複してエネルギー計算しない。保存DC再利用{origins.get('EXISTING_DC_REUSED',0):,}行、新規DC{origins.get('NEW_DC',0):,}行を区別した。

460軌跡、二つのCrr、複数の材料条件は独立反復ではない。全結果は同じ保存軌跡の対応比較であり、p値・信頼区間・出現確率を付与しない。軌跡のparent/group情報もdata/TRAJECTORY_METRICS.csvに保持した。合計Whはこの有限保存集合の和で、配送フリート年間消費ではない。

qLP=171.875、qS=195.959596Ah/kgはChen(2020)の100cycle容量と保持率からの逆算参照値。初回実測値ではない。原著の実験記載、他化学系/別製品の文献参照、継承したモデル仮定、新規探索値を区別する。対象黒鉛全電池でV=3.5Vやu=1を実測したものではない。新規のq=150〜240、V=3〜3.8、u=.7〜1、extra=0〜20等は実現性や独立変更可能性が未検証の数学的探索である。既存出典台帳を引き継ぎ、新規文献値・実験値は採用していない。

## 算定式と連続成立境界

E=20000Wh、f_p=.75、N/P=n、q_n、f_nとし、C=100m_cell_other+F_pack=34kg、δ=追加質量S−LPとする。今回のS設計では

\[M_S=\frac{{E}}{{V_S}}\left(\frac{{1}}{{q_S u_S f_p}}+\frac{{n_S}}{{q_{{nS}}f_{{nS}}}}\right)+C+\delta,\quad D=M_{{LP}}-M_S.\]

正極活物質=E/(Vqu)、正極塗工材=E/(Vquf_p)、負極活物質=En/(Vq_n)、負極塗工材=En/(Vq_nf_n)。平均電圧を下げると必要Ahが増え、正負極の両方が重くなる。qだけを上げても負極は軽くならない。質量単位はWh/V=Ah、Ah/(Ah/kg)=kg。

以下の境界面ではC_LP=C_S=34kgを固定する。その他質量の感度ではC_Sのみを変え、その差100Δm_cell_other+ΔF_packはδへ合算できる。正極配合fpの感度も別途評価し、境界図では.75へ固定する。

A=n_S/(q_n f_n)、B=M_LP−C−δと置けば、B>0で平均電圧境界は

\[V_*(q,u,\delta)=E\left[1/(quf_p)+A\right]/B.\]

V>V*でD>0。容量・利用率境界は、V B/E−A>0のとき

\[q_*=[u f_p(VB/E-A)]^{{-1}},\qquad u_*=[q f_p(VB/E-A)]^{{-1}}.\]

q>q*またはu>u*でD>0。この分母が0以下なら、正の有限q/uでS優位を得る根は存在しない。追加質量境界は

\[\delta_*(q,u,V)=M_{{LP}}-C-\frac{{E}}{{V}}[1/(quf_p)+A],\quad D=\delta_*-\delta.\]

共通V・負極・配合、δ=0ならq u>qLP uLPが必要十分。今回uLP=1。q−u境界はu*=171.875/q。u*≤1を満たすのはq≥171.875。qがLPより低いとu≤1では共通条件の容量由来優位を作れない。δ≥0でV/u等が共通なら、q→∞でも軽量化の上限はLP正極塗工材44.329004329kg。これを超える追加質量はq改善だけでは相殺できない。

BOUNDARY_SURFACES.csvにq−V、q−u、q−追加質量、u−追加質量、q/u依存の追加質量面、T09既知差−未知差の連続標本を保存した。解析根の代入残差は最大{bounds.mass_residual_kg.abs().max():.3g}kg。各q断面で根の両側の符号を確認し、代表点をDCへ接続した。数学的に根が存在しても物理的達成はUNVERIFIED。u>1やδ<0の領域は定義域と区別する（δは差質量として負を許せるが、S専用追加部材の必要量としては負にできない）。

{table(repmerged,['boundary','offset','LP_mass_or_known_kg','S_mass_or_known_kg','delta_mass_kg','mean_delta_Wh'])}

上表はCRR_LOWER_BOUNDの460軌跡平均DC差。相殺点は数値丸め残差内で0Wh、内外で質量とDCの符号が一致する。正の質量削減はLP−S、正のDC差はLP−Sで一貫させた。

代表根の条件は、q=180/u=1でV*=3.387307214V、q=210/V=3.5でu*=.818452381、q=210/u=1/V=3.5でδ*=8.047825191kg、q=195.959596/u=.9/V=3.5でδ*=1.128218869kg。offsetの単位はそれぞれV、無次元、kg、kgである。利用率を1から.9に下げると、基準の追加部材許容量は5.448297415から1.128218869kgへ縮小する。

## 複数因子の追加結果

{table(st)}

同じ容量改善でも、電圧低下・利用率低下・追加部材によって軽量化が縮小、消失、逆転する。上表は宣言した探索域の端点であり、実際の材料がとり得る最小/最大性能ではない。INTERACTION_RESULTS.csvには各条件の正負極活物質、乾燥塗工材、実効容量、LP/S絶対質量、差分を保存した。

交互作用はD(x,y)−D(x,y0)−D(x0,y)+D(x0,y0)という有限差分で測定した。アンカーはS基準値で、単位kg。

{table(mixedtab)}

q×V、q×uは1/(Vqu)の積構造に由来する非加算関係を持つ。容量効果の絶対kgは低V/低uほど大きくなり得るが、Sの絶対質量も増えるため「効果が大きい」と「LPより軽い」を区別する。q×追加質量、u×追加質量は質量式では加算的で、有限交互作用は丸め誤差程度である。それでもδ*がq/uに依存するため、成立判断は結合条件である。DCは正枝が変わる区分線形関数なので、質量上加算的な条件でもDC上は微小な非加算成分が残り得る（data/DC_MIXED_DIFFERENCES.csv）。これは枝切替による決定論的効果で、統計的相互作用の検定ではない。

## T09：担持量と両極空隙率、未知部材差

{table(t9tab)}

正極担持量は活物質kg/片面塗工面積m²、.1kg/m²=10mg/cm²。固定担持ではS正極活物質の減少が面積・Al/Cu箔・膜・膜空隙液を減らす。固定面積方針では同じ担持基準L=.1でLP/Sの箔・膜面積が等しく、正極活物質の減少は塗工厚さと正極空隙液に伝わる。Lの変更はS側の基準面積を変える介入なので、全LでLP/Sが同面積という意味ではない。

T09の90条件（45組）の方針比較で、fixed_loadingとfixed_area_LPの既知差の隔たりは{pt.policy_gap_kg.min():.6f}〜{pt.policy_gap_kg.max():.6f}kg。基準で9.722608121対5.977891152kgとなる差3.744716969kgは、箔・膜・膜空隙液の面積依存分に対応する。data/T09_POLICY_COMPARISON.csvに部材別の差を保存した。

今回の固定密度・固定活物質量の式では、Lは面積材を変え、ep/enはpc/ρp×ep/(1−ep)、nc/ρn×en/(1−en)を介して電解液量を変える。したがってL×ep/enの質量有限差分は丸め誤差程度であり、両極空隙率の寄与も加算的。これはモデルの分離可能性という発見で、厚さ・担持・空隙・輸送特性が実物で独立に制御できる証拠ではない。担持量を増やすと厚さも増すが、輸送/出力制約は本モデルにない。

T09でK_LP−K_S=bK、未知部材差δU=U_S−U_LPとすれば完成差D=bK−δU。完成差の成立はδU<bK、消失は等号、逆転はδU>bK。外装・タブ・端子・箔余白・構造・冷却・BMS等の未確定量を0にしていない。既知小計の負の差も隠さず、未知差境界にそのまま伝える。U_LP/U_S≥0でもδUは負になり得る。完成パック絶対質量・相対削減率・絶対走行DCは全点HOLD。

## 負極設計の交互作用

{table(anoderanges)}

負極設計の2因子・3因子有限交互作用は、元のT08 per-cell関数を用いて同じアンカーから算定した（単位kg）。

{table(amt.groupby('family').mixed_difference_kg.agg(['min','max']).reset_index())}

m_n=E n/(Vq_n)、乾燥負極=m_n/f_nなので、N/P増加は線形に重くし、q_n/f_n改善は逆数で軽くする。f_nだけを変えても負極活物質量は変わらず、添加材量が変わる。NP×qn、NP×fnにはn/(q_n f_n)による交互作用がある。LPを固定してSのみ負極を悪化させる比較では、正極の容量改善余裕が負極追加質量で消失・逆転する。一方、両材料に同じ負極設計を適用しVも共通なら、負極質量は両側に同量加算され、q由来の絶対差5.448297415kgは不変。ただし完成質量に対する比率と、DCの正枝・基準電力量は変わり得る。この二つの比較を混同しない。

## 走行DC：絶対値、差分、成分

基準T08パック96.145654799→90.697357384kg、走行質量1140.034543688→1134.586246273kg。車両置換は1155−20000/180+Mpackを変更せず、運転者55kgを二重加算しない。回転等価61kgは固定。

{table(bot)}

{chr(10).join(lines)}

各軌跡・各追加条件のLP/S絶対Wh、差Wh、相対差%、Wh/km、Wh/kg、距離、速度、加減速、再発進頻度、Crr条件をDC_INTERACTION_RESULTS.csvへ保存した。質量差ゼロでWh/kgは未定義NULLとし、0/0を0で埋めていない。軌跡指標の完全版はdata/TRAJECTORY_METRICS.csv、Crrの距離加重平均はdata/BASELINE_OPERATION_RESPONSE.csv。

同じ5.448kgでも距離が長いほど転がり差が累積し、正枝での加速運動エネルギー差が加わる。減速の負仕事は回収せず、転がりや空力と合算した車輪仕事が正かどうかでDC消費が決まる。速度はCrrの速度項と空力に影響し、空力は質量に直接依存しないが基準消費と正枝条件を変える。停止時間自体の補機負担は対象外で、停止・再発進は速度履歴を介してのみ寄与する。

{table(et,['Crr','point','distance_km','mean_speed_kmh','restarts_per_km','LP_Wh','S_Wh','差_Wh','差_Wh_km','差_Wh_kg'])}

上の最小/最大行は距離なども異なる対応軌跡であり、停止頻度だけの因果効果を推定した比較ではない。距離・平均速度・RMS加速度・再発進/km・停止割合・正のΔv²量について層別とSpearman記述値を保存した（data/DRIVING_STRATA.csv、DESCRIPTIVE_CORRELATIONS.csv）。独立性や交絡除去を仮定しない。

W1転がり、W2空力、W3並進、W4回転を区間で合算してから正値化する。I0=1[W_LP>0]、IS=1[W_S>0]とすれば、差はΣI0(W_LP−W_S)/(3600η)+Σ(I0−IS)W_S/(3600η)。以下はこのLP正枝mask規約による会計である。

{table(cot)}

この会計でW3並進項が差合計に占める割合は、下限Crr {100*cot.iloc[0]['W3並進合計_Wh']/bot.iloc[0]['差合計_Wh']:.3f}%、上限Crr {100*cot.iloc[1]['W3並進合計_Wh']/bot.iloc[1]['差合計_Wh']:.3f}%。差Whが最大の軌跡は最小の軌跡の約{op[op.rolling_case=='CRR_LOWER_BOUND'].delta_DC_Wh.max()/op[op.rolling_case=='CRR_LOWER_BOUND'].delta_DC_Wh.min():.3f}倍であり、単一のWh/kgでは全軌跡を表せない。

W2/W4の直接差は0だが、DC絶対消費には存在する。W3の符号付き全行程和は端点速度差へ望遠和となるため、加速消費を説明する際には正枝maskによる寄与を用いる。正枝補正は枝が変わると生じ、各ケースのDC差を成分と合わせて厳密に再構成する。成分ごとを先に正値化する計算へ変更していない。

## 効果量・重要因子と不確実性

{table(localtab)}

局所列は共通の相対1%入力ステップによる一次応答。extraの基準値0は相対変化を定義できないので、明示した1kg基準幅の1%＝.01kgを用いた。u=1の微分は解析式の内側片側極限を評価し、u>1の物理設計を採用していない。表の正負はDC削減差の増減を表す。生のkg/入力単位をそのまま順位にしていない。FACTOR_IMPORTANCE.csvには無次元正規化微分も保存した。

正規化局所感度ではVがq/u/fpより大きく、q・u・fpは積q u fpとして同じ相対変化の効果を持つ。Vは正負極の両方へ作用する。その他質量の探索幅も大きく効くが、その仮定した幅が入力不確実性の分布を表すわけではない。探索端点の効果幅は宣言した範囲依存であり、局所順位とは別に提示した。T09ではLが面積部材を大きく変えるが、完成パックDCへの重要度へ直接ランキングできない。未知BOM差は1kgの差につき1kgだけ既知軽量化余裕を減らすが、範囲も分布も未確定なので確率的寄与率を付けない。

不確実性の主因は、逆算容量のcycle分母、Li対極から黒鉛全電池への移用、平均電圧と利用率、N/P・負極有効容量の定義、密度/空隙/担持/厚さの同時適格性、実電解液量、外装/構造BOM、保存軌跡の道路受入と観測境界である。これらを探索範囲へ一括置換した信頼区間や発生確率は算出していない。局所感度、探索効果幅、非加算交互作用、符号境界、入力根拠の不確実性をそれぞれ別の結果として扱う。

## 研究上の結論と未解決点

1. **容量改善が質量削減へ伝わる条件**：共通V/u/配合/負極/その他ではq増加が正極塗工材を減らす。一般条件は上記D>0。電圧・利用率・負極設計・追加部材を含めて判断する。
2. **縮小・消失・逆転**：V/u低下、Sだけの負極悪化、追加部材またはT09未知部材差が軽量化余裕を超えると逆転する。連続境界と代表点の符号は確認済み。
3. **何Wh伝わるか**：基準5.448297415kgは下限Crr平均12.916426Wh、上限13.265290Wh。保存軌跡全体で4.510089〜30.524351Wh。LP/S絶対Whを併記してあり、率だけの主張ではない。
4. **走行依存性**：同じ質量差でも転がり距離、速度、正枝加速、枝切替で変わる。460軌跡の有限対応記述に限定し、実配送母集団へ独立標本推定しない。
5. **T08/T09構造差**：T08はその他34kgを集約仮定、T09は面積・空隙依存材を明示して未知BOMを残す。既知差の大小を完成パックの優劣に読み替えない。比較条件はT08_T09_COMPARABILITY.md。
6. **実験不足でも確定する関係**：質量式の単調性、quの相殺関係、電圧/追加質量の解析境界、未知差bK−δU、現モデル内での加算/非加算構造、保存軌跡上のDC質量応答と成分閉合は数理的に確定できる。
7. **実測が必要な事項**：同条件全電池の初期/可逆容量、平均放電電圧、利用率・formation、電極物性と製造/出力/寿命/安全、完成BOM、実車DC。これらの実証採用はHOLDであり、今回の算術PASSで解除しない。

## 最終監査

主計算{run['checks']:,}件、別プロセスの独立した計算経路による追加監査{len(checks):,}件がPASS。独立監査は別研究者の査読を意味しない。全T08比較を元のper-cell pack_budgetと60桁Decimal式で照合。全460軌跡の基準LP/Sを凍結evaluateへ直接照合し、短・中・長3窓で{run['unique_masses']}ユニーク質量の両Crrを直接照合。保存CSV全{rows:,}行の差分、単位正規化、符号、成分和、460軌跡対応数を別プロセスで確認した。CSV丸め後の成分最大残差{maxclosure:.3g}Wh。stock最小{minstock:.6f}Whで非負。

検証走行質量区間は{run['mass_interval'][0]:.6f}〜{run['mass_interval'][1]:.6f}kg。各軌跡・Crrでこの区間全体のDC質量微分が正であり、この区間内でDの符号とDC差の符号が一致する。範囲外へ無条件に一般化しない。核は固定SHA256、入力と既存成果物・論文はevidence/SOURCE_MANIFEST.csvで実行前後一致。T09完成質量NULL、出典/探索区分、量子への不適切な帰属なし、回生/補機等の範囲維持を監査した。

数値計算・会計・境界のモデル内関係はGO、研究の条件付き利用はCONDITIONAL GO、実用完成パック/実車予測はHOLD。論文への統合は本タスクでは行わない。
'''
(O/'FINAL_REPORT_JA.md').write_text(report)

auditrows=[
 ('original six targets','PASS','evidence/REPRODUCTION.csv'),
 ('units and LP minus S signs','PASS','serialized all rows and Decimal/original budget'),
 ('analytic roots and numerical boundary signs','PASS','BOUNDARY_SURFACES.csv; NUMERICAL_AUDIT.csv'),
 ('design exploration distinguished from experiment','PASS','EXPERIMENT_DESIGN.md; INTERACTION_RESULTS.csv input_class'),
 ('frozen DC unchanged','PASS','SHA256; 460 endpoint pairs and 3 all-mass direct checks'),
 ('T09 unknown BOM remains symbolic and absolute masses NULL','PASS','T08_T09_COMPARABILITY.md; INDEPENDENT_AUDIT.csv'),
 ('dependence respected; no fabricated CI/probability','PASS','paired deterministic rows; parent/group retained'),
 ('practical full-cell and vehicle adoption','HOLD','missing measurements/BOM and road qualification'),
 ('quantum attribution excluded','PASS','CLAIM_EVIDENCE_MATRIX.csv C14'),
 ('thesis and original artifacts preserved','PASS','SOURCE_MANIFEST.csv'),
 ('research use verdict','CONDITIONAL GO','conditional references and structural model only')]
csv('evidence/FINAL_AUDIT.csv',[dict(audit=a,status=b,evidence=c) for a,b,c in auditrows])
csv('evidence/INDEPENDENT_AUDIT.csv',checks)
(O/'README.md').write_text('''# T08・T09追加計算

入口はFINAL_REPORT_JA.md。条件・探索範囲はEXPERIMENT_DESIGN.md、モデル比較はT08_T09_COMPARABILITY.md。

再実行はリポジトリrootで以下を実施する。出力環境変数を新しいパスにして旧成果物を保全する。

```bash
export T08_T09_OUTPUT="$PWD/review_outputs/t08_t09_interaction_boundaries_20261105/replay01"
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/t08_t09_interaction_boundaries_20261105/run01/scripts/analyze.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/t08_t09_interaction_boundaries_20261105/run01/scripts/audit_and_report.py
```

指定6値だけを先に確認するにはanalyze.pyに--reproduce-onlyを渡す。RUN_CONFIG.jsonは実行条件の記録で、数値仕様の正本はscripts/analyze.py。Python/numpy/pandas/matplotlibバージョンも記録。保存アーカイブへの絶対パス依存があり、この出力ディレクトリ単独では完全再現しない。SOURCE_MANIFEST.csvが必要入力とhashを列挙する。

INTERACTION_RESULTS.csvはユニーク比較条件の質量・部材、CASE_MEMBERSHIP.csvは複数の実験設計への所属、BOUNDARY_SURFACES.csvは連続境界の標本、DC_INTERACTION_RESULTS.csvは全対応軌跡の絶対Wh/差分/成分、FACTOR_IMPORTANCE.csvは局所/探索範囲効果。DC表のtrajectory_sha256でTRAJECTORY_METRICS.csvを結合すればparent/group・減速度・停止指標を取得できる。新旧区別はoriginとexisting_case_ids。data/に要約・層別・交互作用・境界代表点、figures/にPNG/PDF、evidence/に数値監査と保全hashを保存した。

削減差はLP−S、追加/未知部材差はS−LP。正の削減差がS優位。W1=転がり、W2=空力、W3=並進、W4=回転。空欄は未定義または未確定であり0ではない。
''')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(1,2,figsize=(11,4))
for qn in [300.,360.,400.]:
    g=ant[(ant.qn_Ah_kg==qn)&(ant.fn==.98)&(ant.comparison=='S_ONLY')].sort_values('NP')
    # Baseline anode is shared by both designs and appears only once in the unique-case table.
    if qn==360.:
        g=pd.concat([g,ant[(ant.qn_Ah_kg==360)&(ant.fn==.98)&(ant.NP==1.1)]]).drop_duplicates('NP').sort_values('NP')
    axs[0].plot(g.NP,g.delta_kg,'o-',label=f'qn={qn:g} Ah/kg')
axs[0].axhline(0,color='k',linewidth=.8);axs[0].set(xlabel='S N/P (1)',ylabel='LP-S conditional pack mass (kg)',title='T08: S-only anode redesign, fn=0.98');axs[0].legend(fontsize=8)
for p,bk in [('fixed_loading',9.722608121),('fixed_area_LP',5.977891152)]:
    xx=np.linspace(-10,25,101);axs[1].plot(xx,bk-xx,label=p)
axs[1].axhline(0,color='k',linewidth=.8);axs[1].set(xlabel='Unknown BOM difference U_S-U_LP (kg)',ylabel='LP-S COMPLETE pack mass difference (kg)',title='T09: symbolic difference, absolute masses HOLD');axs[1].legend(fontsize=8)
fig.suptitle('Conditional design exploration; qLP171.875/qS195.959596 Ah/kg, V3.5V, u1; no target full-cell measurement',fontsize=9)
fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/'figures'/('ANODE_AND_UNKNOWN_BOUNDARY.'+ext),dpi=180,bbox_inches='tight')
plt.close(fig)
(O/'figures/FIGURE_CAPTIONS_JA.md').write_text('''# 図の条件とデータ由来

全図は新規の条件付き設計探索で、対象パックの測定値ではない。正の差はLP−S。画像と同名PDFを保存。

- T08_BOUNDARY_MAPS：横軸q[Ah/kg]またはu[1]、縦軸V[V]・u[1]・追加質量[kg]。色は条件付きパック差kg、黒線は解析的相殺境界。E=20kWh、LPはq171.875/u1/V3.5、Sの他条件は基準固定。源泉INTERACTION_RESULTS.csv、BOUNDARY_SURFACES.csvと同じ解析式。材料入力は逆算参照と仮定。
- T09_LOADING_POROSITY：担持量mg/cm²（活物質/片面塗工面積）と既知小計差kg。LPはL10mg/cm²・ep/en=.25固定、Sのen=.25固定でepを比較。既知材のみ、外装/タブ/構造等は未確定、完成質量HOLD。固定面積方針のL変更はS基準面積の変更で、全LでLP/S同面積を意味しない。源泉INTERACTION_RESULTS.csv。
- DRIVING_INTERACTION：距離km、再発進/km、転がり寄与Wh、DC差WhまたはWh/km、並進寄与Wh。基準5.448297415kg軽量化、460保存軌跡×2Crr、凍結DC、回生/勾配/補機等対象外。観測窓限定、依存する軌跡の記述比較。源泉data/BASELINE_OPERATION_RESPONSE.csv。
- FACTOR_IMPORTANCE：局所1%入力の平均DC差Wh（extraのみ.01kgステップ）と、宣言探索範囲の平均DC差幅Wh。CRR_LOWER_BOUND、LP固定、460軌跡平均。u=1は内側微分の接線を表示しu>1設計を採用しない。源泉FACTOR_IMPORTANCE.csv、探索範囲はEXPERIMENT_DESIGN.md。範囲幅は確率不確実性ではない。
- ANODE_AND_UNKNOWN_BOUNDARY：左はN/P[1]、条件付き完成パック差kg、負極容量Ah/kg別、fn=.98固定のSのみ再設計。源泉data/ANODE_DESIGN_COMPARISON.csv。右はT09未知部材差kgと完成パック差kgの記号式bK−δU。LP/S絶対未知量を0にしていない。L=.1kg/m²・ep/en=.25、基準既知差を使用し、絶対質量/DCはHOLD。
''')
manifest=[]
for p in O.rglob('*'):
    if p.is_file() and p.name!='OUTPUT_SHA256.csv' and p.suffix!='.log' and '__pycache__' not in str(p):
        manifest.append(dict(path=str(p.relative_to(O)),sha256=sha(p),bytes=p.stat().st_size))
csv('OUTPUT_SHA256.csv',manifest)
print(json.dumps(dict(independent_checks=len(checks),failures=0,DC_rows=rows,origins=origins,max_serialized_component_residual_Wh=maxclosure,minimum_stock_Wh=minstock,verdict='CONDITIONAL GO'),indent=2))
