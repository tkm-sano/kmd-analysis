# 因果経路2：追加データ取得・科学的採用判定・最終検証計画

## 判定

今回の資料取得・採用判定・実行計画の確定は完了である。研究上の利用判定は**CONDITIONAL GO**である。11項目の対象科学的HOLDを全面解除できる直接対応データは取得できていない。補足資料未取得、S-200初回FCE未確認、黒鉛360の参照出典不明という3件の資料取得・出典対応上のHOLDは解消した。資料取得の解決と対象実用入力の採用は別である。

Level1は既存の数理モデル内で完了である。Level2は資料・採用監査と公開Q-Vの確認までの部分到達であり、今回の調査だけで性能検証完了とはしない。次タスクの少数の公開近縁対照ケース接続・独立検算・主張監査を含む限定Level2を提出前必須とする。Level3のLP/S実用全電池・実車実証は未達であり、本研究目的に対する提出前必須条件とはしない。対象LP/S完成packの予測値を主張する場合は、この限定Level2では不十分である。

## 既存成果の保全

既存の最終採用報告、追加計算報告、README、入力台帳、計算コード、元論文キャッシュ、既存監査を確認した。旧結果を変更せず、以下を固定参照として継承した。

| item | recomputed | unit | status |
| --- | --- | --- | --- |
| T08 baseline mass saving | 5.448297415 | kg | PASS |
| S additional mass boundary | 5.448297415 | kg | PASS |
| S utilization boundary | 0.877094072 | 1 | PASS |
| S voltage boundary | 3.193155684 | V | PASS |
| CRR_LOWER_BOUND saving | 0.412579010 | % | PASS |
| CRR_UPPER_BOUND saving | 0.413590412 | % | PASS |

保存軌跡当たりの基準DC差は4.510～30.524Wh、DC削減率は0.412579～0.413590%である。質量条件527、境界点2575、DC評価402040行の件数を確認した。走行軌跡460本、Crr上下、条件群は独立標本ではない。今回、パック/車両質量やDCの大規模再計算、QAOA/SUMO再実行、論文原本修正は行っていない。公開数値の読取・放電枝積分・保持率の検算だけを追加した。

## 実際に取得・確認した資料

保存したPDFは8件であり、Chen本文12頁、Chen SI19頁、Fe置換原著9頁、BatPaC manual146頁、2026年近縁2報の本文15/12頁とSI37/34頁である。近縁2報は2026-08-04および2026-07-01公開であり、本調査日2026-11-05以前の資料である。出版社のSource Data xlsx2件も取得し、sheet名・cell範囲・入力単位を保存した。TU2020とPark2024は出版社のweb本文/Experimental節まで確認したが、直接PDF/SI保存には403/404の制限が残った。失敗応答も成功資料と区別して保存した。

全157項目のデータ/未取得項目をADDITIONAL_DATA_INVENTORY.csvに記録した。分類件数は{'SENSITIVITY_ONLY': 121, 'DIRECT': 20, 'UNRESOLVED': 9, 'TRANSFERABLE': 4, 'NOT_APPLICABLE': 3}である。DIRECTは「その資料における対象半電池条件へ直接対応」の意味を含み、LP/S黒鉛全電池への直接適用を意味しない。モデル適用範囲と禁止用途を別列にした。

対象LP半電池の0.5C初回充電238mAh/g・FCE65.2%と、1C100cycleの121/194mAh/g等は既存値の再確認である。今回の新しい実験成果ではない。追加確認としてS-200の0.5C初回FCE82.0%の印字、SI19頁の内容、エネルギー保持率、近縁全電池の公開Q-V/formation/高担持条件、BatPaCの360参照元と非活物質積算を台帳化した。

主な抽出値は以下のとおりである。図中に印刷された数値と、曲線から読み取った概数は区別した。

