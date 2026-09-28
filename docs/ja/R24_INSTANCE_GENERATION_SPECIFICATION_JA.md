<a id="r24-instance-generation仕様日本語"></a>

# R24 問題例生成仕様（日本語）

原文正本: [R24_INSTANCE_GENERATION_SPECIFICATION.md](../../reproducibility/outputs/traffic_simulation/r24_instance_generation_specification/20260915_v1/R24_INSTANCE_GENERATION_SPECIFICATION.md)

Specification ID: `R24-INSTANCE-GEN-20260915-v1`<br>
Verdict: `R24_INSTANCE_GENERATION_SPEC_FROZEN_WITH_LIMITATIONS`

この文書は固定済み英語正本の日本語版です。機械実行では原文の固定文字列、列挙値、データ構造、ハッシュ値を使用してください。

## 1. 検証一式階層

1. **Primary — Repeated 無作為 Suite**: researcherによる事例選択biasを減らし、問題例間variationを測る主要な 比較用検証一式
2. **Secondary — Controlled 構造上の Suite**: `CLUSTERED`、`DISPERSED`、`MIXED`による空間構造stress 試験
3. **Reference — Fixed Anchor Suite**: regression、実装比較、QUBO/solver 版比較用の固定alias

<a id="2-problem-sizeと件数"></a>

## 2. 問題規模と件数

| 区分 | n | Repetitions |
|---|---|---:|
| Quantum-comparable core | `{2,3,4}` | 各10 |
| Classical extension | `{5,8,10,15,20}` | 各10 |
| Controlled Structural | `{4,10,20}` | 各structure・nで3 |
| Fixed Anchor | `{4,10,20}` | Primary R01 alias |

無作為 baseは80件、構造上の baseは27件、基準 aliasは3件です。`n`はcomputational ベンチマーク 規模であり、statistical 標本 規模や実経路 配送地点 件数ではありません。

## 3. 乱数の種とSRSWOR

Primary 乱数の種 materialは改行なしの次の文字列です。

```text
R24-INSTANCE-GEN-20260915-v1|suite=RND|n=<decimal n>|rep=<two-digit r>
```

構造上のは次を使います。

```text
R24-INSTANCE-GEN-20260915-v1|suite=STR|structure=<STRUCTURE>|n=<decimal n>|rep=<two-digit r>
```

`seed_digest=SHA256(seed_material)`とし、先頭8 バイトのunsigned big-endian値を`seed_uint64`として保存します。顧客 `c`のselection 得点は次です。

```text
SHA256(seed_digest_hex + "|customer=" + c)
```

Canonical 顧客 識別子 順序に得点を付け、最小n件を選びます。これはequal-確率、without-replacementのハッシュ値-ranked SRSWOR realizationです。PRNG 状態、時刻、手動乱数の種、乱数の種 searchは使いません。

## 4. いいえ-redraw

```text
sample once, validate, record
```

Hard 不具合があっても乱数の種、顧客、rep、識別子を変更しません。次の理由はredrawを正当化しません。

- demand pattern
- 容量 effectの強弱
- route difficulty
- 重複 代理指標またはzero 区間
- solver/QAOAに都合が悪い
- 科学的結果が期待と異なる

<a id="5-structural-suite"></a>

## 5. 構造上の 検証一式

EPSG:4326の出典 coordinateをEPSG:6677へ変換し、projected Euclidean 距離（metres）を使用します。道路網 距離ではありません。

### 集積型

Hash 得点最小顧客を基準とし、基準自身と距離が近いn−1 顧客を選びます。Tieはselection 得点、顧客 識別子順です。

### DISPERSED

Hash 基準から開始し、現在のselected setへの最小 距離が最大の顧客を反復選択するdeterministic farthest-point traversalです。

### MIXED

第1 基準はハッシュ値最小顧客、第2 基準はそこから最遠の顧客です。`ceil(n/2)`と`floor(n/2)`のquotaを設け、両基準へ近い未選択顧客を交互に追加します。

## 6. 基準

| Anchor | 出典 |
|---|---|
| `R24-ANCHOR-N004` | `R24-RND-N004-R01` |
| `R24-ANCHOR-N010` | `R24-RND-N010-R01` |
| `R24-ANCHOR-N020` | `R24-RND-N020-R01` |

Anchorは新規標本ではありません。出典の顧客、q、出発地・到着地、容量、検証 状況を完全に継承します。出典が不正でも置換しません。

<a id="7-routing-validation"></a>

## 7. 経路計算検証

各baseのノード setを`{DEP_006} union customers`とし、全`i != j`をrun_3で計算します。必要記録数は`(n+1)n`です。

保存・検証対象:

- directed reachability
- fastest-model-time path
- 同じ保存先上の距離
- origin/destination edge offset
- 道路区間 sequenceとハッシュ値
- 連続道路区間間のスーモ `delivery` connection/turn
- duplicate proxy、zero-distance、zero-time flag

Population SCCやrun_2 費用で代用しません。Validなsame-代理指標 zero 区間は許可します。

## 8. Hard rejection

Base rejectionは、固定済み列挙値に限ります。主な分類は次のとおりです。

- 固定済み source/hash/manifest不一致
- 顧客 識別子 missing/duplicateまたはn/selection mismatch
- q_i 欠落、corrupt、non-整数、non-正、Q超過
- capacity unit mismatch
- routing proxy/endpoint invalid
- run_3 graph mismatch
- OD computation failure、missing、duplicate、unreachable
- non-finite/negative cost
- SUMO connection/turn failure
- edge sequence/endpoint semantics failure

新しい理由を後付けする場合は、新手順 版が必要です。

<a id="9-capacity-condition"></a>

## 9. 容量 条件

同じbase subsetに対してのみ、3条件を作ります。

\[
D=\sum_iq_i,\quad Q=14,
\quad m=\left\lceil\frac{D}{\rho^*Q}\right\rceil,
\quad \rho_{actual}=\frac{D}{mQ}
\]

`rho*={0.50,0.70,0.90}`です。rhoごとに顧客を再標本しません。

<a id="10-exact-packing-preflight"></a>

## 10. 厳密 packing 事前確認

需要を降順に並べ、m個の容量-Q binsへ配置できるかを、residual-容量 symmetry reductionとmemoizationを使う完全backtrackingで判定します。これは経路計算 最適化ではありません。

`PACKING_INFEASIBLE`の場合もbase subsetを保持し、その条件だけを最適化不可とします。

異なるrhoが同じmになる場合は`DEGENERATE_REGIME_SAME_M`です。全記録を保持し、容量-effect 比較からのみ除外します。

<a id="11-id"></a>

## 11. 識別子

```text
R24-RND-N{nnn}-R{rr}
R24-STR-{STRUCTURE}-N{nnn}-R{rr}
R24-ANCHOR-N{nnn}
```

容量 接尾辞は`-RHO050`、`-RHO070`、`-RHO090`です。

<a id="12-provenanceとclaim"></a>

## 12. 出典・来歴と主張

各問題例から次を逆追跡可能にします。

```text
Instance -> C_eligible -> Routing Proxy -> Synthetic Demand
```

保存対象はsource/graph/protocol/code/output ハッシュ値、乱数の種 material/digest、customer/q vector、出発地・到着地、packing certificateです。

許可される主張は「大田区を基盤とする固定済み合成対象条件を満たす ベンチマーク 母集団からのrepeated-random/controlled 構造上の subsets」です。実carrier 運用や全大田区配送の統計的代表性は主張しません。
