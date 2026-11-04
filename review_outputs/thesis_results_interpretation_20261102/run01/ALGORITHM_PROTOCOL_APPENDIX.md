# アルゴリズム設定の再実行用付録

以下は元凍結PROTOCOL.jsonを読み取った設定である。今回再学習や回路計算は行っていない。FIT.jsonごとの選択角度・精度・seed・training pool hashはB_RESOURCES_PER_FIT.csvのfit_source_pathから参照できる。全fitの値を単一の推定値に置き換えない。元コードのSHA256はALGORITHM_SOURCE_SNAPSHOTS.csv。ファイルが外部保全にある点は公開再現性の制約である。

## mirror_family

`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102/mirror_family/PROTOCOL.json` SHA256 `873aeb06feec9897337ea4ec7671d27eb1d8e9d11064112072b555814f58e98d`

```json
{
  "series": "MIRROR_MATCHING_SWAP_STAGED_V1",
  "variants": {
    "MEAN_P2": {
      "objective": "MEAN",
      "initial_states": 1
    },
    "CVAR10_P2": {
      "objective": "CVAR",
      "alpha": 0.1,
      "initial_states": 1
    },
    "CVAR01_P2": {
      "objective": "CVAR",
      "alpha": 0.01,
      "initial_states": 1
    },
    "COHERENT2_P2": {
      "objective": "MEAN",
      "initial_states": 2
    },
    "COHERENT4_P2": {
      "objective": "MEAN",
      "initial_states": 4
    }
  },
  "representatives": {
    "R3": [
      "R3_001",
      "R3_040",
      "R3_078"
    ],
    "R4": [
      "R4_001",
      "R4_040",
      "R4_078"
    ],
    "R5": [
      "R5_001",
      "R5_036",
      "R5_070"
    ]
  },
  "full_roster": true,
  "customer_partitioning": false,
  "customer_time_windows": false,
  "capacity_PE": 216,
  "service_seconds": 102,
  "return_deadline_seconds": 32400,
  "mixer": "Disjoint partial swaps of positions i and n-1-i; exact isometry to one binary orientation per pair",
  "support": "2**floor(n/2) complete routes, NOT n!; odd center position fixed; global optimum not necessarily reachable",
  "cost": "Original directed road objective folded exactly to binary-chain unary and pairwise terms using integer Decimal input arithmetic",
  "baseline": "Exact minimum over the same matching orbit by classical linear chain DP, evaluation only; no quantum novelty claim over this baseline",
  "nominal_layers": 2,
  "angles": "basis:gamma1=0, beta1,gamma2,beta2; coherent:gamma1,beta1,gamma2,beta2",
  "bounds": {
    "scaled_gamma": [
      0,
      8
    ],
    "beta": [
      -1.5707963267948966,
      1.5707963267948966
    ]
  },
  "fit": "basis:9 embedded-p1 beta points, coherent:4 gamma x3 beta points; two COBYLA starts max24 each; <=64 unique evaluations",
  "objective_sampling": {
    "CVAR_training_shots": 1024,
    "common_random_numbers": true,
    "training_seed_modes": [
      99,
      100,
      101
    ],
    "training_seed_repeats_on_representatives_only": 3
  },
  "repetitions": 10,
  "shots_per_repetition": 8192,
  "measurement_modes": [
    "OPTIMIZED",
    "FIXED_NONZERO",
    "DEPHASED_FIXED_NONZERO"
  ],
  "rng": "PCG64(SeedSequence([2026110201,scale,index,variant_id,mode,rep]))",
  "fixed_nonzero": {
    "gammas_scaled": [
      0.0,
      1.0
    ],
    "betas": [
      0.23,
      0.31
    ]
  },
  "cutoff": 1e-13,
  "tighter_cutoff": 1e-14,
  "truncation_norm_gate": 1e-06,
  "convergence_fidelity_gate": 0.99999999,
  "convergence_energy_gate": 1e-07,
  "numeric_scope": "Small independent exact permutation/qubit controls, accumulated truncation norm, cross-cutoff convergence; not full interval floating-point certification",
  "resource_gate": {
    "per_worker_bytes": 2147483648,
    "max_bond": 256
  },
  "maximum_workers": 128,
  "wall_time_limit": null,
  "rollout_gate": "All correctness, precision, resource, seed-stream and replay checks pass. Quality improvement is reported, not required to publish a negative-result cohort.",
  "inferential_scope": "Seed intervals conditional on each input;26 parent groups retain dependence across scenario variants; single fixed configuration, no broad QAOA advantage claim"
}
```

## grover_depth

`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102/grover_depth/PROTOCOL.json` SHA256 `5e6a58212b1c7981bbd6515a246b38119e524c83b270afcf3ada6512dbd5e615`

