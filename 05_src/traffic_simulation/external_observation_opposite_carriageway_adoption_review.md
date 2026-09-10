# 外部観測参照 opposite carriageway 正式採択レビュー

既存mappingを更新せず、前回抽出済みalternate候補だけを正式採択レビューした。

| 観測区間 | fixed | alternate/composite | coverage | endpoint最大差 | 判定 |
|---|---|---:|---:|---:|---|
| `13300010260` | `DOWN_ORIGIN_TO_TERMINUS` | 14/14 edge | 0.736383/0.586498 | 220.357 m | `REVIEW_REQUIRED` |
| `13400020040` | `DOWN_ORIGIN_TO_TERMINUS` | 43/43 edge | 1.000000/1.000000 | 23.446 m | `ACCEPTED_AS_OPPOSITE_CARRIAGEWAY` |
| `13604210030` | `DOWN_ORIGIN_TO_TERMINUS` | 14/81 edge | 0.999864/0.999747 | 3.205 m | `ACCEPTED_AS_OPPOSITE_CARRIAGEWAY` |

国道1号の既抽出14-edge候補はroute identityとtopologyを満たすが、一端が約220 mオーバーランし、候補側の25 m相互被覆が既存high coverage 60%を下回る。候補を切り詰めず `REVIEW_REQUIRED` とした。

都道421号は既存67 reverse edgeを同じ順序で保持し、欠損部へalternate 14 edgeを挿入した81-edge UP列として検証した。connection violationは0である。

## Summary

- 正式採択: 2
- REVIEW_REQUIRED: 1
- REJECTED: 0
- UNRESOLVED: 0
- 採択後に双方向交通量割当可能: 2

Validation: 92 passed, 0 failed.
