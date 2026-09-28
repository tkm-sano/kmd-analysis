# 外部観測参照対向車線正式採択レビュー

既存対応付けを更新せず、前回抽出済み代替候補だけを正式採択レビューした。

| 観測区間 | 固定済み | alternate/composite | 網羅率 | 端点最大差 | 判定 |
|---|---|---:|---:|---:|---|
| `13300010260` | `DOWN_ORIGIN_TO_TERMINUS` | 14/14 edge | 0.736383/0.586498 | 220.357 m | `REVIEW_REQUIRED` |
| `13400020040` | `DOWN_ORIGIN_TO_TERMINUS` | 43/43 edge | 1.000000/1.000000 | 23.446 m | `ACCEPTED_AS_OPPOSITE_CARRIAGEWAY` |
| `13604210030` | `DOWN_ORIGIN_TO_TERMINUS` | 14/81 edge | 0.999864/0.999747 | 3.205 m | `ACCEPTED_AS_OPPOSITE_CARRIAGEWAY` |

国道1号の既抽出14-道路区間候補は経路 同一性と接続構造を満たすが、一端が約220 mオーバーランし、候補側の25 m相互被覆が既存high 網羅率 60%を下回る。候補を切り詰めず `REVIEW_REQUIRED` とした。

都道421号は既存67 逆方向 道路区間を同じ順序で保持し、欠損部へ代替 14 道路区間を挿入した81-道路区間 UP列として検証した。接続 violationは0である。

## まとめ

- 正式採択: 2
- REVIEW_REQUIRED: 1
- REJECTED: 0
- UNRESOLVED: 0
- 採択後に双方向交通量割当可能: 2

Validation: 92 passed, 0 failed.
