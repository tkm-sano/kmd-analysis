"""Build Japanese reports and structured scientific acceptance records from validated CSVs."""
from pathlib import Path
import sys,os,json,hashlib,platform,subprocess
sys.dont_write_bytecode=True
import pandas as pd,numpy as np,openpyxl
SD=Path(__file__).resolve().parents[1]
O=Path(os.environ.get('LEVEL2_OUTPUT',str(SD))).resolve()
R=next(p for p in SD.parents if (p/'src/kmd_quantitative').exists())
cfg=json.loads((O/'RUN_CONFIG.json').read_text());S=Path(cfg['source_review']);L=Path(cfg['legacy_interaction'])
Z='https://www.nature.com/articles/s41467-026-75101-w'
SO='https://www.nature.com/articles/s41467-026-76366-x'
BAT='https://publications.anl.gov/anlpubs/2022/07/176234.pdf'
ZD='https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-75101-w/MediaObjects/41467_2026_75101_MOESM5_ESM.xlsx'
SS='https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-76366-x/MediaObjects/41467_2026_76366_MOESM3_ESM.xlsx'
def write(n,t):(O/n).write_text(t.strip()+'\n')
def csv(n,rows):pd.DataFrame(rows).to_csv(O/n,index=False,float_format='%.14g')
def table(df):
    if not isinstance(df,pd.DataFrame):df=pd.DataFrame(df)
    def f(x):
        if pd.isna(x):return '—'
        if isinstance(x,(float,np.floating)):return f'{x:.9g}'
        return str(x).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['|'+'|'.join(df.columns)+'|','|'+'|'.join(['---']*len(df.columns))+'|']+['|'+'|'.join(f(v) for v in row)+'|' for row in df.itertuples(index=False,name=None)])
q=pd.read_csv(O/'PUBLIC_QV_VALIDATION.csv');m=pd.read_csv(O/'T08_REPRESENTATIVE_RESULTS.csv');b=pd.read_csv(O/'BOUNDARY_VALIDATION.csv');dc=pd.read_csv(O/'evidence/DC_SMALL_VALIDATION.csv');summary=json.loads((O/'evidence/RUN_RESULT.json').read_text())
a=m.set_index('case_id').loc['R0_Z_H1'];p=m.set_index('case_id').loc['P0_Z_H2'];ret=pd.read_csv(O/'evidence/SONG_CAPACITY_RETENTION.csv').iloc[0]

# Requirements distinguish exact primary-source equations from mass-volume identities derived here.
requirements=[]
def req(id,name,formula,inputs,loc,app,overlap,implemented,missing,scope='PACK',basis='一次資料の構造定義に基づく本研究のSI体積積算'):
    requirements.append(dict(component_id=id,component=name,formula_SI=formula,required_inputs=inputs,primary_source_url=BAT,source_location=loc,
        formula_origin=basis,applicability=app,existing_T09_overlap=overlap,implemented_function=implemented,calculable_scope='指定幾何が既知なら当該部材のみ計算可能',
        unresolved=missing,target_mass_kg=None,target_status='HOLD',accounting_scope=scope))
