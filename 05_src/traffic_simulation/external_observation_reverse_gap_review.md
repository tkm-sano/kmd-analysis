# 外部観測参照 reverse不足 原因調査

正本の条件抽出で6件・4 clusterを再現し、固定mapping・採択edge列・閾値・元データ・networkを変更せず調査した。

| 観測区間 | 固定reverse | 不足edge | alternate corridor | 原因 | 解決区分 |
|---|---:|---:|---:|---|---|
| `13300010260` | 0/15 | 15 | 14 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `MAPPING_ONLY_REVIEW_REQUIRED` |
| `13400020040` | 0/40 | 40 | 43 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `MAPPING_ONLY_REVIEW_REQUIRED` |
| `13403160320` | 0/7 | 7 | 4 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `HOLD_DIRECTION_UNRESOLVED` |
| `13604210030` | 67/77 | 10 | 14 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `MAPPING_ONLY_REVIEW_REQUIRED` |

## 結論

72不足edgeすべてについて、同一node pairのreverseではなく、同一路線の分離oneway反対車道が既存SUMO内に存在した。候補はnetconvert入力OSMにも存在し、生成netからの脱落・network範囲外・source欠損ではない。個々のoneway指定は妥当だが、道路全体としてreverse不要という意味ではないため、主要因を `LEGITIMATE_ONEWAY` ではなく `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` とした。

都道316号はalternate候補を確認したが、方向証拠がUNRESOLVEDである。候補をUP/DOWNとして採用せず、3対象を方向未解決保留とした。

## 6件集計

- mapping修正だけで解決可能（正式再レビュー要）: 3
- network再生成／限定拡張: 0
- OSM/source不足: 0
- legitimate one-wayを終端原因とするもの: 0
- 方向未解決のため保留: 3
- 原因未解決: 0

都道421号は既存67/77を固定し、欠損10 edgeだけを調査した。alternate 14 edgeは欠損区間の両端へ接続し、connection violationは0である。

Validation: 84 passed, 0 failed.
