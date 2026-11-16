# 統計実験設計・集計規則

この版は実験単位と集計処理を実装する。正式需要数、人員、計算反復数、精度・検出力、正式な予算の数値を今回の人工テストから決めない。formal_templateには未決定値をnullで残し、未指定の実行を拒否する。

## 反復単位

|要因|記録と扱い|
|---|---|
|需要|scenario_id、case_id、family_id、demand_seed、生成manifest・候補元hash。A〜D共通|
|規模|S1/S2/S3。入れ子ケースを独立標本として数えない|
|計算乱数|solver_seedとDのquantum_seed。需要seedとは別|
|同じ需要への再実行|run_id、repetition。分散は同じ需要内の計算変動|
|人間|participant_id、経験・ツール、順序、既閲覧、休止、修正。学習・疲労・担当者差を記録|
|内部枝・shots|計算資源・内部処理の記録。独立需要数・外側反復数にしない|
|retry・learning|元試行を保持しanalysis_roleを別にする。primaryの対応平均へ入れない|

同一規模の複数需要はregistered_scenarioで受け入れる。inputs.sampling_planは生成要求を作るだけであり、既存需要やODを再生成しない。新しい生成器の正しさ・母集団・抽出独立性は別途検証が必要であり、seedが異なることだけで独立性を証明しない。

## 二層の表

第一層は全予定runについて予定・実施・未実施／未完了、入力不正、timeout、実行エラー、中断、検証済み計画、修正・retry・learningを表示する。完成率の分母は全observed開始試行で、入力不正を含むことを明記する。エラー・timeoutを除外しない。入力不正件数を別表示する。候補の物理可行率と期限内採用完成率を区別する。実行中で終了記録のないものも未完了として残す。

第二層は比較ペア・同じcaseで双方が成功したprimary記録だけの条件付きD/W/Tを表示する。未実施・入力不正・片側成功・両側失敗を別の状態として表示する。全予定primaryの観測記録が揃わないcaseを、完了したcaseとして扱わない。成功条件付きの平均は常に第一層の完成率と併記する。C/Dが成功していればAの失敗を理由にC対Dの生D/W/Tを消さない。

平均・中央値・標本標準偏差（n≥2）・IQR・最小最大を算出する。第一層のconditional_success_metricsは全roleの成功runを対象とした実施記録の記述であり、learning/retryも含む。正式な方式間の対応比較は第二層のprimaryだけを用いる。IQRは(n−1)pの線形補間である。方式間差はright−left、相対改善率は100×(left−right)/leftである。left=0なら相対率はnullとし理由を保存する。欠測、無限、NaNを補完しない。timeoutを上限秒ちょうどの完了時間へ置換しない。全試行T_attemptと成功条件付きT_totalを分ける。

## 推論を許す条件

既定のfixed_cases/descriptiveは当該ケースにおける記述だけを行い、p値・信頼区間を出さない。複数の独立した需要ケースを事前登録し、対応ケース平均差が独立な正規標本であるという仮定を明記する場合に限り、paired_case_tを選べる。各case・方式で成功primary反復を平均し、caseごとの差を一つの推論単位とする。計算反復数を需要nとして使用しない。

母集団CIでは最低2つの対応成功ケースが必要である。family共有、independent_draw=false、同じ担当者が複数ケースに現れる場合は、この単純な独立ケースCIを出さず理由を保存する。差の分散0でも一般化の精度を保証できないためCIをnullとする。異なる担当者を用いる場合、推論対象は登録した需要・担当者配置を含む条件であり、担当者間能力差を量子処理の効果に読み替えない。担当者内反復や交差配置には別の階層モデルと事前計画が必要で、本版では推論しない。

confidence、比較ペア、主要指標、multiplicityを事前登録する。pointwise_exploratoryは個別区間で同時被覆を主張しない。bonferroniは登録したペア×規模×推論指標の数を用い、失敗後に比較数を減らさない。統計仮定をデータの有意性に合わせて変更しない。失敗が方式に依存する場合、成功条件付きの差は全ケースに対する方式の性能差ではない。選択された成功ケースへの限定を明記する。

方法選択と反復・精度設計の考え方について、問題インスタンスと実行反復を区別するCampelo & Takahashi, 2018, *Sample size estimation for power and accuracy in the experimental comparison of algorithms*, [arXiv:1808.02997v2](https://arxiv.org/abs/1808.02997)、目的・生成機構・評価量を事前に整理するMorris, White & Crowther, 2019, *Using simulation studies to evaluate statistical methods*, [DOI:10.1002/sim.8086](https://doi.org/10.1002/sim.8086)を参考情報として確認した。これらから本研究の具体的nや正規性が導かれるとはしない。

## Jと正式採用

旧J=(D/D_A+W/W_A+T/T_A_ref)/3はA_ruleのprogram時間参照を含む。人手AのT_total参照へ転用しない。human-inclusiveでは参照群・正規化・重みを別途承認・登録するまでJ=null、理由HUMAN_TOTAL_REFERENCE_NOT_PREREGISTEREDである。J欠測を理由にD/W/Tを削除しない。

正式採用の判定は[採用仕様](ADOPTION_SPEC.md)による。少数観測の記述が可能であること、統計的な一般化、配送事業者の代表性は別に判定する。今回は人工入力のみであり、実測の平均・CI・優位性を報告しない。