req('C01','セル外装','m=A_developed*sum(t_layer*rho_layer)','両面・シールを含む展開面積m2;各層厚mと密度kg/m3;セル数','§2.2;§5.2.5 pp58–61 (PDF77–80);§9.3.1.7 p110','積層パウチを選び層仕様・成形面積が確定すること','既知塗工材・箔と重複しない;シール別加算禁止','laminate_kg','LP/Sの外装面積・層仕様・セル数/端部形状')
req('C02','集電体一体タブ','m=rho*t*A_uncoated','積層数;各箔の未塗工幅/長さ;正負箔厚・密度','§5.2.2 Eq5.14;§5.2.5 p60 PDF79','箔一体タブと端子を区別;層ごと面積を集計','T09 foil_massのuncoated_areaへ渡すか本関数のどちらか一方','foil_increment_kg','LP/Sの未塗工幾何;溶接重ね代')
req('C03','集電箔余白・端層','m_add=rho*t*(A_margin+ A_extra_end)','塗工面積;両面係数2;負極端層数;余白とタブの非重複面積','§5.2.5 Eq5.33–5.34 pp59–60 PDF78–79','T09基準A_face/2の既計上分を除外すること','負極余裕面積がnegative_areaに含まれる場合は再加算しない;工程スリット廃棄材は搭載質量に含めない','foil_increment_kg','端層・端箔・実寸法;既存面積の包含範囲')
req('C04','セル端子','m=sum_j rho_j*V_j;矩形区間V=w*l*t','Al/Cu別内部・貫通・外部寸法;個数;密度','§5.2.2 Eq5.17;§5.2.5 Fig5.5 p61 PDF80','厚さや幅既定値は設計参照のみ;実寸を入力','一体箔タブC02から端子を除外;溶接接続でも独立物体の体積はそれぞれ数える','tab_kg;panel_kg','対象端子幾何と接合部材;Niめっきが必要なら別層')
req('M01','セル間・モジュール間接続','m=rho*A_cross*L*n; A_cross=I/sqrt(rho*sigma*Cp*dTdt)','電流A;導電率S/m;密度kg/m3;比熱J/kg/K;許容昇温K/s;長さm;個数','§5.3.2 Eq5.41 p64 PDF83;§5.6 Eq5.53–5.55 pp71–72 PDF90–91','断面設計式は均一導体・ジュール熱・熱容量条件;抵抗/温度/電力制約を別確認','タブ・端子・バスバーを物体IDで一度ずつ計上','tab_kg (既知断面);電流からの断面最適化は仕様のみ','出力・電流・温度制約・直並列構成')
req('M02','モジュール構造','m=sum rho_i*V_i;閉箱ならrho*(LWH-(L-2t)(W-2t)(H-2t))','セル配置;壁・パネル・支持材・絶縁パッドの幾何と材質','§5.3 Eq5.37–5.43 pp62–64 PDF81–83','closed_boxは本研究の閉箱単位検算でありBatPaC形状の完全再現ではない','熱伝導Al板・接続パネルを構造側と熱側へ重複計上しない','panel_kg;closed_box_kg','対象幾何・圧縮荷重・耐振動設計')
req('M03','モジュール管理・ガス放出','m_elec=0.046*Nmod; m_gas=0.005*Nmod','モジュール数;採用する設計範囲','§5.3.2 p64 PDF83;§7.5 pp86–87 PDF105–106','46gと5gはBatPaC参照仮定;対象電池の測定ではない','46gにモジュール配線・センサ等が包含;pack BMSへ重複追加しない','panel以外は明示係数積算(46g例のみ実行)','LP/Sの構成・ガス安全設計・適用適格性',basis='BatPaC報告の設計固定値;対象の実測値ではない')
req('P01','パック構造','m=sum rho_i*V_i','ラック・圧縮材・カバー・ジャケット・断熱材・支持材の幾何','§5.4–5.5 pp65–70 PDF84–89','セル・モジュール配置と圧縮/車載拘束が確定すること','モジュール壁とラック;断熱材と冷却板の所属を固定','panel_kg;closed_box_kg (形状既知のみ)','対象パック配置・機械安全設計')
req('P02','パック端子・バスバー','m=rho*A_cross*L*n','電流・昇温制約;端子長;バスバー経路・個数','§5.5.1;§5.6 Eq5.55 pp71–72 PDF90–91','直並列構成が確定すること','セル端子C04・接続M01と物体境界を分ける','tab_kg;panel_kg (既知幾何)','電流・幾何・構成')
req('P03','BMS・BDU','m_BMS=1.3*[1.1*(0.040*nPCB+0.020*nASIC)+sum(n_j*m_j)] kg','PCB/ASIC数;BDU全カテゴリ個数;モジュール数;パック電圧/構成','§7.2 pp84–85 PDF103–104;Table7.2 p85 PDF104;§7.6 p87 PDF106','PCB数はコンタクタ補正を含む有効個数を外部で決定;単一モジュール又は<50Vの例外を適用','interface配線はBMU/モジュールに内包;46g/moduleはこの式の外;二重の筐体係数を追加しない','bms_kg','LP/Sの構成・PCB/ASIC/コンタクタ数;低電圧規則の選定',basis='一次資料の係数・Table7.2と§7.6から直接組立;構成推定器ではない')
req('T01','内部冷却・熱伝導・冷媒','m=sum(rho_solid*V_solid)+rho_coolant*V_internal','伝導Al板・冷却板・管/マニホールド・内部冷媒の体積;密度;熱負荷','§5.3.2–5.4;§8.2;§8.5 Table8.4 p99 PDF118','セルの抵抗・発熱・冷却適格性から幾何を決定;必要な設計入力が未取得','構造材・冷媒・外部ポンプ冷媒と重複しない','panel_kg (板のみ);流路仕様は記号式','LP/S発熱・流路・冷却仕様;実電解液とは別')
req('T02','外部冷却管理装置','m_external=Table8.2(Qheat)*sqrt(Npack);単一パックで500/1000/3000/6000W ->2/3/5/7kg','熱負荷W;急速充電要否;パック数','§8.3.2 Table8.2 p93 PDF112;§8.5 Table8.4 p99 PDF118','本関数は単一パックのみ;急速充電時7kg選択は設計規則で冷却充足を保証しない','pack質量に入れない;共通冷却装置の絶対質量をLP/S差としない','external_cooler_kg (one-pack)','LP/S熱負荷・装置共用・実搭載構成','SYSTEM_EXTERNAL',basis='BatPaC Table8.2の離散参照設計;対象の実測値ではない')
req('T03','加熱・車両AC拡張','m_heating,m_ACは仕様が定まるまでU_system','ヒータ方式・能力;AC改修部材・質量;車載境界','§8.1;§8.5 Table8.4 p99 PDF118','BatPaCは加熱装置質量/体積をpack/system指標へ算入しない;本研究で実搭載全質量を求める場合は別途必要','原資料で質量対象外の部材を既知0と解釈しない','記号仕様のみ','対象車両・寒冷時要件・実装質量','SYSTEM_EXTERNAL')
req('S01','保護・絶縁・安全部材','m=sum rho_i*V_i+sum n_j*m_j','安全弁・ヒューズ・絶縁・耐火/衝撃部材・拘束材;要求規格','§5.3.2 ガス放出5g/module;Table7.2;§5.4–5.5','BatPaCの収録範囲だけで対象電池の安全適格性は判定しない','ヒューズはBDU;ガス放出はM03;物体IDを共有し二重加算を拒否','Ledger coverage;記号仕様','対象LP/Sの実安全設計と実証')
req('C05','その他セル部材・余剰液','m_other=sum明細; m_liquid=rho_liquid*(V_pores+V_excess)','実注液量;濡れ・飽和;添加剤・ガス余裕;絶縁部材','§2.2;§5.2;対象T09 liquid_mass仕様','既存T09の空隙充填量は幾何モデル;実注液量ではない','既存電解液小計へ実注液全量を重ねて足さない','既存T09 liquid_mass;新LedgerはNone保持','LP/Sの実注液量と余剰液・セルBOM')
csv('T09_COMPONENT_REQUIREMENTS.csv',requirements)

write('PUBLIC_CASE_SELECTION.md',f'''
# 公開全電池ケースの選定

主検算は[Zhang et al.]( {Z})のH-SCLMR/黒鉛全電池である。Source Data `RATE2026_DATA.xlsx`、`Figure S17`のA:B（形成1）、C:D（形成2）を採用する。SI Fig.S17a（PDF18頁）に形成2サイクル、0.1C、30°Cの対応がある。Methods Electrochemical measurements（本文PDF9–10頁）に全電池形成窓1.8–4.75V、2回、1C=250mA/g、黒鉛、N/P≈1.2、正極担持11mg/cm²がある。形成1と形成2は同系列の観測であり、独立標本ではない。

[元xlsx]({ZD})の放電枝から容量と平均電圧を同時に取る。容量は正極活物質基準、電圧は黒鉛全電池端子間である。CR2032実験系列に属する全電池であり、同論文のLi金属対極パウチ試験とは区別する。H-SCLMRのHは本論文の処理でありChenのS-200ではない。LP/Sの性能値としての適用は不可である。

正極配合80:8:2:10の全電池への対応とN/Pの形成後有効容量基準は別記されていない。したがってqとVの共同実測スナップショットに、fp=0.8の条件付き対応、T08有効N/P=1.2の仮定、移用qn=360Ah/kgを付けた仮想設計である。完全実測入力の完成パックを構成したとは判定しない。厚電極90%配合の無条件転用は行わない。

補助検算は[Song et al. Fig.4]({SO})のprotocol4320、45°C、66mA/g（0.33C）、2.0–4.3Vの黒鉛全電池である。[元xlsx]({SS})の`Figure 4`、AY:AZ（BoL放電）、BK:BL（EoL放電）を採用する。本文Fig.4キャプション（PDF6頁）でBoL=形成後の通常1サイクル、EoL=150サイクルと特定できる。SI Fig.S9（PDF11頁）も窓・レートを補助する。形成データとは混合しない。

Songは配合非公開、N/P定義温度に本文45°C/Methods35°C、小型セル表記1Ah/1.5Ahの不一致がある。Q–V数値積分の補助に限定し、Zhangとの共同T08入力や独立反復には使用しない。代表Q–Vとサイクル容量系列の同一試料・同一記録であることも未確認である。

除外した候補は、Song Fig.S8（25°Cだが特定サイクル不明）、Fig.S7b（対Li/Li+電位との対応不十分）、Zhang SCLMR/PCLMR形成曲線（原データ上端約4.8VとMethods全電池窓4.75Vの差がある）である。これらを推測で修正しない。

Zhang原図S17aの縦軸下限2.0Vに対しxlsx放電下端は1.8Vである。下端はMethodsとは整合するが、原図から低電圧末尾の完全一致は確認できない。平均電圧の独立した本文公表値もない。検算は公開数値の再現を意味し、図形と原測定の完全な同一性を保証しない。`evidence/PUBLICATION_ALIGNMENT.csv`に条件付き整合性と未解決点を記録した。
''')

