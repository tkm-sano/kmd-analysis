"""Assemble the evidence ledger and plans; no T08/T09/DC rerun and no thesis writes."""
from pathlib import Path
import csv,json,hashlib,datetime,sys
sys.dont_write_bytecode=True
import pandas as pd
import numpy as np
O=Path(__file__).resolve().parents[1]
R=O.parents[2]
OLD=R/'review_outputs/t08_t09_interaction_boundaries_20261105/run01'
DATE='2026-11-05'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvout(name,rows):
    df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    df.to_csv(O/name,index=False,float_format='%.10g');return df
def table(df,cols=None):
    if cols:df=df[cols]
    lines=['| '+' | '.join(df.columns)+' |','| '+' | '.join(['---']*len(df.columns))+' |']
    for row in df.itertuples(index=False,name=None):
        lines.append('| '+' | '.join('未取得' if pd.isna(v) else f'{v:.6f}' if isinstance(v,float) else str(v).replace('|','/').replace('\n',' ') for v in row)+' |')
    return '\n'.join(lines)

sources={}
def src(sid,title,doi,url,local,chemistry,cell,rate,scope,related='別材料',status='全文確認'):
    sources[sid]=dict(source_id=sid,title=title,doi=doi,url=url,local_evidence=local,chemistry=chemistry,cell_format=cell,
                      rate=rate,scope=scope,material_relation=related,inspection_status=status,access_date=DATE)
src('C_MAIN','Chen et al. Highly reversible oxygen redox in layered compounds enabled by surface polyanions','10.1038/s41467-020-17126-3','https://henkelmanlab.org/pubs/chen20_3411.pdf','sources/CHEN_AUTHOR.pdf; sources/CHEN_AUTHOR.txt','Li1.2Ni0.2Mn0.6O2 LP / sulfur-deposited S-200','CR2025 Li-metal half cell','0.5C Fig5b/c; 1C Fig5e-h; 1C=200mA/g','対象半電池の報告値。黒鉛全電池の実測ではない','対象材料・異なる対極')
src('C_SI','Chen2020 Supplementary Information','10.1038/s41467-020-17126-3','https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-020-17126-3/MediaObjects/41467_2020_17126_MOESM1_ESM.pdf','sources/CHEN_SI_CONFIRMED.pdf; sources/CHEN_SI_CONFIRMED.txt','LP / S-200 and Li2MnO3 calculation','Li-metal half cell / structural characterization','FigS13 0.5C; other figures condition-specific','19ページ、Supplementary Figs1-17。保持率の分母定義を確認できない','対象材料・異なる対極')
src('C_HTML','Chen2020 publisher full text and data availability','10.1038/s41467-020-17126-3','https://www.nature.com/articles/s41467-020-17126-3','sources/CHEN_PUBLISHER.html; sources/CHEN_PUBLISHER.readable.txt','LP/S-200','Li-metal half cell','論文条件別','raw dataは合理的要求により著者から取得する旨。公開Source Data添付を確認できない','対象材料・異なる対極')
src('C_LAB','Henkelman laboratory publication index','','https://henkelmanlab.org/pubs/','sources/CHEN_LAB_PUBS.html','LP/S-200','not applicable','not applicable','著者版本文リンクを確認。独立raw cycleファイルは調査範囲で未確認','対象材料','著者公開一覧を確認')
src('FE19','Wu et al. Elucidating the Effect of Iron Doping on the Electrochemical Performance of Cobalt-Free Lithium-Rich Layered Cathode Materials','10.1002/aenm.201902445','https://publikationen.bibliothek.kit.edu/1000098904/50680585','sources/FE_DOPED_FULL.pdf; sources/FE_DOPED_FULL.txt','Li1.2Mn0.585Ni0.185Fe0.03O2 / graphite SLP30','CR2032 full cell; Swagelok half-cell comparisons','1C=250mA/g; full cell initial 0.1C example / subsequent1C','近縁のFe置換材料。LP/Sの直接実測ではない','近縁材料')
src('TU20','Tu et al. Phase Transformation of Lithium-rich Oxide Cathode in Full Cell and its Suppression by Solid Electrolyte Interphase on Graphite Anode','10.1002/eem2.12034','https://onlinelibrary.wiley.com/doi/full/10.1002/eem2.12034','evidence/web2.json; evidence/web5.json','Li1.2Mn0.55Ni0.15Co0.1O2 / graphite; STD vs2wt%PES','CR2025 graphite full cell','initial3cycles0.05C; subsequent0.5C; 1C=200mA/g','出版社本文をweb経由で確認。直接HTML/PDF/SI保存は403','近縁材料','web本文Results/Methods確認; SI取得失敗')
src('BO24','Park et al. Understanding Boron Chemistry as the Surface Modification and Electrolyte Additive for Co-Free Lithium-Rich Layered Oxide','10.1002/aenm.202401968','https://advanced.onlinelibrary.wiley.com/doi/10.1002/aenm.202401968','evidence/web9.json; evidence/web10.json','Li1.222Ni0.349Mn0.651O2 as reported; LBO coating / LiBOB electrolyte','CR2032 and single-layer graphite pouch full cells','formationC/20; C/10 and C/3 cycling; nominal1C=270mAh/g as printed','出版社Experimental節まで確認。大学PDFリンクは404。硫黄処理ではない','近縁材料','web全文/Methods確認; raw data要請方式')
src('LMR26','Enhancing the longevity of lithium-manganese-rich layered oxides by promoting oxygen redox reversibility','10.1038/s41467-026-76366-x','https://www.nature.com/articles/s41467-026-76366-x','sources/LMR2026_FULL.html; sources/LMR2026_FULL.readable.txt; sources/LMR2026_SI.pdf; sources/LMR2026_DATA.xlsx','Li1.14Ni0.312Mn0.544Co0.004O2 / graphite','pouch; Results1Ah / Methods1.5Ah; large nominal40.9Ah','0.1C formation/N/P definition; 0.33C cycling','Co-lean近縁材料。配合・液量等は製造者非公開。本文とMethodsで一部条件の表記差がある','近縁材料')
src('RATE26','High-rate single-crystalline Li-rich layered oxide with diversified surface-phase cation ordering for Li-ion batteries','10.1038/s41467-026-75101-w','https://www.nature.com/articles/s41467-026-75101-w','sources/RATE2026_FULL.html; sources/RATE2026_FULL.readable.txt; sources/RATE2026_SI.pdf; sources/RATE2026_DATA.xlsx','Co-containing LMR from Mn0.6Ni0.2Co0.2 precursor; H-SCLMR via(NH4)2SO4-assisted leaching','graphite full-cell formation/cycling; Li-metal half-cell and pouch tests separately','1C=250mA/g; full-cell formation0.1C×2; normal0.2Ccharge/0.5Cdischarge','SCLMRはsingle-crystalの名称でChenのS-200ではない。硫酸アンモニウム処理は硫黄蒸着と別処理である','近縁材料')
src('B5','Argonne ANL/CSE-22/1 A Manual for BatPaC v5.0','','https://publications.anl.gov/anlpubs/2022/07/176234.pdf','sources/BATPAC_NHTSA.pdf; sources/BATPAC_NHTSA.txt; evidence/BATPAC_CHEM_PAGE46.png','generic modeled designs; Fig3.14 NMC811/graphite','stiff pouch / module / pack / battery system','design model; not a rate experiment','一次設計資料。ANL直接HTTP403、NHTSA政府公開ミラーから146頁PDFを保存','別化学系・設計モデル')
sources['B5']['download_url']='https://static.nhtsa.gov/nhtsa/downloads/CAFE/2023-NPRM-LD-2b3-2027-2035/Argonne-Databases/Documentation/BatPaC%20v5%20Manual-July%202022.pdf'
sources['LMR26']['local_evidence']+='; sources/LMR2026_PDF.pdf'
sources['RATE26']['local_evidence']+='; sources/RATE2026_PDF.pdf'
csvout('evidence/SOURCE_CATALOG.csv',list(sources.values()))

