# A：従来配送業務を参考にする規則ベース推計の仕様

版：A-rule-estimate-20261112-v1.0。2026-11-12の明示指示により採用。
**佐川急便の従来の人手業務を参考にした研究上の規則モデルであり、同社の実績・実アルゴリズム・暗黙知の再現ではない。**
正本：[a_rule_baseline_v1.json](../../../configs/toc_delivery/a_rule_baseline_v1.json)。
設定をhash固定し、文書の生成表と一致を検査する。実装前の登録は出力のPREREGISTRATION.json。

## 事実と仮定

[佐川・Loogia共同発表](https://www.optimind.tech/news/ルート最適化システム「loogia」を佐川急便で導入を/)から、
出発前の位置確認・時間指定を考慮した訪問順決定が人手業務だったことを採用する。
地理的区域、近隣選択、負荷調整、限定改善、FCFSの具体的規則・回数・秒数は**本研究の仮定**である。
13kmと通常約20kmは2025年の別観測/説明で、2020年人手実測レンジでも校正目標でもない。
26分は別の拠点間輸送の待ちであり、本モデルのWを校正しない。Loogia導入後と改善率も校正しない。

## 共通条件

条件はAD-common-20261111-v1.1の正本をそのまま読む。1配送単位/地点、60/便、最大2便、
積込1800秒、顧客作業120秒、帰着後準備0秒、8〜20時、初便ready式、顧客時間窓なし。
S1=1000/10/2、S2=2000/20/4、S3=4000/40/8。Aとして凍結需要を全量読込し、座標・地点・車両を減らさない。
ODは共通の有向OSM/OSRM。実道路不足を速度・直線距離・人工ODで埋めない。
座標は区域/重心の形づくりだけに使用し、走行費用・移動秒は常に同一ODから取得する。

## A1〜A3の手順

全手法で入力から車両割当と訪問順を生成する。担当車両の外部固定は行わない。
区域の識別順を車両番号へ対応させる処理は構築規則であり、所与の顧客割当ではない。
角度0/120/240度で区域境界を回す9条件を事前固定する。readyや入力seedは変更しない。
同値の場合はstop_id、車両index、バースID順を使う。

1. **A1**：拠点からの方位角（経度差に拠点緯度cosを適用）・半径順位・IDで並べ、V個の連続・同数区域へ分割。
   各区域をその角度順に訪問し、60地点ごとに便を分割する。各車120地点を超えると拒否。
2. **A2**：A1の区域を初期値に、隣接区域間で端点顧客を移す。負荷proxyは各地点の顧客作業120秒と拠点往復移動秒の半分の和。
   負荷二乗和を厳密に減らす移動を最大V回採用。120地点上限を保つ。順序は有向道路距離の最近隣、ID同値処理。
3. **A3**：A2に加え、各車の区域端点2候補を地理重心が近い他2区域へ移すことを2パスまで検討。
   各パス各車につき最大1移動を採用し、最近隣・容量便分割後の総道路距離が厳密に減る場合のみ認める。
   その後、各便に有向距離を全arc再計算するfirst-improvementの区間反転を最大2パス適用。
   非対称ODで対称2-opt差分式を使わない。距離比較許容誤差は1e-6m。

負荷proxyは実際の運行時間の推定器ではなく割当用の規則である。
A2/A3で距離やproxyが改善してもWや勤務可行性の改善は保証しない。後段検査で失敗したら失敗として記録する。
ε制約の最適化は行わない。可行計画を将来の共通参照候補にできるが、ε値は未固定のまま維持する。

## 積込と時刻・評価

初便readyを全車のイベント列へ入れる。最小ready（同時は車両index/便番号）の便を処理し、最も早く空くバースへ割当。
開始=max(ready,バース空き,開場)、終了=開始+1800。出発=積込終了。
訪問ごとに同じODのceil秒移動＋120秒作業、最後に拠点へ戻る。第2便があればready=帰着+0をイベント列へ追加。
FCFSは研究仮定であり、佐川のバース運用としては主張しない。後から優先順位を最適化したり違反を修復したりしない。

`D=Σ全便全arc d_ij/1000 [km]`、`W=Σ(load_start−ready)/60 [min]`。
共通検査器に加え、構築関数を呼ばない独立再計算を行う。
可行解だけのmin/max/medianを報告し、可行解率は可行数/実際に計画生成まで試行した数。
入力HOLD・未実行は0%とせずnull。条件数・失敗を併記する。
独立したDの最小とWの最小を一つの計画点に結合しない。範囲は観測条件集合の記述であり信頼区間ではない。

## Tの二つの意味

`T_program_s`は共通run_measuredによる入力読込直前〜最終独立検証完了のwall秒。
地理区域形成、負荷調整、順序、積込、後処理と検査を含む。道路取得・OD事前生成は含まない。
人手の作業時間として使わない。

人手Tは共通問題での実測を得ていない。
[日本郵便事例](https://loogia.jp/cases/nihonyubin/)の熟練5〜10分/新人30〜60分は外部文脈として残すが、
Nが不明なので秒/地点へ変換せず、佐川の時間やS1〜S3の校正値にも使わない。
したがって優先3の**未校正・明示作業仮定による感度**を計算する。

人手モデルは「直列準備→1人の中央割当→P人の車両別並列計画→1人の最終調整」という直列段階を仮定する。
各車jobは車両準備＋地点数×(位置確認＋順序判断＋確認)。jobの大きい順に最も空く担当者へ割当（LPT、同値はindex）。
`T_workflow=setup + assignment_per_stop*N + max_worker_load + coordination_per_used_vehicle*V_used`。
`person_seconds`は全jobの和と直列段階の和で別計算する。
実際のプログラム実行がある計画では読込/最終検査だけの実測overheadを加え、規則生成CPU時間を人手推計へ足さない。
実行していないS1〜S3ではそのoverheadも未計測のため、均等割当を仮定する構造感度T_workflowのみ別CSVに保存し、研究Tの完成値にしない。

秒数は公表実測から推定した係数ではなく、工程を分けて感度を検証する研究仮説である。
low/central/highは速度の実証された区間ではなく仮定集合。人員は1/ceil(V/2)/V。
人手計画の実測と工程の校正が次段階に必要。規則A1/A2/A3を実際に人が実行した時間とも同定しない。
未校正係数の数値を「採用済みの佐川T」や保証された下限/上限とは扱わない。

## B〜Dとの違い

Aは角度区域・最近隣・限定移動/区間反転とFCFSの固定規則。Clarke–Wrightの節約量/端点ルート結合を使わず、
OR-Toolsの制約最適化・メタヒューリスティクス、列生成・双対価格・AOAも使わない。
限定局所改善が一般的な経路改善操作と共通でも、既存B/C/D実装を流用していない。
B〜Dの結果を読んで係数や規則を選ばず、登録後に変更する場合は別版として旧結果を保全する。

## 設定との自動照合

<!-- BEGIN GENERATED A RULE SETTINGS -->
```json
{
  "schema_version": "1.0",
  "baseline_version": "A-rule-estimate-20261112-v1.0",
  "definition": "佐川急便の従来人手業務を参考にした規則ベース推計。実測・実アルゴリズムの再現ではない。",
  "value_kind": "research_assumption",
  "common_conditions_version": "AD-common-20261111-v1.1",
  "common_conditions_sha256": "bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2",
  "random_seed": null,
  "angle_offsets_deg": [
    0,
    120,
    240
  ],
  "tie_break": "stop_id_then_vehicle_index",
  "methods": {
    "A1": {
      "assignment": "contiguous_equal_count_angular_sectors",
      "order": "angular_sweep",
      "balance_moves_per_vehicle": 0,
      "relocation_passes": 0,
      "two_opt_passes": 0
    },
    "A2": {
      "assignment": "sector_boundary_work_balance",
      "order": "directed_nearest_neighbor",
      "balance_moves_per_vehicle": 1,
      "relocation_passes": 0,
      "two_opt_passes": 0
    },
    "A3": {
      "assignment": "sector_boundary_work_balance_then_distance_relocation",
      "order": "directed_nearest_neighbor_then_directed_two_opt",
      "balance_moves_per_vehicle": 1,
      "relocation_passes": 2,
      "two_opt_passes": 2
    }
  },
  "relocation": {
    "candidate_endpoints_per_vehicle": 2,
    "nearest_other_centroids": 2,
    "acceptance": "strict_total_route_distance_decrease",
    "distance_tolerance_m": 1e-06
  },
  "trip_split": "successive_capacity_chunks_max_two",
  "loading": {
    "rule": "global_ready_FCFS_then_vehicle_index_then_trip_number",
    "berth_choice": "earliest_available_then_berth_id",
    "repair_infeasible": false
  },
  "human_time": {
    "model_version": "workflow-assumptions-v1",
    "evidence_level": "priority_3_explicit_workflow_sensitivity_NOT_observed_or_calibrated",
    "staff_rules": [
      "one",
      "half_vehicles_ceil",
      "all_vehicles"
    ],
    "parallel_assignment": "LPT_greedy_vehicle_jobs_then_worker_index",
    "profiles": {
      "low": {
        "setup_s": 300,
        "assignment_s_per_stop": 2,
        "vehicle_setup_s": 60,
        "lookup_s_per_stop": 5,
        "ordering_s_per_stop": 5,
        "review_s_per_stop": 2,
        "coordination_s_per_used_vehicle": 30
      },
      "central": {
        "setup_s": 600,
        "assignment_s_per_stop": 4,
        "vehicle_setup_s": 120,
        "lookup_s_per_stop": 10,
        "ordering_s_per_stop": 10,
        "review_s_per_stop": 4,
        "coordination_s_per_used_vehicle": 60
      },
      "high": {
        "setup_s": 900,
        "assignment_s_per_stop": 8,
        "vehicle_setup_s": 240,
        "lookup_s_per_stop": 20,
        "ordering_s_per_stop": 20,
        "review_s_per_stop": 8,
        "coordination_s_per_used_vehicle": 120
      }
    },
    "serial_pipeline": [
      "setup",
      "central_vehicle_assignment",
      "parallel_vehicle_route_planning",
      "final_coordination"
    ],
    "include_observed_common_io_and_validation_overhead": true,
    "public_Japan_Post_minutes_context_only": {
      "experienced": [
        5,
        10
      ],
      "novice": [
        30,
        60
      ],
      "reference_stop_count": null,
      "used_for_scaling": false
    },
    "interpretation": "条件付き感度集合。人手実測や信頼区間・妥当な上下限ではない。"
  },
  "validation_cases": [
    {
      "id": "ART_N6",
      "stops": 6,
      "vehicles": 2,
      "berths": 1
    },
    {
      "id": "ART_N20",
      "stops": 20,
      "vehicles": 3,
      "berths": 1
    },
    {
      "id": "ART_N120",
      "stops": 120,
      "vehicles": 2,
      "berths": 1
    },
    {
      "id": "ART_N240",
      "stops": 240,
      "vehicles": 3,
      "berths": 1
    }
  ],
  "research_input_bundles": {
    "S1": null,
    "S2": null,
    "S3": null
  },
  "range_policy": {
    "only_independently_feasible_plans": true,
    "unrun_is_null_not_zero": true,
    "interval_kind": "observed_scenario_set_min_max_median_not_confidence_interval",
    "same_plan_pairing_required": true
  },
  "sources": [
    {
      "url": "https://www.optimind.tech/news/ルート最適化システム「loogia」を佐川急便で導入を/",
      "use": "人手位置確認・順序決定という業務のみ。規則・秒数の根拠にはしない"
    },
    {
      "url": "https://loogia.jp/cases/nihonyubin/",
      "use": "他社人手時間の外部文脈のみ。N不明なので換算・校正しない"
    }
  ]
}
```
<!-- END GENERATED A RULE SETTINGS -->