write('T09_COMPONENT_ACCOUNTING.md',f'''
# T09部材会計の積算仕様

出典は[Argonne BatPaC v5.0 manual]({BAT})である。保存一次資料は`{S}/sources/BATPAC_NHTSA.pdf`であり、同一報告の米政府NHTSA公開版である。印刷頁とPDF通し頁を`T09_COMPONENT_REQUIREMENTS.csv`に併記した。原資料の式・設計固定値と、本研究で導いたSI体積質量恒等式を区別した。BatPaCワークブックの全計算を再実装したものではない。

対象LP/Sの部材質量は今回確定していない。`None`は未知であり0にしない。各部材は`PACK`又は`SYSTEM_EXTERNAL`に所属し、`coverage`で同じ物体の重複登録を拒否する。必要部材を省略した台帳は集計を拒否する。ただしこのチェックは宣言した分類内の完全性であり、設計BOM自体の完全性は別の工学レビューを要する。

実装は`scripts/components.py`である。外装は総展開面積×各層の面密度、箔余白は既計上塗工面積以外の箔面積×厚さ×密度、既知寸法のタブ/端子/板は体積×密度である。閉箱関数は外形体積−内形体積で角を一度だけ数える単位検算であり、対象の実パック形状を仮定しない。接続断面はBatPaC Eq5.53–5.55より、I²L/(Aσ)=ρAL Cp(dT/dt)から A=I/√[ρσCp(dT/dt)] と導ける。この熱的制約の設計最適化は未実装である。

BMSはTable7.2と§7.2/7.6から、m=1.3{{1.1(0.040 nPCB+0.020 nASIC)+Σ n_j m_j}} kgを実装した。BDU1個質量はmain contactor750g、aux180g、precharge90g、resistor185g、disconnect150g、service fuse80g、charger fuse24g、current sensor55gである。電圧/モジュール構成による除外、PCB数の主コンタクタ補正は入力側で確定させる。1PCBは常に正しいという意味ではない。モジュール管理46g/moduleは別計上、ガス放出5g/moduleも別物である。interface配線・センサをこの参照集約質量へさらに加算しない。

内部冷却板・伝導板・冷媒はパック側である。Table8.2の外部管理装置は1パックで冷却能力500/1000/3000/6000Wに対し2/3/5/7kgを選ぶ。関数は最小充足区分を選び、入力不明又は通常条件で6000Wを超えるとNoneを返す。急速充電指定の7kgは原資料の選択規則であり、熱的充足を検証した値ではない。複数パックの√N補正は仕様化のみで未実装である。Table8.4（p99/PDF118）では外部冷却管理の質量はbattery system側であり、pack側には入らない。熱管理装置の絶対7kgを材料差7kgと置くことはできない。加熱装置がBatPaC質量指標の対象外であることも、実物の質量0を意味しない。

`evidence/T09_SYNTHETIC_COMPONENT_RESULTS.csv`は各関数の人工幾何単位例である。外装0.1m²×(40µm×2700kg/m³+80µm×900kg/m³)=0.018kg、Cu余白0.003m²×10µm×8960kg/m³=0.0002688kg、Al矩形端子2個=0.005184kgである。これらは1つの製造可能なセル/パックBOMとして寸法整合させたものではない。台帳例は未知保持と会計境界のソフトウェア検証に限り、その既知小計をLP/SのKへ置換しない。未知部材・内部熱部材・保護部材は台帳でもNULLを維持する。

元T09のfoil_massが未塗工・端層を受け取る場合、新しいfoil_incrementを再加算してはならない。余剰注液も既存空隙充填量へ全注液量を重ねて加算しない。T08の固定34kg（100×0.19+15）にこれらを加えることもしない。T09完成パック質量はHOLDである。
''')

write('T08_T09_COMPARABILITY.md','''
# T08・T09の比較可能性

共通する確定的計算範囲は正極・負極の活物質と乾燥塗工材である。同じ総Wh、同じ測定状態のqとV、有効N/P定義、活物質割合を揃えれば、この範囲を直接比較できる。qを実効値として使った後にICEや保持率を再乗算しない。

T08はその他セル質量0.19kg/cell×100とパック付加15kgを固定集約する。合計34kgの実際のBOM配分は不明である。T09はAl/Cu集電箔、セパレータ、幾何空隙に基づく電解液を個別積算する。T08の34kgにこれらの絶対質量を足すと包含不明の部材を二重計上する。T08とT09の全質量の数値が近くても妥当性確認とはならない。

T09では担持量・密度・空隙率・濡れ・余剰液を置いた既知小計Kと、外装・端子・未塗工箔・構造・接続・BMS・熱管理・保護等の未知Uを分け、Mpack=K+Uを維持する。旧Kは仮定幾何による既知計算成分という意味であり、実測BOMの既知量ではない。今回の幾何単位例を既存Kへ足して対象パックを完成させない。

材料間差は D=M_LP−M_S=(K_LP−K_S)−(U_S−U_LP) である。δU=U_S−U_LP、b=K_LP−K_SとしてδU<bで軽量化、δU=bで相殺、δU>bで逆転である。旧LP/S設計のbはfixed_loadingで9.722608121kg、fixed_area_LPで5.977891152kgであり、今回のZhang形成スナップショットの0.041437385kgとは対象・モデルが異なる。U_LP,U_S≥0でも差δUの符号は固定されない。δUだけ制約しても絶対Uは決まらない。

完成パックの直接比較には、同じ機能（使用可能Wh、電圧、出力、温度、寿命、安全要求）、共通のセル形式/直並列構成、同じpack/system境界、部材リストの閉合、材料別の実入力が必要である。これらが未確定の現状では絶対パック・車両・DCを実測に基づく確定値として比較できない。比較可能なのは共通塗工材成分、宣言した仮定でのT08条件付き差、およびT09の記号的未知差境界である。
''')

