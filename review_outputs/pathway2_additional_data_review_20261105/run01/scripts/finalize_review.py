from pathlib import Path
import csv,json,hashlib,sys,datetime,subprocess
sys.dont_write_bytecode=True
import pandas as pd
import numpy as np
O=Path(__file__).resolve().parents[1];R=O.parents[2]
OLD=R/'review_outputs/t08_t09_interaction_boundaries_20261105/run01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def out(name,rows):
    df=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows);df.to_csv(O/name,index=False,float_format='%.10g');return df
def table(df,cols=None):
    if cols:df=df[cols]
    def f(v):return '未取得' if pd.isna(v) else f'{v:.6f}' if isinstance(v,float) else str(v).replace('|','/').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(df.columns)+' |','| '+' | '.join(['---']*len(df.columns))+' |']+['| '+' | '.join(map(f,r))+' |' for r in df.itertuples(index=False,name=None)])
inv=pd.read_csv(O/'ADDITIONAL_DATA_INVENTORY.csv').fillna('')
hold=pd.read_csv(O/'HOLD_REASSESSMENT.csv').fillna('')
prof=pd.read_csv(O/'evidence/PUBLIC_PROFILE_INTEGRALS.csv')
cyc=pd.read_csv(O/'evidence/PUBLIC_CYCLING_ENDPOINTS.csv')
digit=pd.read_csv(O/'evidence/CHEN_FIG5G_DIGITIZED.csv')
catalog=pd.read_csv(O/'evidence/SOURCE_CATALOG.csv').fillna('')

# Every actual request is logged, including failed paths and the successful mirror/fallback.
acq=[json.loads(s) for s in (O/'evidence/ACQUISITION_LOG.jsonl').read_text().splitlines()]
queries=[
 ('"s41467-020-17126-3" supplementary source data','Chen primary and data availability','本文/補足の確認経路を探索した','evidence/web1.json'),
 ('"lithium rich" "graphite" "full cell" N/P formation voltage','near full-cell data','Tu2020等の一次研究を候補化した','evidence/web2.json'),
 ('"s41467-020-17126-3" "supplementary"','Chen SI','publisher実リンクから19頁SIを取得した','sources/CHEN_SI_CONFIRMED.pdf'),
 ('"Highly reversible oxygen redox" PMC','repository mirror','PMC7343805を同定し本文と添付案内を確認した','sources/CHEN_PMC.html'),
 ('"surface polyanions" "Source Data"','public source data','対象の独立公開cycle原系列を同定できなかった。非存在の証明ではない','evidence/web1.json'),
 ('"sulfur" "Li1.2Ni0.2Mn0.6O2" "graphite"','target sulfur/full cell','同一LP/Sの黒鉛対照全電池データを同定できなかった','evidence/web1.json'),
 ('"17126" "MOESM"','supplement discovery','仮CDNホストはDNS失敗、本文実リンクspringer.comは成功した','evidence/ACQUISITION_LOG.jsonl'),
 ('"Highly reversible oxygen redox in layered compounds" "PMC"','primary mirror','PMC全文を取得した','sources/CHEN_PMC.html'),
 ('"BatPaC v5.0" download Excel model','public design software','manualは取得。v5xlsm実体は本調査で未取得である','evidence/web2.json'),
 ('"lithium-rich" "graphite" "N/P" full cells pouch voltage energy density','related graphite full cells','2026年2報とSource Dataを確認した','sources/LMR2026_DATA.xlsx; sources/RATE2026_DATA.xlsx'),
 ('"sulfur-treated" "graphite" cathode full cell lithium rich','near sulfur treatment','H-SCLMRは硫酸アンモニウムleachingでありChen蒸着S-200とは別である','sources/RATE2026_FULL.readable.txt'),
 ('"Highly reversible oxygen redox" figshare','public repository','Chen原系列の確定recordを同定できなかった','evidence/web6.json'),
 ('"s41467-020-17126-3" data zenodo','public repository','Chen原系列の確定recordを同定できなかった','evidence/web6.json'),
 ('"henkelmanlab.org" "chen20" supplement','author laboratory','著者本文PDFとpublication indexを取得した。独立cycle原系列は未確認である','sources/CHEN_LAB_PUBS.html'),
 ('"Elucidating the Effect of Iron Doping" full cell 2019 voltage','closest Co-free comparison','KIT原著PDF9頁を取得・確認した','sources/FE_DOPED_FULL.pdf'),
 ('"BatPaC 5.0 2022-07-22.xlsm" download','version-specific workbook','原manualのversionを確認したが実行可能xlsmは未取得である','evidence/web7.json'),
 ('site:static.nhtsa.gov "BatPaC" "xlsm"','government distribution','NHTSA公開manualを確認した。xlsmダウンロードURLを確定できなかった','sources/BATPAC_NHTSA.pdf'),
 ('"Understanding Boron Chemistry as the Surface Modification and Electrolyte Additive"','high-loading graphite full cell','出版社Experimental節までwebで確認した。大学PDFは404である','evidence/web10.json'),
 ('"s41467-020-17126-3" "initial" capacity retention','retention denominator','分母cycleの明示根拠を新規には取得できなかった','evidence/web9.json'),
 ('"S-200" "graphite" "polyanions"','exact target full-cell match','同じ材料と条件の黒鉛全電池実測を同定できなかった','evidence/web9.json'),
 ('site:zenodo.org "Highly reversible oxygen redox in layered compounds"','repository-indexed exact title','独立原系列recordの確定なし。検索インデックス範囲の結果である','evidence/web9.json'),
 ('site:figshare.com "Highly reversible oxygen redox in layered compounds"','repository-indexed exact title','独立原系列recordの確定なし。検索インデックス範囲の結果である','evidence/web9.json'),
]
search=[]
for i,(q,scope,result,ev) in enumerate(queries):search.append(dict(search_id=f'Q{i+1:02d}',date='2026-11-05',transport='web search',query_or_url=q,scope=scope,outcome=result,evidence=ev,limitations='一次資料の候補探索。検索結果/二次資料の要約値を採用しない'))
for i,a in enumerate(acq):
    search.append(dict(search_id=f'A{i+1:02d}',date=a['access_utc'],transport='requests GET',query_or_url=a['url'],scope=a['source_id'],
                       outcome=f"HTTP{a.get('status_code','ERROR')}; PDF={a.get('valid_pdf',False)}; {a.get('error','')}",evidence=a.get('local_path','evidence/ACQUISITION_LOG.jsonl'),
                       limitations='取得失敗本文は証拠として数値採用しない。xlsxのcanonical copyは同一bytesで別拡張子保存'))
