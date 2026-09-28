# 都道316号対向車線正式採択レビュー

## 結論

既存4-道路区間 候補を固定して審査した結果、3 対象すべて `REVIEW_REQUIRED` とする。
方向は既存診断を入力として使用し、selectedは `UP_TERMINUS_TO_ORIGIN`、代替は
`DOWN_ORIGIN_TO_TERMINUS` のまま再推測していない。交通 割当も `REVIEW_REQUIRED` を維持する。

<a id="固定review対象"></a>

## 固定確認対象

- selected 7 edges: `45662502;45662510#0;45662510#1;45662510#2;45662510#3;45662510#4;45662510#5`
- alternate 4 edges: `652322551#0;652322551#1;652322551#2;45662512`
- targets: `13403160330`, `13403160340`, `13403160350`

## 判定根拠

route identity、relation `11699637` membership、SUMO connection、node continuity、contamination、
別一方通行 carriageway構造、3 対象の公式section-境界 chainはすべて合格した。bare ref単独、
direct 逆方向 道路区間、visual inspection、GeoJSON coordinate 順序は判定根拠にしていない。

一方、既存25 m / high 網羅率 0.60基準に対し、代替の公式形状被覆は `0.503218`、selected/alternate相互被覆は `0.000000` / `0.000000`、反対端点差は `33.774 m` / `55.979 m` であり、空間的な条件を満たさない。

国道1号と同様に、route/topologyが合格して空間的な条件だけが不足する候補は棄却や強制採択をせず
`REVIEW_REQUIRED` とした。今回の不一致は横方向分離と両端にあり、端部切詰めだけの既存部分的-道路区間
仕様では解消できないため `ACCEPTED_AS_PARTIAL_EDGE_MAPPING` にもしない。

<a id="target別結果"></a>

## 対象別結果

| 対象 | boundary evidence | adoption | traffic assignment |
|---|---|---|---|
| `13403160330` | `DIRECT_60320_TERMINUS_TO_TARGET_ORIGIN` ["45662512"] | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |
| `13403160340` | `CHAIN_VIA_60330_TERMINUS_TO_TARGET_ORIGIN` ["1457802380"] | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |
| `13403160350` | `CHAIN_VIA_60340_TERMINUS_TO_TARGET_ORIGIN` ["1068239670","45662504"] | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |

<a id="他routeとの整合性"></a>

## 他経路との整合性

国道1号・都道2号・都道421号の既存採択確認と同じ25 m / 0.60基準、経路 同一性、
接続構造、混入条件を使用した。都道11号は既存complete 逆方向-道路区間 根拠を参照し、
経路 316専用の例外基準は作成していない。

## 次に必要な証拠

閾値変更ではなく、公式観測境界と両車道中心線の対応を説明できる追加の公式境界 根拠、
または既存道路網形状と公式形状の横方向位置補正値を正式にreconcileする再現可能な証拠が必要である。
既存方向成果物、正式対応付け、交通シミュレーターの道路網、config/thresholdは変更していない。

Validation: 94 passed, 0 failed.