inv=[]
def add(id,sid,name,value,unit,loc,decision,reason,forbidden,conditions='',when='',uncertainty='',kind='REPORTED_NUMBER',newness='NEW_EXTRACTION',scope=''):
    s=sources[sid]
    inv.append(dict(data_id=id,source_id=sid,data_name=name,value=value,unit=unit,source=s['title'],doi=s['doi'],url=s['url'],page_figure_table=loc,
                    experiment_conditions=conditions or s['scope'],chemistry=s['chemistry'],material_relation=s['material_relation'],cell_format=s['cell_format'],
                    measurement_rate=s['rate'],measurement_time=when or '資料の該当図・節に依存',model_applicability=scope or reason,
                    uncertainty=uncertainty or '対象LP/S黒鉛全電池の適格性を保証しない',adoption=decision,adoption_reason=reason,prohibited_use=forbidden,
                    evidence_kind=kind,newness=newness,local_evidence=s['local_evidence']))
HALF='黒鉛全電池の容量・電圧・利用率・完成パック性能への直接代入'
NEAR='LP/S対象材料の実測値への読み替え、異なるレート/サイクル/配合の混合'
MODEL='LP/S実測BOMへの無条件代入、未確定部材を0として完成質量を確定する用途'
add('C01','C_MAIN','LP初回充電容量',238,'mAh/g active','PDFp6 Experimental verification','DIRECT','対象LP半電池で本文に報告されている',HALF,when='first cycle at0.5C',newness='RECONFIRMED_EXISTING')
add('C02','C_MAIN','LP初回クーロン効率',65.2,'%','PDFp6 and Fig5b PDFp8','DIRECT','対象半電池の初回効率である',HALF+'; u=.652とする用途',when='first cycle at0.5C',newness='RECONFIRMED_EXISTING')
add('C03','C_MAIN','LP初回放電容量の算術値',238*.652,'mAh/g active','PDFp6 inputs; 238×.652','SENSITIVITY_ONLY','丸められた初回充電量とFCEからの算術値である。直接報告の放電数値とは区別する',HALF+'; 初回放電の無丸め実測値という表示',when='first cycle at0.5C',uncertainty='238と65.2%の報告丸めを含む',kind='DERIVED_FROM_ROUNDED_REPORT',newness='RECONFIRMED_EXISTING')
add('C04','C_MAIN','S-200初回クーロン効率',82.0,'%','Fig5b PDFp8 blue label; evidence/CHEN_FIG5.png','DIRECT','図中に数値として明記された対象半電池FCEである',HALF+'; u=.82とする用途',when='first cycle at0.5C',kind='PRINTED_FIGURE_LABEL_NOT_DIGITIZED')
for id,name,val in [('C05','S-50初回FCE',79.5),('C06','S-500初回FCE',85.2)]:
    add(id,'C_MAIN',name,val,'%','Fig5b PDFp8','DIRECT','図中印字値である。S-200とは別処理量である',HALF+'; S-200値として使用',when='first cycle at0.5C',kind='PRINTED_FIGURE_LABEL_NOT_DIGITIZED')
for id,name,val,unit in [('C07','LP100cycle放電容量',121,'mAh/g active'),('C08','S-200100cycle放電容量',194,'mAh/g active'),('C09','LP容量保持率',70.4,'%'),('C10','S-200容量保持率',99.0,'%'),('C11','LP比エネルギー保持率',59.5,'%'),('C12','S-200比エネルギー保持率',96.0,'%')]:
    add(id,'C_MAIN',name,val,unit,'PDFp7 Experimental verification; Fig5g/h PDFp8','DIRECT','同論文の1C半電池100cycle指標である',HALF+'; 保持率分母を初回と断定',when='after100cycles1C',newness='RECONFIRMED_OR_NEW_LEDGER_EXTRACTION')
add('C13','C_MAIN','1C電流換算',200,'mA/g active','PDFp7','DIRECT','レートを他研究と対応させるための定義である','他論文の1C=250/270と同電流と扱う用途',when='Fig5g/h test')
add('C14','C_MAIN','活物質担持量','1.0–2.0','mg/cm2 face','PDFp11 Electrochemical characterization','DIRECT','対象半電池の記載範囲である','LP/S各試料の同一担持保証;10/20mg/cm2での性能保証',newness='RECONFIRMED_EXISTING')
add('C15','C_MAIN','乾燥配合active:SuperP:PVDF','75:15:10','wt%','PDFp11 Electrochemical characterization','DIRECT','対象半電池電極配合である','実用大型セル配合として製造性を保証',newness='RECONFIRMED_EXISTING')
add('C16','C_MAIN','測定電圧範囲','2.0–4.8','V vsLi/Li+','PDFp11','DIRECT','Li金属対極基準の範囲である','平均全電池電圧3.4V等を中点から作る用途',newness='RECONFIRMED_EXISTING')
add('C17','C_MAIN','電解液配合','1M LiPF6; EC/DMC1:1 v/v','composition','PDFp11','DIRECT','対象CAPCHEM製品の報告組成である','液密度や実投入量を組成のみから確定',newness='RECONFIRMED_EXISTING')
add('C18','C_MAIN','LP原料量',40,'mg','PDFp10-11 Deposition of sulfur','DIRECT','蒸着処理時のLP原料量である','セル内残留硫黄質量の推定')
add('C19','C_MAIN','S-200の硫黄供給量',200,'mg sulfur source','PDFp11 Deposition of sulfur','DIRECT','S-200は硫黄雰囲気の供給量200mgを指す','200℃の処理名称という解釈;200mgを残留被覆質量へ加える用途')
add('C20','C_MAIN','硫黄処理と余剰硫黄除去','250℃20min + vacuum250℃20min','protocol','PDFp11 Deposition of sulfur','DIRECT','処理条件を同一材料判定に用いる','供給量/残留量を同一視')
add('C21','C_SI','サイクル構造評価のレート',0.5,'C','Supplementary Fig13 PDFp14','DIRECT','SI内の100cycle XRDは0.5C条件である','Fig5g1C保持率系列と同一履歴として統合')
for id,name,loc in [('C22','保持率分母サイクルの明示','本文全12頁;SI全19頁;Fig5g'),('C23','Chenのactivation/formation手順','Methods;SI全19頁'),('C24','S-200初回放電容量の確定数値','Fig5b;本文Experimental verification'),('C25','LP/Sの絶対平均放電電圧','Fig5e/f normalized curves'),('C26','LP/S混合密度・空隙率','Methods;SI'),('C27','対象実電解液投入量','Methods;SI'),('C28','全100cycleの公開原系列','Data availability; publisher/PMC/lab/repository search')]:
    add(id,'C_MAIN' if id!='C28' else 'C_HTML',name,None,'UNRESOLVED',loc,'UNRESOLVED','該当条件に一意に対応する数値・定義を取得できなかった','推測値による欠測補完',uncertainty='未取得。非存在を証明したものではない',kind='MISSING_DATA')