searchdf=out('LITERATURE_SEARCH_LOG.csv',search)

checks=[]
def check(name,ok,detail=''):
    checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=str(detail)))
    if not ok:
        out('evidence/FINAL_CHECKS.csv',checks);raise AssertionError((name,detail))
for r in pd.read_csv(O/'evidence/PROTECTED_BEFORE.csv').itertuples():check('保全 '+r.path,sha(r.path)==r.sha256)
allowed={'DIRECT','TRANSFERABLE','SENSITIVITY_ONLY','NOT_APPLICABLE','UNRESOLVED'}
check('採用分類は指定5種類',set(inv.adoption)==allowed)
check('inventory id一意',not inv.data_id.duplicated().any())
check('必須台帳項目',inv[['data_name','unit','source','url','page_figure_table','experiment_conditions','chemistry','cell_format','measurement_rate','measurement_time','model_applicability','uncertainty','adoption_reason','prohibited_use']].ne('').all().all())
check('近縁値をDIRECTへ昇格していない',not ((inv.material_relation=='近縁材料')&(inv.adoption=='DIRECT')).any())
check('BatPaCモデル値をDIRECT実測扱いしない',not ((inv.source_id=='B5')&(inv.adoption=='DIRECT')).any())
check('対象主要HOLDは11項目',sum(hold.scope=='PRIMARY_TARGET_HOLD')==11)
check('対象主要HOLDの全面解除なし',not (hold[hold.scope=='PRIMARY_TARGET_HOLD'].status=='RESOLVED').any())
for s in catalog.itertuples():
    for f in s.local_evidence.split(';'):check('資料実在 '+f.strip(),(O/f.strip()).is_file())
for a in acq:
    if a.get('local_path'):
        check('取得物hash '+a['source_id'],sha(O/a['local_path'])==a['sha256'])
for source in ['LMR2026_DATA','RATE2026_DATA']:
    check('公開xlsxは取得元と同一bytes '+source,sha(O/'sources'/(source+'.xlsx'))==next(a['sha256'] for a in acq if a['source_id']==source))
for r in pd.read_csv(O/'evidence/EXTRACTION_AUDIT.csv').itertuples():check('公開Q-V '+r.check,r.status=='PASS',r.error)
for material,reported in [('LP',121),('S-200',194)]:
    got=float(digit[(digit.material==material)&(digit.cycle==100)].capacity_mAh_g_approx.iloc[0]);check('図読取100cycle anchor '+material,abs(got-reported)<=5,dict(read=got,report=reported))
ce=pd.read_csv(O/'evidence/CE_CROSSCHECK.csv')
check('formationと通常CEを異条件と記録',(ce.status=='NOT_COMPARABLE_DIFFERENT_RATE_AND_CYCLE_BASIS').all())
counts={}
for file,expected in [('INTERACTION_RESULTS.csv',527),('BOUNDARY_SURFACES.csv',2575),('DC_INTERACTION_RESULTS.csv',402040)]:
    with (OLD/file).open() as f:n=sum(1 for _ in f)-1
    counts[file]=n;check('旧行数 '+file,n==expected,n)
for file in ['NUMERICAL_AUDIT.csv','INDEPENDENT_AUDIT.csv']:
    audit=pd.read_csv(OLD/'evidence'/file);check('既存監査 '+file,(audit.status=='PASS').all(),len(audit))
out('evidence/FINAL_CHECKS.csv',checks)

