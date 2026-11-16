# 学術監査の一次資料・証拠台帳

調査日は2026-11-13である。検索要約だけを根拠に重要な結論を確定していない。以下の「本文確認」は記載した節の原文を閲覧した意味であり、論文全体の逐語的検証や結果の再現実験を意味しない。既存Web保存物、前回監査、今回のオンライン原文を区別する。研究への適用は監査者の推論として明記する。

## 学術・方法論の資料

|ID|論文・資料名、著者、発表年|DOI・原資料|今回の参照箇所・確認範囲|研究に用いる内容／用いない内容|
|---|---|---|---|---|
|S1|Handbook on Constructing Composite Indicators: Methodology and User Guide、OECD/European Union/EC-JRC、2008|[DOI](https://doi.org/10.1787/9789264043466-en)、[公式全文PDF](https://www.oecd.org/content/dam/oecd/en/publications/reports/2008/08/handbook-on-constructing-composite-indicators-methodology-and-user-guide_g1gh9301/9789264043466-en.pdf)|§1.5 正規化（印刷p.27以降）、§1.6 重み/集約（p.31以降）、§1.7、Step5。公式原文確認である|正規化・等重み・補償性を説明する根拠である。本研究の1/3や基準数値を事業者選好として実証するものではない|
|S2|Best Practices for Comparing Optimization Algorithms、Vahid Beiranvand, Warren Hare, Yves Lucet、2017、Optimization and Engineering 18:815–848|[DOI](https://doi.org/10.1007/s11081-017-9366-1)、[著者原稿](https://arxiv.org/pdf/1709.08242)|§3–4、とくに§4.1とTable3（原稿PDF p.8–9）。原文確認である|解品質・成功・資源/時間を分ける根拠である。特定VRPや4CPU設定を最良と認定する根拠ではない|
|S3|Solving Capacitated Vehicle Routing Problem with Quantum Alternating Operator Ansatz and Column Generation、Wei-hao Huang, Hiromichi Matsuyama, Yu Yamashiro、2025|[arXiv v1](https://arxiv.org/html/2503.17051v1)|§III-B列生成、§III-C ALiM/XY、式(20)、§IVの原文を確認した|Dの設計由来である。4〜6顧客CVRP、COBYLA/1000shots等の実験であり、S1〜S3・積込W・総合J・実機高速化を保証しない。原著Tは符号化スロット数の文脈もあり、本研究の計画秒Tと混同しない|
|S4|From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz、Stuart Hadfield, Zhihui Wang, Bryan O'Gorman, Eleanor G. Rieffel, Davide Venturelli, Rupak Biswas、2019年v2|[arXiv v2原文](https://arxiv.org/html/1709.03489v2)|§3/3.1の可行部分空間とmixer条件、XY mixerの記述を確認した|制約を保持するmixerの概念的根拠である。本実装の復号後の全配送/バース可行性まで自動保証する根拠ではない|
|S5|Defining and detecting quantum speedup、Troels F. Rønnowほか、2014、Science 345:420–424|[DOI](https://doi.org/10.1126/science.1252319)、[著者原稿と補足](https://arxiv.org/pdf/1401.2910)|比較定義、Supplementのprogramming/annealing/readout/反復wall費用の原文を確認した|量子処理だけの時間と全費用を区別する根拠である。アニーリング装置の数値を本AOA/CPU時間へ移さない|
|S6|Benchmarking Optimization Software with Performance Profiles、Elizabeth D. Dolan, Jorge J. Moré、2002、Mathematical Programming 91:201–213|[DOI](https://doi.org/10.1007/s101070100263)、[原稿PDF](https://arxiv.org/pdf/cs/0102001)|§1–2。今回読んだarXiv v2は2004年更新の原稿である|失敗を除外する集計や少数難問への依存に注意する根拠である。performance profileを本研究のJやCIへ自動置換するものではない|
|S7|A Hitchhiker's guide to statistical tests for assessing randomized algorithms in software engineering、Andrea Arcuri, Lionel Briand、2014（online first 2012）、STVR24(3):219–250|[出版社原資料/DOI](https://onlinelibrary.wiley.com/doi/10.1002/stvr.1486)|書誌と公開SUMMARYを確認した。大学リポジトリの著者PDFは今回timeoutであり、全本文確認済みとはしない|確率的手法には適切な統計評価が必要という範囲で参照する。本研究n/rや階層CIの具体値を同論文から採用したとはしない|
|S8|A framework for the interactive resolution of multi-objective vehicle routing problems、Martin Josef Geiger, Wolf Wenger、2008|[原著preprint](https://arxiv.org/pdf/0809.0610)|§1–3、とくに§2の割当/順序、§3式(1)の距離/遅延加重和を確認した|多目的VRPと選好の明示例である。査読状態は今回確認していない。遅延TARDYを積込待機Wや計算時間Tと同一視しない|

確認不能の候補も記録するが、重要判断の本文根拠として採用しない。

|ID|候補|今回の取得結果|扱い|
|---|---|---|---|
|U1|G. Mavrotas (2009), Effective implementation of the ε-constraint method in Multi-Objective Mathematical Programming problems、[DOI](https://doi.org/10.1016/j.amc.2009.03.037)、[所属機関の書誌](https://dspace.lib.ntua.gr/xmlui/handle/123456789/19533)|DOI本文403、機関書誌には添付ファイルなし|書誌確認のみである。AUGMECONの本文を読んだとせず、本実装が原著どおりと認定しない|
|U2|N. Jozefowiez, F. Semet, E.-G. Talbi (2008), Multi-objective vehicle routing problems、[DOI候補](https://doi.org/10.1016/j.ejor.2007.05.055)|原本文を取得できず、書誌の検索結果のみである|未確認候補であり、主結論の根拠にしない|

## Aの一次資料と既存保存証拠

|ID|資料・主体・年/箇所|原値/確認事実|本研究への採否と未取得事項|
|---|---|---|---|
|A1|[佐川急便公式の都市/郊外歩数検証](https://www.sagawa-exp.co.jp/about-csr/column/article_33.html)、記事2025年、観測2025-01-10、検証結果|都市担当者のトラック13km/日。通常約20kmは別の一般説明である。保存原文SAGAWA_DISTANCE.txt L180–190と前回の原資料監査で確認した|全車/便/Nが不明で総D_Aへ換算不可である。実際の従来計画一式でも2020年導入前の観測でもない|
|A2|[関東運輸局・佐川関連荷扱い事例](https://wwwtb.mlit.go.jp/kanto/jidou_koutu/kamotu/kamotu_kyougikai/date/kanagawa/12/4.pdf#page=60)、PDF p.60の拠点間輸送図|平均荷積み待ち26分の欄がある。保存原画像KANTO_PAGE-60.pngと既存監査で対象業務を確認した|個人宅ToCの全便W_Aではない。ready/開始の定義とN/V/便数、観測日/生ログは未取得である|
|A3|[日本郵便・Loogia公式導入事例](https://loogia.jp/cases/nihonyubin/)、日本郵便担当者インタビュー「導入前の課題」、記事内2021年時点の注記|紙地図の熟練5〜10分、新人30分〜1時間程度。今回も当該原文を閲覧した。秒換算のみで300〜600/1800〜3600である|個別ルート作成の報告値である。全計画Tや分布/CIにしない。N/V/P、工程別時計境界は不明である|
|A4|[国交省・中小トラック運送業ITツール活用ガイド](https://www.mlit.go.jp/jidosha/content/001311692.pdf#page=7)、PDF p.7/印刷p.11、協栄流通の事例|改善前1センター毎日7〜8時間。今回のPDF原資料と既存行政台帳を照合した。25200〜28800秒は単位換算である|対象センターN/V/P、経過時間/人時の区別が未取得である。S1〜S3へ比例換算せず、全体配車の外部参照としてのみ扱う|

新たな公開運行データを取得したわけではない。異なる資料の数値を同一計画・同一母集団の三指標へ合成していない。企業への連絡・提供依頼は実施していない。

## リポジトリの重要証拠

パスはリポジトリrootからの相対名である。詳細な実在リンクは主報告の本文と、保全した前回FILE_LINK_INDEXにある。以下は該当箇所と重要なキーを固定した台帳である。

|ID|ファイル・箇所|確認内容|対応する監査事項|
|---|---|---|---|
|E01|configs/toc_delivery/common_conditions_v1_1.json L27–54、operations/scenarios|容量60/2便/120/1800/0、1000/10/2等|研究条件とモデル範囲|
|E02|src/kmd_toc/dwt/evaluation.py L34–42|3重み/正参照/加算、AならNone|Q03、候補式の計算核|
|E03|configs/toc_delivery/dwt_balance_v1_4_cpu_parallel.json L7–11/L42–77|A2、A人手T除外、S1旧A2参照とT60、S2/S3 null、equalと他重み|Q03/04/06|
|E04|src/kmd_toc/dwt/methods.py L78–108|A2生成、全B/C/DのCW開始、C追加Routing、共通完成|A定義・具体的比較対象|
|E05|src/kmd_toc/pipeline/classical.py L6–36/L39–63|有向CW、OR-Toolsの容量/距離とGLS、seed|B/Cの違い|
|E06|src/kmd_toc/pipeline/completion.py L57–105|有限プール、物理車両/2便/時刻/バース、ε、D優先同点W、FEASIBLE/OPTIMAL|Q08/16、共通制約|
|E07|src/kmd_toc/dwt/methods.py L175–218/L237–318|有限日列、最大3断片、AOA展開、古典対照、incumbent/量子帰属|Q11/12|
|E08|src/kmd_toc/column_generation/aoa.py L98–100/L183–200/L240–305|小規模guard、Ising/XY、tensor訓練、COBYLA、Statevector最終測定|Q12/13/15|
|E09|src/kmd_toc/dwt/parallel.py L139–167/L222–285/L320以降|全候補検査、D/W選択、親T、全枝CPU/量子量|Q08/10、計時/資源|
|E10|docs/research/DWT_STATISTICAL_PROTOCOL.md L19–25/L103–109|旧S2距離D単一比較、A除外、portfolio費用|Q05/09|
|E11|configs/toc_delivery/dwt_statistical_protocol_v1.json primary/sample_size/quantum|主比較D対C、n/r・精度・主shots等null|Q05/07/13|
|E12|docs/research/toc_delivery_a/A_REFERENCE_VALUES.md L9–15/L50–56と対応JSON|共通A_D/W/T未取得、原値の条件と換算禁止|Q01/02/17|
|E13|docs/research/DWT_FINAL_COMPARISON.md 限定結果/単一A/D量子部分|旧限定11/12受理、新量子経路最終採用0、A2推計|旧結果と新仮説の分離|
|E14|output/toc_delivery/cpu_parallel_20261113_v1/CPU_PARALLEL_VALIDATION_REPORT.md|人工6/20地点、246テスト・90/290検査は過去記録|Q10、今回未実行|
|E15|src/kmd_toc/common/validation.py L66–181|全被覆/容量/ready/積込/移動作業/帰着/W/バース検査|比較の物理的可行性|
|E16|03_data/processed/traffic_simulation/demand/toc_delivery/frozen_demand/v1/MANIFEST.json|固定1需要/規模、合成/単位需要、厳密包含、SHA順位|Q07、一般化範囲|
|E17|output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs/S1〜S3/input.jsonとod/manifest.json|地点/車両/バース数、共通有向Route ODとhash|入力の存在と共有|
|E18|docs/audits/readme_preparation_20261113_v1/FILE_LINK_INDEX.mdとREADME_FACT_AUDIT.md|前回322ファイル索引と120項目監査|再利用した探索地図。当時の2指標仮説判定は今回の正本でない|

主報告の数学的帰結や、参照不足が仮説検証を妨げるとの判断は監査者の推論である。文献が本研究の1/3、具体的参照値、統計必要数、量子優位を実証したとの記載はしていない。
