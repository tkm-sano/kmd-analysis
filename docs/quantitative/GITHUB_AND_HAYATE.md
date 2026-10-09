# 配布範囲・研究説明・評価上の限界

## 配送問題の範囲

本公開候補は固定顧客集合・固定割当の単一巡回を扱います。主目的は道路旅行時間最小化、静的な訪問/時間窓/容量/帰還条件を判定します。正式RQ・主仮説は[READMEの原文引用](../../README.md#研究目的正式rq)を参照してください。

HayateのDECISION_SCOPE.mdは充電地点・充電量等を含む主研究の共通要件です。その要件が今回の配布実装で実現済みという意味ではありません。配送充足はエネルギー比較の前提であり、未配送で電力量が減ったことを省エネ成果としません。QAOA未取得は配送問題の物理的不能と同一ではありません。

## エネルギー境界

配布APIは保存区間のDC牽引Whを扱います。平坦路・回生なし・補機なし・エネルギー側積載0 kg・一定駆動効率・固定軌跡という正式条件を維持します。充電器入力、系統電力、計算機、通信、施設・製造、物流全体は評価外です。18 kWhの残量会計と、充電/SOC制約のある運行シミュレーションを区別します。

HayateのOPERATIONAL_ELECTRICITY_ACCOUNTING_REQUIREMENTS.mdは途中充電や終了在庫を含む主研究の会計要件です。これを今回のControlled-DC実装仕様として移植していません。詳細は[Battery/Energy API](BATTERY_AND_ENERGY_API.md)。

## 主要結果

正本は[最終freeze](../../01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json)。R0取得78/78・同一78、R1取得64/78・同一59/異経路5・未取得14。これらは経路取得件数であり実業務の配送充足率ではありません。

Method×Batteryは共通64ブロックでT=0が59、非ゼロ5、単位percentage points。古典6規模は468論理/460異なるインスタンス、観測された遅延136停止/116経路・帰還期限超過4を保持します。[Analysis API](ANALYSIS_API_AND_FROZEN_RESULTS.md)とNotebook04/05が同梱の保存表へ接続します。Hayateのdocs/RESEARCH_RESULTS.mdの別系列・旧条件を混ぜません。

## 限界

静的可行性、SUMOでの完走、SUMO実時刻による時間窓/帰還診断、実業務の全配送需要充足は別です。全車両同時運行・実業務全需要充足・量子実機優位・一般的大規模QAOA性能・社会全体の省エネは未実証です。充電を含む正式主仮説の成立を、無充電の本モデルだけで判定しません。

Hayateのdocs/RESEARCH_LIMITATIONS.mdは他の研究段階も含みます。本配布物ではこの節と各APIの条件を用いて範囲を明示し、過去文書を上書きしません。

## 用語

|用語|この配布物での意味|
|---|---|
|OD|道路上の出発地・到着地間の旅行時間等。顧客訪問順とは別|
|PUBO / QUBO|高次/二次の二値多項式最適化。正式Candidate C PUBOとqualification QUBOを区別|
|QAOA|量子近似最適化アルゴリズム。今回の正式記録は理想シミュレーション|
|DC牽引Wh|観測軌跡区間の車両牽引用直流電力量。kWh=1,000 Wh|
|Wh/kg|比エネルギー。容量固定下のパック質量へ反映|
|pp|percentage points。割合の差でありkWh差ではない|
|freeze|指定の条件/成果物を固定した記録。全体の妥当性保証や公開許諾ではない|
|NOT_ACQUIRED|所定の標本から採用経路を取得できなかった状態|

この用語説明は既存仕様の読解用で、新しい指標・モデルではありません。Hayateのdocs/GLOSSARY.mdの充電主研究に関する記号とは文脈を分けます。

## GitHubとHayate

推薦95ファイルは軽量再利用の範囲です。配布候補は[Distribution Manifest](../../reproducibility/release/GITHUB_DISTRIBUTION_MANIFEST.json)。元13,360件Release Manifest、全OD/SUMOネットワーク/native環境、全量詳細ログと旧成果はHayate原位置に保持します。GitHub同梱や独立永続バックアップを保証しません。全量研究再現は公開の必須条件とは分離します。

ライセンス・データ再配布・所属機関/共著者を含む権利は承認待ち。LICENSEの存在だけで全ファイルへ適用済みとはしません。Git追跡解除/commit/pushは別途承認が必要です。

## ライセンスの更新

権限を持つ自作コード・Notebookの自作部分へのApache-2.0適用は今回承認・明示しました。[範囲](../../README.md#利用条件ライセンスの適用範囲)を参照。データ・研究結果・共同/第三者の権利確認と、配布全体の公開承認は未完です。