baseline=pd.read_csv(OLD/'evidence/REPRODUCTION.csv')
baseline['recomputed']=baseline.recomputed.map(lambda v:f'{v:.9f}')
data_preview=inv[inv.data_id.isin(['C04','C11','C12','C14','C19','F01','F04','F06','T04','BO01','BO03','BO05','BO06','B01','B02'])][['data_id','data_name','value','unit','adoption','page_figure_table']]
profile_preview=prof[['label','discharge_capacity_mAh_g','mean_discharge_voltage_V','discharge_specific_energy_Wh_kg_positive_active']].copy()
profile_preview.columns=['公開系列','Q_mAh_g正極','平均V_V全電池','比E_Wh_kg正極']
primaryhold=hold[hold.scope=='PRIMARY_TARGET_HOLD']
hold_preview=primaryhold[['hold_id','hold_name','status','remaining_hold']]
counts_adopt=inv.adoption.value_counts().to_dict()
pdfrows=[a for a in acq if a.get('valid_pdf') and a.get('status_code')==200]
newfacts='''対象LP半電池の0.5C初回充電238mAh/g・FCE65.2%と、1C100cycleの121/194mAh/g等は既存値の再確認である。今回の新しい実験成果ではない。追加確認としてS-200の0.5C初回FCE82.0%の印字、SI19頁の内容、エネルギー保持率、近縁全電池の公開Q-V/formation/高担持条件、BatPaCの360参照元と非活物質積算を台帳化した。'''
report=f'''# 因果経路2：追加データ取得・科学的採用判定・最終検証計画

## 判定

今回の資料取得・採用判定・実行計画の確定は完了である。研究上の利用判定は**CONDITIONAL GO**である。11項目の対象科学的HOLDを全面解除できる直接対応データは取得できていない。補足資料未取得、S-200初回FCE未確認、黒鉛360の参照出典不明という3件の資料取得・出典対応上のHOLDは解消した。資料取得の解決と対象実用入力の採用は別である。

Level1は既存の数理モデル内で完了である。Level2は資料・採用監査と公開Q-Vの確認までの部分到達であり、今回の調査だけで性能検証完了とはしない。次タスクの少数の公開近縁対照ケース接続・独立検算・主張監査を含む限定Level2を提出前必須とする。Level3のLP/S実用全電池・実車実証は未達であり、本研究目的に対する提出前必須条件とはしない。対象LP/S完成packの予測値を主張する場合は、この限定Level2では不十分である。

## 既存成果の保全

既存の最終採用報告、追加計算報告、README、入力台帳、計算コード、元論文キャッシュ、既存監査を確認した。旧結果を変更せず、以下を固定参照として継承した。

{table(baseline,['item','recomputed','unit','status'])}

保存軌跡当たりの基準DC差は4.510～30.524Wh、DC削減率は0.412579～0.413590%である。質量条件527、境界点2575、DC評価402040行の件数を確認した。走行軌跡460本、Crr上下、条件群は独立標本ではない。今回、パック/車両質量やDCの大規模再計算、QAOA/SUMO再実行、論文原本修正は行っていない。公開数値の読取・放電枝積分・保持率の検算だけを追加した。

## 実際に取得・確認した資料

保存したPDFは{len(pdfrows)}件であり、Chen本文12頁、Chen SI19頁、Fe置換原著9頁、BatPaC manual146頁、2026年近縁2報の本文15/12頁とSI37/34頁である。近縁2報は2026-08-04および2026-07-01公開であり、本調査日2026-11-05以前の資料である。出版社のSource Data xlsx2件も取得し、sheet名・cell範囲・入力単位を保存した。TU2020とPark2024は出版社のweb本文/Experimental節まで確認したが、直接PDF/SI保存には403/404の制限が残った。失敗応答も成功資料と区別して保存した。

全{len(inv)}項目のデータ/未取得項目をADDITIONAL_DATA_INVENTORY.csvに記録した。分類件数は{counts_adopt}である。DIRECTは「その資料における対象半電池条件へ直接対応」の意味を含み、LP/S黒鉛全電池への直接適用を意味しない。モデル適用範囲と禁止用途を別列にした。

{newfacts}

主な抽出値は以下のとおりである。図中に印刷された数値と、曲線から読み取った概数は区別した。

{table(data_preview)}

## Chen2020：確認できた事項と未取得事項

一次本文は[著者公開PDF](https://henkelmanlab.org/pubs/chen20_3411.pdf)、[出版社本文](https://www.nature.com/articles/s41467-020-17126-3)、[SI実リンク](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-020-17126-3/MediaObjects/41467_2020_17126_MOESM1_ESM.pdf)である。ローカル保存先はsources/CHEN_AUTHOR.pdf、CHEN_PUBLISHER.html、CHEN_SI_CONFIRMED.pdfである。

1. **保持率分母**：本文p7はLP70.4%/121mAh/g、S-20099.0%/194mAh/gを報告するが、分母のcycle番号を明記していない。SI全19頁も確認したが、保持率分母・activation/formation電流手順を特定できない。したがって121/.704=171.875、194/.990≈195.959596は逆算参照のままであり、初回放電容量へ昇格できない。
2. **初回容量・レート**：本文p6とFig5b/c p8は0.5C、Fig5e–hは1Cである。LPの238×.652=155.176mAh/gは丸め報告値からの算術値であり、独立した放電生データ値ではない。S-200の初回FCEはFig5bの青色印字82.0%である。FCEから容量単独を決めるには、対応する初回充電容量も必要である。S-200の初回放電の確定数値は未取得であり、Fig5bの重なる第1/第2サイクルを厳密に割り当てたQ-V系列としては採用しない。
3. **サイクル別容量**：Fig5gの埋込みラスタを抽出し、選択cycleの概数を読み取った。LPはcycle5/10/20/40/60/80/100付近で約156/166/171/171/162/142/121mAh/g、S-200はcycle5/10/40/60/80/100付近で約148/173/196/192/192/193mAh/gである。早期に容量が増える図形は確認できるが、それだけでactivationの操作定義や保持率分母cycleを確定しない。S-20020cycleは線の重なりで読取を保留した。全100cycleの原系列を取得したわけではない。
4. **読取方法・精度**：PDFp8の埋込み画像source-17.pngを用い、座標x=10+534n/100、q=200(432−y)/(432−40)で較正し、5pixel幅の色mask中央値を読む。100cycleは枠を避け99–100付近を読む。読取分解能は約5mAh/gであり、誤差上限保証や信頼区間ではない。100cycleの本文121/194との対応を確認した。初回cycle値や保持率分母の同定には使わない。evidence/CHEN_FIG5G_DIGITIZED.csvとscripts/extract_public_data.pyに再現方法を保存した。
5. **電圧・比エネルギー**：Fig5e/fは正規化容量に対する放電曲線であり、絶対的な平均全電池電圧は報告されていない。本文p7/Fig5hでは100cycle後の比エネルギー保持率59.5%→96.0%を確認した。絶対Wh/kgや黒鉛全電池平均Vをこの率から作らない。
6. **幾何・液量**：Methods p11の活物質1–2mg/cm²、配合75:15:10、Li対極CR2025、室温、2.0–4.8V、CAPCHEM 1M LiPF6 EC/DMC1:1、Celgard2400を再確認した。試料別の対応担持、混合密度、空隙、実厚、実注液量は未取得である。SI FigS13 p14の100cycle XRDは0.5Cであり、Fig5gの1C履歴と同一視しない。
7. **処理量とBOM**：Methods p10–11ではLP40mgに対し硫黄供給50/200/500mgを別るつぼへ置き、250℃20分処理後に250℃20分の真空処理で余剰硫黄を除去する。S-200は200℃ではなく供給硫黄200mgの条件名である。供給量を残留表面種の質量として完成セルへ足してはならない。実残留S/SOxと追加部材差は依然未確定である。
8. **公開生データ**：出版社Data availabilityとPMCは合理的要求による著者提供を案内している。著者研究室一覧、出版社/PMCの添付、Zenodo/FigshareのDOI/タイトル検索を確認した範囲で独立cycle原系列recordを同定できなかった。世界の公開データに存在しないと断定したものではない。著者への連絡は今回実行していない。

SIでは構造/表面状態を示すSupplementary Figs1–17と文献を確認した。補足を取得できたこと自体で、そこに未記載のformation定義や完成セル物性を補完しない。

## 黒鉛全電池：同一・近縁・別材料の判定

**同一LP/S材料・同一条件の黒鉛全電池対は本調査で確認できなかった。** 以下は近縁材料であり、LP/Sの実測値へ改名しない。

- [Wu2019原著](https://publikationen.bibliothek.kit.edu/1000098904/50680585)、DOI10.1002/aenm.201902445、p7–8/Fig10：Fe置換Li1.2Mn0.585Ni0.185Fe0.03O2/graphiteで初回213mAh/g正極、200cycle1C容量保持80.4%を報告する。361Wh/kgは正負極活物質合計質量基準であり、完成セルやパック基準ではない。MethodsのN/P≈1.05は**質量比**であり、容量比1.05ではない。半電池232mAh/gとの213/232をT08のuへ採用しない。
- [Tu2020出版社本文](https://onlinelibrary.wiley.com/doi/full/10.1002/eem2.12034)、Methods4.1/4.2：Co含有Li1.2Mn0.55Ni0.15Co0.1O2/graphite、正極3.9/負極2.2mg/cm²、設計容量比N/P1.3を確認した。初期3cycle0.05C、以後0.5C、2.0–4.6Vである。STD/PESの初回200/240mAh/g・効率63/73%は電解液条件の影響を示す近縁資料である。
- [Park2024出版社本文](https://advanced.onlinelibrary.wiley.com/doi/10.1002/aenm.202401968)、Experimental/Conclusion：別組成LRLOのLBO被覆とLiBOB添加剤の全電池で、正極約14mg/cm²・3mAh/cm²、coin N/P≈1.1、黒鉛active94%、coin50µL/pouch500µLの注液を確認した。400cycleC/3で82%保持である。硫黄処理でもLP/Sでもなく、セル形式を跨いで50/500µLを移用しない。
- [Song2026出版社本文](https://www.nature.com/articles/s41467-026-76366-x)、Methods/Results/SI FigS7–S8、Source Data：Li1.14Ni0.312Mn0.544Co0.004O2/graphiteの1Ah級および公称40.9Ah pouchである。N/P1.07とformation/通常窓の明示を確認した。ResultsのN/P定義45℃とMethods35℃、1Ahと1.5Ahの表記は条件対応を一括推定せず残す。配合・液量・圧力等は製造者非公開である。663Wh/kg、883cycle92.2%は正極活物質質量基準であり、完成セル比エネルギーではない。
- [Zhang2026出版社本文](https://www.nature.com/articles/s41467-026-75101-w)、Methods/Results Fig4/SI FigS17、Source Data：Co含有単結晶LMRの硫酸アンモニウムleaching/300℃処理であり、Chenの硫黄蒸着とは別である。SCLMRはsingle-crystallineの名称で、S-200の意味ではない。黒鉛全電池11mg/cm²・N/P≈1.2、formation0.1C×2、通常0.2Ccharge/0.5Cdischargeを確認した。9mg/cm²・active90%の厚電極278mAh/g/100cycle90.5%はLi金属対極条件である。pouch6µL/mgもLi金属セルであり、黒鉛pouchの実注液量へ置き換えない。

## 公開Q-V・サイクル系列の実抽出

以下は近縁材料の公開Source Dataからの派生値である。平均電圧は同じ放電枝で∫VdQ/Qspanとして計算し、cutoff電圧の中点を使っていない。QはmAh/g正極活物質、比EはWh/kg正極活物質である。対象LP/Sの電圧・容量を確定する値ではない。

{table(profile_preview)}

LMR2026は[公開xlsx](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-76366-x/MediaObjects/41467_2026_76366_MOESM3_ESM.xlsx)のSupplementary Fig.8 A:B/D:E/G:H、SI PDFp10の25℃放電曲線である。RATE2026は[公開xlsx](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-75101-w/MediaObjects/41467_2026_75101_MOESM5_ESM.xlsx)のFigure S17 A:B/C:D/E:F/G:H/I:J/K:L、SI PDFp18の0.1C formation枝である。容量リセットでcharge/dischargeを分け、再標本化や欠測補間をせず台形積分した。source rowと切り出した放電系列をevidence/PUBLIC_PROFILE_INTEGRALS.csv、各*_discharge.csvに保存した。

RATE2026のS17dは通常サイクル0.2C/0.5CのCEであり、S17a–cの0.1C formationのCEとは比較基準が異なる。差を原論文の誤りや全電池利用率として扱わず、evidence/CE_CROSSCHECK.csvでNOT_COMPARABLEと記録した。公開Q-Vの一部で上限が4.8V付近になる等の枝端点とMethodsの4.75Vの対応は、入力条件束を採用する前に確認すべき事項である。これらを隠してLP/S入力へ移用しない。

{table(cyc,['source_id','material','cycle_first','capacity_first','cycle_last','capacity_last','retention_percent','cells'])}

上表のRATE2026は通常cyclingの容量、LMR2026は正極活物質基準の比エネルギーである。LMRの663.35097→611.8651Wh/kgからの92.2385%は本文の丸め92.2%と整合する。RATEのcolumn順はH-SCLMR/PCLMR/SCLMRであり、図の色順や材料名から推測せずsheet headerを確認した。Source Dataは図を支える公開数値であり、装置の未加工計測ログがすべて公開されたという意味ではない。測定誤差・反復分布は付与されていない。

近縁全電池で3.53–3.65V程度の平均Vを算定できても、既存3.193155684V境界との大小だけで対象Sの優位性を立証できない。境界は旧q/u/負極/BOM条件に依存し、新たなqとVは同じ材料・同じ履歴として共同適格化する必要がある。FCEや異レート容量比をuにしない。

## BatPaC v5.0：T09のNULLを制約する設計資料

一次資料は[ANL/CSE-22/1 manual](https://publications.anl.gov/anlpubs/2022/07/176234.pdf)である。直接ダウンロードはHTTP403であり、同manualを[NHTSA政府公開ミラー](https://static.nhtsa.gov/nhtsa/downloads/CAFE/2023-NPRM-LD-2b3-2027-2035/Argonne-Databases/Documentation/BatPaC%20v5%20Manual-July%202022.pdf)から保存した。v5.0/2022-07-22の記述を確認したが、xlsm実体は未取得であり、Excel反復計算やmacroを実行したとは主張しない。

|部材|取得した数値・方法|所在・採用制限|
|---|---|---|
|負極参照|360mAh/g、formation後N/P1.10、98:0:2、activeρ2.24/binderρ1.10g/cm³|Fig3.14 PDFp46。NMC811/Gの設計既定値でありLP/S実測ではない|
|外装|stiff-pouchの表面/折返し/封止部の幾何積算。対象laminate厚さ/層構成は未取得|Secs2.2/5.2.5。ρ×体積で条件付き算定する。NULLを0へ置換しない|
|電極tabs/端子|正/負端子厚1.2/0.8mm、外部8mm/封止5mm、外部幅40/50mmをWposで分岐|Eq5.17 PDFp72、Sec5.2.5 PDFp80。端子の電気的有効長×1.2は物理質量係数ではない|
|箔余白/最外層|負極正極比の寸法余剰は幅2mm・長さ2mm、separator長さ余剰4mm、箔tab長さ1.2×cell厚、最外側片面負極箔を補正|Sec5.2.5 PDFp77–80。両面共有面積と整数layer数を要する|
|セル間接続|Cu接続厚1mm、長さ/個数はcell/module構成へ依存|Eq5.20/5.21/5.41。電流発熱条件と実寸を要する|
|モジュール構造|Al熱伝導材0.4mm、steel壁0.3mm、polymer接続panel2mm、管理機器46g/module、gas release5g/module|Sec5.3 PDFp83。寸法・module数を指定して積算する|
|pack構造/保護|拘束plate2mm、coolantchannel5mm/壁0.3mm、内Al1mm、底外steel1mm、断熱10mm、外Alはenergyによる段階値|Secs5.4/5.5.3 PDFp84–88。20kWh境界の分岐はworkbookで確認する|
|BMS|BMU PCB40g＋ASIC当たり20g、BMU外装10%、BMS外装1.3倍。maincontactor750g/unit等|Secs7.2/7.6、Table7.2 PDFp103–106。series/ASIC数・module数・電圧依存を要する|
|BMS内重複防止|module electronicsは46g/module側に含む。interface wiringはBMU等へlumped|Secs7.4–7.6。全項目を別々に加えて二重計上してはならない|
|冷却/熱管理|冷却液ρ1.07g/cm³、500/1000/3000/6000W級に2/3/5/7kgの追加機器参照|Table8.2 PDFp112、Eq8.12 PDFp113。必要熱負荷を先に求める|
|pack対battery system|pack内冷却構造と冷却液はpack、外部pump/chiller/valving質量はsystem|Sec8.6 Table8.4 PDFp117–118。車両交換範囲に合わせる|

これらは既存T09のNULLを条件付きで制約するための設計データである。幾何・材質・個数が揃えば外装/端子/余白/接続/構造の積算則はTRANSFERABLEとなるが、既定の寸法・部品質量は対象実測でなくSENSITIVITY_ONLYである。T08のcell_other19kg/pack_other15kgへT09明示部材を足すと二重計上になるため、同一会計範囲へ分解して比較する必要がある。

冷却機器2–7kgは各設計の絶対質量参照であり、S−LPの差2–7kgではない。両材料が同じcoolerを必要とすれば差は相殺し、異なる場合だけ追加差が生じる。電流/熱負荷を調べず既存5.448kg境界へ機械的に差し引かない。冷却部材質量を調べても、既存DC核へ補機電力やHVACを追加しない。製造notchingの約8%scrapも残留箔余白ではない。

T09のKを既知小計、Uを未知部材とすれば、D=(K_LP−K_S)−(U_S−U_LP)である。この式と既存境界を維持する。今回Uをゼロ補完せず、完成packの絶対質量・絶対車両質量・絶対DCを新たに算出していない。

## HOLD再判定

{table(hold_preview)}

主要11項目ではRESOLVED0、PARTIALLY_RESOLVED4、UNRESOLVED6、RESEARCH_LIMITATION1である。PARTIALLY_RESOLVEDは近縁資料や設計則の取得で一部の証拠欠落が埋まった意味であり、target_practical_adoption列はHOLDを維持する。資料取得/出典対応sub-HOLD S01/S02/S03のみRESOLVEDである。解除根拠はSI19頁、S-200FCE82.0% Fig5b p8、黒鉛360/N/P1.10 Fig3.14 p46である。

## 更新可能な計算と実測を必要とする計算

取得資料だけでできるのは、公開近縁Q-VのE/Q、公開cycle保持率、同材料内の条件付き比較、BatPaCのgeometry/BMS/熱部材の記号的制約、未知差δUを残した相殺式、既存527条件/2575境界/402040DCの再利用判定である。今回のevidence表はこれらのうち読取/原系列派生量を実行した結果である。

LP/S対象のq/V/u、formation後N/P/負極容量、高担持輸送特性、密度/空隙、実注液、残留S/SOx、完成BOM、出力/寿命/安全と実車DCは新しい対象測定または未公開原系列を必要とする。近縁データから対象値を確定する再計算はできない。

RECALCULATION_PLAN.csvには要求された10項目すべてについて必要/取得/不足入力、使用code、条件、比較、指標、完了基準を記録した。既存codeは読取り専用参照であり、新しいadapterは次run02の予定であって実装済みとはしていない。平均Vは容量と同一放電枝、q_effを直接使う場合のu=1は会計定義であって実験利用率100%ではないことを明示する。

## 作業順序と提出前必須事項

順序は、Step0既存保全→Step1台帳採用→Step2Chen原系列の追加照会→Step3同条件入力束→Step4BOM/交換範囲→Step5少数質量・解析境界検算→必要な場合だけStep6新規質量DC→Step7主張監査である。Step2の外部応答待ちに依存しない近縁ケース整理とBOM仕様化は先行できる。Step8対象セル、Step9実車はLevel3の将来検証である。各Stepの目的・内容・入力・モデル・成果物・完了/移行条件・HOLD対応・作業量はEXECUTION_ROADMAP.mdに定めた。

提出前は、Level1の旧監査確認、限定Level2の一次資料/採用/HOLD整合、少なくとも一つの独立した公開近縁対照ケースの共同入力接続と少数代表点検算、最終claim監査を必須とする。新規大規模gridや全DC再実行は必須としない。新規DCを主張する場合だけ、重複しない確定質量を凍結核へ渡す。近縁referenceケースは対象LP/Sの更新例ではなく、モデル構造と適用条件を検証する独立事例として扱う。

Level3がなくても、部材会計の可視化、容量/電圧/利用率/追加材の成立・消失境界、T08/T09の比較可能条件、保存軌跡上の材料非依存の質量→DC伝達、実証が必要な入力の特定は学術的貢献として成立する。量子計算機で材料改善を実現した、対象実車で消費を削減した、対象完成packの性能を予測したという主張はしない。

## 次にCodexへ指示する作業

「本runの採用台帳・HOLDを正本とし、まずRATE2026またはLMR2026の同条件公開Q-Vから、対象LP/Sと分離した一つの近縁対照ケースを設計せよ。formationと通常サイクル、C-rate、q/V/配合/N/Pの条件対応を監査し、未確定量は記号のまま残せ。BatPaC v5の架構・pack/system質量範囲・BMS重複防止を仕様化し、既存527条件を照合したうえで少数代表点の質量・解析境界を検算せよ。T09の未知Uをゼロにせず、絶対質量未確定なら絶対DCは算出しない。著者原系列の照会文は下書きまでとし、送信は別途指示に従う。大規模DC再評価と論文統合は採用ゲート完了後の別タスクとせよ。」

## 最終監査

既存・原データ・論文等644ファイルを事前hashと照合し不変を確認した。台帳の指定5分類、近縁値のDIRECT昇格なし、モデル既定値の実測扱いなし、11主要HOLDの維持、取得物hash、公開xlsx同一性、放電枝積分、図読取端点、formation/通常cycle区別、旧件数と旧監査を確認した。evidence/FINAL_CHECKS.csvは{len(checks)}件PASSである。取得不能・条件対応差・対象実測不足はFINAL_AUDIT.mdに残した。

新規の独立測定、装置データの誤差モデル、信頼区間、発生確率は作っていない。Source Data数値積分の算術一致を対象実用入力の採用根拠へ昇格していない。今回の達成は追加証拠と判定・作業順序の確定であり、残存HOLDを解消した性能実証ではない。
'''
(O/'FINAL_REPORT_JA.md').write_text(report)

