# 外部観測参照10件 正式mapping候補レビュー

review ID: `external_observation_mapping_candidate_review_20260827`

既存mappingおよびmatching閾値は変更していない。10 target参照は6 unique公式観測区間を参照する。

## 判定結果

| 公式観測区間 | target区間 | 分類 | network被覆 | candidate coverage | route identity | connection violation |
|---|---|---|---:|---:|---|---:|
| `13200100070` | 13200100080 | REVIEW_REQUIRED | 100.0% | 99.8% | CONFIRMED_CANONICAL_NAME_AND_ROUTE_RELATION | 0 |
| `13300010260` | 13300010290 | NETWORK_EXTENSION_REQUIRED | 24.5% | 24.5% | CONFIRMED_PARTIAL_WAY_REF | 0 |
| `13400020040` | 13400020050 | AUTO_ACCEPT | 100.0% | 100.0% | CONFIRMED_WAY_REF | 0 |
| `13400110130` | 13400110100 / 13400110110 / 13400110120 | AUTO_ACCEPT | 100.0% | 100.0% | CONFIRMED_WAY_REF | 0 |
| `13403160320` | 13403160330 / 13403160340 / 13403160350 | AUTO_ACCEPT | 100.0% | 58.1% | CONFIRMED_ROUTE_RELATION | 0 |
| `13604210030` | 13604210040 | AUTO_ACCEPT | 100.0% | 100.0% | CONFIRMED_WAY_REF | 0 |

## `13200100070`

自動選択された`5219302`は無名・refなし・route relationなしの`motorway_link`であるため、正式候補から除外した。公式名「高速1号羽田線」に対し、次の二つの本線corridorを確認した。

- `4854104#1;4854104#2`：coverage 99.8%、接続違反0
- `45554540#0;45554540#1`：coverage 99.4%、接続違反0

両方ともOSM `ref=1`、名称「首都高速1号羽田線」、route relation `4256244`、network=`首都高速道路`、relation ref=`1`である。relationのoperatorは空欄である。路線同一性は確認できるが、Census上り・下りへの割当が未確定のため`REVIEW_REQUIRED`とした。

## `13403160320`

7 edgeのselected corridorは接続違反0、coverage 58.1%で、変更していないmedium基準30%を満たす。OSM Wayの`ref=316`、別名「海岸通り」に加え、route relation `11699637`がnetwork=`JP:prefectural:tokyo`、ref=`316`、名称「日本橋芝浦大森線」を与える。正式路線identityと一致するため3 target参照を`AUTO_ACCEPT`とした。

## `13300010260`の限定拡張

公式geometry 1029.5mのうち、既存ネットワーク被覆は252.7m、未被覆は776.8m（75.5%）である。閾値調整ではなく、未被覆geometryの25m bufferを最小探索範囲とする。

```json
{
  "west": 139.717263428,
  "south": 35.617146755,
  "east": 139.720295799,
  "north": 35.62182519
}
```

これは最小の空間探索bboxである。実際のネットワーク生成では、bbox内の必要wayだけでなく、既存ネットワークへの接続nodeと該当restriction relationのclosureを含める。

## Summary

- 既存ネットワークで正式採用可能：**8/10**
- 手動確認：**1/10**
- 限定ネットワーク拡張が必要：**1/10**
- 未解決：**0/10**

方向別traffic系列への最終割当は本レビューの範囲外であり、`direction_assignment_finalized=false`を維持する。
