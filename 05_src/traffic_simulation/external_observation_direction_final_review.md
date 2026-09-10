# 外部観測参照9件の方向証拠・交通量割当可否 最終確認

## 結論

正本inventoryの条件抽出により9件・5 clusterを再現した。方向証拠は6/9件で確定し、3/9件は未解決を維持した。

方向証拠とreverse corridor可用性は別判定である。固定mapping、採択edge列、matching閾値、元データは変更していない。

## Cluster判定

| cluster | 観測区間 | 対象数 | 固定列の方向 | 方向証拠 | reverse | 交通量割当 |
|---|---:|---:|---|---|---:|---|
| `ROUTE_JP_national_1` | `13300010260` | 1 | `DOWN_ORIGIN_TO_TERMINUS` | `RESOLVED` | 0/15 | `REVERSE_CORRIDOR_MISSING` |
| `ROUTE_JP_prefectural_tokyo_2` | `13400020040` | 1 | `DOWN_ORIGIN_TO_TERMINUS` | `RESOLVED` | 0/40 | `REVERSE_CORRIDOR_MISSING` |
| `ROUTE_JP_prefectural_tokyo_11` | `13400110130` | 3 | `UP_TERMINUS_TO_ORIGIN` | `RESOLVED` | 5/5 | `BIDIRECTIONAL_ASSIGNABLE` |
| `ROUTE_JP_prefectural_tokyo_316` | `13403160320` | 3 | `UNASSIGNED_DIRECTION` | `UNRESOLVED` | 0/7 | `REVERSE_CORRIDOR_MISSING` |
| `ROUTE_JP_PREFECTURAL_ROAD_13_421` | `13604210030` | 1 | `DOWN_ORIGIN_TO_TERMINUS` | `RESOLVED` | 67/77 | `REVERSE_CORRIDOR_PARTIAL` |

## 判定規律

Road Census公式定義の `UP=TERMINUS_TO_ORIGIN`、`DOWN=ORIGIN_TO_TERMINUS` を全clusterへ適用した。原票の相互隣接区間・区境、原票に記載された接続路線、明示的なroute relation、SUMO from/to・接続・reverseの順で照合した。GeoJSON座標順、bearing、交通量の大小は方向判定に使用していない。

完全reverseは、採択列を逆順にした各edgeについて `from/to` を交換したedgeが一意に存在し、その列のSUMO connection violationが0である場合だけ認定した。部分reverseをUP/DOWN列として採用せず、欠損edgeを生成していない。

## QA

- 未分類: 0
- 採択列connection violation: 0
- 既存正式mapping SHA不変: True
- 既存66区間mapping SHA不変: True
- matching設定 SHA不変: True
- validation: 76 passed / 0 failed

詳細な原票端点、anchor、reverse欠損edge、規則・provenanceはCSVとmanifestを正本とする。
