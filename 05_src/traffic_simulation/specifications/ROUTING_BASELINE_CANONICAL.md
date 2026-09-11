# Routing Baseline 正式仕様（現行）

Document ID: `R23-ROUTING-BASELINE-CANONICAL`
Lifecycle: `現行`
Updated: 2026-09-11

本書は配送最適化へ渡すRouting Baselineのcanonical specificationである。道路属性の詳細受入規約は既存のnetwork authorityとimmutable validation artifactが正本であり、本書はRouting Baselineの意味・入出力・下流境界を一意に定義する。

## Scope

Routing Baselineは、受入済み道路network上で配送地点間の移動可能性と移動費用を固定する層である。Reduced Problemはこの層のdirected travel timeを使う小規模Single-Vehicle Route Ordering Problemであり、Capacity、Time Window、Battery/SOC、Charging、Multiple Vehiclesを含むFull EVRPとは別scopeである。

## Entities

- depot: 配送車両の出発・帰着地点。
- customer: 配送対象地点。
- road network node / edge: 道路networkの接続点と有向道路区間。
- delivery location: 建物代表点等の配送地点と、対応付けられた道路側端点。

## Mapping

配送地点はversion付きmapping規則により道路network上のedge/nodeへ対応付ける。depot/customer mappingは端点ID、対応edge、mapping方法、入力hash、provenanceを保持する。最近傍だけで対応を断定せず、delivery通行可能性とnetwork connectivityを検証する。

## Routing outputs

各ordered origin-destination pair `(i,j)`について、`road_distance`、`travel_time`、`reachability`を出力する。origin、destination、network version、routing method、timestamp、provenance、入力hashと単位を併記する。到達不能・欠測のdistance/travel_timeは`null`等で明示し、0へ変換しない。

## Directed semantics

`i → j`と`j → i`は別のordered pairとして扱う。有向travel timeの非対称性を保持し、平均化・対称化・edge IDの符号推測を行わない。

## Reachability

`reachability=true`は、受入済み道路network上で実際にoriginからdestinationへ移動可能であることを示す。unreachable / missing pairを仮想edge、強制移動、人工的な有限値で隠さない。Formal Reduced Problemの採用instanceはcomplete directed reachabilityを要求する。

## Downstream use

| downstream | 渡すもの | 現在の境界 |
|---|---|---|
| Reduced Problem | directed travel time、distance、reachability、provenance | customer-only encoding、n=2,3,4、λ=3.0 |
| Capacity / Time Window | distance、travel time、reachability | 未着手 |
| Battery/SOC / Charging | distance、travel time、network位置、reachability | 未着手・未受入 |
| Full EVRP | 上記outputsとprovenance | R20 BLOCKED、R21 NOT_STARTED |

現行入口は[仕様index](README.md)。旧版・履歴の文書と実行artifactは削除せず、現行仕様と混同しないようindexで区別する。