audit=f'''# 最終監査

調査・採用台帳・HOLD再判定・実行計画の作成は完了である。研究利用はCONDITIONAL GO、対象実用LP/S全電池/完成pack/実車性能はHOLDである。

|監査項目|判定|証拠・残る限界|
|---|---|---|
|既存結果・論文の保全|PASS|644ファイルSHA256一致。旧527/2575/402040行を確認した|
|原著本文・SI・公開数値の実確認|PASS|PDF8件、近縁Source Data xlsx2件、出版社/著者HTML・web記録。取得失敗は別記録である|
|数字・単位・条件・出典・適用範囲|PASS|157項目のinventory。未取得値は空欄/UNRESOLVEDである|
|対象/近縁/別化学系の区別|PASS|近縁の数値を対象DIRECTとしない。ChenDIRECTは半電池条件限定である|
|初回/formation後/通常cycle/C-rate|PASS|S17a–cとdを異条件と記録した。Chen0.5Cと1Cを区別した|
|容量/平均V/比エネルギーの分母|PASS|同じ放電枝E/Q。361Wh/kgは両活物質、663Wh/kgは正極活物質である|
|T09未知部材とpack/system範囲|PASS|U/δUを保持。実外装・残留S・冷却/電流/架構が未確定である|
|主要HOLD再判定|PASS|11項目:全面解除0、一部4、未解決6、研究限界1である|
|出典取得sub-HOLD解除|PASS|SI19頁、S-200FCE82%、黒鉛360の参照を特定した。実用採用の解除ではない|
|数値抽出監査|PASS|台形積分と独立sum一致、Fig5g100cycleを印字121/194へ照合した|
|Level判定|CONDITIONAL|Level1は既存範囲で完了、Level2は部分到達、Level3は未達である|
|次の作業の実行可能性|PASS|10再計算項目と10Stepの入力/不足/コード/完了条件を記録した|
|大規模再計算・論文変更なし|PASS|今回の追加計算は文献数値読取・積分・検算だけである|
|量子帰属/独立標本/確率捏造なし|PASS|材料改良を量子計算機実証に帰属させず、依存系列に検定やCIを付けない|

## 未解決事項

Chen保持率の分母cycleとactivation/formation、S-200の確定した初回放電系列、LP/S黒鉛全電池のq/V/uと高担持物性、実液量、混合密度、残留S、完成BOM、実用出力/寿命/安全、実車DCは未取得または未実証である。BatPaC v5xlsm実体は未取得であり、Excel計算を実行したとは主張しない。BMS/冷却の設計値を対象実測BOMへ代入していない。

LMR2026では本文/MethodsのN/P定義温度45/35℃、1Ah/1.5Ahの対応を未解決として残す。RATE2026の公開formation枝端点とMethods上限の対応も採用前に確認する。formationと通常cyclingのCEの差を同条件の矛盾と誤認しない。著者原系列を推測して埋めず、資料の非存在を断定しない。

## 数値・保全検査

evidence/FINAL_CHECKS.csvの{len(checks)}項目はすべてPASSである。これは文献の完全性や実物性能の合格を意味しない。公開figure source dataの積分は再標本化/補間なしで行った。図読取は概数であり測定値ではなく、約5mAh/gの読取分解能に確率的意味はない。旧DC核・車両質量置換は変更していない。
'''
(O/'FINAL_AUDIT.md').write_text(audit)

