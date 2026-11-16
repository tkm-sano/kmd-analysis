# A〜D共通配送計画条件 v1.1

採用日：2026-11-11。正本は`configs/toc_delivery/common_conditions_v1_1.json`。今回のユーザー指示に基づく研究上の共通仮定であり、実事業者の測定値・設備仕様・勤務実績ではない。設定ファイルの全バイトをコードのSHA256 pinで検査する。下記表は設定から生成し、新規テストで一致を確認する。版を変えずに数値だけ書き換えた入力は拒否する。

<!-- BEGIN GENERATED CONDITIONS -->
|設定キー|採択値|
|---|---|
|scope.region|"東京都大田区"|
|scope.depot_name|"京浜トラックターミナル"|
|scope.delivery|"ToC"|
|scope.depots|1|
|scope.homogeneous_vehicles|true|
|scope.customer_time_windows|false|
|scope.fixed_customer_vehicle_assignment|false|
|scope.unused_vehicles_allowed|true|
|scope.ev_conditions|false|
|units.distance|"m"|
|units.travel_time|"s"|
|units.clock|"s_since_midnight_Asia/Tokyo"|
|units.demand|"delivery_unit"|
|units.D|"km"|
|units.W|"min"|
|units.T|"s"|
|operations.demand_per_stop|1|
|operations.capacity_per_trip|60|
|operations.max_trips_per_vehicle|2|
|operations.service_s|120|
|operations.loading_s|1800|
|operations.preparation_s|0|
|operations.opening_s|28800|
|operations.closing_s|72000|
|operations.first_ready_span_s|3600|
|scenarios.S1|{"berths": 2, "stops": 1000, "vehicles": 10}|
|scenarios.S2|{"berths": 4, "stops": 2000, "vehicles": 20}|
|scenarios.S3|{"berths": 8, "stops": 4000, "vehicles": 40}|
|timing_policy.travel_rounding|"ceil_each_arc_to_seconds"|
|timing_policy.departure|"loading_end"|
|timing_policy.service_start|"arrival"|
|timing_policy.arbitrary_route_waiting|false|
|timing_policy.berth_interval|"half_open"|
|timing_policy.preparation_occupies_berth|false|
|timing_policy.loading_preemptive|false|
|timing_policy.T_start|"before_common_input_load"|
|timing_policy.T_end|"after_final_independent_validation"|
|timing_policy.AOA_time|"quantum_circuit_simulator_wall_time"|
|road_policy.source|"OpenStreetMap"|
|road_policy.router|"OSRM"|
|road_policy.directed|true|
|road_policy.time_dependent_congestion|false|
|road_policy.distance_definition|"distance_of_fastest_route"|
|road_policy.distance_and_duration|"same_table_response"|
|road_policy.fallback_speed_allowed|false|
|road_policy.local_only|true|
|road_policy.snap_review_required|true|
|road_policy.snap_alert_m|100|
|road_policy.block_size|100|
|comparison.A|"sourced_actual_or_reference_levels"|
|comparison.B|"VeRyPy_Clarke_Wright"|
|comparison.C|"OR_Tools"|
|comparison.D|"Huang_CG_AOA"|
|comparison.multiobjective|"bidirectional_epsilon_constraint"|
|comparison.epsilon_W_min|null|
|comparison.epsilon_D_km|null|
|first_ready_rule|opening_s + (3600 * (2*v+1)) // (2*V)|
|conditions_version|AD-common-20261111-v1.1|
<!-- END GENERATED CONDITIONS -->

## v1.1改訂と適用範囲

本追加指示により、A〜D共通の帰着後準備時間を15分から0分へ変更した。旧v1.0設定と既存保存結果はそのまま保全し、現行loaderはv1.1の版・hashを要求する。旧入力・計画の無言変換はしない。積込1800秒/便と顧客先作業120秒/地点は研究上の固定仮定として維持する。顧客作業は帰着時刻、そこから定まる次便ready、勤務終了判定の時間伝播にのみ使用し、D/Wへの直接加算・変動モデル・新たな作業時間目的は導入しない。

以下を共通に使用する。