for id,name,q in [('C29','LP逆算参照容量',121/.704),('C30','S-200逆算参照容量',194/.990)]:
    add(id,'C_MAIN',name,q,'mAh/g=Ah/kg','PDFp7 report arithmetic','SENSITIVITY_ONLY','保持率からの逆算参照としてのみ使用できる','初回放電容量の実測値、formation後黒鉛全電池容量',kind='BACK_CALCULATED_REFERENCE',newness='IMMUTABLE_HISTORICAL_REFERENCE')

for id,name,v,u,loc in [
 ('F01','Fe置換正極/黒鉛の初回放電容量',213,'mAh/g positive active','PDFp7 Fig10 discussion'),
 ('F02','同材料半電池の初回容量',232,'mAh/g positive active','PDFp7 discussion'),
 ('F03','全電池200cycle容量保持率',80.4,'%','PDFp7 Fig10 discussion'),
 ('F04','最大比エネルギー',361,'Wh/kg both active materials','PDFp7 text;Fig10 caption PDFp8'),
 ('F05','200cycle付近比エネルギー',200,'Wh/kg both active materials','PDFp7 text;Fig10 caption PDFp8'),
 ('F06','負極/正極の質量比',1.05,'mass ratio','PDFp8 Experimental'),
 ('F07','1C電流定義',250,'mA/g positive active','PDFp8 Experimental')]:
    add(id,'FE19',name,v,u,loc,'SENSITIVITY_ONLY','近縁Fe置換材料の条件付き参照である',NEAR+';361Wh/kgを完成セル/パック値として使用',when='first or200cycle as named',uncertainty='半電池と全電池の電圧窓が異なる;質量比と容量N/Pは別')
add('F08','FE19','213/232の異条件容量比',213/232,'1','F01/F02 arithmetic','NOT_APPLICABLE','異なる窓・対極の容量比でありT08の純粋な利用率とは定義が異なる','u=.9181をLP/Sへ採用',kind='DERIVED_DIAGNOSTIC_NOT_UTILIZATION')
for id,name,v,u,loc in [('T01','STD/PES初回放電容量','200 / 240','mAh/g positive active','Results2.1 Fig1a'),('T02','STD/PES初回効率','63 / 73','%','Results2.1 Fig1a'),('T03','正極/負極担持量','3.9 / 2.2','mg/cm2 active','Methods4.1'),('T04','設計負極/正極容量比',1.3,'capacity ratio','Methods4.1'),('T05','正極/負極設計比容量','200 / 350','mAh/g','Methods4.1'),('T06','formation相当初期サイクル',3,'cycles at0.05C 2.0–4.6V','Methods4.2')]:
    add(id,'TU20',name,v,u,loc,'SENSITIVITY_ONLY','Co含有近縁正極の黒鉛全電池である',NEAR,when='initial3 or subsequent cycles as named')
for id,name,v,u,loc in [('BO01','正極担持量',14,'mg/cm2 active','Experimental Electrode Preparation'),('BO02','正極面積容量',3,'mAh/cm2','Experimental Electrode Preparation'),('BO03','coin設計N/P',1.1,'capacity ratio approx','Experimental Electrode Preparation'),('BO04','黒鉛活物質割合',94,'%','Experimental Electrode Preparation'),('BO05','coin電解液量',50,'uL/cell','Experimental Electrode Preparation'),('BO06','single-layer pouch電解液量',500,'uL/cell','Experimental Electrode Preparation'),('BO07','400cycle保持率',82,'% atC/3','Conclusion;Fig5c/d')]:
    add(id,'BO24',name,v,u,loc,'SENSITIVITY_ONLY','別組成・ホウ酸塩処理の近縁全電池の値である',NEAR,uncertainty='web本文/Methods確認。raw数値系列は要請方式。cell形式と数量を対応させる必要がある')

for id,name,val,unit,loc in [('L01','公表N/P',1.07,'capacity ratio','Results voltage-window section;Methods Electrochemical testing'),('L02','正極初期放電容量',207.7,'mAh/g positive active approx','Results FigS7 discussion'),('L03','公称大型セル容量',40.9,'Ah nominal','Methods Electrochemical testing'),('L04','大型セル寸法','290.5×159.0×11.5','mm','Methods Electrochemical testing'),('L05','電解液組成','1.2M LiPF6 EC/EMC/DEC20/70/10 +VC0.5wt%+PS0.5wt%','composition','Methods Electrochemical testing'),('L06','公表比エネルギー',663,'Wh/kg positive active','Abstract;Fig7d'),('L07','883cycleエネルギー保持率',92.2,'%','Abstract;Fig7d'),('L08','非公開製造情報','binder/additive amounts; electrolyte volume; stack pressure','UNRESOLVED','Methods first paragraph')]:
    add(id,'LMR26',name,val,unit,loc,'UNRESOLVED' if id=='L08' else 'SENSITIVITY_ONLY','公開範囲が限定されたCo-lean近縁全電池のデータである',NEAR+';663Wh/kgを完成セル・完成パック比エネルギーへ使用',uncertainty='Results N/P定義45℃/Methods35℃;Results1Ah/Methods1.5Ah。該当系列別に扱う')
