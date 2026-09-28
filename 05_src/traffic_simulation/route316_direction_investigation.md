<a id="都道316号-13403160320-direction-formal-investigation"></a>

# 都道316号 `13403160320` 方向正式調査

## 直接原因

既存 `UNRESOLVED` の直接原因は、公式の起点・終点は確認済みでも、部分被覆の7-道路区間
固定列のどちらの端が公式起点／終点側かを、当時の公式隣接区間・接続路線・明示的
経路 関係方向から一意に基準できなかったことである。これは証拠矛盾ではなく
`PRIOR_EVIDENCE_INSUFFICIENT_NOT_CONFLICTING` である。

## 結論

3 対象すべてについて、selected corridorを `RESOLVED_UP` と判定する
（導出分類は `RESOLVED_BY_COMBINED_EVIDENCE`）。診断上の方向は次のとおりである。

- 固定7-道路区間 corridor: `UP_TERMINUS_TO_ORIGIN`
- alternate 4-edge corridor: `DOWN_ORIGIN_TO_TERMINUS`

既存正式対応付け、既存方向 分類、交通シミュレーターの道路網、matching閾値は変更していない。
本成果物は診断レイヤーであり、正式対応付けへの採択適用は別工程とする。

方向証拠状況は `RESOLVED` だが、交通 割当 状況は `REVIEW_REQUIRED` である。
代替は方向・経路 同一性・接続構造の観点では
`FORMAL_ADOPTION_REVIEW_ELIGIBLE_NOT_ADOPTED` であり、正式採択済みではない。

<a id="公式定義とendpoint"></a>

## 公式定義と端点

- MLIT定義: `UP=TERMINUS_TO_ORIGIN; DOWN=ORIGIN_TO_TERMINUS`
- Road Census `13403160320`: 経路 316「日本橋芝浦大森線」、起点側「品川区道」
  （接続先 `13403160400`）、終点側「品川区・大田区境」
- 東京都路線調書: 起点 `中央区日本橋本町三丁目`、終点 `大田区大森南一丁目`
  （2024-04-01現在、文書ファイル page 10 / printed page 193）

東京都の公式路線調書: https://www.kensetsu.metro.tokyo.lg.jp/content/000064960.pdf

<a id="resolving-evidence-combination"></a>

## resolving 根拠組合せ

1. `60320`終点と`60330`起点は公式原票で同じ「品川区・大田区境」である。
2. 代替末尾と`60330`先頭は道路区間 `45662512`を共有する。
3. `60330`終点／`60340`起点は「環状七号線」で、道路区間 `1457802380`を共有する。
4. `60340`終点／`60350`起点は「高速１号羽田線」で、道路区間
   `1068239670;45662504`を共有する。
5. 各列は接続 violation 0で、同じ正本 経路 関係に属する。
6. 固定列と代替列は別一方通行 carriagewayで逆向き
   （方向 cosine -0.998690）である。

この公式端点 chainとスーモ shared-道路区間 接続構造が代替を起点→終点へ基準し、
代替をDOWN、対応する反対車道の固定列をUPへ接続する。形状は車道対応と位置の
補助に限定し、GeoJSON coordinate 順序を方向証拠には使用していない。

<a id="route-relation-diagnosis"></a>

## 経路関係要素診断

- relation: `11699637`
- name / 道路網 / ref: `日本橋芝浦大森線` / `JP:prefectural:tokyo` / `316`
- 演算子: 空欄
- fixed member sequence: `CONTIGUOUS_DECREASING`
- alternate member sequence: `CONTIGUOUS_DECREASING`
- 構成要素 役割: 対象構成要素はすべて空欄

関係は正本 同一性と構成要素 continuityを支持するが、方向注記、演算子、
forward/backward 役割がない。さらに両反対車道が同じdecreasing 索引 trendを持つため、
関係 sequence単独ではUP/DOWNを確定できない。bare numeric `ref=316`単独も使用していない。

## 残る制約

原票が`60320`起点側の接続先として参照する`13403160400`は、手元の`kasyo13.csv`に
対応行がないため、起点側からの独立基準は得られない。ただし終点側から始まる3段の
公式section chainとスーモ 道路区間共有が同一結論を与え、矛盾証拠はない。

## 次工程と成果物

正式対応付けへ反対車道を追加する場合は、本診断とは分離した採択確認を実施する。
本調査は `route316_direction_evidence.csv`、`route316_direction_diagnosis.csv`、詳細な
edge/relation/adjacent/final 分類 コンマ区切り形式、QA ジェイソン形式、成果物一覧、検証 ジェイソン形式を生成する。

<a id="automated-tests"></a>

## 自動化した試験

関連回帰は `82 passed / `
`0 failed`
（Route316専用 `12`件）である。

## Git差分

Gitの更新・stage・変更記録は行っていない。作業 出典として調査スクリプト、本文書、専用試験を
workspaceへ追加し、生成CSV/JSONは既存のignored 処理済み-data ディレクトリへ出力した。
正式 対応付け、交通シミュレーターの道路網、matching config/thresholdのハッシュ値は成果物一覧入力ハッシュ値として固定した。
