# R24 Instance Generation仕様（日本語）

原文authority: [R24_INSTANCE_GENERATION_SPECIFICATION.md](../../reproducibility/outputs/traffic_simulation/r24_instance_generation_specification/20260915_v1/R24_INSTANCE_GENERATION_SPECIFICATION.md)

Specification ID: `R24-INSTANCE-GEN-20260915-v1`<br>
Verdict: `R24_INSTANCE_GENERATION_SPEC_FROZEN_WITH_LIMITATIONS`

この文書はfreeze済み英語authorityの日本語版です。機械実行では原文の固定文字列、enum、schema、hashを使用してください。

## 1. Suite hierarchy

1. **Primary — Repeated Random Suite**: researcherによるcase選択biasを減らし、instance間variationを測るprimary comparison用suite
2. **Secondary — Controlled Structural Suite**: `CLUSTERED`、`DISPERSED`、`MIXED`による空間構造stress test
3. **Reference — Fixed Anchor Suite**: regression、実装比較、QUBO/solver version比較用の固定alias

## 2. Problem sizeと件数

| 区分 | n | Repetitions |
|---|---|---:|
| Quantum-comparable core | `{2,3,4}` | 各10 |
| Classical extension | `{5,8,10,15,20}` | 各10 |
| Controlled Structural | `{4,10,20}` | 各structure・nで3 |
| Fixed Anchor | `{4,10,20}` | Primary R01 alias |

Random baseは80件、structural baseは27件、anchor aliasは3件です。`n`はcomputational benchmark sizeであり、statistical sample sizeや実route stop countではありません。

## 3. SeedとSRSWOR

Primary seed materialは改行なしの次の文字列です。

```text
R24-INSTANCE-GEN-20260915-v1|suite=RND|n=<decimal n>|rep=<two-digit r>
```

Structuralは次を使います。

```text
R24-INSTANCE-GEN-20260915-v1|suite=STR|structure=<STRUCTURE>|n=<decimal n>|rep=<two-digit r>
```

`seed_digest=SHA256(seed_material)`とし、先頭8 bytesのunsigned big-endian値を`seed_uint64`として保存します。Customer `c`のselection scoreは次です。

```text
SHA256(seed_digest_hex + "|customer=" + c)
```

Canonical customer ID orderにscoreを付け、最小n件を選びます。これはequal-probability、without-replacementのhash-ranked SRSWOR realizationです。PRNG state、時刻、手動seed、seed searchは使いません。

## 4. No-redraw

```text
sample once, validate, record
```

Hard failureがあってもseed、customer、rep、IDを変更しません。次の理由はredrawを正当化しません。

- demand pattern
- capacity effectの強弱
- route difficulty
- duplicate proxyまたはzero arc
- solver/QAOAに都合が悪い
- 科学的結果が期待と異なる

## 5. Structural suite

EPSG:4326のsource coordinateをEPSG:6677へ変換し、projected Euclidean distance（metres）を使用します。Network distanceではありません。

### CLUSTERED

Hash score最小customerをanchorとし、anchor自身と距離が近いn−1 customersを選びます。Tieはselection score、customer ID順です。

### DISPERSED

Hash anchorから開始し、現在のselected setへのminimum distanceが最大のcustomerを反復選択するdeterministic farthest-point traversalです。

### MIXED

第1 anchorはhash最小customer、第2 anchorはそこから最遠のcustomerです。`ceil(n/2)`と`floor(n/2)`のquotaを設け、両anchorへ近い未選択customerを交互に追加します。

## 6. Anchor

| Anchor | Source |
|---|---|
| `R24-ANCHOR-N004` | `R24-RND-N004-R01` |
| `R24-ANCHOR-N010` | `R24-RND-N010-R01` |
| `R24-ANCHOR-N020` | `R24-RND-N020-R01` |

Anchorは新規sampleではありません。Sourceのcustomer、q、OD、capacity、validation statusを完全に継承します。Sourceがinvalidでも置換しません。

## 7. Routing validation

各baseのnode setを`{DEP_006} union customers`とし、全`i != j`をrun_3で計算します。必要record数は`(n+1)n`です。

保存・検証対象:

- directed reachability
- fastest-model-time path
- 同じpath上のdistance
- origin/destination edge offset
- edge sequenceとhash
- 連続edge間のSUMO `delivery` connection/turn
- duplicate proxy、zero-distance、zero-time flag

Population SCCやrun_2 costで代用しません。Validなsame-proxy zero arcは許可します。

## 8. Hard rejection

Base rejectionは、freeze済みenumに限ります。主な分類は次のとおりです。

- frozen source/hash/manifest不一致
- customer ID missing/duplicateまたはn/selection mismatch
- q_i missing、corrupt、non-integer、non-positive、Q超過
- capacity unit mismatch
- routing proxy/endpoint invalid
- run_3 graph mismatch
- OD computation failure、missing、duplicate、unreachable
- non-finite/negative cost
- SUMO connection/turn failure
- edge sequence/endpoint semantics failure

新しい理由を後付けする場合は、新protocol versionが必要です。

## 9. Capacity condition

同じbase subsetに対してのみ、3条件を作ります。

\[
D=\sum_iq_i,\quad Q=14,
\quad m=\left\lceil\frac{D}{\rho^*Q}\right\rceil,
\quad \rho_{actual}=\frac{D}{mQ}
\]

`rho*={0.50,0.70,0.90}`です。rhoごとにcustomerを再sampleしません。

## 10. Exact packing preflight

Demandを降順に並べ、m個のcapacity-Q binsへ配置できるかを、residual-capacity symmetry reductionとmemoizationを使う完全backtrackingで判定します。これはrouting optimizationではありません。

`PACKING_INFEASIBLE`の場合もbase subsetを保持し、そのconditionだけをoptimization不可とします。

異なるrhoが同じmになる場合は`DEGENERATE_REGIME_SAME_M`です。全recordを保持し、capacity-effect comparisonからのみ除外します。

## 11. ID

```text
R24-RND-N{nnn}-R{rr}
R24-STR-{STRUCTURE}-N{nnn}-R{rr}
R24-ANCHOR-N{nnn}
```

Capacity suffixは`-RHO050`、`-RHO070`、`-RHO090`です。

## 12. Provenanceとclaim

各instanceから次を逆追跡可能にします。

```text
Instance -> C_eligible -> Routing Proxy -> Synthetic Demand
```

保存対象はsource/graph/protocol/code/output hash、seed material/digest、customer/q vector、OD、packing certificateです。

許可されるclaimは「大田区を基盤とするfreeze済み合成eligible benchmark populationからのrepeated-random/controlled structural subsets」です。実carrier operationや全大田区配送の統計的代表性は主張しません。