add('L09','LMR26','formationと通常運転窓','2.00–4.55V35℃; then4.25–2.00V25℃','protocol large cell','Fig7;SI FigS31/S34 PDFp33/36','SENSITIVITY_ONLY','大型セルに対応する形成・通常サイクルの区別が明示される',NEAR,when='large-format case; not1Ah study')
for id,name,val,unit,loc in [('R01','黒鉛全電池用正極担持量',11,'mg/cm2 active','Methods Electrochemical measurements'),('R02','設計N/P',1.2,'capacity ratio approx','Methods Electrochemical measurements'),('R03','黒鉛乾燥配合','80:10:10','wt% graphite:SuperP:PVDF','Methods Electrochemical measurements'),('R04','厚電極活物質割合',90,'%','Fig4c;Methods thick electrode'),('R05','厚電極担持量',9,'mg/cm2 active','Fig4c;Methods'),('R06','厚電極初期容量',278,'mAh/g positive active','Results cycling;Fig4c'),('R07','厚電極100cycle保持率',90.5,'%','Results cycling;Fig4c'),('R08','coin液量',100,'uL/cell','Methods Electrochemical measurements'),('R09','Li-metal pouch液比',6,'uL/mg positive active','Methods Electrochemical measurements'),('R10','1Cの定義',250,'mA/g positive active','Fig2 caption;SI FigS17'),('R11','formation','0.1C×2 1.8–4.75V','protocol graphite full cell','Methods;SI FigS17 PDFp18'),('R12','通常全電池サイクル','0.2Ccharge/0.5Cdischarge 1.9–4.7V30℃','protocol','Methods;SI FigS17 PDFp18')]:
    add(id,'RATE26',name,val,unit,loc,'SENSITIVITY_ONLY','Co含有・硫酸アンモニウムleaching処理の近縁材料である',NEAR+';R09を黒鉛full-cellの液量へ転用',when='thick Li-metal half-cell if R04–R07; full-cell if R01/R02/R11/R12',uncertainty='pouch試験はLi-metal対極である。formationと通常サイクルを混合しない')

profiles=pd.read_csv(O/'evidence/PUBLIC_PROFILE_INTEGRALS.csv')
for i,r in enumerate(profiles.to_dict('records')):
    sid='LMR26' if r['source_id']=='LMR2026_DATA' else 'RATE26'
    for suffix,name,v,unit in [('Q','放電容量',r['discharge_capacity_mAh_g'],'mAh/g positive active'),('V','平均放電電圧',r['mean_discharge_voltage_V'],'V full cell'),('E','放電比エネルギー',r['discharge_specific_energy_Wh_kg_positive_active'],'Wh/kg positive active')]:
        add(f'P{i+1:02d}{suffix}',sid,r['label']+' '+name,v,unit,f"Source Data / {r['sheet']} / {r['column_Q']}{r['start_row']}:{r['column_V']}{r['end_row']}",'SENSITIVITY_ONLY','同じ放電枝の公開Q-Vを直接積分した近縁セルの派生値である',NEAR+';実測装置の未加工raw値という表示',when=r['label'],kind='DERIVED_FROM_PUBLIC_FIGURE_SOURCE_DATA',uncertainty='原データの測定誤差・反復分布は未提供。積分誤差の小ささは実測精度を保証しない')
for i,r in enumerate(pd.read_csv(O/'evidence/PUBLIC_CYCLING_ENDPOINTS.csv').to_dict('records')):
    sid='LMR26' if r['source_id']=='LMR2026_DATA' else 'RATE26'
    add(f'X{i+1:02d}',sid,r['material']+' 公開系列保持率',r['retention_percent'],'%',f"Source Data / {r['sheet']} / {r['cells']}",'SENSITIVITY_ONLY','公開系列の最終/開始値の算術比である',NEAR,when=f"cycle{r['cycle_first']}→{r['cycle_last']}",kind='DERIVED_FROM_PUBLIC_SOURCE_SERIES',uncertainty=r['scope'])
for i,r in enumerate(pd.read_csv(O/'evidence/CHEN_FIG5G_DIGITIZED.csv').to_dict('records')):
    add(f'G{i+1:02d}','C_MAIN',f"Fig5g {r['material']} cycle{r['cycle']}図読取",r['capacity_mAh_g_approx'],'mAh/g active approx','Fig5g PDFp8; embedded source-17.png','SENSITIVITY_ONLY','図の中後半cycleの概数であり原系列ではない',HALF+';厳密な保持率分母/初回値の決定',when=f"1C cycle{r['cycle']}",kind='FIGURE_DIGITIZED',uncertainty='約5mAh/gの読取分解能。真値誤差上限・信頼区間ではない。cycle100は枠を避け99–100付近。S-20020cycleは重なりで未読取')

for id,name,val,unit,loc in [('B01','黒鉛参照比容量',360,'mAh/g','Fig3.14 PDFp46 printedp27'),('B02','formation後参照N/P',1.10,'capacity ratio','Fig3.14 PDFp46'),('B03','黒鉛active/carbon/binder','98:0:2','wt%','Fig3.14 PDFp46'),('B04','黒鉛活物質密度',2.24,'g/cm3','Fig3.14 PDFp46'),('B05','負極binder密度',1.10,'g/cm3','Fig3.14 PDFp46'),('B06','Cu箔厚さ',10,'um','Fig3.14 PDFp46'),('B07','黒鉛空隙率',25,'%','Fig3.14 PDFp46')]:
    add(id,'B5',name,val,unit,loc,'SENSITIVITY_ONLY','NMC811/graphiteのモデル既定値を視認確認した。360の出典対応は確定した',MODEL,kind='PUBLISHED_DESIGN_DEFAULT_PRINTED_FIGURE')
for id,name,val,unit,loc in [('B08','セル正極/負極端子厚さ','1.2 / 0.8','mm','Sec5.2.2.2 Eq5.17 PDFp72'),('B09','セル間Cu接続厚さ',1,'mm','Eq5.20/5.21 PDFp73'),('B10','正負極寸法余剰','2 width /2 length','mm total;1mm per side','Sec5.2.5 PDFp79'),('B11','separator寸法余剰','2 width /4 length','mm total','Sec5.2.5 PDFp79'),('B12','未塗工集電箔長さ',1.2,'times cell thickness','Sec5.2.5 PDFp79'),('B13','端子外部/封止部長さ','8 /5','mm','Sec5.2.5 PDFp80'),('B14','外部端子幅','40 ifWpos<85mm; else50','mm','Sec5.2.5 PDFp80'),('B15','セル積層充填係数',0.97,'1','Eq5.33 PDFp77-78'),('B16','EV熱伝導Al厚さ',0.4,'mm','Sec5.3.1 PDFp83'),('B17','モジュールsteel壁厚',0.3,'mm','Sec5.3.1 PDFp83'),('B18','接続polymerパネル厚さ',2,'mm','Sec5.3.2 PDFp83'),('B19','module管理機器質量',46,'g/module','Sec5.3.2 PDFp83'),('B20','module gas release質量',5,'g/module','Sec5.3.2 PDFp83'),('B21','拘束plate厚さ',2,'mm','Sec5.4 PDFp84'),('B22','coolantchannel/壁厚','5 /0.3','mm','Sec5.4 PDFp85'),('B23','pack内Al/外steel/断熱層厚','1 /1 /10','mm','Sec5.5.3 PDFp88'),('B24','pack外Al厚さ','1 /1.5 /2 byenergy','mm; <10/10–20/other kWh as printed','Sec5.5.3 PDFp88'),('B25','BMU PCB基準質量',40,'g','Sec7.2 PDFp103'),('B26','ASIC当たり加算質量',20,'g/ASIC','Sec7.2 PDFp103'),('B27','BMU enclosure加算',10,'%','Sec7.2 PDFp103'),('B28','BMS外装係数',1.3,'1','Sec7.6 PDFp106'),('B29','maincontactor質量',750,'g/unit','Table7.2 PDFp104'),('B30','prechargecontactor質量',90,'g/unit','Table7.2 PDFp104'),('B31','service disconnect質量',150,'g/unit','Table7.2 PDFp104'),('B32','current sensor質量',55,'g/unit','Table7.2 PDFp104'),('B33','pack外冷却系の追加質量','2/3/5/7','kg for500/1000/3000/6000W','Table8.2 PDFp112'),('B34','冷却液密度',1.07,'g/cm3','Eq8.12 PDFp113')]:
    add(id,'B5',name,val,unit,loc,'SENSITIVITY_ONLY','選択したstiff-pouch架構の条件付き設計参照として使用できる',MODEL,kind='PUBLISHED_DESIGN_DEFAULT',uncertainty='必要な幾何・電流・module数・熱負荷等は対象で未確定。20kWhちょうどの段階条件は実装確認が必要')