- `load_end_r = load_start_r + 1800`、バース占有は`[load_start_r, load_end_r)`。
- `return_r = departure_r + Σ ceil(OD_duration_ij) + 120 × 訪問地点数`。
- `ready_v2 = return_v1 + 0 = return_v1`、`load_start_v2 >= return_v1`。
- `W = Σ(load_start_r − ready_r)/60`。積込作業30分と顧客先作業を待機時間へ加算しない。

## 解釈と根拠

単一拠点から出発・帰着する非空便を、各車最大2便まで使う。未使用車両は出力に便を持たず、1便だけの運行も許す。顧客割当・便・順序は解法が決定し、共通入力には固定担当を持たない。準備中はバースを占有しない。積込は半開区間[start,end)の連続1800秒で、中断を認めない。

時刻はAsia/Tokyoの午前0時からの整数秒。第1便readyは28800+floor(3600(v+0.5)/V)。実装は整数演算`28800+(3600*(2*v+1))//(2*V)`で誤差を避ける。第2便readyは第1便の独立再計算帰着と同時（帰着後準備0秒）。第2便積込は帰着直後から開始でき、出発はその積込完了後となる。積込終了と出発は同時、顧客の到着と作業開始は同時とし、旧採用仕様の任意途中待機なしを維持する。運行8〜20時の設定によって休憩・労働時間の全法令を満たすとは主張しない。

道路はOpenStreetMap、経路計算はOSRM。静的・有向ODを用い、一方通行を考慮する。同じtable応答のdistanceとdurationを保存する。距離は最速経路に対応する道路距離で、直線距離や最短距離へ置換しない。OSRMの生durationはfloat64秒で保存し、運行計画と検査には各arcのceil秒を共通適用する。保守的丸めの増分は各arcにつき0以上1秒未満で、全体の増分はarc数に依存する。マクロ便でまとめて丸めない。根拠：[OSRM公式HTTP仕様](https://project-osrm.org/docs/v26.5.0/http)。道路の帰属は© OpenStreetMap contributors、[ODbL](https://www.openstreetmap.org/copyright)。実交通混雑や車両寸法制限の完全再現を保証しない。

需要は11/10固定v1を全量読込し、1地点=1配送単位とする。元の合成需要抽出方式・地点・座標・IDを保全し、再生成・削除・再抽出しない。車両容量60は重量kgや実測荷物個数への校正値ではない。

## 評価式・多目的条件

D=Σ全便全arc d_ij/1000 [km]。W=Σ(積込start−ready)/60 [min]で、積込作業は含めない。参考値としてΣ(積込end−ready)/60とW1/W2を保存する。Tは共通入力読込の直前から最終計画の独立検証完了までのperf_counter実測wall秒。方法固有の調整・初期化・変換・最適化・サンプリング・復号・整数選択・後処理も全て含める。共通の道路取得・OD構築は別の前処理台帳へ保存しTに含めない。

AOAは量子回路シミュレータの実行時間であり、実機時間ではない。D/Wの両方向ε制約法を維持し、可行参照計画取得後にε_W[min]、ε_D[km]を全手法共通で固定する。現段階はnullである。

## 由来の区別・感度分析・未確認事項

運行・規模はresearch_assumption、OSRMの単位・経路意味とOSMライセンスはdocumentation、需要はfrozen_synthetic_demand、検証問題はsynthetic_fixtureとデータ上区別する。今回採用した運行値にmeasuredの値はない。Aの実績・参照は出典と地域・需要・期間・指標範囲を伴う別台帳が必要で、異条件の値をS1〜S3結果として扱わない。

感度分析は今回は行わない。候補軸は容量、作業/積込/準備時間、道路snap・経路profile、時間刻みであり、別版を採択して全B〜Dに同一適用する。N/V/バースを解きやすくするために変えない。数値水準は未採択。

未確認は車両用出入口、全地点のOSRM対応、道路graphと全OD、A参照、B/C/D運行接続、共通資源予算/探索seed、ε水準である。条件定義GOと実データ適用HOLDを区別する。監査・判定は同ディレクトリのCOMMON_DATA_AUDIT.md、COMMON_VALIDATION_REPORT.mdを参照する。
