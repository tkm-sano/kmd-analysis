<a id="routing-baseline-正式仕様現行"></a>

# 経路計算の基準 正式仕様（現行）

Document ID: `R23-ROUTING-BASELINE-CANONICAL`
ライフサイクル: `現行`
Updated: 2026-09-11

本書は配送最適化へ渡す経路計算の基準の正本 仕様である。道路属性の詳細受入規約は既存の道路網 正本とimmutable 検証 成果物が正本であり、本書は経路計算の基準の意味・入出力・下流境界を一意に定義する。

<a id="scope"></a>

## 範囲

経路計算の基準は、受入済み道路道路網上で配送地点間の移動可能性と移動費用を固定する層である。Reduced Problemはこの層のdirected 移動 時間を使う小規模Single-車両 経路 Ordering Problemであり、容量、時間窓、Battery/SOC、充電、Multiple Vehiclesを含むFull 電気自動車配送経路問題とは別範囲である。

## 対象

- 配送拠点: 配送車両の出発・帰着地点。
- 顧客: 配送対象地点。
- road 道路網 ノード / 道路区間: 道路道路網の接続点と有向道路区間。
- 配送 位置: 建物代表点等の配送地点と、対応付けられた道路側端点。

## 対応付け

配送地点は版付き対応付け規則により道路道路網上のedge/nodeへ対応付ける。depot/customer 対応付けは端点識別子、対応道路区間、対応付け方法、入力ハッシュ値、出典・来歴を保持する。最近傍だけで対応を断定せず、配送通行可能性と道路網 connectivityを検証する。

<a id="routing-outputs"></a>

## 経路計算出力

各ordered 出発地-到着地 pair `(i,j)`について、`road_distance`、`travel_time`、`reachability`を出力する。出発地、到着地、道路網 版、経路計算 手法、timestamp、出典・来歴、入力ハッシュ値と単位を併記する。到達不能・欠測のdistance/travel_timeは`null`等で明示し、0へ変換しない。

<a id="directed-semantics"></a>

## 有向意味

`i → j`と`j → i`は別のordered pairとして扱う。有向移動 時間の非対称性を保持し、平均化・対称化・道路区間 識別子の符号推測を行わない。

<a id="reachability"></a>

## 到達可能性

`reachability=true`は、受入済み道路道路網上で実際に出発地から到着地へ移動可能であることを示す。到達不能 / 欠落 pairを仮想道路区間、強制移動、人工的な有限値で隠さない。正式 Reduced Problemの採用問題例はcomplete directed 到達可能性を要求する。

## 下流利用

| downstream | 渡すもの | 現在の境界 |
|---|---|---|
| Reduced Problem | directed travel time、distance、reachability、provenance | customer-only encoding、n=2,3,4、λ=3.0 |
| Capacity / Time Window | distance、travel time、reachability | 未着手 |
| Battery/SOC / Charging | 距離、移動 時間、道路網位置、到達可能性 | 未着手・未受入 |
| Full EVRP | 上記出力と出典・来歴 | R20 BLOCKED、R21 NOT_STARTED |

現行入口は[仕様索引](README.md)。旧版・履歴の文書と実行成果物は削除せず、現行仕様と混同しないよう索引で区別する。