for id,name,formula,loc,block in [
 ('B35','固相混合密度','rho_solid=1/sum(w_i/rho_i)','Sec3.4.1/4.1; mass-volume accounting','対象各成分真密度・配合を要する。空隙率を含むbulk密度と区別する'),
 ('B36','端子/余白箔積算','sum(area*thickness*density*count)','Sec5.2.5; Eq5.33–5.36','同一面積規約と最外層片面箔補正を要する'),
 ('B37','BMS質量積算','BMU+BDU+power electronics, enclosure factors; module46g separately','Secs7.2–7.6','module46g内のelectronicsやlumpedwiringを重複計上しない'),
 ('B38','熱管理の質量境界','pack coolant structure vs external pumps/chiller system','Sec8.6 Table8.4 PDFp117–118','pack-onlyとbattery-systemを混合しない。既存交換境界を先に揃える')]:
    add(id,'B5',name,formula,'accounting rule',loc,'TRANSFERABLE','幾何・材質・個数と同一会計境界を指定すれば積算方法を移用できる',MODEL,kind='MODEL_STRUCTURE_NOT_MEASURED_MASS',uncertainty=block)
add('B39','B5','箔notchingのscrap',8,'% approx','Sec9.3.1.4 PDFp128','NOT_APPLICABLE','製造時スクラップであり残存余白質量ではない','完成セルの箔質量を1.08倍する用途',kind='MANUFACTURING_YIELD_NOT_PRODUCT_MASS')
add('B40','B5','Eq5.17端子有効長係数',1.2,'1 resistance correction','Eq5.17 PDFp72','NOT_APPLICABLE','接触抵抗に対する電気的有効長補正である','物理端子の体積/質量を一律1.2倍する用途',kind='ELECTRICAL_EQUIVALENT_NOT_GEOMETRY')
add('B41','B5','cell container laminateの対象厚さ/材質',None,'UNRESOLVED','Sec2.2 and5.2.5','UNRESOLVED','積算方法は取得したが対象LP/S pouch外装の層構成・厚さ・実寸はない','generic層構成を対象実測として採用',kind='MISSING_TARGET_BOM')
inventory=csvout('ADDITIONAL_DATA_INVENTORY.csv',inv)
matrix=[]
for sid,s in sources.items():
    ids=inventory[inventory.source_id==sid].data_id.tolist()
    matrix.append(dict(**s,data_ids='|'.join(ids),direct_target_graphite_fullcell='NO',
                        numerical_use='scope-limited as individually classified',limitations=s['scope']))
csvout('SOURCE_EVIDENCE_MATRIX.csv',matrix)

holds=[]
def hold(id,name,status,evidence,resolved,remaining,gate,scope='PRIMARY_TARGET_HOLD'):
    holds.append(dict(hold_id=id,hold_name=name,status=status,scope=scope,evidence_data_ids=evidence,resolved_scope=resolved,
                      remaining_hold=remaining,target_practical_adoption='HOLD' if scope=='PRIMARY_TARGET_HOLD' else 'not a target performance adoption',release_criterion=gate))