# Claim-by-claim evidence and permitted thesis formulations.
claims=[]
def claim(id,kind,text,primary,loc,result,assumptions,experimental,model,unverified,decision,allowed):
    claims.append(dict(claim_id=id,evidence_class=kind,claim=text,primary_source=primary,source_location=loc,calculation_result=result,assumptions=assumptions,
        experimentally_supported=experimental,model_supported=model,unverified=unverified,thesis_adoption=decision,permitted_statement=allowed))
claim('C01','公開近縁全電池','H-SCLMR形成1/2の容量・平均電圧を同一曲線から計算した',Z+' ; '+ZD,'SI FigS17a PDF18;Methods PDF9–10;sheet A:B/C:D','PUBLIC_QV_VALIDATION.csv Z_H1/Z_H2','Source Dataを正とし放電Qspanを使用','公開記録の容量/電圧;原実験を独立再測定したものではない','XML Decimalとnumpy整合','原図低電圧末尾の完全一致;LP/S移用','CONDITIONAL GO','公開数値から270.85/273.65Ah/kgと3.501438881/3.485490026Vを再現した')
claim('C02','補助系列','Song通常1/150サイクルの記録区間を独立積分した',SO+' ; '+SS,'Fig4b;caption PDF6;Figure4 AY:AZ/BK:BL','PUBLIC_QV_VALIDATION.csv S_BOL/S_EOL','Q開始約0.24を外挿しない','公開近縁全電池Q–V','数値積分一致','代表曲線とcycle系列の同一記録性;配合非公開','CONDITIONAL GO','欠落始端を除く記録区間の平均電圧・エネルギーを算出した')
claim('C03','仮想設計','20kWhのT08共同入力代表点の差は0.041437385kg',Z+' ; legacy T08','同一H-SCLMR形成1/2;公開q,Vのみ','T08_REPRESENTATIVE_RESULTS.csv','fp/fn=.8;qn360;effectiveNP1.2;u1;other34kg','q,Vのみ公開実測から計算','既存式と独立SI式一致','配合対応・有効NP・実部材・製造可能性','CONDITIONAL GO','形成状態別の特性を固定Whで設計し直した条件付き質量差である')
claim('C04','数理境界','容量・電圧・利用率・追加質量・負極設計の境界を検算した','legacy T08; 本研究代数','同条件比較式','BOUNDARY_VALIDATION.csv','他入力固定;正の定義域;数学探索を区別','物理的実現性未確認','解析根・二分法・符号一致','実用運転で境界に到達できるか','GO_WITH_SCOPE','本モデル内の成立・消失境界である')
claim('C05','部材会計','T09の未知部材を仕様化しNULL保持と重複拒否を確認した',BAT,'§5.2.5–5.6;§7.2–7.6;§8.3/8.5','T09_COMPONENT_REQUIREMENTS.csv;evidence/T09_COMPONENT_CHECKS.csv','対象BOMは未知;人工単位例のみ','参照設計方式;対象測定なし','体積質量・境界・重複チェック','対象幾何・熱・安全設計;完全BatPaC再現','CONDITIONAL GO','部材会計の実装可能範囲と未確定項目を明示した')
claim('C06','記号的質量差','T09の成立条件はdeltaU<K_LP−K_Sである','legacy T09','旧採用報告;M=K+U','BOUNDARY_VALIDATION.csv T09_UNKNOWN_*','同じpack範囲;Uをゼロ補完しない','対象Uの実測なし','代数と符号検算','絶対Uと対象パック質量','GO_WITH_SCOPE','既知小計差に未知部材差が及ぼす相殺境界を示した')
claim('C07','保存軌跡Controlled-DC','仮想質量差を凍結核と3保存軌跡へ接続した','frozen controlled_dc + saved trajectory hashes','evidence/SOURCE_MANIFEST.csv','evidence/DC_SMALL_VALIDATION.csv','固定軌跡;Crr2条件;η.9;仮想車両質量','実車計測ではない','旧参照再現・成分閉合・少数新質量一致','460全軌跡に対する新ケース統計;実車外挿','GO_WITH_SCOPE','3軌跡の観測窓内の条件付きDC応答である')
claim('C08','既存LP/Sモデル','旧5.448297415kg/0.412579–0.413590%を今回の近縁結果と区別する','legacy final adoption/interactions','既存FINAL_REPORT_JA;原Controlled-DC','evidence/LEGACY_REFERENCE_CHECKS.csv','旧入力とモデル境界を維持','LP/S実用パック測定なし','既存条件付き計算として支持','実用EV削減の実証','CONDITIONAL GO','旧LP/S仮定モデルと今回の近縁全電池検算を別の証拠層とする')
claim('C09','対象材料実験','Chen逆算容量を対象の初回放電容量と同一視する','https://doi.org/10.1038/s41467-020-17126-3','旧SOURCE_EVIDENCE_MATRIX/HOLD_REASSESSMENT','今回更新なし','必要な初回Q–Vを未取得','支持しない','逆算恒等式まで','対象LP/S初回容量・平均全電池電圧・利用率','NOT_ADOPT','Chen逆算容量の初回容量への採用はHOLDである')
claim('C10','実用電池予測','LP/S完成パック質量を実測又は確定した',Z+' ; '+SO+' ; '+BAT,'対象条件に一致する完成BOMなし','actual_pack_mass_kg=NULL','実材料別BOM未取得','支持しない','仮想設計まで','対象完成セル/パック','NOT_ADOPT','対象LP/S完成パックは未確定である')
claim('C11','実車実証','実EVの電力量削減率を実証した','保存軌跡+凍結モデル','実車DC電力計測なし','practical_EV_claim=HOLD','実車境界/回生等未同定','支持しない','保存軌跡上のモデル応答まで','実車電流電圧・軌跡・補機・回生','NOT_ADOPT','Controlled-DCは実車省電力の実証ではない')
claim('C12','量子計算帰属','量子計算によってLP/S材料性能を改善した','対象となる実証なし','本研究の材料改善実験/量子計算達成なし','NOT_ESTABLISHED','材料数値は一次資料/仮定','支持しない','質量とDCの条件付き関係まで','量子計算から材料改質への因果鎖','NOT_ADOPT','量子計算技術の成果へ帰属しない')
claim('C13','レベル解釈','限定Level2の完了は対象LP/S実用性能実証である','本監査の範囲定義','LEVEL2_COMPLETION_AUDIT.csv','限定Level2のみ','近縁公開入力と仮定の分離','対象実証は未達','検算手続き完了','Level3対象電池・実車','NOT_ADOPT','限定Level2と対象実証Level3を明確に区別する')
csv('CLAIM_EVIDENCE_MATRIX.csv',claims)

