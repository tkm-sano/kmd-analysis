# 都道316号 opposite carriageway 正式採択レビュー

## 結論

既存4-edge candidateを固定して審査した結果、3 targetすべて `REVIEW_REQUIRED` とする。
directionは既存診断をinputとして使用し、selectedは `UP_TERMINUS_TO_ORIGIN`、alternateは
`DOWN_ORIGIN_TO_TERMINUS` のまま再推測していない。traffic assignmentも `REVIEW_REQUIRED` を維持する。

## 固定review対象

- selected 7 edges: `45662502;45662510#0;45662510#1;45662510#2;45662510#3;45662510#4;45662510#5`
- alternate 4 edges: `652322551#0;652322551#1;652322551#2;45662512`
- targets: `13403160330`, `13403160340`, `13403160350`

## 判定根拠

route identity、relation `11699637` membership、SUMO connection、node continuity、contamination、
別oneway carriageway構造、3 targetの公式section-boundary chainはすべてPASSした。bare ref単独、
direct reverse edge、visual inspection、GeoJSON coordinate orderは判定根拠にしていない。

一方、既存25 m / high coverage 0.60基準に対し、alternateの公式geometry被覆は `0.503218`、selected/alternate相互被覆は `0.000000` / `0.000000`、反対端点差は `33.774 m` / `55.979 m` であり、spatial条件を満たさない。

国道1号と同様に、route/topologyがPASSしてspatial条件だけが不足する候補は棄却や強制採択をせず
`REVIEW_REQUIRED` とした。今回の不一致は横方向分離と両端にあり、端部切詰めだけの既存partial-edge
仕様では解消できないため `ACCEPTED_AS_PARTIAL_EDGE_MAPPING` にもしない。

## target別結果

| target | boundary evidence | adoption | traffic assignment |
|---|---|---|---|
| `13403160330` | `DIRECT_60320_TERMINUS_TO_TARGET_ORIGIN` ["45662512"] | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |
| `13403160340` | `CHAIN_VIA_60330_TERMINUS_TO_TARGET_ORIGIN` ["1457802380"] | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |
| `13403160350` | `CHAIN_VIA_60340_TERMINUS_TO_TARGET_ORIGIN` ["1068239670","45662504"] | `REVIEW_REQUIRED` | `REVIEW_REQUIRED` |

## 他routeとの整合性

国道1号・都道2号・都道421号の既存採択reviewと同じ25 m / 0.60基準、route identity、
topology、contamination条件を使用した。都道11号は既存complete reverse-edge evidenceを参照し、
Route 316専用の例外基準は作成していない。

## 次に必要な証拠

閾値変更ではなく、公式観測境界と両車道中心線の対応を説明できる追加の公式boundary evidence、
または既存network形状と公式geometryの横方向offsetを正式にreconcileする再現可能な証拠が必要である。
既存direction成果物、正式mapping、SUMO network、config/thresholdは変更していない。

Validation: 94 passed, 0 failed.