hold('H01','Chen逆算容量の初回容量への適用','UNRESOLVED','C01–C04;C22–C24;C29–C30','初回FCEの図中数値と0.5C/1Cの区別を確認した','保持率分母cycle・activation/formationと初回1Cの対応は未確定である','著者原系列と試験手順から保持率分母・各レートのcycle番号を一意に対応させる')
hold('H02','LP/S–黒鉛全電池の利用可能容量','UNRESOLVED','F01–F08;T01–T06;P01–P09','近縁全電池の実例と公開Q-Vを取得した','同じLP/Sの黒鉛全電池対照測定がない','同一温度/窓/レート/担持/N/P/formationでLP/S対を測定する')
hold('H03','平均全電池電圧','PARTIALLY_RESOLVED','P01V–P09V','近縁全電池の平均電圧を公開Q-Vから算定できた','LP/S別の平均全電池電圧は未確定である','LP/S各放電枝で積分E/Qし、容量と同一条件を確認する')
hold('H04','容量利用率','UNRESOLVED','C02;C04;F08;R11–R12','FCEとformation後利用率が別指標であることを整理した','T08参照qに対応する同条件全電池q/uがない','qの分母・サイクル・可逆容量・Li損失を揃え、損失の二重適用を排除する')
hold('H05','正極・負極の混合密度','UNRESOLVED','C26;B04–B05;B35','別設計の黒鉛/結着材密度と混合則を確認した','LP/S実配合の固相密度、calendering後bulk密度と空隙率はない','対象成分真密度と乾燥配合、または質量・面積・厚さ・空隙の整合測定を取得する')
hold('H06','高担持条件での容量維持','PARTIALLY_RESOLVED','BO01–BO03;R01–R07;X01–X03','近縁黒鉛全電池11mg/cm2と別近縁14mg/cm2、厚半電池9mg/cm2を確認した','LP/Sの10/20mg/cm2探索点での輸送・出力・容量適格性は未確定である','同じLP/Sで担持/厚さ/空隙/電流密度/寿命の対応を測定する')
hold('H07','実際の電解液量','UNRESOLVED','C27;BO05–BO06;R08–R09;L08','近縁セルの50/100/500uL、Li-metal pouch6uL/mgを取得した','対象LP/Sの実投入量・飽和度・余剰液はない','対象電極/膜空隙と実注液・残留液を対応させる')
hold('H08','外装・タブ・構造部材','PARTIALLY_RESOLVED','B08–B41','寸法・個数依存の公開積算則とBMS/冷却のモデル値を取得した','対象LP/Sセル形式・材質・寸法・modules・電流・熱負荷がない','一致するarchitectureを宣言した条件付きBOMまたは対象実測BOMを作る')
hold('H09','T09完成パック質量','UNRESOLVED','H05–H08;B38;B41','未知部材を制約するための変数と式を列挙した','K+UのU絶対量と差が未確定である','会計範囲・全BOM・単位・部材和を閉じる。未知が残れば絶対値をNULL維持する')
hold('H10','実車の走行時DC電力量','RESEARCH_LIMITATION','既存402040行;H02–H09','凍結DCの条件付き観測軌跡応答は既存検証済みである','回生/補機/勾配/実積載等を含む実車実証は本研究の検証範囲外である','Level3で実車端子DC・質量・速度・環境・SOCを同期測定する。現核の意味を拡張しない')
hold('H11','出力・寿命・安全性','PARTIALLY_RESOLVED','C07–C12;F03;BO07;R06–R07;L07–L09','半電池/近縁全電池の寿命、formation、ガス問題の資料を取得した','LP/S黒鉛完成セルの出力・長期寿命・熱/濫用安全は未実証である','対象セルのpulse/DCIR/温度・寿命・ガス・安全試験を実施する。近縁値を合格証としない')
hold('S01','Chen補足資料未取得','RESOLVED','C_SI','19頁PDF全体を取得・読取り・保存した','分母cycle定義は別の未解決事項である','source hashとpublisherリンクを保存済み','SOURCE_ACCESS_SUBHOLD')
hold('S02','S-200初回FCE未確認','RESOLVED','C04','Fig5b印字82.0%・0.5C・Li対極を確認した','初回放電容量の確定数値・黒鉛全電池容量は別問題である','PDFp8と図を保存済み','SOURCE_ACCESS_SUBHOLD')
hold('S03','黒鉛360の参照出典不明','RESOLVED','B01–B03','Fig3.14 PDFp46 NMC811/graphiteの360・N/P1.10・98%activeを視認した','LP/S対象負極としての実用採用は別問題である','実測値ではなく公開設計既定値と分類済み','SOURCE_TRACEABILITY_SUBHOLD')
holdframe=csvout('HOLD_REASSESSMENT.csv',holds)

code8='review_outputs/t08_t09_interaction_boundaries_20261105/run01/scripts/analyze.py::mass (read-only reference)'
code9='/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/t09_open_data_model_20261029/run01/model.py::geometry/foil_mass/liquid_mass/account_cell'
codeDC='src/kmd_quantitative/energy/controlled_dc.py::evaluate (frozen alias)'
plan=[]
def calc(id,task,need,got,lack,code,conditions,compare,metrics,done,can,dependency):
    plan.append(dict(calculation_id=id,task=task,required_inputs=need,acquired_inputs=got,missing_inputs=lack,code_to_use=code,
                     calculation_conditions=conditions,comparison=compare,output_metrics=metrics,completion_criterion=done,
                     calculability=can,dependency=dependency,execution_in_current_task='NO_LARGE_RECALCULATION',
                     planned_adapter='next run02/scripts/recalculate_pathway2.py (NOT YET CREATED)'))
calc('R01','正極容量の再設定','LP/S可逆容量、レート、温度、cycle/formation、質量基準','C01–C15;近縁source-data','LP/Sの同条件黒鉛全電池q','code8='+code8,'既存q逆算値は固定保存。新規qは別scenario','同条件LP対S;近縁事例は別モデル系','q_eff,positiveactive/coating kg','q×uの意味を一本化し二重損失補正を排除','NEAR_MATERIAL_CASE_POSSIBLE;TARGET_MEASUREMENT_NEEDED','Step2/3')
calc('R02','材料別平均電圧','各対象の同じ放電枝Q,V、cycle、rate、温度','P01V–P09Vの近縁派生値','LP/S黒鉛全電池Q-V',code8+';scripts/extract_public_data.py','meanV=integral(VdQ)/Qspan。cutoff中点や半電池Vを代用しない','材料別q,Vを同一履歴に対応','meanV,Q,E and rounding/error notes','枝・単位・積分・source cell-rangeを照合','NEAR_MATERIAL_DERIVATION_DONE;TARGET_MEASUREMENT_NEEDED','Step2/3')
calc('R03','利用率の再設定','q_refとq_effの同条件定義、Li損失とactivation','FCEと利用率の区別・formation資料','対象対応系列',code8,'q_effを直接使う場合u=1は会計上の定義で、実験利用率100%と主張しない','同一基準q_refへ対応したLP/S','u,qu,loss ledger','0<u<=1の定義域確認。q基準が異なる比をuにしない','TARGET_MEASUREMENT_NEEDED','Step2/3')
calc('R04','負極容量・N/P更新','可逆qn・f_n・N/P定義、formation後Li在庫','B01–B07;T04/T05;R02/R03','対象LP/S負極とformation',code8+';'+code9+'::negative_mass','mass ratio1.05をcapacityN/P1.05としない','共通負極変更とS-only変更を分離','active/coating negative kg,Ah balance','N/Pの容量基準・不可逆損失一回適用を監査','REFERENCE_SENSITIVITY_POSSIBLE;TARGET_MEASUREMENT_NEEDED','Step3')
calc('R05','電極幾何更新','担持、乾燥配合、混合固相密度、空隙、実厚、面積','B35;C14/C15;R01–R07','LP/S高担持実測、密度/空隙組',code9,'fixed_loading/fixed_area_LPの意味を維持。新geometryは別scenario','LP固定S-onlyと共通再設計を区別','A,t,pore,foil,separator,liquid kg','厚さ/体積/面積一致・全面対向・両面箔共有・NULL保持','CONDITIONAL_GEOMETRY_POSSIBLE;TARGET_QUALIFICATION_NEEDED','Step3/4')
calc('R06','T09未知部材制約','pouch層、tabs、余白、module topology、冷却/電気要件','B08–B41公開寸法/個数則','target寸法/材質/熱負荷;v5workbook実装',code9+'; next run02 BOM adapter (planned)','packとsystem交換範囲を先に一致させる。未取得材はNULL','同architecture LP/S、未知U_LP/U_S/δUを別管理','known subtotal,U constraints,δU boundary','全11カテゴリとpackBOMの一意会計、wiring等重複なし','CONDITIONAL_BOM_DESIGN_POSSIBLE_AFTER_ARCHITECTURE_SELECTION','Step4')
calc('R07','パック質量差更新','R01–R06の共同適格入力またはU差制約','既存527質量条件と解析境界;新規参照資料','対象full BOM/δU',code8+';'+code9,'まず採用可能入力だけscenario fingerprint照合','旧参考例を不変にして新scenarioとの差を比較','LP/S絶対kgと差、T09はK差−δU','未知Uあれば絶対値HOLD。既存入力重複は再計算しない','REFERENCE_CASE_REUSABLE;TARGET_COMPLETE_MASS_HOLD','Step5')
calc('R08','車両質量差更新','交換範囲内の適格Mpack、運転者/積載固定','既存1155−20000/180+Mnew式','対象確定Mpackおよびpack/system差の帰属',code8+'::NONPACK','元の置換式を変えず、元vehicle側に含まれるcoolerを二重加算しない','同じ保存車両構成','running mass kg,delta kg','運転者55kg一回、回転等価61kg固定、交換境界一致','CONDITIONAL_MAPPING_POSSIBLE_AFTER_R07','Step5')
calc('R09','Controlled-DC再評価','適格走行質量、保存460軌跡、凍結核','既存402040行・411質量・両Crr','新規で重複しない質量のみ',codeDC,'既存軌跡/Crr核/モデル境界固定。新質量だけ評価','同軌跡のLP/S対応、Crr上下を別集計','absoluteWh,deltaWh,%,Wh/km,Wh/kg,W1–W4+branch','hash/基準再現・直接核照合・枝閉合・非独立性維持','NO_RERUN_NOW;ONLY_NEW_QUALIFIED_MASSES_LATER','Step6')
calc('R10','成立・消失境界更新','適格q/u/V/negative/BOM差式','既存2575境界点と解析式','新規入力共同成立域',code8+'::boundaries;next run02 adapter (planned)','解析根を先に求め、未計算の代表点だけ数値確認','旧境界面不変、新境界は別表','zero surface,sign tests,domain,δU allowance','解析/数値残差と境界内外符号、数学域と物理域の区別','SYMBOLIC_UPDATE_POSSIBLE;TARGET_FEASIBILITY_HOLD','Step5/6')
plans=csvout('RECALCULATION_PLAN.csv',plan)