(O/'README.md').write_text('''# 因果経路2追加データレビュー

入口はFINAL_REPORT_JA.mdである。数値採用はADDITIONAL_DATA_INVENTORY.csv、出典はSOURCE_EVIDENCE_MATRIX.csv、再判定はHOLD_REASSESSMENT.csv、計算設計はRECALCULATION_PLAN.csv、順序はEXECUTION_ROADMAP.md、完了条件はCOMPLETION_CRITERIA.md、監査はFINAL_AUDIT.mdである。

sources/は取得した一次資料・補足・Source Dataである。403/404等のHTML応答も失敗証拠として保存し、文献本文の数値根拠として採用していない。web記録はevidence/web*.jsonである。xlsxは初回取得時に誤拡張子.htmlで保存された同一bytesも残しており、canonicalな.xlsxコピーとのhash一致を監査した。

再現する場合はこのrunを新しい独立先に複製し、複製先のscriptsを実行する。既存T08/T09出力と本runの保存値を上書きしない。sourcesからの読取・台帳再生成は以下である。

```bash
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/prepare_evidence.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/extract_public_data.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/build_review.py
PYTHONDONTWRITEBYTECODE=1 .conda/bin/python <new-run>/scripts/finalize_review.py
```

実行場所は元リポジトリrootを想定し、new-runもreview_outputs/<task>/runNNの深さへ置く。旧パス依存は保全manifestに記録した。依存はPython3.11、requests、numpy、pandas、openpyxl、Pillow、およびPopplerのpdftotext/pdftoppm/pdftocairoである。acquire.pyとREQUEST_BATCH*.jsonは実際の取得要求を記録したもので、再ダウンロード時のHTTP成功は保証しない。成功物のSOURCE_SHA256.csvと取得ログが出典追跡の基準である。

公開データ派生量はevidence/PUBLIC_PROFILE_INTEGRALS.csv、元セル範囲と放電枝CSV、cycle端点はPUBLIC_CYCLING_ENDPOINTS.csv、Chen概数はCHEN_FIG5G_DIGITIZED.csvである。これらはLP/S対象パックの新しい予測値ではない。
''')
out('evidence/SOURCE_SHA256.csv',[dict(path=str(p.relative_to(O)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted((O/'sources').iterdir()) if p.is_file()])
(O/'evidence/RUN_SUMMARY.json').write_text(json.dumps(dict(inventory_rows=len(inv),search_log_rows=len(searchdf),primary_HOLD_status=primaryhold.status.value_counts().to_dict(),resolved_source_subholds=3,
    public_profile_integrals=len(prof),digitized_points=len(digit),protected_files=644,audit_checks=len(checks),failures=0,existing_rows=counts,pdf_count=len(pdfrows),large_recalculation=False,thesis_modified=False,
    level1='COMPLETE_WITHIN_EXISTING_MODEL',level2='PARTIAL_PENDING_SMALL_REFERENCE_CASE_AND_FINAL_CLAIM_AUDIT',level3='UNDEMONSTRATED',verdict='CONDITIONAL GO',numpy=np.__version__,pandas=pd.__version__),ensure_ascii=False,indent=2)+'\n')
manifest=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='OUTPUT_SHA256.csv' and '__pycache__' not in str(p):manifest.append(dict(path=str(p.relative_to(O)),sha256=sha(p),bytes=p.stat().st_size))
out('OUTPUT_SHA256.csv',manifest)
print((O/'evidence/RUN_SUMMARY.json').read_text())