```json
{
  "series": "FULL_PERMUTATION_GROVER_DEPTH_P2_P3_V1",
  "layers": [
    2,
    3
  ],
  "representatives": {
    "R3": [
      "R3_001",
      "R3_040",
      "R3_078"
    ],
    "R4": [
      "R4_001",
      "R4_040",
      "R4_078"
    ],
    "R5": [
      "R5_001",
      "R5_036",
      "R5_070"
    ]
  },
  "full_roster": true,
  "customer_partitioning": false,
  "customer_time_windows": false,
  "capacity_PE": 216,
  "service_seconds": 102,
  "return_deadline_seconds": 32400,
  "support": "All n! customer permutations, independently certified return feasible; ideal uniform initial permutation state",
  "training_samples": 65536,
  "training": "Reuse unchanged p1 uniform cost pool on main cohort; independent pools on representative training-seed repeats",
  "optimizer": "Analytic last beta, two COBYLA starts x32 function calls, embedded p1 and split initialization; <=68 unique evaluations",
  "gamma_scaled_bounds": [
    0,
    8
  ],
  "beta_bounds": [
    -3.141592653589793,
    3.141592653589793
  ],
  "global_angle_optimum_proved": false,
  "final_validation": "n<=25: existing exact complex subset DP; n>25: shared independent uniform MC prefix over all characteristic frequencies",
  "MC_epsilons": [
    0.002,
    0.001,
    0.0005
  ],
  "MC_family_failure": 1e-06,
  "MC_confidence": "Simultaneous complex Hoeffding union over all queries and all3 predefined sample sizes; optional refinement is covered",
  "numerical_phase": "Complex Taylor16 on reduced |x|<=1/8 plus repeated squaring, explicit conservative IEEE bound and route-cost/angle error",
  "state_precision": "Unitary telescoping norm-error propagation; normalized-state trace upper<=.01 and infidelity<=.001; independent-PRNG/IEEE assumptions explicit",
  "shots": 8192,
  "measurement_seeds": 10,
  "representative_training_repeats": 3,
  "rng": "PCG64 with separate SeedSequence components for input/layers/training/validation/measurement",
  "maximum_DP_workers": 32,
  "maximum_MC_workers": 64,
  "per_worker_DP_memory_bytes": 34359738368,
  "wall_time_limit": null,
  "resource_failure": "If error gate still fails at the predefined third precision, no performance value is promoted and full rollout remains unqualified"
}
```

## active_adjacent_p3

`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/staged_qaoa_validation_20261102/active_adjacent_p3/PROTOCOL.json` SHA256 `f4605d6aeec0e2533edb7d7d3f9df39c0760caba9d4fccb753c07c95c67a6022`

```json
{
  "method": "Adjacent parity swap p3; active-label MPS rank64, explicit truncation bound",
  "optimizer": "Deterministic three-point grid t={0,.5,1}; gamma fixed, all beta scaled by t; choose conservative upper expected energy",
  "gammas": [
    0.0,
    0.009,
    0.017
  ],
  "base_betas": [
    0.07,
    0.09,
    0.11
  ],
  "trace_target": 0.01,
  "memory_bytes": 8589934592,
  "work_units_per_state": 1000000000000.0,
  "shots": 8192,
  "measurement_seeds": 10,
  "scope": "Restricted angle search, no continuous or global angle optimum claim. Approximation errors conditional on floating-point residual model.",
  "seeds": "Independent PCG64 measurement streams; deterministic training has no training seed; seed0 replayed exactly",
  "invalid": "Count all invalid raw outcomes; never repair or resample. Best feasible draw reported with invalid count.",
  "freeze_before_representatives": true
}
```

## 本文3.13へ追加する説明

mirrorは経路位置iとn−1−iの互いに素なpartial swapを二値の向きへ同型変換した支持を用いる。各入力の元有向OD費用を整数Decimal演算で二値chainの単項・二体項へ折り込み、同支持の古典chain-DP最小を対照とする。単一基底初期状態では第1位相が大域位相となるためγ1=0であり、COHERENT2/4は2/4初期状態を用いる。層数2、角度範囲・開始格子・COBYLA最大評価数は上記固定設定に従う。CVAR学習は1024shotと共通乱数を使い、最終8192shotの測定とは分ける。全件のtraining_mode99と代表点に限る追加学習seedを混合しない。

Groverは理想的な全順列一様初期状態とn!支持のモデルを用い、主cohortでは既存65536費用の学習poolを保持する。p=2/3、解析的な最後のβと2開始点のCOBYLA、最大68固有評価という固定予算である。n≤25の最終検証は保存complex subset-DP、n>25は別一様MCの共通prefixと事前3精度を用いる。学習・最終検証・Born測定の乱数を区別し、global角度最適を証明したとはしない。

activeはgammas=[0,0.009,0.017]、base betas=[0.07,0.09,0.11]とし、betaをt∈{0,0.5,1}で尺度変更する3点gridで保守的な期待費用上界を選ぶ。連続最適化や全角度最適を主張しない。rank64のactive-label MPSとtruncation誤差条件は元コード・PROTOCOLの通りである。これらのソフトウェア上の状態表現の大きさを、そのまま実装済み量子ハードウェア資源に読み替えない。