steps=[
 ('0','既存証拠の固定','旧527/2575/402040と監査・hashを固定し、参照結果としてロックする','既存報告・CSV・code','既存T08/T09/DC','保全manifest/既存結果台帳','hash一致・既存数値変更なし','以後の入力は新IDとする','既存hash差が出たら原因確認まで再計算しない','1–2人時','提出前必須'),
 ('1','今回の追加証拠の採用確定','資料・原図・Source Dataの条件と個別採用を査読し、source/target適用範囲を固定する','本run inventory/source matrix/HOLD','文献採用判定','採用台帳/未取得項目表','DIRECTが半電池限定であること、近縁値の転用制限を確認','限定Level2の主張セットを確定する','根拠不十分な値はUNRESOLVED/SENSITIVITY_ONLYへ戻す','2–4人時','提出前必須'),
 ('2','Chen cycle定義の追加照会','保持率分母cycle・activation・0.5C/1C原系列・S200初回Q-Vの入手を試みる','著者の原系列・試験手順・依頼項目','source review only','cycle mapping table/原系列または取得不能記録','分母とサイクル番号・温度・電流密度を一意に確認','得られればR01/R02。得られなければ既存参考例を維持する','期限を決め、未回答はH01維持。文献値を推測しない','依頼準備2–3人時＋確認2–4人時。待ち時間は著者応答次第','限定Level2では取得試行/未解決明記が必須。解消自体は不要'),
 ('3','同条件電極/黒鉛全電池入力の共同適格化','半電池と全電池のq/V/formation/N/P/担持/密度/空隙を条件束として評価する','LP/S対象全電池系列、または完全に分離した近縁ケース','T08入力会計/half-full transfer','共同入力条件表/採用可否','レート・電圧窓・時点・質量分母が一致し、損失二重適用がない','対象データが揃えばtarget scenario。近縁だけなら独立したreference scenario','target入力はHOLD維持。近縁ケースをLP/Sとして改名しない','公開データ整備4–8人時。対象実測は4–8人日準備＋試験日程','限定Level2では入力分類が必須。target実証はLevel3寄り'),
 ('4','BOM会計境界と条件付き架構の確定','100sのmodule構成・cell寸法・pouch層・tabs・余白・BMS/冷却を選定し、BatPaC実装を照合する','B5 manual、v5workbook、幾何、電流/熱負荷、交換境界','T09 geometry＋BOM adapter予定','architecture specification/BOM ledger/未知U制約','module46g・BMS・wiring・cooler等が二重計上されず、未知はNULLである','generic designの条件付き補完が成立した範囲だけR06/R07へ進む','選定不能な部材をゼロにせずU/δUとして残す','8–16人時＋workbook取得/操作待ち','完成pack主張をしないなら記号境界で提出可能'),
 ('5','最小限の新規質量・境界計算','採用入力を既存527条件と照合し、追加必要点と解析境界だけ計算する','Step3/4共同入力・既存INTERACTION/BOUNDARY','T08/T09 mass and analytic roots','new mass/zero surface/代表点符号監査','旧結果不変、単位/会計/解析根・数値一致','DCへ渡せる適格な新規走行質量を確定する','U残存ならT09絶対DCへ渡さない','3–6人時','新規効果量を論文主張へ追加する場合のみ必須'),
 ('6','必要なDC応答だけ更新','411既存質量・保存DCを照合し、新質量だけ460軌跡×両Crrで評価する','Step5出力と保存軌跡/hash','凍結Controlled-DC evaluate','新Wh表/成分閉合/旧結果との差','絶対値・差・正規化・枝補正を直接核へ照合、非独立性を維持','新規質量/DCの採用主張を更新できる','対象M未確定なら既存材料非依存質量応答で止める','3–6人時、計算時間は追加ユニーク質量数依存','新規効果量を論文主張へ追加する場合のみ必須'),
 ('7','提出前の主張・学術監査','Level1/限定Level2/Level3の主張を分け、全claimを出典と数値へ結ぶ','既存結果＋本run＋必要ならStep5/6','claim-evidence audit','最終claim matrix/提出用制約・限界一覧','逆算を初回、近縁を対象、設計値を実測、DFTを量子計算機実証としない','別タスクの論文統合へ移行できる','限定Level2で成立する貢献へ主張を縮約する','3–6人時','提出前必須'),
 ('8','実用セルの実証','LP/S黒鉛全電池対を設計・製造し、q/V/寿命/出力/ガス/安全・BOMを測定する','試料・試験設備・製造/安全手順','対象実セル・実パック','実験Q-V/BOM/寿命安全結果','再現試験と同条件対照、BOM閉合、規定試験の判定を満たす','Level3車両検証の候補セル/packが得られる','試験不成立・不足はHOLD。近縁文献で合格代用しない','設計準備2–4人週＋数週～数か月のcycling。設備次第','研究目的上は提出前必須でない'),
 ('9','実車端子DCの実証','確定packで同一運行条件の対照測定を行い質量→実車DCを検証する','適格pack、車両、同期DC/速度/SOC/環境/積載','実車計測。凍結DCは別の比較基準として保持','実車対応差・測定誤差・適用域','回生・補機・勾配を観測し、モデル範囲との差を説明する','Level3主張の完了を判定する','実施不能ならRESEARCH_LIMITATIONを維持する','計測準備1–2人週＋実走日程・解析1–2人週','提出前必須でない'),
]
roadrows=[]
for n,purpose,work,inputs,model,outputs,done,gate,onhold,labor,required in steps:
    if n=='5':required='限定Level2完了には少数の公開近縁ケース検算が必須。新規大規模探索は不要'
    roadrows.append(dict(step=n,purpose=purpose,activities=work,required_inputs=inputs,model=model,deliverables=outputs,completion_criterion=done,next_step_gate=gate,hold_action=onhold,estimated_effort=labor,submission_requirement=required))