completion=[
 ('A','CONDITIONAL PASS','DOI/ローカルSHA/シート/セル/形成条件を追跡可能','PUBLIC_QV_VALIDATION.csv;evidence/SOURCE_MANIFEST.csv','Zhang原図末尾と元xlsxの完全一致は未確認;原著著者側の数値対応情報を将来取得;今回連絡しない'),
 ('B','PASS','4曲線をopenpyxl+numpyと独立ZIP/XML+Decimal60で再現','PUBLIC_QV_VALIDATION.csv','PASSは公開数値の記録区間に限る;Song未収録始端を外挿しない;原図との完全一致はAの条件'),
 ('C','CONDITIONAL PASS','同じ形成枝のq,Vで共同入力を構成;不足入力を移用/仮定/NULLとして区分','JOINT_INPUT_CASES.csv','全電池専用配合・形成後NP基準・負極容量・実BOMを取得するまで仮想設計に限定する'),
 ('D','PASS','17代表点で既存T08関数と独立percell SI計算が一致','T08_REPRESENTATIVE_RESULTS.csv','実測パック質量の検証ではない'),
 ('E','PASS','6基準根の代数/二分法/前後符号が一致;定義域外と根なしも検出','BOUNDARY_VALIDATION.csv','境界の物理的実現性は別途測定を要する'),
 ('F','CONDITIONAL PASS','対象部材・計算式・重複・未知U・pack/system範囲を明記','T09_COMPONENT_REQUIREMENTS.csv;T09_COMPONENT_ACCOUNTING.md','完成BOM/熱/安全設計取得後に積算;現状は一部関数と記号仕様までで完成質量HOLD'),
 ('G','PASS','旧結果再利用を検討し新質量は3軌跡だけ凍結核で直接確認','DC_REUSE_DECISION.csv;evidence/DC_SMALL_VALIDATION.csv','実用絶対DCはHOLD;未評価軌跡へ新ケースの数値を外挿しない'),
 ('H','PASS','実測/公開検算/仮想設計/保存軌跡/実用/量子帰属を分離','CLAIM_EVIDENCE_MATRIX.csv','禁止主張は論文へ採用しない')]
csv('LEVEL2_COMPLETION_AUDIT.csv',[dict(condition=k,status=s,evidence=ev,artifact=ar,remaining_action=ac,scope='LIMITED_LEVEL2_PUBLIC_RELATED_CELL_AND_CONDITIONAL_MODEL') for k,s,ev,ar,ac in completion])

# Prior values are immutable references, explicitly distinct from this run.
legacy=pd.read_csv(L/'INTERACTION_RESULTS.csv');old=legacy[legacy.case_id=='N0000'].iloc[0]
legacyrows=[dict(name='T08_base_mass_delta',expected=5.448297415,actual=old.delta_mass_kg,tolerance=1e-9,unit='kg',status='PASS' if abs(old.delta_mass_kg-5.448297415)<1e-9 else 'FAIL')]
oldreport=(R/'review_outputs/t08_t09_final_adoption_20261105/FINAL_REPORT_JA.md').read_text()
for label,value in [('extra','5.448297415'),('u','0.877094072'),('V','3.193155684'),('CRR_LOWER_BOUND','0.412579'),('CRR_UPPER_BOUND','0.413590')]:
 legacyrows.append(dict(name=label,expected=value,actual='present in immutable adopted report',tolerance=None,unit='reference record',status='PASS' if value in oldreport else 'FAIL'))
for policy,expect in [('fixed_loading',9.722608121),('fixed_area_LP',5.977891152)]:
 rr=legacy[(legacy.model=='T09')&(legacy.policy==policy)&(legacy.S_L==.1)&(legacy.S_ep==.25)&(legacy.S_en==.25)].iloc[0]
 legacyrows.append(dict(name='T09 known delta '+policy,expected=expect,actual=rr.delta_mass_kg,tolerance=1e-9,unit='kg',status='PASS' if abs(rr.delta_mass_kg-expect)<1e-9 else 'FAIL'))
csv('evidence/LEGACY_REFERENCE_CHECKS.csv',legacyrows)

