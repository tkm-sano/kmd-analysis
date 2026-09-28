# 外部観測参照9件の方向証拠・交通量割当可否 最終確認

## 結論

正本一覧の条件抽出により9件・5 clusterを再現した。方向証拠は6/9件で確定し、3/9件は未解決を維持した。

方向証拠と逆方向 corridor可用性は別判定である。固定対応付け、採択道路区間列、matching閾値、元データは変更していない。

## 群判定

| cluster | 観測区間 | 対象数 | 固定列の方向 | 方向証拠 | 逆方向 | 交通量割当 |
|---|---:|---:|---|---|---:|---|
| `ROUTE_JP_national_1` | `13300010260` | 1 | `DOWN_ORIGIN_TO_TERMINUS` | `RESOLVED` | 0/15 | `REVERSE_CORRIDOR_MISSING` |
| `ROUTE_JP_prefectural_tokyo_2` | `13400020040` | 1 | `DOWN_ORIGIN_TO_TERMINUS` | `RESOLVED` | 0/40 | `REVERSE_CORRIDOR_MISSING` |
| `ROUTE_JP_prefectural_tokyo_11` | `13400110130` | 3 | `UP_TERMINUS_TO_ORIGIN` | `RESOLVED` | 5/5 | `BIDIRECTIONAL_ASSIGNABLE` |
| `ROUTE_JP_prefectural_tokyo_316` | `13403160320` | 3 | `UNASSIGNED_DIRECTION` | `UNRESOLVED` | 0/7 | `REVERSE_CORRIDOR_MISSING` |
| `ROUTE_JP_PREFECTURAL_ROAD_13_421` | `13604210030` | 1 | `DOWN_ORIGIN_TO_TERMINUS` | `RESOLVED` | 67/77 | `REVERSE_CORRIDOR_PARTIAL` |

## 判定規律

Road Census公式定義の `UP=TERMINUS_TO_ORIGIN`、`DOWN=ORIGIN_TO_TERMINUS` を全clusterへ適用した。原票の相互隣接区間・区境、原票に記載された接続路線、明示的な経路 関係、スーモ from/to・接続・逆方向の順で照合した。GeoJSON座標順、bearing、交通量の大小は方向判定に使用していない。

完全逆方向は、採択列を逆順にした各道路区間について `from/to` を交換した道路区間が一意に存在し、その列のスーモ 接続 violationが0である場合だけ認定した。部分逆方向をUP/DOWN列として採用せず、欠損道路区間を生成していない。

## QA

- 未分類: 0
- 採択列接続 violation: 0
- 既存正式対応付け ハッシュ値不変: 真
- 既存66区間対応付け ハッシュ値不変: 真
- matching設定 ハッシュ値不変: 真
- validation: 76 passed / 0 failed

詳細な原票端点、基準、逆方向欠損道路区間、規則・出典・来歴はコンマ区切り形式と成果物一覧を正本とする。