| data_id | data_name | value | unit | adoption | page_figure_table |
| --- | --- | --- | --- | --- | --- |
| C04 | S-200初回クーロン効率 | 82.0 | % | DIRECT | Fig5b PDFp8 blue label; evidence/CHEN_FIG5.png |
| C11 | LP比エネルギー保持率 | 59.5 | % | DIRECT | PDFp7 Experimental verification; Fig5g/h PDFp8 |
| C12 | S-200比エネルギー保持率 | 96.0 | % | DIRECT | PDFp7 Experimental verification; Fig5g/h PDFp8 |
| C14 | 活物質担持量 | 1.0–2.0 | mg/cm2 face | DIRECT | PDFp11 Electrochemical characterization |
| C19 | S-200の硫黄供給量 | 200 | mg sulfur source | DIRECT | PDFp11 Deposition of sulfur |
| F01 | Fe置換正極/黒鉛の初回放電容量 | 213 | mAh/g positive active | SENSITIVITY_ONLY | PDFp7 Fig10 discussion |
| F04 | 最大比エネルギー | 361 | Wh/kg both active materials | SENSITIVITY_ONLY | PDFp7 text;Fig10 caption PDFp8 |
| F06 | 負極/正極の質量比 | 1.05 | mass ratio | SENSITIVITY_ONLY | PDFp8 Experimental |
| T04 | 設計負極/正極容量比 | 1.3 | capacity ratio | SENSITIVITY_ONLY | Methods4.1 |
| BO01 | 正極担持量 | 14 | mg/cm2 active | SENSITIVITY_ONLY | Experimental Electrode Preparation |
| BO03 | coin設計N/P | 1.1 | capacity ratio approx | SENSITIVITY_ONLY | Experimental Electrode Preparation |
| BO05 | coin電解液量 | 50 | uL/cell | SENSITIVITY_ONLY | Experimental Electrode Preparation |
| BO06 | single-layer pouch電解液量 | 500 | uL/cell | SENSITIVITY_ONLY | Experimental Electrode Preparation |
| B01 | 黒鉛参照比容量 | 360 | mAh/g | SENSITIVITY_ONLY | Fig3.14 PDFp46 printedp27 |
| B02 | formation後参照N/P | 1.1 | capacity ratio | SENSITIVITY_ONLY | Fig3.14 PDFp46 |

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

| 公開系列 | Q_mAh_g正極 | 平均V_V全電池 | 比E_Wh_kg正極 |
| --- | --- | --- | --- |
| LMR2026_protocol_4620 | 247.951520 | 3.536511 | 876.883273 |
| LMR2026_protocol_4330 | 179.596360 | 3.645324 | 654.686908 |
| LMR2026_protocol_4320 | 204.533940 | 3.534076 | 722.838528 |
| RATE2026_H-SCLMR_formation_cycle1 | 270.850000 | 3.501439 | 948.364721 |
| RATE2026_H-SCLMR_formation_cycle2 | 273.650000 | 3.485490 | 953.804345 |
| RATE2026_SCLMR_formation_cycle1 | 260.100000 | 3.625924 | 943.102961 |
| RATE2026_SCLMR_formation_cycle2 | 262.620000 | 3.617713 | 950.083741 |
| RATE2026_PCLMR_formation_cycle1 | 261.110000 | 3.627256 | 947.112924 |
| RATE2026_PCLMR_formation_cycle2 | 264.710000 | 3.609651 | 955.510591 |

LMR2026は[公開xlsx](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-76366-x/MediaObjects/41467_2026_76366_MOESM3_ESM.xlsx)のSupplementary Fig.8 A:B/D:E/G:H、SI PDFp10の25℃放電曲線である。RATE2026は[公開xlsx](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-75101-w/MediaObjects/41467_2026_75101_MOESM5_ESM.xlsx)のFigure S17 A:B/C:D/E:F/G:H/I:J/K:L、SI PDFp18の0.1C formation枝である。容量リセットでcharge/dischargeを分け、再標本化や欠測補間をせず台形積分した。source rowと切り出した放電系列をevidence/PUBLIC_PROFILE_INTEGRALS.csv、各*_discharge.csvに保存した。