write('FINAL_REPORT_JA.md',f'''
# 因果経路2の限定Level 2検証・最終報告

## 1. 総合判定

**CONDITIONAL GO：公開近縁全電池データによる限定Level 2の検算・会計・学術監査は、明記した条件の下で完了である。** 対象LP/S実用電池の性能実証、T09完成パック、実車DC効果はHOLDである。A/C/FはCONDITIONAL PASS、B/D/E/G/HはPASSである。完全実測入力によるパック予測を達成したとは判定しない。

新規計算は公開4放電曲線、T08代表17条件、境界検証18行、3保存軌跡×2転がり条件×4質量条件のDC24行である。18境界行は6基準根、6定義域/根不存在診断、6旧T09未知差の符号点であり、18個の独立実験ではない。既存527質量条件・2,575境界点・402,040DC行は変更せず参照した。既存成果物と保護対象{summary['protected_files']}ファイルのSHA-256を検査した。

## 2. 採用した公開全電池ケース

主検算は[Zhang et al.（2026）]({Z})のH-SCLMR/黒鉛全電池、SI Fig.S17a（PDF18頁）の形成1/2サイクル、0.1C=25mA/g、30°C、1.8–4.75Vである。1材料・1系列の2状態であり、材料間改善や独立反復ではない。同論文のLi金属対極の高担持試験やパウチ試験を混合しない。

補助検算は[Song et al.（2026）]({SO})のprotocol4320、45°C、0.33C=66mA/g、2.0–4.3V、形成後通常1/150サイクル（Fig.4キャプションPDF6頁）である。非公開配合とN/P条件の不一致があるためQ–V検算に限定した。LP/Sとは異なる材料である。詳細は`PUBLIC_CASE_SELECTION.md`である。

## 3. 実際に使用した入力値

主条件のqとVは下表の同じ放電枝に由来する。qの単位mAh/gは数値としてAh/kgに等しい。fp=0.8はMethodsの標準配合80:8:2:10を全電池にも適用する条件付き仮定、fn=0.8は報告黒鉛配合8:1:1、qn=360Ah/kgはBatPaCの別化学系設計参照値である（Fig.3.14、PDF46頁、前回保存図`BATPAC_CHEM_PAGE46.png`）。qnは実測不足のため300/400も探索した。

N/P≈1.2は原著報告であるが、形成後の有効容量基準との対応は不明であり、T08有効N/P=1.2への対応を仮定とした。実効放電容量qを直接使うためu=1は帳簿上の定義であり、100%の物理利用率を実測した意味ではない。u=0.95は追加の仮想損失でありICE/保持率を重ねて使わない。

総エネルギーE=20,000Wh、セル数100、セルその他0.19kg/cell、パック付加15kg、基準追加差0kgは旧T08を継承する研究仮定である。その他合計は34kgである。公開コインセルの実測パック構成ではない。実際の負極容量・有効N/P・セル/パック部材・完成パック質量はNULLである。入力の5分類と不足項目は`JOINT_INPUT_CASES.csv`に記録した。

## 4. 公開Q–Vの検算結果

{table(q[['case_id','range','n_points','Q_discharge_mAh_g','mean_discharge_V','specific_energy_Wh_kg_positive_active']].rename(columns={'case_id':'ケース','range':'元セル範囲','n_points':'点数','Q_discharge_mAh_g':'放電容量Ah/kg','mean_discharge_V':'平均V','specific_energy_Wh_kg_positive_active':'正極活物質基準Wh/kg'}))}

[Zhang xlsx]({ZD})は`Figure S17`、[Song xlsx]({SS})は`Figure 4`である。元列ラベル、SHA、サイクル、窓、レート、行範囲、放電枝の抽出法は`PUBLIC_QV_VALIDATION.csv`にある。Zhangは容量がリセットされる点から後半放電を切り出し、Songは明示されたdchg列を使った。再サンプリングや枝の継ぎ合わせは行っていない。

Qdis=Qend−Qstart、e=Σ(Vi+Vi+1)(Qi+1−Qi)/2、平均V=e/Qdisである。eの単位V·mAh/g=mWh/g=Wh/kgは正極活物質だけを分母とし、セル/パック比エネルギーではない。openpyxl+numpy台形積分と、xlsxを直接ZIP/XMLで読んだ60桁Decimalの別経路で、容量・積分・平均電圧が一致した。最大積分差は{q.integral_error_Wh_kg.max():.3g}Wh/kgである。これは計算差であり測定精度を意味しない。

Songの記録はQstart={q.iloc[2].Q_start_mAh_g:.5f}/{q.iloc[3].Q_start_mAh_g:.5f}mAh/gから始まるため、表は記録区間容量である。欠落初期区間を外挿せず、Qend={q.iloc[2].Q_end_mAh_g:.5f}/{q.iloc[3].Q_end_mAh_g:.5f}mAh/gとも区別した。サイクル系列H:Iは{ret.BoL_capacity_mAh_g:.5f}→{ret.EoL_capacity_mAh_g:.5f}mAh/g、保持率{ret.retention_percent:.6f}%であるのに対し、代表曲線Qspanの比は{ret.representative_curve_Qspan_retention_percent:.6f}%である。同じ測定記録と確定できず、この差を丸め誤差と説明しない。Fig.7の別大型セル663Wh/kgとは比較しない。

Zhang原図下限2.0Vとxlsx下端1.8Vの完全な図形対応は未確認である。Methodsの1.8Vとは整合するが、原図から末尾を補完しない。原著に本4曲線の平均Vの別スカラー値はなく、本文値との完全一致を装わない。

## 5. T08質量計算の結果

式は旧T08のままである。qp=q·u、mp=E/(V·qp)、mp,dry=mp/fp、mn=(E/V)·NP/qn、mn,dry=mn/fn、Mpack=mp,dry+mn,dry+100mother,cell+mother,pack+mextraである。容量Ah/kg、E Wh、V V、質量kgである。負極不可逆損失は本検算で別途重ねて加算しない。

{table(m.loc[m.case_id.isin(['R0_Z_H1','P0_Z_H2','V_MINUS','V_PLUS','U_095','NP_125','EXTRA_1','QN_300','QN_400']),['case_id','positive_active_kg','positive_coating_kg','negative_active_kg','negative_coating_kg','other_total_kg','hypothetical_pack_kg','delta_reference_minus_case_kg']].rename(columns={'case_id':'条件','positive_active_kg':'正極活物質kg','positive_coating_kg':'正極乾燥kg','negative_active_kg':'負極活物質kg','negative_coating_kg':'負極乾燥kg','other_total_kg':'その他kg','hypothetical_pack_kg':'仮想パックkg','delta_reference_minus_case_kg':'基準−比較kg'}))}

基準セル1個は{a.cell_mass_kg:.9f}kg、100セル合計{a.cell_sum_kg:.9f}kg、仮想パック{a.hypothetical_pack_kg:.9f}kg、20kWh/M={a.hypothetical_pack_specific_Wh_kg:.9f}Wh/kgである。比較はそれぞれ{p.cell_mass_kg:.9f}kg、{p.cell_sum_kg:.9f}kg、{p.hypothetical_pack_kg:.9f}kg、{p.hypothetical_pack_specific_Wh_kg:.9f}Wh/kgである。差は{summary['delta_kg']:.12f}kg（{p.relative_mass_saving_percent:.9f}%）である。

17条件の全成分・相対差・比エネルギーは`T08_REPRESENTATIVE_RESULTS.csv`にある。旧関数をASTで読んで実行し、独立の1セルSI経路（Wh→J→C→g→kg、100セル合算）と照合した。最大差は{m.mass_error_kg.max():.3g}kgである。容量増加と平均電圧低下を共同入力した微小差であり、材料性能改善の実験結果ではない。未知部材を解決したのではなく、固定質量を明示した仮想設計の算術検算である。

## 6. 成立・消失境界

基準質量MA、C=100mother,cell+mother,pack、W=MA−C−mextra、a=NP/(qn fn)、h=V W/E−aと置く。q*=1/(u fp h)、u*=1/(q fp h)でありh>0が必要である。V*=E[1/(q u fp)+a]/WでW>0が必要である。mextra*=MA−C−(E/V)[1/(q u fp)+a]である。NP*=[V W/E−1/(q u fp)]qn fn、qn*=NP/{{fn[V W/E−1/(q u fp)]}}で後者の分母は正でなければならない。

{table(b[b.boundary_id.str.startswith('B_')][['axis','analytic_root','unit','numerical_root','delta_on_kg','delta_below_kg','delta_above_kg']].rename(columns={'axis':'変数','analytic_root':'解析根','unit':'単位','numerical_root':'二分法根','delta_on_kg':'境界差kg','delta_below_kg':'直前差kg','delta_above_kg':'直後差kg'}))}

容量/利用率/平均電圧/負極容量は根より大きい側でD=MA−MB>0、追加質量/N/Pは小さい側でD>0である。他入力はZ_H2仮想設計に固定した。6根全てで二分法と解析根が一致し、境界上|D|<1e−9kg、前後で符号が変わる。存在する根が製造・運転可能という意味ではない。

qを比較条件の0.8倍にするとu*>1となり利用率0<u≤1では相殺できない。C+mextra>MAなら正の有限q/u/V根は存在しない。qを0.4倍にした形式NP根は負となり正NPでの根はない。V=3.0Vの場合の追加差根は負であり、S側だけ非負追加質量を置く探索域外である。これらも`BOUNDARY_VALIDATION.csv`で別判定した。

旧LP/SのT09はD=b−δUであり、b=9.722608121kg（fixed_loading）又は5.977891152kg（fixed_area_LP）を維持した。δU=b±0.1kgの差は∓0.1kgであり、完成質量は計算しない。旧LP/S T08境界5.448297415kg、u=0.877094072、V=3.193155684Vを今回の根へ置換しない。

## 7. T09部材会計の結果

[BatPaC v5.0]({BAT})に基づき{len(requirements)}分類で幾何・材料・構成・熱入力、式、適用条件、重複範囲、未確定項目を仕様化した。`T09_COMPONENT_REQUIREMENTS.csv`と`T09_COMPONENT_ACCOUNTING.md`が正本である。外装積層、箔余白、矩形タブ/端子/板、閉箱、明示構成のBMS、単一パック外部冷却参照を実装した。熱/電流に基づく全体設計、実対象BOMの生成は未実装である。

人工幾何例の単位検算、閉箱の独立面分割、未知None保持、箔/配線二重登録拒否、必要項目の省略拒否を実行した。人工例の0.018kg外装等をLP/Sの部材質量として採用しない。外部冷却質量はbattery system側、内部流路・冷媒はpack側である。T08固定34kgへの追加は行わない。T09完成パック質量はHOLDを維持した。

## 8. Controlled-DC接続要否

既存527条件・402,040行を照合したが今回代表点の同一絶対質量はなく、近傍のDC数値をそのまま流用しなかった。新規評価は基準・比較・追加1kg・相殺点の4仮想質量だけ、既存460軌跡から距離最小・中央・最大の3軌跡、CRR_LOWER_BOUND/UPPER_BOUNDで直接行った。他の代表点は質量検算のみとした。`DC_REUSE_DECISION.csv`に個別判断を記録した。

仮想車両質量式は1155−20000/180+Mpack kgのままである。基準{dc.reference_running_kg.iloc[0]:.9f}kg、比較{dc[dc.case_id=='P0_Z_H2'].comparison_running_kg.iloc[0]:.9f}kgである。旧検証区間内だが完全一致質量ではないため少数の直接計算とした。凍結核ハッシュと保存軌跡ハッシュを確認し、同じ3軌跡上の旧LP参照6行を再現した。

{table(dc[dc.case_id=='P0_Z_H2'][['rolling_case','distance_km','reference_DC_Wh','comparison_DC_Wh','saving_DC_Wh','saving_percent','saving_Wh_km','saving_Wh_kg']].rename(columns={'rolling_case':'Crr条件','distance_km':'距離km','reference_DC_Wh':'基準Wh','comparison_DC_Wh':'比較Wh','saving_DC_Wh':'差Wh','saving_percent':'差%','saving_Wh_km':'差Wh/km','saving_Wh_kg':'差Wh/kg'}))}

この表の範囲は3軌跡のみであり、460全体の新しい最大/最小ではない。全24行の絶対値・成分は`evidence/DC_SMALL_VALIDATION.csv`である。固定軌跡と回転等価質量の下でW2空気抵抗/W4回転項の差は0、W1転がり/W3並進と正値化枝変更補正で差が閉合する。最大閉合残差は1e−7Wh未満である。区間仕事の和を正値化後にη=0.9で割る旧規則を維持し、回生/HVAC/勾配/停止時補機/未観測終端ギャップは追加しない。

未知Uを持つT09の完成車両質量・絶対DCは計算しない。表は仮想T08設計のモデル応答であり、公開電池搭載EVの予測や実車省電力実証ではない。

## 9. 修士論文に採用できる主張

公開近縁全電池の同一放電曲線からのq/V/e換算再現、明示仮定下のT08質量式の整合性、連続境界と根不存在の条件、T09未知差の記号境界、保存軌跡上の質量→DC応答は採用可能である。実験値、原著由来計算値、移用値、仮定、未確定を分けて記載することが条件である。`CLAIM_EVIDENCE_MATRIX.csv`に{len(claims)}主張を監査した。

採用可能な表現は「公開近縁全電池を使いモデル換算の整合性を検算した」「20kWhの仮想設計で質量優位性が消失する条件を示した」「凍結モデルの保存軌跡上でDC応答を確認した」である。量子計算でLP/S性能を改善した、LP/S完成パック質量を確定した、実EV削減率を実証した、近縁値をLP/S測定値として使った、という主張は採用不可である。独立標本としての検定や恣意的CI/確率は算出しない。

## 10. 残存HOLD

対象LP/S初回容量へのChen逆算容量の適用、LP/S–黒鉛の同条件容量/平均電圧/利用率、混合密度・高担持利用率・負極容量と形成後バランス、実注液量、完成BOM、出力・寿命・安全性、T09完成質量、実車DC実証は未解決である。近縁資料でこれらを解除しない。Zhangの配合対応と有効NP基準、原図低電圧末尾、Song代表曲線と容量系列の対応も残る。

## 11. 限定Level 2の完了判定

{table(pd.DataFrame([{'条件':x[0],'判定':x[1],'根拠':x[2]} for x in completion]))}

限定Level2は「公開近縁入力の独立数値検算＋仮定を区別した代表設計＋会計仕様＋主張監査」の範囲で完了である。A/C/Fの条件を外して「完全な文献実証」と記載してはならない。完成BOM・物理的実現性・対象LP/Sへの適格性を必須とするLevel2定義では依然HOLDである。Level3（実用全電池・実車実証）は未達である。

## 12. 次に必要な作業

提出前は本監査の数値と採用可能文言を論文の表・限界へ統合し、査読時に元xlsxとスクリプトへ辿れるようにする作業を別タスクで行う。既存LP/S結果、今回近縁検算、仮想感度を別の表にする。今回原本は変更していない。

次の実装優先順は、(1)全電池配合と形成後NP基準が確認できる既存資料が追加された時だけ共同入力を更新、(2)対象設計の非重複BOM・幾何・注液・熱入力を取得しT09台帳を閉じる、(3)成立した少数の新質量だけ既存DC条件と照合し必要分を凍結核で評価、(4)出力/寿命/安全と実車DCを別実証で検証、である。資料不足時は記号UとHOLDを維持する。現段階で大規模DC再計算は不要である。

次にCodexへ指示すべき作業は「本run01のCONDITIONAL GOの範囲と禁止主張を維持し、修士論文への統合案・図表・引用差分を別ディレクトリで作成せよ」である。実測入力未取得のまま完成パック/実車予測へ拡張しない。
''')

