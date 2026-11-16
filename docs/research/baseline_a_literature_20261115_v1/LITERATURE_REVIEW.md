# ベースラインAの先行研究追加調査

確認日は2026-11-15である。今回の範囲は、先行研究の再利用実績、公開実装・データ、車両割当・訪問順・複数便・積込待機への適用可能性の調査である。アルゴリズムやRQ・仮説、既存の採用判定は変更していない。再現実験・本実験・有料計算・外部連絡は実施していない。

**実績模倣の訪問順成分ではCookらのLKH-AMZを第一再現候補、Wuらを第二再現候補とする。複数車両の割当を含める理論的候補はCanoyらの2023年論文である。ただし、いずれも大田区の全体Aとして採用確定できたわけではない。** これら三つは異なる候補の役割であり、無検証で組み合わせて単一の実証済み方式と呼ばない。

## 選定の観点

研究を引用していること、後続研究が手法を拡張したこと、比較実験で使ったこと、独立した著者が同じ実装を再実行したことを分ける。賞・被引用数だけで標準手法とは判定しない。原論文の結果を大田区のD/W/Tへ転用せず、本研究の需要・道路・制約で計画を生成する必要がある。

## 候補の比較

|研究・一次資料|実績との対応と対象|公開物・再現上の状態|今回の判断|
|---|---|---|---|
|Cook, Held, Helsgaun： [Constrained Local Search for Last-Mile Routing](https://doi.org/10.1287/trsc.2022.1185)、2022年オンライン、2024年58(1)掲載|過去の配送順から制約を得て、ペナルティ付き局所探索で実績に近い単一ルートを作る。最短経路だけを求める方式とは評価目的が異なる|[著者実装](https://github.com/heldstephan/jpt-amz)とMITライセンス、モデル構築・適用script、TSPLIB生成処理を確認した。競技版と論文改良版の対応は未確定である|**訪問順の第一再現候補**。独立研究での比較対象利用も確認できた。全車両割当、2便、拠点待機は原方式の実証範囲としない|
|Wuほか：[Learning from Drivers to Tackle the Amazon Last Mile Routing Research Challenge](https://arxiv.org/abs/2205.04001)、2022|PPMで区域の遷移系列を学び、rolloutで区域順、TSPで区域内順序を作る。米国実績の順序を対象とする|[著者実装](https://github.com/aws-samples/amazon-sagemaker-amazon-routing-challenge-sol)とローカル実行経路を確認した。論文のLKHと公開例のOR-Toolsは異なる実装である|**第二再現候補**。公開実装を再現する場合、原論文と同一実装とは記述しない。大田区での区域と未知区域への一般化が課題である|
|Canoyほか：[Learn and route: learning implicit preferences for vehicle routing](https://doi.org/10.1007/s10601-023-09363-2)、2023|Markovモデルで計画者の選好を学び、複数車両の容量制約付きルーティングを生成する。9か月201日分の企業計画を評価する。変化前は平均約35地点/9車、変化後は25地点/6車との説明がある|§4.2の実データ、割当差RDとarc差AD、時系列評価、Python3.7.4/CPLEX12.9を確認した。原データと著者コードの公開場所は未確認である|**車両割当を含む設計の主要参考**。本研究の1000〜4000地点への性能やToC適合は立証されない。原データの入手見通しが立たないまま忠実再現を約束しない|
|Canoyほか：[Probability estimation and structured output prediction for learning preferences in last mile delivery](https://doi.org/10.1016/j.cie.2024.109932)、2024|区域遷移確率と距離を組み合わせ、区域順とstop順を二段階で生成する。実績の疎な住所集合への対応を検討する|正式版の書誌・要旨と、[2022年前刷本文](https://arxiv.org/html/2201.10269v1)を確認した。保存PDFは2022年前刷であり、2024年最終版全文ではない。著者コード公開場所は未確認である|**方式の補助候補**。Amazon実績を用いた順序成分の再実装候補である。前刷と最終版の差を確かめる必要がある|
|Dieter, Caron, Schryen：[Integrating driver behavior into last-mile delivery routing](https://doi.org/10.1016/j.ejor.2023.04.043)、2023|予測された運転者の経路と提案経路の差、およびコストを扱うTSPTWの意思決定支援枠組みである|出版社の要旨を確認した。大学保存PDFの取得はtimeoutであり、実装・原データへの公開アクセスを今回確定できていない|**有力な関連枠組み**。引用は多いが、現時点で最初の実装対象にはしない。全文未取得部分を推測して仕様化しない|
|Sun, Arslan：[A contextual framework for learning routing experiences in last-mile delivery](https://doi.org/10.1016/j.trb.2025.103172)、2025|実績の選好を特徴量別の遷移重みに学び、TSPで経路を生成する|2024年CIRRELT報告版に加え、2025年Transportation Research Part B掲載版を確認した。著者コードの公開場所は未確認である|**学習する特徴と解釈可能性の参考**。前回の2024年報告版のみという書誌を更新する|
|Rashidi, Nourinejad, Roorda：[Generating practical last-mile delivery routes using a data-informed insertion heuristic](https://doi.org/10.1016/j.trc.2025.105278)、2025|実績の経路品質を学ぶ分類器と挿入法を組み合わせる。§5.1でCook法とOR-Tools GLSを比較対象にする|出版社本文の閲覧で比較対象利用を確認した。原著者コードをそのまま再実行したかは未確認である。データはrequestとされる|**後続研究の比較利用・評価設計の証拠**。自ら学習した品質分類器によるHQ判定を実務での観測改善と同一視しない|
|Nourmohammadiほか：[A data-driven preference learning approach for multi-objective vehicle routing problems in last-mile delivery](https://doi.org/10.1016/j.trc.2025.105101)、2025|複数目的CVRPTWで選好の重みを学び、実物流プラットフォームのシナリオで評価する|出版社に著者はデータを共有する許可を持たないとの明記がある|**全車両と選好学習の参考**。公開資料だけという条件で、その実データによる再学習・忠実な数値再現を第一候補にしない|
|Canoy, Guns：[Vehicle Routing by Learning from Historical Solutions](https://doi.org/10.1007/978-3-030-30048-7_4)、2019|過去の人手計画から遷移確率を学ぶ、2023年論文につながる先行研究である|[著者前刷](https://arxiv.org/abs/1909.07893)と正式版がある。同じ研究系統の後続拡張を独立追試と数えない|**方法論の起点**。旧版だけの書誌レコード被引用数を研究全体の影響と同一視しない|
|大佛・田口：[チーム集配方式における配達経路の最適化と配達業務の効率性評価](https://doi.org/10.3130/aija.85.1877)、2020|ヤマトの実配送調査に基づく作業時間・移動速度等と、実経路/最適化経路の比較である|全文・要旨は前回確認済みである。SDと台車担当FCの協調を扱う|**国内業務の補助根拠**。現行の車両単独モデルの全体Aへ直接置き換えない|

## 被引用数の再照合

出典をOpenAlex APIへ統一した。2026-11-15取得の個別レコードの `cited_by_count` であり、Google Scholar等と同じ件数とは限らない。前刷・会議版・掲載版を足し合わせていない。原レスポンス、DOI、著者、更新時刻は[sources/OPENALEX.json](sources/OPENALEX.json)に保存した。

|レコード|被引用数|OpenAlex ID|
|---|---:|---|
|Dieterほか2023|67|[W4367669861](https://openalex.org/W4367669861)|
|Cookほか2022オンライン版|34|[W4310251926](https://openalex.org/W4310251926)|
|Canoyほか2023|18|[W4387528389](https://openalex.org/W4387528389)|
|Nourmohammadiほか2025|16|[W4408836183](https://openalex.org/W4408836183)|
|Canoyほか2024掲載版|11|[W4391344344](https://openalex.org/W4391344344)|
|Wuほか2022前刷|9|[W4280644164](https://openalex.org/W4280644164)|
|Sun・Arslan2025掲載版|4|[W4407658241](https://openalex.org/W4407658241)|
|Rashidiほか2025|2|[W4413270905](https://openalex.org/W4413270905)|
|Canoy・Guns2019 DOIレコードのみ|1|[W2974313221](https://openalex.org/W2974313221)|
|大佛・田口2020|0|[W3090655603](https://openalex.org/W3090655603)|

Canoy2019は前刷等への引用統合を未確認である。1件という数字を同研究系統全体の被引用数として解釈しない。SpringerのCanoy2023ページは12件と表示したが、今回の統一表はOpenAlex18件を使う。0件は他サービスや実際の引用が0である保証ではない。被引用数による採用足切りは設けない。

## 引用、拡張、実験比較、独立再実行

|関係|確認した水準|未確認の点|
|---|---|---|
|Rashidi2025 → Cook法|独立著者の論文§5.1で、経路生成枠組みの実験比較対象として使うことを確認した|元著者公開コードの特定commitを無改変で再実行したか、その忠実度は未確認である|
|Canoy2019 → Canoy2023 → Canoy2024|共通著者を含む方法の発展と、VRPから区域・stop順への拡張を確認した|3本を独立3研究による同じ方式の追試と数えない|
|Sun2025 → Rashidi2025の関連研究説明|後続論文の本文で、特徴別遷移重みを学ぶ方式として引用・説明されることを確認した|Sun法をRashidi論文で数値再実装比較したことは確認できていない|
|Wu2022 → 著者コード|著者による実装公開と異なるTSP backendへの適用を確認した|独立著者による厳密な再実行を今回確定していない|

今回の調査から「幅広く再現済みの標準ベースライン」と断定しない。第一再現候補を選ぶ根拠は、目的適合、原実装・ライセンス、公開実績、他論文での実験比較がそろう点である。

## 複数便・積込・現場導入の補足文献

[Arikanほか2023：Human-Centric Parcel Delivery at Deutsche Post](https://doi.org/10.1287/inte.2023.0031)は、実配達履歴から先行関係制約を得る、現場導入された宅配の経路生成を報告する。Aに古典最適化を含めること自体が実務との矛盾になるわけではない。一方、原データ・コードの公開入手は今回未確認であり、対象拠点のD/W/T校正値として使わない。

[Rijalほか2023：Dynamics between warehouse operations and vehicle routing](https://doi.org/10.1111/poms.14051) §7.1は、実際の倉庫の逐次計画を比較基準とし、先にルート、次に倉庫準備を計画する方式を明示する。積込を含む比較基準を業務工程から定義する例として参考になる。ただし対象は小売補充の倉庫であり、当該ToC拠点のFCFS運用や積込待機値の根拠ではない。

[Xuほか2023：Multi-Trip Vehicle Routing Problem with Time Windows and Resource Synchronization on Heterogeneous Facilities](https://doi.org/10.3390/systems11080412)は、複数便と有限施設の同期を明示的に扱う。ただし長距離の産業物流・複数勤務日の設定であり、ToC実績の代表資料ではない。数理的な制約の参考に限る。

これらを組み合わせても単一事業者の実績セットにはならない。巡回順論文の中で荷物の積込順に言及があっても、それは拠点の有限バース待機Wの実測検証と異なる。

## 適用に向けた判断

今回確認した主な実績模倣論文に、凍結した大田区全需要の車両割当、最大2便、拠点バース待機、同一定義のD/W/Tまでを一括で実証する方式は確認できなかった。Canoy2023とNourmohammadi2025は複数車両という点で近いが、公開データと規模に不足がある。Cook/Wuは再現可能性が高いが、担当先集合が与えられた後の順序成分である。

従って、先行研究の方式を再現する次段階へ進む根拠は得られた。一方、文献の掲載値をAのD/W/Tへ置くことや、現在の代表性FAILを引用数だけで変更することはできない。次の具体的なゲートは[再現・移転計画](ADOPTION_AND_REPRODUCTION_PLAN.md)に記載した。