RATE2026のS17dは通常サイクル0.2C/0.5CのCEであり、S17a–cの0.1C formationのCEとは比較基準が異なる。差を原論文の誤りや全電池利用率として扱わず、evidence/CE_CROSSCHECK.csvでNOT_COMPARABLEと記録した。公開Q-Vの一部で上限が4.8V付近になる等の枝端点とMethodsの4.75Vの対応は、入力条件束を採用する前に確認すべき事項である。これらを隠してLP/S入力へ移用しない。

| source_id | material | cycle_first | capacity_first | cycle_last | capacity_last | retention_percent | cells |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RATE2026_DATA | H-SCLMR | 1 | 226.220000 | 100 | 214.450000 | 94.797100 | CH4:CI103 |
| RATE2026_DATA | PCLMR | 1 | 223.970000 | 100 | 201.300000 | 89.878109 | CH4:CJ103 |
| RATE2026_DATA | SCLMR | 1 | 193.480000 | 100 | 175.900000 | 90.913790 | CH4:CK103 |
| LMR2026_DATA | Co-lean LMR 40Ah protocol 4.25-2.0V | 1 | 663.350970 | 883 | 611.865100 | 92.238517 | V4:W886 |

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

| hold_id | hold_name | status | remaining_hold |
| --- | --- | --- | --- |
| H01 | Chen逆算容量の初回容量への適用 | UNRESOLVED | 保持率分母cycle・activation/formationと初回1Cの対応は未確定である |
| H02 | LP/S–黒鉛全電池の利用可能容量 | UNRESOLVED | 同じLP/Sの黒鉛全電池対照測定がない |
| H03 | 平均全電池電圧 | PARTIALLY_RESOLVED | LP/S別の平均全電池電圧は未確定である |
| H04 | 容量利用率 | UNRESOLVED | T08参照qに対応する同条件全電池q/uがない |
| H05 | 正極・負極の混合密度 | UNRESOLVED | LP/S実配合の固相密度、calendering後bulk密度と空隙率はない |
| H06 | 高担持条件での容量維持 | PARTIALLY_RESOLVED | LP/Sの10/20mg/cm2探索点での輸送・出力・容量適格性は未確定である |
| H07 | 実際の電解液量 | UNRESOLVED | 対象LP/Sの実投入量・飽和度・余剰液はない |
| H08 | 外装・タブ・構造部材 | PARTIALLY_RESOLVED | 対象LP/Sセル形式・材質・寸法・modules・電流・熱負荷がない |
| H09 | T09完成パック質量 | UNRESOLVED | K+UのU絶対量と差が未確定である |
| H10 | 実車の走行時DC電力量 | RESEARCH_LIMITATION | 回生/補機/勾配/実積載等を含む実車実証は本研究の検証範囲外である |
| H11 | 出力・寿命・安全性 | PARTIALLY_RESOLVED | LP/S黒鉛完成セルの出力・長期寿命・熱/濫用安全は未実証である |

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

既存・原データ・論文等644ファイルを事前hashと照合し不変を確認した。台帳の指定5分類、近縁値のDIRECT昇格なし、モデル既定値の実測扱いなし、11主要HOLDの維持、取得物hash、公開xlsx同一性、放電枝積分、図読取端点、formation/通常cycle区別、旧件数と旧監査を確認した。evidence/FINAL_CHECKS.csvは717件PASSである。取得不能・条件対応差・対象実測不足はFINAL_AUDIT.mdに残した。

新規の独立測定、装置データの誤差モデル、信頼区間、発生確率は作っていない。Source Data数値積分の算術一致を対象実用入力の採用根拠へ昇格していない。今回の達成は追加証拠と判定・作業順序の確定であり、残存HOLDを解消した性能実証ではない。
