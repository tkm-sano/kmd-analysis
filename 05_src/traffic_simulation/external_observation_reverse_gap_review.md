<a id="外部観測参照-reverse不足-原因調査"></a>

# 外部観測参照 逆方向不足 原因調査

正本の条件抽出で6件・4 clusterを再現し、固定対応付け・採択道路区間列・閾値・元データ・道路網を変更せず調査した。

| 観測区間 | 固定逆方向 | 不足道路区間 | alternate corridor | 原因 | 解決区分 |
|---|---:|---:|---:|---|---|
| `13300010260` | 0/15 | 15 | 14 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `MAPPING_ONLY_REVIEW_REQUIRED` |
| `13400020040` | 0/40 | 40 | 43 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `MAPPING_ONLY_REVIEW_REQUIRED` |
| `13403160320` | 0/7 | 7 | 4 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `HOLD_DIRECTION_UNRESOLVED` |
| `13604210030` | 67/77 | 10 | 14 edge | `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` | `MAPPING_ONLY_REVIEW_REQUIRED` |

## 結論

72不足道路区間すべてについて、同一ノード pairの逆方向ではなく、同一路線の分離一方通行反対車道が既存スーモ内に存在した。候補はnetconvert入力オープンストリートマップにも存在し、生成netからの脱落・道路網範囲外・出典欠損ではない。個々の一方通行指定は妥当だが、道路全体として逆方向不要という意味ではないため、主要因を `LEGITIMATE_ONEWAY` ではなく `ALTERNATE_REVERSE_CARRIAGEWAY_IN_SUMO` とした。

都道316号は代替候補を確認したが、方向証拠が未解決である。候補をUP/DOWNとして採用せず、3対象を方向未解決保留とした。

## 6件集計

- 対応付け修正だけで解決可能（正式再レビュー要）: 3
- 道路網再生成／限定拡張: 0
- OSM/source不足: 0
- legitimate one-道路地物を終端原因とするもの: 0
- 方向未解決のため保留: 3
- 原因未解決: 0

都道421号は既存67/77を固定し、欠損10 道路区間だけを調査した。代替 14 道路区間は欠損区間の両端へ接続し、接続 violationは0である。

Validation: 84 passed, 0 failed.
