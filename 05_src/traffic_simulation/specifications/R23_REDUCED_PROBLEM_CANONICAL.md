# 縮約した問題正式仕様（現行）

Document ID: `R23-REDUCED-PROBLEM-CANONICAL`
ライフサイクル: `現行`
Updated: 2026-09-14（status/authority linksのみ）

正式 A、Experiment B1、Experiment B2を経て受入されたReduced Problem 基準の正本 仕様である。

## 問題

Single-車両 経路 Ordering Problem。配送拠点=`0`、顧客=`1...n`。配送拠点から出発し、各顧客を1回訪問して配送拠点へ戻る。経路は`(0, π_1, ..., π_n, 0)`。

<a id="encoding"></a>

## 符号化

顧客-only 位置 符号化 `x[i,t] = 1` iff 顧客 `i` is assigned to 訪問 位置 `t`。論理上の 変数は`n²`、配送拠点は変数にしない。

## 必須制約

各顧客をちょうど1回割り当て、各訪問 位置にちょうど1 顧客を割り当てる。これは訪問順序 実行可能性でありFull 電気自動車配送経路問題 実行可能性ではない。

<a id="objective-and-qubo"></a>

## 目的 ・ 制約なし二値二次最適化

closed 経路のdirected 移動時間の費用を最小化する。

```text
H_QUBO = H_travel + λ(P_customer + P_position)
```

`H_travel`は配送拠点→first、連続顧客間、last→配送拠点のdirected 移動 term、罰則項は厳密-one制約の二乗である。正式 範囲は`n=2,3,4`、`λ=3.0`。λをn≥5へ一般化しない。詳細な係数・theorem linkageは[R20 supporting 仕様](R20_QAOA_SUBPROBLEM_SPEC.md)と正式 A 根拠を参照する。

<a id="exact-reference"></a>

## 厳密 参照

permutation enumerationで厳密 参照を作成し、best decoded 実行可能 経路と比較する。不正 bitstringsは破棄し、修復しない。

## 確率 ・ 復号

- `P_feasible`: 全体-状態 分母で配送ルールを守った状態の確率質量。
- `P_optimal`: 全体-状態 分母で厳密 最適 状態の確率質量。
- 確率はrenormalizeしない。
- `exact_optimum_found`は経路一致を示すだけで、P_optimal=1、100% 標本抽出 success、convergenceを意味しない。

<a id="current-evidence"></a>

## 現行 根拠

- 正式 A: n=2,3,4のproblem-規模、p、確率、中央処理装置 Aer burdenを確認。
- B1: COBYLAでinitialization 感度、問題例 heterogeneity、厳密 best-経路 recovery、終了 不確実性を確認。
- B2: fixed_0.1の6 paired 条件でCOBYLA/Nelder-MeadのP_feasible、P_optimal、実行時間、nfev、終了差を確認。比較基準 COBYLAとB2 Nelder-Meadはそれぞれ厳密 best 経路 recovery 6/6。B2 scientific 整合性は6/6 VERIFIEDだが、terminal-索引 ハッシュ値不整合6件により成果物 整合性はFAILED。現行assessmentは[R23 状況](../R23_STATUS.md)を参照する。
- status: `R23_REDUCED_PROBLEM_BASELINE_ACCEPTED_WITH_LIMITATIONS`。

## 限界

`n=2,3,4`のみ、small deterministic 問題例 set、厳密 状態ベクトル、有限 回測定なし、noiseなし、中央処理装置 Aer、limited optimizers/initializations、Full 電気自動車配送経路問題 constraintsなし。量子処理装置 性能、量子優位性、量子近似最適化アルゴリズム convergence、n>4、Full 電気自動車配送経路問題 generalizationを示さない。

<a id="current-authority"></a>

## 現行 正本

Scientific definition and accepted baseline scope are above. Current n=5 results, closure, audit axes, limitations and R24 gate are maintained only in [R23_STATUS.md](../R23_STATUS.md). The pre-cleanup document is retained byte-identically in the archive status snapshots.

n=5のλ 正本はλ=4.0、厳密方式 条件 λ>(5+1)/2=3。λ−境界=1、2λ−(n+1)=2。旧正本のmargin表記のみerratumが訂正し、元成果物とλは不変。n=2,3,4のλ=3.0は不変。