csvout('evidence/EXECUTION_ROADMAP.csv',roadrows)

road='# 因果経路2の検証完了までの実行計画\n\n本計画は今回の調査に基づく実行順序である。推定作業量は担当者作業時間の計画値であり、確率区間や完了保証ではない。外部照会・設備予約・cyclingの待ち時間は別である。著者等への連絡は今回実行していない。\n\n'
for row in roadrows:
    road+=f"## Step {row['step']}：{row['purpose']}\n\n"
    for key,label in [('activities','実施内容'),('required_inputs','必要入力'),('model','使用モデル'),('deliverables','成果物'),('completion_criterion','完了判定'),('next_step_gate','移行条件'),('hold_action','HOLD時の対応'),('estimated_effort','推定作業量'),('submission_requirement','提出前の位置付け')]:road+=f"- {label}：{row[key]}。\n"
    road+='\n'
road+='''## 不要な再計算を避ける規則

既存527条件（437T08＋90T09）、2575境界点、402040行DCは固定参照である。入力fingerprintを照合し、同一入力は質量表を、同一走行質量はDCを再利用する。物性変化が同じ最終質量へ到達する限り、凍結DCは材料名に依存しない。再利用時には両Crr・軌跡hash・走行質量・energy boundary・核hashが同じことを確認する。

新しいV/u等で枝の区間外となる質量を扱う場合、既存1122.538728–1172.249406kgの検証区間外へ線形外挿せず、凍結evaluateで再評価する。連続境界は解析式を先に使い、境界内外の少数代表点だけ追加する。既存460軌跡、QAOA、SUMO、経路最適化は再実行不要である。T09のUが未確定なら絶対pack/絶対DCを作らず、K差−δUと材料非依存DC応答のまま保持する。

今回の範囲はStep0/1の成果とStep2以降の計画確定である。新しいBOMの設計選定、質量/DCの大規模再計算、論文修正は実施していない。
'''
(O/'EXECUTION_ROADMAP.md').write_text(road)

criteria='''# 検証完了基準

## Level 1：数理モデル内の検証

必要条件は、入力定義と単位・基準/比較の一致、既存値再現、正負極容量/質量の会計、T09NULL保持、解析境界と数値符号の一致、固定軌跡と凍結DCの再現・W1～W4/枝補正閉合、車両質量置換の一回適用、依存する軌跡への独立標本推定を行わないことである。

判定は既存成果の範囲で完了である。旧runの12374件数値監査と3298件別プロセス監査を証拠として継承し、今回それを新規実験の検証へ読み替えない。今回の作業では大規模再計算せず、入力/output hashと既存監査を確認した。新規BOMや検証区間外の質量へ拡張した場合はその追加部分を改めて検証する必要がある。

## Level 2：文献・公開データに基づく条件付き検証

完了条件は、一次本文/補足/Source Dataを実際に確認し、すべての採用値を数値・単位・図表・測定時点・電池形式・rate・化学系へ追跡でき、対象直接値と近縁/別化学系/設計参照を分け、HOLDと適用不可用途を明示し、資料上の不整合・未公開項目を推測しないことである。

今回完了したのは資料取得・採用監査と公開Q-Vの派生量確認までであり、Level2全体の完了とは判定しない。限定した主張に対するLevel2を完了させるには、次タスクで少なくとも一つの同条件の公開近縁対照ケースを、対象LP/Sから明確に分離して設定し、共同入力の整合性、質量核との接続、記号的未知BOM、相殺条件を少数代表点で独立検算し、Step7の主張監査を閉じる必要がある。近縁全電池の存在だけで対象全電池の入力を採用してはならない。LP/S黒鉛全電池と完成packの性能妥当性は、この限定Level2を満たしてもHOLDのままである。

公開設計でgeneric pouch BOMを閉じる場合、その条件付き設計はLevel2に含め得る。ただしarchitecture・電流・熱負荷・未知項目・pack/system境界がすべて指定されて初めて完成設計となる。今回は構造パラメータの取得と作業計画までであり、generic完成BOMの算定完了は主張しない。

## Level 3：実用全電池・実車の実証

必要条件は、同じLP/S材料の黒鉛全電池対の可逆Q-V、formation/Li在庫、N/P・担持・密度・空隙・実液量、セル/packの完全BOM、出力・温度・長期寿命・ガス・安全試験、および確定packを搭載した実車DCの対応計測である。必要な反復と測定不確かさは実験設計に基づき定める。今回取得した近縁寿命データ、DFT、凍結DC、設計仮定は対象実証の代用としない。

判定は未達である。実車DCは本修士研究の制御モデル範囲外の研究限界であり、Level3を提出前の必須条件とはしない。実用性能や量子計算機による材料改良の実証を論文で主張する場合は、その主張を削除するか、対応する実証を満たす必要がある。

## 提出前の研究上の必須条件

本研究目的からは、Level1と、上記限定主張に対するLevel2の完了を必須とする。これは研究上の主張に対応する判断であり、大学の提出規則や審査委員会による合否の確認ではない。

必須作業は、既存結果の保全、本runの採用/HOLD台帳の確認、半電池/全電池・初回/formation後・異なるC-rate・比エネルギー分母の区分、T09未知質量と適用域の明示、上記の小規模な文献対照ケース接続、claim-evidence最終監査である。新規入力によるDC効果量を追加して主張する場合だけ、必要な新規質量のDCを計算する。既存402040行の全面再計算は不要である。対象全電池測定がなければ、記号的成立条件・設計範囲の相殺境界・材料非依存の質量→DC応答を学術的貢献の中心とする。

提出前の計算を増やすこと自体は完了基準ではない。未確定入力を増やした大量計算は科学的HOLDを解除しない。今回の資料で対象q/V/u/BOMを一括置換することは認めない。
'''
(O/'COMPLETION_CRITERIA.md').write_text(criteria)

print('Built ledger',len(inv),'rows;',len(holds),'HOLD entries;',len(plan),'recalculation plans.')