# Publication-style plots: source units and limits are part of each figure.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':9})
fig,ax=plt.subplots(1,2,figsize=(11,4))
for i,ids in enumerate([['Z_H1','Z_H2'],['S_BOL','S_EOL']]):
 for id in ids:
  f=pd.read_csv(O/'evidence'/f'{id}_DISCHARGE.csv');ax[i].plot(f.q_mAh_g-f.q_mAh_g.iloc[0],f.voltage_V,label=id,lw=1.2)
 ax[i].set(xlabel='Recorded discharge Q span (Ah/kg positive active)',ylabel='Full-cell terminal voltage (V)');ax[i].legend();ax[i].grid(alpha=.2)
ax[0].set_title('Zhang Fig.S17: formation 1/2, 0.1C, 30 C')
ax[1].set_title('Song Fig.4: normal 1/150, 0.33C, 45 C')
fig.suptitle('Public related LMR/graphite; not LP/S; native Source Data, no tail extrapolation')
fig.tight_layout();fig.savefig(O/'figures/PUBLIC_QV.png',dpi=180);fig.savefig(O/'figures/PUBLIC_QV.pdf');plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4.8))
r=m[~m.case_id.str.startswith('ROOT')];ax.barh(r.case_id,r.delta_reference_minus_case_kg);ax.axvline(0,color='black',lw=.8)
ax.set_xlabel('Reference minus comparison hypothetical pack mass (kg)');ax.set_title('T08 20 kWh redesign; Zhang formation snapshots + declared assumptions')
fig.text(.1,.01,'E=20kWh, fp=fn=0.8, qn=360Ah/kg, NP=1.2, u=1, other=34kg unless varied; not actual mass',fontsize=8)
fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(O/'figures/T08_REPRESENTATIVES.png',dpi=180);fig.savefig(O/'figures/T08_REPRESENTATIVES.pdf');plt.close(fig)
write('figures/README.md','''
# 図の範囲

PUBLIC_QVはSource Dataの生点を直線接続した放電曲線である。横軸は記録開始点からの放電容量Ah/kg正極活物質、縦軸は全電池端子電圧Vである。Zhang形成1/2は0.1C、30°C、Methods1.8–4.75V、Song通常1/150は0.33C、45°C、2.0–4.3Vである。未収録区間は補完していない。出典セル範囲・SHAはPUBLIC_QV_VALIDATION.csvにある。

T08_REPRESENTATIVESは基準形成1由来設計−比較設計のkg差である。比較形成2のq/Vを基本とし、他入力はRUN_CONFIG.json、各変更はT08_REPRESENTATIVE_RESULTS.csvを参照する。その他34kg等を仮定した20kWh再設計であり、実セルのサイクル中質量変化・実パック性能・対象LP/S測定ではない。
''')
versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,openpyxl=openpyxl.__version__,matplotlib=matplotlib.__version__,platform=platform.platform())
write('evidence/ENVIRONMENT.json',json.dumps(versions,indent=2))
catalog=pd.read_csv(S/'evidence/SOURCE_CATALOG.csv')
catalog=catalog[catalog.local_evidence.fillna('').str.contains('RATE2026|LMR2026|BATPAC')].copy()
catalog['immutable_source_directory']=str(S)
catalog.to_csv(O/'evidence/PRIMARY_SOURCE_CATALOG.csv',index=False)
write('README.md','''
# 因果経路2・限定Level2検証 run01

結論はFINAL_REPORT_JA.md、計算条件はRUN_CONFIG.json、数値確認はevidence/NUMERICAL_CHECKS.csv、独立した保存後監査はevidence/SERIALIZED_AUDIT.csvにある。原データを新しく読み直し、旧T08関数と凍結DC核を参照する。旧成果物・論文は書き換えない。

リポジトリルートで以下を順に実行する。

```bash
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/pathway2_level2_validation_20261105/run01/scripts/validate.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/pathway2_level2_validation_20261105/run01/scripts/report.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python review_outputs/pathway2_level2_validation_20261105/run01/scripts/audit.py
```

完全再現にはRUN_CONFIG.json記載の旧成果物、旧T09参照、保存軌跡アーカイブ、凍結コード、sourcesのPDF/xlsxが必要である。外部取得は不要である。環境のバージョンはevidence/ENVIRONMENT.json、原著・SI・元xlsxのURLはevidence/PRIMARY_SOURCE_CATALOG.csvに記録する。別出力への再実行は環境変数LEVEL2_OUTPUTに新しい空ディレクトリの絶対パスを与え、3スクリプトに共通指定する。設定を変更する場合は別のJSONへ複製し、LEVEL2_CONFIGにその絶対パスを与える。元成果物を変更しない。

今回の数値は公開近縁全電池の記録と仮想20kWh設計の算術検算である。実用LP/S完成パック・実車DCはHOLDである。17質量条件、境界18行、3軌跡/2Crr/4質量のDC24行であり、大規模再計算ではない。図はfigures、放電生抽出と部材単位検算はevidenceにある。
''')
print('Reports, acceptance CSVs and figures generated.',flush=True)
